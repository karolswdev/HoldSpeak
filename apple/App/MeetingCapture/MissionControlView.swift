import SwiftUI

// HSM-25-02 — the conveyor: mission control's belt, the Agent Desk's
// bigger sibling. Same posture as CompanionBoardState/AgentDeskView
// (HSM-15-08): a poll-populated @Published model, unreachable
// rendered as a first-class state (never thrown), a #if simulator
// seed for offline screenshots. Design tokens: Sig.* + .signalCard
// verbatim, matching the Agent Desk exactly.

/// Mission control's live state — unreachable is a rendered `Reach`
/// case, never an error surfaced by throwing.
enum MCReach: Equatable {
    case connecting
    case ok
    case unreachable(String)
    /// The owner-only routes rejected the token (401/403): a
    /// distinct state from "can't reach the hub" so the fix is
    /// obvious (re-pair), not "check your network".
    case unauthorized
}

@MainActor
final class MissionControlModel: ObservableObject {
    @Published var reach: MCReach = .connecting
    @Published var repos: [MCRepoState] = []
    @Published var pins: [String: [MCSession]] = [:]
    @Published var offBelt: [MCSession] = []
    @Published var events: [MCEvent] = []

    private let client: HTTPDesktopClient
    private var pollTask: Task<Void, Never>?

    init(client: HTTPDesktopClient) {
        self.client = client
    }

    func startPolling() {
        guard pollTask == nil else { return }
        guard ProcessInfo.processInfo.environment["HS_DESK_MC"] == nil else { return }
        pollTask = Task { @MainActor in
            while !Task.isCancelled {
                await tick()
                try? await Task.sleep(nanoseconds: 4_000_000_000)
            }
        }
    }

    func stopPolling() {
        pollTask?.cancel()
        pollTask = nil
    }

    /// One poll tick: unreachable keeps last truth (the coder-poll
    /// idiom) rather than clearing the belt to empty.
    func tick() async {
        do {
            let state = try await client.missionControlState()
            repos = state.repos
            reach = .ok
        } catch let error as HTTPDesktopClient.DesktopClientError {
            if case .http(let code) = error, code == 401 || code == 403 {
                reach = .unauthorized
            } else {
                reach = .unreachable("hub unreachable")
            }
            return // sessions/events are meaningless without a live feed
        } catch {
            reach = .unreachable("hub unreachable")
            return
        }

        if let sessionsPayload = try? await client.missionControlSessions(),
           sessionsPayload.isLive, let doc = sessionsPayload.sessions {
            (pins, offBelt) = pinMissionControlSessions(doc.sessions)
        }
        if let eventsPayload = try? await client.missionControlEvents(tail: 20) {
            events = eventsPayload.repos.flatMap { $0.events ?? [] }
        }
    }

    #if targetEnvironment(simulator)
    /// Offline demo seed (the CompanionMesh idiom): a plausible belt
    /// for Simulator screenshots, gated by env so it never fires on
    /// a real device.
    func seedDemo() {
        guard ProcessInfo.processInfo.environment["HS_DEMO_MC"] != nil else { return }
        reach = .ok
        repos = [MCRepoState(
            name: "delivery-workbench", path: "/repos/dw", status: "live",
            feed: MCFeed(feedSchema: 1, projects: [MCProject(
                slug: "work-log-automation", prefix: "WLA",
                currentPhase: MCPhase(number: 14, title: "The Absorption",
                                      status: "open", storiesDone: 6, storiesTotal: 7),
                nextStory: MCNextStory(storyId: "WLA-14-07", title: "Prove it", status: "backlog"),
                phases: [MCPhase(number: 14, title: "The Absorption",
                                  status: "open", storiesDone: 6, storiesTotal: 7)],
                stories: [MCStory(storyId: "WLA-14-07", title: "Prove it",
                                   status: "backlog", phase: 14, evidenceExists: false)],
                warnings: 1)]))]
        (pins, offBelt) = pinMissionControlSessions([
            MCSession(key: "claude:demo", agent: "claude", correlation: "on_story",
                      stories: [MCSessionStory(storyId: "WLA-14-07")],
                      awaitingResponse: true, stale: false, tmux: nil),
        ])
        events = [MCEvent(ts: "2026-07-05T00:00:00Z", event: "gate_refusal",
                           story: "WLA-14-07", detail: ["rule": .string("story-evidence")])]
    }
    #endif
}

struct MissionControlView: View {
    @StateObject private var model: MissionControlModel
    @Environment(\.dismiss) private var dismiss

    init(client: HTTPDesktopClient) {
        _model = StateObject(wrappedValue: MissionControlModel(client: client))
    }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    header
                    content
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .navigationTitle("")
        .topBack { dismiss() }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .onAppear {
            #if targetEnvironment(simulator)
            model.seedDemo()
            #endif
            model.startPolling()
        }
        .onDisappear { model.stopPolling() }
    }

    private var header: some View {
        HStack {
            Text("Mission Control").font(.title2.weight(.semibold)).foregroundStyle(Sig.text)
            Spacer()
            reachChip
        }
        .padding(.top, 40) // clears the .topBack overlay chip (Simulator-proven overlap fix)
    }

    @ViewBuilder private var reachChip: some View {
        switch model.reach {
        case .connecting: mcChip("clock", "connecting", Sig.muted)
        case .ok: mcChip("checkmark.circle", "live", Sig.ok)
        case .unreachable: mcChip("wifi.slash", "unreachable", Sig.bad)
        case .unauthorized: mcChip("lock", "pair with the owner token", Sig.warn)
        }
    }

    /// A small glyph+text pill (there's no existing small chip in the
    /// shared design system — `GlyphChip` is a large icon badge, a
    /// different shape) for the reach indicator and repo status.
    private func mcChip(_ glyph: String, _ text: String, _ tint: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: glyph).font(.caption2)
            Text(text).font(.caption2)
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 8).padding(.vertical, 3)
        .background(Capsule().fill(tint.opacity(0.15)))
    }

    @ViewBuilder private var content: some View {
        switch model.reach {
        case .connecting:
            emptyState("Connecting to the hub…")
        case .unreachable(let detail):
            emptyState(detail)
        case .unauthorized:
            emptyState("This hub's mission control needs the owner token. Pair in Settings.")
        case .ok:
            if model.repos.isEmpty {
                emptyState("No rails repos configured on this hub.")
            } else {
                ForEach(model.repos, id: \.path) { repo in repoBlock(repo) }
                if !model.offBelt.isEmpty { offBeltSection }
                if !model.events.isEmpty { eventsSection }
            }
        }
    }

    private func emptyState(_ text: String) -> some View {
        Text(text).foregroundStyle(Sig.muted).padding(.top, 40)
    }

    @ViewBuilder
    private func repoBlock(_ repo: MCRepoState) -> some View {
        if !repo.isLive {
            HStack {
                Text(repo.name).foregroundStyle(Sig.text)
                mcChip("exclamationmark.triangle", repo.status, Sig.warn)
            }
            .signalCard()
        } else if let feed = repo.feed {
            ForEach(feed.projects, id: \.slug) { project in
                projectBelt(project)
            }
        }
    }

    private func projectBelt(_ project: MCProject) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 4) {
                Text(project.slug).font(.headline).foregroundStyle(Sig.text)
                ForEach(project.phases, id: \.number) { phase in
                    Text("\(phase.number)")
                        .font(.caption2.monospaced())
                        .foregroundStyle(phase.status == "closed" ? Sig.faint
                            : (phase.number == project.currentPhase?.number ? Sig.text : Sig.muted))
                        .padding(.horizontal, 5).padding(.vertical, 1)
                        .background(RoundedRectangle(cornerRadius: 4).stroke(Sig.line))
                }
                if project.warnings > 0 {
                    Text("⚠ \(project.warnings)").font(.caption2).foregroundStyle(Sig.warn)
                }
            }
            let beltStories = project.currentPhase.map { current in
                project.stories.filter { $0.phase == current.number }
            } ?? []
            FlowLayout(spacing: 6) {
                ForEach(beltStories, id: \.storyId) { story in
                    storyChip(story, project: project)
                }
            }
        }
        .signalCard()
    }

    private func storyChip(_ story: MCStory, project: MCProject) -> some View {
        let isNext = story.storyId == project.nextStory?.storyId
        return HStack(spacing: 4) {
            Text(story.storyId).font(.caption.monospaced())
            if story.evidenceExists { Text("✓").font(.caption2) }
            ForEach(model.pins[story.storyId] ?? [], id: \.key) { session in
                sessionPin(session)
            }
        }
        .foregroundStyle(isNext ? Sig.accent : Sig.muted)
        .padding(.horizontal, 8).padding(.vertical, 3)
        .background(
            Capsule().stroke(isNext ? Sig.accent : Sig.line, lineWidth: isNext ? 1.5 : 1)
        )
    }

    private func sessionPin(_ session: MCSession) -> some View {
        Text("\(session.awaitingResponse ? "🙋" : "🤖")\(session.agent)")
            .font(.caption2)
            .opacity(session.stale ? 0.5 : 1)
            .padding(.horizontal, 5)
            .background(Capsule().fill(Sig.s2))
    }

    private var offBeltSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("off the belt").font(.caption.weight(.semibold)).foregroundStyle(Sig.muted)
            ForEach(model.offBelt, id: \.key) { session in
                HStack {
                    Text(session.key).font(.caption.monospaced())
                    Text(session.correlation.replacingOccurrences(of: "_", with: " "))
                        .font(.caption2).foregroundStyle(Sig.faint)
                }
                .foregroundStyle(Sig.text)
            }
        }
        .signalCard()
    }

    private var eventsSection: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("rail events").font(.caption.weight(.semibold)).foregroundStyle(Sig.muted)
            ForEach(model.events.reversed().prefix(6), id: \.ts) { event in
                let isRefusal = event.event == "gate_refusal"
                Text("\(isRefusal ? "✕ " : "")\(formatMCEvent(event))")
                    .font(.caption2.monospaced())
                    .foregroundStyle(isRefusal ? Sig.bad : Sig.faint)
            }
        }
        .signalCard()
    }
}

#if targetEnvironment(simulator)
/// Simulator-only: the belt seeded for a design screenshot (the
/// AgentDeskDemo/DictateDemo idiom). HS_DEMO_MISSIONCONTROL=1 to
/// route here from MeetingCaptureApp; HS_DEMO_MC=1 fires the seed
/// inside MissionControlModel; no live hub is reachable in the
/// Simulator, so polling never needs to succeed for this shot.
struct MissionControlDemo: View {
    var body: some View {
        let peer = DesktopPeer(host: "127.0.0.1", port: 8080)
        let config = HTTPDesktopClient.Config(peer: peer) ?? HTTPDesktopClient.Config(baseURL: URL(string: "http://127.0.0.1:8080")!)
        NavigationStack {
            MissionControlView(client: HTTPDesktopClient(config: config))
        }
    }
}
#endif
