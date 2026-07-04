import SwiftUI

// HSM-5-06 device harness — the iPad's on-device (Mode C) meeting-intelligence run.
//
// Dressed in the "Signal" design language (bold near-black surfaces, one orange
// signal reserved for the live/primary moment, real depth + per-type artifact
// cards) so it's showpiece-grade, not stock SwiftUI. Compiled as one module with
// the Contracts/Providers/RuntimeCore sources (gen-inference-harness.rb), so it
// imports no package modules.

@main
struct InferenceHarnessApp: App {
    var body: some Scene {
        WindowGroup { HarnessView().preferredColorScheme(.dark) }
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
    static let done = Color(hex: 0x3ECF8E)

    /// Per-artifact-type accent + glyph — visual variety across the result cards.
    static func style(for type: String) -> (Color, String) {
        switch type {
        case "decisions":     return (Color(hex: 0x5B8DEF), "checkmark.seal.fill")
        case "action_items":  return (done, "arrow.right.circle.fill")
        case "requirements":  return (Color(hex: 0xF2A33C), "list.bullet.rectangle.fill")
        case "risk_register": return (Color(hex: 0xE5544B), "exclamationmark.triangle.fill")
        default:              return (accent, "sparkles")
        }
    }
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

@MainActor
final class HarnessModel: ObservableObject {
    @Published var endpoint = ProcessInfo.processInfo.environment["HS_ENDPOINT"] ?? "http://192.168.1.13:8081/v1"
    @Published var model = ProcessInfo.processInfo.environment["HS_MODEL"] ?? "local"
    @Published var mode: RuntimeMode = .homelab
    @Published var running = false
    @Published var status = "Ready when you are."
    @Published var elapsed = ""
    @Published var results: [ArtifactResult] = []

    var autoRun: Bool { ProcessInfo.processInfo.environment["HS_AUTORUN"] == "1" }

    /// Honest egress descriptor (positioning: one badge, never a privacy novel).
    var egress: String {
        switch mode {
        case .local: return "on device"
        case .homelab, .endpoint:
            let host = URL(string: endpoint)?.host ?? "endpoint"
            return "local + LAN → \(host)"
        }
    }

    struct ArtifactResult: Identifiable {
        let id = UUID()
        let type: String
        let ok: Bool
        let title: String
        let body: String
    }

    private func sampleTranscript() -> Transcript {
        let lines: [(String, String)] = [
            ("Alice", "Let's lock the API. I propose we standardize on the OpenAI-compatible endpoint for mobile inference."),
            ("Bob", "Agreed. We decided the iPad will default to the homelab endpoint rather than loading a local model."),
            ("Alice", "Bob, can you wire the endpoint config screen by Friday?"),
            ("Bob", "Yes, I'll own the endpoint settings UI and have it ready Friday."),
            ("Alice", "One risk: if the LAN is unreachable we need a local fallback so meetings don't stall."),
        ]
        var t = 0.0
        let segments = lines.map { pair -> Segment in
            defer { t += 5 }
            return Segment(text: pair.1, speaker: pair.0, startTime: t, endTime: t + 5)
        }
        return Transcript(meetingId: "ipad_mtg_001", segments: segments, transcriptHash: "ipad-hash")
    }

    func run() {
        guard !running, let url = URL(string: endpoint) else { return }
        running = true
        results = []
        elapsed = ""
        status = "Generating artifacts on device…"
        let config = EndpointConfig(baseURL: url, model: model, temperature: 0.2, timeout: 180)

        Task { @MainActor in
            let start = Date()
            do {
                let provider = try InferenceProviderFactory.make(mode: mode, endpoint: config)
                let engine = ArtifactGenerationEngine(provider: provider)
                let types: [ArtifactType] = [.decisions, .actionItems, .requirements]
                let outcomes = await engine.generate(types: types, from: sampleTranscript())
                for (type, result) in outcomes {
                    switch result {
                    case .success(let a):
                        results.append(.init(type: type.rawValue, ok: true, title: a.title, body: a.bodyMarkdown))
                    case .failure(let e):
                        results.append(.init(type: type.rawValue, ok: false, title: "Couldn't generate", body: "\(e)"))
                    }
                }
                let secs = String(format: "%.1f", Date().timeIntervalSince(start))
                let ok = results.filter(\.ok).count
                status = "\(ok)/\(results.count) artifacts, on device"
                elapsed = "\(secs)s"
            } catch {
                status = "Error: \(error)"
            }
            running = false
        }
    }
}

struct HarnessView: View {
    @StateObject private var m = HarnessModel()

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            // The signal glow, top-trailing.
            RadialGradient(colors: [Sig.accent.opacity(0.18), .clear],
                           center: .topTrailing, startRadius: 0, endRadius: 520)
                .ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    header
                    configCard
                    runButton
                    statusRow
                    if m.running && m.results.isEmpty { generatingState }
                    ForEach(m.results) { artifactCard($0) }
                    Spacer(minLength: 24)
                }
                .padding(24)
                .frame(maxWidth: 760)
                .frame(maxWidth: .infinity)
            }
        }
        .onAppear { if m.autoRun { m.run() } }
    }

    // MARK: header

    private var header: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(LinearGradient(colors: [Sig.accent, Color(hex: 0xEC5A28)],
                                         startPoint: .topLeading, endPoint: .bottomTrailing))
                    .frame(width: 30, height: 30)
                    .overlay(Image(systemName: "waveform").font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.bg))
                Text("HoldSpeak").font(.system(size: 19, weight: .bold)).foregroundStyle(Sig.text)
                Text("Mobile").font(.system(size: 19, weight: .regular)).foregroundStyle(Sig.faint)
                Spacer()
                Text("Mode C")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Sig.accent)
                    .padding(.horizontal, 10).padding(.vertical, 5)
                    .background(Sig.accent.opacity(0.12), in: Capsule())
            }
            Text("On-device meeting intelligence")
                .font(.system(size: 30, weight: .bold)).foregroundStyle(Sig.text)
                .fixedSize(horizontal: false, vertical: true)
            Text("A meeting, turned into decisions you can act on — generated on the device.")
                .font(.system(size: 15)).foregroundStyle(Sig.muted)
        }
    }

    // MARK: config

    private var configCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 8) {
                ForEach([RuntimeMode.local, .homelab, .endpoint], id: \.self) { mode in
                    let on = m.mode == mode
                    Text(label(mode))
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(on ? Sig.bg : Sig.muted)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 9)
                        .background(on ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.s3),
                                    in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                        .onTapGesture { m.mode = mode }
                }
            }
            row(icon: "link", label: "Endpoint", value: m.endpoint)
            Divider().overlay(Sig.line)
            row(icon: "cpu", label: "Model", value: m.model)
            HStack(spacing: 7) {
                Image(systemName: "lock.shield.fill").font(.system(size: 12)).foregroundStyle(Sig.done)
                Text(m.egress).font(.system(size: 12.5, weight: .medium)).foregroundStyle(Sig.muted)
            }
            .padding(.top, 2)
        }
        .padding(18)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Sig.line, lineWidth: 1))
    }

    private func row(icon: String, label: String, value: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon).font(.system(size: 13)).foregroundStyle(Sig.faint).frame(width: 18)
            Text(label).font(.system(size: 14)).foregroundStyle(Sig.muted)
            Spacer()
            Text(value).font(.system(size: 13.5, design: .monospaced)).foregroundStyle(Sig.text)
                .lineLimit(1).truncationMode(.middle)
        }
    }

    private func label(_ m: RuntimeMode) -> String {
        switch m { case .local: return "Local · A"; case .homelab: return "Homelab · B"; case .endpoint: return "Endpoint · C" }
    }

    // MARK: primary action

    private var runButton: some View {
        Button(action: m.run) {
            HStack(spacing: 9) {
                Image(systemName: m.running ? "circle.dotted" : "sparkles")
                    .font(.system(size: 16, weight: .semibold))
                Text(m.running ? "Generating…" : "Generate artifacts on device")
                    .font(.system(size: 16, weight: .semibold))
            }
            .frame(maxWidth: .infinity).padding(.vertical, 15)
            .foregroundStyle(Sig.bg)
            .background(
                LinearGradient(colors: m.running ? [Sig.s3, Sig.s3] : [Sig.accent, Color(hex: 0xEC5A28)],
                               startPoint: .leading, endPoint: .trailing),
                in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .foregroundStyle(m.running ? Sig.faint : Sig.bg)
            .shadow(color: m.running ? .clear : Sig.accent.opacity(0.35), radius: 18, y: 8)
        }
        .disabled(m.running)
    }

    private var statusRow: some View {
        HStack(spacing: 8) {
            Circle().fill(m.running ? Sig.accent : (m.results.isEmpty ? Sig.faint : Sig.done))
                .frame(width: 8, height: 8)
            Text(m.status).font(.system(size: 14, weight: .medium)).foregroundStyle(Sig.muted)
            Spacer()
            if !m.elapsed.isEmpty {
                Text(m.elapsed).font(.system(size: 13, design: .monospaced)).foregroundStyle(Sig.faint)
            }
        }
    }

    private var generatingState: some View {
        VStack(spacing: 12) {
            ProgressView().tint(Sig.accent).scaleEffect(1.2)
            Text("Reading the transcript, proposing artifacts…")
                .font(.system(size: 13)).foregroundStyle(Sig.faint)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 40)
        .background(Sig.s1.opacity(0.5), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    // MARK: artifact card

    private func artifactCard(_ r: HarnessModel.ArtifactResult) -> some View {
        let (tint, glyph) = Sig.style(for: r.type)
        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 9) {
                Image(systemName: r.ok ? glyph : "xmark.octagon.fill")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(r.ok ? tint : Sig.accent)
                Text(r.type.uppercased())
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.5)
                    .foregroundStyle(tint)
                Spacer()
                Text("draft").font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(Sig.faint)
                    .padding(.horizontal, 7).padding(.vertical, 3)
                    .background(Sig.s3, in: Capsule())
            }
            Text(r.title).font(.system(size: 16.5, weight: .semibold)).foregroundStyle(Sig.text)
                .fixedSize(horizontal: false, vertical: true)
            Text(r.body).font(.system(size: 14)).foregroundStyle(Sig.muted)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(18)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(LinearGradient(colors: [tint.opacity(0.35), Sig.line],
                                       startPoint: .topLeading, endPoint: .bottomTrailing), lineWidth: 1)
        )
        .overlay(alignment: .leading) {
            RoundedRectangle(cornerRadius: 2).fill(tint).frame(width: 3).padding(.vertical, 14)
        }
    }
}
