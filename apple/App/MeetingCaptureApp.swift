import SwiftUI
import AVFoundation
import Network
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
            ZStack(alignment: .top) {
                // HS_DEMO_NOTEBOOK opens straight onto the notebook surface for a
                // screenshot run (no mic/taps needed); the real entry is the meeting list.
                if ProcessInfo.processInfo.environment["HS_DEMO_NOTEBOOK"] != nil {
                    DemoNotebookView()
                } else if ProcessInfo.processInfo.environment["HS_DEMO_CAPTURE"] != nil {
                    // HSM-20-03 — the live capture canvas straight, for a compact-width screenshot run.
                    NavigationStack { CaptureView(model: CaptureModel(), done: {}) }
                } else if ProcessInfo.processInfo.environment["HS_CLASSIC_HOME"] != nil {
                    MeetingListView()
                        .onOpenURL { url in
                            guard url.pathExtension.lowercased() == "gguf" else { return }
                            try? ModelFiles.importModel(from: url)
                        }
                } else if ProcessInfo.processInfo.environment["HS_REAL_DESK"] != nil {
                    // The 3D physics object desk (HSM-14-19..24), behind a flag while the motion-first
                    // 2.5D diorama is the front door.
                    DeskHome()
                        .onOpenURL { url in
                            guard url.pathExtension.lowercased() == "gguf" else { return }
                            try? ModelFiles.importModel(from: url)
                        }
                } else {
                    // HSM-14 — the premium, motion-first 2.5D DIORAMA is the home (owner-blessed direction):
                    // alive objects, tap-to-focus intelligence, the capture moment. 3D desk behind
                    // HS_REAL_DESK=1; the classic list behind HS_CLASSIC_HOME=1.
                    DioStage()
                }
                // The run queue rides above every screen — the app-wide transparency surface.
                QueueHUD()
                // The proactive presence nudge rides above the queue — it taps YOU (HSM-15-09).
                PresenceNudgeOverlay()
            }
            .preferredColorScheme(.dark)
            .onAppear {
                #if targetEnvironment(simulator)
                let env = ProcessInfo.processInfo.environment
                // LIVE SYNC in-code proof (no App-layer test target): run the desk store's
                // 7-kind snapshot→push→pull→apply + tombstone + LWW round-trip and log it.
                if env["HS_SYNC_SELFCHECK"] == "1" { DeskSyncStore.selfCheck() }
                if env["HS_DEMO_QUEUE"] == "1" {
                    RunQueueStore.shared.seedDemo()
                    RunQueueStore.shared.expanded = env["HS_DEMO_QUEUE_OPEN"] == "1"
                }
                // HSM-15-09 — seed a freshly-waiting agent so BOTH the nudge card AND the HUD
                // waiting lane are visible with no taps. Feeding `ingest` a rising edge fires
                // the nudge; the lane shows the currently-waiting agents.
                if env["HS_DEMO_PRESENCE"] == "1" {
                    PresenceStore.shared.ingest(PresenceStore.demoSeed)
                    // HS_DEMO_PRESENCE_OPEN=1 expands the HUD ledger to show the waiting LANE rows;
                    // default keeps the pill (the always-on ambient lane badge) under the nudge.
                    RunQueueStore.shared.expanded = env["HS_DEMO_PRESENCE_OPEN"] == "1"
                }
                #endif
            }
        }
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
    @Published var diagFrames: Int = 0         // diagnostic: audio frames captured (0 ⇒ no mic audio)
    @Published var diagPeak: Float = 0         // diagnostic: loudest raw RMS this run

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
                            // read the chosen Whisper model from UserDefaults at call time (thread-safe; a
                            // settings change applies on the next recording without rebuilding capture)
                            makeTranscriber: { WhisperKitTranscriber(chunks: $0, model: UserDefaults.standard.string(forKey: "hs.inf.whisper") ?? "base") },   // key == InferenceConfigStore.whisperKey
                            diarize: Self.makeDiarize())
        refresh()
    }

    func refresh() { meetings = mc?.meetings() ?? [] }

    /// HSM-14-17 — the diarize closure handed to `MeetingCapture`. Lazily loads the bundled Core ML
    /// embedder once (on first use, off the main thread by the time `stop()` calls it), and gates on
    /// the live opt-in setting: when OFF it returns the segments untouched, so capture behaves exactly
    /// as before. A fresh `SpeakerDiarizer` per meeting keeps "Speaker 1/2/…" scoped to the recording.
    private static let sharedEmbedder: AudioEmbedding? = { try? AudioEmbedder() }()
    private static func makeDiarize() -> (@Sendable ([Segment], [Int16], Int) -> [Segment])? {
        guard let embedder = sharedEmbedder else { return nil }
        return { segments, audio, sampleRate in
            // Read the toggle at call time so flipping it takes effect without rebuilding capture.
            let on = DispatchQueue.main.sync { InferenceConfigStore.shared.diarizationOn }
            guard on else { return segments }
            return SpeakerDiarizer(embedder: embedder).diarize(segments, audio: audio, sampleRate: sampleRate)
        }
    }

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
                try? await Task.sleep(nanoseconds: 700_000_000)   // poll cadence; the bounded ~10s window keeps each tick cheap
                await mc.tick()
                if case .recording(let t) = mc.state { await MainActor.run { self?.liveTranscript = t; self?.ingest(t) } }
            }
        }
        // Fast, independent poll of the mic amplitude (20 Hz) — the waveform reacts to sound the
        // instant it arrives, with no transcription round-trip.
        levelTicker = Task { [weak self] in
            while !Task.isCancelled, self?.recording == true {
                await MainActor.run {
                    guard let self else { return }
                    self.level = self.mc?.inputLevel ?? 0
                    self.diagFrames = self.mc?.capturedFrames ?? 0
                    self.diagPeak = self.mc?.peakLevel ?? 0
                }
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

/// Thread-safe live mic amplitude (0…~1), gained + instant-attack/fast-decay so a waveform visibly
/// tracks the voice (HSM-15-01). Mirrors `MeetingCapture.updateLevel`; used by the Dictate surface,
/// whose `AudioCaptureService` doesn't expose a level itself.
final class LevelMeter: @unchecked Sendable {
    private let q = DispatchQueue(label: "voice.level")
    private var _level: Float = 0
    var level: Float { q.sync { _level } }
    func reset() { q.sync { _level = 0 } }
    func ingest(_ chunk: AudioChunk) {
        guard !chunk.samples.isEmpty else { return }
        var sum: Float = 0
        for s in chunk.samples { let f = Float(s) / 32768.0; sum += f * f }
        let rms = (sum / Float(chunk.samples.count)).squareRoot()
        let gained = Swift.min(1, rms * 4.5)
        q.sync { _level = Swift.max(gained, _level * 0.74) }
    }
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
            // HSM-18-04 — this is the DICTATION (speak-to-fill) path, so spoken symbols apply here
            // ("new line" -> newline, "open paren" -> "("). Meeting capture (Stores.swift) stays
            // verbatim and never runs this. Built-ins only for now; the user-symbol editor follows.
            if said.isEmpty { self.error = "Didn't catch that — try again, or type it." }
            else { text = SpokenSymbols().process(said) }
        } catch { self.error = "Couldn't transcribe: \(error)" }
    }
}

// MARK: - Meeting list

struct MeetingListView: View {
    @StateObject private var model = CaptureModel()
    @ObservedObject private var peers = DictatePeerStore.shared
    @ObservedObject private var presence = PresenceStore.shared
    @State private var capturing = false
    @State private var appeared = false
    @State private var recordPulse = false
    @State private var showAgentDesk = false
    @State private var showDictate = false
    @State private var showConnect = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        #if targetEnvironment(simulator)
        if ProcessInfo.processInfo.environment["HS_DEMO_GEN"] == "1" { return AnyView(GenTheaterDemo()) }
        if ProcessInfo.processInfo.environment["HS_DEMO_SETTINGS"] == "1" { return AnyView(SettingsDemo()) }
        if ProcessInfo.processInfo.environment["HS_DEMO_WORKBENCH"] == "1" || ProcessInfo.processInfo.environment["HS_DEMO_WORKBENCH_LLM"] == "1" { return AnyView(NavigationStack { WorkbenchView() }) }
        if ProcessInfo.processInfo.environment["HS_DEMO_WB_EXEC"] == "1" { return AnyView(NavigationStack { WorkbenchView() }) }
        if ProcessInfo.processInfo.environment["HS_DEMO_AGENTDESK"] == "1" { return AnyView(AgentDeskDemo()) }
        if ProcessInfo.processInfo.environment["HS_DEMO_DICTATE"] == "1" { return AnyView(DictateDemo()) }
        if ProcessInfo.processInfo.environment["HS_DEMO_CONNECT"] == "1" { return AnyView(ConnectDemo()) }
        #endif
        return AnyView(listBody)
    }

    private var listBody: some View {
        NavigationStack {
            ZStack {
                background
                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        header
                        Button { tactile(.medium); capturing = true } label: { recordHero }
                            .buttonStyle(PressableCard())
                            .accessibilityLabel("New recording — capture a meeting on-device")
                        Button { tactile(.medium); showDictate = true } label: { dictateCta }
                            .buttonStyle(PressableCard())
                            .accessibilityLabel("Dictate to your Mac — talk on this iPad, the words land on your Mac")
                        Button { tactile(.medium); showConnect = true } label: { connectCta }
                            .buttonStyle(PressableCard())
                            .accessibilityLabel("Your Computer — find and pair with your desktop on your network")
                        NavigationLink { WorkbenchView() } label: { workbenchCta }.buttonStyle(PressableCard())
                        NavigationLink { AgentDeskView(state: CompanionBoardState()) } label: { agentDeskCta }.buttonStyle(PressableCard())
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
            .navigationDestination(isPresented: $showAgentDesk) {
                // Opened from a nudge/lane → show the live presence board, not an empty one.
                AgentDeskView(state: presence.board.targets.isEmpty ? CompanionBoardState() : presence.board)
            }
            // A nudge "Answer"/"Open desk" or a HUD lane tap requests the desk; route it here.
            .onChange(of: presence.requestDesk) { _, want in
                if want { showAgentDesk = true; presence.requestDesk = false }
            }
            .navigationDestination(isPresented: $showDictate) {
                DictateView()
            }
            .navigationDestination(isPresented: $showConnect) {
                ConnectView()
            }
            #if targetEnvironment(simulator)
            // Design-screenshot convenience: HS_DEMO=1 opens straight to the live canvas; HS_DEMO_HOME seeds rows.
            .onAppear {
                if ProcessInfo.processInfo.environment["HS_DEMO_HOME"] == "1" { model.seedHomeDemo() }
                if ProcessInfo.processInfo.environment["HS_DEMO"] == "1" { capturing = true }
                if ProcessInfo.processInfo.environment["HS_DEMO_AGENTDESK"] == "1" { showAgentDesk = true }
                if ProcessInfo.processInfo.environment["HS_DEMO_DICTATE"] == "1" { showDictate = true }
                if ProcessInfo.processInfo.environment["HS_DEMO_CONNECT"] == "1" { showConnect = true }
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
            HStack(spacing: 10) {
                if !model.meetings.isEmpty {
                    Text("\(model.meetings.count)").font(.system(size: 20, weight: .heavy).monospacedDigit())
                        .foregroundStyle(Sig.text)
                        .frame(width: 46, height: 46).signalCard(Sig.s2, radius: 14)
                }
                NavigationLink { SettingsView() } label: {
                    Image(systemName: "gearshape.fill").font(.system(size: 18, weight: .bold))
                        .foregroundStyle(Sig.muted)
                        .frame(width: 46, height: 46).signalCard(Sig.s2, radius: 14)
                }
                .buttonStyle(PressableCard())
                .accessibilityLabel("Settings")
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

    // A full-width flagship tile under the hero — the Workbench, your own intelligence workflows.
    private var workbenchCta: some View {
        HStack(spacing: 14) {
            GlyphChip(system: "slider.horizontal.3", gradient: Sig.accentGradient, size: 50)
            VStack(alignment: .leading, spacing: 3) {
                Text("Workbench").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Build your own intelligence workflows").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading).signalCard(radius: 20)
    }

    // The Agent Desk — your live coding agents and the question each is asking.
    private var agentDeskCta: some View {
        HStack(spacing: 14) {
            GlyphChip(system: "cpu.fill", gradient: Sig.localGradient, size: 50)
            VStack(alignment: .leading, spacing: 3) {
                Text("Agent Desk").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Your live agents — answer the one that's waiting").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading).signalCard(radius: 20)
    }

    // The flagship mesh tile — talk on this iPad, the words land in whatever's focused on your Mac.
    // Peer-named when paired; invites pairing when not. Wears the ON-DEVICE / local-mesh badge.
    private var dictateCta: some View {
        let paired = peers.isPaired
        return HStack(spacing: 14) {
            GlyphChip(system: "mic.fill", gradient: Sig.accentGradient, size: 50)
            VStack(alignment: .leading, spacing: 5) {
                Text(paired ? "Dictate to \(peers.displayName)" : "Dictate to your Mac")
                    .font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                if paired {
                    HStack(spacing: 6) {
                        Image(systemName: "lock.fill").font(.system(size: 8, weight: .black))
                        Text("ON-DEVICE · LOCAL MESH").font(.system(size: 10, weight: .heavy)).tracking(0.9)
                    }
                    .foregroundStyle(Sig.local)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(Sig.local.opacity(0.12), in: Capsule())
                    .overlay(Capsule().strokeBorder(Sig.local.opacity(0.25), lineWidth: 1))
                } else {
                    Text("Tap to pair — your iPad is the best mic in the house")
                        .font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint).lineLimit(1)
                }
            }
            Spacer()
            Image(systemName: paired ? "chevron.right" : "link.badge.plus")
                .font(.system(size: 14, weight: .bold)).foregroundStyle(paired ? Sig.faint : Sig.accent)
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading).signalCard(radius: 20)
    }

    // The mesh connection home (HSM-15-10) — find your computer on the network and pair, no IP typing.
    // Names the paired Mac when connected; invites discovery when not. Wears the local-network badge.
    private var connectCta: some View {
        let paired = peers.isPaired
        return HStack(spacing: 14) {
            GlyphChip(system: "laptopcomputer", gradient: Sig.localGradient, size: 50)
            VStack(alignment: .leading, spacing: 5) {
                Text(paired ? peers.displayName : "Your Computer")
                    .font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                if paired {
                    HStack(spacing: 6) {
                        Image(systemName: "checkmark.seal.fill").font(.system(size: 9, weight: .black))
                        Text("PAIRED · ON YOUR NETWORK").font(.system(size: 10, weight: .heavy)).tracking(0.9)
                    }
                    .foregroundStyle(Sig.local)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(Sig.local.opacity(0.12), in: Capsule())
                    .overlay(Capsule().strokeBorder(Sig.local.opacity(0.25), lineWidth: 1))
                } else {
                    Text("Find and pair your desktop — no IP to type")
                        .font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint).lineLimit(1)
                }
            }
            Spacer()
            Image(systemName: paired ? "chevron.right" : "dot.radiowaves.left.and.right")
                .font(.system(size: 14, weight: .bold)).foregroundStyle(paired ? Sig.faint : Sig.local)
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading).signalCard(radius: 20)
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
        .overlay(alignment: .topLeading) {
            // Guaranteed escape from the capture lobby (the recorder has its own stop while recording).
            if !model.recording { BackChip(action: done).padding(.top, 10).padding(.leading, 16) }
        }
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
                Circle().stroke(Sig.bad.opacity(0.4 + 0.55 * Double(min(1, model.level))), lineWidth: 2 + CGFloat(min(1, model.level)) * 3)
                    .frame(width: 60, height: 60)
                    .scaleEffect(1 + CGFloat(min(1, model.level)) * 0.4)   // swells with your voice
                    .animation(.easeOut(duration: 0.07), value: model.level)
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
                               onSendToNotes: { model.sendToNotes(b.text) },
                               onTack: {
                                   withAnimation(.spring(response: 0.4, dampingFraction: 0.75)) {
                                       model.pin(b, at: CGPoint(x: tack.midX, y: tack.midY), in: size, boardTop: pinFloor)
                                   }
                                   tactile(.medium)
                               })
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

/// A live mic-health readout shown during recording so a broken capture is diagnosable on the
/// device at a glance: frames climbing ⇒ audio is flowing; peak > 0 ⇒ the mic hears sound; "text ✓"
/// ⇒ Whisper is producing. Temporary while the recording regression is chased.
private struct MicDiag: View {
    let frames: Int
    let peak: Float
    let level: Float
    let hasText: Bool
    private var healthy: Bool { frames > 0 && peak > 0.005 }
    var body: some View {
        HStack(spacing: 9) {
            Circle().fill(frames == 0 ? Sig.bad : (healthy ? Sig.ok : Sig.warn)).frame(width: 8, height: 8)
            Text("MIC").font(.system(size: 9, weight: .heavy)).tracking(1).foregroundStyle(Sig.faint)
            Text("\(frames / 16_000)s·\(frames)fr").font(.system(size: 11, weight: .semibold).monospacedDigit())
                .foregroundStyle(frames == 0 ? Sig.bad : Sig.text)
            Text("peak \(String(format: "%.3f", peak))").font(.system(size: 11, weight: .semibold).monospacedDigit())
                .foregroundStyle(peak > 0.005 ? Sig.text : Sig.warn)
            Text("lvl \(String(format: "%.2f", level))").font(.system(size: 11, weight: .semibold).monospacedDigit())
                .foregroundStyle(Sig.muted)
            Text(hasText ? "text ✓" : "text –").font(.system(size: 11, weight: .bold))
                .foregroundStyle(hasText ? Sig.ok : Sig.faint)
        }
        .padding(.horizontal, 14).padding(.vertical, 8)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().strokeBorder(Sig.topHairline, lineWidth: 1))
        .shadow(color: .black.opacity(0.4), radius: 8, y: 3)
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
        // Perceptual gain: a gamma < 1 expands the quiet end so normal speech drives full bars.
        let amp = active ? min(1, pow(max(0, level), 0.62)) : 0
        TimelineView(.animation) { ctx in
            let t = ctx.date.timeIntervalSinceReferenceDate
            HStack(alignment: .center, spacing: 3) {
                ForEach(0..<bars, id: \.self) { i in
                    // Each bar gets its own fast, irregular wobble — but the WHOLE envelope scales
                    // with amp, so silence is a calm flat line and your voice makes it leap.
                    let phase = t * 12 + Double(i) * 0.9
                    let wobble = 0.5 + 0.5 * sin(phase) * sin(phase * 0.41 + 1.3)
                    let centerBias = 1 - 0.55 * abs(Double(i) - Double(bars - 1) / 2) / (Double(bars) / 2)
                    let dyn = amp * CGFloat(wobble * centerBias)              // voice-driven
                    let idle = active ? 0.05 + 0.03 * CGFloat(0.5 + 0.5 * sin(phase)) : 0
                    let h = 3 + (dyn + idle) * height
                    Capsule()
                        .fill(LinearGradient(colors: [Sig.accent, Sig.accent.opacity(0.5)], startPoint: .bottom, endPoint: .top))
                        .frame(width: 3, height: max(3, h))
                        .shadow(color: Sig.accent.opacity(Double(min(0.8, dyn * 1.4))), radius: 3)  // glows on peaks
                        .opacity(active ? 1 : 0.35)
                }
            }
            .animation(.easeOut(duration: 0.06), value: amp)
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
    var onTack: () -> Void = {}             // one-thumb tack (HSM-20-03): tap-to-tack via the menu
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
            // One-thumb tack (HSM-20-03): a phone can't always drag a bubble to the tack zone, so the
            // menu offers a direct "mark this moment" — the same MIR-steering tack as a drop-on-target.
            Button { onTack() } label: { Label("Tack this moment", systemImage: "pin.fill") }
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

// MARK: - Meeting detail (reopen-intact)

struct MeetingDetailView: View {
    let meeting: Meeting
    @Environment(\.dismiss) private var dismiss
    @StateObject private var notes: NotebookModel
    @StateObject private var review: MeetingReviewState
    @ObservedObject private var workflows = WorkflowStore.shared
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
                    TranscriptView(segments: meeting.segments, meetingID: meeting.id).id(0)

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
        .topBack { dismiss() }
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
                GenerationTheater(note: review.note, lens: review.profile, types: review.genTypes,
                                  done: review.genDone, current: review.genCurrent)
                    .transition(.asymmetric(insertion: .scale(scale: 0.92).combined(with: .opacity),
                                            removal: .opacity))
            } else if review.genFlourish > 0 {
                flourishBanner(review.genFlourish)
                    .transition(.scale(scale: 0.9).combined(with: .opacity))
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
                if !workflows.saved.isEmpty {
                    Menu {
                        ForEach(workflows.saved) { w in
                            Button { Task { await review.generate(workflowTypes: w.producedTypes(default: [.decisions, .actionItems, .requirements])) } } label: {
                                Label(w.name, systemImage: "wand.and.stars")
                            }
                        }
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "slider.horizontal.3"); Text("Run a workflow")
                            Image(systemName: "chevron.up.chevron.down").font(.system(size: 11, weight: .bold)).opacity(0.6)
                        }
                        .font(.subheadline.weight(.semibold)).foregroundStyle(Sig.accent)
                        .frame(maxWidth: .infinity).padding(.vertical, 11)
                        .background(Sig.accent.opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Sig.accent.opacity(0.35), lineWidth: 1))
                    }
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
        .signalCard(radius: 18)
        .animation(.spring(response: 0.5, dampingFraction: 0.82), value: review.generating)
    }

    // The completion flourish: a brief, bright "N insights ready" banner after a run finishes.
    private func flourishBanner(_ n: Int) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "sparkles").font(.system(size: 16, weight: .bold))
            Text("\(n) insight\(n == 1 ? "" : "s") ready").font(.system(size: 15, weight: .heavy))
            Spacer()
            Image(systemName: "checkmark.circle.fill").font(.system(size: 17, weight: .bold))
        }
        .foregroundStyle(.black)
        .padding(.horizontal, 16).padding(.vertical, 13)
        .background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .shadow(color: Sig.accent.opacity(0.4), radius: 14, y: 6)
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
