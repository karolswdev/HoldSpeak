import SwiftUI

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
        guard let c = client() else { return }
        loading = true; defer { loading = false }
        let summary = localSummary
        let shell = CompanionShell(link: CompanionLink(client: c),
                                   meetings: CompanionMeetings(client: c),
                                   localProvider: { summary })
        state = await shell.load()
        if case .success(let b) = await CompanionBoard(client: c).load() { board = b }
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
}

// MARK: - Shell

struct ShellView: View {
    @StateObject private var model = ShellModel()
    @State private var tab: Tab = ShellView.initialTab

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
        .task { if model.canConnect { await model.load() } }
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
        }
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
                rowNote("No local recordings yet — capture, transcription and inference run here, nothing leaves.")
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
                let meetings = model.state?.serverMeetings ?? []
                if meetings.isEmpty {
                    rowNote("No meetings on the desktop yet.")
                } else {
                    ForEach(meetings) { m in meetingRow(m, tint: Sig.accent) }
                }
                HStack(spacing: 12) {
                    Button { Task { await model.startMeeting() } } label: {
                        label("Start meeting", "record.circle", filled: true)
                    }
                    Button { Task { await model.stopMeeting() } } label: {
                        label("Stop", "stop.circle", filled: false)
                    }
                    if !model.busy.isEmpty {
                        ProgressView().tint(Sig.accent); Text(model.busy).font(.caption).foregroundStyle(Sig.faint)
                    }
                }
            } else {
                rowNote("The desktop isn't reachable right now. Nothing here is blocked — your iPad's own runtime above is fully live. It reconnects on its own when the server returns.")
                Button { Task { await model.load() } } label: { label("Retry", "arrow.clockwise", filled: false) }
            }
        }
        .cardChrome(border: connected ? Sig.line : Sig.warn.opacity(0.35))
    }

    // MARK: Dictate — nav slot (on-device)

    private var dictateScreen: some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("DICTATE", "Speak; it types — fully on-device", Sig.local, live: true)
            FlowChips(["Push-to-talk", "On-device Whisper", "Rich pipeline on send"], tint: Sig.local)
            rowNote("Dictation runs on this iPad. The deep dictation surface lands with the on-device experience; the companion never moves it off the device.")
        }
        .cardChrome(border: Sig.local.opacity(0.35))
    }

    // MARK: Companion — nav slot (Phase 13 lives here)

    private var companionScreen: some View {
        VStack(alignment: .leading, spacing: 14) {
            peerHeader("ANSWER THE CODER", "The agent's question, on your iPad", Sig.accent,
                       live: model.board.awaiting)
            if model.board.targets.isEmpty {
                rowNote("No coder is waiting right now. When an agent in your session asks a question, it surfaces here — answer it by voice.")
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
            rowNote("Speak your answer; it transcribes on-device and delivers into the coder — never autonomously.")
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
                    Text("It stays a full on-device runtime — pairing just adds the server you code against.")
                        .font(.footnote).foregroundStyle(Sig.faint)
                }
                VStack(alignment: .leading, spacing: 14) {
                    field("Host", text: $model.host, placeholder: "192.168.1.x", keyboard: .URL)
                    HStack(spacing: 12) {
                        field("Port", text: $model.portText, placeholder: "8000", keyboard: .numberPad).frame(width: 130)
                        field("Token", text: $model.token, placeholder: "Bearer token", secure: true)
                    }
                    Button { Task { await model.load() } } label: {
                        Text("Connect").font(.headline).foregroundStyle(.black)
                            .frame(maxWidth: .infinity).padding(.vertical, 13)
                            .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
                    }
                    .disabled(!model.canConnect).opacity(model.canConnect ? 1 : 0.5)
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
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.caption.weight(.bold)).tracking(1.5).foregroundStyle(tint)
                Text(sub).font(.caption).foregroundStyle(Sig.faint)
            }
            Spacer()
        }
    }

    private func meetingRow(_ m: MeetingSummary, tint: Color) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "waveform").font(.caption).foregroundStyle(tint)
            Text(m.title ?? m.id).font(.subheadline).foregroundStyle(Sig.text).lineLimit(1)
            Spacer()
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
