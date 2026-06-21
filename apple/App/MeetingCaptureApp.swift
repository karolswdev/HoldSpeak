import SwiftUI
import AVFoundation
import WhisperKit

// HSM-8-01 — the iPad's on-device meeting-capture loop. Open the app, see your
// recordings, press Record, watch the transcript appear, stop to keep it. Capture
// (Phase 2) + Whisper (Phase 3) + persistence (Phase 4) run fully ON-DEVICE through the
// RuntimeCore `MeetingCapture` view-model; this is the spine the PencilKit notebook
// (HSM-8-02) and review (HSM-8-04) hang off. Nothing leaves the iPad.

@main
struct MeetingCaptureApp: App {
    var body: some Scene {
        WindowGroup { MeetingListView().preferredColorScheme(.dark) }
    }
}

// MARK: - On-device transcription (WhisperKit behind ITranscriber)

final class WhisperKitTranscriber: ITranscriber, @unchecked Sendable {
    private let chunks: [AudioChunk]
    private let model: String
    init(chunks: [AudioChunk], model: String) { self.chunks = chunks; self.model = model }
    func transcribe() async throws -> [Segment] {
        let samples = chunks.flatMap { $0.samples }
        guard samples.count >= 16_000 / 4 else { return [] }
        let floats = samples.map { Float($0) / 32768.0 }
        let whisper = try await WhisperKit(WhisperKitConfig(model: model))
        let results = try await whisper.transcribe(audioArray: floats)
        let clean = WhisperText.clean(results.flatMap { $0.segments }.map(\.text).joined(separator: " "))
        guard !clean.isEmpty else { return [] }
        return [TranscribedSegment(text: clean, startTime: 0, endTime: 0).asContractSegment()]
    }
}

// MARK: - SQLite-backed MeetingStore (Phase-4 persistence)

/// Adapts the Phase-4 `SQLiteStorage` to the capture loop's `MeetingStore`, most-recent
/// first. Falls back to an in-memory store if the DB can't open, so the app still runs.
final class SQLiteMeetingStore: MeetingStore, @unchecked Sendable {
    private let storage: SQLiteStorage
    init() throws {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        storage = try SQLiteStorage(path: docs.appendingPathComponent("meetings.sqlite").path)
    }
    func save(_ meeting: Meeting) throws { try storage.saveMeeting(meeting) }
    func load(id: String) throws -> Meeting? { try storage.loadMeeting(id: id) }
    func list() throws -> [Meeting] {
        try storage.allMeetings().sorted { $0.modifiedAt > $1.modifiedAt }.map(\.meeting)
    }
}

// MARK: - Signal palette

private enum Sig {
    static let bg = Color(hex: 0x0E0F13)
    static let s1 = Color(hex: 0x15171D)
    static let s2 = Color(hex: 0x1C1F27)
    static let line = Color.white.opacity(0.07)
    static let text = Color(hex: 0xF2F3F5)
    static let muted = Color(hex: 0x9BA2B0)
    static let faint = Color(hex: 0x767E8D)
    static let accent = Color(hex: 0xFF6B35)
    static let bad = Color(hex: 0xE5544B)
    static let local = Color(hex: 0x5B8DEF)
}
private extension Color {
    init(hex: UInt) { self.init(.sRGB, red: Double((hex >> 16) & 0xFF)/255,
                                green: Double((hex >> 8) & 0xFF)/255, blue: Double(hex & 0xFF)/255, opacity: 1) }
}

// MARK: - Model

@MainActor
final class CaptureModel: ObservableObject {
    @Published var meetings: [Meeting] = []
    @Published var recording = false
    @Published var transcribing = false
    @Published var liveTranscript = ""
    @Published var error = ""

    private var mc: MeetingCapture?
    private var ticker: Task<Void, Never>?

    init() {
        let store: MeetingStore
        do { store = try SQLiteMeetingStore() }
        catch { self.error = "Store unavailable: \(error)"; return }
        mc = MeetingCapture(capture: AudioCaptureService(), store: store,
                            makeTranscriber: { WhisperKitTranscriber(chunks: $0, model: "base") })
        refresh()
    }

    func refresh() { meetings = mc?.meetings() ?? [] }

    func startRecording() async {
        guard let mc else { return }
        guard await Self.requestMic() else { error = "Microphone permission denied."; return }
        liveTranscript = ""; error = ""
        mc.start()
        if case .failed(let r) = mc.state { error = r; return }
        recording = true
        ticker = Task { [weak self] in
            while !Task.isCancelled, self?.recording == true {
                try? await Task.sleep(nanoseconds: 3_000_000_000)   // window the live transcript
                await mc.tick()
                if case .recording(let t) = mc.state { await MainActor.run { self?.liveTranscript = t } }
            }
        }
    }

    func stopRecording() async {
        guard let mc else { return }
        ticker?.cancel(); ticker = nil
        recording = false; transcribing = true; defer { transcribing = false }
        _ = await mc.stop()
        if case .failed(let r) = mc.state { error = r }
        refresh()
    }

    static func requestMic() async -> Bool {
        await withCheckedContinuation { c in AVAudioApplication.requestRecordPermission { c.resume(returning: $0) } }
    }
}

// MARK: - Meeting list

struct MeetingListView: View {
    @StateObject private var model = CaptureModel()
    @State private var capturing = false

    var body: some View {
        NavigationStack {
            ZStack {
                Sig.bg.ignoresSafeArea()
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        header
                        Button { capturing = true } label: { recordCta }
                        if !model.error.isEmpty { errorNote(model.error) }
                        if model.meetings.isEmpty {
                            Text("No recordings yet. Press record to capture a meeting — it stays on this iPad.")
                                .font(.callout).foregroundStyle(Sig.faint).padding(.top, 8)
                        } else {
                            ForEach(model.meetings, id: \.id) { m in
                                NavigationLink { MeetingDetailView(meeting: m) } label: { meetingRow(m) }
                                    .buttonStyle(.plain)
                            }
                        }
                    }
                    .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
                }
            }
            .navigationDestination(isPresented: $capturing) {
                CaptureView(model: model, done: { capturing = false })
            }
            .toolbar(.hidden, for: .navigationBar)
        }
        .tint(Sig.accent)
        .onAppear { model.refresh() }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("ON-DEVICE").font(.caption2.weight(.bold)).tracking(2).foregroundStyle(Sig.local)
            Text("Meetings").font(.largeTitle.bold()).foregroundStyle(Sig.text)
            Text("Record · transcribe · keep — all on this iPad, nothing leaves.")
                .font(.footnote).foregroundStyle(Sig.faint)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var recordCta: some View {
        HStack(spacing: 10) {
            Image(systemName: "record.circle.fill").font(.title3)
            Text("New recording").font(.headline)
            Spacer()
            Image(systemName: "chevron.right").font(.caption).opacity(0.6)
        }
        .foregroundStyle(.black).padding(.horizontal, 18).padding(.vertical, 15)
        .background(Sig.accent, in: RoundedRectangle(cornerRadius: 14))
    }

    private func meetingRow(_ m: Meeting) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "waveform").foregroundStyle(Sig.local)
            VStack(alignment: .leading, spacing: 3) {
                Text(m.title ?? "Meeting").font(.subheadline.weight(.semibold)).foregroundStyle(Sig.text)
                Text(m.startedAt.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption).foregroundStyle(Sig.faint)
            }
            Spacer()
            Text("\(m.segments.count) segs").font(.caption2).foregroundStyle(Sig.faint)
            Image(systemName: "chevron.right").font(.caption2).foregroundStyle(Sig.faint)
        }
        .padding(14).background(Sig.s1, in: RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Sig.line, lineWidth: 1))
    }

    private func errorNote(_ s: String) -> some View {
        Text(s).font(.caption).foregroundStyle(Sig.bad)
            .padding(12).frame(maxWidth: .infinity, alignment: .leading)
            .background(Sig.bad.opacity(0.1), in: RoundedRectangle(cornerRadius: 10))
    }
}

// MARK: - Capture screen

struct CaptureView: View {
    @ObservedObject var model: CaptureModel
    var done: () -> Void

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            VStack(spacing: 18) {
                HStack {
                    Text(model.recording ? "Recording" : (model.transcribing ? "Transcribing…" : "Ready"))
                        .font(.title3.bold()).foregroundStyle(model.recording ? Sig.accent : Sig.text)
                    if model.recording { recordingDot }
                    Spacer()
                    Button("Done") { done() }.foregroundStyle(Sig.muted)
                }
                transcriptCard
                recordButton
            }
            .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
        }
        .toolbar(.hidden, for: .navigationBar)
    }

    private var recordingDot: some View {
        Circle().fill(Sig.bad).frame(width: 10, height: 10)
            .shadow(color: Sig.bad.opacity(0.8), radius: 5)
    }

    private var transcriptCard: some View {
        ScrollView {
            Text(model.liveTranscript.isEmpty
                 ? (model.recording ? "Listening… your words appear here on-device." : "Press record to start.")
                 : model.liveTranscript)
                .font(.title3).foregroundStyle(model.liveTranscript.isEmpty ? Sig.faint : Sig.text)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(18).frame(maxWidth: .infinity, minHeight: 220, alignment: .topLeading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
    }

    private var recordButton: some View {
        Button {
            Task { if model.recording { await model.stopRecording(); done() } else { await model.startRecording() } }
        } label: {
            HStack(spacing: 10) {
                Image(systemName: model.recording ? "stop.fill" : "record.circle")
                Text(model.recording ? "Stop & keep" : "Record")
            }
            .font(.headline).foregroundStyle(model.recording ? .white : .black)
            .frame(maxWidth: .infinity).padding(.vertical, 16)
            .background(model.recording ? Sig.bad : Sig.accent, in: RoundedRectangle(cornerRadius: 16))
        }
        .disabled(model.transcribing)
    }
}

// MARK: - Meeting detail (reopen-intact)

struct MeetingDetailView: View {
    let meeting: Meeting
    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text(meeting.title ?? "Meeting").font(.largeTitle.bold()).foregroundStyle(Sig.text)
                    Text(meeting.startedAt.formatted(date: .complete, time: .shortened))
                        .font(.caption).foregroundStyle(Sig.faint)
                    if meeting.segments.isEmpty {
                        Text("No speech was transcribed.").font(.callout).foregroundStyle(Sig.faint)
                    } else {
                        ForEach(Array(meeting.segments.enumerated()), id: \.offset) { _, seg in
                            Text(seg.text).font(.body).foregroundStyle(Sig.text)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(12).background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
                        }
                    }
                }
                .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
    }
}
