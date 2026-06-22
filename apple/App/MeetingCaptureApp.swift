import SwiftUI
import AVFoundation
import WhisperKit
import PencilKit
import Vision
import os
import UIKit
import MarkdownUI
import UniformTypeIdentifiers
import WebKit

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
                    // AirDrop / "Open in HoldSpeak" a .gguf → copy it into the app's container.
                    .onOpenURL { url in
                        guard url.pathExtension.lowercased() == "gguf" else { return }
                        try? ModelFiles.importModel(from: url)
                    }
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

    // The WhisperKit model is LOADED ONCE and reused. Previously every call constructed a fresh
    // `WhisperKit(...)`, which reloads the CoreML model from disk (seconds) — so live ticks
    // compounded into a frozen-feeling control plane. Cached in a lock-guarded static (WhisperKit
    // isn't Sendable, so it never crosses an isolation boundary — created + used in this method).
    private static let cacheLock = NSLock()
    nonisolated(unsafe) private static var modelCache: [String: WhisperKit] = [:]
    private static func cachedModel(_ k: String) -> WhisperKit? { cacheLock.lock(); defer { cacheLock.unlock() }; return modelCache[k] }
    private static func cacheModel(_ k: String, _ m: WhisperKit) { cacheLock.lock(); modelCache[k] = m; cacheLock.unlock() }

    func transcribe() async throws -> [Segment] {
        let samples = chunks.flatMap { $0.samples }
        guard samples.count >= 16_000 / 4 else { return [] }
        let floats = samples.map { Float($0) / 32768.0 }
        let whisper: WhisperKit
        if let cached = Self.cachedModel(model) {
            whisper = cached
        } else {
            whisper = try await WhisperKit(WhisperKitConfig(model: model))
            Self.cacheModel(model, whisper)
        }
        let results = try await whisper.transcribe(audioArray: floats)
        // Preserve WhisperKit's real per-segment timestamps (relative to this window) instead of
        // collapsing to one zero-timestamp segment — the sliding-window commit (HSM-14-12) needs
        // them to know exactly which audio a committed segment covers. `WhisperText.clean` runs
        // per segment; all-non-speech segments drop out, so a blank window still cleans to [].
        let segs = results.flatMap { $0.segments }.compactMap { seg -> Segment? in
            let text = WhisperText.clean(seg.text)
            guard !text.isEmpty else { return nil }
            return TranscribedSegment(text: text, startTime: Double(seg.start), endTime: Double(seg.end)).asContractSegment()
        }
        return segs
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

/// HSM-14 — a snippet pulled from the transcript onto the note canvas. The user grabs a moment
/// (a live bubble or a tacked note) and drops it here as a movable card to ink around.
struct NoteCard: Identifiable, Codable, Equatable {
    var id = UUID()
    var text: String
    var x: Double
    var y: Double
}

@MainActor
final class NotebookModel: ObservableObject {
    @Published var pages: [PKDrawing]
    @Published var current = 0
    @Published var cards: [NoteCard] = []          // transcript snippets pulled onto the canvas
    private let notebook: Notebook
    private let cardsURL: URL

    init(store: NotebookStore, meetingID: String) {
        notebook = Notebook(store: store, meetingID: meetingID)
        let loaded = notebook.reload().compactMap { try? PKDrawing(data: $0) }
        pages = loaded.isEmpty ? [PKDrawing()] : loaded
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        cardsURL = docs.appendingPathComponent("notecards-\(meetingID).json")
        cards = (try? JSONDecoder().decode([NoteCard].self, from: Data(contentsOf: cardsURL))) ?? []
    }

    func page(_ i: Int) -> Binding<PKDrawing> {
        Binding(get: { self.pages[i] }, set: { self.pages[i] = $0; self.save() })
    }
    func addPage() { pages.append(PKDrawing()); current = pages.count - 1; save() }
    func save() { try? notebook.save(pages: pages.map { $0.dataRepresentation() }) }
    var hasInk: Bool { pages.contains { !$0.strokes.isEmpty } }

    // HSM-14 — transcript → note canvas.
    func addCard(_ text: String, at p: CGPoint) {
        cards.append(NoteCard(text: text, x: Double(p.x), y: Double(p.y))); saveCards()
    }
    func moveCard(_ id: UUID, to p: CGPoint) {
        guard let i = cards.firstIndex(where: { $0.id == id }) else { return }
        cards[i].x = Double(p.x); cards[i].y = Double(p.y); saveCards()
    }
    func removeCard(_ id: UUID) { cards.removeAll { $0.id == id }; saveCards() }
    private func saveCards() { try? JSONEncoder().encode(cards).write(to: cardsURL, options: .atomic) }
}

// MARK: - Notebook surface

struct NotebookView: View {
    @ObservedObject var model: NotebookModel
    var editable: Bool
    var onPromote: ((NoteCard, ArtifactType) -> Void)? = nil

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
            ZStack(alignment: .topLeading) {
                PencilCanvas(drawing: editable ? model.page(model.current) : .constant(model.pages[model.current]),
                             editable: editable)
                // HSM-14 — transcript snippets pulled onto the canvas float ABOVE the ink, so you
                // can drag them around and ink in the gaps. Always rendered (so they reliably
                // reappear when a saved meeting is reopened).
                ForEach(model.cards) { card in
                    NoteCardView(card: card, editable: editable,
                                 onMove: { model.moveCard(card.id, to: $0) },
                                 onRemove: { withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { model.removeCard(card.id) } },
                                 onPromote: onPromote.map { op in { type in op(card, type) } })
                }
            }
            .frame(maxWidth: .infinity, minHeight: 360)
            .background(SigN.s1, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(SigN.line, lineWidth: 1))
            .coordinateSpace(name: "notecanvas")
        }
    }
}

/// A transcript snippet living on the note canvas: a quoted, tinted card you drag to place and
/// ink around. Tap its corner to remove. Lands with a spring when it arrives from the transcript.
struct NoteCardView: View {
    let card: NoteCard
    let editable: Bool
    let onMove: (CGPoint) -> Void
    let onRemove: () -> Void
    var onPromote: ((ArtifactType) -> Void)? = nil
    @State private var landed = false
    @State private var lifting = false
    @State private var promoted = false

    private let promoteTypes: [ArtifactType] = [.decisions, .actionItems, .riskRegister, .requirements, .adr]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 7) {
                Image(systemName: "quote.opening").font(.system(size: 11, weight: .bold)).foregroundStyle(SigN.accent)
                Text(card.text)
                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(SigN.muted)
                    .lineLimit(5).fixedSize(horizontal: false, vertical: true)
            }
            // The card OFFERS something: turn this moment into a real intelligence artifact.
            if let onPromote, editable {
                Button {
                    guard !promoted else { return }
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { promoted = true }
                    tactile(.medium); onPromote(guessArtifactType(card.text))
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: promoted ? "checkmark.circle.fill" : "sparkles")
                        Text(promoted ? "In review" : "Promote to artifact")
                    }
                    .font(.system(size: 10, weight: .heavy))
                    .foregroundStyle(promoted ? SigN.accent : .black)
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(promoted ? SigN.accent.opacity(0.16) : SigN.accent, in: Capsule())
                }
                .buttonStyle(.plain)
                .contextMenu {
                    ForEach(promoteTypes, id: \.self) { t in
                        Button { withAnimation { promoted = true }; tactile(.medium); onPromote(t) } label: {
                            Label("Promote as \(artifactTypeLabel(t))", systemImage: artifactGlyph(t))
                        }
                    }
                }
            }
        }
        .padding(.horizontal, 11).padding(.vertical, 9)
        .frame(width: 196, alignment: .leading)
        .background(SigN.s1, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous).stroke(SigN.accent.opacity(lifting ? 0.85 : 0.4), lineWidth: lifting ? 1.6 : 1))
        .shadow(color: .black.opacity(lifting ? 0.5 : 0.28), radius: lifting ? 14 : 7, y: lifting ? 8 : 4)
        .overlay(alignment: .topTrailing) {
            if editable {
                Button(action: onRemove) {
                    Image(systemName: "xmark.circle.fill").font(.system(size: 16))
                        .foregroundStyle(SigN.faint).background(Circle().fill(SigN.s1))
                }
                .buttonStyle(.plain).offset(x: 6, y: -6)
            }
        }
        .scaleEffect(landed ? (lifting ? 1.04 : 1) : 1.3)
        .position(x: card.x, y: card.y)
        .gesture(editable ?
            DragGesture(coordinateSpace: .named("notecanvas"))
                .onChanged { v in if !lifting { withAnimation(.spring(response: 0.2, dampingFraction: 0.7)) { lifting = true } }; onMove(v.location) }
                .onEnded { _ in withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { lifting = false } }
            : nil)
        .onAppear { withAnimation(.spring(response: 0.34, dampingFraction: 0.6)) { landed = true } }
        .transition(.scale.combined(with: .opacity))
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

// MARK: - Signal depth + motion (HSM-14 craft elevation)

private extension Sig {
    static let bgTop = Color(hex: 0x191B23)
    /// A cinematic vertical wash — depth instead of a flat fill.
    static var bgGradient: LinearGradient {
        LinearGradient(colors: [bgTop, bg], startPoint: .top, endPoint: .bottom)
    }
    /// The brand accent as a warm diagonal gradient (amber → ember) for hero surfaces.
    static var accentGradient: LinearGradient {
        LinearGradient(colors: [Color(hex: 0xFF9D5C), accent, Color(hex: 0xF24A2E)],
                       startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    static var accentSoft: Color { accent.opacity(0.15) }
    static var localGradient: LinearGradient {
        LinearGradient(colors: [Color(hex: 0x7AA6FF), local], startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    /// A top-lit hairline so cards catch light at the top edge (glass realism).
    static var topHairline: LinearGradient {
        LinearGradient(colors: [Color.white.opacity(0.12), Color.white.opacity(0.035)],
                       startPoint: .top, endPoint: .bottom)
    }
}

/// Elevated Signal surface: layered fill + a top-lit hairline + a soft drop shadow. The one card
/// treatment the whole app shares, so elevation is consistent (not random shadow values).
private struct SignalCard: ViewModifier {
    var fill: Color = Sig.s1
    var radius: CGFloat = 18
    var elevated: Bool = true
    func body(content: Content) -> some View {
        content
            .background(fill, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(Sig.topHairline, lineWidth: 1))
            .shadow(color: .black.opacity(elevated ? 0.38 : 0), radius: elevated ? 16 : 0, y: elevated ? 9 : 0)
    }
}
private extension View {
    func signalCard(_ fill: Color = Sig.s1, radius: CGFloat = 18, elevated: Bool = true) -> some View {
        modifier(SignalCard(fill: fill, radius: radius, elevated: elevated))
    }
}

/// A gradient-filled rounded glyph chip — the consistent icon container across rows/CTAs.
private struct GlyphChip: View {
    let system: String
    var gradient: LinearGradient = Sig.localGradient
    var size: CGFloat = 46
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.28, style: .continuous).fill(gradient)
                .shadow(color: .black.opacity(0.25), radius: 5, y: 3)
            Image(systemName: system).font(.system(size: size * 0.42, weight: .bold)).foregroundStyle(.white)
        }.frame(width: size, height: size)
    }
}

/// Press feedback every tappable card shares: a subtle scale + dim on a spring (HIG scale-feedback).
private struct PressableCard: ButtonStyle {
    var scale: CGFloat = 0.975
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? scale : 1)
            .opacity(configuration.isPressed ? 0.94 : 1)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: configuration.isPressed)
    }
}

// MARK: - Live capture canvas model (HSM-14)

/// A finished utterance, floating in the live stream until it's tacked to the board.
struct LiveBubble: Identifiable, Equatable {
    let id = UUID()
    let text: String
    let t: Double          // elapsed seconds when it was heard — becomes the moment's anchor
}
/// A bubble the user grabbed and placed on the board. `tacked` distinguishes the two HSM-14-13
/// drops: a **tacked** note wears a pushpin + a slight tilt and ALSO marks the moment (HSM-8-03,
/// steering the intelligence); a **loose** note is just placed (no pushpin, no marked moment).
struct PinnedNote: Identifiable, Equatable {
    let id: UUID
    let text: String
    var pos: CGPoint
    var rot: Double
    let t: Double
    var tacked: Bool = true
    var w: CGFloat = 162          // HSM-14-13 — corner-drag resizes this; text reflows within it
}

/// Split a running transcript into finished sentences + the trailing in-progress fragment.
/// WhisperKit's windowed state mostly APPENDS, so counting finished sentences is a stable way
/// to spawn one bubble per utterance without re-bubbling on minor revisions.
enum LiveSentences {
    static func split(_ text: String) -> (completed: [String], trailing: String) {
        var completed: [String] = []; var cur = ""
        for ch in text {
            cur.append(ch)
            if ch == "." || ch == "!" || ch == "?" {
                let s = cur.trimmingCharacters(in: .whitespacesAndNewlines)
                if !s.isEmpty { completed.append(s) }
                cur = ""
            }
        }
        return (completed, cur.trimmingCharacters(in: .whitespacesAndNewlines))
    }
}

/// HSM-14 — render a bundled pixel-art asset crisply if present, else fall back to an SF Symbol.
/// Keeps the build independent of the (optional) generated art: the UI works either way.
@ViewBuilder func pixelAsset(_ name: String, size: CGFloat, fallback: String, tint: Color = Sig.accent) -> some View {
    if let ui = UIImage(named: name) {
        Image(uiImage: ui).resizable().interpolation(.none).frame(width: size, height: size)
    } else {
        Image(systemName: fallback).font(.system(size: size * 0.74, weight: .bold)).foregroundStyle(tint)
    }
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
    // HSM-14 — the live capture canvas: utterances stream as bubbles, the user tacks the
    // important ones to the board (which marks the moment for the on-device intelligence).
    @Published var liveBubbles: [LiveBubble] = []
    @Published var pinned: [PinnedNote] = []
    @Published var partial = ""                   // the words still being transcribed
    @Published var notesJump = 0                  // bump → the UI switches to the Notes pane
    private var bubbledCount = 0
    private var lastFull = ""

    let notebookStore: NotebookStore = FileNotebookStore()
    private let linkStore: LinkStore = FileLinkStore()
    private var linker: TranscriptLinker?
    private var recordStart: Date?
    private var mc: MeetingCapture?
    private var ticker: Task<Void, Never>?
    private var levelTicker: Task<Void, Never>?
    @Published var level: Float = 0            // HSM-14 — live mic amplitude for the waveform

    // HSM-14-13 — the floating recorder's spatial state (dock / free position / minimized), held on
    // the model so it survives pane switches and re-entry within the session. The snap math lives
    // in RuntimeCore (`RecorderSnap`, host-tested); the view just renders this.
    @Published var recorderLayout = RecorderLayout()
    func dockRecorder(_ dock: RecorderDock, freeCenter: CGPoint?) {
        recorderLayout.dock = dock
        if let f = freeCenter { recorderLayout.freeCenter = f }
    }
    func toggleRecorderMinimized() { recorderLayout.minimized.toggle() }

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
        liveBubbles = []; pinned = []; partial = ""; bubbledCount = 0; lastFull = ""
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
                try? await Task.sleep(nanoseconds: 1_200_000_000)   // window the live transcript (model is cached, so this is the cadence)
                await mc.tick()
                if case .recording(let t) = mc.state { await MainActor.run { self?.liveTranscript = t; self?.ingest(t) } }
            }
        }
        // Fast, independent poll of the mic amplitude (20 Hz) — the waveform reacts to sound the
        // instant it arrives, with no transcription round-trip.
        levelTicker = Task { [weak self] in
            while !Task.isCancelled, self?.recording == true {
                await MainActor.run { self?.level = self?.mc?.inputLevel ?? 0 }
                try? await Task.sleep(nanoseconds: 50_000_000)
            }
            await MainActor.run { self?.level = 0 }
        }
    }

    func stopRecording() async {
        guard let mc else { return }
        ticker?.cancel(); ticker = nil
        levelTicker?.cancel(); levelTicker = nil; level = 0
        recording = false; transcribing = true; defer { transcribing = false }
        notebook?.save()           // final flush of the meeting's notes
        _ = await mc.stop()
        if case .failed(let r) = mc.state { error = r }
        refresh()
    }

    private func elapsed() -> Double { recordStart.map { Date().timeIntervalSince($0) } ?? 0 }
    var elapsedSeconds: Double { elapsed() }     // for the floating recorder's timer

    /// HSM-14 — turn the running transcript into floating bubbles. Each newly-finished sentence
    /// becomes a pinnable bubble; the trailing fragment shows as the live caption. Capped so the
    /// stream stays glanceable (older bubbles drift off the top).
    private func ingest(_ raw: String) {
        let full = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !full.isEmpty, full != lastFull else { return }
        lastFull = full
        let parts = LiveSentences.split(full)
        if parts.completed.count > bubbledCount {
            let now = elapsed()
            for s in parts.completed[bubbledCount...] { liveBubbles.append(LiveBubble(text: s, t: now)) }
            bubbledCount = parts.completed.count
            if liveBubbles.count > 5 { liveBubbles.removeFirst(liveBubbles.count - 5) }
        }
        partial = parts.trailing
    }

    // HSM-14-13 — a live bubble is being dragged; the canvas shows the tack target and highlights
    // it when the drag is over it. `bubbleDragPoint` is in the named "canvas" space.
    @Published var bubbleDragging = false
    @Published var bubbleDragPoint: CGPoint?

    /// Route a dropped bubble (HSM-14-13 deliverable 2): the tack zone tacks it (marks the moment),
    /// a drop below the stream places it loose, a drop back in the stream snaps it back. The
    /// decision is RuntimeCore's pure `BubblePlacement` (host-tested). Returns whether it committed
    /// (so the bubble view knows to snap home when it didn't).
    func drop(_ b: LiveBubble, at p: CGPoint, in size: CGSize, pinFloor: CGFloat, tackZone: CGRect) -> Bool {
        switch BubblePlacement.decide(at: p, pinFloor: pinFloor, tackZone: tackZone) {
        case .tack:  pin(b, at: p, in: size, boardTop: pinFloor);        return true
        case .loose: placeLoose(b, at: p, in: size, boardTop: pinFloor); return true
        case .snapBack:                                                  return false
        }
    }

    /// Tack a bubble to the board at its drop point. THE WHOLE POINT: a tacked bubble is also a
    /// marked moment (HSM-8-03), so the on-device intelligence weights what you cared about.
    func pin(_ b: LiveBubble, at p: CGPoint, in size: CGSize, boardTop: CGFloat) {
        let pos = clampToBoard(p, in: size, boardTop: boardTop)
        pinned.append(PinnedNote(id: b.id, text: b.text, pos: pos, rot: Double.random(in: -5...5), t: b.t, tacked: true))
        liveBubbles.removeAll { $0.id == b.id }
        try? linker?.markMoment(at: b.t, label: String(b.text.prefix(120)))
        markCount = linker?.links().count ?? markCount
    }

    /// Place a bubble loose on the desktop — just arranged, NOT a marked moment (HSM-14-13). It can
    /// be promoted to a tacked moment later via `tackExisting`.
    func placeLoose(_ b: LiveBubble, at p: CGPoint, in size: CGSize, boardTop: CGFloat) {
        let pos = clampToBoard(p, in: size, boardTop: boardTop)
        pinned.append(PinnedNote(id: b.id, text: b.text, pos: pos, rot: 0, t: b.t, tacked: false))
        liveBubbles.removeAll { $0.id == b.id }
    }

    /// Promote a loose card to a tacked moment — NOW it marks the moment and steers the intelligence.
    func tackExisting(_ id: UUID) {
        guard let i = pinned.firstIndex(where: { $0.id == id }), !pinned[i].tacked else { return }
        pinned[i].tacked = true
        pinned[i].rot = Double.random(in: -5...5)
        try? linker?.markMoment(at: pinned[i].t, label: String(pinned[i].text.prefix(120)))
        markCount = linker?.links().count ?? markCount
        tactile(.medium)
    }

    /// Tacked moments only — what actually steers MIR (loose cards don't count).
    var tackedCount: Int { pinned.filter(\.tacked).count }
    var looseCount: Int { pinned.filter { !$0.tacked }.count }

    func unpin(_ id: UUID) { pinned.removeAll { $0.id == id } }

    /// HSM-14-13 deliverable 3 — corner-drag resize: clamp the width to the readable range; text
    /// reflows within it. Width persists on the model for the session.
    func resizePin(_ id: UUID, to width: CGFloat) {
        guard let i = pinned.firstIndex(where: { $0.id == id }) else { return }
        pinned[i].w = CardSize.clampWidth(width)
    }

    // HSM-14-13 deliverable 4 — the loose-card positions before the last tidy, kept for one undo.
    @Published private(set) var canUndoTidy = false
    private var preTidy: [UUID: CGPoint] = [:]

    /// One-tap tidy: re-flow the loose cards into a readable centered grid below `pinFloor`
    /// (tacked moments stay put — they were placed deliberately). Saves the prior arrangement so a
    /// single undo restores it.
    func tidyLoose(in size: CGSize, pinFloor: CGFloat) {
        let loose = pinned.enumerated().filter { !$0.element.tacked }
        guard !loose.isEmpty else { return }
        preTidy = Dictionary(uniqueKeysWithValues: loose.map { ($0.element.id, $0.element.pos) })
        let targets = WorkspaceTidy.layout(count: loose.count, in: size, pinFloor: pinFloor)
        for (slot, item) in loose.enumerated() { pinned[item.offset].pos = targets[slot] }
        canUndoTidy = true
        tactile(.medium)
    }

    func undoTidy() {
        guard canUndoTidy else { return }
        for i in pinned.indices { if let p = preTidy[pinned[i].id] { pinned[i].pos = p } }
        preTidy = [:]; canUndoTidy = false
        tactile()
    }

    /// HSM-14 — pull a transcript moment ONTO the note canvas as a draggable card, then jump to
    /// the Notes pane so the user lands where it arrived. The notebook exists once recording starts.
    func sendToNotes(_ text: String) {
        guard let nb = notebook else { return }
        let n = nb.cards.count
        nb.addCard(String(text.prefix(240)),
                   at: CGPoint(x: 150 + CGFloat(n % 3) * 26, y: 120 + CGFloat(n % 8) * 24))
        notesJump += 1
        tactile(.medium)
    }

    /// HSM-14 — promote a note snippet to a real `needs_review` artifact on the LIVE meeting; it
    /// shows up in the intelligence pane when the meeting is reviewed.
    func promoteNoteToArtifact(_ text: String, type: ArtifactType) {
        guard let id = mc?.currentID else { return }
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let store = try? SQLiteStorage(path: docs.appendingPathComponent("meetings.sqlite").path)
        try? store?.saveArtifact(noteArtifact(meetingId: id, type: type, text: text))
        flashMessage("Promoted to a \(artifactTypeLabel(type)) — review it after the meeting")
        tactile(.medium)
    }

    @Published var flash = ""
    func flashMessage(_ s: String) {
        flash = s
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.4) { if self.flash == s { self.flash = "" } }
    }
    func movePin(_ id: UUID, to p: CGPoint, in size: CGSize, boardTop: CGFloat) {
        guard let i = pinned.firstIndex(where: { $0.id == id }) else { return }
        pinned[i].pos = clampToBoard(p, in: size, boardTop: boardTop)
    }
    private func clampToBoard(_ p: CGPoint, in size: CGSize, boardTop: CGFloat) -> CGPoint {
        CGPoint(x: min(max(p.x, 90), size.width - 90),
                y: min(max(p.y, boardTop + 34), size.height - 44))
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

    #if targetEnvironment(simulator)
    /// Simulator-only: stage a few saved meetings so a home-screen design screenshot shows real rows.
    func seedHomeDemo() {
        guard meetings.isEmpty else { return }
        func segs(_ n: Int) -> [Segment] { (0..<n).map { Segment(text: "w\($0)", speaker: "Speaker 1", startTime: 0, endTime: 1) } }
        let now = Date()
        meetings = [
            Meeting(id: "demo-1", startedAt: now.addingTimeInterval(-5400), endedAt: now.addingTimeInterval(-4800),
                    duration: 600, title: "Q3 planning — guilds vs activation", segments: segs(42),
                    intelStatus: IntelStatus(state: "ready"), micLabel: "On-device", remoteLabel: ""),
            Meeting(id: "demo-2", startedAt: now.addingTimeInterval(-90000), endedAt: now.addingTimeInterval(-88800),
                    duration: 1200, title: "Incident review — PI-204 cert outage", segments: segs(88),
                    intelStatus: IntelStatus(state: "ready"), micLabel: "On-device", remoteLabel: ""),
            Meeting(id: "demo-3", startedAt: now.addingTimeInterval(-180000), endedAt: now.addingTimeInterval(-179000),
                    duration: 1000, title: "Write-path scaling sync", segments: segs(31),
                    intelStatus: IntelStatus(state: "ready"), micLabel: "On-device", remoteLabel: ""),
        ]
    }

    /// Simulator-only: stage a few bubbles + tacked notes so a design screenshot shows the live
    /// canvas in flight. Never compiled into the device build — real behavior is untouched.
    func seedDemo(size: CGSize, boardTop: CGFloat) {
        guard liveBubbles.isEmpty, pinned.isEmpty, !recording else { return }
        recording = true; level = 0.14            // show the recording state + floating recorder
        // HSM-14-13 — design-screenshot hooks for the recorder's spatial states.
        let env = ProcessInfo.processInfo.environment
        if let raw = env["HS_DEMO_DOCK"], let d = RecorderDock(rawValue: raw) { recorderLayout.dock = d }
        if env["HS_DEMO_MIN"] == "1" { recorderLayout.minimized = true }
        liveBubbles = [
            LiveBubble(text: "Let's ship the beta to the design partners on Friday.", t: 12),
            LiveBubble(text: "Karol owns the migration script and the rollback plan.", t: 47),
            LiveBubble(text: "Risk: the vendor SLA doesn't cover the EU region yet.", t: 88),
        ]
        pinned = [
            // One tacked moment (pushpin + tilt, steers MIR) and one loose card (just placed, and
            // resized wider) — the HSM-14-13 deliverable-2/3 distinction, on one surface.
            PinnedNote(id: UUID(), text: "Decision: launch Friday, design partners first.",
                       pos: CGPoint(x: size.width * 0.30, y: size.height * 0.60), rot: -4, t: 12, tacked: true),
            PinnedNote(id: UUID(), text: "Action: Karol owns the migration script and the rollback plan for the EU region.",
                       pos: CGPoint(x: size.width * 0.66, y: size.height * 0.72), rot: 0, t: 47, tacked: false, w: 232),
        ]
        partial = "and we should double-check the analytics events before"
        // Show the tack target lit, as if a bubble is being dragged over it.
        if env["HS_DEMO_TACK"] == "1" {
            bubbleDragging = true
            bubbleDragPoint = CGPoint(x: size.width / 2, y: max(120, size.height - 56 - 80) + 28)
        }
        // Seed several scattered loose cards and tidy them, to show the grid re-flow (deliverable 4).
        if env["HS_DEMO_TIDY"] == "1" {
            let notes = ["Open Q: EU SLA coverage?", "Owner: Karol — rollback", "Metric: activation +6%",
                         "Risk: vendor lock-in", "Next: analytics audit"]
            pinned = notes.enumerated().map { i, txt in
                PinnedNote(id: UUID(), text: txt,
                           pos: CGPoint(x: size.width * (0.2 + Double(i % 3) * 0.28),
                                        y: size.height * (0.42 + Double(i % 4) * 0.13)),
                           rot: 0, t: Double(i * 10), tacked: false)
            }
            tidyLoose(in: size, pinFloor: boardTop)
        }
        // Stage the notes canvas with a couple of pulled-in transcript cards for the screenshot.
        if notebook == nil {
            let nb = NotebookModel(store: notebookStore, meetingID: "demo-sim")
            nb.cards = []
            nb.addCard("Decision: launch Friday, design partners first.", at: CGPoint(x: 150, y: 130))
            nb.addCard("Risk: the vendor SLA doesn't cover the EU region yet.", at: CGPoint(x: 250, y: 330))
            notebook = nb
        }
    }
    #endif
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

// MARK: - Models (import & manage — front and center, owner-requested)

/// An on-device model file in the app's container.
struct InstalledModel: Identifiable {
    let url: URL
    var sizeBytes: Int
    var id: String { url.lastPathComponent }
    var name: String { url.deletingPathExtension().lastPathComponent }
    enum Kind { case language, visionProjector
        var label: String { self == .visionProjector ? "Vision projector" : "Language / vision model" }
        var glyph: String { self == .visionProjector ? "eye.fill" : "brain.head.profile" }
        var tint: Color { self == .visionProjector ? Sig.local : Sig.accent }
    }
    var kind: Kind { url.lastPathComponent.lowercased().contains("mmproj") ? .visionProjector : .language }
}

/// The app-side model-files helper: imports/lists/deletes `.gguf` in the app's **Documents**
/// (where the on-device runtime's `localGGUF()` loads from + where pushes land). Delegates to
/// the tested Providers `ModelStore` (HSM-5-03), wrapping the security scope for picker URLs.
enum ModelFiles {
    static var root: URL { FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0] }
    static var store: ModelStore { ModelStore(root: root) }

    static func installed() -> [InstalledModel] {
        ((try? store.installedModels()) ?? [])
            .map { InstalledModel(url: $0, sizeBytes: (try? $0.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0) }
    }

    /// Copy an imported/AirDropped file into the container (the host owns the security scope).
    @discardableResult
    static func importModel(from src: URL) throws -> URL {
        let scoped = src.startAccessingSecurityScopedResource()
        defer { if scoped { src.stopAccessingSecurityScopedResource() } }
        return try store.importModel(from: src)
    }

    static func delete(_ m: InstalledModel) { try? store.delete(m.url) }

    static func size(_ bytes: Int) -> String {
        let f = ByteCountFormatter(); f.allowedUnits = [.useGB, .useMB]; f.countStyle = .file
        return f.string(fromByteCount: Int64(bytes))
    }
    static var ggufTypes: [UTType] { [UTType(filenameExtension: "gguf") ?? .data] }
}

struct ModelsView: View {
    @State private var models: [InstalledModel] = []
    @State private var importing = false
    @State private var note = ""
    @State private var busy = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Button { dismiss() } label: {
                        HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Home") }
                            .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                            .padding(.vertical, 8).padding(.trailing, 12)
                    }
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Models").font(.system(size: 32, weight: .heavy)).foregroundStyle(Sig.text)
                        Text("Everything runs on this iPad. Import a .gguf from Files or AirDrop — no Mac, no account.")
                            .font(.system(size: 14)).foregroundStyle(Sig.faint)
                    }
                    Button { importing = true } label: { importCta }.disabled(busy)
                    if !note.isEmpty {
                        HStack(spacing: 7) {
                            if busy { ProgressView().tint(Sig.accent) }
                            Text(note).font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.muted)
                        }
                    }
                    if models.isEmpty && !busy {
                        Text("No models yet. Import one to power on-device intelligence.")
                            .font(.callout).foregroundStyle(Sig.faint).padding(.top, 6)
                    } else {
                        ForEach(models) { modelCard($0) }
                    }
                }
                .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .fileImporter(isPresented: $importing, allowedContentTypes: ModelFiles.ggufTypes, allowsMultipleSelection: true) { result in
            guard case .success(let urls) = result, !urls.isEmpty else { return }
            busy = true; note = "Importing \(urls.count) file\(urls.count == 1 ? "" : "s")…"; tactile()
            Task.detached {
                var ok = 0
                for u in urls { if (try? ModelFiles.importModel(from: u)) != nil { ok += 1 } }
                await MainActor.run {
                    busy = false; note = "Imported \(ok) model\(ok == 1 ? "" : "s"). They're on this iPad now."; refresh()
                }
            }
        }
        .onAppear(perform: refresh)
    }

    private func refresh() { withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) { models = ModelFiles.installed() } }

    private var importCta: some View {
        HStack(spacing: 12) {
            Image(systemName: "square.and.arrow.down.fill").font(.system(size: 20, weight: .bold)).foregroundStyle(Sig.accent)
            VStack(alignment: .leading, spacing: 2) {
                Text("Import a model").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Pick a .gguf from Files (AirDrop a model, then import it here)").font(.system(size: 12)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
        }
        .padding(16)
        .frame(maxWidth: .infinity)
        .background(Sig.accent.opacity(0.12), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [7, 5])).foregroundStyle(Sig.accent.opacity(0.5)))
    }

    private func modelCard(_ m: InstalledModel) -> some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill(m.kind.tint.opacity(0.16))
                Image(systemName: m.kind.glyph).font(.system(size: 18, weight: .bold)).foregroundStyle(m.kind.tint)
            }.frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text(m.name).font(.system(size: 15.5, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 6) {
                    Text(m.kind.label).font(.system(size: 12, weight: .heavy)).foregroundStyle(m.kind.tint)
                    Text("·").foregroundStyle(Sig.faint)
                    Text(ModelFiles.size(m.sizeBytes)).font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.faint)
                }
            }
            Spacer(minLength: 4)
            Button { tactile(); ModelFiles.delete(m); refresh() } label: {
                Image(systemName: "trash").font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.faint)
                    .frame(width: 38, height: 38).background(Sig.s3, in: Circle())
            }
        }
        .padding(13)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Sig.line, lineWidth: 1))
    }
}

// MARK: - Sketch → Diagram (HSM-14-08: the Pencil as a diagram language, live)

private func shapeTint(_ k: ShapeKind) -> Color {
    switch k { case .rectangle: return Sig.local; case .diamond: return Sig.accent; case .ellipse: return Sig.ok }
}

/// Recognizes the PencilKit drawing into a graph + Mermaid, live + on-device. Geometry does the
/// shapes/edges (HSM-14-08 engine); on-device Vision reads the handwriting into node labels.
@MainActor final class SketchModel: ObservableObject {
    @Published var drawing = PKDrawing() { didSet { schedule() } }
    @Published var graph = DiagramGraph(nodes: [], edges: [])
    @Published var mermaid = ""
    @Published var vlmBusy = false
    @Published var vlmError = ""
    @Published var usedAI = false
    @Published var diagramType = ""
    private var task: Task<Void, Never>?

    /// HSM-14-09 — hand the whole sketch to the local vision model (Qwythos on .43) when the
    /// geometry isn't enough. It returns Mermaid; we parse + render it natively.
    func recognizeWithAI() {
        guard !drawing.strokes.isEmpty, !vlmBusy else { return }
        let png = Self.renderPNG(drawing)
        vlmBusy = true; vlmError = ""; tactile(.medium)
        Task { [weak self] in
            do {
                let raw = try await SketchVLM.mermaid(from: png)
                let (mm, type) = MermaidParse.parseResponse(raw)
                let g = MermaidParse.graph(mm)
                await MainActor.run {
                    self?.vlmBusy = false; self?.usedAI = true; self?.mermaid = mm; self?.diagramType = type
                    withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { self?.graph = g }
                }
            } catch {
                await MainActor.run { self?.vlmBusy = false; self?.vlmError = "Couldn't reach the vision model: \(error.localizedDescription)" }
            }
        }
    }
    nonisolated static func renderPNG(_ drawing: PKDrawing) -> Data {
        let b = drawing.bounds.insetBy(dx: -24, dy: -24)
        let rect = (b.isNull || b.isEmpty) ? CGRect(x: 0, y: 0, width: 400, height: 300) : b
        let drawn = drawing.image(from: rect, scale: 2)
        let r = UIGraphicsImageRenderer(size: drawn.size)
        let onWhite = r.image { ctx in
            UIColor.white.setFill(); ctx.fill(CGRect(origin: .zero, size: drawn.size)); drawn.draw(at: .zero)
        }
        return onWhite.pngData() ?? Data()
    }

    func schedule() {
        task?.cancel()
        let d = drawing
        task = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 280_000_000)        // debounce while drawing
            if Task.isCancelled { return }
            let result = await Task.detached { Self.recognize(d) }.value   // Vision off the main actor
            if Task.isCancelled { return }
            withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) { self?.graph = result.0 }
            self?.mermaid = result.1
        }
    }
    func clear() {
        drawing = PKDrawing(); graph = DiagramGraph(nodes: [], edges: []); mermaid = ""
    }

    nonisolated static func recognize(_ drawing: PKDrawing) -> (DiagramGraph, String) {
        var nodes: [DiagramBuilder.NodeInput] = []
        var connectors: [DiagramBuilder.ConnectorInput] = []
        for s in drawing.strokes {
            let pts = s.path.map { StrokePoint(Double($0.location.x), Double($0.location.y)) }
            guard pts.count >= 2 else { continue }
            switch ShapeRecognizer.classify(pts) {
            case .shape(let kind, let b):
                nodes.append(.init(kind: kind, text: ocrText(in: b, drawing: drawing), bounds: b))
            case .connector(let from, let to):
                let len = ((to.x - from.x) * (to.x - from.x) + (to.y - from.y) * (to.y - from.y)).squareRoot()
                if len > 30 { connectors.append(.init(from: from, to: to, label: nil)) }   // skip tiny text strokes
            }
        }
        let g = DiagramBuilder.build(nodes: nodes, connectors: connectors)
        return (g, MermaidGenerator.flowchart(g))
    }

    /// On-device handwriting OCR over a shape's region → its node label.
    nonisolated static func ocrText(in b: Bounds, drawing: PKDrawing) -> String {
        let rect = CGRect(x: b.minX - 6, y: b.minY - 6, width: b.w + 12, height: b.h + 12)
        guard rect.width > 8, rect.height > 8 else { return "" }
        let img = drawing.image(from: rect, scale: 2)
        guard let cg = img.cgImage else { return "" }
        var text = ""
        let req = VNRecognizeTextRequest { request, _ in
            text = (request.results as? [VNRecognizedTextObservation])?
                .compactMap { $0.topCandidates(1).first?.string }.joined(separator: " ") ?? ""
        }
        req.recognitionLevel = .accurate
        req.usesLanguageCorrection = true
        try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
        return text.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

/// Calls a local OpenAI-compatible VISION endpoint (Qwythos + mmproj on .43) to turn a sketch
/// image into Mermaid. Points at the owner's LAN server; swap the URL to retarget.
enum SketchVLM {
    static let endpoint = URL(string: "http://192.168.1.43:8080/v1/chat/completions")!
    static func mermaid(from png: Data) async throws -> String {
        let b64 = png.base64EncodedString()
        let prompt = """
        You are an expert at reading hand-drawn diagrams. Look at this sketch and reproduce it as a Mermaid diagram.

        FIRST decide which Mermaid diagram type best fits what is actually drawn:
        - "flowchart"        — boxes/diamonds joined by arrows (processes, decisions)
        - "sequenceDiagram"  — actors with vertical lifelines and horizontal messages
        - "classDiagram"     — boxes with a title + a list of fields/methods, connected
        - "stateDiagram-v2"  — states with labelled transitions, often a start/end dot
        - "erDiagram"        — entities with attributes and relationship lines
        - "mindmap"          — a central node with radiating branches
        - "gantt" or "timeline" — bars/events along a time axis

        THEN output VALID Mermaid for that type. Read the handwritten labels (fix obvious misspellings),
        keep it minimal and correct. For flowcharts: box A["x"], diamond B{"x"}, circle C(("x")),
        edge A --> B, labelled edge B -->|yes| C.

        Return ONLY JSON: {"diagram_type": "<one of the names above>", "mermaid": "<the full mermaid code, \\n between lines>"}.
        """
        let body: [String: Any] = [
            "messages": [["role": "user", "content": [
                ["type": "text", "text": prompt],
                ["type": "image_url", "image_url": ["url": "data:image/png;base64,\(b64)"]],
            ]]],
            "max_tokens": 900, "temperature": 0.2,
            "response_format": [
                "type": "json_schema",
                "json_schema": [
                    "name": "diagram",
                    "schema": ["type": "object",
                               "properties": ["diagram_type": ["type": "string"],
                                              "mermaid": ["type": "string", "minLength": 1]],
                               "required": ["diagram_type", "mermaid"], "additionalProperties": false],
                ],
            ],
        ]
        var req = URLRequest(url: endpoint, timeoutInterval: 120)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, _) = try await URLSession.shared.data(for: req)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let msg = (json?["choices"] as? [[String: Any]])?.first?["message"] as? [String: Any]
        return (msg?["content"] as? String) ?? ""
    }
}

/// Parse Mermaid flowchart text → a `DiagramGraph` with a simple layered layout, so the VLM's
/// output renders natively. Best-effort: a parse miss just leaves the graph empty (the raw
/// Mermaid is still shown).
enum MermaidParse {
    static func extract(_ raw: String) -> String {
        var s = raw
        if let f = s.range(of: "```") {
            s = String(s[f.upperBound...])
            if let e = s.range(of: "```") { s = String(s[..<e.lowerBound]) }
        }
        if let nl = s.firstIndex(of: "\n"), s[s.startIndex..<nl].lowercased().contains("mermaid") {
            s = String(s[s.index(after: nl)...])
        }
        if let r = s.range(of: "flowchart") { s = String(s[r.lowerBound...]) }
        else if let r = s.range(of: "graph ") { s = String(s[r.lowerBound...]) }
        return s.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// The model returns `{"diagram_type":"…","mermaid":"…"}` (json_schema) or raw/fenced mermaid.
    /// Returns the cleaned mermaid + the diagram type (inferred from the header if absent).
    static func parseResponse(_ content: String) -> (mermaid: String, type: String) {
        if let data = content.data(using: .utf8),
           let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let mm = obj["mermaid"] as? String {
            let m = extract(mm)
            let t = (obj["diagram_type"] as? String).flatMap { $0.isEmpty ? nil : $0 } ?? inferType(m)
            return (m, t)
        }
        let m = extract(content)
        return (m, inferType(m))
    }
    static func inferType(_ mermaid: String) -> String {
        let head = (mermaid.split(separator: "\n").first.map(String.init) ?? "").lowercased()
        let map: [(String, String)] = [
            ("sequencediagram", "sequence"), ("classdiagram", "class"), ("statediagram", "state"),
            ("erdiagram", "ER"), ("mindmap", "mindmap"), ("gantt", "gantt"), ("timeline", "timeline"),
            ("flowchart", "flowchart"), ("graph", "flowchart"),
        ]
        for (k, v) in map where head.contains(k) { return v }
        return "diagram"
    }

    static func graph(_ mermaid: String) -> DiagramGraph {
        var kinds: [String: ShapeKind] = [:]
        var texts: [String: String] = [:]
        var order: [String] = []
        var edges: [(String, String, String?)] = []
        func note(_ id: String, _ kind: ShapeKind?, _ text: String?) {
            if !order.contains(id) { order.append(id) }
            if let k = kind { kinds[id] = k }
            if let t = text, !t.isEmpty { texts[id] = t }
        }
        for raw in mermaid.split(separator: "\n") {
            let line = raw.trimmingCharacters(in: .whitespaces)
            scanDefs(line, note)
            for e in scanEdges(line) { note(e.0, nil, nil); note(e.1, nil, nil); edges.append(e) }
        }
        var depth: [String: Int] = [:]; for id in order { depth[id] = 0 }
        for _ in 0..<max(order.count, 1) {
            for (a, b, _) in edges { let d = (depth[a] ?? 0) + 1; if d > (depth[b] ?? 0) { depth[b] = d } }
        }
        var perRow: [Int: Int] = [:]
        var nodes: [DiagramNode] = []
        for id in order {
            let d = depth[id] ?? 0
            let col = perRow[d, default: 0]; perRow[d] = col + 1
            let x = Double(col) * 175, y = Double(d) * 115
            nodes.append(DiagramNode(id: id, kind: kinds[id] ?? .rectangle, text: texts[id] ?? id,
                                     bounds: Bounds(minX: x, minY: y, maxX: x + 130, maxY: y + 54)))
        }
        return DiagramGraph(nodes: nodes, edges: edges.map { DiagramEdge(from: $0.0, to: $0.1, label: $0.2) })
    }

    private static func scanDefs(_ l: String, _ note: (String, ShapeKind?, String?) -> Void) {
        let pats: [(String, ShapeKind)] = [
            (#"([A-Za-z0-9_]+)\(\(\s*\"?([^\")]*)\"?\s*\)\)"#, .ellipse),
            (#"([A-Za-z0-9_]+)\{\s*\"?([^\"}]*)\"?\s*\}"#, .diamond),
            (#"([A-Za-z0-9_]+)\[\s*\"?([^\"\]]*)\"?\s*\]"#, .rectangle),
        ]
        for (pat, kind) in pats {
            guard let re = try? NSRegularExpression(pattern: pat) else { continue }
            let ns = l as NSString
            re.enumerateMatches(in: l, range: NSRange(location: 0, length: ns.length)) { m, _, _ in
                guard let m = m, m.numberOfRanges >= 3 else { return }
                note(ns.substring(with: m.range(at: 1)), kind,
                     ns.substring(with: m.range(at: 2)).trimmingCharacters(in: .whitespaces))
            }
        }
    }
    private static func scanEdges(_ l: String) -> [(String, String, String?)] {
        let pat = #"([A-Za-z0-9_]+)(?:\[[^\]]*\]|\{[^}]*\}|\(\([^)]*\)\))?\s*[-.=]+>\s*(?:\|([^|]*)\|\s*)?([A-Za-z0-9_]+)"#
        guard let re = try? NSRegularExpression(pattern: pat) else { return [] }
        let ns = l as NSString
        var out: [(String, String, String?)] = []
        re.enumerateMatches(in: l, range: NSRange(location: 0, length: ns.length)) { m, _, _ in
            guard let m = m, m.numberOfRanges >= 4 else { return }
            let a = ns.substring(with: m.range(at: 1))
            let label = m.range(at: 2).location != NSNotFound ? ns.substring(with: m.range(at: 2)).trimmingCharacters(in: .whitespaces) : nil
            out.append((a, ns.substring(with: m.range(at: 3)), label))
        }
        return out
    }
}

/// A REAL Mermaid renderer — a WKWebView running the bundled mermaid.js (offline). Renders any
/// valid Mermaid the geometry engine or the VLM produces, re-rendering on each code change.
struct MermaidWebView: UIViewRepresentable {
    let code: String

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        let wv = WKWebView(frame: .zero, configuration: cfg)
        wv.navigationDelegate = context.coordinator
        wv.isOpaque = false
        wv.backgroundColor = .clear
        wv.scrollView.backgroundColor = .clear
        context.coordinator.wv = wv
        wv.loadHTMLString(Self.html(), baseURL: nil)
        return wv
    }

    func updateUIView(_ wv: WKWebView, context: Context) {
        context.coordinator.latest = code
        if context.coordinator.ready { context.coordinator.render(code) }
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        weak var wv: WKWebView?
        var ready = false
        var latest = ""
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            ready = true
            if !latest.isEmpty { render(latest) }
        }
        func render(_ code: String) {
            let esc = code.replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: "`", with: "\\`").replacingOccurrences(of: "$", with: "\\$")
            wv?.evaluateJavaScript("renderMermaid(`\(esc)`)", completionHandler: nil)
        }
    }

    static func html() -> String {
        let lib = (Bundle.main.url(forResource: "mermaid.min", withExtension: "js")
            .flatMap { try? String(contentsOf: $0, encoding: .utf8) }) ?? ""
        return """
        <!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=3">
        <style>
          html,body{margin:0;background:transparent;}
          #wrap{padding:10px;display:flex;align-items:center;justify-content:center;min-height:100%;}
          .mermaid svg{max-width:100%;height:auto;}
          .err{color:#E5544B;font:12px -apple-system;padding:10px;white-space:pre-wrap;}
        </style>
        <script>\(lib)</script></head>
        <body><div id="wrap"><div class="mermaid" id="m"></div></div>
        <script>
          mermaid.initialize({ startOnLoad:false, theme:'dark', securityLevel:'loose',
            themeVariables:{ background:'transparent', primaryColor:'#1D202A', primaryTextColor:'#F3F4F7',
              lineColor:'#9CA3B2', primaryBorderColor:'#FF6B35' } });
          async function renderMermaid(code){
            const t = (code||'').trim();
            if(!t){ document.getElementById('m').innerHTML=''; return; }
            try{ const { svg } = await mermaid.render('g'+Date.now(), t);
                 document.getElementById('m').innerHTML = svg; }
            catch(e){ document.getElementById('m').innerHTML = '<div class="err">'+String(e&&e.message||e)+'</div>'; }
          }
        </script></body></html>
        """
    }
}

/// Renders a `DiagramGraph` natively (offline, on-brand) — nodes as shapes, edges as arrows,
/// laid out at the sketched positions, scaled to fit.
struct DiagramPreview: View {
    let graph: DiagramGraph

    var body: some View {
        GeometryReader { geo in
            if graph.nodes.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "scribble.variable").font(.system(size: 26)).foregroundStyle(Sig.faint)
                    Text("Draw boxes, diamonds and arrows — the diagram builds itself.")
                        .font(.system(size: 13)).foregroundStyle(Sig.faint).multilineTextAlignment(.center)
                }.frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Canvas { ctx, size in render(ctx, size) }
            }
        }
    }

    private func render(_ ctx: GraphicsContext, _ size: CGSize) {
        let minX = graph.nodes.map { $0.bounds.minX }.min() ?? 0
        let maxX = graph.nodes.map { $0.bounds.maxX }.max() ?? 1
        let minY = graph.nodes.map { $0.bounds.minY }.min() ?? 0
        let maxY = graph.nodes.map { $0.bounds.maxY }.max() ?? 1
        let gw = max(maxX - minX, 1), gh = max(maxY - minY, 1)
        let pad: CGFloat = 44
        let scale = max(min((size.width - 2 * pad) / gw, (size.height - 2 * pad) / gh), 0.05)
        let offX = (size.width - gw * scale) / 2 - minX * scale
        let offY = (size.height - gh * scale) / 2 - minY * scale
        func pt(_ x: Double, _ y: Double) -> CGPoint { CGPoint(x: x * scale + offX, y: y * scale + offY) }
        func centerOf(_ n: DiagramNode) -> CGPoint { pt(n.bounds.cx, n.bounds.cy) }

        // edges (under nodes)
        for e in graph.edges {
            guard let a = graph.nodes.first(where: { $0.id == e.from }),
                  let b = graph.nodes.first(where: { $0.id == e.to }) else { continue }
            let p1 = centerOf(a), p2 = centerOf(b)
            var line = Path(); line.move(to: p1); line.addLine(to: p2)
            ctx.stroke(line, with: .color(Sig.muted), lineWidth: 2)
            // arrowhead
            let ang = atan2(p2.y - p1.y, p2.x - p1.x)
            let tip = CGPoint(x: p2.x - cos(ang) * 14, y: p2.y - sin(ang) * 14)
            var head = Path()
            head.move(to: tip)
            head.addLine(to: CGPoint(x: tip.x - cos(ang - 0.5) * 12, y: tip.y - sin(ang - 0.5) * 12))
            head.addLine(to: CGPoint(x: tip.x - cos(ang + 0.5) * 12, y: tip.y - sin(ang + 0.5) * 12))
            head.closeSubpath()
            ctx.fill(head, with: .color(Sig.muted))
        }
        // nodes
        for n in graph.nodes {
            let c = centerOf(n)
            let w = max(n.bounds.w * scale, 56), h = max(n.bounds.h * scale, 34)
            let r = CGRect(x: c.x - w / 2, y: c.y - h / 2, width: w, height: h)
            let tint = shapeTint(n.kind)
            let shape: Path
            switch n.kind {
            case .rectangle: shape = Path(roundedRect: r, cornerRadius: 9)
            case .ellipse: shape = Path(ellipseIn: r)
            case .diamond:
                var p = Path()
                p.move(to: CGPoint(x: r.midX, y: r.minY)); p.addLine(to: CGPoint(x: r.maxX, y: r.midY))
                p.addLine(to: CGPoint(x: r.midX, y: r.maxY)); p.addLine(to: CGPoint(x: r.minX, y: r.midY)); p.closeSubpath()
                shape = p
            }
            ctx.fill(shape, with: .color(tint.opacity(0.18)))
            ctx.stroke(shape, with: .color(tint), lineWidth: 2)
            let label = n.text.isEmpty ? "…" : n.text
            ctx.draw(Text(label).font(.system(size: 12, weight: .bold)).foregroundColor(Sig.text), at: c)
        }
    }
}

struct SketchToDiagramView: View {
    @StateObject private var model = SketchModel()
    @Environment(\.dismiss) private var dismiss
    @State private var copied = false

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            VStack(spacing: 12) {
                HStack {
                    Button { dismiss() } label: {
                        HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Home") }
                            .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                    }
                    Spacer()
                    Text("Sketch → Diagram").font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                    Spacer()
                    Button { tactile(); model.clear() } label: {
                        Image(systemName: "trash").font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.faint)
                    }
                }.padding(.horizontal, 16).padding(.top, 8)

                // Draw
                ZStack(alignment: .topLeading) {
                    PencilCanvas(drawing: $model.drawing, editable: true)
                    if model.drawing.strokes.isEmpty {
                        Text("Draw here ✏️").font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.faint).padding(14)
                    }
                }
                .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18))
                .overlay(RoundedRectangle(cornerRadius: 18).stroke(Sig.line, lineWidth: 1))
                .frame(maxHeight: .infinity)
                .padding(.horizontal, 14)

                // Recognize-with-AI (the local vision model rescues messy sketches)
                Button { model.recognizeWithAI() } label: {
                    HStack(spacing: 8) {
                        if model.vlmBusy { ProgressView().tint(.black) } else { Image(systemName: "sparkles") }
                        Text(model.vlmBusy ? "Reading your sketch…" : "Recognize with AI")
                    }
                    .font(.system(size: 15, weight: .heavy)).foregroundStyle(.black)
                    .frame(maxWidth: .infinity).frame(height: 50)
                    .background(Sig.accent.opacity(model.drawing.strokes.isEmpty ? 0.3 : 1), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .disabled(model.drawing.strokes.isEmpty || model.vlmBusy)
                .padding(.horizontal, 14)
                if !model.vlmError.isEmpty {
                    Text(model.vlmError).font(.caption).foregroundStyle(Sig.warn).padding(.horizontal, 16)
                }

                // Live diagram
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(model.usedAI ? "AI DIAGRAM" : "LIVE DIAGRAM").font(.system(size: 11, weight: .heavy)).tracking(1.4)
                            .foregroundStyle(model.usedAI ? Sig.accent : Sig.faint)
                        if model.usedAI && !model.diagramType.isEmpty {
                            Text(model.diagramType).font(.system(size: 10, weight: .heavy)).foregroundStyle(Sig.local)
                                .padding(.horizontal, 7).padding(.vertical, 2).background(Sig.local.opacity(0.16), in: Capsule())
                        }
                        Spacer()
                        if !model.usedAI && !model.graph.nodes.isEmpty {
                            Text("\(model.graph.nodes.count) nodes · \(model.graph.edges.count) edges")
                                .font(.system(size: 11, weight: .semibold)).foregroundStyle(Sig.muted)
                        }
                    }
                    Group {
                        if model.mermaid.isEmpty {
                            VStack(spacing: 8) {
                                Image(systemName: "scribble.variable").font(.system(size: 26)).foregroundStyle(Sig.faint)
                                Text("Draw boxes, diamonds and arrows — or tap Recognize with AI.")
                                    .font(.system(size: 13)).foregroundStyle(Sig.faint).multilineTextAlignment(.center)
                            }.frame(maxWidth: .infinity, maxHeight: .infinity)
                        } else {
                            MermaidWebView(code: model.mermaid)
                        }
                    }
                    .frame(height: 240)
                    .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    if !model.mermaid.isEmpty {
                        HStack {
                            Text(model.mermaid).font(.system(size: 11, design: .monospaced)).foregroundStyle(Sig.muted).lineLimit(3)
                            Spacer(minLength: 8)
                            Button {
                                UIPasteboard.general.string = model.mermaid; tactile(.medium)
                                withAnimation { copied = true }
                                DispatchQueue.main.asyncAfter(deadline: .now() + 1.3) { withAnimation { copied = false } }
                            } label: {
                                Image(systemName: copied ? "checkmark.circle.fill" : "doc.on.doc")
                                    .foregroundStyle(copied ? Sig.ok : Sig.accent)
                            }
                            ShareLink(item: model.mermaid) { Image(systemName: "square.and.arrow.up").foregroundStyle(Sig.accent) }
                        }
                        .padding(10).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12))
                    }
                }
                .padding(.horizontal, 14).padding(.bottom, 10)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .preferredColorScheme(.dark)
    }
}

// MARK: - Meeting list

struct MeetingListView: View {
    @StateObject private var model = CaptureModel()
    @State private var capturing = false
    @State private var appeared = false
    @State private var recordPulse = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        NavigationStack {
            ZStack {
                background
                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        header
                        Button { tactile(.medium); capturing = true } label: { recordHero }
                            .buttonStyle(PressableCard())
                            .accessibilityLabel("New recording — capture a meeting on-device")
                        HStack(spacing: 12) {
                            NavigationLink { ModelsView() } label: { modelsCta }.buttonStyle(PressableCard())
                            NavigationLink { SketchToDiagramView() } label: { sketchCta }.buttonStyle(PressableCard())
                        }
                        if !model.error.isEmpty { errorNote(model.error) }
                        if model.meetings.isEmpty {
                            emptyState.transition(.opacity)
                        } else {
                            Text("RECENT").font(.system(size: 11, weight: .heavy)).tracking(1.6)
                                .foregroundStyle(Sig.faint).padding(.top, 6).padding(.leading, 2)
                            ForEach(Array(model.meetings.enumerated()), id: \.element.id) { i, m in
                                NavigationLink { MeetingDetailView(meeting: m) } label: { meetingRow(m) }
                                    .buttonStyle(PressableCard())
                                    .opacity(appeared ? 1 : 0)
                                    .offset(y: appeared ? 0 : 14)
                                    .animation(reduceMotion ? nil : .spring(response: 0.5, dampingFraction: 0.82)
                                        .delay(0.05 + Double(i) * 0.05), value: appeared)
                            }
                        }
                    }
                    .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
                }
            }
            .navigationDestination(isPresented: $capturing) {
                CaptureView(model: model, done: { capturing = false })
            }
            #if targetEnvironment(simulator)
            // Design-screenshot convenience: HS_DEMO=1 opens straight to the live canvas; HS_DEMO_HOME seeds rows.
            .onAppear {
                if ProcessInfo.processInfo.environment["HS_DEMO_HOME"] == "1" { model.seedHomeDemo() }
                if ProcessInfo.processInfo.environment["HS_DEMO"] == "1" { capturing = true }
            }
            #endif
            .toolbar(.hidden, for: .navigationBar)
        }
        .tint(Sig.accent)
        .onAppear {
            model.refresh()
            withAnimation(reduceMotion ? nil : .spring(response: 0.6, dampingFraction: 0.85)) { appeared = true }
            if !reduceMotion { recordPulse = true }
        }
    }

    // A cinematic dark wash with a soft amber glow up top — depth, not a flat fill.
    private var background: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(0.16)).frame(width: 420)
                .blur(radius: 130).offset(x: 150, y: -300).ignoresSafeArea()
            Circle().fill(Sig.local.opacity(0.10)).frame(width: 360)
                .blur(radius: 140).offset(x: -180, y: -180).ignoresSafeArea()
        }
    }

    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 7) {
                HStack(spacing: 7) {
                    Image(systemName: "lock.fill").font(.system(size: 9, weight: .black))
                    Text("ON-DEVICE · NOTHING LEAVES").font(.system(size: 10, weight: .heavy)).tracking(1.4)
                }
                .foregroundStyle(Sig.local)
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background(Sig.local.opacity(0.12), in: Capsule())
                .overlay(Capsule().strokeBorder(Sig.local.opacity(0.25), lineWidth: 1))
                Text("Meetings").font(.system(size: 38, weight: .heavy)).foregroundStyle(Sig.text)
                    .shadow(color: .black.opacity(0.3), radius: 8, y: 3)
            }
            Spacer()
            if !model.meetings.isEmpty {
                Text("\(model.meetings.count)").font(.system(size: 20, weight: .heavy).monospacedDigit())
                    .foregroundStyle(Sig.text)
                    .frame(width: 46, height: 46).signalCard(Sig.s2, radius: 14)
            }
        }
        .padding(.top, 8)
        .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 10)
    }

    // The hero: a tall gradient card with a pulsing record glyph + a clear primary action.
    private var recordHero: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle().stroke(.white.opacity(0.35), lineWidth: 2).frame(width: 58, height: 58)
                    .scaleEffect(recordPulse ? 1.12 : 0.92).opacity(recordPulse ? 0 : 0.9)
                    .animation(reduceMotion ? nil : .easeOut(duration: 1.8).repeatForever(autoreverses: false), value: recordPulse)
                Circle().fill(.black.opacity(0.16)).frame(width: 58, height: 58)
                Image(systemName: "mic.fill").font(.system(size: 23, weight: .bold)).foregroundStyle(.black)
            }
            VStack(alignment: .leading, spacing: 3) {
                Text("New recording").font(.system(size: 21, weight: .heavy)).foregroundStyle(.black)
                Text("Tap to capture — transcribed live on this iPad")
                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(.black.opacity(0.68))
            }
            Spacer()
            Image(systemName: "arrow.right").font(.system(size: 17, weight: .black)).foregroundStyle(.black.opacity(0.72))
        }
        .padding(.horizontal, 22).padding(.vertical, 22)
        .background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.22), lineWidth: 1))
        .shadow(color: Sig.accent.opacity(0.45), radius: 26, y: 12)
        .opacity(appeared ? 1 : 0).scaleEffect(appeared ? 1 : 0.96)
    }

    private var modelsCta: some View {
        let n = ModelFiles.installed().count
        return tile(chip: GlyphChip(system: "cpu.fill"),
                    title: "Models",
                    subtitle: n == 0 ? "Import to enable intelligence" : "\(n) on this iPad")
    }

    private var sketchCta: some View {
        tile(chip: GlyphChip(system: "scribble.variable", gradient: Sig.accentGradient),
             title: "Sketch → Diagram",
             subtitle: "Pencil boxes become Mermaid")
    }

    // A compact, equal-weight secondary tile (the two sit side by side under the hero).
    private func tile(chip: GlyphChip, title: String, subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 11) {
            HStack {
                chip
                Spacer()
                Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                Text(subtitle).font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint).lineLimit(1)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(15).signalCard(radius: 20)
    }

    private func meetingRow(_ m: Meeting) -> some View {
        HStack(spacing: 14) {
            GlyphChip(system: "waveform")
            VStack(alignment: .leading, spacing: 3) {
                Text(m.title ?? "Untitled meeting").font(.system(size: 16, weight: .bold))
                    .foregroundStyle(Sig.text).lineLimit(1)
                Text(m.startedAt.formatted(date: .abbreviated, time: .shortened))
                    .font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Text("\(m.segments.count) segs").font(.system(size: 11, weight: .heavy).monospacedDigit())
                .foregroundStyle(Sig.muted)
                .padding(.horizontal, 9).padding(.vertical, 5).background(Sig.s3, in: Capsule())
            Image(systemName: "chevron.right").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
        }
        .padding(13).signalCard(radius: 16)
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle().fill(Sig.accentSoft).frame(width: 84, height: 84)
                Circle().strokeBorder(Sig.accent.opacity(0.3), lineWidth: 1).frame(width: 84, height: 84)
                Image(systemName: "waveform").font(.system(size: 32, weight: .semibold)).foregroundStyle(Sig.accent)
            }
            VStack(spacing: 6) {
                Text("No meetings yet").font(.system(size: 18, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Press New recording to capture your first meeting. It transcribes live and stays on this iPad — nothing leaves.")
                    .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.faint)
                    .multilineTextAlignment(.center).frame(maxWidth: 320).lineSpacing(2)
            }
        }
        .frame(maxWidth: .infinity).padding(.top, 54)
    }

    private func errorNote(_ s: String) -> some View {
        HStack(spacing: 9) {
            Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 13, weight: .bold))
            Text(s).font(.system(size: 13, weight: .medium))
        }
        .foregroundStyle(Sig.bad)
        .padding(13).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.bad.opacity(0.12), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Sig.bad.opacity(0.3), lineWidth: 1))
    }
}

// MARK: - Capture screen

struct CaptureView: View {
    @ObservedObject var model: CaptureModel
    var done: () -> Void
    @State private var pane: Pane = {
        #if targetEnvironment(simulator)
        if ProcessInfo.processInfo.environment["HS_DEMO_NOTES"] == "1" { return .notes }
        #endif
        return .transcript
    }()
    enum Pane: String, CaseIterable { case transcript = "Transcript", notes = "Notes" }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            if model.recording { recordingBody } else { lobbyBody }
            flashToast
        }
        .animation(.spring(response: 0.5, dampingFraction: 0.82), value: model.recording)
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: model.flash)
        .toolbar(.hidden, for: .navigationBar)
        // HSM-14 — sending a transcript moment to notes flips to the Notes pane so the user
        // sees it land in the canvas.
        .onChange(of: model.notesJump) { _, _ in withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { pane = .notes } }
        #if targetEnvironment(simulator)
        .onAppear { model.seedDemo(size: CGSize(width: 720, height: 1300), boardTop: max(176, 1300 * 0.42)) }
        #endif
    }

    // The "lobby": not recording. Title, pane picker, the canvas, and the big Record button.
    private var lobbyBody: some View {
        VStack(spacing: 16) {
            HStack {
                Text(model.transcribing ? "Transcribing…" : "Ready")
                    .font(.title3.bold()).foregroundStyle(Sig.text)
                Spacer()
                Button("Done") { done() }.foregroundStyle(Sig.muted)
            }
            Picker("", selection: $pane) {
                ForEach(Pane.allCases, id: \.self) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            paneContent
            recordButton
        }
        .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
    }

    // Recording: the canvas goes full-bleed and the controls collapse into a single compact,
    // DRAGGABLE floating recorder (move it anywhere). No big button, no big segmented bar —
    // the surface is the meeting, the chrome gets out of the way (HSM-14, owner's "OS-like" ask).
    private var recordingBody: some View {
        GeometryReader { geo in
            ZStack(alignment: .topLeading) {
                paneContent
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .padding(.horizontal, 12).padding(.top, 12).padding(.bottom, 2)
                // The recorder docks/floats/minimizes within this surface (HSM-14-13) — it knows
                // the viewport so a drag can snap it to an edge home.
                FloatingRecorder(model: model, pane: $pane, viewport: geo.size,
                                 onStop: { Task { await model.stopRecording(); done() } })
            }
            .frame(width: geo.size.width, height: geo.size.height)
        }
        .frame(maxWidth: 860).frame(maxWidth: .infinity)
        .transition(.opacity)
    }

    @ViewBuilder private var paneContent: some View {
        if pane == .transcript {
            LiveCaptureCanvas(model: model)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Sig.bg, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Sig.line, lineWidth: 1))
        } else {
            notesPane
        }
    }

    @ViewBuilder private var flashToast: some View {
        if !model.flash.isEmpty {
            VStack {
                HStack(spacing: 8) {
                    Image(systemName: "sparkles").font(.system(size: 13, weight: .bold))
                    Text(model.flash).font(.system(size: 13, weight: .semibold))
                }
                .foregroundStyle(.black).padding(.horizontal, 14).padding(.vertical, 10)
                .background(Sig.accent, in: Capsule()).shadow(color: .black.opacity(0.4), radius: 10, y: 4)
                .padding(.top, 8)
                Spacer()
            }
            .transition(.move(edge: .top).combined(with: .opacity)).zIndex(50)
        }
    }

    @ViewBuilder private var notesPane: some View {
        if let nb = model.notebook {
            NotebookView(model: nb, editable: true,    // ink + transcript coexist; strokes persist
                         onPromote: { card, type in model.promoteNoteToArtifact(card.text, type: type) })
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

/// HSM-14 — the floating recorder. While recording, ALL the meeting controls collapse into this
/// one compact, frosted, DRAGGABLE capsule: stop, a live elapsed timer, the audio-reactive
/// waveform, mark-this-moment, and a transcript/notes toggle. Drag it anywhere — the canvas is
/// the meeting; the chrome floats and moves out of the way (the owner's "OS-like" ask).
struct FloatingRecorder: View {
    @ObservedObject var model: CaptureModel
    @Binding var pane: CaptureView.Pane
    let viewport: CGSize
    let onStop: () -> Void
    @State private var drag: CGSize = .zero
    @State private var dragging = false

    private var home: CGPoint {
        RecorderSnap.home(for: model.recorderLayout.dock, in: viewport, free: model.recorderLayout.freeCenter)
    }

    var body: some View {
        Group {
            if model.recorderLayout.minimized { orb } else { capsule }
        }
        .scaleEffect(dragging ? 1.04 : 1)
        .position(x: home.x + drag.width, y: home.y + drag.height)
        .gesture(dragGesture)
        .animation(.spring(response: 0.42, dampingFraction: 0.82), value: model.recorderLayout)
        .animation(.spring(response: 0.42, dampingFraction: 0.82), value: drag == .zero)
    }

    // The drag both moves the recorder and, on release, snaps it to the nearest edge home (medium
    // haptic) or leaves it floating where it was let go (light haptic), clamped on-screen so it can
    // never be lost. The snap decision is RuntimeCore's `RecorderSnap` (host-tested).
    private var dragGesture: some Gesture {
        DragGesture()
            .onChanged { v in
                if !dragging { withAnimation(.spring(response: 0.2, dampingFraction: 0.7)) { dragging = true } }
                drag = v.translation
            }
            .onEnded { v in
                let dropped = CGPoint(x: home.x + v.translation.width, y: home.y + v.translation.height)
                let dock = RecorderSnap.dock(forCenter: dropped, in: viewport)
                let free = dock == .floating ? RecorderSnap.clamp(dropped, in: viewport) : nil
                withAnimation(.spring(response: 0.42, dampingFraction: 0.78)) {
                    model.dockRecorder(dock, freeCenter: free)
                    drag = .zero
                    dragging = false
                }
                tactile(dock == .floating ? .light : .medium)
            }
    }

    // The full control capsule (expanded state).
    private var capsule: some View {
        HStack(spacing: 14) {
            Button(action: onStop) {
                ZStack {
                    Circle().fill(Sig.bad).frame(width: 40, height: 40)
                        .shadow(color: Sig.bad.opacity(0.7), radius: dragging ? 2 : 6)
                    RoundedRectangle(cornerRadius: 3.5).fill(.white).frame(width: 14, height: 14)
                }
            }.buttonStyle(.plain)

            VStack(alignment: .leading, spacing: 1) {
                TimelineView(.periodic(from: .now, by: 1)) { _ in
                    Text(clockString(model.elapsedSeconds))
                        .font(.system(size: 16, weight: .heavy).monospacedDigit()).foregroundStyle(Sig.text)
                }
                HStack(spacing: 3) {
                    Circle().fill(Sig.bad).frame(width: 5, height: 5)
                    Text("REC · on-device").font(.system(size: 8, weight: .bold)).tracking(0.5).foregroundStyle(Sig.faint)
                }
            }

            MicWaveform(level: CGFloat(model.level), active: true, bars: 16, height: 26).frame(width: 96)

            Rectangle().fill(Sig.line).frame(width: 1, height: 28)

            Button { model.mark(); tactile(.medium) } label: {
                VStack(spacing: 0) {
                    Image(systemName: "star.circle.fill").font(.system(size: 21))
                    if model.markCount > 0 { Text("\(model.markCount)").font(.system(size: 9, weight: .heavy)) }
                }.foregroundStyle(Sig.local)
            }.buttonStyle(.plain)

            Button {
                withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
                    pane = pane == .transcript ? .notes : .transcript
                }; tactile()
            } label: {
                Image(systemName: pane == .transcript ? "pencil.and.outline" : "waveform")
                    .font(.system(size: 19, weight: .semibold)).foregroundStyle(Sig.accent)
                    .frame(width: 30, height: 30)
            }.buttonStyle(.plain)

            // Collapse to the rec orb — the meeting keeps running; the chrome gets fully out of the way.
            Button { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { model.toggleRecorderMinimized() }; tactile() } label: {
                Image(systemName: "minus.circle.fill")
                    .font(.system(size: 19, weight: .semibold)).foregroundStyle(Sig.faint)
                    .frame(width: 30, height: 30)
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 16).padding(.vertical, 10)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().stroke(Sig.line, lineWidth: 1))
        .shadow(color: .black.opacity(0.5), radius: dragging ? 22 : 14, y: dragging ? 12 : 7)
    }

    // The minimized "rec orb": a glanceable recording heartbeat + a live timer tick. Tap to
    // re-expand — one gesture restores every control (the "never trap" rule). Drag to dock it.
    private var orb: some View {
        Button { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { model.toggleRecorderMinimized() }; tactile(.medium) } label: {
            ZStack {
                Circle().fill(.ultraThinMaterial).frame(width: 60, height: 60)
                    .overlay(Circle().stroke(Sig.line, lineWidth: 1))
                Circle().stroke(Sig.bad.opacity(0.55), lineWidth: 2).frame(width: 60, height: 60)
                    .scaleEffect(1 + CGFloat(model.level) * 0.18)   // breathes with the mic
                VStack(spacing: 1) {
                    Circle().fill(Sig.bad).frame(width: 7, height: 7)
                    TimelineView(.periodic(from: .now, by: 1)) { _ in
                        Text(clockString(model.elapsedSeconds))
                            .font(.system(size: 11, weight: .heavy).monospacedDigit()).foregroundStyle(Sig.text)
                    }
                }
            }
        }
        .buttonStyle(.plain)
        .shadow(color: .black.opacity(0.5), radius: dragging ? 18 : 10, y: dragging ? 9 : 5)
    }
}

// MARK: - The live capture canvas (HSM-14)

/// The meeting, alive. Finished utterances float up as bubbles; the words still being heard
/// pulse as a live caption; and you grab any bubble — finger or Apple Pencil — and tack it to
/// the board below. A tacked bubble isn't decoration: it marks that moment so the on-device
/// intelligence weights what you cared about. This replaces the old wall-of-text transcript.
struct LiveCaptureCanvas: View {
    @ObservedObject var model: CaptureModel

    var body: some View {
        GeometryReader { geo in
            // The whole surface is the board. The stream lives in the top strip; a bubble dropped
            // below `pinFloor` is placed loose, and a bubble dropped on the tack target is TACKED
            // (a marked moment that steers the intelligence) — free-place vs tack (HSM-14-13).
            let pinFloor: CGFloat = max(140, geo.size.height * 0.17)
            let tack = tackZone(in: geo.size)
            ZStack(alignment: .topLeading) {
                // One free-form desktop — a subtle dot-grid surface, not two stacked boxes.
                RoundedRectangle(cornerRadius: 18, style: .continuous).fill(Sig.s1)
                    .overlay(DesktopGrid().clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous)))
                    .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Sig.line, lineWidth: 1))

                ForEach(model.pinned) { n in
                    PinnedNoteView(
                        note: n,
                        onMove: { model.movePin(n.id, to: $0, in: geo.size, boardTop: pinFloor) },
                        onRemove: { withAnimation(.spring(response: 0.32, dampingFraction: 0.7)) { model.unpin(n.id) }; tactile() },
                        onTack: { withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) { model.tackExisting(n.id) } },
                        onResize: { model.resizePin(n.id, to: $0) },
                        onSendToNotes: { model.sendToNotes(n.text) })
                }

                if model.liveBubbles.isEmpty && model.partial.isEmpty {
                    idleHeader.frame(width: geo.size.width, height: geo.size.height)
                } else {
                    stream(pinFloor: pinFloor, size: geo.size, tack: tack)
                }

                tackTarget(tack)            // appears only while a bubble is being dragged

                footerChip
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                    .padding(14)

                tidyControl(size: geo.size, pinFloor: pinFloor)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
                    .padding(14)
            }
            .coordinateSpace(name: "canvas")
            .frame(width: geo.size.width, height: geo.size.height)
            #if targetEnvironment(simulator)
            .onAppear { model.seedDemo(size: geo.size, boardTop: max(140, geo.size.height * 0.17)) }
            #endif
        }
        .frame(minHeight: 440)
    }

    // Utterances stream from the top; drag one out to place it loose, or onto the tack target to tack it.
    private func stream(pinFloor: CGFloat, size: CGSize, tack: CGRect) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(model.liveBubbles) { b in
                LiveBubbleView(bubble: b, boardTop: pinFloor,
                               onDragChanged: { loc in model.bubbleDragging = true; model.bubbleDragPoint = loc },
                               onDrop: { loc in
                                   let committed = withAnimation(.spring(response: 0.4, dampingFraction: 0.75)) {
                                       model.drop(b, at: loc, in: size, pinFloor: pinFloor, tackZone: tack)
                                   }
                                   model.bubbleDragging = false; model.bubbleDragPoint = nil
                                   return committed
                               },
                               onSendToNotes: { model.sendToNotes(b.text) })
            }
            if !model.partial.isEmpty { LiveCaption(text: model.partial) }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 10).padding(.top, 12)
        .frame(width: size.width, height: size.height, alignment: .top)
    }

    // The tack zone (HSM-14-13): a fixed target near the bottom where a dropped bubble becomes a
    // marked moment. Everywhere else is free placement.
    private func tackZone(in size: CGSize) -> CGRect {
        let w = min(264, size.width - 72), h: CGFloat = 56
        return CGRect(x: (size.width - w) / 2, y: max(120, size.height - h - 80), width: w, height: h)
    }

    // HSM-14-13 deliverable 4 — one-tap tidy (re-flow loose cards into a readable grid) with a
    // single undo. Shows only when there's something to tidy or undo, so it never clutters.
    @ViewBuilder private func tidyControl(size: CGSize, pinFloor: CGFloat) -> some View {
        if model.looseCount > 1 || model.canUndoTidy {
            HStack(spacing: 10) {
                if model.canUndoTidy {
                    Button { withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { model.undoTidy() } } label: {
                        Label("Undo", systemImage: "arrow.uturn.backward").font(.system(size: 11, weight: .bold))
                            .foregroundStyle(Sig.muted)
                    }.buttonStyle(.plain)
                }
                if model.looseCount > 1 {
                    Button { withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { model.tidyLoose(in: size, pinFloor: pinFloor) } } label: {
                        Label("Tidy", systemImage: "square.grid.2x2").font(.system(size: 11, weight: .bold))
                            .foregroundStyle(Sig.accent)
                    }.buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 12).padding(.vertical, 8)
            .background(.ultraThinMaterial, in: Capsule())
            .overlay(Capsule().stroke(Sig.line, lineWidth: 1))
        }
    }

    // The target only materializes while a bubble is being dragged, and lights up when the drag is
    // over it — a discoverable "drop here to tack" affordance that never clutters the resting canvas.
    @ViewBuilder private func tackTarget(_ zone: CGRect) -> some View {
        if model.bubbleDragging {
            let over = model.bubbleDragPoint.map { zone.contains($0) } ?? false
            HStack(spacing: 7) {
                pixelAsset("pushpin", size: 16, fallback: "pin.fill", tint: over ? Sig.accent : Sig.muted)
                Text(over ? "Release to tack — steers the intelligence" : "Drop here to tack")
                    .font(.system(size: 12, weight: .bold)).foregroundStyle(over ? Sig.accent : Sig.muted)
            }
            .frame(width: zone.width, height: zone.height)
            .background(over ? Sig.accent.opacity(0.16) : Sig.s2.opacity(0.7),
                        in: RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
                .strokeBorder(over ? Sig.accent : Sig.line, style: StrokeStyle(lineWidth: over ? 2 : 1.5, dash: [7, 5])))
            .scaleEffect(over ? 1.06 : 1)
            .position(x: zone.midX, y: zone.midY)
            .animation(.spring(response: 0.28, dampingFraction: 0.7), value: over)
            .transition(.opacity.combined(with: .scale(scale: 0.9)))
            .zIndex(15)
        }
    }

    private var footerChip: some View {
        let tacked = model.tackedCount, loose = model.pinned.count - tacked
        return HStack(spacing: 6) {
            pixelAsset("pushpin", size: 13, fallback: "pin.fill", tint: Sig.accent)
            Text(model.pinned.isEmpty
                 ? (model.recording ? "Drag a moment out to place it — drop on the tack target to steer the intelligence" : "Your moments live here")
                 : (loose > 0 ? "\(tacked) tacked · \(loose) placed" : "\(tacked) tacked"))
                .font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.muted)
        }
        .padding(.horizontal, 11).padding(.vertical, 7)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().stroke(Sig.line, lineWidth: 1))
    }

    @ViewBuilder private var idleHeader: some View {
        VStack(spacing: 12) {
            if model.recording {
                MicWaveform(level: CGFloat(model.level), active: true, bars: 32, height: 52)
            } else {
                pixelAsset("qlippy", size: 58, fallback: "mic.circle.fill", tint: Sig.faint)
            }
            Text(model.recording ? "Listening… your words will float up here." : "Press Record — your meeting comes alive here.")
                .font(.callout).foregroundStyle(Sig.faint).multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity).padding(.bottom, 18)
    }

}

/// HSM-14 — a faint dot grid: the "desktop" texture that makes the capture surface read as a
/// spatial board you arrange on, not a flat page.
struct DesktopGrid: View {
    var body: some View {
        Canvas { ctx, size in
            let step: CGFloat = 26, d: CGFloat = 1.4
            var y = step / 2
            while y < size.height {
                var x = step / 2
                while x < size.width {
                    ctx.fill(Path(ellipseIn: CGRect(x: x - d / 2, y: y - d / 2, width: d, height: d)), with: .color(Sig.line))
                    x += step
                }
                y += step
            }
        }
        .allowsHitTesting(false)
    }
}

/// HSM-14 — the audio-reactive VU. Bars dance to the live mic amplitude (`level`) with a
/// travelling shimmer, so the control plane visibly responds to sound the instant it arrives —
/// before any transcription. Quiet → a gentle idle ripple; loud → tall bars.
struct MicWaveform: View {
    var level: CGFloat
    var active: Bool
    var bars: Int = 28
    var height: CGFloat = 44

    var body: some View {
        let amp = active ? min(1, max(0.04, level * 7)) : 0
        TimelineView(.animation) { ctx in
            let t = ctx.date.timeIntervalSinceReferenceDate
            HStack(alignment: .center, spacing: 3) {
                ForEach(0..<bars, id: \.self) { i in
                    let shimmer = 0.45 + 0.55 * (0.5 + 0.5 * sin(t * 7 + Double(i) * 0.55))
                    let centerBias = 1 - abs(Double(i) - Double(bars) / 2) / Double(bars)   // taller in the middle
                    let h = 3 + CGFloat(shimmer * centerBias) * amp * height + (active ? 2 : 0)
                    Capsule()
                        .fill(LinearGradient(colors: [Sig.accent, Sig.accent.opacity(0.55)], startPoint: .bottom, endPoint: .top))
                        .frame(width: 3, height: max(3, h))
                        .opacity(active ? 1 : 0.35)
                }
            }
            .animation(.easeOut(duration: 0.08), value: amp)
        }
        .frame(height: height)
    }
}

/// A streaming utterance. Springs in on appear; lifts (shadow + scale) the instant you grab it;
/// drop it below the fold to tack it to the board, or release high to snap it back.
struct LiveBubbleView: View {
    let bubble: LiveBubble
    let boardTop: CGFloat
    var onDragChanged: (CGPoint) -> Void = { _ in }
    let onDrop: (CGPoint) -> Bool          // returns whether the drop committed (else snap home)
    var onSendToNotes: () -> Void = {}
    @State private var offset: CGSize = .zero
    @State private var lifting = false
    @State private var appeared = false

    var body: some View {
        HStack(spacing: 9) {
            Circle().fill(Sig.accent).frame(width: 7, height: 7)
                .shadow(color: Sig.accent.opacity(0.7), radius: 3)
            Text(bubble.text)
                .font(.system(size: 15, weight: .medium)).foregroundStyle(Sig.text)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 4)
            Image(systemName: "hand.draw.fill").font(.system(size: 11)).foregroundStyle(lifting ? Sig.accent : Sig.faint)
        }
        .padding(.horizontal, 13).padding(.vertical, 10)
        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 15, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous)
            .stroke(lifting ? Sig.accent : Sig.line, lineWidth: lifting ? 1.6 : 1))
        .shadow(color: .black.opacity(lifting ? 0.55 : 0), radius: lifting ? 16 : 0, y: lifting ? 9 : 0)
        .scaleEffect(lifting ? 1.04 : (appeared ? 1 : 0.82))
        .opacity(appeared ? 1 : 0)
        .offset(offset)
        .zIndex(lifting ? 20 : 0)
        .gesture(
            DragGesture(coordinateSpace: .named("canvas"))
                .onChanged { v in
                    if !lifting { withAnimation(.spring(response: 0.2, dampingFraction: 0.7)) { lifting = true }; tactile() }
                    offset = v.translation
                    onDragChanged(v.location)               // drive the tack-target highlight
                }
                .onEnded { v in
                    // Loose-place by default; the tack zone (or the stream) is decided by the canvas.
                    if onDrop(v.location) {
                        tactile(.medium)                     // committed (tacked or placed)
                    } else {
                        withAnimation(.spring(response: 0.35, dampingFraction: 0.68)) { offset = .zero; lifting = false }
                    }
                })
        .onAppear { withAnimation(.spring(response: 0.5, dampingFraction: 0.68)) { appeared = true } }
        .transition(.asymmetric(
            insertion: .scale(scale: 0.8).combined(with: .opacity),
            removal: .opacity))
        .contextMenu {
            Button { onSendToNotes() } label: { Label("Add to notes", systemImage: "square.and.pencil") }
            Button { UIPasteboard.general.string = bubble.text } label: { Label("Copy", systemImage: "doc.on.doc") }
        }
    }
}

/// The words still being transcribed — a glowing, breathing caption beneath the bubbles.
struct LiveCaption: View {
    let text: String
    @State private var pulse = false
    var body: some View {
        HStack(spacing: 8) {
            HStack(spacing: 3) {
                ForEach(0..<3) { i in
                    Capsule().fill(Sig.accent)
                        .frame(width: 3, height: pulse ? 13 : 5)
                        .animation(.easeInOut(duration: 0.5).repeatForever().delay(Double(i) * 0.15), value: pulse)
                }
            }
            Text(text).font(.system(size: 15, weight: .medium)).italic().foregroundStyle(Sig.muted)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 13).padding(.vertical, 8)
        .background(Sig.accent.opacity(0.08), in: RoundedRectangle(cornerRadius: 13))
        .onAppear { pulse = true }
        .transition(.opacity)
    }
}

/// A tacked moment: a brass pushpin holding a slightly-tilted sticky note. Lands with a bounce,
/// drags to reposition, and unpins when you tap its pin.
struct PinnedNoteView: View {
    let note: PinnedNote
    let onMove: (CGPoint) -> Void
    let onRemove: () -> Void
    var onTack: () -> Void = {}
    var onResize: (CGFloat) -> Void = { _ in }
    var onSendToNotes: () -> Void = {}
    @State private var landed = false
    @State private var resizeBase: CGFloat?      // card width at the start of a corner-drag

    var body: some View {
        VStack(spacing: -4) {
            // Only a tacked moment wears the pushpin; a loose card is just a card.
            if note.tacked {
                Button(action: onRemove) {
                    pixelAsset("pushpin", size: 26, fallback: "pin.fill", tint: Sig.accent)
                        .rotationEffect(.degrees(UIImage(named: "pushpin") == nil ? -28 : 0))
                        .shadow(color: .black.opacity(0.4), radius: 3, y: 2)
                }
                .buttonStyle(.plain).zIndex(1)
            }
            Text(note.text)
                .font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.text)
                .lineLimit(8).multilineTextAlignment(.leading)
                .frame(width: note.w, alignment: .leading)            // resize reflows the text
                .padding(.horizontal, 11).padding(.vertical, 10)
                .background(note.tacked ? Sig.s3 : Sig.s2, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous)
                    .stroke(note.tacked ? Sig.accent.opacity(0.4) : Sig.line, lineWidth: 1))
                .overlay(alignment: .bottomTrailing) { resizeHandle }
                .shadow(color: .black.opacity(note.tacked ? 0.45 : 0.3), radius: note.tacked ? 9 : 6, y: note.tacked ? 5 : 4)
        }
        .rotationEffect(.degrees(note.tacked ? note.rot : 0))
        .scaleEffect(landed ? 1 : 1.35)
        .position(note.pos)
        .gesture(
            DragGesture(coordinateSpace: .named("canvas"))
                .onChanged { onMove($0.location) })
        .onAppear { withAnimation(.spring(response: 0.3, dampingFraction: 0.5)) { landed = true }; tactile(note.tacked ? .heavy : .light) }
        .transition(.scale.combined(with: .opacity))
        .contextMenu {
            if !note.tacked {
                Button { onTack() } label: { Label("Tack as moment", systemImage: "pin.fill") }
            }
            Button { onSendToNotes() } label: { Label("Add to notes", systemImage: "square.and.pencil") }
            Button { UIPasteboard.general.string = note.text } label: { Label("Copy", systemImage: "doc.on.doc") }
            Button(role: .destructive) { onRemove() } label: { Label("Remove", systemImage: "trash") }
        }
    }

    // Corner-drag to resize the card width (text reflows; the model clamps to the readable range).
    private var resizeHandle: some View {
        Image(systemName: "arrow.down.right")
            .font(.system(size: 9, weight: .black))
            .foregroundStyle(Sig.faint)
            .frame(width: 22, height: 22)
            .contentShape(Rectangle())
            .offset(x: 4, y: 4)
            .gesture(
                DragGesture()
                    .onChanged { v in
                        if resizeBase == nil { resizeBase = note.w }
                        onResize((resizeBase ?? note.w) + v.translation.width)
                    }
                    .onEnded { _ in resizeBase = nil; tactile() })
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
                    // Stream the single pass — animate the insert so each card materializes in.
                    if !chunk { try? storage?.saveArtifact(a); withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { load() } }
                    Self.glog("w\(wi) ok \(type.rawValue)")
                } catch {
                    lastError = "\(error)"; Self.glog("w\(wi) FAIL \(type.rawValue): \(error)")
                }
            }
        }
        let merged = ArtifactMerge.dedup(all)
        if chunk { for a in merged { try? storage?.saveArtifact(a) }; withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { load() } }
        Self.glog("done produced=\(merged.count)")
        note = merged.isEmpty
            ? "The model produced nothing." + (lastError.isEmpty ? "" : " (\(lastError))")
            : ""
    }

    /// HSM-14 — promote a hand-note into a real `needs_review` artifact that joins the model's
    /// in the intelligence pane (the loop closes: your notes become reviewable intelligence).
    func promoteNote(_ text: String, type: ArtifactType) {
        try? storage?.saveArtifact(noteArtifact(meetingId: meeting.id, type: type, text: text))
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { load() }
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
/// HSM-14 — the MIR profile as a meaningful LENS, not a sort toggle: an icon + a one-line
/// description of what it surfaces first. The lens drives BOTH what gets generated (which
/// artifact types) and the order it reads in — these helpers make that legible in the UI.
private func profileIcon(_ p: MIRProfile) -> String {
    switch p {
    case .balanced: return "circle.grid.cross.fill"
    case .architect: return "ruler.fill"
    case .delivery: return "shippingbox.fill"
    case .product: return "sparkles.rectangle.stack.fill"
    case .incident: return "exclamationmark.octagon.fill"
    }
}
private func profileBlurb(_ p: MIRProfile) -> String {
    switch p {
    case .balanced: return "An even read of the room — decisions, action items, risks and requirements."
    case .architect: return "Leads with the design record — ADRs, decisions and the dependency map."
    case .delivery: return "Plans the work — milestones, action items and what could slip."
    case .product: return "Hears the customer — requirements, customer signals and scope."
    case .incident: return "Reconstructs what happened — timeline, runbook changes and risks."
    }
}
/// mm:ss for the recorder timer.
private func clockString(_ s: Double) -> String {
    let t = Int(max(0, s)); return String(format: "%d:%02d", t / 60, t % 60)
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

// MARK: - Note → artifact promotion (HSM-14)

/// Build a `needs_review` artifact from hand-authored note text — a proposal the user reviews
/// alongside the model's. `pluginId` marks it as note-sourced; confidence is 1.0 (you wrote it).
func noteArtifact(meetingId: String, type: ArtifactType, text: String) -> Artifact {
    Artifact(
        id: UUID().uuidString, meetingId: meetingId, artifactType: type,
        title: noteArtifactTitle(text), bodyMarkdown: text, structuredJson: .object([:]),
        confidence: 1.0, status: .needsReview, pluginId: "holdspeak.mobile.note",
        pluginVersion: "1", sources: [ArtifactSource(sourceType: "note", sourceRef: "handwritten")])
}
private func noteArtifactTitle(_ text: String) -> String {
    let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
    if let c = t.firstIndex(of: ":") { return String(t[..<c]).trimmingCharacters(in: .whitespaces) }  // "Decision: …" → "Decision"
    let words = t.split(separator: " ").prefix(6).joined(separator: " ")
    return words.isEmpty ? "Note" : words
}
/// Guess the artifact type from the snippet so the one-tap "Promote" does the obvious thing;
/// the long-press menu still offers an explicit choice.
func guessArtifactType(_ text: String) -> ArtifactType {
    let t = text.lowercased()
    if t.hasPrefix("decision") || t.contains("decided") || t.contains("we'll go with") { return .decisions }
    if t.hasPrefix("risk") || t.contains("risk") || t.contains("blocker") { return .riskRegister }
    if t.hasPrefix("action") || t.contains("todo") || t.contains("owner") || t.contains("follow up") { return .actionItems }
    if t.hasPrefix("requirement") || t.contains("must ") || t.contains("should ") || t.contains("need to") { return .requirements }
    return .decisions
}

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
    @State private var materialize = false   // HSM-14 — the tint-ring flash when a card first lands

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
        // HSM-14 — a card doesn't just "appear": it MATERIALIZES. A tint-colored ring flashes
        // around it as it lands, then fades — so a freshly-generated insight announces itself.
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(tint, lineWidth: 2.5)
                .opacity(materialize ? 0.9 : 0)
                .shadow(color: tint.opacity(0.85), radius: materialize ? 16 : 0)
                .allowsHitTesting(false)
        )
        .onAppear {
            let d = Double(index) * 0.06
            withAnimation(.spring(response: 0.55, dampingFraction: 0.74).delay(d)) { appeared = true }
            withAnimation(.easeOut(duration: 0.32).delay(d)) { materialize = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + d + 0.65) {
                withAnimation(.easeInOut(duration: 0.85)) { materialize = false }
            }
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

// MARK: - Transcript, recrafted (HSM-14 — alive, not a wall of text in a gray box)

/// A gently-breathing waveform so the transcript feels alive, not static.
struct WaveformBars: View {
    var color: Color = Sig.accent
    var count: Int = 30
    var body: some View {
        TimelineView(.animation) { ctx in
            let t = ctx.date.timeIntervalSinceReferenceDate
            HStack(spacing: 3) {
                ForEach(0..<count, id: \.self) { i in
                    let s = 0.5 + 0.5 * sin(t * 2.1 + Double(i) * 0.45)
                    Capsule().fill(color.opacity(0.3 + 0.45 * s)).frame(width: 3, height: 5 + 16 * s)
                }
            }
        }
        .frame(height: 24)
    }
}

/// One utterance / paragraph — staggered fade-in, speaker-coloured, tap to copy.
struct TranscriptBlock: View {
    let speaker: String?
    let time: Double?
    let text: String
    let color: Color
    let index: Int
    @State private var appeared = false
    @State private var copied = false

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            RoundedRectangle(cornerRadius: 2).fill(color.opacity(0.85)).frame(width: 3)
            VStack(alignment: .leading, spacing: 7) {
                if let speaker, !speaker.isEmpty {
                    HStack(spacing: 8) {
                        ZStack { Circle().fill(color.opacity(0.2))
                            Text(initials(speaker)).font(.system(size: 10, weight: .heavy)).foregroundStyle(color) }
                            .frame(width: 24, height: 24)
                        Text(speaker).font(.system(size: 13, weight: .heavy)).foregroundStyle(color)
                        if let time { Text(timeStr(time)).font(.system(size: 11, weight: .semibold).monospacedDigit()).foregroundStyle(Sig.faint) }
                        Spacer(minLength: 0)
                        if copied { Image(systemName: "checkmark.circle.fill").font(.system(size: 13)).foregroundStyle(Sig.ok) }
                    }
                }
                Text(text).font(.system(size: 16)).foregroundStyle(Sig.text).lineSpacing(5)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(15)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).stroke(Sig.line, lineWidth: 1))
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 14)
        .onAppear { withAnimation(.spring(response: 0.55, dampingFraction: 0.8).delay(Double(index) * 0.05)) { appeared = true } }
        .onTapGesture {
            UIPasteboard.general.string = text; tactile()
            withAnimation { copied = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { withAnimation { copied = false } }
        }
    }
    private func initials(_ s: String) -> String {
        let i = s.split(separator: " ").prefix(2).compactMap { $0.first }.map(String.init).joined()
        return i.isEmpty ? "•" : i.uppercased()
    }
    private func timeStr(_ t: Double) -> String { String(format: "%d:%02d", Int(t) / 60, Int(t) % 60) }
}

struct TranscriptView: View {
    let segments: [Segment]

    var body: some View {
        if segments.isEmpty {
            HStack(spacing: 10) {
                Image(systemName: "waveform.slash").foregroundStyle(Sig.faint)
                Text("No speech was transcribed.").font(.callout).foregroundStyle(Sig.faint)
            }
            .padding(16).frame(maxWidth: .infinity, alignment: .leading)
            .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
        } else {
            VStack(alignment: .leading, spacing: 12) {
                header
                ForEach(Array(blocks.enumerated()), id: \.offset) { i, b in
                    TranscriptBlock(speaker: b.speaker, time: b.time, text: b.text, color: b.color, index: i)
                }
            }
        }
    }

    private var header: some View {
        HStack(spacing: 12) {
            WaveformBars()
            Spacer()
            Text("\(wordCount) words").font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.muted)
            Button { UIPasteboard.general.string = fullText; tactile(.medium) } label: {
                Image(systemName: "doc.on.doc").font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.accent)
            }
            ShareLink(item: fullText) { Image(systemName: "square.and.arrow.up").font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.accent) }
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .background(LinearGradient(colors: [Sig.accent.opacity(0.12), Sig.s1], startPoint: .leading, endPoint: .trailing),
                    in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
    }

    private var fullText: String { segments.map(\.text).joined(separator: "\n\n") }
    private var wordCount: Int { fullText.split(whereSeparator: { $0 == " " || $0 == "\n" }).count }

    /// Multi-segment → speaker utterances; a single run-on segment → readable sentence paragraphs.
    private var blocks: [(speaker: String?, time: Double?, text: String, color: Color)] {
        if segments.count > 1 {
            return segments.map { (speaker: $0.speaker.isEmpty ? "Speaker" : $0.speaker, time: $0.startTime, text: $0.text, color: speakerColor($0.speaker)) }
        }
        guard let seg = segments.first else { return [] }
        return paragraphs(seg.text).map { (speaker: nil, time: nil, text: $0, color: Sig.local) }
    }
    private func speakerColor(_ s: String) -> Color {
        let palette = [Sig.local, Sig.accent, Sig.ok, Sig.warn, Color(hex: 0xB57BEE), Color(hex: 0x3FC7C7)]
        return palette[abs(s.hashValue) % palette.count]
    }
    private func paragraphs(_ text: String) -> [String] {
        var sentences: [String] = []; var cur = ""
        for ch in text {
            cur.append(ch)
            if ch == "." || ch == "!" || ch == "?" {
                let t = cur.trimmingCharacters(in: .whitespaces); if !t.isEmpty { sentences.append(t) }; cur = ""
            }
        }
        let tail = cur.trimmingCharacters(in: .whitespaces); if !tail.isEmpty { sentences.append(tail) }
        if sentences.isEmpty { return [text] }
        var out: [String] = []; var i = 0
        while i < sentences.count { out.append(sentences[i..<min(i + 2, sentences.count)].joined(separator: " ")); i += 2 }
        return out
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
                    TranscriptView(segments: meeting.segments).id(0)

                    Text("NOTES").font(.caption2.weight(.bold)).tracking(1.5).foregroundStyle(Sig.local).padding(.top, 8)
                    // Reloads the meeting's PencilKit pages + pulled-in transcript cards; editable
                    // so notes can be added after, and a card can be promoted into the review.
                    NotebookView(model: notes, editable: true,
                                 onPromote: { card, type in review.promoteNote(card.text, type: type) })
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
            // HSM-14 — the LENS, not a sort toggle. It picks which intelligence to surface first
            // and drives what gets generated. Each lens names what it emphasizes, so changing it
            // is never a mystery: the blurb explains it and the type chips preview its focus.
            VStack(alignment: .leading, spacing: 9) {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(MIRProfile.allCases, id: \.self) { p in
                            let sel = review.profile == p
                            Button {
                                tactile()
                                withAnimation(.spring(response: 0.42, dampingFraction: 0.78)) { review.profile = p }
                            } label: {
                                HStack(spacing: 6) {
                                    Image(systemName: profileIcon(p)).font(.system(size: 12, weight: .bold))
                                    Text(p.rawValue.capitalized).font(.system(size: 13, weight: .heavy))
                                }
                                .foregroundStyle(sel ? .black : Sig.muted)
                                .padding(.horizontal, 13).padding(.vertical, 8)
                                .background(sel ? Sig.accent : Sig.s2, in: Capsule())
                                .overlay(Capsule().stroke(sel ? Color.clear : Sig.line, lineWidth: 1))
                                .scaleEffect(sel ? 1 : 0.96)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, 1).padding(.vertical, 1)
                }
                Text(profileBlurb(review.profile))
                    .font(.system(size: 12.5)).foregroundStyle(Sig.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .transition(.opacity).id(review.profile)
                // The types this lens leads with — a live preview of its focus.
                HStack(spacing: 6) {
                    ForEach(MIRRouter.baseEmphasis[review.profile] ?? [], id: \.self) { t in
                        HStack(spacing: 4) {
                            Image(systemName: artifactGlyph(t)).font(.system(size: 9, weight: .bold))
                            Text(artifactTypeLabel(t)).font(.system(size: 10, weight: .bold))
                        }
                        .foregroundStyle(artifactTint(t))
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(artifactTint(t).opacity(0.14), in: Capsule())
                        .overlay(Capsule().stroke(artifactTint(t).opacity(0.35), lineWidth: 1))
                    }
                }
            }

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
                    VStack(spacing: 2) {
                        HStack(spacing: 6) {
                            Image(systemName: review.hasGeneratedArtifacts ? "arrow.clockwise" : "sparkles")
                            Text(review.hasGeneratedArtifacts ? "Regenerate on-device" : "Generate on-device")
                        }
                        .font(.subheadline.weight(.semibold))
                        Text("Through the \(review.profile.rawValue.capitalized) lens")
                            .font(.system(size: 11, weight: .bold)).opacity(0.65)
                    }
                    .foregroundStyle(.black)
                    .frame(maxWidth: .infinity).padding(.vertical, 11)
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
