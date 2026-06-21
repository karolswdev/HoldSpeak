import SwiftUI
import AVFoundation
import WhisperKit

// HSM-13-04 (the gate) — Answer the coder, by voice, from the iPad. Point this at the
// same HoldSpeak desktop your coding session runs against: it surfaces the waiting
// agent's question, you HOLD TO SPEAK an answer, it is transcribed ON-DEVICE
// (WhisperKit), you review it, and on an explicit Send it is delivered into that coder
// session through the inject path (POST /api/dictation/remote). The capture +
// transcription are the iPad's; only the resulting text leaves. Never autonomous.
//
// Built as ONE module with Contracts/Providers/RuntimeCore (gen-companion-answer.rb) +
// the WhisperKit package, so it drives the REAL VoiceNoteComposer (HSM-13-02) over the
// REAL AudioCaptureService + a WhisperKit-backed ITranscriber + HTTPDesktopClient.

@main
struct CompanionAnswerApp: App {
    var body: some Scene {
        WindowGroup { AnswerView().preferredColorScheme(.dark) }
    }
}

// MARK: - On-device transcription (WhisperKit-backed ITranscriber)

/// Transcribes captured audio fully on-device with WhisperKit. Built over the audio it
/// was handed (the `VoiceNoteComposer` factory shape) — convert the accumulated
/// 16 kHz mono PCM16 chunks to normalized floats and run Whisper, mapping its segments
/// to the Phase-0 `Segment` contract. The model loads lazily inside `transcribe()` and
/// is released when it returns (peak-memory discipline).
final class WhisperKitTranscriber: ITranscriber, @unchecked Sendable {
    private let chunks: [AudioChunk]
    private let model: String

    init(chunks: [AudioChunk], model: String) {
        self.chunks = chunks
        self.model = model
    }

    func transcribe() async throws -> [Segment] {
        let samples = chunks.flatMap { $0.samples }
        guard samples.count >= 16_000 / 4 else { return [] }   // < ~0.25s → nothing to say
        let floats = samples.map { Float($0) / 32768.0 }
        let whisper = try await WhisperKit(WhisperKitConfig(model: model))
        let results = try await whisper.transcribe(audioArray: floats)
        // WhisperKit's raw segment text carries special tokens — <|startoftranscript|>,
        // <|en|>, <|0.00|> timestamps, <|endoftext|>. `WhisperText.clean` strips them so
        // the coder receives clean prose, not control markup (a real-metal run caught
        // this; the cleaner is unit-tested in the package).
        let raw = results.flatMap { $0.segments }.map(\.text).joined(separator: " ")
        let clean = WhisperText.clean(raw)
        guard !clean.isEmpty else { return [] }
        return [TranscribedSegment(text: clean, startTime: 0, endTime: 0).asContractSegment()]
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
    static let warn = Color(hex: 0xF2A33C)
    static let bad = Color(hex: 0xE5544B)
}

private extension Color {
    init(hex: UInt) {
        self.init(.sRGB,
                  red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: 1)
    }
}

// MARK: - Model

@MainActor
final class AnswerModel: ObservableObject {
    @Published var host = ProcessInfo.processInfo.environment["HS_DESKTOP_HOST"] ?? ""
    @Published var portText = ProcessInfo.processInfo.environment["HS_DESKTOP_PORT"] ?? "8000"
    @Published var token = ProcessInfo.processInfo.environment["HS_DESKTOP_TOKEN"] ?? ""

    @Published var connection: DesktopConnection?
    @Published var egress = ""
    @Published var board = CompanionBoardState()   // the waiting coders + the selected target (HSM-13-03)

    // Voice answer state (mirrored from the VoiceNoteComposer)
    @Published var phase: Phase = .idle
    @Published var reviewText = ""
    @Published var status = ""
    @Published var delivered = false
    @Published var modelName = "base"

    enum Phase: Equatable { case idle, recording, transcribing, review, delivering, delivered, failed }

    private var composer: VoiceNoteComposer?

    var canConnect: Bool { !host.trimmingCharacters(in: .whitespaces).isEmpty }
    /// The target an answer would currently land in (the selected waiting coder).
    var activeTarget: CompanionTarget? { board.activeTarget }

    private func makeClient() -> HTTPDesktopClient? {
        guard let port = Int(portText.trimmingCharacters(in: .whitespaces)), port > 0 else { return nil }
        let peer = DesktopPeer(host: host, port: port, token: token.isEmpty ? nil : token, scheme: "http")
        guard let config = HTTPDesktopClient.Config(peer: peer) else { return nil }
        return HTTPDesktopClient(config: config)
    }

    /// Probe the desktop and pull the waiting question.
    func connect() async {
        guard let port = Int(portText.trimmingCharacters(in: .whitespaces)), port > 0 else {
            connection = .offline("invalid port"); return
        }
        let peer = DesktopPeer(host: host, port: port, token: token.isEmpty ? nil : token, scheme: "http")
        guard let config = HTTPDesktopClient.Config(peer: peer) else { connection = .offline("invalid host"); return }
        let link = CompanionLink(client: HTTPDesktopClient(config: config))
        egress = link.egressLabel
        connection = await link.probe()
        await refreshBoard()
    }

    /// Load the Companion board (the waiting coders + the selected target) via the seam.
    func refreshBoard() async {
        guard let client = makeClient() else { return }
        if case .success(let s) = await CompanionBoard(client: client).load() { board = s }
    }

    /// Make `target` the active reply target — the next answer delivers to it.
    func select(_ target: CompanionTarget) async {
        guard let client = makeClient() else { return }
        if case .success(let s) = await CompanionBoard(client: client).select(target) { board = s }
    }

    /// Pin/unpin a waiting coder (sticky target).
    func pin(_ target: CompanionTarget, _ pinned: Bool) async {
        guard let client = makeClient() else { return }
        if case .success(let s) = await CompanionBoard(client: client).pin(target, pinned: pinned) { board = s }
    }

    // MARK: voice answer

    func startRecording() async {
        guard await Self.requestMic() else { status = "Microphone permission denied."; phase = .failed; return }
        guard let client = makeClient() else { status = "Invalid pairing."; phase = .failed; return }
        let model = modelName
        let c = VoiceNoteComposer(
            capture: AudioCaptureService(),
            client: client,
            makeTranscriber: { chunks in WhisperKitTranscriber(chunks: chunks, model: model) }
        )
        composer = c
        reviewText = ""; status = ""; delivered = false
        c.startRecording()
        phase = .recording
    }

    func stopAndTranscribe() async {
        guard let c = composer else { return }
        phase = .transcribing
        status = "Transcribing on-device…"
        await c.stopAndTranscribe()
        sync(c)
    }

    func send() async {
        guard let c = composer else { return }
        c.editText(reviewText)             // honor any edits to the recognized text
        phase = .delivering
        status = "Delivering to the coder…"
        _ = await c.send()
        sync(c)
    }

    private func sync(_ c: VoiceNoteComposer) {
        switch c.state {
        case .idle: phase = .idle
        case .recording: phase = .recording
        case .transcribing: phase = .transcribing
        case .review(let t): reviewText = t; phase = .review; status = t.isEmpty ? "No speech recognized." : "Review, then send."
        case .delivering: phase = .delivering
        case .delivered(let r):
            phase = .delivered; delivered = r.delivered
            status = r.delivered ? "Delivered → the coder received it." : "Processed, but no coder was waiting."
        case .failed(let stage, let reason):
            phase = .failed; status = "\(stage) failed: \(reason)"
        }
    }

    static func requestMic() async -> Bool {
        await withCheckedContinuation { cont in
            AVAudioApplication.requestRecordPermission { cont.resume(returning: $0) }
        }
    }
}

// MARK: - View

struct AnswerView: View {
    @StateObject private var model = AnswerModel()

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    if model.connection == nil { pairingCard } else { connectionRow }
                    if model.connection?.reachable == true {
                        boardCard
                        answerCard
                    }
                    footer
                }
                .padding(20).frame(maxWidth: 580).frame(maxWidth: .infinity)
            }
        }
        .task { if model.canConnect { await model.connect() } }
        .tint(Sig.accent)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("ANSWER THE CODER").font(.caption.weight(.bold)).tracking(2).foregroundStyle(Sig.accent)
            Text("Reply to your coding session by voice")
                .font(.largeTitle.bold()).foregroundStyle(Sig.text)
            Text("HSM-13-04 · spoken on the iPad, transcribed on-device, delivered into the coder")
                .font(.footnote).foregroundStyle(Sig.faint)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var pairingCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            cardTitle("Pair", "Your HoldSpeak desktop on your own network")
            field("Host", text: $model.host, placeholder: "192.168.1.x", keyboard: .URL)
            HStack(spacing: 12) {
                field("Port", text: $model.portText, placeholder: "8000", keyboard: .numberPad).frame(width: 130)
                field("Token", text: $model.token, placeholder: "Bearer token", secure: true)
            }
            Button { Task { await model.connect() } } label: {
                Text("Connect").font(.headline).foregroundStyle(.black)
                    .frame(maxWidth: .infinity).padding(.vertical, 13)
                    .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
            }
            .disabled(!model.canConnect).opacity(model.canConnect ? 1 : 0.5)
        }
        .cardChrome()
    }

    private var connectionRow: some View {
        let reachable = model.connection?.reachable ?? false
        return HStack(spacing: 10) {
            Circle().fill(reachable ? Sig.ok : Sig.bad).frame(width: 10, height: 10)
            Text(reachable ? "Connected to \(model.host)" : "Unreachable")
                .font(.subheadline).foregroundStyle(Sig.muted)
            Spacer()
            Button { Task { await model.refreshBoard() } } label: {
                Image(systemName: "arrow.clockwise").foregroundStyle(Sig.accent)
            }
        }
        .padding(12).background(Sig.s1, in: RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Sig.line, lineWidth: 1))
    }

    /// The Companion board (HSM-13-03): the waiting coders, the selected target made
    /// unmistakable. Tap a row to make it the target your answer will land in.
    private var boardCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Circle().fill(model.board.awaiting ? Sig.warn : Sig.faint).frame(width: 8, height: 8)
                Text(model.board.awaiting ? "Waiting for you" : "No coder waiting")
                    .font(.caption.weight(.bold)).tracking(1)
                    .foregroundStyle(model.board.awaiting ? Sig.warn : Sig.faint)
                Spacer()
                if model.board.targets.count > 1 {
                    Text("\(model.board.targets.count) sessions").font(.caption2).foregroundStyle(Sig.faint)
                }
            }
            if model.board.targets.isEmpty {
                Text("Nothing is waiting on the desktop right now. An answer still delivers into the focused session.")
                    .font(.caption).foregroundStyle(Sig.faint)
            } else {
                ForEach(model.board.targets) { t in targetRow(t) }
            }
        }
        .cardChrome()
    }

    private func targetRow(_ t: CompanionTarget) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: t.selected ? "largecircle.fill.circle" : "circle")
                    .foregroundStyle(t.selected ? Sig.accent : Sig.faint)
                Text(t.project ?? t.agent).font(.subheadline.weight(.semibold)).foregroundStyle(Sig.text)
                if t.pinned { Image(systemName: "pin.fill").font(.caption2).foregroundStyle(Sig.accent) }
                if t.stale { Text("stale").font(.caption2).foregroundStyle(Sig.warn) }
                Spacer()
                Button { Task { await model.pin(t, !t.pinned) } } label: {
                    Image(systemName: t.pinned ? "pin.slash" : "pin").font(.caption).foregroundStyle(Sig.muted)
                }
            }
            if let q = t.question, !q.isEmpty {
                Text(q).font(.callout).foregroundStyle(t.selected ? Sig.text : Sig.muted)
                    .lineLimit(3).frame(maxWidth: .infinity, alignment: .leading)
            }
            if !t.selected {
                Button { Task { await model.select(t) } } label: {
                    Text("Answer this one").font(.caption.weight(.semibold)).foregroundStyle(Sig.accent)
                }
            } else {
                Text("Your answer lands here").font(.caption2.weight(.bold)).tracking(1).foregroundStyle(Sig.accent)
            }
        }
        .padding(12)
        .background(t.selected ? Sig.s3 : Sig.s2, in: RoundedRectangle(cornerRadius: 11))
        .overlay(RoundedRectangle(cornerRadius: 11)
            .stroke(t.selected ? Sig.accent.opacity(0.5) : Sig.line, lineWidth: 1))
    }

    @ViewBuilder private var answerCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            cardTitle("Your answer", "Hold to speak — transcribed on-device")
            recordButton
            if model.phase == .transcribing || model.phase == .delivering {
                HStack(spacing: 8) { ProgressView().tint(Sig.accent); Text(model.status).font(.subheadline).foregroundStyle(Sig.muted) }
            }
            if model.phase == .review || model.phase == .delivered || model.phase == .failed {
                TextEditor(text: $model.reviewText)
                    .scrollContentBackground(.hidden).frame(minHeight: 90)
                    .font(.body).foregroundStyle(Sig.text)
                    .padding(10).background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(Sig.line, lineWidth: 1))
                Button { Task { await model.send() } } label: {
                    Text(model.phase == .delivering ? "Sending…" : "Send to the coder")
                        .font(.headline).foregroundStyle(.black)
                        .frame(maxWidth: .infinity).padding(.vertical, 13)
                        .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
                }
                .disabled(model.reviewText.trimmingCharacters(in: .whitespaces).isEmpty || model.phase == .delivering)
            }
            if !model.status.isEmpty && model.phase != .transcribing && model.phase != .delivering {
                statusRow("Status", model.status, model.phase == .delivered && model.delivered ? Sig.ok
                          : (model.phase == .failed ? Sig.bad : Sig.muted))
            }
            if !model.egress.isEmpty { egressBadge(model.egress) }
        }
        .cardChrome()
    }

    private var recordButton: some View {
        let recording = model.phase == .recording
        return Button {
            Task { if recording { await model.stopAndTranscribe() } else { await model.startRecording() } }
        } label: {
            HStack(spacing: 10) {
                Image(systemName: recording ? "stop.fill" : "mic.fill")
                Text(recording ? "Stop & transcribe" : "Hold to speak")
            }
            .font(.headline).foregroundStyle(recording ? .white : .black)
            .frame(maxWidth: .infinity).padding(.vertical, 15)
            .background(recording ? Sig.bad : Sig.accent, in: RoundedRectangle(cornerRadius: 14))
        }
        .disabled(model.phase == .transcribing || model.phase == .delivering)
    }

    private var footer: some View {
        Text("Recording + transcription happen on this iPad; only the text you send leaves, to the paired desktop. Delivered only on your explicit Send — never autonomously.")
            .font(.caption).foregroundStyle(Sig.faint).frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: bits

    private func cardTitle(_ t: String, _ sub: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(t).font(.headline).foregroundStyle(Sig.text)
            Text(sub).font(.caption).foregroundStyle(Sig.faint)
        }
    }

    private func field(_ label: String, text: Binding<String>, placeholder: String,
                       keyboard: UIKeyboardType = .default, secure: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label.uppercased()).font(.caption2.weight(.bold)).tracking(1).foregroundStyle(Sig.faint)
            Group {
                if secure { SecureField(placeholder, text: text) }
                else { TextField(placeholder, text: text).keyboardType(keyboard) }
            }
            .textInputAutocapitalization(.never).autocorrectionDisabled()
            .font(.body.monospaced()).foregroundStyle(Sig.text)
            .padding(.horizontal, 12).padding(.vertical, 10)
            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Sig.line, lineWidth: 1))
        }
    }

    private func statusRow(_ k: String, _ v: String, _ color: Color) -> some View {
        HStack(alignment: .top) {
            Text(k).font(.subheadline).foregroundStyle(Sig.muted)
            Spacer()
            Text(v).font(.subheadline.monospaced()).foregroundStyle(color).multilineTextAlignment(.trailing)
        }
    }

    private func egressBadge(_ label: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "arrow.up.right.circle.fill").foregroundStyle(Sig.accent)
            Text(label).font(.caption.monospaced()).foregroundStyle(Sig.muted)
        }
        .padding(.horizontal, 10).padding(.vertical, 8).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s3, in: RoundedRectangle(cornerRadius: 9))
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(Sig.line, lineWidth: 1))
    }
}

private extension View {
    func cardChrome() -> some View {
        self.padding(18).frame(maxWidth: .infinity, alignment: .leading)
            .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
    }
}
