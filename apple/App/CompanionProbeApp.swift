import SwiftUI

// HSM-12-01 (real-metal probe) — the Companion seam on the device. Point this iPad
// at the same HoldSpeak desktop/homelab server a coding session runs against and
// watch it connect: pairing (host/port/token) → handshake against /health +
// /api/runtime/status → reachable / runtime-ready / honest egress. It drives the
// REAL `HTTPDesktopClient` + `CompanionLink` from HSM-12-01 (no mock), so a green
// connection here is a real-metal proof of the seam and the first seed of the
// HSM-12-03 shell. Dressed in the "Signal" language to a high UI standard.
//
// Compiled as ONE module with the Contracts/Providers/RuntimeCore sources
// (gen-companion-probe.rb), so it imports no package modules.

@main
struct CompanionProbeApp: App {
    var body: some Scene {
        WindowGroup { ProbeView().preferredColorScheme(.dark) }
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
}

private extension Color {
    init(hex: UInt) {
        self.init(.sRGB,
                  red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255,
                  opacity: 1)
    }
}

// MARK: - Model

@MainActor
final class ProbeModel: ObservableObject {
    @Published var host = ProcessInfo.processInfo.environment["HS_DESKTOP_HOST"] ?? ""
    @Published var portText = ProcessInfo.processInfo.environment["HS_DESKTOP_PORT"] ?? "8000"
    @Published var token = ProcessInfo.processInfo.environment["HS_DESKTOP_TOKEN"] ?? ""
    @Published var useTLS = false

    @Published var probing = false
    @Published var connection: DesktopConnection?
    @Published var egress = ""
    @Published var didProbe = false

    /// Auto-probe on launch when a host is supplied via the environment (hands-off
    /// device demo); otherwise wait for the owner to fill the form and tap Connect.
    var autoProbe: Bool { !host.trimmingCharacters(in: .whitespaces).isEmpty }

    func connect() async {
        probing = true
        defer { probing = false; didProbe = true }

        guard let port = Int(portText.trimmingCharacters(in: .whitespaces)), port > 0 else {
            connection = .offline("invalid port"); egress = ""; return
        }
        let peer = DesktopPeer(host: host, port: port,
                               token: token.isEmpty ? nil : token,
                               scheme: useTLS ? "https" : "http")
        guard let config = HTTPDesktopClient.Config(peer: peer) else {
            connection = .offline("invalid host"); egress = ""; return
        }
        let link = CompanionLink(client: HTTPDesktopClient(config: config))
        egress = link.egressLabel
        connection = await link.probe()
    }
}

// MARK: - View

struct ProbeView: View {
    @StateObject private var model = ProbeModel()

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    pairingCard
                    if model.didProbe || model.probing { statusCard }
                    footer
                }
                .padding(20)
                .frame(maxWidth: 560)
                .frame(maxWidth: .infinity)
            }
        }
        .task { if model.autoProbe { await model.connect() } }
        .tint(Sig.accent)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("COMPANION").font(.caption.weight(.bold)).tracking(2).foregroundStyle(Sig.accent)
            Text("Point this iPad at your desktop")
                .font(.largeTitle.bold()).foregroundStyle(Sig.text)
            Text("HSM-12-01 · the desktop client seam, on real metal")
                .font(.footnote).foregroundStyle(Sig.faint)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var pairingCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            cardTitle("Pair", "Your HoldSpeak desktop / homelab, on your own network")
            field("Host", text: $model.host, placeholder: "192.168.1.x or desk.tailnet",
                  keyboard: .URL)
            HStack(spacing: 12) {
                field("Port", text: $model.portText, placeholder: "8000", keyboard: .numberPad)
                    .frame(width: 140)
                Toggle("HTTPS", isOn: $model.useTLS)
                    .toggleStyle(.switch).tint(Sig.accent)
                    .font(.subheadline).foregroundStyle(Sig.muted)
            }
            field("Token (optional)", text: $model.token, placeholder: "Bearer token if your server requires one",
                  secure: true)

            Button { Task { await model.connect() } } label: {
                HStack {
                    if model.probing { ProgressView().tint(.black) }
                    Text(model.probing ? "Connecting…" : "Connect")
                        .font(.headline).foregroundStyle(.black)
                }
                .frame(maxWidth: .infinity).padding(.vertical, 13)
                .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
            }
            .disabled(model.probing || model.host.trimmingCharacters(in: .whitespaces).isEmpty)
            .opacity(model.host.trimmingCharacters(in: .whitespaces).isEmpty ? 0.5 : 1)
        }
        .cardChrome()
    }

    @ViewBuilder private var statusCard: some View {
        let c = model.connection
        let reachable = c?.reachable ?? false
        let ready = c?.runtimeReady ?? false
        let dotColor = !reachable ? Sig.bad : (ready ? Sig.ok : Sig.warn)
        let title = !reachable ? "Unreachable" : (ready ? "Connected" : "Reachable")

        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 10) {
                Circle().fill(dotColor).frame(width: 12, height: 12)
                    .shadow(color: dotColor.opacity(0.7), radius: 6)
                Text(title).font(.title3.bold()).foregroundStyle(Sig.text)
                Spacer()
                if model.probing { ProgressView().tint(Sig.accent) }
            }
            statusRow("Reachable", reachable ? "yes" : "no", reachable ? Sig.ok : Sig.bad)
            statusRow("Runtime ready", ready ? "yes" : "no", ready ? Sig.ok : Sig.warn)
            if let detail = c?.detail, !detail.isEmpty {
                statusRow("Detail", detail, Sig.muted)
            }
            if !model.egress.isEmpty { egressBadge(model.egress) }
        }
        .cardChrome()
    }

    private var footer: some View {
        Text("Reachability probes /health; readiness reads /api/runtime/status. Nothing is sent but the probe — the egress badge shows exactly where it goes.")
            .font(.caption).foregroundStyle(Sig.faint)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: bits

    private func cardTitle(_ t: String, _ sub: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(t).font(.headline).foregroundStyle(Sig.text)
            Text(sub).font(.caption).foregroundStyle(Sig.faint)
        }
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

    private func statusRow(_ k: String, _ v: String, _ color: Color) -> some View {
        HStack {
            Text(k).font(.subheadline).foregroundStyle(Sig.muted)
            Spacer()
            Text(v).font(.subheadline.monospaced()).foregroundStyle(color)
                .multilineTextAlignment(.trailing)
        }
    }

    private func egressBadge(_ label: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "arrow.up.right.circle.fill").foregroundStyle(Sig.accent)
            Text(label).font(.caption.monospaced()).foregroundStyle(Sig.muted)
        }
        .padding(.horizontal, 10).padding(.vertical, 8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s3, in: RoundedRectangle(cornerRadius: 9))
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(Sig.line, lineWidth: 1))
    }
}

private extension View {
    func cardChrome() -> some View {
        self.padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
    }
}
