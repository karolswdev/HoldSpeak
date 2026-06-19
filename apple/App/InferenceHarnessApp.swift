import SwiftUI

// HSM-5-06 device harness: the iPad's first real meeting-intelligence run.
//
// This is NOT the Phase-8 iPad experience — it is the on-device proof that the
// charter's Mode C (any OpenAI-compatible endpoint) works end to end on real
// hardware: a transcript → OpenAIEndpointProvider → ArtifactGenerationEngine →
// contract-shaped artifacts, all on the iPad, talking to a homelab/LAN endpoint
// so the device spends no unified memory on a resident model (owner steer
// 2026-06-19). It is compiled as one module with the Contracts/Providers/
// RuntimeCore sources (see scripts/gen-inference-harness.rb), so it imports no
// package modules — the types are already in scope.

@main
struct InferenceHarnessApp: App {
    var body: some Scene {
        WindowGroup { HarnessView() }
    }
}

@MainActor
final class HarnessModel: ObservableObject {
    // Default to the dev Mac on the LAN; editable on-device. `HS_ENDPOINT` /
    // `HS_MODEL` override it (used for the simulator capture, which reaches the
    // host over loopback).
    @Published var endpoint = ProcessInfo.processInfo.environment["HS_ENDPOINT"] ?? "http://192.168.1.13:8081/v1"
    @Published var model = ProcessInfo.processInfo.environment["HS_MODEL"] ?? "local"
    @Published var mode: RuntimeMode = .homelab
    @Published var running = false
    @Published var status = "Ready."
    @Published var results: [ArtifactResult] = []

    /// `HS_AUTORUN=1` kicks generation on launch (so a screenshot captures real output).
    var autoRun: Bool { ProcessInfo.processInfo.environment["HS_AUTORUN"] == "1" }

    struct ArtifactResult: Identifiable {
        let id = UUID()
        let type: String
        let ok: Bool
        let title: String
        let body: String
    }

    // A small but real meeting: clear decisions + an action + a risk.
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
        status = "Generating artifacts on device via \(mode.rawValue) endpoint…"
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
                        results.append(.init(type: type.rawValue, ok: true,
                                             title: a.title, body: a.bodyMarkdown))
                    case .failure(let e):
                        results.append(.init(type: type.rawValue, ok: false,
                                             title: "failed", body: "\(e)"))
                    }
                }
                let secs = String(format: "%.1f", Date().timeIntervalSince(start))
                let ok = results.filter(\.ok).count
                status = "Done — \(ok)/\(results.count) artifacts in \(secs)s on device."
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
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    header
                    config
                    Button(action: m.run) {
                        Label(m.running ? "Running…" : "Generate artifacts on device",
                              systemImage: "sparkles")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(m.running)

                    Text(m.status)
                        .font(.callout)
                        .foregroundStyle(m.running ? .secondary : .primary)

                    if m.running { ProgressView().frame(maxWidth: .infinity) }

                    ForEach(m.results) { r in artifactCard(r) }
                }
                .padding()
            }
            .navigationTitle("HoldSpeak · Mode C")
            .onAppear { if m.autoRun { m.run() } }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("On-device meeting intelligence")
                .font(.title2).bold()
            Text("contracts v\(HoldSpeakContracts.contractVersion) · HSM-5-06")
                .font(.footnote.monospaced()).foregroundStyle(.secondary)
        }
    }

    private var config: some View {
        VStack(alignment: .leading, spacing: 8) {
            Picker("Mode", selection: $m.mode) {
                Text("Homelab (B)").tag(RuntimeMode.homelab)
                Text("Endpoint (C)").tag(RuntimeMode.endpoint)
                Text("Local (A)").tag(RuntimeMode.local)
            }
            .pickerStyle(.segmented)
            LabeledContent("Endpoint") {
                TextField("endpoint", text: $m.endpoint)
                    .textFieldStyle(.roundedBorder)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
            }
            LabeledContent("Model") {
                TextField("model", text: $m.model)
                    .textFieldStyle(.roundedBorder)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
            }
        }
        .padding()
        .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 12))
    }

    private func artifactCard(_ r: HarnessModel.ArtifactResult) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: r.ok ? "checkmark.seal.fill" : "xmark.octagon.fill")
                    .foregroundStyle(r.ok ? .green : .red)
                Text(r.type).font(.caption.monospaced()).foregroundStyle(.secondary)
                Spacer()
            }
            Text(r.title).font(.headline)
            Text(r.body).font(.callout).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.quaternary.opacity(0.25), in: RoundedRectangle(cornerRadius: 12))
    }
}
