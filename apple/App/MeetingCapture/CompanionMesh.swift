import SwiftUI
import Foundation
import Network

// HSM-14-19 "The Desk" decomposition: the Companion + Mesh surface — the Agent Desk (HSM-15-08), the
// dictate-into-your-Mac peer (Phase 13/15), and LAN mesh discovery/pairing (NWBrowser) — lifted
// verbatim out of MeetingCaptureApp.swift. Same module; HTTPDesktopClient/Sig/etc. resolve.

// MARK: - The Agent Desk (HSM-15-08)

/// The Agent Desk — HoldSpeak's third pillar beside dictation and meetings: a glanceable command
/// surface for the AI coding agents you run. Each live `CompanionTarget` becomes a Signal card —
/// repo, the agent (Claude/Codex), a STATE chip (working / waiting on you / idle / stale), and, when
/// waiting, the question as a tight quote (never prose). Waiting agents sort to the top and pulse.
/// Reads from a `CompanionBoardState`: live over `HTTPDesktopClient.companionStatus()`, or an injected
/// seed for the Simulator. No narration — chips + quotes only (POSITIONING).
struct AgentDeskView: View {
    /// Injected for the Simulator seed; the live wiring polls `companionStatus()` into this.
    @State var state: CompanionBoardState
    @State private var pulse = false
    @State private var appeared = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    /// Waiting (and pinned) sort to the top; within a tier, stable by id.
    private var ordered: [CompanionTarget] {
        state.targets.enumerated().sorted { a, b in
            let (ai, av) = a; let (bi, bv) = b
            if AgentDeskView.rank(av) != AgentDeskView.rank(bv) {
                return AgentDeskView.rank(av) < AgentDeskView.rank(bv)
            }
            return ai < bi
        }.map { $0.element }
    }

    /// Sort key: a waiting agent first, then pinned, then everything else; stale sinks.
    static func rank(_ t: CompanionTarget) -> Int {
        if AgentDeskView.isWaiting(t) { return t.pinned ? 0 : 1 }
        if t.stale { return 4 }
        return t.pinned ? 2 : 3
    }

    static func isWaiting(_ t: CompanionTarget) -> Bool {
        !t.stale && (t.question?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false)
    }

    private var waitingCount: Int { state.targets.filter { AgentDeskView.isWaiting($0) }.count }

    var body: some View {
        ZStack {
            background
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    header
                    if state.targets.isEmpty {
                        emptyState.transition(.opacity)
                    } else {
                        ForEach(Array(ordered.enumerated()), id: \.element.id) { i, t in
                            AgentDeskCard(target: t, pulse: $pulse,
                                          onAnswer: { answer(t) }, onPin: { pin(t) }, onDismiss: { dismiss(t) })
                                .opacity(appeared ? 1 : 0)
                                .offset(y: appeared ? 0 : 16)
                                .animation(reduceMotion ? nil : .spring(response: 0.5, dampingFraction: 0.82)
                                    .delay(0.04 + Double(i) * 0.05), value: appeared)
                        }
                    }
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .navigationTitle("")
        .topBack { dismiss() }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .onAppear {
            withAnimation(reduceMotion ? nil : .spring(response: 0.6, dampingFraction: 0.85)) { appeared = true }
            if !reduceMotion { pulse = true }
        }
    }

    private var background: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(waitingCount > 0 ? 0.18 : 0.12)).frame(width: 420)
                .blur(radius: 130).offset(x: 150, y: -300).ignoresSafeArea()
            Circle().fill(Sig.local.opacity(0.10)).frame(width: 360)
                .blur(radius: 140).offset(x: -180, y: -180).ignoresSafeArea()
        }
    }

    // Workbench-grade header: an eyebrow badge that reads waiting count, a heavy title, a glyph chip.
    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 7) {
                HStack(spacing: 6) {
                    Circle().fill(waitingCount > 0 ? Sig.warn : Sig.ok).frame(width: 7, height: 7)
                        .scaleEffect(pulse && waitingCount > 0 ? 1.35 : 1)
                        .animation(reduceMotion ? nil : .easeInOut(duration: 0.9).repeatForever(autoreverses: true), value: pulse)
                    Text(waitingCount > 0 ? "\(waitingCount) WAITING ON YOU" : "ALL CLEAR")
                        .font(.system(size: 10, weight: .heavy)).tracking(1.4)
                }
                .foregroundStyle(waitingCount > 0 ? Sig.warn : Sig.ok)
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background((waitingCount > 0 ? Sig.warn : Sig.ok).opacity(0.12), in: Capsule())
                .overlay(Capsule().strokeBorder((waitingCount > 0 ? Sig.warn : Sig.ok).opacity(0.25), lineWidth: 1))
                Text("Agent Desk").font(.system(size: 38, weight: .heavy)).foregroundStyle(Sig.text)
                    .shadow(color: .black.opacity(0.3), radius: 8, y: 3)
            }
            Spacer()
            ZStack {
                GlyphChip(system: "cpu.fill", gradient: Sig.accentGradient, size: 50)
                if !state.targets.isEmpty {
                    Text("\(state.targets.count)").font(.system(size: 11, weight: .heavy).monospacedDigit())
                        .foregroundStyle(.white).padding(.horizontal, 6).padding(.vertical, 2)
                        .background(Sig.bad, in: Capsule()).overlay(Capsule().strokeBorder(Sig.bg, lineWidth: 2))
                        .offset(x: 20, y: -20)
                }
            }
        }
        .padding(.top, 8)
        .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 10)
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle().fill(Sig.accentSoft).frame(width: 84, height: 84)
                Circle().strokeBorder(Sig.accent.opacity(0.3), lineWidth: 1).frame(width: 84, height: 84)
                Image(systemName: "cpu").font(.system(size: 32, weight: .semibold)).foregroundStyle(Sig.accent)
            }
            VStack(spacing: 6) {
                Text("No agents linked").font(.system(size: 18, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Run a coding agent on your desktop")
                    .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.faint)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity).padding(.vertical, 50)
    }

    // Answer / manage actions reuse the HSM-13 spine over the companion routes. Stubbed here for the
    // surface build; the live wiring drives select → voice/type → /api/dictation/remote (TODO HSM-15-08).
    private func answer(_ t: CompanionTarget) {
        tactile(.medium)
        // TODO(HSM-15-08): selectCompanionTarget(t) → present the HSM-13 voice/type answer composer →
        // sendRemoteDictation → delivered into this agent's tmux pane.
    }
    private func pin(_ t: CompanionTarget) {
        tactile(.light)
        // TODO(HSM-15-08): pinCompanionTarget(agent:sessionID:pinned:) over the live client; mutate locally too.
        if let i = state.targets.firstIndex(where: { $0.id == t.id }) {
            state.targets[i].pinned.toggle()
        }
    }
    private func dismiss(_ t: CompanionTarget) {
        tactile(.light)
        // TODO(HSM-15-08): dismissCompanionTarget(agent:sessionID:) over the live client.
        if let i = state.targets.firstIndex(where: { $0.id == t.id }) {
            state.targets[i].question = nil
        }
    }
}

/// One agent on the desk — a Signal card. Waiting agents wear a warm border + a breathing pulse and
/// surface the question as a tight quote; idle/stale read quieter.
private struct AgentDeskCard: View {
    let target: CompanionTarget
    @Binding var pulse: Bool
    let onAnswer: () -> Void
    let onPin: () -> Void
    let onDismiss: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var waiting: Bool { AgentDeskView.isWaiting(target) }
    private var agentLabel: String { target.agent.lowercased() == "codex" ? "Codex" : "Claude" }
    private var agentGlyph: String { target.agent.lowercased() == "codex" ? "chevron.left.forwardslash.chevron.right" : "sparkles" }

    /// State chip color + label + glyph.
    private var stateColor: Color { target.stale ? Sig.faint : (waiting ? Sig.warn : Sig.ok) }
    private var stateLabel: String { target.stale ? "STALE" : (waiting ? "WAITING ON YOU" : "WORKING") }
    private var stateGlyph: String { target.stale ? "clock.badge.xmark" : (waiting ? "hand.raised.fill" : "bolt.fill") }

    /// The question, tightened to a single tight quote — never a paragraph (POSITIONING).
    private var tightQuestion: String? {
        guard let q = target.question?.trimmingCharacters(in: .whitespacesAndNewlines), !q.isEmpty else { return nil }
        // Collapse whitespace; take the first sentence/line; cap length.
        let collapsed = q.split(whereSeparator: { $0.isNewline || $0 == "\t" })
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }.joined(separator: " ")
        var first = collapsed
        if let end = collapsed.firstIndex(where: { $0 == "?" || $0 == "." || $0 == "!" }) {
            first = String(collapsed[...end])
        }
        if first.count > 96 {
            first = String(first.prefix(93)).trimmingCharacters(in: .whitespaces) + "…"
        }
        return first
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 13) {
            HStack(spacing: 13) {
                GlyphChip(system: agentGlyph, gradient: waiting ? Sig.accentGradient : Sig.localGradient, size: 46)
                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 7) {
                        Text(agentLabel).font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                        if target.pinned {
                            Image(systemName: "pin.fill").font(.system(size: 10, weight: .bold)).foregroundStyle(Sig.accent)
                        }
                    }
                    Text(target.project ?? "—").font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Sig.faint).lineLimit(1)
                }
                Spacer()
                stateChip
            }

            if let q = tightQuestion, waiting {
                Text("“\(q)”")
                    .font(.system(size: 15, weight: .semibold).italic())
                    .foregroundStyle(Sig.text)
                    .lineSpacing(4)
                    .multilineTextAlignment(.leading)
                    .lineLimit(3)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.vertical, 12).padding(.leading, 16).padding(.trailing, 14)
                    .background(Sig.accent.opacity(0.07), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 2, style: .continuous)
                            .fill(Sig.accentGradient).frame(width: 3).padding(.vertical, 10).padding(.leading, 7)
                    }
                    .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Sig.accent.opacity(0.12), lineWidth: 1))
            }

            if waiting {
                HStack(spacing: 10) {
                    Button(action: onAnswer) {
                        HStack(spacing: 7) {
                            Image(systemName: "mic.fill").font(.system(size: 13, weight: .bold))
                            Text("Answer").font(.system(size: 14, weight: .heavy))
                        }
                        .foregroundStyle(.black).padding(.horizontal, 16).padding(.vertical, 10)
                        .background(Sig.accentGradient, in: Capsule())
                        .overlay(Capsule().strokeBorder(.white.opacity(0.2), lineWidth: 1))
                    }
                    .buttonStyle(PressableCard())
                    deskGlyphButton("pin.fill", tint: target.pinned ? Sig.accent : Sig.muted, action: onPin)
                    deskGlyphButton("xmark", tint: Sig.muted, action: onDismiss)
                    Spacer()
                }
            }
        }
        .padding(15)
        .signalCard(waiting ? Sig.s2 : Sig.s1, radius: 20)
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .strokeBorder(waiting ? Sig.accent.opacity(pulse ? 0.65 : 0.30) : .clear, lineWidth: 1.5)
                .animation(reduceMotion ? nil : .easeInOut(duration: 1.3).repeatForever(autoreverses: true), value: pulse)
        )
        .shadow(color: waiting ? Sig.accent.opacity(pulse ? 0.28 : 0.12) : .clear, radius: 18, y: 8)
        .animation(reduceMotion ? nil : .easeInOut(duration: 1.3).repeatForever(autoreverses: true), value: pulse)
        .opacity(target.stale ? 0.72 : 1)
    }

    private var stateChip: some View {
        HStack(spacing: 5) {
            Image(systemName: stateGlyph).font(.system(size: 10, weight: .black))
            Text(stateLabel).font(.system(size: 10, weight: .heavy)).tracking(0.8)
        }
        .foregroundStyle(stateColor)
        .padding(.horizontal, 9).padding(.vertical, 6)
        .background(stateColor.opacity(0.14), in: Capsule())
        .overlay(Capsule().strokeBorder(stateColor.opacity(0.30), lineWidth: 1))
    }

    private func deskGlyphButton(_ system: String, tint: Color, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: system).font(.system(size: 14, weight: .bold)).foregroundStyle(tint)
                .frame(width: 40, height: 40).signalCard(Sig.s3, radius: 12, elevated: false)
        }
        .buttonStyle(PressableCard())
    }
}

// MARK: - Dictate to your desktop (HSM-15-01 — the flagship mesh surface)

/// The paired desktop peer, persisted across launches. The flagship home reads this to name the
/// "Dictate to {your desktop}" tile and to know whether to invite pairing. Seedable via the
/// `HS_DESKTOP_*` env (a real-metal LAN trace) so a device run points at a live server with no taps.
@MainActor final class DictatePeerStore: ObservableObject {
    static let shared = DictatePeerStore()

    // UserDefaults-backed so pairing survives launches; @Published so the home tile + sheet react.
    @Published var host: String { didSet { defaults.set(host, forKey: "hs.peer.host") } }
    @Published var portText: String { didSet { defaults.set(portText, forKey: "hs.peer.port") } }
    @Published var token: String { didSet { defaults.set(token, forKey: "hs.peer.token") } }
    @Published var name: String { didSet { defaults.set(name, forKey: "hs.peer.name") } }
    private let defaults = UserDefaults.standard

    private init() {
        let env = ProcessInfo.processInfo.environment
        host = defaults.string(forKey: "hs.peer.host") ?? ""
        portText = defaults.string(forKey: "hs.peer.port") ?? "8000"
        token = defaults.string(forKey: "hs.peer.token") ?? ""
        name = defaults.string(forKey: "hs.peer.name") ?? ""
        if host.isEmpty, let h = env["HS_DESKTOP_HOST"], !h.isEmpty { host = h }
        if let p = env["HS_DESKTOP_PORT"], !p.isEmpty { portText = p }
        if token.isEmpty, let t = env["HS_DESKTOP_TOKEN"], !t.isEmpty { token = t }
        if name.isEmpty, let n = env["HS_DESKTOP_NAME"], !n.isEmpty { name = n }
    }

    /// True once a host has been entered — the tile then names the Mac; otherwise it invites pairing.
    var isPaired: Bool { !host.trimmingCharacters(in: .whitespaces).isEmpty }

    /// The Mac's display name: a user-given name, else the host, else a sensible default.
    var displayName: String {
        let n = name.trimmingCharacters(in: .whitespaces)
        if !n.isEmpty { return n }
        let h = host.trimmingCharacters(in: .whitespaces)
        return h.isEmpty ? "your desktop" : h
    }

    var peer: DesktopPeer? {
        guard let port = Int(portText.trimmingCharacters(in: .whitespaces)), port > 0 else { return nil }
        let (scheme, h) = PeerAddress.split(host)
        guard !h.isEmpty else { return nil }
        return DesktopPeer(host: h, port: port, token: token.isEmpty ? nil : token, scheme: scheme)
    }

    func client() -> HTTPDesktopClient? {
        guard let peer, let config = HTTPDesktopClient.Config(peer: peer) else { return nil }
        return HTTPDesktopClient(config: config)
    }

    /// Persist a discovered computer as the paired peer (HSM-15-10). Host/port come from
    /// Bonjour resolution — no IP typing — and only the token (when required) is entered.
    func adopt(name: String, host: String, port: Int, token: String? = nil) {
        self.name = name
        self.host = host
        self.portText = String(port)
        if let token { self.token = token }
    }

    /// Forget the paired computer (HSM-15-10) — every mesh feature reads this one peer, so a
    /// clean forget returns the whole app to the "no computer yet" state. The token is cleared
    /// first (a credential, never left behind).
    func forget() {
        token = ""
        host = ""
        name = ""
        portText = "8000"
    }
}

/// The dictation session: on-device WhisperKit hears you, each finalized utterance is delivered to
/// the paired Mac via `POST /api/dictation/remote` with `target_mode: focused` — the desktop runs it
/// through the full pipeline and free-types it into whatever app is focused. The transcription is
/// LOCAL; only the finished words cross the LAN. An unreachable Mac is a rendered state, never an error.
@MainActor final class DictateModel: ObservableObject {
    /// Reachability of the paired Mac — a first-class state, not an error wall.
    enum Reach: Equatable { case unknown, reachable, asleep, unpaired }
    /// One delivered line in the read-back: the words + whether the desktop confirmed delivery.
    struct Line: Identifiable, Equatable { let id = UUID(); let text: String; var delivered: Bool }

    @Published var listening = false
    @Published var handsFree = false        // hands-free keeps the mic open between utterances
    @Published var transcribing = false
    @Published var level: Float = 0          // live mic amplitude — drives the reactive waveform
    @Published var partial = ""              // the words still being heard
    @Published var lines: [Line] = []        // the finalized read-back (newest last)
    @Published var reach: Reach = .unknown
    @Published var lastDelivered = false     // the quiet confirmation tick
    // HSM-18-01 — the dictation-pipeline contract, surfaced:
    @Published var readiness: DictationReadiness?   // the hub's own verdict for the strip
    @Published var pending: DictationDryRun?        // the armed receipt awaiting Send
    @Published var previewing = false               // dry-run in flight
    // HSM-18-05 — the source-cited pre-briefing nudges + the armed grounding:
    @Published var nudges: [ActivityNudge] = []
    @Published var groundedNudge: ActivityNudge?    // "Dictate with this" parked this record

    /// Opt-in preview: release arms a receipt instead of typing (off = the historical
    /// direct flow — preview is never the default story). Persisted across launches.
    var previewMode: Bool {
        get { UserDefaults.standard.bool(forKey: "hs.dictate.preview") }
        set { objectWillChange.send(); UserDefaults.standard.set(newValue, forKey: "hs.dictate.preview") }
    }

    private let peers = DictatePeerStore.shared
    private let capture = AudioCaptureService()
    private let sink = ChunkSink()
    private let meter = LevelMeter()
    private var levelTicker: Task<Void, Never>?

    // HSM-21-01: the one grammar — on-device hearing, the words cross the LAN to the
    // named Mac. A mixed posture, from the Contracts EgressScope.
    var egressScope: EgressScope { .mixed(peers.displayName) }
    var isPaired: Bool { peers.isPaired }
    var macName: String { peers.displayName }

    /// Probe the Mac so the surface opens honest. Never throws — maps to a rendered Reach.
    /// A reachable hub also yields the dictation readiness snapshot for the strip
    /// (`GET /api/dictation/readiness`, HSM-18-01) — absence renders as no strip, never an error.
    func probe() async {
        guard peers.isPaired else { reach = .unpaired; return }
        guard let client = peers.client() else { reach = .asleep; return }
        let c = await client.handshake()
        reach = c.reachable ? .reachable : .asleep
        readiness = c.reachable ? (try? await client.dictationReadiness()) : nil
        // HSM-18-05 — the source-cited nudges ride the same probe; absence is quiet.
        nudges = c.reachable ? ((try? await client.activityNudges(limit: 3)) ?? []) : []
    }

    /// HSM-18-05 — park the nudge's record on the hub (one-shot, recency-bounded):
    /// the NEXT dictation grounds in it, spoken here or at the desk. The chip shows
    /// what's armed; delivery clears it (the hub consumed the pin).
    func dictateWith(_ nudge: ActivityNudge) async {
        guard let client = peers.client() else { reach = .asleep; return }
        guard let recordId = nudge.citations.first?.recordId else { return }
        do { try await client.selectNudge(recordId: recordId); groundedNudge = nudge }
        catch { reach = .asleep }
    }

    func dismissNudge(_ nudge: ActivityNudge) async {
        nudges.removeAll { $0.key == nudge.key }
        if groundedNudge?.key == nudge.key { groundedNudge = nil }
        guard let client = peers.client() else { return }
        try? await client.dismissNudge(id: nudge.key)
    }

    /// Push-to-talk down / hands-free arm: open the mic and start sampling the level.
    func startListening() async {
        guard !listening else { return }
        guard await CaptureModel.requestMic() else { reach = .asleep; return }
        sink.reset(); meter.reset(); partial = ""
        do { try capture.start { [sink, meter] chunk in sink.add(chunk); meter.ingest(chunk) }; listening = true }
        catch { listening = false; return }
        // Poll the live mic amplitude (20 Hz) so the waveform reacts the instant sound arrives.
        levelTicker = Task { [weak self] in
            while !Task.isCancelled, self?.listening == true {
                await MainActor.run { self?.level = self?.meter.level ?? 0 }
                try? await Task.sleep(nanoseconds: 50_000_000)
            }
            await MainActor.run { self?.level = 0 }
        }
    }

    /// Push-to-talk up / hands-free stop: close the mic, transcribe the clip ON-DEVICE, deliver it.
    func stopAndDeliver() async {
        guard listening else { return }
        try? capture.stop()
        listening = false
        levelTicker?.cancel(); levelTicker = nil; level = 0
        transcribing = true; defer { transcribing = false }
        let said: String
        do {
            let segs = try await WhisperKitTranscriber(chunks: sink.drain(), model: "base").transcribe()
            said = segs.map(\.text).joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        } catch { return }
        guard !said.isEmpty else { return }
        // HSM-18-01 — preview mode arms a receipt instead of typing: the dry-run shows
        // exactly what would land BEFORE a keystroke leaves the iPad.
        if previewMode { await preview(said) } else { await deliver(said) }
    }

    /// Run the utterance through the hub's dry-run and arm the receipt. If the hub can't
    /// preview (unreachable mid-flight), fall back to the exact non-preview lane — the
    /// words are never lost, and that lane already renders failure honestly (an
    /// un-ticked line + Reach.asleep).
    func preview(_ text: String) async {
        guard let client = peers.client() else { reach = .asleep; return }
        previewing = true; defer { previewing = false }
        do {
            let receipt = try await client.dictationDryRun(utterance: text)
            if receipt.finalText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                // An empty receipt is a broken receipt — never arm (or send) nothing.
                await deliver(text)
            } else {
                pending = receipt
            }
        } catch { await deliver(text) }
    }

    /// Commit the armed receipt: the hub types it VERBATIM (`raw: true`) — what
    /// previewed is exactly what lands, no second trip through the pipeline.
    func sendPending() async {
        guard let receipt = pending else { return }
        pending = nil
        await deliver(receipt.finalText, raw: true)
    }

    func discardPending() { pending = nil }

    /// Deliver a finalized utterance to the focused Mac app. Appends to the read-back optimistically,
    /// then flips its tick from the desktop's `RemoteDictationResult.delivered`. Unreachable → the
    /// line stays (un-ticked) and Reach goes `.asleep`; never a thrown error at the user.
    func deliver(_ text: String, raw: Bool = false) async {
        var line = Line(text: text, delivered: false)
        lines.append(line)
        if lines.count > 6 { lines.removeFirst(lines.count - 6) }
        guard let client = peers.client() else { reach = .asleep; return }
        do {
            let result = try await client.sendRemoteDictation(text: text, target: .focused, raw: raw)
            line.delivered = result.delivered
            if let i = lines.firstIndex(where: { $0.id == line.id }) { lines[i].delivered = result.delivered }
            lastDelivered = result.delivered
            reach = .reachable
            // The hub consumed the one-shot pin with this dictation (HSM-18-05).
            groundedNudge = nil
        } catch {
            reach = .asleep
        }
    }

    #if targetEnvironment(simulator)
    /// Simulator-only: stage a live-looking session for the design screenshot — connected, an active
    /// mic level (so the waveform leaps), a trailing partial, and a read-back with one line in flight.
    func seedDemo(preview: Bool = false) {
        reach = .reachable
        level = 0.72
        partial = "and bump the retry budget to five attempts"
        lines = [
            Line(text: "Refactor the dictation runner so the focused-app path doesn't gate on a coder session.", delivered: true),
            Line(text: "Add a regression test for the asleep-peer first-class state.", delivered: true),
            Line(text: "Wire the egress badge to the live peer name.", delivered: false),
        ]
        // HSM-18-01 — the readiness strip + (optionally) an armed receipt for the shot.
        readiness = DictationReadiness(
            ready: true,
            runtime: DictationRuntimeReadiness(status: "available", resolvedBackend: "mlx"))
        // HSM-18-05 — two source-cited nudges: a record nudge (armed) + a window nudge.
        nudges = [
            ActivityNudge(
                key: "record:42", kind: "record",
                title: "You reviewed PR #216 minutes ago",
                body: "The dictation teleprompter — readiness strip, Preview first receipt, raw verbatim delivery.",
                score: 0.9,
                citations: [NudgeCitation(recordId: 42, sourceBrowser: "safari", sourceProfile: "default",
                                          domain: "github.com", title: "PR #216 · HoldSpeak",
                                          url: "https://github.com/karolswdev/HoldSpeak/pull/216", visitCount: 4)]),
            ActivityNudge(
                key: "window:2026-07-03T11:00:00", kind: "window",
                title: "9 pages touched since your last dictation",
                body: "Mostly github.com and the HoldSpeak docs.",
                score: 0.6, citations: [], windowRecordCount: 9),
        ]
        groundedNudge = nudges.first
        if preview {
            UserDefaults.standard.set(true, forKey: "hs.dictate.preview")
            level = 0; partial = ""
            pending = DictationDryRun(
                finalText: "Refactor the dictation runner so the focused-app path doesn't gate on a coder session.",
                totalElapsedMs: 412, blocksCount: 2)
        }
    }
    #endif
}

/// The flagship "Dictate to your desktop" surface (HSM-15-01): the iPad is the best mic in the house,
/// your desktop has every app you work in. Pick it up, talk, and the words land in whatever is focused —
/// transcribed on-device, typed through the desktop's full dictation pipeline. No prose; chips + symbols.
struct DictateView: View {
    @StateObject private var model = DictateModel()
    @State private var appeared = false
    @State private var ring = false
    @State private var pairing = false
    @State private var showCommands = false   // HSM-18-02 — the macro authoring board
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    // HSM-20-04 — on iPhone the dictation surface promotes to a bottom-edge HOLD BAR that reflows,
    // on press, into a bottom-up teleprompter (the vision's signature dictation beat).
    @Environment(\.horizontalSizeClass) private var hSizeClass
    private var isLane: Bool { hSizeClass == .compact }

    var body: some View {
        ZStack {
            background
            if isLane { laneBody } else { regularBody }
        }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .sheet(isPresented: $pairing) { PairMacSheet() }
        .navigationDestination(isPresented: $showCommands) { CommandsBoard() }
        .onAppear {
            withAnimation(reduceMotion ? nil : .spring(response: 0.6, dampingFraction: 0.85)) { appeared = true }
            if !reduceMotion { ring = true }
            #if targetEnvironment(simulator)
            if let d = ProcessInfo.processInfo.environment["HS_DEMO_DICTATE"], d == "1" || d == "preview" {
                model.seedDemo(preview: d == "preview"); return
            }
            #endif
            Task { await model.probe() }
        }
    }

    // The iPad / wide layout — the full scrolling stage with the centered push-to-talk hero.
    private var regularBody: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                header
                reachChip
                readinessStrip
                nudgeCards
                waveformHero
                talkControls
                if let receipt = model.pending { receiptCard(receipt) }
                readBack
            }
            .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.82), value: model.pending)
    }

    // MARK: - The iPhone hold-bar teleprompter (HSM-20-04)

    /// The lane layout: the read-back scrolls above, a persistent accent HOLD BAR lives on the
    /// bottom edge (thumb zone), and pressing it reflows a bottom-up teleprompter UP from the bar —
    /// no dim toward the bar (the bar's elevation carries focus, a dim would be a scrim).
    private var laneBody: some View {
        ZStack(alignment: .bottom) {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    header
                    reachChip
                    readinessStrip
                    nudgeCards
                    readBack
                }
                .padding(.horizontal, 18).padding(.top, 8).padding(.bottom, 180)
                .frame(maxWidth: .infinity)
            }
            if let receipt = model.pending {
                receiptCard(receipt)
                    .padding(.horizontal, 14).padding(.bottom, 92)   // sits just above the hold bar
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            } else if model.listening || !model.partial.isEmpty {
                teleprompter.transition(.move(edge: .bottom).combined(with: .opacity))
            }
            holdBar
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.82), value: model.listening)
        .animation(.spring(response: 0.4, dampingFraction: 0.82), value: model.pending)
    }

    /// The bottom-up teleprompter that rises from the hold bar while you talk: a destination + egress
    /// pill at the top, the "→ Cursor" target line full weight, and the live "you said" partial
    /// largest and nearest the thumb. Reads bottom-to-top so the freshest words sit by your hand.
    private var teleprompter: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "arrow.right").font(.system(size: 11, weight: .black))
                Text("→ \(model.macName)").font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.accent)
                Spacer(minLength: 8)
                egressBadge
            }
            Text(model.partial.isEmpty ? "Listening…" : model.partial)
                .font(.system(size: 23, weight: .bold)).foregroundStyle(model.partial.isEmpty ? Sig.faint : Sig.text)
                .frame(maxWidth: .infinity, alignment: .leading)
                .animation(.easeOut(duration: 0.18), value: model.partial)
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1.opacity(0.96), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(Sig.accent.opacity(0.35), lineWidth: 1.5))
        .shadow(color: .black.opacity(0.45), radius: 22, y: -6)
        .padding(.horizontal, 14).padding(.bottom, 92)   // sits just above the hold bar
    }

    /// The persistent bottom-edge hold bar: an accent-gradient capsule the thumb owns. Press-and-hold
    /// opens the mic (reusing the model's listen/deliver), release commits with a success haptic.
    private var holdBar: some View {
        let armed = model.isPaired
        return HStack(spacing: 12) {
            Image(systemName: model.listening ? "waveform" : "mic.fill").font(.system(size: 20, weight: .bold))
            Text(model.listening ? "Release to send" : (armed ? "Hold to talk" : "Pair your desktop to start"))
                .font(.system(size: 17, weight: .heavy))
            if model.listening { Spacer(minLength: 4); MicWaveform(level: CGFloat(model.level), active: true, bars: 16, height: 22).frame(width: 90, height: 22) }
        }
        .foregroundStyle(armed ? .black : Sig.muted)
        .frame(maxWidth: .infinity).padding(.vertical, 18)
        .background(armed ? AnyShapeStyle(Sig.accentGradient) : AnyShapeStyle(Sig.s2),
                    in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(armed ? Color.white.opacity(0.22) : Sig.line, lineWidth: 1))
        .scaleEffect(model.listening ? 0.98 : 1)
        .shadow(color: model.listening ? Sig.accent.opacity(0.45) : .black.opacity(0.3), radius: model.listening ? 24 : 12, y: 6)
        .padding(.horizontal, 14).padding(.bottom, 10)
        .contentShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    guard armed, !model.handsFree, !model.listening else { return }
                    tactile(.medium); Task { await model.startListening() }
                }
                .onEnded { _ in
                    guard !model.handsFree, model.listening else { return }
                    tactile(.heavy); Task { await model.stopAndDeliver() }   // release commits
                }
        )
        .simultaneousGesture(TapGesture().onEnded { if !armed { tactile(.medium); pairing = true } })
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: model.listening)
    }

    private var background: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(model.listening ? 0.22 : 0.14)).frame(width: 460)
                .blur(radius: 140).offset(x: 120, y: -300).ignoresSafeArea()
                .animation(.easeInOut(duration: 0.6), value: model.listening)
            Circle().fill(Sig.local.opacity(0.10)).frame(width: 360)
                .blur(radius: 140).offset(x: -180, y: -160).ignoresSafeArea()
        }
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 9) {
                Button { tactile(); dismiss() } label: {
                    HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Home") }
                        .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                }
                .buttonStyle(.plain)
                egressBadge
                Text("Dictate").font(.system(size: 38, weight: .heavy)).foregroundStyle(Sig.text)
                    .shadow(color: .black.opacity(0.3), radius: 8, y: 3)
                HStack(spacing: 7) {
                    Image(systemName: "arrow.right").font(.system(size: 12, weight: .black)).foregroundStyle(Sig.faint)
                    Text(model.macName).font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.accent)
                }
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 10) {
                GlyphChip(system: "mic.fill", gradient: Sig.accentGradient, size: 50)
                // HSM-18-02 — the macro authoring board rides the dictate surface.
                Button { tactile(.light); showCommands = true } label: {
                    HStack(spacing: 5) {
                        Image(systemName: "command").font(.system(size: 11, weight: .bold))
                        Text("Commands").font(.system(size: 12, weight: .heavy))
                    }
                    .foregroundStyle(Sig.muted)
                    .padding(.horizontal, 11).padding(.vertical, 7)
                    .background(Sig.s2, in: Capsule())
                    .overlay(Capsule().strokeBorder(Sig.line, lineWidth: 1))
                }
                .buttonStyle(PressableCard())
            }
        }
        .padding(.top, 8)
        .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 10)
    }

    /// The egress reality, one badge (POSITIONING canon; HSM-21-01: the words + symbol +
    /// honest tint come from the Contracts EgressScope — a mixed posture never dresses local).
    private var egressBadge: some View {
        let scope = model.egressScope
        let tint: Color = scope.leavesDevice ? Sig.warn : Sig.local
        return HStack(spacing: 6) {
            Image(systemName: scope.symbolName).font(.system(size: 9, weight: .black))
            Text(scope.label.uppercased()).font(.system(size: 10, weight: .heavy)).tracking(1.0)
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 10).padding(.vertical, 5)
        .background(tint.opacity(0.12), in: Capsule())
        .overlay(Capsule().strokeBorder(tint.opacity(0.25), lineWidth: 1))
    }

    /// First-class reachability: a tight chip, never an error wall. Unpaired invites pairing.
    @ViewBuilder private var reachChip: some View {
        switch model.reach {
        case .unpaired:
            Button { tactile(.medium); pairing = true } label: {
                statusChip("link.badge.plus", "Pair your desktop to start", Sig.accent, filled: true)
            }
            .buttonStyle(PressableCard())
        case .asleep:
            Button { tactile(); Task { await model.probe() } } label: {
                statusChip("moon.zzz.fill", "Desktop asleep · not reachable — tap to retry", Sig.warn)
            }
            .buttonStyle(PressableCard())
        case .reachable:
            statusChip("checkmark.circle.fill", "Connected · words land on \(model.macName)", Sig.ok)
        case .unknown:
            statusChip("dot.radiowaves.left.and.right", "Reaching \(model.macName)…", Sig.muted)
        }
    }

    private func statusChip(_ glyph: String, _ text: String, _ color: Color, filled: Bool = false) -> some View {
        HStack(spacing: 8) {
            Image(systemName: glyph).font(.system(size: 13, weight: .bold))
            Text(text).font(.system(size: 13, weight: .heavy))
            Spacer(minLength: 0)
            if filled { Image(systemName: "chevron.right").font(.system(size: 12, weight: .black)).opacity(0.7) }
        }
        .foregroundStyle(filled ? .black : color)
        .padding(.horizontal, 14).padding(.vertical, 11)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(filled ? AnyShapeStyle(Sig.accentGradient) : AnyShapeStyle(color.opacity(0.12)),
                    in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous)
            .strokeBorder(filled ? Color.white.opacity(0.2) : color.opacity(0.28), lineWidth: 1))
        .opacity(appeared ? 1 : 0)
    }

    /// HSM-18-01 — the hub's own dictation-pipeline verdict as chips. No snapshot = no strip.
    @ViewBuilder private var readinessStrip: some View {
        if model.reach == .reachable, let r = model.readiness {
            HStack(spacing: 8) {
                miniChip(r.ready == true ? "checkmark.seal.fill" : "xmark.seal.fill",
                         r.ready == true ? "Pipeline ready" : "Pipeline not ready",
                         r.ready == true ? Sig.ok : Sig.warn)
                if let backend = r.runtime?.resolvedBackend ?? r.runtime?.requestedBackend {
                    miniChip("cpu", backend, Sig.muted)
                }
                if let t = r.target?.displayLabel { miniChip("arrow.right", t, Sig.muted) }
                Spacer(minLength: 0)
            }
            .opacity(appeared ? 1 : 0)
        }
    }

    private func miniChip(_ glyph: String, _ text: String, _ color: Color) -> some View {
        HStack(spacing: 5) {
            Image(systemName: glyph).font(.system(size: 10, weight: .black))
            Text(text).font(.system(size: 11, weight: .heavy))
        }
        .foregroundStyle(color)
        .padding(.horizontal, 9).padding(.vertical, 5)
        .background(color.opacity(0.1), in: Capsule())
        .overlay(Capsule().strokeBorder(color.opacity(0.22), lineWidth: 1))
    }

    /// HSM-18-05 — the source-cited pre-briefing nudges. Each card names its sources;
    /// "Dictate with this" arms the next utterance with the record. Quiet when empty.
    @ViewBuilder private var nudgeCards: some View {
        if model.reach == .reachable, !model.nudges.isEmpty {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(model.nudges, id: \.key) { nudge in nudgeCard(nudge) }
            }
            .opacity(appeared ? 1 : 0)
        }
    }

    private func nudgeCard(_ nudge: ActivityNudge) -> some View {
        let grounded = model.groundedNudge?.key == nudge.key
        return VStack(alignment: .leading, spacing: 9) {
            Text(nudge.title).font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.text)
            if !nudge.body.isEmpty {
                Text(nudge.body).font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.muted)
                    .lineLimit(2).fixedSize(horizontal: false, vertical: true)
            }
            if !nudge.citations.isEmpty {
                HStack(spacing: 6) {
                    ForEach(Array(nudge.citations.prefix(3).enumerated()), id: \.offset) { _, c in
                        miniChip("link", c.title ?? c.domain, Sig.faint)
                    }
                    Spacer(minLength: 0)
                }
            }
            HStack(spacing: 10) {
                Button { tactile(.light); Task { await model.dismissNudge(nudge) } } label: {
                    Text("Dismiss").font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.faint)
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .background(Sig.s2, in: Capsule())
                        .overlay(Capsule().strokeBorder(Sig.line, lineWidth: 1))
                }
                .buttonStyle(PressableCard())
                if nudge.citations.first != nil {
                    Button { tactile(.medium); Task { await model.dictateWith(nudge) } } label: {
                        HStack(spacing: 6) {
                            Image(systemName: grounded ? "checkmark.circle.fill" : "mic.badge.plus")
                                .font(.system(size: 12, weight: .bold))
                            Text(grounded ? "Armed" : "Dictate with this")
                                .font(.system(size: 13, weight: .heavy))
                        }
                        .foregroundStyle(grounded ? .black : Sig.accent)
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .background(grounded ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.accent.opacity(0.12)), in: Capsule())
                        .overlay(Capsule().strokeBorder(Sig.accent.opacity(grounded ? 0 : 0.3), lineWidth: 1))
                    }
                    .buttonStyle(PressableCard())
                }
                Spacer(minLength: 0)
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
            .strokeBorder(grounded ? Sig.accent.opacity(0.5) : Sig.line, lineWidth: 1))
    }

    /// HSM-18-01 — the armed receipt: exactly what will type, shown before it types.
    /// Send commits it verbatim (`raw`); Discard drops it. The receipt IS the contract.
    private func receiptCard(_ receipt: DictationDryRun) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 7) {
                Image(systemName: "arrow.right.circle.fill")
                    .font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.local)
                Text(receipt.target?.displayLabel.map { "Types into \($0)" } ?? "Types into the focused app")
                    .font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.muted)
                Spacer(minLength: 8)
                if let ms = receipt.totalElapsedMs { miniChip("bolt.fill", "\(Int(ms)) ms", Sig.faint) }
                if let b = receipt.blocksCount, b > 0 { miniChip("square.stack.3d.up.fill", "\(b)", Sig.faint) }
            }
            Text(receipt.finalText)
                .font(.system(size: 19, weight: .semibold)).foregroundStyle(Sig.text)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
            if let warnings = receipt.warnings, !warnings.isEmpty {
                miniChip("exclamationmark.triangle.fill",
                         "\(warnings.count) warning\(warnings.count == 1 ? "" : "s")", Sig.warn)
            }
            HStack(spacing: 10) {
                Button {
                    tactile(.light); model.discardPending()
                } label: {
                    Text("Discard").font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.muted)
                        .frame(maxWidth: .infinity).padding(.vertical, 13)
                        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
                }
                .buttonStyle(PressableCard())
                Button {
                    tactile(.heavy); Task { await model.sendPending() }
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "paperplane.fill").font(.system(size: 14, weight: .bold))
                        Text("Send to \(model.macName)").font(.system(size: 15, weight: .heavy))
                    }
                    .foregroundStyle(.black)
                    .frame(maxWidth: .infinity).padding(.vertical, 13)
                    .background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Color.white.opacity(0.2), lineWidth: 1))
                }
                .buttonStyle(PressableCard())
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1.opacity(0.97), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(Sig.local.opacity(0.45), lineWidth: 1.5))
        .shadow(color: .black.opacity(0.4), radius: 20, y: -4)
    }

    /// The hero: the reactive waveform that leaps with your voice, on a deep Signal stage. The
    /// trailing partial caption shows what's being heard right now.
    private var waveformHero: some View {
        VStack(spacing: 16) {
            MicWaveform(level: CGFloat(model.level), active: model.listening || model.level > 0.001,
                        bars: 40, height: 64)
                .frame(height: 64).frame(maxWidth: .infinity)
            Text(model.partial.isEmpty
                 ? (model.listening ? "Listening…" : (model.transcribing ? "Transcribing on-device…" : "Hold to talk"))
                 : model.partial)
                .font(.system(size: 16, weight: model.partial.isEmpty ? .heavy : .semibold))
                .foregroundStyle(model.partial.isEmpty ? Sig.faint : Sig.text)
                .multilineTextAlignment(.center).lineLimit(2)
                .frame(maxWidth: .infinity, minHeight: 24)
                .animation(.easeOut(duration: 0.2), value: model.partial)
        }
        .padding(.vertical, 26).padding(.horizontal, 18)
        .frame(maxWidth: .infinity)
        .signalCard(Sig.s1, radius: 24)
        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous)
            .strokeBorder(model.listening ? Sig.accent.opacity(ring ? 0.55 : 0.25) : Sig.line, lineWidth: 1.5)
            .animation(reduceMotion ? nil : .easeInOut(duration: 1.1).repeatForever(autoreverses: true), value: ring))
        .shadow(color: model.listening ? Sig.accent.opacity(0.3) : .clear, radius: 22, y: 10)
        .opacity(appeared ? 1 : 0).scaleEffect(appeared ? 1 : 0.97)
    }

    /// The two ways to talk: a big push-to-talk (press-and-hold) and a hands-free toggle that keeps
    /// the mic open. Disabled until the Mac is paired (the reach chip then leads to pairing).
    private var talkControls: some View {
        VStack(spacing: 12) {
            // Push-to-talk: press down to open the mic, release to transcribe + deliver.
            ZStack {
                Circle().fill(model.listening ? AnyShapeStyle(Sig.accentGradient) : AnyShapeStyle(Sig.s2))
                    .frame(width: 110, height: 110)
                    .overlay(Circle().strokeBorder(model.listening ? Color.white.opacity(0.25) : Sig.line, lineWidth: 1.5))
                    .shadow(color: model.listening ? Sig.accent.opacity(0.5) : .black.opacity(0.3),
                            radius: model.listening ? 26 : 12, y: 8)
                    .scaleEffect(model.listening ? 1.06 : 1)
                if model.listening {
                    Circle().stroke(Sig.accent.opacity(0.5), lineWidth: 2).frame(width: 110, height: 110)
                        .scaleEffect(ring ? 1.35 : 1).opacity(ring ? 0 : 0.8)
                        .animation(reduceMotion ? nil : .easeOut(duration: 1.0).repeatForever(autoreverses: false), value: ring)
                }
                Image(systemName: model.listening ? "waveform" : "mic.fill")
                    .font(.system(size: 38, weight: .bold))
                    .foregroundStyle(model.listening ? .black : Sig.accent)
            }
            .contentShape(Circle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        guard model.isPaired, !model.handsFree, !model.listening else { return }
                        tactile(.medium); Task { await model.startListening() }
                    }
                    .onEnded { _ in
                        guard !model.handsFree, model.listening else { return }
                        tactile(.light); Task { await model.stopAndDeliver() }
                    }
            )
            .animation(.spring(response: 0.32, dampingFraction: 0.7), value: model.listening)
            .disabled(!model.isPaired)
            .opacity(model.isPaired ? 1 : 0.5)

            Text(model.handsFree ? "Hands-free · tap to stop" : "Press and hold to talk")
                .font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.faint)

            // Hands-free keeps the mic open between utterances; Preview first (HSM-18-01)
            // arms a receipt on release instead of typing straight through.
            HStack(spacing: 10) {
                Button {
                    guard model.isPaired else { tactile(.medium); pairing = true; return }
                    tactile(.medium)
                    model.handsFree.toggle()
                    if model.handsFree { Task { await model.startListening() } }
                    else if model.listening { Task { await model.stopAndDeliver() } }
                } label: {
                    HStack(spacing: 9) {
                        Image(systemName: model.handsFree ? "infinity.circle.fill" : "infinity")
                            .font(.system(size: 16, weight: .bold))
                        Text(model.handsFree ? "Hands-free ON" : "Hands-free")
                            .font(.system(size: 15, weight: .heavy))
                    }
                    .foregroundStyle(model.handsFree ? .black : Sig.muted)
                    .padding(.horizontal, 18).padding(.vertical, 11)
                    .background(model.handsFree ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.s2), in: Capsule())
                    .overlay(Capsule().strokeBorder(model.handsFree ? Color.clear : Sig.line, lineWidth: 1))
                }
                .buttonStyle(PressableCard())

                Button {
                    tactile(.medium)
                    model.previewMode.toggle()
                } label: {
                    HStack(spacing: 9) {
                        Image(systemName: model.previewMode ? "doc.text.magnifyingglass" : "doc.text")
                            .font(.system(size: 16, weight: .bold))
                        Text(model.previewMode ? "Preview first ON" : "Preview first")
                            .font(.system(size: 15, weight: .heavy))
                    }
                    .foregroundStyle(model.previewMode ? .black : Sig.muted)
                    .padding(.horizontal, 18).padding(.vertical, 11)
                    .background(model.previewMode ? AnyShapeStyle(Sig.local) : AnyShapeStyle(Sig.s2), in: Capsule())
                    .overlay(Capsule().strokeBorder(model.previewMode ? Color.clear : Sig.line, lineWidth: 1))
                }
                .buttonStyle(PressableCard())
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .opacity(appeared ? 1 : 0)
    }

    /// The live read-back: the finalized utterances that have been sent, each with a quiet delivery
    /// tick once the Mac confirms it. No prose — the lines are the words, the tick is the receipt.
    @ViewBuilder private var readBack: some View {
        if !model.lines.isEmpty {
            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 7) {
                    Image(systemName: "text.line.first.and.arrowtriangle.forward")
                        .font(.system(size: 11, weight: .black))
                    Text("SENT TO \(model.macName.uppercased())").font(.system(size: 11, weight: .heavy)).tracking(1.4)
                    Spacer()
                }
                .foregroundStyle(Sig.faint)
                ForEach(model.lines) { line in
                    HStack(alignment: .top, spacing: 11) {
                        Image(systemName: line.delivered ? "checkmark.circle.fill" : "arrow.up.circle")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundStyle(line.delivered ? Sig.ok : Sig.muted)
                        Text(line.text).font(.system(size: 15, weight: .medium)).foregroundStyle(Sig.text)
                            .fixedSize(horizontal: false, vertical: true)
                        Spacer(minLength: 0)
                    }
                    .padding(13)
                    .background(Sig.s2, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
                    .transition(.asymmetric(insertion: .move(edge: .bottom).combined(with: .opacity), removal: .opacity))
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .animation(.spring(response: 0.45, dampingFraction: 0.82), value: model.lines)
            .opacity(appeared ? 1 : 0)
        }
    }
}

// MARK: - The Connect surface ("Your Desktop" — discovery-first pairing, HSM-15-10)

/// One computer the iPad found on the LAN by Bonjour (`_holdspeak._tcp`). Identified by the
/// advertised name; host/port arrive on resolve so tap-to-connect needs no IP typing. `requiresToken`
/// is read from the service's TXT record (and confirmed by `GET /api/mesh/info` on connect).
struct DiscoveredComputer: Identifiable, Equatable {
    let id: String            // a stable identity for the discovered endpoint (the Bonjour name)
    var name: String          // the desktop's advertised name ("Karol's Mac")
    var host: String?         // resolved host (nil until resolved)
    var port: Int?            // resolved port
    var requiresToken: Bool   // TXT `requiresToken` — does pairing need the desktop's token
    var reachable: Bool       // last-known reach (true while advertising; refined by /api/mesh/info)

    var resolved: Bool { host != nil && port != nil }
}

/// Browses the LAN for HoldSpeak desktops via Bonjour (`NWBrowser` over `_holdspeak._tcp`) and
/// resolves each to host + port (`NWConnection`). The "discovery verb": find the Mac by name, never
/// type its IP. Fail-soft — a Simulator with no LAN service simply shows an empty list (or the
/// `HS_DEMO_CONNECT` seed), never an error wall. Requires NSBonjourServices in Info.plist.
@MainActor final class MeshBrowser: ObservableObject {
    @Published var computers: [DiscoveredComputer] = []
    @Published var browsing = false

    private var browser: NWBrowser?
    private var resolvers: [String: NWConnection] = [:]

    /// Begin browsing. Idempotent — a second call while already browsing is a no-op.
    func start() {
        guard browser == nil else { return }
        #if targetEnvironment(simulator)
        // The Simulator can't browse a real LAN service; HS_DEMO_CONNECT seeds the list instead.
        if ProcessInfo.processInfo.environment["HS_DEMO_CONNECT"] == "1" { seedDemo(); return }
        #endif
        let params = NWParameters()
        params.includePeerToPeer = true
        let b = NWBrowser(for: .bonjourWithTXTRecord(type: "_holdspeak._tcp", domain: nil), using: params)
        b.stateUpdateHandler = { [weak self] state in
            Task { @MainActor in
                switch state {
                case .ready, .setup: self?.browsing = true
                case .failed, .cancelled: self?.browsing = false
                default: break
                }
            }
        }
        b.browseResultsChangedHandler = { [weak self] results, _ in
            Task { @MainActor in self?.ingest(results) }
        }
        browser = b
        browsing = true
        b.start(queue: .main)
    }

    func stop() {
        browser?.cancel(); browser = nil
        resolvers.values.forEach { $0.cancel() }; resolvers.removeAll()
        browsing = false
    }

    /// Map the current Bonjour result set into discovered rows, resolving any new ones.
    private func ingest(_ results: Set<NWBrowser.Result>) {
        var next: [DiscoveredComputer] = []
        for result in results {
            guard case let .service(name, _, _, _) = result.endpoint else { continue }
            var requiresToken = false
            if case let .bonjour(txt) = result.metadata, let v = txt["requiresToken"] {
                requiresToken = (v == "1" || v.lowercased() == "true")
            }
            // Preserve an already-resolved host/port across result-set churn.
            let prior = computers.first { $0.id == name }
            next.append(DiscoveredComputer(id: name, name: name, host: prior?.host, port: prior?.port,
                                           requiresToken: requiresToken, reachable: true))
            if prior?.resolved != true { resolve(result.endpoint, name: name) }
        }
        computers = next.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
    }

    /// Resolve a Bonjour endpoint to a concrete host + port via a short-lived NWConnection.
    private func resolve(_ endpoint: NWEndpoint, name: String) {
        guard resolvers[name] == nil else { return }
        let conn = NWConnection(to: endpoint, using: .tcp)
        resolvers[name] = conn
        conn.stateUpdateHandler = { [weak self, weak conn] state in
            guard state == .ready, let conn, let inner = conn.currentPath?.remoteEndpoint else { return }
            if case let .hostPort(host, port) = inner {
                let h = Self.hostString(host)
                Task { @MainActor in
                    self?.apply(name: name, host: h, port: Int(port.rawValue))
                    conn.cancel()
                }
            }
        }
        conn.start(queue: .main)
    }

    private func apply(name: String, host: String, port: Int) {
        guard let i = computers.firstIndex(where: { $0.id == name }) else { return }
        computers[i].host = host
        computers[i].port = port
        resolvers[name]?.cancel(); resolvers[name] = nil
    }

    nonisolated private static func hostString(_ host: NWEndpoint.Host) -> String {
        switch host {
        case .name(let n, _): return n
        case .ipv4(let a): return "\(a)".components(separatedBy: "%").first ?? "\(a)"
        case .ipv6(let a): return "\(a)".components(separatedBy: "%").first ?? "\(a)"
        @unknown default: return "\(host)"
        }
    }

    /// Seed a believable discovered list for the Simulator screenshot (HS_DEMO_CONNECT=1):
    /// two reachable computers (one token-gated) and one asleep/unreachable.
    func seedDemo() {
        browsing = true
        computers = [
            DiscoveredComputer(id: "Karol's Mac", name: "Karol's Mac", host: "192.168.1.13", port: 8000,
                               requiresToken: true, reachable: true),
            DiscoveredComputer(id: "studio-linux", name: "studio-linux", host: "192.168.1.43", port: 8000,
                               requiresToken: false, reachable: true),
            DiscoveredComputer(id: "mac-mini-loft", name: "mac-mini-loft", host: "192.168.1.27", port: 8000,
                               requiresToken: false, reachable: false),
        ]
    }
}

/// The desktop's self-identification from the unauthenticated `GET /api/mesh/info` (name, version,
/// whether a token is required). Confirms a discovered computer's identity on connect.
struct MeshInfo: Decodable, Equatable {
    var name: String?
    var version: String?
    var requiresToken: Bool?
}

/// "Your Desktop" — the first-class, discovery-first place to find and pair with your desktop
/// (HSM-15-10). Browses the LAN by Bonjour, lists computers by name + reach, tap-to-connect (host/port
/// from discovery — no IP typing), a tight token pairing step when required, and a manual fallback.
/// The single paired peer it writes (`DictatePeerStore`) is what dictation / Agent Desk / the Queue
/// HUD all read. The home of the mesh connection.
struct ConnectView: View {
    @StateObject private var browser = MeshBrowser()
    @ObservedObject private var peers = DictatePeerStore.shared
    @State private var appeared = false
    @State private var pairTarget: DiscoveredComputer?     // the computer mid-pairing (token step / confirm)
    @State private var pairToken = ""
    @State private var confirming = false                  // hitting /api/mesh/info on tap
    @State private var manual = false                      // the "Connect manually" sheet
    @State private var reach: DictateModel.Reach = .unknown
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        ZStack {
            background
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    header
                    if peers.isPaired { pairedCard }
                    discoverySection
                    manualRow
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .sheet(item: $pairTarget) { target in
            tokenSheet(for: target)
        }
        .sheet(isPresented: $manual) { PairMacSheet() }
        .onAppear {
            withAnimation(reduceMotion ? nil : .spring(response: 0.6, dampingFraction: 0.85)) { appeared = true }
            browser.start()
            if peers.isPaired { Task { await probePaired() } }
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_DEMO_CONNECT"] == "1" { browser.seedDemo() }
            #endif
        }
        .onDisappear { browser.stop() }
    }

    private var background: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.local.opacity(0.16)).frame(width: 440)
                .blur(radius: 140).offset(x: 150, y: -300).ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(0.08)).frame(width: 360)
                .blur(radius: 140).offset(x: -180, y: -180).ignoresSafeArea()
        }
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 9) {
                Button { tactile(); dismiss() } label: {
                    HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Home") }
                        .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                }
                .buttonStyle(.plain)
                HStack(spacing: 7) {
                    Image(systemName: "dot.radiowaves.left.and.right").font(.system(size: 9, weight: .black))
                    Text("ON YOUR NETWORK").font(.system(size: 10, weight: .heavy)).tracking(1.4)
                }
                .foregroundStyle(Sig.local)
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background(Sig.local.opacity(0.12), in: Capsule())
                .overlay(Capsule().strokeBorder(Sig.local.opacity(0.25), lineWidth: 1))
                Text("Your Desktop").font(.system(size: 36, weight: .heavy)).foregroundStyle(Sig.text)
                    .shadow(color: .black.opacity(0.3), radius: 8, y: 3)
            }
            Spacer()
            GlyphChip(system: "laptopcomputer", gradient: Sig.localGradient, size: 50)
        }
        .padding(.top, 8)
        .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 10)
    }

    // The paired computer: a tight reach chip + forget / re-pair. The one peer the whole mesh reads.
    private var pairedCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 14) {
                GlyphChip(system: "checkmark.seal.fill", gradient: Sig.localGradient, size: 46)
                VStack(alignment: .leading, spacing: 4) {
                    Text(peers.displayName).font(.system(size: 18, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                    Text("\(peers.host):\(peers.portText)").font(.system(size: 12, weight: .semibold).monospaced())
                        .foregroundStyle(Sig.faint)
                }
                Spacer()
                reachChip
            }
            HStack(spacing: 10) {
                Button { tactile(); Task { await probePaired() } } label: {
                    manageButton("arrow.clockwise", "Re-check", Sig.local)
                }.buttonStyle(PressableCard())
                Button { tactile(.medium); withAnimation { peers.forget(); reach = .unknown } } label: {
                    manageButton("trash.fill", "Forget", Sig.bad)
                }.buttonStyle(PressableCard())
            }
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading).signalCard(radius: 20)
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(Sig.local.opacity(0.30), lineWidth: 1))
        .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 10)
    }

    private func manageButton(_ icon: String, _ label: String, _ tint: Color) -> some View {
        HStack(spacing: 7) {
            Image(systemName: icon).font(.system(size: 12, weight: .bold))
            Text(label).font(.system(size: 14, weight: .heavy))
        }
        .foregroundStyle(tint)
        .frame(maxWidth: .infinity).padding(.vertical, 11)
        .background(tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(tint.opacity(0.28), lineWidth: 1))
    }

    @ViewBuilder private var reachChip: some View {
        let (icon, label, color): (String, String, Color) = {
            switch reach {
            case .reachable: return ("checkmark.circle.fill", "Reachable", Sig.ok)
            case .asleep: return ("moon.zzz.fill", "Asleep", Sig.warn)
            case .unpaired: return ("link.badge.plus", "Not paired", Sig.faint)
            case .unknown: return ("dot.radiowaves.left.and.right", "Checking…", Sig.muted)
            }
        }()
        HStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 11, weight: .black))
            Text(label.uppercased()).font(.system(size: 10, weight: .heavy)).tracking(0.8)
        }
        .foregroundStyle(color)
        .padding(.horizontal, 10).padding(.vertical, 6)
        .background(color.opacity(0.14), in: Capsule())
        .overlay(Capsule().strokeBorder(color.opacity(0.30), lineWidth: 1))
    }

    // The discovered list — computers found on the LAN by name, tap to connect.
    @ViewBuilder private var discoverySection: some View {
        HStack(spacing: 8) {
            Text("DISCOVERED ON YOUR NETWORK").font(.system(size: 11, weight: .heavy)).tracking(1.4)
                .foregroundStyle(Sig.faint)
            if browser.browsing {
                ProgressView().controlSize(.mini).tint(Sig.local)
            }
            Spacer()
        }
        .padding(.top, 6).padding(.leading, 2)
        .opacity(appeared ? 1 : 0)

        if browser.computers.isEmpty {
            scanningState.opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 12)
        } else {
            ForEach(Array(browser.computers.enumerated()), id: \.element.id) { i, c in
                Button { tactile(.medium); tap(c) } label: { discoveredRow(c) }
                    .buttonStyle(PressableCard())
                    .disabled(!c.reachable)
                    .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 14)
                    .animation(reduceMotion ? nil : .spring(response: 0.5, dampingFraction: 0.82)
                        .delay(0.05 + Double(i) * 0.05), value: appeared)
            }
        }
    }

    private func discoveredRow(_ c: DiscoveredComputer) -> some View {
        HStack(spacing: 14) {
            GlyphChip(system: c.name.lowercased().contains("linux") ? "pc" : "laptopcomputer",
                      gradient: c.reachable ? Sig.localGradient : Sig.localGradient, size: 50)
                .opacity(c.reachable ? 1 : 0.5)
            VStack(alignment: .leading, spacing: 4) {
                Text(c.name).font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 7) {
                    Image(systemName: c.reachable ? "dot.radiowaves.left.and.right" : "moon.zzz.fill")
                        .font(.system(size: 9, weight: .black))
                    Text(c.reachable ? (c.requiresToken ? "Reachable · needs pairing code" : "Reachable · ready to pair")
                                     : "Asleep · not reachable")
                        .font(.system(size: 11, weight: .heavy)).tracking(0.4)
                }
                .foregroundStyle(c.reachable ? Sig.ok : Sig.warn)
            }
            Spacer()
            if confirming && pairTarget?.id == c.id {
                ProgressView().controlSize(.small).tint(Sig.local)
            } else if c.reachable {
                Image(systemName: c.requiresToken ? "key.fill" : "arrow.right")
                    .font(.system(size: 14, weight: .black)).foregroundStyle(Sig.local)
            }
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading).signalCard(radius: 20)
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous)
            .strokeBorder(c.reachable ? Sig.local.opacity(0.18) : Sig.line, lineWidth: 1))
    }

    private var scanningState: some View {
        VStack(spacing: 14) {
            ZStack {
                Circle().fill(Sig.local.opacity(0.12)).frame(width: 78, height: 78)
                Circle().strokeBorder(Sig.local.opacity(0.3), lineWidth: 1).frame(width: 78, height: 78)
                Image(systemName: "dot.radiowaves.left.and.right").font(.system(size: 30, weight: .semibold))
                    .foregroundStyle(Sig.local)
            }
            VStack(spacing: 6) {
                Text("Looking for your desktop…").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Run HoldSpeak on your desktop.")
                    .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.faint)
                    .multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity).padding(.vertical, 28).padding(.horizontal, 18).signalCard(Sig.s1, radius: 22)
    }

    // The manual fallback for when discovery isn't available (no Bonjour on the network).
    private var manualRow: some View {
        Button { tactile(); manual = true } label: {
            HStack(spacing: 12) {
                Image(systemName: "keyboard").font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                    .frame(width: 40, height: 40).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Connect manually").font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.text)
                    Text("Enter the host, port and token by hand").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
                }
                Spacer()
                Image(systemName: "chevron.right").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
            }
            .padding(14).frame(maxWidth: .infinity, alignment: .leading).signalCard(Sig.s1, radius: 16)
        }
        .buttonStyle(PressableCard())
        .padding(.top, 6)
        .opacity(appeared ? 1 : 0)
    }

    // The token pairing step — tight, guided, not a raw form.
    private func tokenSheet(for target: DiscoveredComputer) -> some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 20) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Pair with").font(.system(size: 13, weight: .heavy)).tracking(0.6).foregroundStyle(Sig.faint)
                        Text(target.name).font(.system(size: 26, weight: .heavy)).foregroundStyle(Sig.text)
                    }
                    Spacer()
                    Button { pairTarget = nil; pairToken = "" } label: {
                        Image(systemName: "xmark").font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                            .frame(width: 38, height: 38).background(Sig.s2, in: Circle())
                    }
                }
                HStack(spacing: 10) {
                    Image(systemName: "key.fill").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.local)
                    Text("This computer needs a pairing token.").font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.text)
                }
                .padding(13).frame(maxWidth: .infinity, alignment: .leading)
                .background(Sig.local.opacity(0.10), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                VStack(alignment: .leading, spacing: 6) {
                    Text("PAIRING TOKEN").font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint)
                    TextField("shown when you run holdspeak web", text: $pairToken)
                        .font(.system(size: 16, weight: .semibold).monospaced()).foregroundStyle(Sig.text)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .padding(14).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
                    Text("Printed on your desktop at startup.")
                        .font(.system(size: 12)).foregroundStyle(Sig.faint)
                }
                Button { connect(target, token: pairToken.isEmpty ? nil : pairToken) } label: {
                    Text("Pair").font(.system(size: 17, weight: .heavy)).foregroundStyle(.black)
                        .frame(maxWidth: .infinity).padding(.vertical, 14)
                        .background(Sig.localGradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                }
                .disabled(pairToken.trimmingCharacters(in: .whitespaces).isEmpty)
                .opacity(pairToken.trimmingCharacters(in: .whitespaces).isEmpty ? 0.5 : 1)
                Spacer()
            }
            .padding(24).frame(maxWidth: 560).frame(maxWidth: .infinity)
        }
        .presentationDetents([.medium, .large])
    }

    // MARK: actions

    /// Tap a discovered computer: confirm identity via `GET /api/mesh/info`, then either pair
    /// straight through (no token) or present the token step (token required).
    private func tap(_ c: DiscoveredComputer) {
        guard c.reachable, let host = c.host, let port = c.port else { return }
        confirming = true
        pairTarget = nil
        Task {
            let info = await fetchMeshInfo(host: host, port: port)
            await MainActor.run {
                confirming = false
                let needsToken = info?.requiresToken ?? c.requiresToken
                if needsToken {
                    pairToken = ""
                    pairTarget = c        // present the token step
                } else {
                    connect(c, token: nil)
                }
            }
        }
    }

    /// Persist the discovered computer as the paired peer (host/port from discovery) and probe it.
    private func connect(_ c: DiscoveredComputer, token: String?) {
        guard let host = c.host, let port = c.port else { return }
        peers.adopt(name: c.name, host: host, port: port, token: token)
        pairTarget = nil; pairToken = ""
        Task { await probePaired() }
    }

    private func probePaired() async {
        guard peers.isPaired else { reach = .unpaired; return }
        guard let client = peers.client() else { reach = .asleep; return }
        let c = await client.handshake()
        await MainActor.run { reach = c.reachable ? .reachable : .asleep }
    }

    /// The unauthenticated identity probe (`GET /api/mesh/info`). Fail-soft — `nil` when the
    /// endpoint isn't there yet (the desktop half ships separately), so the TXT hint is used.
    private func fetchMeshInfo(host: String, port: Int) async -> MeshInfo? {
        guard let url = PeerAddress.base(host, port)?.appendingPathComponent("api/mesh/info") else { return nil }
        var req = URLRequest(url: url); req.timeoutInterval = 4
        guard let (data, resp) = try? await URLSession.shared.data(for: req),
              let http = resp as? HTTPURLResponse, (200...299).contains(http.statusCode) else { return nil }
        return try? HoldSpeakContracts.decoder().decode(MeshInfo.self, from: data)
    }
}

#if targetEnvironment(simulator)
/// Simulator-only: the Connect surface with a seeded discovery list (HS_DEMO_CONNECT=1) so the
/// "Your Desktop" screen renders fully without a live LAN service.
struct ConnectDemo: View {
    var body: some View { NavigationStack { ConnectView() } }
}
#endif

/// The pairing sheet: enter the Mac's host + port (and an optional token) so the iPad can reach the
/// desktop server on the LAN. One clear path, not buried in Settings (HSM-15-01).
struct PairMacSheet: View {
    @ObservedObject private var peers = DictatePeerStore.shared
    @Environment(\.dismiss) private var dismiss

    // A visible connection test — the manual sheet used to just save fields and
    // dismiss (no probe, no feedback), so a wrong host/port/token failed silently.
    // Now it dials the hub and shows the EXACT URL + the real result/error.
    private enum Probe: Equatable { case idle, testing, ok(String), fail(String) }
    @State private var probe: Probe = .idle

    /// The literal URL the client will dial — shown so a typo (a scheme, a stray
    /// path, the wrong port) is obvious on screen.
    private var dialedURL: String {
        PeerAddress.describe(peers.host, port: peers.portText, path: "/health")
    }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HStack {
                        Text("Pair your desktop").font(.system(size: 28, weight: .heavy)).foregroundStyle(Sig.text)
                        Spacer()
                        Button { dismiss() } label: {
                            Image(systemName: "xmark").font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                                .frame(width: 38, height: 38).background(Sig.s2, in: Circle())
                        }
                    }
                    Text("Run HoldSpeak on your desktop, then enter its address. A hostname works too; prefix https:// when the desktop is behind TLS (e.g. tailscale serve).")
                        .font(.system(size: 14)).foregroundStyle(Sig.faint)
                    field("Name", text: $peers.name, placeholder: "Karol's Mac")
                    field("Host", text: $peers.host, placeholder: "100.x.y.z or host.example.com")
                    field("Port", text: $peers.portText, placeholder: "8765")
                    field("Token", text: $peers.token, placeholder: "shown when you run holdspeak web")

                    // What it will actually dial + the live probe result.
                    VStack(alignment: .leading, spacing: 6) {
                        Text("WILL DIAL").font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint)
                        Text(dialedURL).font(.system(size: 13, weight: .semibold, design: .monospaced))
                            .foregroundStyle(Sig.muted).lineLimit(2).minimumScaleFactor(0.7)
                    }
                    switch probe {
                    case .idle: EmptyView()
                    case .testing:
                        HStack(spacing: 8) { ProgressView().controlSize(.small); Text("Testing…").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint) }
                    case .ok(let d):
                        Label(d, systemImage: "checkmark.circle.fill").font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.ok)
                    case .fail(let d):
                        Label(d, systemImage: "xmark.octagon.fill").font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.bad).lineLimit(4)
                    }

                    HStack(spacing: 12) {
                        Button { runProbe() } label: {
                            HStack(spacing: 7) {
                                Image(systemName: "dot.radiowaves.left.and.right")
                                Text("Test connection").font(.system(size: 15, weight: .heavy))
                            }
                            .foregroundStyle(Sig.text).frame(maxWidth: .infinity).padding(.vertical, 14)
                            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
                        }
                        .disabled(!peers.isPaired || probe == .testing)
                        .opacity(peers.isPaired ? 1 : 0.5)
                        Button { dismiss() } label: {
                            Text("Done").font(.system(size: 17, weight: .heavy)).foregroundStyle(.black)
                                .frame(maxWidth: .infinity).padding(.vertical, 14)
                                .background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                        }
                        .disabled(!peers.isPaired)
                        .opacity(peers.isPaired ? 1 : 0.5)
                    }
                }
                .padding(22).frame(maxWidth: 600).frame(maxWidth: .infinity)
            }
        }
    }

    private func runProbe() {
        probe = .testing
        Task {
            guard let client = peers.client() else {
                await MainActor.run { probe = .fail("Couldn't build a request — check the host and port (port must be a number).") }
                return
            }
            let c = await client.handshake()
            await MainActor.run {
                probe = c.reachable ? .ok(c.runtimeReady ? "Reachable · \(c.detail)" : "Reachable")
                                    : .fail(c.detail)   // "desktop unreachable: <the real URLError reason>"
            }
        }
    }

    private func field(_ label: String, text: Binding<String>, placeholder: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label.uppercased()).font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint)
            TextField(placeholder, text: text)
                .font(.system(size: 16, weight: .semibold)).foregroundStyle(Sig.text)
                .textInputAutocapitalization(.never).autocorrectionDisabled()
                .padding(14).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
        }
    }
}

#if targetEnvironment(simulator)
/// Simulator-only: the Dictate surface seeded for a design screenshot — a named Mac, an active
/// waveform (a non-zero level so the meter leaps), a read-back of dictated lines (one in-flight),
/// and the egress badge. The desktop peer + a real mic aren't live in the Simulator. HS_DEMO_DICTATE=1.
struct DictateDemo: View {
    var body: some View {
        NavigationStack { DictateView() }
            .onAppear {
                let p = DictatePeerStore.shared
                if p.host.isEmpty { p.host = "192.168.1.13"; p.portText = "8081" }
                if p.name.isEmpty { p.name = "Karol's Mac" }
            }
    }
}

/// Simulator-only: the Agent Desk seeded with a few live agents (one working, one waiting with a
/// real-sounding question, one idle, one stale) for a design screenshot. Waiting sorts first + pulses.
struct AgentDeskDemo: View {
    static let seed = CompanionBoardState(
        readyForReply: true,
        blockers: [],
        awaiting: true,
        targets: [
            CompanionTarget(agent: "claude", sessionID: "s1",
                            question: "Run the destructive schema migration on prod now, or stage it behind a backup first?",
                            project: "holdspeak/web-runtime", selected: true, pinned: false, stale: false, confidence: "high"),
            CompanionTarget(agent: "codex", sessionID: "s2",
                            question: nil, project: "acme/billing-api", selected: false, pinned: true, stale: false, confidence: "high"),
            CompanionTarget(agent: "claude", sessionID: "s3",
                            question: nil, project: "infra/terraform", selected: false, pinned: false, stale: false, confidence: "medium"),
            CompanionTarget(agent: "codex", sessionID: "s4",
                            question: "Should I keep retrying the flaky integration test or skip it?",
                            project: "tools/scratchpad", selected: false, pinned: false, stale: true, confidence: "low"),
        ])
    var body: some View { NavigationStack { AgentDeskView(state: AgentDeskDemo.seed) } }
}

/// Simulator-only: open Settings with a sample LAN endpoint configured, for a design screenshot.
struct SettingsDemo: View {
    var body: some View {
        NavigationStack { SettingsView() }
            .onAppear {
                let c = InferenceConfigStore.shared
                c.mode = .homelab
                if c.endpointURL.isEmpty { c.endpointURL = "http://192.168.1.43:8080/v1"; c.endpointModel = "qwen3-9b" }
            }
    }
}

/// Simulator-only: the generation theater mid-flight, inside the real INTELLIGENCE card, for a
/// design screenshot (the live model needs a resident GGUF + minutes). Never in the device build.
struct GenTheaterDemo: View {
    private let types: [ArtifactType] = [.decisions, .actionItems, .riskRegister, .requirements]
    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.accent.opacity(0.14)).frame(width: 420).blur(radius: 130)
                .offset(x: 150, y: -320).ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("INTELLIGENCE").font(.caption2.weight(.bold)).tracking(1.5).foregroundStyle(Sig.accent)
                        Spacer()
                    }
                    GenerationTheater(note: "", lens: .delivery, types: types,
                                      done: [.decisions], current: .actionItems)
                }
                .padding(16).signalCard(radius: 18)
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
    }
}
#endif
