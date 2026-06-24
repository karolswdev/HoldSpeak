import XCTest
import Contracts
import Providers
@testable import RuntimeCore

#if canImport(CoreML)
import CoreML

/// A self-contained, end-to-end REAL diarization proof (opt-in: `RUN_DIARIZE_PROOF=1`).
///
/// It generates its OWN two-voice dialogue with macOS `say` (a woman + a man, alternating turns),
/// splices the turns into one 16 kHz mono take, then runs the ACTUAL shipping pipeline — the real
/// `AudioEmbed` Core ML model behind `AudioEmbedder` + the real `SpeakerDiarizer` — and asserts the
/// post-recording pass separates the take back into exactly those two speakers. No pre-baked
/// fixtures, no stub embedder: dialogue in, speaker labels out.
///
/// macOS-only + needs the (gitignored) model, so it is OPT-IN and skipped in CI. The model path
/// defaults to the repo's `apple/ml/AudioEmbed.mlpackage` (override with `DIARIZE_MODEL`); the
/// clustering threshold defaults to the shipping value (override with `DIARIZE_THRESHOLD`).
final class DiarizeProofTests: XCTestCase {

    /// One scripted turn: who says it, and what.
    private struct Turn { let voice: String; let truth: String; let line: String }

    private let dialogue: [Turn] = [
        Turn(voice: "Daniel",   truth: "M", line: "Good morning everyone, thanks for joining the architecture review. Let us start with the database migration plan for the new service."),
        Turn(voice: "Samantha", truth: "F", line: "Thanks for that. I looked at the migration and I am quite worried about the downtime window during the cutover on Friday night."),
        Turn(voice: "Daniel",   truth: "M", line: "That is a fair concern. We could use a blue green deployment so we never have to take the production service offline at all."),
        Turn(voice: "Samantha", truth: "F", line: "I really like that approach. I will draft the rollback procedure in case the new cluster starts to misbehave under real load."),
        Turn(voice: "Daniel",   truth: "M", line: "Perfect. Let us also add a synthetic monitoring check so that we catch any regressions long before our customers ever notice."),
        Turn(voice: "Samantha", truth: "F", line: "Completely agreed. I will own the monitoring task and report back to the whole team by Friday with a working dashboard."),
    ]

    func testGeneratedDialogueSeparatesBackIntoTwoSpeakers() async throws {
        let env = ProcessInfo.processInfo.environment
        try XCTSkipUnless(env["RUN_DIARIZE_PROOF"] == "1", "set RUN_DIARIZE_PROOF=1 to run the real end-to-end diarization proof")
        let sampleRate = 16_000
        let threshold = Float(env["DIARIZE_THRESHOLD"] ?? "") ?? 0.65

        // 1) Load the REAL model through the shipping AudioEmbedder (compile the .mlpackage first).
        let modelURL = env["DIARIZE_MODEL"].map { URL(fileURLWithPath: $0) } ?? Self.repoModelURL()
        try XCTSkipUnless(FileManager.default.fileExists(atPath: modelURL.path),
                          "model not found at \(modelURL.path) — set DIARIZE_MODEL")
        let compiled = try await MLModel.compileModel(at: modelURL)
        let embedder = try AudioEmbedder(compiledModelURL: compiled)

        // 2) Generate + splice the dialogue: each turn -> say -> 16 kHz mono PCM -> one take.
        let work = FileManager.default.temporaryDirectory.appendingPathComponent("diarize-e2e-\(getpid())")
        try? FileManager.default.createDirectory(at: work, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: work) }

        var audio: [Int16] = []
        var segments: [Segment] = []
        var cursor = 0
        for (i, turn) in dialogue.enumerated() {
            let pcm = try Self.synthesize(turn.line, voice: turn.voice, into: work, index: i)
            let start = Double(cursor) / Double(sampleRate)
            let end = Double(cursor + pcm.count) / Double(sampleRate)
            segments.append(Segment(text: turn.line, speaker: "Speaker 1", startTime: start, endTime: end))
            audio.append(contentsOf: pcm)
            cursor += pcm.count
        }
        XCTAssertGreaterThan(audio.count, sampleRate * 10, "expected a multi-second take")

        // 3) Run the ACTUAL post-recording diarization pass.
        let diarizer = SpeakerDiarizer(embedder: embedder, threshold: threshold)
        let labelled = diarizer.diarize(segments, audio: audio, sampleRate: sampleRate)

        // 4) Show it — the spliced dialogue, relabelled by who the model thinks spoke each turn.
        print("\n=== END-TO-END DIARIZATION (threshold \(threshold), model \(modelURL.lastPathComponent)) ===")
        for (i, seg) in labelled.enumerated() {
            let mark = (Self.truthPartition(dialogue.map(\.truth)) == Self.intPartition(labelled.map(\.speakerId))) ? "" : "  <-?"
            print(String(format: "  %@ (%@)  ->  %@%@", dialogue[i].voice, dialogue[i].truth, seg.speaker, mark))
            _ = i
        }
        print("  discovered speakers: \(diarizer.speakers.count)")

        // 5) Assert the model partitioned the take back into the true two voices.
        let truthPart = Self.truthPartition(dialogue.map(\.truth))
        let predPart  = Self.intPartition(labelled.map(\.speakerId))
        XCTAssertEqual(Set(labelled.map(\.speakerId)).count, 2, "expected exactly 2 speakers")
        XCTAssertEqual(predPart, truthPart, "predicted speaker partition must match the true M/F turns")
        print("=== PASS: the woman's turns and the man's turns separated correctly ===\n")
    }

    // MARK: - Audio generation (macOS `say` + `afconvert`, no third-party deps)

    /// `say` the line in `voice` → AIFF → 16 kHz mono s16 PCM (via `afconvert`) → `[Int16]`.
    private static func synthesize(_ line: String, voice: String, into dir: URL, index: Int) throws -> [Int16] {
        let aiff = dir.appendingPathComponent("turn-\(index).aiff")
        let wav  = dir.appendingPathComponent("turn-\(index).wav")
        try run("/usr/bin/say", ["-v", voice, line, "-o", aiff.path])
        // LEI16@16000, mono — the transcriber/diarizer contract.
        try run("/usr/bin/afconvert", ["-f", "WAVE", "-d", "LEI16@16000", "-c", "1", aiff.path, wav.path])
        return try pcm16FromWAV(wav)
    }

    @discardableResult
    private static func run(_ launchPath: String, _ args: [String]) throws -> Int32 {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: launchPath)
        p.arguments = args
        p.standardOutput = nil; p.standardError = nil
        try p.run()
        p.waitUntilExit()
        XCTAssertEqual(p.terminationStatus, 0, "\(launchPath) \(args.first ?? "") failed")
        return p.terminationStatus
    }

    /// Parse a little-endian s16 WAV's `data` chunk into `[Int16]` (alignment-safe).
    private static func pcm16FromWAV(_ url: URL) throws -> [Int16] {
        let data = try Data(contentsOf: url)
        guard let r = data.range(of: Data("data".utf8)) else { return [] }
        let sizeAt = r.upperBound
        guard sizeAt + 4 <= data.count else { return [] }
        let size = Int(data[sizeAt..<sizeAt + 4].reduce(UInt32(0)) { ($0 >> 8) | (UInt32($1) << 24) }) // LE
        let start = sizeAt + 4
        let bytes = [UInt8](data[start..<min(data.count, start + size)])
        var out = [Int16](); out.reserveCapacity(bytes.count / 2)
        var i = 0
        while i + 1 < bytes.count {
            out.append(Int16(bitPattern: UInt16(bytes[i]) | (UInt16(bytes[i + 1]) << 8)))
            i += 2
        }
        return out
    }

    // MARK: - Helpers

    /// `apple/ml/AudioEmbed.mlpackage`, derived from this test file's location.
    private static func repoModelURL() -> URL {
        URL(fileURLWithPath: #filePath)            // …/apple/Tests/RuntimeCoreTests/DiarizeProofTests.swift
            .deletingLastPathComponent()           // …/RuntimeCoreTests
            .deletingLastPathComponent()           // …/Tests
            .deletingLastPathComponent()           // …/apple
            .appendingPathComponent("ml/AudioEmbed.mlpackage")
    }

    /// Canonical partition by first appearance: [F,M,F] and [M,F,M] both differ from [0,0,1].
    private static func truthPartition(_ xs: [String]) -> [Int] { canonical(xs) }
    private static func intPartition(_ xs: [String?]) -> [Int] { canonical(xs.map { $0 ?? "" }) }
    private static func canonical<T: Hashable>(_ items: [T]) -> [Int] {
        var seen: [T: Int] = [:]; var out: [Int] = []
        for x in items { if let id = seen[x] { out.append(id) } else { let id = seen.count; seen[x] = id; out.append(id) } }
        return out
    }
}
#endif
