import SwiftUI
import Foundation

// HSM-14-19 "The Desk" decomposition: the Settings surface (where intelligence runs — on-device vs
// LAN endpoint, model/diarization knobs) lifted verbatim out of MeetingCaptureApp.swift. Same module.

// MARK: - Settings (where intelligence runs)

/// The settings surface the owner asked for: choose where a meeting's intelligence runs — fully on
/// this iPad, or against an OpenAI-compatible endpoint on your LAN — and configure + live-test that
/// endpoint. Signal depth throughout; the egress reality is shown plainly, never narrated.
struct SettingsView: View {
    @ObservedObject private var cfg = InferenceConfigStore.shared
    @Environment(\.dismiss) private var dismiss
    @FocusState private var focused: Field?
    @State private var fetch: FetchState = .idle
    @State private var models: [String] = []
    @State private var localModels: [InstalledModel] = []     // installed on-device GGUF language models
    @State private var showModels = false                     // present the model manager (import/delete)
    enum Field: Hashable { case url, key }
    enum FetchState: Equatable { case idle, loading, ok(Int), fail }

    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.local.opacity(0.13)).frame(width: 400).blur(radius: 130)
                .offset(x: -150, y: -300).ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    header
                    label("WHERE INTELLIGENCE RUNS")
                    targetCard(.local, "This iPad", "Fully on-device · nothing ever leaves", "ipad", Sig.localGradient)
                    if cfg.isLocal { onDeviceModelCard }
                    targetCard(.homelab, "LAN endpoint", "An OpenAI-compatible server on your network", "server.rack", Sig.accentGradient)
                    if !cfg.isLocal { endpointCard }
                    egressRow
                    label("TRANSCRIPTION")
                    whisperCard
                    label("WHO'S TALKING")
                    diarizeCard
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .onTapGesture { focused = nil }
        .onAppear { refreshLocalModels() }
        .sheet(isPresented: $showModels, onDismiss: { refreshLocalModels() }) { NavigationStack { ModelsView() }.preferredColorScheme(.dark) }
    }

    private func refreshLocalModels() { localModels = ModelFiles.installed().filter { $0.kind == .language } }
    private func selectedLocalName() -> String {
        if let m = localModels.first(where: { $0.id == cfg.localModelId }) { return m.name }
        return localModels.first?.name ?? ""
    }

    // ON-DEVICE MODEL — pick which installed .gguf runs local intelligence, or import one. The desk's
    // AI core uses exactly this choice (callLLM resolves cfg.localModelId → its path).
    private var onDeviceModelCard: some View {
        VStack(alignment: .leading, spacing: 11) {
            HStack(spacing: 8) {
                Text("ON-DEVICE MODEL").font(.system(size: 10, weight: .heavy)).tracking(0.8).foregroundStyle(Sig.faint)
                Spacer()
                Text("\(localModels.count) installed").font(.system(size: 10, weight: .heavy)).foregroundStyle(Sig.faint)
            }
            if localModels.isEmpty {
                Button { tactile(); showModels = true } label: {
                    HStack(spacing: 10) {
                        GlyphChip(system: "tray.and.arrow.down.fill", gradient: Sig.accentGradient, size: 42)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("No models on this iPad").font(.system(size: 15.5, weight: .heavy)).foregroundStyle(Sig.text)
                            Text("Import a .gguf to run intelligence on-device").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
                        }
                        Spacer(); Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
                    }
                }.buttonStyle(PressableCard())
            } else {
                HStack(spacing: 8) {
                    Menu {
                        ForEach(localModels) { m in
                            Button { cfg.localModelId = m.id; tactile() } label: {
                                Label(m.name, systemImage: cfg.localModelId == m.id || (cfg.localModelId.isEmpty && m.id == localModels.first?.id) ? "checkmark" : "brain.head.profile")
                            }
                        }
                    } label: {
                        HStack {
                            Image(systemName: "brain.head.profile").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.accent)
                            Text(selectedLocalName()).font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text).lineLimit(1)
                            Spacer(); Image(systemName: "chevron.up.chevron.down").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
                        }
                        .padding(.horizontal, 13).padding(.vertical, 12)
                        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
                    }
                    Button { tactile(); showModels = true } label: {
                        Image(systemName: "slider.horizontal.3").font(.system(size: 18, weight: .bold)).foregroundStyle(.black)
                            .frame(width: 48, height: 48).background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 13, style: .continuous))
                    }.buttonStyle(PressableCard()).accessibilityLabel("Manage models")
                }
            }
        }
        .padding(16).signalCard(radius: 20)
        .transition(.asymmetric(insertion: .scale(scale: 0.96).combined(with: .opacity), removal: .opacity))
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("SETTINGS").font(.system(size: 10, weight: .heavy)).tracking(1.6).foregroundStyle(Sig.accent)
                Text("Intelligence").font(.system(size: 32, weight: .heavy)).foregroundStyle(Sig.text)
            }
            Spacer()
            Button { dismiss() } label: {
                Image(systemName: "xmark").font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                    .frame(width: 44, height: 44).signalCard(Sig.s2, radius: 14)
            }.buttonStyle(PressableCard())
        }.padding(.top, 6)
    }

    private func label(_ s: String) -> some View {
        Text(s).font(.system(size: 11, weight: .heavy)).tracking(1.4).foregroundStyle(Sig.faint).padding(.leading, 2).padding(.top, 4)
    }

    private func targetCard(_ m: RuntimeMode, _ title: String, _ sub: String, _ glyph: String, _ g: LinearGradient) -> some View {
        let sel = (m == .local) == cfg.isLocal
        return Button {
            tactile(); withAnimation(.spring(response: 0.42, dampingFraction: 0.8)) { cfg.mode = m; fetch = .idle }
        } label: {
            HStack(spacing: 14) {
                GlyphChip(system: glyph, gradient: g, size: 50)
                VStack(alignment: .leading, spacing: 3) {
                    Text(title).font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                    Text(sub).font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
                }
                Spacer()
                Image(systemName: sel ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 22, weight: .bold)).foregroundStyle(sel ? Sig.accent : Sig.faint)
            }
            .padding(15)
            .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous)
                .strokeBorder(sel ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.topHairline), lineWidth: sel ? 2 : 1))
            .shadow(color: .black.opacity(0.34), radius: sel ? 16 : 8, y: sel ? 9 : 5)
        }.buttonStyle(PressableCard())
    }

    private var endpointCard: some View {
        VStack(alignment: .leading, spacing: 13) {
            field("ENDPOINT URL", $cfg.endpointURL, "http://192.168.1.43:8080/v1", .url, keyboard: .URL)
            modelRow
            field("API KEY (OPTIONAL)", $cfg.endpointKey, "Bearer token, if your server needs one", .key, secure: true)
        }
        .padding(16).signalCard(radius: 20)
        .transition(.asymmetric(insertion: .scale(scale: 0.96).combined(with: .opacity), removal: .opacity))
    }

    // The model is PICKED from what the endpoint actually serves (GET /v1/models) — never typed.
    // The fetch button doubles as the reachability check; states stay tight (no prose).
    private var modelRow: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("MODEL").font(.system(size: 10, weight: .heavy)).tracking(0.8).foregroundStyle(Sig.faint)
                Spacer()
                statusChip
            }
            HStack(spacing: 8) {
                Menu {
                    ForEach(models, id: \.self) { m in Button(m) { cfg.endpointModel = m; tactile() } }
                } label: {
                    HStack {
                        Text(cfg.endpointModel.isEmpty ? "Fetch to choose" : cfg.endpointModel)
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundStyle(cfg.endpointModel.isEmpty ? Sig.faint : Sig.text).lineLimit(1)
                        Spacer()
                        Image(systemName: "chevron.up.chevron.down").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
                    }
                    .padding(.horizontal, 13).padding(.vertical, 12)
                    .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
                }
                .disabled(models.isEmpty)

                Button { fetchModels() } label: {
                    Image(systemName: "arrow.down.circle.fill").font(.system(size: 20, weight: .bold)).foregroundStyle(.black)
                        .frame(width: 48, height: 48)
                        .background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 13, style: .continuous))
                        .opacity(cfg.endpointConfig == nil ? 0.5 : 1)
                }
                .buttonStyle(PressableCard())
                .disabled(cfg.endpointConfig == nil || fetch == .loading)
                .accessibilityLabel("Fetch models from endpoint")
            }
        }
    }

    @ViewBuilder private var statusChip: some View {
        switch fetch {
        case .loading: ProgressView().controlSize(.small).tint(Sig.accent)
        case .ok(let n): chip("\(n) found", "checkmark", Sig.ok)
        case .fail: chip("no connection", "xmark", Sig.bad)
        case .idle: EmptyView()
        }
    }

    private func chip(_ t: String, _ icon: String, _ c: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.system(size: 9, weight: .black))
            Text(t).font(.system(size: 10, weight: .heavy))
        }
        .foregroundStyle(c).padding(.horizontal, 7).padding(.vertical, 3).background(c.opacity(0.16), in: Capsule())
    }

    private func field(_ l: String, _ text: Binding<String>, _ placeholder: String, _ f: Field,
                       keyboard: UIKeyboardType = .default, secure: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(l).font(.system(size: 10, weight: .heavy)).tracking(0.8).foregroundStyle(Sig.faint)
            Group {
                if secure { SecureField("", text: text, prompt: Text(placeholder).foregroundColor(Sig.faint)) }
                else { TextField("", text: text, prompt: Text(placeholder).foregroundColor(Sig.faint)) }
            }
            .focused($focused, equals: f)
            .keyboardType(keyboard).textInputAutocapitalization(.never).autocorrectionDisabled()
            .font(.system(size: 15, weight: .medium)).foregroundStyle(Sig.text)
            .padding(.horizontal, 13).padding(.vertical, 12)
            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous)
                .strokeBorder(focused == f ? Sig.accent : Color.white.opacity(0.08), lineWidth: focused == f ? 1.5 : 1))
        }
    }

    // The WhisperKit speech model for recording + import. Bigger = sharper but slower + a larger one-time
    // download on first use. Read by the capture transcriber from UserDefaults on the next recording.
    private struct WhisperOpt: Identifiable { let id: String; let title: String; let hint: String }
    private var whisperOpts: [WhisperOpt] { [
        .init(id: "tiny", title: "Tiny", hint: "Fastest · roughest"),
        .init(id: "base", title: "Base", hint: "Balanced · the default"),
        .init(id: "small", title: "Small", hint: "Sharper · slower · bigger download"),
        .init(id: "large-v3", title: "Large v3", hint: "Best · slowest · large download"),
    ] }
    private func whisperTitle() -> String { whisperOpts.first { $0.id == cfg.whisperModel }?.title ?? cfg.whisperModel }
    private func whisperHint() -> String { whisperOpts.first { $0.id == cfg.whisperModel }?.hint ?? "Bigger = sharper but slower" }

    private var whisperCard: some View {
        HStack(spacing: 14) {
            GlyphChip(system: "waveform.badge.mic", gradient: Sig.localGradient, size: 50)
            VStack(alignment: .leading, spacing: 3) {
                Text("Speech model").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text(whisperHint()).font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Menu {
                ForEach(whisperOpts) { o in
                    Button { cfg.whisperModel = o.id; tactile() } label: {
                        Label("\(o.title) — \(o.hint)", systemImage: cfg.whisperModel == o.id ? "checkmark" : "waveform")
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text(whisperTitle()).font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text)
                    Image(systemName: "chevron.up.chevron.down").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
                }
                .padding(.horizontal, 13).padding(.vertical, 11)
                .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
            }
        }
        .padding(15).background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    // HSM-14-17 — the opt-in diarization toggle. Fully on-device; the egress badge below the toggle
    // says so plainly (no prose). Default ON.
    private var diarizeCard: some View {
        HStack(spacing: 14) {
            GlyphChip(system: "person.2.wave.2.fill", gradient: Sig.localGradient, size: 50)
            VStack(alignment: .leading, spacing: 3) {
                Text("Identify speakers (on-device)").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Label each line with who spoke it").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Toggle("", isOn: $cfg.diarizationOn).labelsHidden().tint(Sig.accent)
        }
        .padding(15)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    private var egressRow: some View {
        HStack(spacing: 8) {
            Image(systemName: cfg.isLocal ? "lock.shield.fill" : "antenna.radiowaves.left.and.right")
                .font(.system(size: 12, weight: .bold))
            Text(cfg.egressLabel).font(.system(size: 12, weight: .heavy))
        }
        .foregroundStyle(cfg.isLocal ? Sig.local : Sig.accent)
        .padding(.horizontal, 12).padding(.vertical, 8)
        .background((cfg.isLocal ? Sig.local : Sig.accent).opacity(0.12), in: Capsule())
        .padding(.top, 4)
    }

    private func fetchModels() {
        guard cfg.endpointConfig != nil else { return }
        focused = nil; withAnimation { fetch = .loading }; tactile()
        Task {
            do {
                let ms = try await cfg.fetchModels()
                await MainActor.run {
                    models = ms
                    if cfg.endpointModel.isEmpty || !ms.contains(cfg.endpointModel) { cfg.endpointModel = ms.first ?? cfg.endpointModel }
                    withAnimation { fetch = .ok(ms.count) }; tactile(.medium)
                }
            } catch {
                await MainActor.run { withAnimation { fetch = .fail } ; tactile(.heavy) }
            }
        }
    }
}
