import SwiftUI

// HSM-5-02 (real-metal) — the FULLY-LOCAL (charter Mode A) device harness. Loads a
// GGUF from the app's Documents (push it with scripts/push-model-device.sh) and turns
// a meeting transcript into artifacts with **no network** — llama.cpp via LLM.swift
// (LlamaProvider) on the device's Metal. This is the airplane-mode paradigm: host
// the model on the iPad itself. Unlike the Mode-C harness, this app LINKS the native
// engine (InferenceLlama + the LLM package).
//
// Compiled as ONE module with the Contracts/Providers/RuntimeCore/InferenceLlama
// sources (gen-local-harness.rb), so it imports no package modules.

@main
struct LocalHarnessApp: App {
    var body: some Scene {
        WindowGroup { LocalView().preferredColorScheme(.dark) }
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
    static let bad = Color(hex: 0xE5544B)

    static func style(for type: String) -> (Color, String) {
        switch type {
        case "decisions":    return (Color(hex: 0x5B8DEF), "checkmark.seal.fill")
        case "action_items": return (ok, "arrow.right.circle.fill")
        case "requirements": return (Color(hex: 0xF2A33C), "list.bullet.rectangle.fill")
        default:             return (accent, "sparkles")
        }
    }
}

private extension Color {
    init(hex: UInt) {
        self.init(.sRGB,
                  red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: 1)
    }
}

// MARK: - Model

@MainActor
final class LocalModel: ObservableObject {
    @Published var running = false
    @Published var status = "Fully on-device — no network."
    @Published var modelName = ""
    @Published var modelPath: String?
    @Published var elapsed = ""
    @Published var results: [ArtifactResult] = []

    struct ArtifactResult: Identifiable {
        let id = UUID(); let type: String; let ok: Bool; let title: String; let body: String
    }

    var autoRun: Bool { ProcessInfo.processInfo.environment["HS_AUTORUN"] == "1" }

    init() { locateModel() }

    /// Find a `.gguf` in the app's Documents (pushed via push-model-device.sh).
    func locateModel() {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            status = "No Documents directory."; return
        }
        let ggufs = ((try? FileManager.default.contentsOfDirectory(at: docs, includingPropertiesForKeys: nil)) ?? [])
            .filter { $0.pathExtension.lowercased() == "gguf" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        if let first = ggufs.first {
            modelPath = first.path; modelName = first.lastPathComponent
            status = "Model ready — tap Run to generate, fully on device."
        } else {
            modelPath = nil; modelName = ""
            status = "No .gguf in Documents. Push one: scripts/push-model-device.sh <model>.gguf"
        }
    }

    func run() {
        guard !running, let path = modelPath else { return }
        running = true; results = []; elapsed = ""; status = "Loading the model on device…"
        Task { @MainActor in
            let start = Date()
            do {
                let provider = try LlamaProvider(modelPath: path)
                status = "Generating artifacts — fully on device…"
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
                status = "\(results.filter(\.ok).count)/\(results.count) artifacts, fully on device"
                elapsed = "\(secs)s"
            } catch {
                status = "Error: \(error)"
            }
            running = false
        }
    }

    private func sampleTranscript() -> Transcript {
        let lines: [(String, String)] = [
            ("Alice", "Let's lock the plan. I propose we ship the iPad able to host its own model, fully offline."),
            ("Bob", "Agreed. We decided Mode A runs llama.cpp on the device with no endpoint."),
            ("Alice", "Bob, can you push a 4B GGUF and run the airplane-mode test by Friday?"),
            ("Bob", "Yes, I'll own the on-device run and have it ready Friday."),
            ("Alice", "One risk: a 12B model could thermally throttle on battery, so keep the default at 4B."),
        ]
        var t = 0.0
        let segments = lines.map { pair -> Segment in
            defer { t += 5 }
            return Segment(text: pair.1, speaker: pair.0, startTime: t, endTime: t + 5)
        }
        return Transcript(meetingId: "ipad_local_001", segments: segments, transcriptHash: "ipad-local-hash")
    }
}

// MARK: - View

struct LocalView: View {
    @StateObject private var m = LocalModel()

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            RadialGradient(colors: [Sig.accent.opacity(0.16), .clear],
                           center: .topTrailing, startRadius: 0, endRadius: 520).ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    modelCard
                    runButton
                    statusLine
                    if m.running && m.results.isEmpty { generating }
                    ForEach(m.results) { card($0) }
                    egressBadge
                    Spacer(minLength: 16)
                }
                .padding(22).frame(maxWidth: 720).frame(maxWidth: .infinity)
            }
        }
        .onAppear { if m.autoRun { m.run() } }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(LinearGradient(colors: [Sig.accent, Color(hex: 0xEC5A28)], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .frame(width: 30, height: 30)
                    .overlay(Image(systemName: "cpu.fill").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.bg))
                Text("HoldSpeak").font(.system(size: 19, weight: .bold)).foregroundStyle(Sig.text)
                Text("Mobile").font(.system(size: 19)).foregroundStyle(Sig.faint)
                Spacer()
                Text("Mode A · local")
                    .font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.accent)
                    .padding(.horizontal, 10).padding(.vertical, 5)
                    .background(Sig.accent.opacity(0.12), in: Capsule())
            }
            Text("Hosted on the iPad").font(.system(size: 29, weight: .bold)).foregroundStyle(Sig.text)
            Text("A meeting, turned into decisions by a model running on this device — airplane-mode, no endpoint.")
                .font(.system(size: 15)).foregroundStyle(Sig.muted).fixedSize(horizontal: false, vertical: true)
        }
    }

    private var modelCard: some View {
        let has = m.modelPath != nil
        return HStack(spacing: 12) {
            Image(systemName: has ? "shippingbox.fill" : "shippingbox")
                .font(.system(size: 22)).foregroundStyle(has ? Sig.ok : Sig.faint)
            VStack(alignment: .leading, spacing: 3) {
                Text(has ? m.modelName : "No model on device").font(.system(size: 15, weight: .semibold).monospaced()).foregroundStyle(Sig.text)
                Text(has ? "GGUF in Documents · loads with llama.cpp" : "Push one: scripts/push-model-device.sh <model>.gguf")
                    .font(.caption).foregroundStyle(Sig.faint)
            }
            Spacer()
            Button { m.locateModel() } label: { Image(systemName: "arrow.clockwise").foregroundStyle(Sig.muted) }
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Sig.line, lineWidth: 1))
    }

    private var runButton: some View {
        Button { m.run() } label: {
            HStack {
                if m.running { ProgressView().tint(.black) } else { Image(systemName: "play.fill").foregroundStyle(.black) }
                Text(m.running ? "Working…" : "Run on device").font(.headline).foregroundStyle(.black)
            }
            .frame(maxWidth: .infinity).padding(.vertical, 13)
            .background(Sig.accent, in: RoundedRectangle(cornerRadius: 12))
        }
        .disabled(m.running || m.modelPath == nil)
        .opacity(m.modelPath == nil ? 0.5 : 1)
    }

    private var statusLine: some View {
        HStack {
            Text(m.status).font(.subheadline).foregroundStyle(Sig.muted)
            Spacer()
            if !m.elapsed.isEmpty { Text(m.elapsed).font(.subheadline.monospaced()).foregroundStyle(Sig.accent) }
        }
    }

    private var generating: some View {
        HStack(spacing: 10) {
            ProgressView().tint(Sig.accent)
            Text("The model is thinking, on the device…").font(.subheadline).foregroundStyle(Sig.faint)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
    }

    private func card(_ r: LocalModel.ArtifactResult) -> some View {
        let (color, glyph) = Sig.style(for: r.type)
        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 9) {
                Image(systemName: r.ok ? glyph : "exclamationmark.triangle.fill").foregroundStyle(r.ok ? color : Sig.bad)
                Text(r.type.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.system(size: 13, weight: .bold)).tracking(0.5).foregroundStyle(r.ok ? color : Sig.bad)
                Spacer()
            }
            Text(r.title).font(.system(size: 16, weight: .semibold)).foregroundStyle(Sig.text)
            Text(r.body).font(.system(size: 14).monospaced()).foregroundStyle(Sig.muted)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Sig.line, lineWidth: 1))
    }

    private var egressBadge: some View {
        HStack(spacing: 8) {
            Image(systemName: "lock.fill").foregroundStyle(Sig.ok)
            Text("on-device · nothing leaves").font(.caption.monospaced()).foregroundStyle(Sig.muted)
        }
        .padding(.horizontal, 10).padding(.vertical, 8)
        .background(Sig.s3, in: RoundedRectangle(cornerRadius: 9))
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(Sig.line, lineWidth: 1))
    }
}
