import SwiftUI
import UniformTypeIdentifiers

// HSM-12-03 — the unified Companion shell. One native app that presents BOTH the iPad's
// own on-device runtime AND the desktop/homelab server it is pointed at, web-app-
// consistent (Meetings / Dictate / Companion) in the Signal language. The device is a
// first-class peer of the server, never reduced to a remote — an unreachable desktop is
// a calm "working on-device" state, never a blocked app. All logic lives in the
// Runtime-Core view-models (CompanionShell / CompanionMeetings / CompanionBoard); the
// views only present.

@main
struct CompanionShellApp: App {
    var body: some Scene {
        WindowGroup { ShellView().preferredColorScheme(.dark) }
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
    static let local = Color(hex: 0x5B8DEF)   // a calm blue for the device's own runtime
}

private extension Color {
    init(hex: UInt) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255, opacity: 1)
    }
}

// HSM-19-04 — the confidence ring: an artifact's synthesis confidence as a filled arc, banded
// (high green / medium amber / low red) so the machine's certainty reads at a glance. A high
// confidence lands heavy and almost fully lit; a low one sits hollow and danger-tinted.
private struct ConfidenceRing: View {
    let confidence: Double            // 0...1
    var size: CGFloat = 48
    private var band: Color {
        if confidence >= 0.75 { return Sig.ok }
        if confidence >= 0.5 { return Sig.warn }
        return Sig.bad
    }
    var body: some View {
        ZStack {
            Circle().stroke(Sig.s3, lineWidth: 4)
            Circle().trim(from: 0, to: max(0.02, min(1, confidence)))
                .stroke(band, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .shadow(color: band.opacity(confidence >= 0.75 ? 0.5 : 0), radius: 5)
            Text("\(Int((confidence * 100).rounded()))").font(.system(size: size * 0.3, weight: .heavy)).foregroundStyle(band)
        }
        .frame(width: size, height: size)
    }
}

// MARK: - Model

@MainActor
final class ShellModel: ObservableObject {
    @Published var host = ProcessInfo.processInfo.environment["HS_DESKTOP_HOST"] ?? ""
    @Published var portText = ProcessInfo.processInfo.environment["HS_DESKTOP_PORT"] ?? "8000"
    @Published var token = ProcessInfo.processInfo.environment["HS_DESKTOP_TOKEN"] ?? ""

    @Published var state: CompanionShellState?
    @Published var board = CompanionBoardState()
    @Published var loading = false
    @Published var busy = ""                 // a short "starting…/stopping…" note
    @Published var connectError = ""         // shown on the connect screen when host/port is invalid

    var canConnect: Bool { !host.trimmingCharacters(in: .whitespaces).isEmpty }
    var paired: Bool { state != nil }

    /// The iPad's own runtime — always present. On a real device these capabilities are
    /// live (Phases 2/3/5); local recordings would come from the on-device store.
    private let localSummary = LocalRuntimeSummary(
        ready: true,
        capabilities: ["On-device capture", "Whisper transcription", "Local inference (Mode A)"],
        meetings: [])

    private func client() -> HTTPDesktopClient? {
        guard let port = Int(portText.trimmingCharacters(in: .whitespaces)), port > 0 else { return nil }
        let peer = DesktopPeer(host: host, port: port, token: token.isEmpty ? nil : token, scheme: "http")
        guard let config = HTTPDesktopClient.Config(peer: peer) else { return nil }
        return HTTPDesktopClient(config: config)
    }

    func load() async {
        guard let c = client() else { connectError = "Enter a valid host and port."; return }
        connectError = ""
        loading = true; defer { loading = false }
        let summary = localSummary
        let shell = CompanionShell(link: CompanionLink(client: c),
                                   meetings: CompanionMeetings(client: c),
                                   localProvider: { summary })
        state = await shell.load()
        if case .success(let b) = await CompanionBoard(client: c).load() { board = b }
        if state?.mode == .connected {
            facets = try? await c.listFacets()
            await loadLearning()
        }
    }

    // MARK: Faceted archive (HSM-19-02) — narrow the desktop archive server-side. The chips
    // are the hub's distinct facet values (`/api/meetings/facets`); a selection or a search
    // re-lists via `/api/meetings?search=&speaker=&tag=` — never a client-side filter of a
    // stale page. Empty facets are a normal state (honest at N=0): no chip row renders.
    @Published var facets: MeetingFacets?
    @Published var searchQuery = ""
    @Published var selectedSpeaker: String?
    @Published var selectedTag: String?
    @Published var searchResults: [MeetingSummary]?
    @Published var searching = false

    var filtersActive: Bool {
        !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty
            || selectedSpeaker != nil || selectedTag != nil
    }

    func applyFilters() async {
        guard let c = client() else { return }
        guard filtersActive else { searchResults = nil; return }
        let q = searchQuery.trimmingCharacters(in: .whitespaces)
        searching = true; defer { searching = false }
        searchResults = try? await c.searchMeetings(
            query: q.isEmpty ? nil : q, speaker: selectedSpeaker, type: selectedTag)
    }

    func toggleSpeaker(_ s: String) async {
        selectedSpeaker = selectedSpeaker == s ? nil : s
        await applyFilters()
    }

    func toggleTag(_ t: String) async {
        selectedTag = selectedTag == t ? nil : t
        await applyFilters()
    }

    func clearFilters() {
        searchQuery = ""; selectedSpeaker = nil; selectedTag = nil; searchResults = nil
    }

    func startMeeting() async {
        guard let c = client() else { return }
        busy = "Starting meeting…"; defer { busy = "" }
        _ = await CompanionMeetings(client: c).start()
        await load()
    }

    func stopMeeting() async {
        guard let c = client() else { return }
        busy = "Stopping…"; defer { busy = "" }
        _ = await CompanionMeetings(client: c).stop()
        await load()
    }

    // MARK: Dictation teleprompter (HSM-18-01) — preview the rewrite + its destination
    // BEFORE a keystroke leaves the app, then send to the Mac. Voice input is the next layer;
    // the hero here is the receipt-before-the-action.
    @Published var dictateText = ""
    @Published var dictatePreview: DictationDryRun?
    @Published var dictating = false
    @Published var dictateError = ""
    @Published var dictateSent = false

    /// Run the typed utterance through the hub's dry-run so the user watches the rewrite resolve.
    func previewDictation() async {
        let utterance = dictateText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !utterance.isEmpty else { return }
        guard let c = client() else { dictateError = "Pair your desktop first."; return }
        dictating = true; dictateError = ""; dictateSent = false; defer { dictating = false }
        do {
            let result = try await c.dictationDryRun(utterance: utterance)
            // An empty receipt is a broken receipt: never preview (or let Send free-type) nothing.
            if result.finalText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                dictatePreview = nil; dictateError = "The pipeline returned nothing to type."
            } else {
                dictatePreview = result
            }
        } catch { dictatePreview = nil; dictateError = "Couldn't reach your desktop for a preview." }
    }

    /// Commit the previewed text: free-type the rewritten result into the focused desktop app.
    /// `raw: true` (HSM-18-01) — the receipt already went through the pipeline; the hub
    /// types it VERBATIM, so what previewed is exactly what lands.
    func sendDictation() async {
        guard let c = client(), let preview = dictatePreview else { return }
        dictating = true; dictateError = ""; defer { dictating = false }
        do {
            _ = try await c.sendRemoteDictation(text: preview.finalText, target: .focused, raw: true)
            dictateSent = true; dictatePreview = nil; dictateText = ""
        } catch { dictateError = "Send failed. Is a desktop app focused?" }
    }

    // MARK: Meeting import (HSM-19-03) — hand an on-device recording or transcript to the
    // hub's full intel pipeline. The hub answers 202 immediately (the meeting row appears
    // in a visible `importing` state) and runs Whisper/parse in the background.
    @Published var showImporter = false
    @Published var importBusy = false
    @Published var importNote = ""

    func importFile(url: URL) async {
        guard let c = client() else { return }
        importBusy = true; importNote = ""; defer { importBusy = false }
        // Files-app picks are security-scoped; the real filename must ride the part —
        // the hub validates by suffix and titles the meeting from the stem.
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        do {
            _ = try await c.importMeeting(
                fileURL: url, filename: url.lastPathComponent, mimeType: Self.mime(for: url))
            importNote = "Importing on your desktop"
            await load()   // the new row appears, wearing its importing state
        } catch HTTPDesktopClient.DesktopClientError.http(let code) {
            importNote = code == 400
                ? "The desktop refused the file (format or empty)."
                : "The desktop refused (\(code))."
        } catch { importNote = "Couldn't reach your desktop." }
    }

    static func mime(for url: URL) -> String {
        switch url.pathExtension.lowercased() {
        case "wav": return "audio/wav"
        case "mp3": return "audio/mpeg"
        case "m4a", "mp4": return "audio/mp4"
        case "flac": return "audio/flac"
        case "ogg": return "audio/ogg"
        case "vtt": return "text/vtt"
        case "srt": return "application/x-subrip"
        case "txt": return "text/plain"
        default: return "application/octet-stream"
        }
    }

    // MARK: Learning loop (HSM-19-06) — READ-ONLY: the hub's "what HoldSpeak learned"
    // digest + the dictation journal. No write affordances by shape (corrections CRUD and
    // on-device journaling are deliberately out — Phase 9 owns them).
    @Published var learningDigest: LearningDigest?
    @Published var journal: JournalResponse?
    @Published var learningWindow = "week"

    func loadLearning() async {
        guard let c = client() else { return }
        learningDigest = try? await c.learningDigest(window: learningWindow)
        journal = try? await c.journalEntries(limit: 12)
    }

    func setLearningWindow(_ window: String) async {
        guard learningWindow != window else { return }
        learningWindow = window
        guard let c = client() else { return }
        learningDigest = try? await c.learningDigest(window: window)
    }

    // MARK: Aftercare (HSM-19-01) — the close-the-loop digest for a meeting.
    @Published var aftercare: Aftercare?
    @Published var aftercareLoading = false

    func loadAftercare(meetingId: String) async {
        guard let c = client() else { return }
        aftercareLoading = true; defer { aftercareLoading = false }
        aftercare = try? await c.aftercare(meetingId: meetingId)
        filingItemId = nil; filedItemIds = []; fileIssueError = ""
    }

    // MARK: Aftercare file-issue (HSM-19-01) — an accepted open item becomes a GitHub-issue
    // actuator PROPOSAL (`proposed` state; the hub is idempotent per item). Approving it is a
    // separate act — the review queue (19-05), never this button.
    @Published var fileIssueRepo = ""            // "owner/name", remembered for the session
    @Published var filingItemId: String?         // the item whose inline repo row is open
    @Published var filingBusy = false
    @Published var filedItemIds: Set<String> = []
    @Published var fileIssueError = ""

    func fileIssue(itemId: String) async {
        guard let c = client(), let meetingId = aftercare?.meetingId else { return }
        let repo = fileIssueRepo.trimmingCharacters(in: .whitespaces)
        guard !repo.isEmpty else { return }
        filingBusy = true; fileIssueError = ""; defer { filingBusy = false }
        do {
            let result = try await c.fileAftercareIssue(
                meetingId: meetingId, actionItemId: itemId, repo: repo)
            if result.success {
                filedItemIds.insert(itemId); filingItemId = nil
            } else {
                fileIssueError = result.error ?? "The desktop refused the filing."
            }
        } catch HTTPDesktopClient.DesktopClientError.http(let code) {
            // The hub 400s on a missing repo or an item that isn't accepted; the button is
            // gated to accepted items, so name the repo shape as the likely miss.
            fileIssueError = code == 400
                ? "The desktop refused — repo must be owner/name and the item accepted."
                : "The desktop refused (\(code))."
        } catch { fileIssueError = "Couldn't reach your desktop." }
    }

    // MARK: Artifacts (HSM-19-04) — each meeting artifact wears its synthesis confidence.
    @Published var artifacts: [MeetingArtifact] = []

    func loadArtifacts(meetingId: String) async {
        guard let c = client() else { return }
        artifacts = (try? await c.meetingArtifacts(meetingId: meetingId)) ?? []
    }

    // MARK: Proposals review (HSM-19-05) — the queue of actuator proposals for this meeting,
    // wherever they were created (the web, live in-meeting, a 19-01 file-issue). Approve is
    // the separate human gate; a slack target executes immediately on approval (the hub's
    // consent model), which is why its control wears the cloud mark.
    @Published var proposals: [MeetingProposal] = []
    @Published var decidingIds: Set<String> = []
    @Published var proposalsError = ""

    func loadProposals(meetingId: String) async {
        guard let c = client() else { return }
        proposals = (try? await c.meetingProposals(meetingId: meetingId)) ?? []
        proposalsError = ""
    }

    func decideProposal(_ p: MeetingProposal, approved: Bool) async {
        guard let c = client() else { return }
        decidingIds.insert(p.id); proposalsError = ""; defer { decidingIds.remove(p.id) }
        do {
            let result = try await c.decideProposal(
                meetingId: p.meetingId, proposalId: p.id, approved: approved)
            if result.success, let updated = result.proposal {
                if let i = proposals.firstIndex(where: { $0.id == updated.id }) {
                    proposals[i] = updated
                }
            } else {
                proposalsError = result.error ?? "The desktop refused the decision."
            }
        } catch HTTPDesktopClient.DesktopClientError.http(let code) {
            proposalsError = "The desktop refused (\(code))."
        } catch { proposalsError = "Couldn't reach your desktop." }
    }
}

// MARK: - Shell

struct ShellView: View {
    @StateObject private var model = ShellModel()
    @State private var tab: Tab = ShellView.initialTab
    // HSM-20-04 — the compact (iPhone) signal: stack the Port/Token row vertically on the lane.
    @Environment(\.horizontalSizeClass) private var hSizeClass
    private var isLane: Bool { hSizeClass == .compact }

    enum Tab: String, CaseIterable { case meetings = "Meetings", dictate = "Dictate", companion = "Companion"
        var icon: String { switch self { case .meetings: "waveform"; case .dictate: "mic"; case .companion: "person.wave.2" } }
    }

    /// The tab to open on launch — `HS_SHELL_TAB` lets a screenshot run land on a given
    /// tab without a tap (default Meetings).
    static var initialTab: Tab {
        Tab(rawValue: (ProcessInfo.processInfo.environment["HS_SHELL_TAB"] ?? "").capitalized) ?? .meetings
    }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            if !model.paired && !model.canConnect {
                connectScreen
            } else {
                VStack(spacing: 0) {
                    topBar
                    ScrollView {
                        VStack(alignment: .leading, spacing: 18) {
                            switch tab {
                            case .meetings: meetingsScreen
                            case .dictate: dictateScreen
                            case .companion: companionScreen
                            }
                        }
                        .padding(20).frame(maxWidth: 720).frame(maxWidth: .infinity)
                    }
                    tabBar
                }
            }
        }
        .tint(Sig.accent)
        .task {
            if model.canConnect {
                await model.load()
                // HS_SHELL_OPEN_MEETING lets a screenshot run land on a meeting's digest
                // without a tap (the HS_SHELL_TAB pattern).
                if let mid = ProcessInfo.processInfo.environment["HS_SHELL_OPEN_MEETING"] {
                    await model.loadAftercare(meetingId: mid)
                    await model.loadArtifacts(meetingId: mid)
                    await model.loadProposals(meetingId: mid)
                }
                // HS_SHELL_FACET_SPEAKER/_TAG land a screenshot run on a narrowed archive
                // (a REAL server-side search, not a seed — the HS_SHELL_TAB pattern).
                if let s = ProcessInfo.processInfo.environment["HS_SHELL_FACET_SPEAKER"] {
                    await model.toggleSpeaker(s)
                }
                if let t = ProcessInfo.processInfo.environment["HS_SHELL_FACET_TAG"] {
                    await model.toggleTag(t)
                }
                // HS_SHELL_IMPORT_FILE uploads a file on launch through the SAME
                // importFile path the picker calls — a real end-to-end proof without a
                // headless tap on the Files sheet.
                if let path = ProcessInfo.processInfo.environment["HS_SHELL_IMPORT_FILE"] {
                    await model.importFile(url: URL(fileURLWithPath: path))
                }
            }
        }
        .onAppear {
            #if targetEnvironment(simulator)
            // HS_SHELL_DEMO=teleprompter seeds a resolved dry-run so the Dictate screen's preview
            // hero renders without a live hub (a layout proof, not a device proof).
            if ProcessInfo.processInfo.environment["HS_SHELL_DEMO"] == "teleprompter" {
                model.host = model.host.isEmpty ? "192.168.1.13" : model.host
                model.dictateText = "use redis with a twenty four hour TTL period"
                model.dictatePreview = DictationDryRun(
                    finalText: "Use Redis with a 24 hour TTL.",
                    target: DryRunTarget(label: "Cursor", confidence: 0.91),
                    warnings: [], totalElapsedMs: 380, blocksCount: 2,
                    project: DictationProject(name: "holdspeak"))
            }
            // HS_SHELL_DEMO=aftercare seeds a close-the-loop digest on the Meetings screen;
            // =aftercare-filing additionally opens the HSM-19-01 file-issue row on the
            // accepted item (a layout proof for the inline repo field).
            let demo = ProcessInfo.processInfo.environment["HS_SHELL_DEMO"]
            if demo == "aftercare" || demo == "aftercare-filing" {
                model.host = model.host.isEmpty ? "192.168.1.13" : model.host
                model.aftercare = Aftercare(
                    meetingId: "m1", meetingTitle: "Q3 kickoff", meetingDate: "2026-06-27",
                    openItems: AftercareOpenItems(total: 3, byOwner: [
                        AftercareOwnerGroup(owner: "Karol", count: 2, items: [
                            AftercareOpenItem(id: "a1", task: "Own the mesh-sync approval contract", owner: "Karol", due: "Fri",
                                              reviewState: "accepted"),
                            AftercareOpenItem(id: "a2", task: "Demo the air-gapped proof", owner: "Karol"),
                        ]),
                        AftercareOwnerGroup(owner: nil, count: 1, items: [
                            AftercareOpenItem(id: "a3", task: "Decide the iPhone size-class cutoff", owner: nil),
                        ]),
                    ]),
                    decisions: [
                        AftercareDecision(decision: "Ship the desk to the web this quarter."),
                        AftercareDecision(decision: "Whisper language is one knob across dictation, meetings, and import."),
                    ],
                    sinceLastMeeting: AftercareSinceLastMeeting(
                        previousMeeting: AftercarePreviousMeeting(id: "m0", title: "Planning", date: "2026-06-20"),
                        newDecisions: [AftercareDecision(decision: "Ship the desk to the web this quarter.")],
                        newActions: [AftercareOpenItem(id: "a3", task: "Decide the iPhone size-class cutoff")],
                        closedActions: [AftercareClosedAction(id: "c1", task: "Pick the on-device model", status: "done")],
                        changed: true),
                    isEmpty: false, slackConfigured: true)
                if demo == "aftercare-filing" {
                    model.filingItemId = "a1"
                    model.fileIssueRepo = "karolswdev/HoldSpeak"
                }
            }
            // HS_SHELL_DEMO=proposals seeds the review queue in all four states (HSM-19-05).
            if demo == "proposals" {
                model.host = model.host.isEmpty ? "192.168.1.13" : model.host
                model.proposals = [
                    MeetingProposal(id: "pr1", meetingId: "m1", status: .proposed,
                        target: "github", action: "create_issue",
                        preview: "Create issue in karolswdev/HoldSpeak: \"Wire the file-issue action\" (owner: Karol)",
                        reversible: false),
                    MeetingProposal(id: "pr2", meetingId: "m1", status: .proposed,
                        target: "slack", action: "send_message",
                        preview: "Post the aftercare digest for \"Q3 kickoff\" to #team-holdspeak",
                        reversible: false),
                    MeetingProposal(id: "pr3", meetingId: "m1", status: .executed,
                        target: "slack", action: "send_message",
                        preview: "Post the follow-up draft to #team-holdspeak",
                        reversible: false),
                    MeetingProposal(id: "pr4", meetingId: "m1", status: .failed,
                        target: "webhook", action: "post",
                        preview: "POST the decisions digest to the team webhook",
                        reversible: false, error: "Connector not configured on the desktop"),
                ]
            }
            // HS_SHELL_DEMO=artifacts seeds artifacts of varied confidence to show the ring banding.
            if ProcessInfo.processInfo.environment["HS_SHELL_DEMO"] == "artifacts" {
                model.host = model.host.isEmpty ? "192.168.1.13" : model.host
                model.artifacts = [
                    MeetingArtifact(id: "ar1", meetingId: "m1", artifactType: "decisions",
                        title: "Ship the desk to the web this quarter.", bodyMarkdown: "",
                        confidence: 0.92, status: "accepted",
                        sources: [MeetingArtifactSource(sourceType: "transcript", sourceRef: "seg-14"),
                                  MeetingArtifactSource(sourceType: "decision", sourceRef: "d-2")]),
                    MeetingArtifact(id: "ar2", meetingId: "m1", artifactType: "action_items",
                        title: "Karol owns the mesh-sync approval contract.", bodyMarkdown: "",
                        confidence: 0.71, status: "needs_review",
                        sources: [MeetingArtifactSource(sourceType: "transcript", sourceRef: "seg-31")]),
                    MeetingArtifact(id: "ar3", meetingId: "m1", artifactType: "risk_register",
                        title: "No owner for the air-gapped proof timeline.", bodyMarkdown: "",
                        confidence: 0.41, status: "needs_review",
                        sources: [MeetingArtifactSource(sourceType: "transcript", sourceRef: "seg-48")]),
                ]
            }
            #endif
        }
    }

    // MARK: top bar — identity + connection chip

    private var topBar: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text("HOLDSPEAK").font(.caption2.weight(.bold)).tracking(2).foregroundStyle(Sig.accent)
                Text("Companion").font(.title2.bold()).foregroundStyle(Sig.text)
            }
            Spacer()
            connectionChip
        }
        .padding(.horizontal, 20).padding(.top, 16).padding(.bottom, 12)
        .background(Sig.bg)
        .overlay(Rectangle().fill(Sig.line).frame(height: 1), alignment: .bottom)
    }

    private var connectionChip: some View {
        let connected = model.state?.mode == .connected
        return HStack(spacing: 7) {
            Circle().fill(connected ? Sig.ok : Sig.warn).frame(width: 8, height: 8)
            Text(connected ? "Desktop · \(model.host)" : "On-device")
                .font(.caption.weight(.medium)).foregroundStyle(Sig.muted)
            if model.loading { ProgressView().scaleEffect(0.6).tint(Sig.accent) }
        }
        .padding(.horizontal, 11).padding(.vertical, 7)
        .background(Sig.s2, in: Capsule()).overlay(Capsule().stroke(Sig.line, lineWidth: 1))
    }

    // MARK: Meetings — the device's own runtime AND the server, side by side

    private var meetingsScreen: some View {
        VStack(alignment: .leading, spacing: 18) {
            thisIPadCard
            desktopCard
            if !model.artifacts.isEmpty { artifactsCard(model.artifacts) }
            if !model.proposals.isEmpty { proposalsCard(model.proposals) }
            if let a = model.aftercare, !a.isEmpty { aftercareCard(a) }
        }
    }

    // MARK: Proposals card (HSM-19-05) — the review queue: every actuator proposal for the
    // meeting, wherever it was created. Approve/Reject only on `proposed`; decided ones
    // render their state (and error) honestly. A slack approve executes immediately, so it
    // wears the cloud mark.
    private func proposalsCard(_ props: [MeetingProposal]) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("PROPOSALS", "You approve every send", Sig.accent,
                       live: props.contains { $0.status == .proposed })
            ForEach(props, id: \.id) { p in
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) {
                        Image(systemName: p.target == "slack" ? "paperplane.fill" : "arrow.up.right.square")
                            .font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.accent)
                        Text("\(p.target) · \(p.action.replacingOccurrences(of: "_", with: " "))")
                            .font(.caption.weight(.semibold)).foregroundStyle(Sig.text)
                        Spacer(minLength: 6)
                        if p.target == "slack" { egressChip(.cloud("slack")) }
                        statusPill(p.status.rawValue)
                    }
                    Text(p.preview).font(.callout).foregroundStyle(Sig.muted)
                        .lineLimit(4).fixedSize(horizontal: false, vertical: true)
                    if let err = p.error, !err.isEmpty {
                        Text(err).font(.caption2).foregroundStyle(Sig.bad)
                    }
                    if p.status == .proposed {
                        HStack(spacing: 10) {
                            Button { Task { await model.decideProposal(p, approved: true) } } label: {
                                HStack(spacing: 5) {
                                    if model.decidingIds.contains(p.id) { ProgressView().controlSize(.mini).tint(.black) }
                                    else { Image(systemName: "checkmark").font(.system(size: 11, weight: .bold)) }
                                    Text("Approve").font(.caption.weight(.bold))
                                }
                                .foregroundStyle(.black)
                                .padding(.horizontal, 14).padding(.vertical, 8)
                                .background(Sig.ok, in: Capsule())
                            }.buttonStyle(.plain)
                            Button { Task { await model.decideProposal(p, approved: false) } } label: {
                                Text("Reject").font(.caption.weight(.bold)).foregroundStyle(Sig.muted)
                                    .padding(.horizontal, 14).padding(.vertical, 8)
                                    .background(Sig.s3, in: Capsule())
                            }.buttonStyle(.plain)
                        }
                        .disabled(model.decidingIds.contains(p.id))
                    }
                }
                .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12)
                    .stroke(p.status == .proposed ? Sig.warn.opacity(0.4) : Sig.line, lineWidth: 1))
            }
            if !model.proposalsError.isEmpty {
                Text(model.proposalsError).font(.caption2).foregroundStyle(Sig.warn)
            }
        }
        .cardChrome(border: Sig.accent.opacity(0.3))
    }

    // The one egress chip (HSM-21-01): words + symbol + honest tint split come from the
    // Contracts EgressScope grammar — a mixed or cloud posture never dresses local.
    private func egressChip(_ scope: EgressScope) -> some View {
        let tint: Color = scope.leavesDevice ? Sig.warn : Sig.local
        return HStack(spacing: 4) {
            Image(systemName: scope.symbolName).font(.system(size: 8, weight: .bold))
            Text(scope.label).font(.caption2.weight(.semibold))
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 7).padding(.vertical, 3)
        .background(tint.opacity(0.12), in: Capsule())
    }

    // MARK: The filter row (HSM-19-02) — search + the hub's facet chips. A lit chip is the
    // active filter; tapping it again clears it. Narrowing is server-side.
    @ViewBuilder private var filterRow: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.faint)
                TextField("Search transcripts", text: $model.searchQuery)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                    .font(.subheadline).foregroundStyle(Sig.text)
                    .onSubmit { Task { await model.applyFilters() } }
                if model.searching { ProgressView().controlSize(.mini).tint(Sig.accent) }
                if model.filtersActive {
                    Button { model.clearFilters() } label: {
                        Image(systemName: "xmark.circle.fill").font(.system(size: 14)).foregroundStyle(Sig.faint)
                    }.buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 11).padding(.vertical, 9)
            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Sig.line, lineWidth: 1))

            if let f = model.facets, !f.speakers.isEmpty || !f.tags.isEmpty {
                FlowLayout(spacing: 8) {
                    ForEach(f.speakers, id: \.self) { s in
                        facetChip(s, icon: "person.fill", selected: model.selectedSpeaker == s) {
                            Task { await model.toggleSpeaker(s) }
                        }
                    }
                    ForEach(f.tags, id: \.self) { t in
                        facetChip(t, icon: "tag.fill", selected: model.selectedTag == t) {
                            Task { await model.toggleTag(t) }
                        }
                    }
                }
            }
        }
    }

    private func facetChip(_ label: String, icon: String, selected: Bool,
                           action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 5) {
                Image(systemName: icon).font(.system(size: 9, weight: .bold))
                Text(label).font(.caption.weight(.medium))
            }
            .foregroundStyle(selected ? .black : Sig.accent)
            .padding(.horizontal, 10).padding(.vertical, 6)
            .background(selected ? Sig.accent : Sig.accent.opacity(0.12), in: Capsule())
            .overlay(Capsule().stroke(Sig.accent.opacity(selected ? 0 : 0.3), lineWidth: 1))
        }
        .buttonStyle(.plain)
    }

    // MARK: Artifacts card (HSM-19-04) — the confidence-ring moment: every artifact wears
    // its synthesis confidence as an arc, and points at where it was synthesized from.
    private func artifactsCard(_ arts: [MeetingArtifact]) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("ARTIFACTS", "Each one wears its confidence", Sig.accent, live: false)
            ForEach(arts, id: \.id) { art in
                HStack(alignment: .top, spacing: 12) {
                    ConfidenceRing(confidence: art.confidence ?? 0).opacity(art.confidence == nil ? 0.4 : 1)
                    VStack(alignment: .leading, spacing: 6) {
                        HStack(spacing: 6) {
                            Text(art.title).font(.subheadline.weight(.semibold)).foregroundStyle(Sig.text)
                                .fixedSize(horizontal: false, vertical: true)
                            Spacer(minLength: 6)
                            statusPill(art.status)
                        }
                        Text(art.artifactType.replacingOccurrences(of: "_", with: " "))
                            .font(.caption2.weight(.medium)).tracking(0.5).foregroundStyle(Sig.faint)
                        if !art.sources.isEmpty {
                            HStack(spacing: 5) {
                                Image(systemName: "link").font(.system(size: 9, weight: .bold)).foregroundStyle(Sig.faint)
                                Text("Synthesized from " + art.sources.map { $0.sourceType.replacingOccurrences(of: "_", with: " ") }.joined(separator: " · "))
                                    .font(.caption2).foregroundStyle(Sig.muted).lineLimit(1)
                            }
                        }
                    }
                }
                .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(art.status == "needs_review" ? Sig.warn.opacity(0.4) : Sig.line, lineWidth: 1))
            }
            rowNote("Accept a needs-review artifact to settle it.")
        }
        .cardChrome(border: Sig.accent.opacity(0.3))
    }

    private func statusPill(_ s: String) -> some View {
        let (label, tint): (String, Color) = {
            switch s {
            case "accepted", "approved", "executed": return (s, Sig.ok)
            case "needs_review": return ("needs review", Sig.warn)
            case "proposed": return ("proposed", Sig.warn)
            case "rejected", "failed": return (s, Sig.bad)
            default: return (s.replacingOccurrences(of: "_", with: " "), Sig.faint)
            }
        }()
        return Text(label).font(.caption2.weight(.semibold)).foregroundStyle(tint)
            .padding(.horizontal, 7).padding(.vertical, 3).background(tint.opacity(0.12), in: Capsule())
    }

    // MARK: Aftercare card (HSM-19-01) — close the loop: what's still open (by owner),
    // what was decided, and the real diff since the previous meeting.
    private func aftercareCard(_ a: Aftercare) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("AFTERCARE", a.meetingTitle ?? "Close the loop", Sig.accent, live: false)

            if let since = a.sinceLastMeeting, since.changed {
                HStack(spacing: 8) {
                    if !since.newDecisions.isEmpty { diffChip("\(since.newDecisions.count) decided", "checkmark.seal.fill", Sig.ok) }
                    if !since.newActions.isEmpty { diffChip("\(since.newActions.count) new", "plus.circle.fill", Sig.accent) }
                    if !since.closedActions.isEmpty { diffChip("\(since.closedActions.count) closed", "checkmark.circle.fill", Sig.faint) }
                    Spacer()
                }
            }

            if a.openItems.total > 0 {
                Text("STILL OPEN · \(a.openItems.total)").font(.caption2.weight(.bold)).tracking(1.2).foregroundStyle(Sig.faint)
                ForEach(Array(a.openItems.byOwner.enumerated()), id: \.offset) { _, group in
                    VStack(alignment: .leading, spacing: 7) {
                        HStack(spacing: 6) {
                            Image(systemName: "person.fill").font(.system(size: 10, weight: .bold)).foregroundStyle(Sig.muted)
                            Text(group.owner ?? "Unassigned").font(.caption.weight(.semibold)).foregroundStyle(Sig.text)
                            Text("\(group.count)").font(.caption2).foregroundStyle(Sig.faint)
                        }
                        ForEach(group.items, id: \.id) { item in
                            VStack(alignment: .leading, spacing: 8) {
                                HStack(alignment: .top, spacing: 8) {
                                    Circle().fill(Sig.faint).frame(width: 5, height: 5).padding(.top, 6)
                                    Text(item.task).font(.callout).foregroundStyle(Sig.muted).fixedSize(horizontal: false, vertical: true)
                                    Spacer(minLength: 0)
                                    if let due = item.due { Text(due).font(.caption2).foregroundStyle(Sig.warn) }
                                    // HSM-19-01 — only an accepted item can be filed (the hub 400s otherwise).
                                    if item.reviewState == "accepted" {
                                        if model.filedItemIds.contains(item.id) {
                                            statusPill("proposed")
                                        } else if model.filingItemId != item.id {
                                            Button {
                                                model.filingItemId = item.id; model.fileIssueError = ""
                                            } label: {
                                                HStack(spacing: 4) {
                                                    Image(systemName: "arrow.up.right.square").font(.system(size: 9, weight: .bold))
                                                    Text("File issue").font(.caption2.weight(.semibold))
                                                }
                                                .foregroundStyle(Sig.accent)
                                                .padding(.horizontal, 8).padding(.vertical, 4)
                                                .background(Sig.accent.opacity(0.12), in: Capsule())
                                            }.buttonStyle(.plain)
                                        }
                                    }
                                }
                                if model.filingItemId == item.id, !model.filedItemIds.contains(item.id) {
                                    fileIssueRow(itemId: item.id)
                                }
                            }
                        }
                    }
                    .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 11))
                    .overlay(RoundedRectangle(cornerRadius: 11).stroke(Sig.line, lineWidth: 1))
                }
            }

            if !a.decisions.isEmpty {
                Text("DECIDED · \(a.decisions.count)").font(.caption2.weight(.bold)).tracking(1.2).foregroundStyle(Sig.faint)
                ForEach(Array(a.decisions.enumerated()), id: \.offset) { _, d in
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "checkmark.seal.fill").font(.system(size: 12)).foregroundStyle(Sig.ok).padding(.top, 1)
                        Text(d.decision).font(.callout).foregroundStyle(Sig.text).fixedSize(horizontal: false, vertical: true)
                    }
                }
            }

        }
        .cardChrome(border: Sig.accent.opacity(0.3))
    }

    // HSM-19-01 — the inline repo row (no modal): type the target once, file, done. Filing
    // records a PROPOSAL on the desktop; the approve lives in the review queue.
    private func fileIssueRow(itemId: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                TextField("owner/name", text: $model.fileIssueRepo)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                    .font(.callout.monospaced()).foregroundStyle(Sig.text)
                    .padding(.horizontal, 10).padding(.vertical, 8)
                    .background(Sig.s3, in: RoundedRectangle(cornerRadius: 9))
                    .overlay(RoundedRectangle(cornerRadius: 9).stroke(Sig.line, lineWidth: 1))
                Button { Task { await model.fileIssue(itemId: itemId) } } label: {
                    HStack(spacing: 5) {
                        if model.filingBusy { ProgressView().controlSize(.mini).tint(.black) }
                        Text("File").font(.caption.weight(.bold)).foregroundStyle(.black)
                    }
                    .padding(.horizontal, 14).padding(.vertical, 9)
                    .background(Sig.accent, in: RoundedRectangle(cornerRadius: 9))
                }
                .buttonStyle(.plain)
                .disabled(model.filingBusy || model.fileIssueRepo.trimmingCharacters(in: .whitespaces).isEmpty)
                Button { model.filingItemId = nil; model.fileIssueError = "" } label: {
                    Image(systemName: "xmark").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint)
                        .padding(9).background(Sig.s3, in: Circle())
                }.buttonStyle(.plain).disabled(model.filingBusy)
            }
            if !model.fileIssueError.isEmpty {
                Text(model.fileIssueError).font(.caption2).foregroundStyle(Sig.warn)
            }
        }
        .padding(.leading, 13)
    }

    private func diffChip(_ text: String, _ icon: String, _ tint: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.system(size: 9, weight: .bold))
            Text(text).font(.caption2.weight(.semibold))
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 9).padding(.vertical, 5)
        .background(tint.opacity(0.12), in: Capsule())
    }

    private var thisIPadCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("THIS iPAD", "Your on-device runtime — stands on its own", Sig.local,
                       live: model.state?.local.ready ?? true)
            if let caps = model.state?.local.capabilities, !caps.isEmpty {
                FlowChips(caps, tint: Sig.local)
            }
            let local = model.state?.local.meetings ?? []
            if local.isEmpty {
                rowNote("No recordings yet.")
            } else {
                ForEach(local) { m in meetingRow(m, tint: Sig.local) }
            }
        }
        .cardChrome(border: Sig.local.opacity(0.35))
    }

    @ViewBuilder private var desktopCard: some View {
        let connected = model.state?.mode == .connected
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("DESKTOP", connected ? "The server you code against" : "Unreachable — working on-device",
                       connected ? Sig.ok : Sig.warn, live: connected)
            if connected {
                let meetings = model.searchResults ?? model.state?.serverMeetings ?? []
                filterRow
                if meetings.isEmpty {
                    rowNote(model.filtersActive ? "No meetings match." : "No meetings on the desktop yet.")
                } else {
                    Text("Tap a meeting for its digest")
                        .font(.caption2).foregroundStyle(Sig.faint)
                    ForEach(meetings) { m in
                        Button {
                            Task {
                                await model.loadAftercare(meetingId: m.id)
                                await model.loadArtifacts(meetingId: m.id)
                                await model.loadProposals(meetingId: m.id)
                            }
                        } label: { meetingRow(m, tint: Sig.accent) }
                        .buttonStyle(.plain)
                    }
                    if model.aftercareLoading {
                        HStack(spacing: 7) { ProgressView().controlSize(.mini).tint(Sig.accent); Text("Loading the close-the-loop digest…").font(.caption2).foregroundStyle(Sig.faint) }
                    }
                }
                HStack(spacing: 12) {
                    Button { Task { await model.startMeeting() } } label: {
                        label("Start meeting", "record.circle", filled: true)
                    }
                    Button { Task { await model.stopMeeting() } } label: {
                        label("Stop", "stop.circle", filled: false)
                    }
                    // HSM-19-03 — a recording or transcript on this iPad becomes a real
                    // meeting on the desktop (the full intel pipeline).
                    Button { model.showImporter = true } label: {
                        label("Import file", "square.and.arrow.down", filled: false)
                    }
                    .disabled(model.importBusy)
                    if !model.busy.isEmpty {
                        ProgressView().tint(Sig.accent); Text(model.busy).font(.caption).foregroundStyle(Sig.faint)
                    }
                }
                if model.importBusy {
                    HStack(spacing: 7) {
                        ProgressView().controlSize(.mini).tint(Sig.accent)
                        Text("Uploading…").font(.caption2).foregroundStyle(Sig.faint)
                    }
                }
                if !model.importNote.isEmpty {
                    Text(model.importNote).font(.caption)
                        .foregroundStyle(model.importNote.hasPrefix("Importing") ? Sig.ok : Sig.warn)
                }
            } else {
                rowNote("Desktop not reachable. Your iPad runtime stays live.")
                Button { Task { await model.load() } } label: { label("Retry", "arrow.clockwise", filled: false) }
            }
        }
        .cardChrome(border: connected ? Sig.line : Sig.warn.opacity(0.35))
        .fileImporter(isPresented: $model.showImporter,
                      allowedContentTypes: importTypes,
                      allowsMultipleSelection: false) { result in
            if case .success(let urls) = result, let url = urls.first {
                Task { await model.importFile(url: url) }
            }
        }
    }

    /// Audio plus the transcript formats the hub parses (.vtt/.srt/.txt).
    private var importTypes: [UTType] {
        var types: [UTType] = [.audio, .plainText]
        if let vtt = UTType(filenameExtension: "vtt") { types.append(vtt) }
        if let srt = UTType(filenameExtension: "srt") { types.append(srt) }
        return types
    }

    // MARK: Dictate — nav slot (on-device)

    private var dictateScreen: some View {
        VStack(alignment: .leading, spacing: 18) {
            teleprompterCard
            learningCard
        }
    }

    private var teleprompterCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("DICTATE", "Watch the rewrite resolve, then send to your desktop", Sig.local, live: true)

                VStack(alignment: .leading, spacing: 8) {
                    Text("WHAT YOU'D SAY").font(.caption2.weight(.bold)).tracking(1.4).foregroundStyle(Sig.faint)
                    TextField("Type or paste an utterance…", text: $model.dictateText, axis: .vertical)
                        .lineLimit(2...5).font(.body).foregroundStyle(Sig.text)
                        .padding(12).background(Sig.s2, in: RoundedRectangle(cornerRadius: 11))
                        .overlay(RoundedRectangle(cornerRadius: 11).stroke(Sig.line, lineWidth: 1))
                    Button { Task { await model.previewDictation() } } label: {
                        HStack(spacing: 7) {
                            if model.dictating && model.dictatePreview == nil { ProgressView().controlSize(.mini).tint(.black) }
                            else { Image(systemName: "wand.and.stars") }
                            Text(model.dictating && model.dictatePreview == nil ? "Resolving…" : "Preview the rewrite")
                        }
                        .font(.subheadline.weight(.semibold)).foregroundStyle(.black)
                        .frame(maxWidth: .infinity).padding(.vertical, 11)
                        .background(Sig.local, in: RoundedRectangle(cornerRadius: 11))
                    }
                    .disabled(model.dictateText.trimmingCharacters(in: .whitespaces).isEmpty || model.dictating)
                }

                if let preview = model.dictatePreview {
                    let destination = preview.target?.displayLabel
                    VStack(alignment: .leading, spacing: 11) {
                        HStack(spacing: 7) {
                            Image(systemName: "arrow.right.circle.fill").foregroundStyle(Sig.local)
                            Text(destination.map { "Types into \($0)" } ?? "Types into the focused desktop app")
                                .font(.caption.weight(.semibold)).foregroundStyle(Sig.muted)
                            Spacer()
                            // HSM-21-01: a mixed posture, honestly amber (this chip used to
                            // render "Local + host" in the local treatment).
                            egressChip(.mixed(model.host.isEmpty ? "your desktop" : model.host))
                        }
                        Text(preview.finalText).font(.title3.weight(.semibold)).foregroundStyle(Sig.text)
                            .textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
                        HStack(spacing: 8) {
                            if let ms = preview.totalElapsedMs { metaChip("\(Int(ms)) ms", "bolt.fill", Sig.faint) }
                            if let b = preview.blocksCount, b > 0 { metaChip("\(b) block\(b == 1 ? "" : "s")", "square.stack.3d.up.fill", Sig.faint) }
                            if let w = preview.warnings, !w.isEmpty { metaChip("\(w.count) warning\(w.count == 1 ? "" : "s")", "exclamationmark.triangle.fill", Sig.warn) }
                        }
                        HStack(spacing: 10) {
                            Button { model.dictatePreview = nil } label: {
                                Text("Edit").font(.subheadline.weight(.semibold)).foregroundStyle(Sig.muted)
                                    .frame(maxWidth: .infinity).padding(.vertical, 11)
                                    .background(Sig.s2, in: RoundedRectangle(cornerRadius: 11))
                            }
                            Button { Task { await model.sendDictation() } } label: {
                                HStack(spacing: 7) {
                                    if model.dictating { ProgressView().controlSize(.mini).tint(.black) }
                                    else { Image(systemName: "paperplane.fill") }
                                    Text("Send to your desktop")
                                }
                                .font(.subheadline.weight(.semibold)).foregroundStyle(.black)
                                .frame(maxWidth: .infinity).padding(.vertical, 11)
                                .background(Sig.local, in: RoundedRectangle(cornerRadius: 11))
                            }.disabled(model.dictating)
                        }
                    }
                    .padding(13).background(Sig.s1, in: RoundedRectangle(cornerRadius: 13))
                    .overlay(RoundedRectangle(cornerRadius: 13).stroke(Sig.local.opacity(0.45), lineWidth: 1))
                }

                if model.dictateSent {
                    HStack(spacing: 7) {
                        Image(systemName: "checkmark.circle.fill").foregroundStyle(Sig.ok)
                        Text("Sent to your desktop").font(.caption.weight(.semibold)).foregroundStyle(Sig.ok)
                    }
                }
                if !model.dictateError.isEmpty {
                    Text(model.dictateError).font(.caption).foregroundStyle(Sig.warn)
                }
            }
            .cardChrome(border: Sig.local.opacity(0.35))
    }

    // MARK: Learning card (HSM-19-06) — dictation's afterlife, read-only: the digest's
    // headline numbers with the week/all window, then the recent journal. Honest at N=0.
    @ViewBuilder private var learningCard: some View {
        if let digest = model.learningDigest {
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 9) {
                    peerHeader("LEARNED", digest.enabled ? "Corrections route into new dictations" : "Corrections are off on the desktop",
                               Sig.accent, live: digest.enabled)
                    HStack(spacing: 0) {
                        windowButton("Week", value: "week")
                        windowButton("All", value: "all")
                    }
                    .background(Sig.s2, in: Capsule())
                    .overlay(Capsule().stroke(Sig.line, lineWidth: 1))
                }
                HStack(spacing: 8) {
                    metaChip("\(digest.totals.correctionsMade) correction\(digest.totals.correctionsMade == 1 ? "" : "s")", "slider.horizontal.3", Sig.accent)
                    metaChip("\(digest.totals.dictationsCorrected) corrected", "arrow.uturn.backward", Sig.faint)
                    if digest.enabled && digest.totals.similarNudged > 0 {
                        metaChip("\(digest.totals.similarNudged) similar nudged", "sparkles", Sig.ok)
                    }
                    metaChip("\(digest.totals.journalCount) journaled", "book.closed.fill", Sig.faint)
                }
                if !digest.corrections.isEmpty {
                    ForEach(digest.corrections.prefix(4)) { row in
                        HStack(spacing: 8) {
                            Image(systemName: row.kind == "target" ? "scope" : "arrow.triangle.branch")
                                .font(.system(size: 10, weight: .bold)).foregroundStyle(Sig.accent)
                            Text(row.gist).font(.caption).foregroundStyle(Sig.muted).lineLimit(1)
                            Image(systemName: "arrow.right").font(.system(size: 8, weight: .bold)).foregroundStyle(Sig.faint)
                            Text(row.value).font(.caption.weight(.semibold)).foregroundStyle(Sig.text).lineLimit(1)
                            Spacer(minLength: 6)
                            if row.similar > 0 {
                                Text("\(row.similar) similar").font(.caption2).foregroundStyle(Sig.ok)
                            }
                        }
                        .padding(.horizontal, 11).padding(.vertical, 8)
                        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Sig.line, lineWidth: 1))
                    }
                }
                if let journal = model.journal {
                    Text(journal.count > 0 ? "JOURNAL · \(journal.count)" : "JOURNAL")
                        .font(.caption2.weight(.bold)).tracking(1.2).foregroundStyle(Sig.faint)
                    if !journal.enabled {
                        rowNote("Journaling is off on the desktop.")
                    } else if journal.items.isEmpty {
                        rowNote("No dictations journaled yet.")
                    } else {
                        ForEach(journal.items.prefix(6)) { entry in
                            VStack(alignment: .leading, spacing: 4) {
                                Text(entry.finalText).font(.callout).foregroundStyle(Sig.text)
                                    .lineLimit(2).fixedSize(horizontal: false, vertical: true)
                                HStack(spacing: 8) {
                                    Text(entry.source == "dry_run" ? "dry run" : entry.source)
                                        .font(.caption2.weight(.medium)).foregroundStyle(Sig.faint)
                                    if let target = entry.targetProfile, !target.isEmpty {
                                        Text(target).font(.caption2).foregroundStyle(Sig.muted)
                                    }
                                    if entry.corrected {
                                        Text("corrected").font(.caption2.weight(.semibold)).foregroundStyle(Sig.accent)
                                    }
                                    if let learning = entry.learning, learning.matched, learning.similar > 0 {
                                        Text("learned from \(learning.similar) similar")
                                            .font(.caption2.weight(.semibold)).foregroundStyle(Sig.ok)
                                    }
                                    Spacer(minLength: 0)
                                    if let ms = entry.totalMs { Text("\(Int(ms)) ms").font(.caption2).foregroundStyle(Sig.faint) }
                                }
                            }
                            .padding(.horizontal, 11).padding(.vertical, 8)
                            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
                            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Sig.line, lineWidth: 1))
                        }
                    }
                }
            }
            .cardChrome(border: Sig.accent.opacity(0.3))
        }
    }

    private func windowButton(_ label: String, value: String) -> some View {
        Button { Task { await model.setLearningWindow(value) } } label: {
            Text(label).font(.caption2.weight(.bold))
                .foregroundStyle(model.learningWindow == value ? .black : Sig.muted)
                .padding(.horizontal, 11).padding(.vertical, 6)
                .background(model.learningWindow == value ? Sig.accent : .clear, in: Capsule())
        }
        .buttonStyle(.plain)
    }


    private func metaChip(_ text: String, _ icon: String, _ tint: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.system(size: 9, weight: .bold))
            Text(text).font(.caption2.weight(.medium))
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 8).padding(.vertical, 5)
        .background(Sig.s2, in: Capsule())
    }

    // MARK: Companion — nav slot (Phase 13 lives here)

    private var companionScreen: some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("ANSWER THE CODER", "The agent's question, on your iPad", Sig.accent,
                       live: model.board.awaiting)
            if model.board.targets.isEmpty {
                rowNote("No coder is waiting.")
            } else {
                ForEach(model.board.targets) { t in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack(spacing: 8) {
                            Image(systemName: t.selected ? "largecircle.fill.circle" : "circle")
                                .foregroundStyle(t.selected ? Sig.accent : Sig.faint)
                            Text(t.project ?? t.agent).font(.subheadline.weight(.semibold)).foregroundStyle(Sig.text)
                            if t.pinned { Image(systemName: "pin.fill").font(.caption2).foregroundStyle(Sig.accent) }
                            Spacer()
                            Text(t.confidence ?? "").font(.caption2).foregroundStyle(Sig.faint)
                        }
                        if let q = t.question, !q.isEmpty {
                            Text(q).font(.callout).foregroundStyle(Sig.muted).lineLimit(2)
                        }
                    }
                    .padding(12).background(Sig.s2, in: RoundedRectangle(cornerRadius: 11))
                    .overlay(RoundedRectangle(cornerRadius: 11).stroke(Sig.line, lineWidth: 1))
                }
            }
        }
        .cardChrome(border: Sig.line)
    }

    // MARK: custom Signal tab bar

    private var tabBar: some View {
        HStack(spacing: 0) {
            ForEach(Tab.allCases, id: \.self) { t in
                Button { tab = t } label: {
                    VStack(spacing: 4) {
                        Image(systemName: t.icon).font(.system(size: 18, weight: .semibold))
                        Text(t.rawValue).font(.caption2.weight(.medium))
                    }
                    .foregroundStyle(tab == t ? Sig.accent : Sig.faint)
                    .frame(maxWidth: .infinity).padding(.vertical, 10)
                }
            }
        }
        .padding(.horizontal, 12).padding(.bottom, 6).padding(.top, 4)
        .background(Sig.s1).overlay(Rectangle().fill(Sig.line).frame(height: 1), alignment: .top)
    }

    // MARK: connect onboarding

    private var connectScreen: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("COMPANION").font(.caption.weight(.bold)).tracking(2).foregroundStyle(Sig.accent)
                    Text("Point your iPad at your desktop").font(.largeTitle.bold()).foregroundStyle(Sig.text)
                }
                VStack(alignment: .leading, spacing: 14) {
                    field("Host", text: $model.host, placeholder: "192.168.1.x", keyboard: .URL)
                    // On the lane the two-up Port/Token row is cramped, so it stacks; on iPad it stays
                    // two-up (Port fixed, Token flexible). One layout, chosen by the size class.
                    if isLane {
                        field("Port", text: $model.portText, placeholder: "8000", keyboard: .numberPad)
                        field("Token", text: $model.token, placeholder: "Bearer token", secure: true)
                    } else {
                        HStack(spacing: 12) {
                            field("Port", text: $model.portText, placeholder: "8000", keyboard: .numberPad).frame(width: 130)
                            field("Token", text: $model.token, placeholder: "Bearer token", secure: true)
                        }
                    }
                    Button { Task { await model.load() } } label: {
                        Text("Connect").font(.headline).foregroundStyle(.black)
                            .frame(maxWidth: .infinity).padding(.vertical, 13)
                            .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
                    }
                    .disabled(!model.canConnect).opacity(model.canConnect ? 1 : 0.5)
                    if !model.connectError.isEmpty {
                        Text(model.connectError).font(.caption).foregroundStyle(Sig.warn)
                    }
                }
                .cardChrome(border: Sig.line)
            }
            .padding(20).frame(maxWidth: 560).frame(maxWidth: .infinity)
        }
    }

    // MARK: bits

    private func peerHeader(_ title: String, _ sub: String, _ tint: Color, live: Bool) -> some View {
        HStack(spacing: 9) {
            Circle().fill(live ? tint : Sig.faint).frame(width: 9, height: 9)
                .shadow(color: live ? tint.opacity(0.6) : .clear, radius: 5)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.caption.weight(.bold)).tracking(1.5).foregroundStyle(tint)
                Text(sub).font(.caption).foregroundStyle(Sig.faint)
            }
            Spacer()
        }
        // color-alone status is also stated in text for VoiceOver + non-color-perceivers.
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(title). \(live ? "active" : "idle"). \(sub)")
    }

    private func meetingRow(_ m: MeetingSummary, tint: Color) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "waveform").font(.caption).foregroundStyle(tint)
            Text(m.title ?? m.id).font(.subheadline).foregroundStyle(Sig.text).lineLimit(1)
            Spacer()
            // HSM-19-03 — an import in flight (or failed) wears its honest state.
            if m.intelStatus == "importing" {
                HStack(spacing: 4) {
                    ProgressView().controlSize(.mini).tint(Sig.warn)
                    Text("importing").font(.caption2.weight(.semibold)).foregroundStyle(Sig.warn)
                }
            } else if m.intelStatus == "import_failed" {
                Text("import failed").font(.caption2.weight(.semibold)).foregroundStyle(Sig.bad)
            }
            if let n = m.actionItemCount, n > 0 {
                Text("\(n) actions").font(.caption2).foregroundStyle(Sig.faint)
            }
        }
        .padding(.horizontal, 12).padding(.vertical, 10)
        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 10))
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Sig.line, lineWidth: 1))
    }

    private func rowNote(_ s: String) -> some View {
        Text(s).font(.caption).foregroundStyle(Sig.faint).frame(maxWidth: .infinity, alignment: .leading)
    }

    private func label(_ t: String, _ icon: String, filled: Bool) -> some View {
        HStack(spacing: 6) { Image(systemName: icon); Text(t).font(.subheadline.weight(.semibold)) }
            .foregroundStyle(filled ? .black : Sig.text)
            .padding(.horizontal, 14).padding(.vertical, 9)
            .background(filled ? Sig.accent : Sig.s3, in: RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(filled ? .clear : Sig.line, lineWidth: 1))
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
}

/// Wrapping capability chips — a simple flow layout so chips wrap on the iPad's canvas.
private struct FlowChips: View {
    let items: [String]
    let tint: Color
    init(_ items: [String], tint: Color) { self.items = items; self.tint = tint }
    var body: some View {
        FlowLayout(spacing: 8) {
            ForEach(items, id: \.self) { c in
                Text(c).font(.caption.weight(.medium)).foregroundStyle(tint)
                    .padding(.horizontal, 10).padding(.vertical, 6)
                    .background(tint.opacity(0.12), in: Capsule())
                    .overlay(Capsule().stroke(tint.opacity(0.3), lineWidth: 1))
            }
        }
    }
}

/// A minimal flow layout (chips wrap to the next line on overflow).
private struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? .infinity
        var x: CGFloat = 0, y: CGFloat = 0, rowHeight: CGFloat = 0
        for v in subviews {
            let s = v.sizeThatFits(.unspecified)
            if x + s.width > maxWidth { x = 0; y += rowHeight + spacing; rowHeight = 0 }
            x += s.width + spacing; rowHeight = max(rowHeight, s.height)
        }
        return CGSize(width: maxWidth == .infinity ? x : maxWidth, height: y + rowHeight)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX, y = bounds.minY, rowHeight: CGFloat = 0
        for v in subviews {
            let s = v.sizeThatFits(.unspecified)
            if x + s.width > bounds.maxX { x = bounds.minX; y += rowHeight + spacing; rowHeight = 0 }
            v.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(s))
            x += s.width + spacing; rowHeight = max(rowHeight, s.height)
        }
    }
}

private extension View {
    func cardChrome(border: Color) -> some View {
        self.padding(18).frame(maxWidth: .infinity, alignment: .leading)
            .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(border, lineWidth: 1))
    }
}
