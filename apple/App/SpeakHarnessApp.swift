import SwiftUI
import AVFoundation
import WhisperKit

// HSM-3 + HSM-5-02 — "Speak to it": the air-gapped notetaker loop, end to end on the
// iPad. Press Record, talk through a meeting; on Stop the audio is transcribed
// ON-DEVICE with WhisperKit, the transcript is fed to the local Qwen3 model
// (LlamaProvider), and you get decisions / action_items / requirements — all with no
// network (after the one-time Whisper model fetch). This is the paradigm made real on
// the user's own words, not a canned transcript.
//
// Compiled as ONE module with the Contracts/Providers/RuntimeCore/InferenceLlama
// sources (gen-speak-harness.rb) + the WhisperKit + LLM SPM packages.

@main
struct SpeakHarnessApp: App {
    var body: some Scene {
        WindowGroup { SpeakView().preferredColorScheme(.dark) }
    }
}

// MARK: - Signal palette

private enum Sig {
    static let bg = Color(hex: 0x0E0F13)
    static let s1 = Color(hex: 0x15171D)
    static let s2 = Color(hex: 0x1C1F27)
    static let s3 = Color(hex: 0x242833)
    static let line = Color.white.opacity(0.07)
    static let text = Color(hex: 0xF2F3F5)
    static let muted = Color(hex: 0x9BA2B0)
    static let faint = Color(hex: 0x767E8D)
    static let accent = Color(hex: 0xFF6B35)
    static let ok = Color(hex: 0x3ECF8E)
    static let bad = Color(hex: 0xE5544B)
    static func style(for type: String) -> (Color, String) {
        switch type {
        case "decisions":    return (Color(hex: 0x5B8DEF), "checkmark.seal.fill")
        case "action_items": return (ok, "arrow.right.circle.fill")
        case "requirements": return (Color(hex: 0xF2A33C), "list.bullet.rectangle.fill")
        default:             return (accent, "sparkles")
        }
    }
}
private extension Color {
    init(hex: UInt) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255, opacity: 1)
    }
}

// MARK: - Model

@MainActor
final class SpeakModel: ObservableObject {
    enum Phase: Equatable { case idle, recording, transcribing, generating, done, error(String) }

    @Published var phase: Phase = .idle
    @Published var seconds = 0
    @Published var transcript = ""
    @Published var results: [Art] = []
    @Published var note = "Press record and talk through a meeting."

    struct Art: Identifiable { let id = UUID(); let type: String; let ok: Bool; let title: String; let body: String }

    private let capture = AudioCaptureService()
    private var pcm: [Int16] = []
    private var timer: Timer?

    var isBusy: Bool { phase == .transcribing || phase == .generating }
    var isRecording: Bool { phase == .recording }

    func toggleRecord() { isRecording ? stop() : start() }

    private func start() {
        Task { @MainActor in
            let granted = await Self.requestMic()
            guard granted else { phase = .error("Microphone permission denied"); return }
            pcm.removeAll(); transcript = ""; results = []; seconds = 0
            do {
                try capture.start { [weak self] chunk in
                    // Hops to the main actor to mutate the buffer (capture calls off-thread).
                    Task { @MainActor in self?.pcm.append(contentsOf: chunk.samples) }
                }
                phase = .recording; note = "Listening… talk through your meeting, then stop."
                timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
                    Task { @MainActor in self?.seconds += 1 }
                }
            } catch { phase = .error("Couldn't start the mic: \(error)") }
        }
    }

    private func stop() {
        timer?.invalidate(); timer = nil
        try? capture.stop()
        let samples = pcm
        guard samples.count > 16_000 else { phase = .error("Too short — record a few seconds."); return }
        Task { await transcribeThenGenerate(samples) }
    }

    private func transcribeThenGenerate(_ samples: [Int16]) async {
        phase = .transcribing; note = "Transcribing on device with Whisper…"
        let floats = samples.map { Float($0) / 32768.0 }
        do {
            // Load Whisper, transcribe, then release it BEFORE loading the 3GB LLM
            // so peak memory stays ~max(model), not the sum (8GB iPad).
            var whisper: WhisperKit? = try await WhisperKit(WhisperKitConfig(model: "base"))
            // HSM-18-03 — the ONE language resolver; "auto"/absent -> nil, byte-identical.
            var decodeOpts = DecodingOptions()
            decodeOpts.language = WhisperLanguage.configuredCode()
            let out = try await whisper!.transcribe(audioArray: floats, decodeOptions: decodeOpts)
            let segs = out.flatMap { $0.segments }
            transcript = segs.map { $0.text }.joined(separator: " ")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            whisper = nil
            guard !transcript.isEmpty else { phase = .error("Whisper heard nothing — try again, louder."); return }

            guard let modelPath = Self.localGGUF() else {
                phase = .error("No .gguf in Documents — push one with push-model-device.sh"); return
            }
            phase = .generating; note = "Generating artifacts with the on-device model…"
            let t = transcriptToContract(segs)
            // A real 2-min transcript eats most of the default 2048 ctx, so the
            // longer action_items/requirements output got squeezed out before any
            // JSON appeared ("no JSON"). 8192 leaves ample room for both the
            // transcript AND the generated JSON. Whisper is released above, so the
            // peak is just the LLM + its KV cache — fits the 8GB iPad.
            let provider = try LlamaProvider(modelPath: modelPath, maxTokenCount: 8192)
            let engine = ArtifactGenerationEngine(provider: provider)
            let outcomes = await engine.generate(types: [.decisions, .actionItems, .requirements], from: t)
            for (type, r) in outcomes {
                switch r {
                case .success(let a): results.append(.init(type: type.rawValue, ok: true, title: a.title, body: a.bodyMarkdown))
                case .failure(let e): results.append(.init(type: type.rawValue, ok: false, title: "Couldn't generate", body: "\(e)"))
                }
            }
            phase = .done; note = "\(results.filter(\.ok).count)/\(results.count) artifacts — from your voice, on device."
        } catch {
            phase = .error("\(error)")
        }
    }

    private func transcriptToContract(_ segs: [TranscriptionSegment]) -> Transcript {
        let mapped = segs.map {
            Segment(text: $0.text.trimmingCharacters(in: .whitespaces), speaker: "Speaker 1",
                    speakerId: nil, startTime: Double($0.start), endTime: Double($0.end),
                    isBookmarked: false, deviceId: nil)
        }
        return Transcript(meetingId: "ipad_voice_001",
                          segments: mapped.isEmpty
                            ? [Segment(text: transcript, speaker: "Speaker 1", startTime: 0, endTime: Double(seconds))]
                            : mapped,
                          transcriptHash: "ipad-voice")
    }

    static func localGGUF() -> String? {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else { return nil }
        return ((try? FileManager.default.contentsOfDirectory(at: docs, includingPropertiesForKeys: nil)) ?? [])
            .filter { $0.pathExtension.lowercased() == "gguf" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }.first?.path
    }

    static func requestMic() async -> Bool {
        await withCheckedContinuation { cont in
            AVAudioApplication.requestRecordPermission { cont.resume(returning: $0) }
        }
    }
}

// MARK: - View

struct SpeakView: View {
    @StateObject private var m = SpeakModel()

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            RadialGradient(colors: [Sig.accent.opacity(0.16), .clear],
                           center: .top, startRadius: 0, endRadius: 520).ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    recordCard
                    if !m.transcript.isEmpty { transcriptCard }
                    ForEach(m.results) { card($0) }
                    if case .done = m.phase { egress }
                    Spacer(minLength: 16)
                }
                .padding(22).frame(maxWidth: 720).frame(maxWidth: .infinity)
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(LinearGradient(colors: [Sig.accent, Color(hex: 0xEC5A28)], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .frame(width: 30, height: 30)
                    .overlay(Image(systemName: "waveform").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.bg))
                Text("HoldSpeak").font(.system(size: 19, weight: .bold)).foregroundStyle(Sig.text)
                Text("Mobile").font(.system(size: 19)).foregroundStyle(Sig.faint)
                Spacer()
                Text("Speak · local").font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.accent)
                    .padding(.horizontal, 10).padding(.vertical, 5).background(Sig.accent.opacity(0.12), in: Capsule())
            }
            Text("Speak your meeting").font(.system(size: 29, weight: .bold)).foregroundStyle(Sig.text)
            Text("Record, and the iPad transcribes your voice and pulls out the decisions — on-device, no network.")
                .font(.system(size: 15)).foregroundStyle(Sig.muted).fixedSize(horizontal: false, vertical: true)
        }
    }

    private var recordCard: some View {
        VStack(spacing: 16) {
            Button { m.toggleRecord() } label: {
                ZStack {
                    Circle().fill(m.isRecording ? Sig.bad : Sig.accent).frame(width: 96, height: 96)
                        .shadow(color: (m.isRecording ? Sig.bad : Sig.accent).opacity(0.5), radius: 16)
                    Image(systemName: m.isRecording ? "stop.fill" : "mic.fill")
                        .font(.system(size: 38, weight: .bold)).foregroundStyle(.black)
                }
            }
            .disabled(m.isBusy)
            .opacity(m.isBusy ? 0.5 : 1)
            if m.isRecording {
                Text(String(format: "%02d:%02d", m.seconds / 60, m.seconds % 60))
                    .font(.system(size: 22, weight: .bold).monospaced()).foregroundStyle(Sig.text)
            } else if m.isBusy {
                HStack(spacing: 8) { ProgressView().tint(Sig.accent); Text(m.note).font(.subheadline).foregroundStyle(Sig.muted) }
            }
            if !m.isBusy && !m.isRecording {
                Text(m.note).font(.subheadline).foregroundStyle(Sig.muted).multilineTextAlignment(.center)
            }
        }
        .padding(22).frame(maxWidth: .infinity)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
    }

    private var transcriptCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("TRANSCRIPT").font(.caption2.weight(.bold)).tracking(1).foregroundStyle(Sig.faint)
            Text(m.transcript).font(.system(size: 14)).foregroundStyle(Sig.muted)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Sig.line, lineWidth: 1))
    }

    private func card(_ r: SpeakModel.Art) -> some View {
        let (color, glyph) = Sig.style(for: r.type)
        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 9) {
                Image(systemName: r.ok ? glyph : "exclamationmark.triangle.fill").foregroundStyle(r.ok ? color : Sig.bad)
                Text(r.type.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.system(size: 13, weight: .bold)).tracking(0.5).foregroundStyle(r.ok ? color : Sig.bad)
                Spacer()
            }
            Text(r.title).font(.system(size: 16, weight: .semibold)).foregroundStyle(Sig.text)
            Text(r.body).font(.system(size: 14).monospaced()).foregroundStyle(Sig.muted)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Sig.line, lineWidth: 1))
    }

    private var egress: some View {
        HStack(spacing: 8) {
            Image(systemName: "lock.fill").foregroundStyle(Sig.ok)
            Text("on device").font(.caption.monospaced()).foregroundStyle(Sig.muted)
        }
        .padding(.horizontal, 10).padding(.vertical, 8)
        .background(Sig.s3, in: RoundedRectangle(cornerRadius: 9))
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(Sig.line, lineWidth: 1))
    }
}
