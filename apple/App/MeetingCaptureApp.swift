import SwiftUI
import AVFoundation
import WhisperKit
import PencilKit
import Vision
import os
import UIKit
import MarkdownUI

// HSM-8-01 — the iPad's on-device meeting-capture loop. Open the app, see your
// recordings, press Record, watch the transcript appear, stop to keep it. Capture
// (Phase 2) + Whisper (Phase 3) + persistence (Phase 4) run fully ON-DEVICE through the
// RuntimeCore `MeetingCapture` view-model; this is the spine the PencilKit notebook
// (HSM-8-02) and review (HSM-8-04) hang off. Nothing leaves the iPad.

@main
struct MeetingCaptureApp: App {
    var body: some Scene {
        WindowGroup {
            // HS_DEMO_NOTEBOOK opens straight onto the notebook surface for a
            // screenshot run (no mic/taps needed); the real entry is the meeting list.
            if ProcessInfo.processInfo.environment["HS_DEMO_NOTEBOOK"] != nil {
                DemoNotebookView().preferredColorScheme(.dark)
            } else {
                MeetingListView().preferredColorScheme(.dark)
            }
        }
    }
}

/// A standalone notebook for screenshot-verification of the rich surface (tool picker +
/// pages), over an in-memory store.
struct DemoNotebookView: View {
    @StateObject private var notes = NotebookModel(store: InMemoryNotebookStore(), meetingID: "demo")
    var body: some View {
        ZStack {
            Color(.sRGB, red: 0x0E/255, green: 0x0F/255, blue: 0x13/255, opacity: 1).ignoresSafeArea()
            VStack(alignment: .leading, spacing: 14) {
                Text("NOTEBOOK").font(.caption.weight(.bold)).tracking(2)
                    .foregroundStyle(Color(.sRGB, red: 0x5B/255, green: 0x8D/255, blue: 0xEF/255, opacity: 1))
                Text("Handwritten notes").font(.largeTitle.bold()).foregroundStyle(.white)
                NotebookView(model: notes, editable: true)
            }
            .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
        }
    }
}

final class InMemoryNotebookStore: NotebookStore, @unchecked Sendable {
    private var blobs: [String: Data] = [:]
    func saveNotebook(_ data: Data, meetingID: String) throws { blobs[meetingID] = data }
    func loadNotebook(meetingID: String) throws -> Data? { blobs[meetingID] }
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

// MARK: - Notebook persistence (HSM-8-02) — a meeting-keyed blob behind the seam

/// Backs the `NotebookStore` seam with one JSON blob per meeting in the app container.
/// The view never touches files — it goes through the `Notebook` view-model.
final class FileNotebookStore: NotebookStore, @unchecked Sendable {
    private let dir: URL
    init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        dir = docs.appendingPathComponent("notebooks", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }
    private func url(_ id: String) -> URL { dir.appendingPathComponent("\(id).json") }
    func saveNotebook(_ data: Data, meetingID: String) throws { try data.write(to: url(meetingID), options: .atomic) }
    func loadNotebook(meetingID: String) throws -> Data? {
        let u = url(meetingID)
        return FileManager.default.fileExists(atPath: u.path) ? try Data(contentsOf: u) : nil
    }
}

/// File-backed `LinkStore` (HSM-8-03) — a meeting-keyed JSON blob of transcript links.
final class FileLinkStore: LinkStore, @unchecked Sendable {
    private let dir: URL
    init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        dir = docs.appendingPathComponent("links", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }
    private func url(_ id: String) -> URL { dir.appendingPathComponent("\(id).json") }
    func saveLinks(_ data: Data, meetingID: String) throws { try data.write(to: url(meetingID), options: .atomic) }
    func loadLinks(meetingID: String) throws -> Data? {
        let u = url(meetingID)
        return FileManager.default.fileExists(atPath: u.path) ? try Data(contentsOf: u) : nil
    }
}

// MARK: - PencilKit canvas (the magic pencil)

/// A PencilKit canvas with the system tool picker (pen / highlighter / eraser). Strokes
/// flow back through `drawing`; stroke capture stays on PencilKit's own path so it never
/// fights transcription for the main thread.
struct PencilCanvas: UIViewRepresentable {
    @Binding var drawing: PKDrawing
    var editable: Bool

    func makeUIView(context: Context) -> PKCanvasView {
        let cv = PKCanvasView()
        cv.drawing = drawing
        cv.backgroundColor = .clear
        cv.isOpaque = false
        cv.drawingPolicy = .anyInput               // finger OR pencil (the sim has no pencil)
        cv.delegate = context.coordinator
        if editable {
            let picker = context.coordinator.toolPicker
            picker.setVisible(true, forFirstResponder: cv)
            picker.addObserver(cv)
            DispatchQueue.main.async { cv.becomeFirstResponder() }
        } else {
            cv.isUserInteractionEnabled = false
        }
        return cv
    }

    func updateUIView(_ cv: PKCanvasView, context: Context) {
        if cv.drawing != drawing { cv.drawing = drawing }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, PKCanvasViewDelegate {
        let parent: PencilCanvas
        let toolPicker = PKToolPicker()
        init(_ parent: PencilCanvas) { self.parent = parent }
        func canvasViewDrawingDidChange(_ cv: PKCanvasView) { parent.drawing = cv.drawing }
    }
}

@MainActor
final class NotebookModel: ObservableObject {
    @Published var pages: [PKDrawing]
    @Published var current = 0
    private let notebook: Notebook

    init(store: NotebookStore, meetingID: String) {
        notebook = Notebook(store: store, meetingID: meetingID)
        let loaded = notebook.reload().compactMap { try? PKDrawing(data: $0) }
        pages = loaded.isEmpty ? [PKDrawing()] : loaded
    }

    func page(_ i: Int) -> Binding<PKDrawing> {
        Binding(get: { self.pages[i] }, set: { self.pages[i] = $0; self.save() })
    }
    func addPage() { pages.append(PKDrawing()); current = pages.count - 1; save() }
    func save() { try? notebook.save(pages: pages.map { $0.dataRepresentation() }) }
    var hasInk: Bool { pages.contains { !$0.strokes.isEmpty } }
}

// MARK: - Notebook surface

struct NotebookView: View {
    @ObservedObject var model: NotebookModel
    var editable: Bool

    var body: some View {
        VStack(spacing: 10) {
            HStack(spacing: 10) {
                Text("Page \(model.current + 1) of \(model.pages.count)")
                    .font(.caption.weight(.medium)).foregroundStyle(SigN.muted)
                Spacer()
                if editable {
                    Button { if model.current > 0 { model.current -= 1 } } label: {
                        Image(systemName: "chevron.left").foregroundStyle(model.current > 0 ? SigN.accent : SigN.faint)
                    }.disabled(model.current == 0)
                    Button { if model.current < model.pages.count - 1 { model.current += 1 } } label: {
                        Image(systemName: "chevron.right").foregroundStyle(model.current < model.pages.count - 1 ? SigN.accent : SigN.faint)
                    }.disabled(model.current == model.pages.count - 1)
                    Button { model.addPage() } label: {
                        HStack(spacing: 4) { Image(systemName: "plus"); Text("Page") }
                            .font(.caption.weight(.semibold)).foregroundStyle(SigN.accent)
                    }
                }
            }
            PencilCanvas(drawing: editable ? model.page(model.current) : .constant(model.pages[model.current]),
                         editable: editable)
                .frame(maxWidth: .infinity, minHeight: 360)
                .background(SigN.s1, in: RoundedRectangle(cornerRadius: 14))
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(SigN.line, lineWidth: 1))
        }
    }
}

/// A tiny palette mirror so the notebook views compile alongside the (fileprivate) one.
private enum SigN {
    static let s1 = Color(.sRGB, red: 0x15/255, green: 0x17/255, blue: 0x1D/255, opacity: 1)
    static let line = Color.white.opacity(0.07)
    static let muted = Color(.sRGB, red: 0x9B/255, green: 0xA2/255, blue: 0xB0/255, opacity: 1)
    static let faint = Color(.sRGB, red: 0x76/255, green: 0x7E/255, blue: 0x8D/255, opacity: 1)
    static let accent = Color(.sRGB, red: 0xFF/255, green: 0x6B/255, blue: 0x35/255, opacity: 1)
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
    @Published var notebook: NotebookModel?      // the live meeting's notes (HSM-8-02)
    @Published var markCount = 0                  // moments flagged this meeting (HSM-8-03)

    let notebookStore: NotebookStore = FileNotebookStore()
    private let linkStore: LinkStore = FileLinkStore()
    private var linker: TranscriptLinker?
    private var recordStart: Date?
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
        markCount = 0; recordStart = Date()
        if let id = mc.currentID {
            notebook = NotebookModel(store: notebookStore, meetingID: id)
            linker = TranscriptLinker(store: linkStore, meetingID: id)
        }
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
        notebook?.save()           // final flush of the meeting's notes
        _ = await mc.stop()
        if case .failed(let r) = mc.state { error = r }
        refresh()
    }

    /// One-gesture "mark this moment" at the current elapsed time (HSM-8-03). A linked
    /// anchor with no note — flag a live meeting at speed.
    func mark() {
        guard let linker, let start = recordStart else { return }
        try? linker.markMoment(at: Date().timeIntervalSince(start), label: "★")
        markCount = linker.links().count
    }

    static func requestMic() async -> Bool {
        await withCheckedContinuation { c in AVAudioApplication.requestRecordPermission { c.resume(returning: $0) } }
    }
}

// MARK: - Voice correction capture (HSM-14-07)

/// Thread-safe collector for streamed audio chunks (capture thread → main).
final class ChunkSink: @unchecked Sendable {
    private let q = DispatchQueue(label: "voice.chunks")
    private var chunks: [AudioChunk] = []
    func add(_ c: AudioChunk) { q.sync { chunks.append(c) } }
    func drain() -> [AudioChunk] { q.sync { chunks } }
    func reset() { q.sync { chunks.removeAll() } }
}

/// A short on-device voice capture for a correction: record the mic, transcribe the clip with
/// WhisperKit. No meeting is created — fully local, just the user's words.
@MainActor
final class VoiceCaptureState: ObservableObject {
    @Published var recording = false
    @Published var transcribing = false
    @Published var text = ""
    @Published var error = ""
    private let capture = AudioCaptureService()
    private let sink = ChunkSink()

    func start() async {
        guard await CaptureModel.requestMic() else { error = "Microphone permission denied."; return }
        error = ""; text = ""; sink.reset()
        do { try capture.start { [sink] chunk in sink.add(chunk) }; recording = true }
        catch { self.error = "Couldn't start the mic: \(error)" }
    }

    func stopAndTranscribe() async {
        try? capture.stop()
        recording = false
        transcribing = true; defer { transcribing = false }
        do {
            let segs = try await WhisperKitTranscriber(chunks: sink.drain(), model: "base").transcribe()
            let said = segs.map(\.text).joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
            if said.isEmpty { self.error = "Didn't catch that — try again, or type it." } else { text = said }
        } catch { self.error = "Couldn't transcribe: \(error)" }
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
    @State private var pane: Pane = .transcript
    enum Pane: String, CaseIterable { case transcript = "Transcript", notes = "Notes" }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            VStack(spacing: 16) {
                HStack {
                    Text(model.recording ? "Recording" : (model.transcribing ? "Transcribing…" : "Ready"))
                        .font(.title3.bold()).foregroundStyle(model.recording ? Sig.accent : Sig.text)
                    if model.recording { recordingDot }
                    Spacer()
                    Button("Done") { done() }.foregroundStyle(Sig.muted)
                }
                Picker("", selection: $pane) {
                    ForEach(Pane.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)

                if pane == .transcript {
                    transcriptCard
                } else {
                    notesPane
                }
                if model.recording { markRow }
                recordButton
            }
            .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
        }
        .toolbar(.hidden, for: .navigationBar)
    }

    @ViewBuilder private var notesPane: some View {
        if let nb = model.notebook {
            NotebookView(model: nb, editable: true)   // ink + transcript coexist; strokes persist
        } else {
            VStack(spacing: 8) {
                Image(systemName: "pencil.and.scribble").font(.largeTitle).foregroundStyle(Sig.local)
                Text("Press Record to start a meeting, then take handwritten notes here — they save with it.")
                    .font(.callout).foregroundStyle(Sig.faint).multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity, minHeight: 360)
            .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Sig.line, lineWidth: 1))
        }
    }

    private var recordingDot: some View {
        Circle().fill(Sig.bad).frame(width: 10, height: 10)
            .shadow(color: Sig.bad.opacity(0.8), radius: 5)
    }

    private var markRow: some View {
        Button { model.mark() } label: {
            HStack(spacing: 8) {
                Image(systemName: "star.circle.fill")
                Text("Mark this moment")
                Spacer()
                if model.markCount > 0 { Text("\(model.markCount)").font(.caption.weight(.bold)) }
            }
            .font(.subheadline.weight(.semibold)).foregroundStyle(Sig.local)
            .padding(.horizontal, 14).padding(.vertical, 11)
            .background(Sig.local.opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Sig.local.opacity(0.35), lineWidth: 1))
        }
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

// MARK: - On-device artifact generation + review (HSM-8-04)

@MainActor
final class MeetingReviewState: ObservableObject {
    let meeting: Meeting
    @Published var artifacts: [Artifact] = []
    @Published var profile: MIRProfile
    @Published var generating = false
    @Published var note = ""
    @Published var correctingId: String?     // HSM-14-07 — the card regenerating from a voice correction

    private let storage: SQLiteStorage?
    private let marks: [Double]              // hand-flagged moments (HSM-8-03) — weight extraction

    init(meeting: Meeting) {
        self.meeting = meeting
        self.profile = meeting.routingProfile
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        storage = try? SQLiteStorage(path: docs.appendingPathComponent("meetings.sqlite").path)
        marks = TranscriptLinker(store: FileLinkStore(), meetingID: meeting.id).links().map(\.anchorTime)
        load()
    }

    func load() { artifacts = (try? storage?.loadArtifacts(meetingId: meeting.id)) ?? [] }

    var groups: [ArtifactGroup] { ReviewModel(artifacts: artifacts).grouped(profile: profile) }
    var pendingCount: Int { ReviewModel(artifacts: artifacts).pendingCount }

    /// Generate the meeting's artifacts ON-DEVICE (Mode A): the MIR profile picks the
    /// types, the local GGUF model drafts each, and they persist as proposals.
    /// The on-device context CEILING — what we'd *like* (16K ≈ ~80 min of speech).
    /// HSM-8-08 lowers it to what THIS device can actually afford (the KV-cache is RAM),
    /// and HSM-8-07 chunks anything that still won't fit — so we never gamble on memory
    /// regardless of meeting length.
    private static let contextCeiling = 16_384

    /// Memory headroom before the iOS jetsam limit, with a conservative fallback.
    private static func availableMemoryBytes() -> Int {
        let avail = Int(os_proc_available_memory())
        return avail > 0 ? avail : Int(ProcessInfo.processInfo.physicalMemory / 2)
    }

    // Pullable diagnostics for the generation path (Documents/gen-debug.log).
    static func glogReset() { try? FileManager.default.removeItem(at: glogURL()) }
    static func glogURL() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("gen-debug.log")
    }
    static func glog(_ s: String) {
        NSLog("HSGEN: \(s)")
        let url = glogURL(); let line = s + "\n"
        if let h = try? FileHandle(forWritingTo: url) { h.seekToEndOfFile(); if let d = line.data(using: .utf8) { h.write(d) }; try? h.close() }
        else { try? line.write(to: url, atomically: true, encoding: .utf8) }
    }

    func generate() async {
        Self.glogReset()
        let chars = meeting.segments.map(\.text).joined(separator: " ").count
        Self.glog("segments=\(meeting.segments.count) chars=\(chars) tokens≈\(chars / 4)")
        guard !meeting.segments.isEmpty else {
            note = "No transcript to analyze — this recording saved no text."; Self.glog("ABORT empty"); return
        }
        guard let modelPath = Self.localGGUF() else {
            note = "No on-device model found. Push a .gguf to the app's Documents first."; Self.glog("ABORT no model"); return
        }
        generating = true; defer { generating = false }

        // Regenerate cleanly: drop any PRIOR model artifacts so a re-run replaces rather
        // than piles up (ids are fresh UUIDs each run). The handwritten ink is preserved.
        for a in artifacts where a.pluginId == "holdspeak.mobile.intelligence" {
            try? storage?.deleteArtifact(id: a.id, at: Date())
        }
        load()

        // HSM-8-08 — size the context to THIS device, never a blind constant.
        let modelBytes = ((try? FileManager.default.attributesOfItem(atPath: modelPath))?[.size] as? Int) ?? 0
        let avail = Self.availableMemoryBytes()
        let context = OnDeviceBudget.contextTokens(
            availableBytes: avail, modelBytes: modelBytes,
            marginBytes: 768 * 1_048_576, ceiling: Self.contextCeiling)
        let windowBudget = OnDeviceBudget.windowTokens(context: context)
        Self.glog("availMB=\(avail / 1_048_576) modelMB=\(modelBytes / 1_048_576) context=\(context) window=\(windowBudget)")

        let transcript = Transcript(meetingId: meeting.id, segments: meeting.segments,
                                    transcriptHash: "ondevice-\(meeting.segments.count)")
        let types = marks.isEmpty
            ? (MIRRouter.baseEmphasis[profile] ?? [.decisions, .actionItems, .requirements])
            : InkEmphasis.routedTypes(profile: profile, transcript: transcript, marks: marks)
        Self.glog("types=\(types.map(\.rawValue))")

        // HSM-8-07 — chunk a long meeting into length-bounded windows; a short one is a
        // single window (the whole transcript). One loop drives both.
        let chunk = OnDeviceBudget.needsChunking(
            transcriptTokens: OnDeviceBudget.transcriptTokens(transcript.segments), windowTokens: windowBudget)
        let windows = chunk
            ? TranscriptWindowing.windows(transcript.segments, maxTokens: windowBudget)
            : [transcript.segments]
        Self.glog("chunk=\(chunk) windows=\(windows.count) sizes=\(windows.map { $0.count }) tokens=\(windows.map { OnDeviceBudget.transcriptTokens($0) })")

        var all: [Artifact] = []
        var lastError = ""
        for (wi, segs) in windows.enumerated() {
            let sub = Transcript(meetingId: transcript.meetingId, segments: segs,
                                 transcriptHash: "\(transcript.transcriptHash)#w\(wi)")
            for type in types {
                note = chunk ? "Long meeting — pass \(wi + 1)/\(windows.count): \(artifactTypeLabel(type))…"
                             : "Generating \(artifactTypeLabel(type))…"
                do {
                    // FRESH provider per inference — a clean llama context every time. The
                    // FIRST call always works; reusing one instance accumulates KV (the
                    // 2nd+ call starves → noJSON) and clearing it mid-flight races the
                    // decoder (crash). A new instance is the deterministic clean slate, and
                    // it also dodges LLM.swift's `isAvailable` getting stuck after a bad run
                    // (the "had to restart the app" symptom). It deinits at scope exit, so
                    // only one llama context is ever resident.
                    let provider = try LlamaProvider(modelPath: modelPath, maxTokenCount: Int32(context))
                    let engine = ArtifactGenerationEngine(provider: provider, maxAttempts: 2)
                    let a = try await engine.generate(type, from: sub)
                    all.append(a)
                    if !chunk { try? storage?.saveArtifact(a); load() }   // stream the single pass
                    Self.glog("w\(wi) ok \(type.rawValue)")
                } catch {
                    lastError = "\(error)"; Self.glog("w\(wi) FAIL \(type.rawValue): \(error)")
                }
            }
        }
        let merged = ArtifactMerge.dedup(all)
        if chunk { for a in merged { try? storage?.saveArtifact(a) }; load() }
        Self.glog("done produced=\(merged.count)")
        note = merged.isEmpty
            ? "The model produced nothing." + (lastError.isEmpty ? "" : " (\(lastError))")
            : ""
    }

    func approve(_ id: String) {
        try? ReviewModel(artifacts: artifacts, store: storage).approve(id); load()
    }
    func reject(_ id: String) {
        try? ReviewModel(artifacts: artifacts, store: storage).reject(id); load()
    }

    /// HSM-14-07 — apply a spoken correction: re-route the artifact + the user's words back to
    /// the local model and **regenerate it in place** (same id → the card morphs, no duplicate).
    /// Propose-and-confirm: the corrected version returns as a `.draft` the user re-approves.
    func correct(_ artifact: Artifact, spoken: String) async {
        let spoken = spoken.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !spoken.isEmpty else { return }
        guard let modelPath = Self.localGGUF() else { note = "No on-device model found."; return }
        withAnimation(.easeInOut(duration: 0.35)) { correctingId = artifact.id }
        defer { withAnimation(.easeInOut(duration: 0.45)) { correctingId = nil } }
        let modelBytes = ((try? FileManager.default.attributesOfItem(atPath: modelPath))?[.size] as? Int) ?? 0
        let context = OnDeviceBudget.contextTokens(
            availableBytes: Self.availableMemoryBytes(), modelBytes: modelBytes,
            marginBytes: 768 * 1_048_576, ceiling: Self.contextCeiling)
        do {
            let provider = try LlamaProvider(modelPath: modelPath, maxTokenCount: Int32(context))
            let transcript = Transcript(meetingId: meeting.id, segments: meeting.segments,
                                        transcriptHash: "ondevice-\(meeting.segments.count)")
            let fixed = try await ArtifactCorrection.corrected(
                original: artifact, correction: spoken, transcript: transcript,
                provider: provider, idGenerator: { artifact.id })   // replace in place
            try? storage?.saveArtifact(fixed)
            withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { load() }
        } catch { note = "Couldn't apply the correction: \(error)" }
    }

    var hasInkArtifacts: Bool { artifacts.contains { $0.pluginId == "holdspeak.mobile.ink" } }
    var hasGeneratedArtifacts: Bool { artifacts.contains { $0.pluginId == "holdspeak.mobile.intelligence" } }

    /// HSM-8-06 — the magic pencil, involved. Render each handwritten page to an actual
    /// IMAGE attached to the meeting (the literal scribble — arrows, sketches, stars),
    /// AND recognize the handwriting on-device (Vision) into a text note. Both are
    /// proposals you review; nothing is auto-committed.
    func promoteNotes() async {
        let pages = NotebookModel(store: FileNotebookStore(), meetingID: meeting.id).pages
        let inked = pages.filter { !$0.strokes.isEmpty }
        guard !inked.isEmpty else { note = "No handwritten notes on this meeting yet."; return }
        generating = true; note = "Reading your handwriting on-device…"; defer { generating = false }
        let dir = Self.inkDir()
        for (i, drawing) in inked.enumerated() {
            guard let image = Self.render(drawing) else { continue }
            // 1) attach the literal ink as an image artifact
            if let png = image.pngData() {
                let url = dir.appendingPathComponent("\(meeting.id)-\(i).png")
                try? png.write(to: url, options: .atomic)
                let imageArtifact = Artifact(
                    id: "ink-img-\(meeting.id)-\(i)", meetingId: meeting.id, artifactType: .diagram,
                    title: "Handwritten note \(i + 1)", bodyMarkdown: "",
                    structuredJson: .object(["source": .string("ink"), "image_path": .string(url.path)]),
                    confidence: 1, status: .draft, pluginId: "holdspeak.mobile.ink",
                    pluginVersion: HoldSpeakContracts.contractVersion,
                    sources: [ArtifactSource(sourceType: "handwriting", sourceRef: "notebook")])
                try? storage?.saveArtifact(imageArtifact); load()
            }
            // 2) recognize the handwriting → a text note proposal (best-effort; the image
            //    above is already attached, so OCR never blocks the owner's ask)
            let text = await Self.recognize(image)
            if !text.isEmpty {
                let recognized = InkPromoter.artifact(text: text, type: .actionItems,
                                                      meetingID: meeting.id, id: "ink-txt-\(meeting.id)-\(i)")
                try? storage?.saveArtifact(recognized); load()
            }
        }
        note = ""
    }

    private static func inkDir() -> URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let dir = docs.appendingPathComponent("ink-images", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }


    /// Render a PencilKit page to a light-background image (dark ink reads best for the
    /// eye and Vision). Defensive: a sprawling canvas's bounds could be huge — clamp the
    /// pixel budget so the renderer can't OOM (the crash on first try).
    private static func render(_ drawing: PKDrawing) -> UIImage? {
        var bounds = drawing.bounds
        guard bounds.width > 1, bounds.height > 1, bounds.width.isFinite, bounds.height.isFinite else { return nil }
        bounds = bounds.insetBy(dx: -24, dy: -24)
        // Fit into ~6 megapixels at most, scaling down a large drawing rather than
        // allocating a giant bitmap.
        let budget: CGFloat = 6_000_000
        let scale = min(2.0, (budget / (bounds.width * bounds.height)).squareRoot())
        let ink = drawing.image(from: bounds, scale: scale)
        let format = UIGraphicsImageRendererFormat.default()
        format.scale = scale
        format.opaque = true
        let renderer = UIGraphicsImageRenderer(size: bounds.size, format: format)
        return renderer.image { ctx in
            UIColor(white: 0.97, alpha: 1).setFill()
            ctx.fill(CGRect(origin: .zero, size: bounds.size))
            ink.draw(in: CGRect(origin: .zero, size: bounds.size))
        }
    }

    /// On-device handwriting recognition (Vision). Runs in a **detached** task so the
    /// synchronous `perform` (and its results read) never cross the main actor — the
    /// actor-crossing was the crash. `nonisolated` + a fresh request per call.
    nonisolated private static func recognize(_ image: UIImage) async -> String {
        guard let cg = image.cgImage else { return "" }
        return await Task.detached(priority: .userInitiated) {
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true
            do {
                try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
                let lines = (request.results)?.compactMap { $0.topCandidates(1).first?.string } ?? []
                return lines.joined(separator: "\n")
            } catch {
                return ""
            }
        }.value
    }

    static func localGGUF() -> String? {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else { return nil }
        return ((try? FileManager.default.contentsOfDirectory(at: docs, includingPropertiesForKeys: nil)) ?? [])
            .filter { $0.pathExtension.lowercased() == "gguf" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }.first?.path
    }
}

private func artifactTypeLabel(_ t: ArtifactType) -> String {
    t.rawValue.replacingOccurrences(of: "_", with: " ").capitalized
}

/// Per-type accent (HSM-14 Tactile Sheets — each artifact type reads at a glance).
private func artifactTint(_ t: ArtifactType) -> Color {
    switch t {
    case .decisions, .decisionAnnouncement: return Sig.ok
    case .actionItems, .milestonePlan: return Sig.accent
    case .riskRegister, .incidentTimeline, .runbookDelta: return Sig.warn
    case .requirements, .scopeReview, .dependencyMap: return Sig.local
    default: return Sig.local
    }
}
private func artifactGlyph(_ t: ArtifactType) -> String {
    switch t {
    case .decisions, .decisionAnnouncement: return "checkmark.seal.fill"
    case .actionItems: return "bolt.fill"
    case .riskRegister: return "exclamationmark.triangle.fill"
    case .incidentTimeline: return "clock.badge.exclamationmark.fill"
    case .requirements: return "list.bullet.rectangle.fill"
    case .adr: return "doc.text.fill"
    case .diagram, .dependencyMap: return "rectangle.3.group.fill"
    case .milestonePlan: return "flag.checkered"
    case .customerSignals, .stakeholderUpdate: return "person.2.fill"
    default: return "sparkles"
    }
}
/// A light tactile tap (HSM-14 — the app should feel hand-driven).
private func tactile(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
    UIImpactFeedbackGenerator(style: style).impactOccurred()
}

/// A clean one-glance teaser for a card: strip the common Markdown syntax so the preview
/// reads as plain prose (the full doc renders the real Markdown on tap).
private func plainPreview(_ md: String) -> String {
    var s = md
    for token in ["**", "__", "`", "#", ">", "- ", "* "] { s = s.replacingOccurrences(of: token, with: "") }
    return s.replacingOccurrences(of: "\n", with: " ").trimmingCharacters(in: .whitespacesAndNewlines)
}

/// Wraps an artifact so it can drive a `.sheet(item:)` without retroactive Identifiable.
struct OpenDoc: Identifiable { let id = UUID(); let artifact: Artifact; let ink: UIImage? }

/// HSM-14-03 — the Tactile Sheets artifact card: gesture-first + ALIVE. Swipe tilts/scales
/// the card and pops a bouncing action badge (left → approve, right → dismiss, haptic on
/// commit); tap opens the full readable/copyable/shareable document; cards spring + stagger
/// in on appear. Tinted by type, elevated. Wired to the live review actions.
struct SwipeableArtifactCard: View {
    let artifact: Artifact
    let ink: UIImage?
    var index: Int = 0
    var regenerating: Bool = false
    let onApprove: () -> Void
    let onDismiss: () -> Void
    let onOpen: () -> Void
    @State private var dragX: CGFloat = 0
    @State private var appeared = false
    @State private var pressed = false
    @State private var shimmerX: CGFloat = -0.7

    private var actionable: Bool { artifact.status == .draft || artifact.status == .needsReview }
    private var tint: Color { artifactTint(artifact.artifactType) }
    private var swipeProgress: CGFloat { min(abs(dragX) / 100, 1) }

    var body: some View {
        ZStack {
            HStack {
                sideAction("xmark.circle.fill", "Dismiss", Sig.bad, active: dragX > 55, lead: true)
                Spacer()
                sideAction("checkmark.circle.fill", "Approve", Sig.ok, active: dragX < -55, lead: false)
            }
            face
                .blur(radius: regenerating ? 3 : 0)
                .overlay { if regenerating { regeneratingOverlay } }
                .offset(x: regenerating ? 0 : dragX)
                .rotationEffect(.degrees(regenerating ? 0 : Double(dragX) / 26), anchor: .bottom)
                .scaleEffect(pressed ? 0.97 : 1 - swipeProgress * 0.05)
                .gesture(actionable && !regenerating ? drag : nil)
                .onTapGesture {
                    guard !regenerating else { return }
                    tactile()
                    withAnimation(.spring(response: 0.22, dampingFraction: 0.55)) { pressed = true }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.13) {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { pressed = false }
                        onOpen()
                    }
                }
                .animation(.easeInOut(duration: 0.35), value: regenerating)
        }
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 22)
        .scaleEffect(appeared ? 1 : 0.95, anchor: .top)
        .onAppear {
            withAnimation(.spring(response: 0.55, dampingFraction: 0.74).delay(Double(index) * 0.06)) { appeared = true }
        }
        .onChange(of: regenerating) { _, on in
            if on {
                shimmerX = -0.7
                withAnimation(.linear(duration: 1.15).repeatForever(autoreverses: false)) { shimmerX = 1.3 }
            }
        }
    }

    /// HSM-14-07 — the card "re-thinking" with the user's spoken note: a tint shimmer sweep,
    /// a glowing border, and a pulsing sparkle badge, over the blurred old content. The
    /// corrected content is revealed underneath when the overlay fades.
    @ViewBuilder private var regeneratingOverlay: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Sig.bg.opacity(0.55))
            GeometryReader { geo in
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(LinearGradient(colors: [.clear, tint.opacity(0.5), .clear], startPoint: .leading, endPoint: .trailing))
                    .frame(width: geo.size.width * 0.55)
                    .offset(x: shimmerX * geo.size.width)
                    .blendMode(.plusLighter)
            }
            VStack(spacing: 9) {
                Image(systemName: "sparkles").font(.system(size: 24, weight: .bold)).foregroundStyle(tint)
                    .symbolEffect(.variableColor.iterative.reversing, options: .repeating)
                Text("Re-thinking with your note…").font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.text)
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(tint, lineWidth: 2)
            .shadow(color: tint.opacity(0.85), radius: 11))
        .transition(.opacity.combined(with: .scale(scale: 1.03)))
    }

    private var drag: some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { g in withAnimation(.interactiveSpring()) { dragX = max(-170, min(170, g.translation.width)) } }
            .onEnded { g in
                if g.translation.width < -100 { tactile(.heavy); onApprove() }
                else if g.translation.width > 100 { tactile(.heavy); onDismiss() }
                withAnimation(.spring(response: 0.4, dampingFraction: 0.62)) { dragX = 0 }
            }
    }

    private var face: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 11) {
                ZStack {
                    RoundedRectangle(cornerRadius: 11, style: .continuous).fill(tint.opacity(0.18))
                    Image(systemName: artifactGlyph(artifact.artifactType)).font(.system(size: 15, weight: .bold)).foregroundStyle(tint)
                }.frame(width: 36, height: 36)
                VStack(alignment: .leading, spacing: 2) {
                    Text(artifactTypeLabel(artifact.artifactType)).font(.system(size: 12, weight: .heavy)).tracking(0.4).foregroundStyle(tint)
                    Text(artifact.title).font(.system(size: 16.5, weight: .bold)).foregroundStyle(Sig.text).lineLimit(2)
                }
                Spacer(minLength: 4)
                statusView
            }
            if let ink {
                Image(uiImage: ink).resizable().scaledToFit().frame(maxHeight: 220).frame(maxWidth: .infinity)
                    .background(Color.white, in: RoundedRectangle(cornerRadius: 10))
            }
            if !artifact.bodyMarkdown.isEmpty {
                Text(plainPreview(artifact.bodyMarkdown))
                    .font(.system(size: 14)).foregroundStyle(Sig.muted).lineSpacing(2).lineLimit(3)
            }
            HStack(spacing: 6) {
                if actionable {
                    Image(systemName: "hand.draw.fill").font(.system(size: 11, weight: .bold))
                    Text("swipe → approve  ·  ← dismiss").font(.system(size: 12, weight: .semibold))
                }
                Spacer()
                Image(systemName: "arrow.up.left.and.arrow.down.right").font(.system(size: 11, weight: .bold))
                Text("Open").font(.system(size: 12, weight: .heavy))
            }
            .foregroundStyle(Sig.faint.opacity(0.9))
        }
        .padding(15)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Sig.line, lineWidth: 1))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous)
            .stroke((dragX < 0 ? Sig.ok : Sig.bad).opacity(0.7 * swipeProgress), lineWidth: 2))
        .shadow(color: .black.opacity(0.32 + swipeProgress * 0.1), radius: 14 + swipeProgress * 8, x: 0, y: 8)
    }

    @ViewBuilder private var statusView: some View {
        switch artifact.status {
        case .accepted: pill("Approved", Sig.ok)
        case .rejected: pill("Dismissed", Sig.faint)
        default: Image(systemName: "circle.dashed").font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.faint)
        }
    }
    private func pill(_ t: String, _ c: Color) -> some View {
        Text(t).font(.system(size: 11, weight: .heavy)).foregroundStyle(c)
            .padding(.horizontal, 9).padding(.vertical, 4).background(c.opacity(0.14), in: Capsule())
    }
    private func sideAction(_ sys: String, _ label: String, _ c: Color, active: Bool, lead: Bool) -> some View {
        VStack(spacing: 5) {
            Image(systemName: sys).font(.system(size: 30, weight: .heavy)).foregroundStyle(c)
                .symbolEffect(.bounce, value: active)
            Text(label).font(.system(size: 11, weight: .bold)).foregroundStyle(c)
        }
        .padding(.horizontal, 20)
        .scaleEffect(active ? 1.18 : 0.85)
        .opacity(active ? 1 : 0.6)
        .animation(.spring(response: 0.3, dampingFraction: 0.55), value: active)
    }
}

/// HSM-14-03 — the full artifact as a readable document: rendered Markdown (MarkdownUI,
/// styled code blocks), selectable text, Copy + Share. Tap a card to open it.
struct ArtifactDetailView: View {
    let artifact: Artifact
    let ink: UIImage?
    var onCorrect: ((String) -> Void)? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var copied = false
    @State private var showVoice = false
    private var tint: Color { artifactTint(artifact.artifactType) }
    private var actionable: Bool { artifact.status == .draft || artifact.status == .needsReview }
    private var shareText: String {
        "\(artifactTypeLabel(artifact.artifactType)) — \(artifact.title)\n\n\(artifact.bodyMarkdown)"
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HStack(spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 13, style: .continuous).fill(tint.opacity(0.18))
                            Image(systemName: artifactGlyph(artifact.artifactType)).font(.system(size: 19, weight: .bold)).foregroundStyle(tint)
                        }.frame(width: 46, height: 46)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(artifactTypeLabel(artifact.artifactType)).font(.system(size: 12, weight: .heavy)).tracking(0.6).foregroundStyle(tint)
                            Text(artifact.title).font(.system(size: 23, weight: .heavy)).foregroundStyle(Sig.text)
                        }
                        Spacer(minLength: 0)
                    }
                    if let ink {
                        Image(uiImage: ink).resizable().scaledToFit().frame(maxWidth: .infinity)
                            .background(Color.white, in: RoundedRectangle(cornerRadius: 12))
                    }
                    if artifact.bodyMarkdown.isEmpty {
                        Text("No written content for this artifact.").font(.callout).foregroundStyle(Sig.faint)
                    } else {
                        Markdown(artifact.bodyMarkdown)
                            .markdownTextStyle { ForegroundColor(Sig.text); FontSize(16) }
                            .markdownBlockStyle(\.codeBlock) { config in
                                config.label.padding(12).font(.system(.callout, design: .monospaced))
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12))
                            }
                            .tint(Sig.accent)
                            .textSelection(.enabled)
                    }

                    if onCorrect != nil && actionable {
                        Button { showVoice = true } label: {
                            HStack(spacing: 9) {
                                Image(systemName: "mic.badge.plus").font(.system(size: 16, weight: .bold))
                                Text("Not right? Fix it by voice").font(.system(size: 15.5, weight: .heavy))
                            }
                            .foregroundStyle(tint)
                            .frame(maxWidth: .infinity).frame(height: 54)
                            .background(tint.opacity(0.14), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).stroke(tint.opacity(0.45), lineWidth: 1))
                        }
                        .padding(.top, 6)
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(Sig.bg.ignoresSafeArea())
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark.circle.fill").font(.system(size: 22)).foregroundStyle(Sig.faint)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    HStack(spacing: 16) {
                        Button {
                            UIPasteboard.general.string = artifact.bodyMarkdown.isEmpty ? artifact.title : artifact.bodyMarkdown
                            tactile(.medium)
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) { copied = true }
                            DispatchQueue.main.asyncAfter(deadline: .now() + 1.4) { withAnimation { copied = false } }
                        } label: {
                            Image(systemName: copied ? "checkmark.circle.fill" : "doc.on.doc")
                                .font(.system(size: 18, weight: .semibold)).foregroundStyle(copied ? Sig.ok : Sig.text)
                                .symbolEffect(.bounce, value: copied)
                        }
                        ShareLink(item: shareText) {
                            Image(systemName: "square.and.arrow.up").font(.system(size: 18, weight: .semibold)).foregroundStyle(Sig.text)
                        }
                    }
                }
            }
        }
        .preferredColorScheme(.dark)
        .sheet(isPresented: $showVoice) {
            VoiceCorrectionSheet(artifact: artifact) { spoken in onCorrect?(spoken) }
        }
    }
}

/// HSM-14-07 — "say what's wrong," on-device. Record → WhisperKit → the spoken correction (or
/// type it), then re-route to the local model. Submitting closes back to the meeting where the
/// card itself shows the "re-thinking" effect.
struct VoiceCorrectionSheet: View {
    let artifact: Artifact
    let onSubmit: (String) -> Void
    @Environment(\.dismiss) private var dismiss
    @StateObject private var voice = VoiceCaptureState()
    @State private var correction = ""
    @State private var pulse = false
    private var tint: Color { artifactTint(artifact.artifactType) }
    private var canSubmit: Bool { !correction.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                VStack(spacing: 6) {
                    Text("What's wrong with it?").font(.system(size: 25, weight: .heavy)).foregroundStyle(Sig.text)
                    Text(artifact.title).font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.faint).lineLimit(1)
                }.padding(.top, 6)

                Spacer(minLength: 0)
                Button { Task { await toggle() } } label: { micButton }
                    .disabled(voice.transcribing)
                Text(statusLine).font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.muted)
                Spacer(minLength: 0)

                TextField("…or type what to fix", text: $correction, axis: .vertical)
                    .lineLimit(2...5).font(.system(size: 16)).foregroundStyle(Sig.text)
                    .padding(14).background(Sig.s2, in: RoundedRectangle(cornerRadius: 16))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
                if !voice.error.isEmpty {
                    Text(voice.error).font(.caption).foregroundStyle(Sig.warn)
                }

                Button { onSubmit(correction) } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "wand.and.stars")
                        Text("Regenerate with this")
                    }
                    .font(.system(size: 16, weight: .heavy)).foregroundStyle(.black)
                    .frame(maxWidth: .infinity).frame(height: 56)
                    .background(canSubmit ? Sig.accent : Sig.s3, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                }
                .disabled(!canSubmit)
            }
            .padding(24)
            .background(Sig.bg.ignoresSafeArea())
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .topBarLeading) { Button("Cancel") { dismiss() }.tint(Sig.faint) } }
            .onChange(of: voice.text) { _, t in if !t.isEmpty { correction = t } }
        }
        .preferredColorScheme(.dark)
        .presentationDetents([.medium, .large])
    }

    private var micButton: some View {
        ZStack {
            Circle().fill(voice.recording ? Sig.bad.opacity(0.18) : tint.opacity(0.16))
                .frame(width: 112, height: 112)
                .scaleEffect(voice.recording && pulse ? 1.14 : 1)
            Circle().fill(voice.recording ? Sig.bad : tint).frame(width: 80, height: 80)
            Image(systemName: voice.transcribing ? "waveform" : (voice.recording ? "stop.fill" : "mic.fill"))
                .font(.system(size: 30, weight: .bold)).foregroundStyle(.black)
                .symbolEffect(.variableColor.iterative, isActive: voice.transcribing)
        }
        .onChange(of: voice.recording) { _, on in
            pulse = false
            if on { withAnimation(.easeInOut(duration: 0.7).repeatForever(autoreverses: true)) { pulse = true } }
        }
    }
    private var statusLine: String {
        if voice.transcribing { return "Transcribing on-device…" }
        if voice.recording { return "Listening… tap to stop" }
        if !correction.isEmpty { return "Tap to re-record, or edit below" }
        return "Tap the mic and say what to fix"
    }
    private func toggle() async {
        if voice.recording { await voice.stopAndTranscribe() } else { await voice.start() }
    }
}

// MARK: - Meeting detail (reopen-intact)

struct MeetingDetailView: View {
    let meeting: Meeting
    @StateObject private var notes: NotebookModel
    @StateObject private var review: MeetingReviewState
    private let links: [TranscriptLink]
    @State private var openDoc: OpenDoc?

    init(meeting: Meeting) {
        self.meeting = meeting
        _notes = StateObject(wrappedValue: NotebookModel(store: FileNotebookStore(), meetingID: meeting.id))
        _review = StateObject(wrappedValue: MeetingReviewState(meeting: meeting))
        links = TranscriptLinker(store: FileLinkStore(), meetingID: meeting.id).links()
    }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text(meeting.title ?? "Meeting").font(.largeTitle.bold()).foregroundStyle(Sig.text)
                    Text(meeting.startedAt.formatted(date: .complete, time: .shortened))
                        .font(.caption).foregroundStyle(Sig.faint)

                    if !links.isEmpty {
                        Text("MARKED MOMENTS").font(.caption2.weight(.bold)).tracking(1.5).foregroundStyle(Sig.local).padding(.top, 4)
                        ForEach(Array(links.enumerated()), id: \.offset) { _, link in
                            Button {
                                if let i = TranscriptLinker.segmentIndex(for: link.anchorTime, in: meeting.segments) {
                                    withAnimation { proxy.scrollTo(i, anchor: .center) }
                                }
                            } label: {
                                HStack(spacing: 8) {
                                    Image(systemName: link.isMark ? "star.fill" : "pencil.line").foregroundStyle(Sig.local)
                                    Text(link.label ?? (link.isMark ? "Marked moment" : "Note"))
                                        .font(.subheadline).foregroundStyle(Sig.text)
                                    Spacer()
                                    Text(String(format: "%.0fs", link.anchorTime)).font(.caption.monospaced()).foregroundStyle(Sig.faint)
                                    Image(systemName: "arrow.down.right").font(.caption2).foregroundStyle(Sig.faint)
                                }
                                .padding(11).background(Sig.local.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
                            }.buttonStyle(.plain)
                        }
                    }

                    artifactsSection

                    Text("TRANSCRIPT").font(.caption2.weight(.bold)).tracking(1.5).foregroundStyle(Sig.faint).padding(.top, 4)
                    if meeting.segments.isEmpty {
                        Text("No speech was transcribed.").font(.callout).foregroundStyle(Sig.faint)
                    } else {
                        ForEach(Array(meeting.segments.enumerated()), id: \.offset) { i, seg in
                            Text(seg.text).font(.body).foregroundStyle(Sig.text)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(12).background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
                                .id(i)
                        }
                    }

                    Text("NOTES").font(.caption2.weight(.bold)).tracking(1.5).foregroundStyle(Sig.local).padding(.top, 8)
                    // Reloads the meeting's PencilKit pages; editable so notes can be added after.
                    NotebookView(model: notes, editable: true)
                }
                .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .sheet(item: $openDoc) { doc in
            ArtifactDetailView(artifact: doc.artifact, ink: doc.ink, onCorrect: { spoken in
                openDoc = nil                                   // back to the meeting — the card itself shows it
                Task { await review.correct(doc.artifact, spoken: spoken) }
            })
        }
    }

    // MARK: artifact review (HSM-8-04)

    @ViewBuilder private var artifactsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Text("INTELLIGENCE").font(.caption2.weight(.bold)).tracking(1.5).foregroundStyle(Sig.accent)
                Spacer()
                egressBadge
            }
            Picker("Profile", selection: $review.profile) {
                ForEach(MIRProfile.allCases, id: \.self) { Text($0.rawValue.capitalized).tag($0) }
            }
            .pickerStyle(.segmented)

            if review.generating {
                HStack(spacing: 8) {
                    ProgressView().tint(Sig.accent)
                    Text(review.note.isEmpty ? "Thinking on-device…" : review.note)
                        .font(.caption).foregroundStyle(Sig.muted)
                }
                Text("Runs fully on this iPad — a few minutes for a 4B model, no network.")
                    .font(.caption2).foregroundStyle(Sig.faint)
            }

            // Whatever's been produced so far — generated artifacts and/or handwritten
            // notes — streams in here.
            if review.artifacts.isEmpty && !review.generating {
                Text("Generate decisions, action items, risks and more from this meeting — or add your handwritten notes. All on-device.")
                    .font(.caption).foregroundStyle(Sig.faint)
            } else {
                ForEach(review.groups, id: \.type) { group in
                    ForEach(Array(group.items.enumerated()), id: \.element.id) { idx, a in
                        SwipeableArtifactCard(
                            artifact: a, ink: inkImage(a), index: idx,
                            regenerating: review.correctingId == a.id,
                            onApprove: { review.approve(a.id) },
                            onDismiss: { review.reject(a.id) },
                            onOpen: { openDoc = OpenDoc(artifact: a, ink: inkImage(a)) })
                    }
                }
            }

            // The two actions are INDEPENDENT — adding handwritten notes must never block
            // generating the AI intelligence (and vice-versa). Generate is ALWAYS available:
            // "Generate on-device" when nothing's there, "Regenerate on-device" once it is
            // (a clean regenerate drops the prior model artifacts and keeps your ink).
            if !review.generating {
                Button { Task { await review.generate() } } label: {
                    HStack(spacing: 6) {
                        Image(systemName: review.hasGeneratedArtifacts ? "arrow.clockwise" : "sparkles")
                        Text(review.hasGeneratedArtifacts ? "Regenerate on-device" : "Generate on-device")
                    }
                    .font(.subheadline.weight(.semibold)).foregroundStyle(.black)
                    .frame(maxWidth: .infinity).padding(.vertical, 12)
                    .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
                }
                if !review.hasInkArtifacts {
                    Button { Task { await review.promoteNotes() } } label: {
                        HStack(spacing: 6) { Image(systemName: "hand.draw"); Text("Add your handwritten notes") }
                            .font(.subheadline.weight(.semibold)).foregroundStyle(Sig.local)
                            .frame(maxWidth: .infinity).padding(.vertical, 11)
                            .background(Sig.local.opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Sig.local.opacity(0.35), lineWidth: 1))
                    }
                }
            }
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Sig.line, lineWidth: 1))
    }

    private func artifactCard(_ a: Artifact) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Text(a.title).font(.subheadline.weight(.semibold)).foregroundStyle(Sig.text)
                Spacer()
                statusChip(a.status)
            }
            if let img = inkImage(a) {
                Image(uiImage: img).resizable().scaledToFit()
                    .frame(maxHeight: 260).frame(maxWidth: .infinity)
                    .background(Color.white, in: RoundedRectangle(cornerRadius: 8))
            }
            if !a.bodyMarkdown.isEmpty {
                Text(a.bodyMarkdown).font(.caption).foregroundStyle(Sig.muted).lineLimit(6)
            }
            if a.status == .draft || a.status == .needsReview {
                HStack(spacing: 10) {
                    Button { review.approve(a.id) } label: {
                        Label("Approve", systemImage: "checkmark.circle.fill").font(.caption.weight(.semibold))
                            .foregroundStyle(.black).padding(.horizontal, 12).padding(.vertical, 7)
                            .background(Sig.ok, in: Capsule())
                    }
                    Button { review.reject(a.id) } label: {
                        Label("Dismiss", systemImage: "xmark").font(.caption.weight(.semibold))
                            .foregroundStyle(Sig.muted).padding(.horizontal, 12).padding(.vertical, 7)
                            .background(Sig.s3, in: Capsule())
                    }
                }
            }
        }
        .padding(12).background(Sig.s2, in: RoundedRectangle(cornerRadius: 11))
        .overlay(RoundedRectangle(cornerRadius: 11).stroke(Sig.line, lineWidth: 1))
    }

    /// Load the attached ink image for an ink-image artifact, if any.
    private func inkImage(_ a: Artifact) -> UIImage? {
        guard a.pluginId == "holdspeak.mobile.ink",
              case .object(let o) = a.structuredJson,
              case .string(let path)? = o["image_path"] else { return nil }
        return UIImage(contentsOfFile: path)
    }

    private func statusChip(_ s: ArtifactStatus) -> some View {
        let (label, color): (String, Color) = {
            switch s {
            case .accepted: ("Approved", Sig.ok)
            case .rejected: ("Dismissed", Sig.faint)
            case .needsReview: ("Review", Sig.warn)
            case .draft: ("Proposed", Sig.local)
            }
        }()
        return Text(label).font(.caption2.weight(.bold)).foregroundStyle(color)
            .padding(.horizontal, 8).padding(.vertical, 3)
            .background(color.opacity(0.12), in: Capsule())
    }

    private var egressBadge: some View {
        HStack(spacing: 5) {
            Image(systemName: "lock.fill").font(.caption2)
            Text("on-device").font(.caption2.weight(.medium))
        }
        .foregroundStyle(Sig.ok).padding(.horizontal, 8).padding(.vertical, 4)
        .background(Sig.ok.opacity(0.1), in: Capsule())
    }
}
