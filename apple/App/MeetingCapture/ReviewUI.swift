import SwiftUI
import Foundation
import AVFoundation
import MarkdownUI
import UIKit
import Vision
import PencilKit

// HSM-14-19 "The Desk" decomposition: the on-device artifact generation + REVIEW surface (HSM-8-04) —
// MeetingReviewState (the generation theater + routing), the swipeable artifact cards + detail +
// voice-correction, the transcript view, segment replay, and the shared artifact/profile formatting
// helpers — lifted verbatim out of MeetingCaptureApp.swift. Same module.

// MARK: - On-device artifact generation + review (HSM-8-04)

@MainActor
final class MeetingReviewState: ObservableObject {
    let meeting: Meeting
    @Published var artifacts: [Artifact] = []
    @Published var profile: MIRProfile
    @Published var generating = false
    @Published var note = ""
    @Published var correctingId: String?     // HSM-14-07 — the card regenerating from a voice correction
    @Published var overrideProfileId: String = ""   // Phase 24 — run this generation on a chosen profile ("" = active)
    // HSM-14 generation theater — real per-type progress the UI animates as the model drafts each.
    @Published var genTypes: [ArtifactType] = []   // the lens's planned types for this run
    @Published var genDone: Set<ArtifactType> = [] // types the model has produced so far
    @Published var genCurrent: ArtifactType?       // the type in flight right now
    @Published var genFlourish: Int = 0            // >0 briefly after a run: "N insights ready"

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
    /// The on-device context CEILING — what we'd *like*. Raised to 32K for the
    /// 12GB tier (iPhone 17 Pro/Air, recent iPads) now that the increased-memory
    /// entitlement is live: ~2h of speech in one pass. HSM-8-08's budget still
    /// LOWERS this to what THIS device can actually afford (the KV-cache is RAM,
    /// clamped by `os_proc_available_memory()`), so a smaller device simply lands
    /// below 32K — the ceiling never gambles, and HSM-8-07 chunks the rest.
    private static let contextCeiling = 32_768

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

    func generate(workflowTypes: [ArtifactType]? = nil) async {
        Self.glogReset()
        let chars = meeting.segments.map(\.text).joined(separator: " ").count
        Self.glog("segments=\(meeting.segments.count) chars=\(chars) tokens≈\(chars / 4)")
        guard !meeting.segments.isEmpty else {
            note = "No transcript to analyze — this recording saved no text."; Self.glog("ABORT empty"); return
        }
        // Where intelligence runs is a user setting (Settings → Intelligence): on this iPad, or a
        // LAN endpoint. Refuse cleanly if the chosen target isn't ready.
        let cfg = InferenceConfigStore.shared
        let modelPath = Self.localGGUF()
        if cfg.isLocal && modelPath == nil {
            note = "No on-device model found. Push a .gguf to the app's Documents, or switch to a LAN endpoint in Settings."
            Self.glog("ABORT no model"); return
        }
        if !cfg.isLocal && cfg.endpointConfig == nil {
            note = "No endpoint configured. Set a LAN endpoint URL in Settings, or switch to on-device."
            Self.glog("ABORT no endpoint"); return
        }
        generating = true; defer { generating = false }

        // Regenerate cleanly: drop any PRIOR model artifacts so a re-run replaces rather
        // than piles up (ids are fresh UUIDs each run). The handwritten ink is preserved.
        for a in artifacts where a.pluginId == "holdspeak.mobile.intelligence" {
            try? storage?.deleteArtifact(id: a.id, at: Date())
        }
        load()

        // HSM-8-08 — on-device, size the context to THIS device (the KV-cache is RAM), never a
        // blind constant. An endpoint has its own memory, so use the ceiling there.
        let context: Int
        if cfg.isLocal, let mp = modelPath {
            let modelBytes = ((try? FileManager.default.attributesOfItem(atPath: mp))?[.size] as? Int) ?? 0
            let avail = Self.availableMemoryBytes()
            context = OnDeviceBudget.contextTokens(
                availableBytes: avail, modelBytes: modelBytes,
                marginBytes: 768 * 1_048_576, ceiling: Self.contextCeiling)
            Self.glog("local availMB=\(avail / 1_048_576) modelMB=\(modelBytes / 1_048_576) context=\(context)")
        } else {
            context = Self.contextCeiling
            Self.glog("endpoint mode host=\(cfg.endpointConfig?.baseURL.host ?? "?") context=\(context)")
        }
        let windowBudget = OnDeviceBudget.windowTokens(context: context)

        let transcript = Transcript(meetingId: meeting.id, segments: meeting.segments,
                                    transcriptHash: "ondevice-\(meeting.segments.count)")
        // A workflow run pins the types it produces; otherwise the lens (+ tacked moments) pick them.
        let types = workflowTypes ?? (marks.isEmpty
            ? (MIRRouter.baseEmphasis[profile] ?? [.decisions, .actionItems, .requirements])
            : InkEmphasis.routedTypes(profile: profile, transcript: transcript, marks: marks))
        Self.glog("types=\(types.map(\.rawValue)) workflow=\(workflowTypes != nil)")
        // Light up the generation theater with the planned types.
        genTypes = types; genDone = []; genCurrent = nil; genFlourish = 0

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
                withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) { genCurrent = type }
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
                    let provider = try cfg.makeProvider(profile: cfg.resolveProfile(override: overrideProfileId), localModelPath: modelPath, context: context)
                    let engine = ArtifactGenerationEngine(provider: provider, maxAttempts: 2)
                    let a = try await engine.generate(type, from: sub)
                    all.append(a)
                    // The type landed — light it up in the theater and stream the card in.
                    withAnimation(.spring(response: 0.45, dampingFraction: 0.7)) { _ = genDone.insert(type); genCurrent = nil }
                    tactile(.light)
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
        genCurrent = nil
        note = merged.isEmpty
            ? "The model produced nothing." + (lastError.isEmpty ? "" : " (\(lastError))")
            : ""
        // A satisfying finish: a heavier haptic + a transient "N insights ready" flourish.
        if !merged.isEmpty {
            tactile(.heavy)
            withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) { genFlourish = merged.count }
            Task { try? await Task.sleep(nanoseconds: 3_200_000_000)
                   await MainActor.run { withAnimation(.easeOut(duration: 0.4)) { genFlourish = 0 } } }
        }
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
            let provider = try LlamaProvider.make(modelPath: modelPath, maxTokenCount: Int32(context))
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
        let ggufs = ((try? FileManager.default.contentsOfDirectory(at: docs, includingPropertiesForKeys: nil)) ?? [])
            .filter { $0.pathExtension.lowercased() == "gguf" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        // Honour the model picked in Settings (persisted by InferenceConfigStore under this key);
        // fall back to the first installed model when nothing is selected.
        let selected = UserDefaults.standard.string(forKey: "hs.inf.localmodel") ?? ""
        if !selected.isEmpty, let m = ggufs.first(where: { $0.lastPathComponent == selected }) { return m.path }
        return ggufs.first?.path
    }
}

// HSM-14-19: internal (was private) so the extracted WorkbenchUI.swift shares it.
func artifactTypeLabel(_ t: ArtifactType) -> String {
    t.rawValue.replacingOccurrences(of: "_", with: " ").capitalized
}

/// Per-type accent (HSM-14 Tactile Sheets — each artifact type reads at a glance).
func artifactTint(_ t: ArtifactType) -> Color {
    switch t {
    case .decisions, .decisionAnnouncement: return Sig.ok
    case .actionItems, .milestonePlan: return Sig.accent
    case .riskRegister, .incidentTimeline, .runbookDelta: return Sig.warn
    case .requirements, .scopeReview, .dependencyMap: return Sig.local
    default: return Sig.local
    }
}
func artifactGlyph(_ t: ArtifactType) -> String {
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
func profileIcon(_ p: MIRProfile) -> String {
    switch p {
    case .balanced: return "circle.grid.cross.fill"
    case .architect: return "ruler.fill"
    case .delivery: return "shippingbox.fill"
    case .product: return "sparkles.rectangle.stack.fill"
    case .incident: return "exclamationmark.octagon.fill"
    }
}
func profileBlurb(_ p: MIRProfile) -> String {
    switch p {
    case .balanced: return "An even read of the room — decisions, action items, risks and requirements."
    case .architect: return "Leads with the design record — ADRs, decisions and the dependency map."
    case .delivery: return "Plans the work — milestones, action items and what could slip."
    case .product: return "Hears the customer — requirements, customer signals and scope."
    case .incident: return "Reconstructs what happened — timeline, runbook changes and risks."
    }
}
/// mm:ss for the recorder timer.
func clockString(_ s: Double) -> String {
    let t = Int(max(0, s)); return String(format: "%d:%02d", t / 60, t % 60)
}
/// A light tactile tap (HSM-14 — the app should feel hand-driven). Internal so the extracted
/// DesignSystem.swift (BackChip) shares it (HSM-14-19 decomposition).
func tactile(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
    UIImpactFeedbackGenerator(style: style).impactOccurred()
}

/// A clean one-glance teaser for a card: strip the common Markdown syntax so the preview
/// reads as plain prose (the full doc renders the real Markdown on tap).
func plainPreview(_ md: String) -> String {
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
func noteArtifactTitle(_ text: String) -> String {
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
                                Text("Fix it by voice").font(.system(size: 15.5, weight: .heavy))
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
    var canPlay: Bool = false           // diarization replay: this block has saved audio to play
    var playing: Bool = false           // this block is currently sounding
    var onPlay: () -> Void = {}
    @State private var appeared = false
    @State private var copied = false

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            RoundedRectangle(cornerRadius: 2).fill((playing ? Sig.accent : color).opacity(0.85)).frame(width: 3)
            VStack(alignment: .leading, spacing: 7) {
                if let speaker, !speaker.isEmpty {
                    HStack(spacing: 8) {
                        ZStack { Circle().fill(color.opacity(0.2))
                            Text(initials(speaker)).font(.system(size: 10, weight: .heavy)).foregroundStyle(color) }
                            .frame(width: 24, height: 24)
                        Text(speaker).font(.system(size: 13, weight: .heavy)).foregroundStyle(color)
                        if let time { Text(timeStr(time)).font(.system(size: 11, weight: .semibold).monospacedDigit()).foregroundStyle(Sig.faint) }
                        // Tap to HEAR this segment — the owner's tool to judge if the speaker label is right.
                        if canPlay {
                            Button { onPlay() } label: {
                                Image(systemName: playing ? "pause.circle.fill" : "play.circle.fill")
                                    .font(.system(size: 18)).foregroundStyle(playing ? Sig.accent : color)
                            }.buttonStyle(.plain)
                        }
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
        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
            .stroke(playing ? Sig.accent : Sig.line, lineWidth: playing ? 2 : 1))
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
    @StateObject private var player: SegmentAudioPlayer

    init(segments: [Segment], meetingID: String) {
        self.segments = segments
        _player = StateObject(wrappedValue: SegmentAudioPlayer(meetingID: meetingID))
    }

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
                    TranscriptBlock(speaker: b.speaker, time: b.time, text: b.text, color: b.color, index: i,
                                    canPlay: player.canPlay && b.time != nil,
                                    playing: player.playingIndex == i,
                                    onPlay: { if let s = b.time, let e = b.end { player.toggle(index: i, start: s, end: e) } })
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
    private var blocks: [(speaker: String?, time: Double?, end: Double?, text: String, color: Color)] {
        if segments.count > 1 {
            return segments.map { (speaker: $0.speaker.isEmpty ? "Speaker" : $0.speaker, time: $0.startTime, end: $0.endTime, text: $0.text, color: speakerColor($0.speaker)) }
        }
        guard let seg = segments.first else { return [] }
        return paragraphs(seg.text).map { (speaker: nil, time: nil, end: nil, text: $0, color: Sig.local) }
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

// MARK: - Generation theater (HSM-14 craft) — the on-device model, thinking, made visible

/// The post-meeting payoff, made beautiful: a living "thinking" orb (concentric accent rings + a
/// rotating conic shimmer + a breathing core) over a constellation of the lens's target types that
/// light up one-by-one as the on-device model drafts each. This replaces a 1pt spinner — the user
/// watches their meeting's intelligence assemble itself, on this iPad, with nothing leaving.
struct GenerationTheater: View {
    let note: String
    let lens: MIRProfile
    let types: [ArtifactType]
    let done: Set<ArtifactType>
    let current: ArtifactType?
    @State private var pulse = false
    @State private var spin = false
    @State private var orbSpin = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var headline: String {
        if let c = current { return "Drafting \(artifactTypeLabel(c))…" }
        return note.isEmpty ? "Reading the meeting on-device…" : note
    }

    var body: some View {
        VStack(spacing: 16) {
            orb
            VStack(spacing: 5) {
                Text(headline).font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                    .contentTransition(.opacity).id(headline)
                Text("Through the \(lens.rawValue.capitalized) lens")
                    .font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.accent)
            }
            if !types.isEmpty { constellation }
            HStack(spacing: 6) {
                Image(systemName: "lock.shield.fill").font(.system(size: 11, weight: .bold))
                Text("On-device").font(.system(size: 11, weight: .semibold))
            }
            .foregroundStyle(Sig.local)
            .padding(.horizontal, 11).padding(.vertical, 6)
            .background(Sig.local.opacity(0.10), in: Capsule())
        }
        .frame(maxWidth: .infinity).padding(.vertical, 26).padding(.horizontal, 12)
        .background(
            RadialGradient(colors: [Sig.accent.opacity(0.12), .clear], center: .top, startRadius: 8, endRadius: 220)
        )
        .onAppear { pulse = true; spin = true; orbSpin = true }
    }

    // A bespoke PixelLab plasma core — a swirling energy orb, slowly rotating + breathing — ringed
    // by outward accent pulses and a sweeping shimmer arc. The intelligence, literally alive.
    private var orb: some View {
        ZStack {
            ForEach(0..<3, id: \.self) { i in
                Circle().stroke(Sig.accent.opacity(0.45 - Double(i) * 0.12), lineWidth: 2)
                    .frame(width: 74 + CGFloat(i) * 28, height: 74 + CGFloat(i) * 28)
                    .scaleEffect(pulse ? 1.12 : 0.92)
                    .opacity(pulse ? 0.15 : 0.8)
                    .animation(reduceMotion ? nil : .easeInOut(duration: 1.7).repeatForever().delay(Double(i) * 0.22), value: pulse)
            }
            Circle().fill(Sig.accent.opacity(0.5)).frame(width: 66, height: 66).blur(radius: 24)   // bloom
            pixelAsset("theaterorb", size: 80, fallback: "sparkles", tint: .black)
                .rotationEffect(.degrees(orbSpin ? 360 : 0))
                .scaleEffect(pulse ? 1.05 : 0.96)
                .shadow(color: Sig.accent.opacity(0.7), radius: 16)
                .animation(reduceMotion ? nil : .linear(duration: 9).repeatForever(autoreverses: false), value: orbSpin)
                .animation(reduceMotion ? nil : .easeInOut(duration: 1.2).repeatForever(), value: pulse)
            Circle().trim(from: 0, to: 0.32)
                .stroke(AngularGradient(colors: [.clear, .white.opacity(0.9), .clear], center: .center),
                        style: StrokeStyle(lineWidth: 3, lineCap: .round))
                .frame(width: 96, height: 96)
                .rotationEffect(.degrees(spin ? 360 : 0))
                .animation(reduceMotion ? nil : .linear(duration: 1.2).repeatForever(autoreverses: false), value: spin)
        }
        .frame(height: 132)
    }

    // The lens's types — pending (dim) → in-flight (glowing, ringed) → done (filled + check).
    private var constellation: some View {
        HStack(spacing: 8) {
            ForEach(types, id: \.self) { t in
                let isDone = done.contains(t), isCur = current == t
                HStack(spacing: 5) {
                    Image(systemName: isDone ? "checkmark.circle.fill" : artifactGlyph(t))
                        .font(.system(size: 11, weight: .bold))
                    Text(artifactTypeLabel(t)).font(.system(size: 11, weight: .heavy))
                }
                .foregroundStyle(isDone ? .black : (isCur ? artifactTint(t) : Sig.faint))
                .padding(.horizontal, 10).padding(.vertical, 6)
                .background(isDone ? artifactTint(t) : (isCur ? artifactTint(t).opacity(0.16) : Sig.s2), in: Capsule())
                .overlay(Capsule().stroke(isCur ? artifactTint(t) : .clear, lineWidth: 1.5))
                .scaleEffect(isCur ? 1.07 : 1)
                .animation(.spring(response: 0.4, dampingFraction: 0.7), value: isDone)
                .animation(.spring(response: 0.4, dampingFraction: 0.7), value: isCur)
            }
        }
    }
}

// MARK: - Segment replay (judge the diarizer's speaker labels by ear)

/// Plays back a single transcript segment from a meeting's saved WAV so the owner can HEAR a segment
/// and judge whether its speaker label is right (the diarizer's whole point). It loads the meeting's
/// `…/meeting-audio/<id>.wav` once, seeks the player to the segment's `startTime`, plays, and stops
/// after `(endTime - startTime)`. If no WAV exists (older meetings, or capture never wrote one), it is
/// simply unavailable — `canPlay` is false and the play control is absent. Never crashes on a missing
/// file. `@MainActor` because it drives `@Published` UI state and an `AVAudioPlayer`.
@MainActor
final class SegmentAudioPlayer: ObservableObject {
    /// The segment index currently sounding (for the row highlight + ▶/⏸ toggle), or `nil` when idle.
    @Published private(set) var playingIndex: Int?

    private var player: AVAudioPlayer?
    private var stopWork: DispatchWorkItem?
    /// The category we found before we forced `.playback`, restored when playback ends — capture set
    /// `.record`, which makes a player produce no sound, so we must switch and put it back politely.
    private var priorCategory: AVAudioSession.Category?

    /// Whether this meeting actually has a replayable take on disk. The UI hides the play control when false.
    let canPlay: Bool
    private let audioURL: URL?

    init(meetingID: String) {
        let url = MeetingAudioStore.audioURL(for: meetingID)
        self.audioURL = url
        self.canPlay = url.map { FileManager.default.fileExists(atPath: $0.path) } ?? false
    }

    /// Toggle playback of one segment: tapping the one already sounding stops it; tapping another
    /// retargets. Seeks to `start`, plays, and self-stops after the segment's duration.
    func toggle(index: Int, start: Double, end: Double) {
        if playingIndex == index { stop(); return }
        guard canPlay, let url = audioURL else { return }

        // Recording left the session in `.record` (silent playback). Force a playback-capable category
        // for the duration of the replay, remembering the old one to restore.
        let session = AVAudioSession.sharedInstance()
        if priorCategory == nil { priorCategory = session.category }
        try? session.setCategory(.playback, mode: .default)
        try? session.setActive(true)

        if player == nil { player = try? AVAudioPlayer(contentsOf: url) }
        guard let p = player else { stop(); return }
        p.prepareToPlay()
        p.currentTime = max(0, min(start, p.duration))
        p.play()
        playingIndex = index

        let dur = max(0.05, end - start)
        let work = DispatchWorkItem { [weak self] in self?.stop() }
        stopWork?.cancel(); stopWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + dur, execute: work)
    }

    func stop() {
        stopWork?.cancel(); stopWork = nil
        player?.stop()
        playingIndex = nil
        // Restore whatever category was active before we forced `.playback` (best-effort).
        if let prior = priorCategory {
            try? AVAudioSession.sharedInstance().setCategory(prior)
            priorCategory = nil
        }
    }
}
