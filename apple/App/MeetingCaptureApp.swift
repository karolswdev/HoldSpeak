import SwiftUI
import AVFoundation
import WhisperKit
import PencilKit

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

// MARK: - Meeting detail (reopen-intact)

struct MeetingDetailView: View {
    let meeting: Meeting
    @StateObject private var notes: NotebookModel
    private let links: [TranscriptLink]

    init(meeting: Meeting) {
        self.meeting = meeting
        _notes = StateObject(wrappedValue: NotebookModel(store: FileNotebookStore(), meetingID: meeting.id))
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
    }
}
