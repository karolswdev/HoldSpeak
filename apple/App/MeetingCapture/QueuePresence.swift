import SwiftUI
import Foundation

// HSM-14-19 "The Desk" decomposition: the run-queue + presence transparency layer (HSM-14-15) — the
// app-wide Job queue (RunQueueStore/QueueHUD, the Dynamic-Island-style pill -> ledger) and the
// presence-nudge overlay — lifted verbatim out of MeetingCaptureApp.swift. Same module.

// MARK: - The run queue — a first-class, app-wide transparency surface (HSM-14-15)
//
// Every workflow run is a Job with a visible state. The queue rides ABOVE every screen (home,
// meeting capture, the notebook) as a small pill under the status bar — tap to expand and see
// exactly what's queued, what's being asked, what's working, and what's blocked. 1000% transparency.

enum JobStatus: String {
    case queued, working, blocked, done, failed
    var label: String {
        switch self {
        case .queued: return "Queued"; case .working: return "Working"; case .blocked: return "Blocked"
        case .done: return "Done"; case .failed: return "Failed"
        }
    }
    var color: Color {
        switch self {
        case .queued: return Sig.faint; case .working: return Sig.accent; case .blocked: return Sig.warn
        case .done: return Sig.ok; case .failed: return Sig.bad
        }
    }
    var glyph: String {
        switch self {
        case .queued: return "hourglass"; case .working: return "bolt.fill"; case .blocked: return "pause.circle.fill"
        case .done: return "checkmark.circle.fill"; case .failed: return "xmark.octagon.fill"
        }
    }
}

/// One unit of work the queue tracks: a single node executing for a workflow run.
struct QueuedJob: Identifiable {
    let id: UUID
    var workflow: String        // which run it belongs to
    var step: String            // what's being asked (the node)
    var target: String          // where it runs — "On-device" / "Endpoint"
    var status: JobStatus
    var progress: Double = 0    // 0…1 while working
    var note: String?           // e.g. "endpoint down · retry 2/4"
    init(_ workflow: String, _ step: String, target: String, status: JobStatus, progress: Double = 0, note: String? = nil) {
        self.id = UUID(); self.workflow = workflow; self.step = step
        self.target = target; self.status = status; self.progress = progress; self.note = note
    }
}

/// One agent waiting on you, as the HUD shows it (HSM-15-09) — a first-class lane item
/// alongside jobs. The queue is "what the machine is doing"; this is "who's waiting on
/// you". Tapping the lane opens the desk; the nudge is the louder, dismissible surface.
struct WaitingAgent: Identifiable, Equatable {
    let id: String          // "agent/sessionID" — matches PresenceEvent.id
    var agent: String       // "claude" / "codex"
    var repo: String        // project, for the lane label
}

@MainActor final class RunQueueStore: ObservableObject {
    static let shared = RunQueueStore()
    @Published var jobs: [QueuedJob] = []
    /// Agents waiting on a reply — the proactive lane (HSM-15-09). App-wide, even mid-meeting.
    @Published var waitingAgents: [WaitingAgent] = []
    @Published var expanded = false

    // ── The mesh lane (HSM-15-03): the paired desktop's in-flight jobs + the
    // proposals awaiting YOUR nod, polled from `GET /api/mesh/inbox`. One queue,
    // every origin — the transparency + approval spine, on the glass in your hand.
    @Published var meshJobs: [MeshInboxJob] = []
    @Published var meshProposals: [MeshInboxProposal] = []
    @Published var deskProjections: [DeskProjectionDTO] = []
    @Published var projectionCounts: [String: Int] = [:]
    @Published var projectionTotal = 0
    @Published var projectionHasMore = false
    /// The peer can't be reached — a FIRST-CLASS state: the last-known rows stay,
    /// degraded to blocked (`auto-resumes`), never an error spinner.
    @Published var meshUnreachable = false
    var meshPeerName = "your Mac"
    private var meshPollTask: Task<Void, Never>?
    private var meshClient: HTTPDesktopClient?

    var working: Int { jobs.filter { $0.status == .working }.count }
    var meshWorking: Int { meshJobs.filter { $0.status == "running" }.count }
    var queued: Int { jobs.filter { $0.status == .queued }.count }
    var blocked: Int { jobs.filter { $0.status == .blocked }.count }
    var live: Int { working + queued + blocked }
    /// The HUD is visible whenever there's a job, an agent waiting, or mesh content.
    var hasContent: Bool {
        !jobs.isEmpty || !waitingAgents.isEmpty || !meshJobs.isEmpty ||
            !meshProposals.isEmpty || !deskProjections.isEmpty
    }
    /// Active jobs first (working → blocked → queued), then recently finished.
    var ordered: [QueuedJob] {
        let rank: [JobStatus: Int] = [.working: 0, .blocked: 1, .queued: 2, .done: 3, .failed: 4]
        return jobs.sorted { (rank[$0.status] ?? 9) < (rank[$1.status] ?? 9) }
    }

    /// Reconcile the waiting lane against the latest companion snapshot — the lane shows
    /// *currently* waiting agents (it isn't edge-triggered; the nudge is). Idempotent.
    func setWaiting(_ agents: [WaitingAgent]) {
        if waitingAgents != agents { waitingAgents = agents }
    }

    // MARK: mesh polling + decisions (HSM-15-03)

    /// Begin polling the paired desktop's inbox. Off in Simulator demos (which seed
    /// directly). A poll failure flips `meshUnreachable`, never throws to the UI.
    func startMeshPolling(_ client: HTTPDesktopClient, peerName: String,
                          every seconds: TimeInterval = 5) {
        meshClient = client
        meshPeerName = peerName
        meshPollTask?.cancel()
        meshPollTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.pollMesh()
                try? await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
            }
        }
    }
    func stopMeshPolling() { meshPollTask?.cancel(); meshPollTask = nil }

    private func pollMesh() async {
        guard let client = meshClient else { return }
        if let inbox = try? await client.meshInbox() {
            meshJobs = inbox.jobs ?? []
            meshProposals = inbox.proposals ?? []
            meshUnreachable = false
        } else {
            meshUnreachable = true
        }
        if let envelope = try? await client.deskProjections() {
            deskProjections = envelope.projections
            projectionCounts = envelope.counts
            projectionTotal = envelope.page.total
            projectionHasMore = envelope.page.hasMore
        }
    }

    func loadOlderProjections() async {
        guard let client = meshClient, projectionHasMore else { return }
        if let envelope = try? await client.deskProjections(offset: deskProjections.count) {
            deskProjections += envelope.projections
            projectionCounts = envelope.counts
            projectionTotal = envelope.page.total
            projectionHasMore = envelope.page.hasMore
        }
    }

    func setProjectionPresentation(_ projection: DeskProjectionDTO, action: String) async {
        guard let client = meshClient else { return }
        try? await client.updateProjectionPresentation(id: projection.id, action: action)
        await pollMesh()
    }

    /// Decide a pending proposal FROM THE HUD — one act, the same decision routes
    /// the desktop uses (origin picks the route; the audit names this surface).
    /// Re-polls for fresh truth so the row settles honestly.
    func decideMesh(_ proposal: MeshInboxProposal, approved: Bool) async {
        guard let client = meshClient else { return }
        if proposal.origin == "desk" {
            _ = try? await client.decideDeskProposal(
                target: proposal.target ?? "", proposalId: proposal.id, approved: approved)
        } else if let meetingId = proposal.meetingId {
            _ = try? await client.decideProposal(
                meetingId: meetingId, proposalId: proposal.id, approved: approved)
        }
        await pollMesh()
    }

    func seedDemo() {
        jobs = [
            QueuedJob("Standup digest", "Risks → questions", target: "Endpoint", status: .working, progress: 0.62),
            QueuedJob("Standup digest", "Decisions", target: "On-device", status: .queued),
            QueuedJob("Aftercare", "Action items", target: "Endpoint", status: .blocked, note: "endpoint down · retry 3/4 · auto-resumes"),
            QueuedJob("Standup digest", "Summary", target: "On-device", status: .done),
        ]
    }

    /// The mesh lane for a screenshot run: a grinding hub digest + a proposal
    /// awaiting the nod (the `HS_DEMO_MESHQ` affordance drives this).
    func seedMeshDemo(unreachable: Bool = false) {
        meshPeerName = "Karol's Mac"
        meshJobs = [
            MeshInboxJob(id: "intelq:m1", kind: "intel", label: "Q3 kickoff digest",
                         status: "running", meetingId: "m1", attempts: 1),
            MeshInboxJob(id: "pj1", kind: "plugin", label: "risk_register",
                         status: "queued", meetingId: "m1", attempts: 0),
        ]
        meshProposals = [
            MeshInboxProposal(id: "prop-d", origin: "desk", target: "slack",
                              action: "send_message",
                              preview: "Digest → #eng-updates", status: "proposed"),
        ]
        meshUnreachable = unreachable
    }
}

/// The floating queue pill + its expandable panel. Lives at the app root, above every screen.
struct QueueHUD: View {
    @ObservedObject private var store = RunQueueStore.shared
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulse = false
    @State private var selectedProjection: DeskProjectionDTO?

    var body: some View {
        VStack(spacing: 0) {
            if store.hasContent {
                if store.expanded { panel } else { pill }
            }
            Spacer(minLength: 0)
        }
        .padding(.top, 6)
        .frame(maxWidth: .infinity)
        .animation(.spring(response: 0.4, dampingFraction: 0.84), value: store.expanded)
        .animation(.spring(response: 0.45, dampingFraction: 0.85), value: store.jobs.count)
        .animation(.spring(response: 0.45, dampingFraction: 0.85), value: store.waitingAgents.count)
        .animation(.spring(response: 0.45, dampingFraction: 0.85), value: store.meshProposals.count)
        .animation(.spring(response: 0.45, dampingFraction: 0.85), value: store.meshJobs.count)
        .onAppear { pulse = true }
        .sheet(item: $selectedProjection) { projection in
            NavigationStack { projectionDetail(projection) }.preferredColorScheme(.dark)
        }
    }

    // Collapsed: a glanceable status pill, Dynamic-Island-style, under the status bar.
    private var pill: some View {
        Button { tactile(); store.expanded = true } label: {
            HStack(spacing: 9) {
                ZStack {
                    Circle().fill(beacon.color.opacity(0.25)).frame(width: 22, height: 22)
                        .scaleEffect(pulse ? 1.25 : 0.85)
                        .animation(reduceMotion ? nil : .easeInOut(duration: 0.9).repeatForever(autoreverses: true), value: pulse)
                    Image(systemName: beacon.glyph).font(.system(size: 11, weight: .black)).foregroundStyle(beacon.color)
                }
                Text(summary).font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.text)
                if !store.waitingAgents.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "hand.raised.fill").font(.system(size: 9, weight: .black))
                        Text(agentSummary).font(.system(size: 11, weight: .bold))
                    }
                    .foregroundStyle(Sig.warn)
                    .padding(.horizontal, 7).padding(.vertical, 3).background(Sig.warn.opacity(0.16), in: Capsule())
                }
                if !store.meshProposals.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "checkmark.seal.fill").font(.system(size: 9, weight: .black))
                        Text("\(store.meshProposals.count) to approve").font(.system(size: 11, weight: .bold))
                    }
                    .foregroundStyle(Sig.warn)
                    .padding(.horizontal, 7).padding(.vertical, 3).background(Sig.warn.opacity(0.16), in: Capsule())
                }
                if (store.projectionCounts["needs_attention"] ?? 0) > 0 {
                    HStack(spacing: 4) {
                        Image(systemName: "exclamationmark.bubble.fill").font(.system(size: 9, weight: .black))
                        Text("\(store.projectionCounts["needs_attention"] ?? 0) need you")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .foregroundStyle(Sig.warn)
                    .padding(.horizontal, 7).padding(.vertical, 3)
                    .background(Sig.warn.opacity(0.16), in: Capsule())
                }
                if store.blocked > 0 {
                    Text("\(store.blocked) blocked").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.warn)
                        .padding(.horizontal, 7).padding(.vertical, 3).background(Sig.warn.opacity(0.16), in: Capsule())
                }
                Image(systemName: "chevron.down").font(.system(size: 9, weight: .black)).foregroundStyle(Sig.faint)
            }
            .padding(.horizontal, 14).padding(.vertical, 9)
            .background(.ultraThinMaterial, in: Capsule())
            .overlay(Capsule().strokeBorder(Sig.topHairline, lineWidth: 1))
            .shadow(color: .black.opacity(0.4), radius: 12, y: 5)
        }.buttonStyle(PressableCard())
    }

    // Expanded: the full ledger of what the machine is doing right now.
    private var panel: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 10) {
                Image(systemName: "square.stack.3d.up.fill").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.accent)
                Text("QUEUE").font(.system(size: 11, weight: .heavy)).tracking(1.5).foregroundStyle(Sig.text)
                Text(summary).font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint)
                Spacer()
                Button { tactile(); store.expanded = false } label: {
                    Image(systemName: "chevron.up").font(.system(size: 13, weight: .black)).foregroundStyle(Sig.muted)
                        .frame(width: 30, height: 30).background(Sig.s2, in: Circle())
                }.buttonStyle(PressableCard())
            }
            .padding(.horizontal, 16).padding(.top, 14).padding(.bottom, 10)

            ScrollView {
                VStack(spacing: 8) {
                    ForEach(store.deskProjections) { projection in projectionRow(projection) }
                    ForEach(store.waitingAgents) { agent in agentLaneRow(agent) }
                    ForEach(store.meshProposals) { proposal in proposalRow(proposal) }
                    ForEach(store.ordered) { job in jobRow(job) }
                    ForEach(store.meshJobs) { job in meshJobRow(job) }
                    if store.projectionHasMore {
                        Button("Load older (\(max(0, store.projectionTotal - store.deskProjections.count)) remain)") {
                            Task { await store.loadOlderProjections() }
                        }
                        .font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.accent)
                    }
                }
                .padding(.horizontal, 12).padding(.bottom, 12)
            }
            .frame(maxHeight: 520)

            if store.meshUnreachable {
                HStack(spacing: 7) {
                    Image(systemName: "desktopcomputer.trianglebadge.exclamationmark").font(.system(size: 11, weight: .bold))
                    Text("\(store.meshPeerName) unreachable · auto-resumes").font(.system(size: 11, weight: .medium))
                }
                .foregroundStyle(Sig.warn).padding(.horizontal, 16).padding(.bottom, store.blocked > 0 ? 4 : 14)
            }
            if store.blocked > 0 {
                HStack(spacing: 7) {
                    Image(systemName: "clock.arrow.circlepath").font(.system(size: 11, weight: .bold))
                    Text("Resumes when the model is reachable.").font(.system(size: 11, weight: .medium))
                }
                .foregroundStyle(Sig.faint).padding(.horizontal, 16).padding(.bottom, 14)
            }
        }
        .frame(maxWidth: 440)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
        .shadow(color: .black.opacity(0.55), radius: 28, y: 14)
        .padding(.horizontal, 14)
        .transition(.move(edge: .top).combined(with: .opacity))
    }

    private func projectionRow(_ projection: DeskProjectionDTO) -> some View {
        Button { tactile(); selectedProjection = projection } label: {
            HStack(spacing: 12) {
                ZStack {
                    Circle().fill(projection.attentionState == "needs_attention" ? Sig.warn.opacity(0.16) : Sig.ok.opacity(0.14))
                        .frame(width: 36, height: 36)
                    Image(systemName: projection.projectionKind == "receipt" ? "checkmark.seal.fill" : "exclamationmark.bubble.fill")
                        .font(.system(size: 14, weight: .black))
                        .foregroundStyle(projection.attentionState == "needs_attention" ? Sig.warn : Sig.ok)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text(projection.title).font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.text).lineLimit(2)
                    Text("\(projection.subjectLabel) · \(projection.actualDestination ?? projection.outcome)")
                        .font(.system(size: 11, weight: .semibold)).foregroundStyle(Sig.faint).lineLimit(2)
                }
                Spacer(minLength: 4)
                Image(systemName: "chevron.right").font(.system(size: 10, weight: .bold)).foregroundStyle(Sig.faint)
            }
            .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 15, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
        }
        .buttonStyle(PressableCard())
        .accessibilityLabel("\(projection.subjectLabel), \(projection.title), \(projection.outcome)")
        .accessibilityHint("Opens destination, authority, attempt, outcome, and source receipt details")
    }

    private func projectionDetail(_ projection: DeskProjectionDTO) -> some View {
        List {
            Section("\(projection.projectionKind == "receipt" ? "Receipt" : "Attention") · \(projection.subjectLabel)") {
                Text(projection.title).font(.headline)
                Text(projection.summary).foregroundStyle(.secondary)
            }
            Section("What happened") {
                LabeledContent("Reason", value: projection.reasonCode)
                LabeledContent("Decision", value: projection.decisionKind)
                LabeledContent("Destination", value: projection.actualDestination ?? "Not reached")
                LabeledContent("Authority", value: projection.authorityBasis ?? "Not required")
                LabeledContent("Attempt", value: projection.attempt.map(String.init) ?? "—")
                LabeledContent("Outcome", value: projection.outcome)
                LabeledContent("Source", value: "\(projection.sourceKind) · \(projection.sourceId)")
            }
            Section {
                if projection.attentionState == "needs_attention" {
                    Button("Acknowledge") {
                        tactile(); selectedProjection = nil
                        Task { await store.setProjectionPresentation(projection, action: "acknowledge") }
                    }
                }
                Button("Dismiss this card") {
                    tactile(); selectedProjection = nil
                    Task { await store.setProjectionPresentation(projection, action: "dismiss") }
                }
            } footer: {
                Text("Dismissal changes only this Desk projection. The source record and subject remain unchanged.")
            }
        }
        .navigationTitle("Desk memory")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func jobRow(_ job: QueuedJob) -> some View {
        HStack(spacing: 12) {
            ZStack {
                Circle().fill(job.status.color.opacity(0.16)).frame(width: 36, height: 36)
                if job.status == .working {
                    Image(systemName: "bolt.fill").font(.system(size: 14, weight: .black)).foregroundStyle(job.status.color)
                        .scaleEffect(pulse ? 1.12 : 0.9)
                        .animation(reduceMotion ? nil : .easeInOut(duration: 0.6).repeatForever(autoreverses: true), value: pulse)
                } else {
                    Image(systemName: job.status.glyph).font(.system(size: 14, weight: .bold)).foregroundStyle(job.status.color)
                }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(job.step).font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 5) {
                    Text(job.workflow).font(.system(size: 11, weight: .medium)).foregroundStyle(Sig.faint)
                    Text("·").foregroundStyle(Sig.faint)
                    Image(systemName: job.target == "On-device" ? "ipad" : "network").font(.system(size: 9, weight: .bold))
                    Text(job.target).font(.system(size: 11, weight: .semibold))
                }.foregroundStyle(Sig.faint).lineLimit(1)
                if job.status == .working {
                    GeometryReader { g in
                        ZStack(alignment: .leading) {
                            Capsule().fill(Sig.s3).frame(height: 4)
                            Capsule().fill(Sig.accentGradient).frame(width: max(6, g.size.width * job.progress), height: 4)
                        }
                    }.frame(height: 4).padding(.top, 3)
                } else if let note = job.note {
                    Text(note).font(.system(size: 10.5, weight: .semibold)).foregroundStyle(job.status.color).lineLimit(1).padding(.top, 1)
                }
            }
            Spacer(minLength: 4)
            Text(job.status.label).font(.system(size: 10, weight: .heavy)).tracking(0.4)
                .foregroundStyle(job.status.color)
                .padding(.horizontal, 9).padding(.vertical, 5)
                .background(job.status.color.opacity(0.14), in: Capsule())
        }
        .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 15, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    // An agent-waiting lane row: a raised-hand glyph, "{agent} is waiting", the repo, and a
    // tap-to-open-desk affordance. Matches the jobRow craft (same chip + capsule label vocabulary).
    private func agentLaneRow(_ agent: WaitingAgent) -> some View {
        Button {
            tactile(); store.expanded = false; PresenceStore.shared.requestDesk = true
        } label: {
            HStack(spacing: 12) {
                ZStack {
                    Circle().fill(Sig.warn.opacity(0.16)).frame(width: 36, height: 36)
                    Image(systemName: "hand.raised.fill").font(.system(size: 14, weight: .black)).foregroundStyle(Sig.warn)
                        .scaleEffect(pulse ? 1.12 : 0.9)
                        .animation(reduceMotion ? nil : .easeInOut(duration: 0.7).repeatForever(autoreverses: true), value: pulse)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("\(agentName(agent.agent)) is waiting").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                    HStack(spacing: 5) {
                        Image(systemName: "cpu").font(.system(size: 9, weight: .bold))
                        Text(agent.repo).font(.system(size: 11, weight: .semibold))
                        Text("·").foregroundStyle(Sig.faint)
                        Text("tap to answer").font(.system(size: 11, weight: .medium))
                    }.foregroundStyle(Sig.faint).lineLimit(1)
                }
                Spacer(minLength: 4)
                Text("WAITING").font(.system(size: 10, weight: .heavy)).tracking(0.4)
                    .foregroundStyle(Sig.warn)
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(Sig.warn.opacity(0.14), in: Capsule())
            }
            .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 15, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(Sig.warn.opacity(0.25), lineWidth: 1))
        }
        .buttonStyle(PressableCard())
    }

    // A pending-approval row (HSM-15-03): the proposal's preview + its target,
    // and the two decision buttons — approving here IS approving on the desktop
    // (one act, the same route, the audit names this surface). Blocked-lane
    // vocabulary: it is work waiting on YOU.
    private func proposalRow(_ proposal: MeshInboxProposal) -> some View {
        HStack(spacing: 12) {
            ZStack {
                Circle().fill(Sig.warn.opacity(0.16)).frame(width: 36, height: 36)
                Image(systemName: "checkmark.seal.fill").font(.system(size: 14, weight: .black)).foregroundStyle(Sig.warn)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(proposal.preview ?? proposal.action ?? "Proposal")
                    .font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 5) {
                    Image(systemName: "desktopcomputer").font(.system(size: 9, weight: .bold))
                    Text(store.meshPeerName).font(.system(size: 11, weight: .semibold))
                    Text("·").foregroundStyle(Sig.faint)
                    Text(proposal.target ?? "").font(.system(size: 11, weight: .semibold))
                }.foregroundStyle(Sig.faint).lineLimit(1)
            }
            Spacer(minLength: 4)
            Button {
                tactile()
                Task { await store.decideMesh(proposal, approved: false) }
            } label: {
                Text("Reject").font(.system(size: 11, weight: .heavy))
                    .foregroundStyle(Sig.muted)
                    .padding(.horizontal, 11).padding(.vertical, 6)
                    .background(Sig.s3, in: Capsule())
            }.buttonStyle(PressableCard())
            Button {
                tactile()
                Task { await store.decideMesh(proposal, approved: true) }
            } label: {
                Text(proposal.commitment?.approve ?? "Approve for \(proposal.target ?? "executor")")
                    .font(.system(size: 11, weight: .heavy)).lineLimit(1)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 11).padding(.vertical, 6)
                    .background(Sig.accentGradient, in: Capsule())
            }.buttonStyle(PressableCard())
        }
        .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 15, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(Sig.warn.opacity(0.25), lineWidth: 1))
    }

    // A hub job row (HSM-15-03): the same job vocabulary, the origin naming the
    // peer. When the peer is unreachable the row degrades to blocked-style
    // (`auto-resumes`) — a first-class state, never an error spinner.
    private func meshJobRow(_ job: MeshInboxJob) -> some View {
        let status: JobStatus = store.meshUnreachable ? .blocked
            : (job.status == "running" ? .working : .queued)
        return HStack(spacing: 12) {
            ZStack {
                Circle().fill(status.color.opacity(0.16)).frame(width: 36, height: 36)
                Image(systemName: status.glyph).font(.system(size: 14, weight: .bold)).foregroundStyle(status.color)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(job.label ?? job.id).font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 5) {
                    Text(job.kind == "plugin" ? "Plugin run" : "Meeting digest")
                        .font(.system(size: 11, weight: .medium)).foregroundStyle(Sig.faint)
                    Text("·").foregroundStyle(Sig.faint)
                    Image(systemName: "desktopcomputer").font(.system(size: 9, weight: .bold))
                    Text(store.meshPeerName).font(.system(size: 11, weight: .semibold))
                }.foregroundStyle(Sig.faint).lineLimit(1)
                if store.meshUnreachable {
                    Text("peer unreachable · auto-resumes")
                        .font(.system(size: 10.5, weight: .semibold)).foregroundStyle(status.color)
                        .lineLimit(1).padding(.top, 1)
                }
            }
            Spacer(minLength: 4)
            Text(status.label).font(.system(size: 10, weight: .heavy)).tracking(0.4)
                .foregroundStyle(status.color)
                .padding(.horizontal, 9).padding(.vertical, 5)
                .background(status.color.opacity(0.14), in: Capsule())
        }
        .padding(11).background(Sig.s2, in: RoundedRectangle(cornerRadius: 15, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    private func agentName(_ a: String) -> String { a.lowercased() == "codex" ? "Codex" : "Claude" }

    private var beacon: JobStatus {
        store.blocked > 0 || !store.waitingAgents.isEmpty || !store.meshProposals.isEmpty || store.meshUnreachable
            ? .blocked : (store.working > 0 || store.meshWorking > 0 ? .working : .queued)
    }
    private var summary: String {
        var parts: [String] = []
        if store.working > 0 { parts.append("\(store.working) working") }
        if store.queued > 0 { parts.append("\(store.queued) queued") }
        if !store.meshJobs.isEmpty { parts.append("\(store.meshJobs.count) on \(store.meshPeerName)") }
        if parts.isEmpty && store.jobs.isEmpty && !store.waitingAgents.isEmpty { return "Coder sessions" }
        if parts.isEmpty { parts.append(store.meshProposals.isEmpty ? "idle" : "needs you") }
        return parts.joined(separator: " · ")
    }
    private var agentSummary: String {
        let n = store.waitingAgents.count
        if n == 1, let one = store.waitingAgents.first { return "1 coder session waiting · \(one.repo)" }
        return "\(n) coder sessions waiting"
    }
}


// MARK: - Proactive agent presence (HSM-15-09)

// Dictation taps the agent; presence taps YOU. This is the app-wide proactive layer: a
// poll of `companionStatus()` feeds the pure `PresenceWatcher`, the HUD gains a waiting
// lane, and the moment a coder crosses into "awaiting on you" a tight nudge slides in —
// answer by voice on the spot, open the desk, or dismiss. It only ever surfaces; it never
// answers for you. Quiet-mode + per-agent mute respect your focus.

/// The app-wide presence brain + the surfaces' shared state. One instance, mounted at the
/// app root next to the Queue HUD, so a waiting agent reaches every screen — even mid-meeting.
@MainActor final class PresenceStore: ObservableObject {
    static let shared = PresenceStore()

    /// The current nudge stack (newest on top). Edge-triggered: one entry per rising edge.
    @Published var nudges: [PresenceEvent] = []
    /// The latest full companion snapshot — so opening the desk from a nudge/lane shows the
    /// live board (not an empty one).
    @Published var board = CompanionBoardState()
    /// Set by the HUD lane / a nudge action to ask the host to open the Agent Desk.
    @Published var requestDesk = false
    /// The session a nudge wants to answer-by-voice; the host routes it into the desk's
    /// answer composer (reusing the HSM-13 spine). nil when no answer is pending.
    @Published var answerTarget: CompanionTarget?
    /// Focus / do-not-disturb — suppresses surfacing (the watcher still tracks edges).
    @Published var quiet = false { didSet { watcher.quiet = quiet } }

    private var watcher = PresenceWatcher()
    private var pollTask: Task<Void, Never>?

    /// Drive the watcher + the HUD lane from a fresh companion snapshot. The lane reflects
    /// *currently* waiting agents; the nudge is fired only on a rising edge.
    func ingest(_ state: CompanionBoardState, now: Date = Date()) {
        board = state
        // The always-on HUD lane: who is waiting right now.
        let waiting = state.targets
            .filter { PresenceWatcher.isWaiting($0) }
            .map { WaitingAgent(id: $0.id, agent: $0.agent, repo: $0.project ?? "—") }
        RunQueueStore.shared.setWaiting(waiting)

        // The rising-edge nudge(s).
        for event in watcher.ingest(state, now: now) where !nudges.contains(where: { $0.id == event.id }) {
            nudges.append(event)
        }
    }

    /// Mute a session for the rest of the run (per-agent mute) and drop its nudge.
    func mute(_ id: String) {
        watcher.muted.insert(id)
        nudges.removeAll { $0.id == id }
    }

    /// Dismiss a nudge without muting — the lane keeps it; the agent's NEXT fresh ask re-fires.
    func dismiss(_ id: String) {
        watcher.forget(id)
        nudges.removeAll { $0.id == id }
    }

    /// One-tap voice answer from a nudge: hand the target to the desk's answer composer
    /// (the HSM-13 spine) and clear the nudge. Honest + non-autonomous — it opens the
    /// composer, it never sends for you.
    func answerByVoice(_ event: PresenceEvent) {
        answerTarget = event.target
        requestDesk = true
        nudges.removeAll { $0.id == event.id }
    }

    /// Begin polling a live desktop client (device/LAN). Off in the Simulator demo (which
    /// seeds `ingest` directly). Honors quiet-mode via the watcher.
    func startPolling(_ client: IDesktopClient, every seconds: TimeInterval = 4) {
        pollTask?.cancel()
        pollTask = Task { [weak self] in
            while !Task.isCancelled {
                if let state = try? await client.companionStatus() { self?.ingest(state) }
                try? await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
            }
        }
        // TODO(HSM-15-09): when backgrounded, raise an opt-in local notification for a
        // fresh rising edge (UNUserNotificationCenter), gated by quiet-mode + per-agent mute.
    }

    func stopPolling() { pollTask?.cancel(); pollTask = nil }

    #if targetEnvironment(simulator)
    /// A freshly-waiting board for the `HS_DEMO_PRESENCE` screenshot: one agent crossing into
    /// "awaiting on you" with a real-sounding ask (fires the nudge + populates the HUD lane).
    static let demoSeed = CompanionBoardState(
        readyForReply: true, blockers: [], awaiting: true,
        targets: [
            CompanionTarget(agent: "claude", sessionID: "s1",
                            question: "Run the destructive schema migration on prod now, or stage it behind a backup first?",
                            project: "holdspeak/web-runtime", selected: true, confidence: "high"),
            CompanionTarget(agent: "codex", sessionID: "s2",
                            question: "Keep retrying the flaky integration test or skip it?",
                            project: "acme/billing-api", confidence: "medium"),
        ])
    #endif
}

/// The presence nudge: a tight, dismissible Signal card that slides in from the top when an
/// agent crosses into waiting. The question rides as a TIGHT quote (never prose); actions are
/// Answer (voice) / Open desk / Dismiss. Only the topmost nudge shows; the rest stack behind.
struct PresenceNudgeOverlay: View {
    @ObservedObject private var store = PresenceStore.shared
    @ObservedObject private var queue = RunQueueStore.shared
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulse = false

    var body: some View {
        VStack {
            if let event = store.nudges.last {
                PresenceNudgeCard(event: event, pulse: $pulse,
                                  onAnswer: { store.answerByVoice(event) },
                                  onOpenDesk: { store.requestDesk = true; store.dismiss(event.id) },
                                  onDismiss: { store.dismiss(event.id) },
                                  onMute: { store.mute(event.id) })
                    .padding(.horizontal, 14)
                    .transition(reduceMotion ? .opacity : .move(edge: .top).combined(with: .opacity))
                    .id(event.id)
            }
            Spacer(minLength: 0)
        }
        // Sit below the Queue HUD: the collapsed pill (~64) or the expanded ledger panel,
        // so the two proactive surfaces never overlap.
        .padding(.top, queue.expanded ? 260 : 64)
        .frame(maxWidth: .infinity)
        .animation(reduceMotion ? nil : .spring(response: 0.5, dampingFraction: 0.82), value: store.nudges.map(\.id))
        .onAppear { if !reduceMotion { pulse = true } }
    }
}

private struct PresenceNudgeCard: View {
    let event: PresenceEvent
    @Binding var pulse: Bool
    let onAnswer: () -> Void
    let onOpenDesk: () -> Void
    let onDismiss: () -> Void
    let onMute: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var agentLabel: String { event.agent.lowercased() == "codex" ? "Codex" : "Claude" }
    private var agentGlyph: String { event.agent.lowercased() == "codex" ? "chevron.left.forwardslash.chevron.right" : "sparkles" }

    /// The ask, tightened to a single quote — the SAME discipline the desk card uses (no prose).
    private var tightQuestion: String? {
        guard let q = event.question?.trimmingCharacters(in: .whitespacesAndNewlines), !q.isEmpty else { return nil }
        let collapsed = q.split(whereSeparator: { $0.isNewline || $0 == "\t" })
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }.joined(separator: " ")
        var first = collapsed
        if let end = collapsed.firstIndex(where: { $0 == "?" || $0 == "." || $0 == "!" }) {
            first = String(collapsed[...end])
        }
        if first.count > 92 { first = String(first.prefix(89)).trimmingCharacters(in: .whitespaces) + "…" }
        return first
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 11) {
                GlyphChip(system: agentGlyph, gradient: Sig.accentGradient, size: 42)
                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 6) {
                        Circle().fill(Sig.warn).frame(width: 7, height: 7)
                            .scaleEffect(pulse ? 1.35 : 1)
                            .animation(reduceMotion ? nil : .easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: pulse)
                        Text("WAITING ON YOU").font(.system(size: 10, weight: .heavy)).tracking(1.1).foregroundStyle(Sig.warn)
                    }
                    HStack(spacing: 5) {
                        Text(event.project ?? "—").font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                        Text("·").foregroundStyle(Sig.faint)
                        Text(agentLabel).font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.faint)
                    }
                }
                Spacer(minLength: 4)
                Button { tactile(.light); onMute() } label: {
                    Image(systemName: "bell.slash.fill").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
                        .frame(width: 32, height: 32).background(Sig.s3, in: Circle())
                }.buttonStyle(PressableCard()).accessibilityLabel("Mute this agent")
                Button { tactile(.light); onDismiss() } label: {
                    Image(systemName: "xmark").font(.system(size: 12, weight: .black)).foregroundStyle(Sig.muted)
                        .frame(width: 32, height: 32).background(Sig.s3, in: Circle())
                }.buttonStyle(PressableCard()).accessibilityLabel("Dismiss")
            }

            if let q = tightQuestion {
                Text("“\(q)”")
                    .font(.system(size: 15, weight: .semibold).italic())
                    .foregroundStyle(Sig.text).lineSpacing(3).lineLimit(2)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.vertical, 11).padding(.leading, 15).padding(.trailing, 13)
                    .background(Sig.accent.opacity(0.08), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 2, style: .continuous)
                            .fill(Sig.accentGradient).frame(width: 3).padding(.vertical, 9).padding(.leading, 6)
                    }
                    .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Sig.accent.opacity(0.12), lineWidth: 1))
            }

            HStack(spacing: 10) {
                Button { tactile(.medium); onAnswer() } label: {
                    HStack(spacing: 7) {
                        Image(systemName: "mic.fill").font(.system(size: 13, weight: .bold))
                        Text("Answer").font(.system(size: 14, weight: .heavy))
                    }
                    .foregroundStyle(.black).padding(.horizontal, 18).padding(.vertical, 10)
                    .background(Sig.accentGradient, in: Capsule())
                    .overlay(Capsule().strokeBorder(.white.opacity(0.2), lineWidth: 1))
                }.buttonStyle(PressableCard())
                Button { tactile(.light); onOpenDesk() } label: {
                    Text("Open desk").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.text)
                        .padding(.horizontal, 16).padding(.vertical, 10)
                        .background(Sig.s3, in: Capsule())
                        .overlay(Capsule().strokeBorder(Sig.topHairline, lineWidth: 1))
                }.buttonStyle(PressableCard())
                Spacer(minLength: 0)
            }
        }
        .padding(15)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(Sig.accent.opacity(pulse ? 0.5 : 0.28), lineWidth: 1.5)
            .animation(reduceMotion ? nil : .easeInOut(duration: 1.4).repeatForever(autoreverses: true), value: pulse))
        .shadow(color: .black.opacity(0.5), radius: 26, y: 12)
        .shadow(color: Sig.accent.opacity(0.16), radius: 20, y: 6)
        .frame(maxWidth: 460)
    }
}
