import SwiftUI
import Foundation
import AVFAudio

// HSM-14-19 "The Desk" decomposition: the Settings surface (where intelligence runs — on-device vs
// LAN endpoint, model/diarization knobs) lifted verbatim out of MeetingCaptureApp.swift. Same module.

// MARK: - Settings (where intelligence runs)

/// The settings surface the owner asked for: choose where a meeting's intelligence runs — fully on
/// this iPad, or against an OpenAI-compatible endpoint on your LAN — and configure + live-test that
/// endpoint. Signal depth throughout; the egress reality is shown plainly, never narrated.
struct SettingsView: View {
    @ObservedObject private var cfg = InferenceConfigStore.shared
    @ObservedObject private var mesh = MeshServeStore.shared     // HSM-25-02 — the serving state line
    @ObservedObject private var peer = DictatePeerStore.shared
    @Environment(\.dismiss) private var dismiss
    @FocusState private var focused: Field?
    @State private var fetch: FetchState = .idle
    @State private var models: [String] = []
    @State private var localModels: [InstalledModel] = []     // installed on-device GGUF language models
    @State private var showModels = false                     // present the model manager (import/delete)
    @State private var showProfiles = false                   // present the runtime-profiles manager (Phase 24)
    @State private var symbolRows: [SymbolRow] = []           // HSM-18-04 — the user symbol dictionary
    @State private var storeHealth: StoreHealth?              // HSM-23-03 — the readiness panel
    @State private var micPermission = ""
    @State private var hubProbe: HubProbe = .idle
    enum Field: Hashable { case url, key }
    enum FetchState: Equatable { case idle, loading, ok(Int), fail }
    enum HubProbe: Equatable { case idle, loading, ok(SetupStatus), fail }

    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            Circle().fill(Sig.local.opacity(0.13)).frame(width: 400).blur(radius: 130)
                .offset(x: -150, y: -300).ignoresSafeArea()
            ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    header
                    label("WHERE INTELLIGENCE RUNS")
                    // The active profile is the default for everything not overridden inline — always exposed.
                    RunsOnPicker(selectedId: $cfg.activeProfileId, label: "Active profile")
                    Button { tactile(); showProfiles = true } label: {
                        HStack(spacing: 8) {
                            Image(systemName: "rectangle.stack.fill").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.accent)
                            Text("Manage profiles").font(.system(size: 13.5, weight: .heavy)).foregroundStyle(Sig.text)
                            Text("\(cfg.profiles.count)").font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.faint)
                            Spacer(); Image(systemName: "chevron.right").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint)
                        }
                        .padding(.horizontal, 13).padding(.vertical, 11)
                        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
                    }
                    targetCard(.local, "This \(DeviceLabel.current)", "Runs on this \(DeviceLabel.current)", DeviceLabel.current == "iPhone" ? "iphone" : "ipad", Sig.localGradient)
                    if cfg.isLocal { onDeviceModelCard }
                    targetCard(.homelab, "LAN endpoint", "An OpenAI-compatible server on your network", "server.rack", Sig.accentGradient)
                    if !cfg.isLocal { endpointCard }
                    egressRow
                    meshServeCard
                    label("TRANSCRIPTION")
                    whisperCard
                    languageCard
                    label("SPOKEN SYMBOLS")
                    symbolsCard
                    label("WHO'S TALKING")
                    diarizeCard
                    label("READINESS").id("readiness")
                    deviceReadinessCard
                    desktopReadinessCard
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
            .onAppear {
                // Screenshot-run affordance (sim only): jump to the readiness
                // section — the same view the scroll gesture reaches.
                #if targetEnvironment(simulator)
                if ProcessInfo.processInfo.environment["HS_DEMO_READINESS"] == "1" {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
                        withAnimation { proxy.scrollTo("readiness", anchor: .top) }
                    }
                }
                #endif
            }
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .onTapGesture { focused = nil }
        .onAppear { refreshLocalModels(); loadSymbolRows(); probeReadiness() }
        .sheet(isPresented: $showModels, onDismiss: { refreshLocalModels() }) { NavigationStack { ModelsView() }.preferredColorScheme(.dark) }
        .sheet(isPresented: $showProfiles) { NavigationStack { ProfilesView() }.preferredColorScheme(.dark) }
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
                            Text("No models on this \(DeviceLabel.current)").font(.system(size: 15.5, weight: .heavy)).foregroundStyle(Sig.text)
                            Text("Tap to download one").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
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

    // HSM-18-03 — the spoken-language picker, mirroring the hub's one-knob model (one setting drives
    // dictation, meetings, and import). "Auto" is Whisper's per-utterance detection; picking a language
    // helps short or code-switching speech. Options come from the vendored WhisperLanguage registry.
    private var languageItems: [(code: String, name: String)] {
        WhisperLanguage.names.map { ($0.key, $0.value) }.sorted { $0.name < $1.name }
    }
    private func languageTitle() -> String {
        let raw = cfg.whisperLanguage
        if raw.isEmpty || raw == "auto" { return "Auto" }
        return WhisperLanguage.names[raw] ?? raw
    }
    private var languageCard: some View {
        HStack(spacing: 14) {
            GlyphChip(system: "globe", gradient: Sig.localGradient, size: 50)
            VStack(alignment: .leading, spacing: 3) {
                Text("Spoken language").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Auto-detects per utterance.").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Menu {
                Button { cfg.whisperLanguage = "auto"; tactile() } label: {
                    Label("Auto (detect)", systemImage: (cfg.whisperLanguage.isEmpty || cfg.whisperLanguage == "auto") ? "checkmark" : "globe")
                }
                ForEach(languageItems, id: \.code) { item in
                    Button { cfg.whisperLanguage = item.code; tactile() } label: {
                        Label(item.name, systemImage: cfg.whisperLanguage == item.code ? "checkmark" : "character.bubble")
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text(languageTitle()).font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text)
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

    // HSM-18-04 — the user spoken-symbol dictionary: your phrases, your symbols, user-wins
    // over the built-ins, one longest-first pass at the speak-to-fill site. Persisted as
    // plain JSON (`SpokenSymbols.userSymbolsKey`); empty = built-ins only, byte-identical.
    struct SymbolRow: Identifiable {
        let id = UUID()
        var spoken = ""
        var symbol = ""
        var attach = "none"
    }

    private static let attachModes: [(mode: String, label: String)] = [
        ("none", "Keep spaces"), ("left", "Attach left"),
        ("right", "Attach right"), ("both", "Attach both"),
    ]

    private func loadSymbolRows() {
        #if targetEnvironment(simulator)
        if ProcessInfo.processInfo.environment["HS_DEMO_SYMBOLS"] == "1" {
            symbolRows = [SymbolRow(spoken: "tilde", symbol: "~"),
                          SymbolRow(spoken: "arrow", symbol: "→"),
                          SymbolRow(spoken: "dash", symbol: "—", attach: "both")]
            return
        }
        #endif
        symbolRows = SpokenSymbols.loadUserSymbols().map {
            SymbolRow(spoken: $0.spoken, symbol: $0.symbol, attach: $0.attach)
        }
    }

    private func persistSymbolRows() {
        SpokenSymbols.saveUserSymbols(symbolRows.compactMap { row in
            let spoken = row.spoken.trimmingCharacters(in: .whitespaces)
            guard !spoken.isEmpty, !row.symbol.isEmpty else { return nil }
            return SpokenSymbols.UserSymbol(spoken: spoken, symbol: row.symbol, attach: row.attach)
        })
    }

    private var symbolsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 14) {
                GlyphChip(system: "character.textbox", gradient: Sig.localGradient, size: 50)
                VStack(alignment: .leading, spacing: 3) {
                    Text("Your symbols").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                    Text("Say the phrase · it types the symbol").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
                }
                Spacer()
            }
            ForEach($symbolRows) { $row in
                HStack(spacing: 8) {
                    MicFillField(placeholder: "spoken phrase", text: $row.spoken)
                    MicFillField(placeholder: "symbol", text: $row.symbol)
                        .frame(maxWidth: 170)
                    Menu {
                        ForEach(Self.attachModes, id: \.mode) { m in
                            Button { row.attach = m.mode; persistSymbolRows(); tactile() } label: {
                                Label(m.label, systemImage: row.attach == m.mode ? "checkmark" : "arrow.left.and.right")
                            }
                        }
                    } label: {
                        Image(systemName: "arrow.left.and.right.square")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundStyle(row.attach == "none" ? Sig.faint : Sig.accent)
                            .frame(width: 34, height: 34)
                            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                    }
                    Button {
                        tactile(.light)
                        symbolRows.removeAll { $0.id == row.id }
                        persistSymbolRows()
                    } label: {
                        Image(systemName: "trash").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
                            .frame(width: 34, height: 34)
                            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
                .onChange(of: row.spoken) { _, _ in persistSymbolRows() }
                .onChange(of: row.symbol) { _, _ in persistSymbolRows() }
            }
            Button { tactile(); withAnimation { symbolRows.append(SymbolRow()) } } label: {
                HStack(spacing: 6) {
                    Image(systemName: "plus.circle.fill").font(.system(size: 13, weight: .bold))
                    Text("Add a symbol").font(.system(size: 13, weight: .heavy))
                }
                .foregroundStyle(Sig.accent)
                .padding(.horizontal, 13).padding(.vertical, 9)
                .background(Sig.accent.opacity(0.1), in: Capsule())
                .overlay(Capsule().strokeBorder(Sig.accent.opacity(0.3), lineWidth: 1))
            }
            .buttonStyle(.plain)
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

    // HSM-25-02 — serving is consent (off by default; the desktop HS-85 rule).
    // The subline is the whole story: the guard's named reason when unarmable,
    // "no hub paired" without a peer, the serving state while on. No prose.
    private var meshServeCard: some View {
        HStack(spacing: 14) {
            GlyphChip(system: "antenna.radiowaves.left.and.right",
                      gradient: Sig.accentGradient, size: 50)
            VStack(alignment: .leading, spacing: 3) {
                Text("Serve my models to the mesh")
                    .font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text(meshServeSubline)
                    .font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Toggle("", isOn: $cfg.meshServeOn).labelsHidden().tint(Sig.accent)
                .disabled(mesh.refusal != nil || !peer.isPaired)
        }
        .padding(15)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    private var meshServeSubline: String {
        if let refusal = mesh.refusal { return refusal }
        if !peer.isPaired { return "no hub paired" }
        guard cfg.meshServeOn else { return "off" }
        let runs = mesh.jobsServed == 1 ? "1 run" : "\(mesh.jobsServed) runs"
        return "serving as \(mesh.node) · \(runs)"
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

    // HSM-23-03 — the readiness panel. The Wave-4 schema safety (refuse-newer +
    // backup-then-apply) finally gets a face: this iPad's half reads the REAL store
    // (same open path the app uses), mic permission, and installed models; the
    // desktop half renders the hub's own doctor sections off /api/setup/status when
    // a peer is paired. Labels state the posture; nothing narrates.
    private var deviceReadinessCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 14) {
                GlyphChip(system: "checkmark.seal.fill", gradient: Sig.localGradient, size: 50)
                VStack(alignment: .leading, spacing: 3) {
                    Text("This \(DeviceLabel.current)").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                    Text("HoldSpeak \(appVersion())").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
                }
                Spacer()
            }
            readinessRow("Store") { storeChip }
            readinessRow("Microphone") { micChip }
            readinessRow("Models") { modelsChip }
        }
        .padding(15).background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    private var desktopReadinessCard: some View {
        let peer = DictatePeerStore.shared
        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 14) {
                GlyphChip(system: "desktopcomputer", gradient: Sig.accentGradient, size: 50)
                VStack(alignment: .leading, spacing: 3) {
                    Text(peer.isPaired ? peer.displayName : "Your desktop")
                        .font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                    if case .ok(let s) = hubProbe, let v = s.version, !v.isEmpty {
                        Text("HoldSpeak \(v)").font(.system(size: 12, weight: .medium)).foregroundStyle(Sig.faint)
                    }
                }
                Spacer()
                switch hubProbe {
                case .idle: chip("not paired", "link", Sig.muted)
                case .loading: ProgressView().controlSize(.small).tint(Sig.accent)
                case .fail: chip("unreachable", "xmark", Sig.bad)
                case .ok(let s): overallChip(s.overall ?? "")
                }
            }
            if case .ok(let s) = hubProbe, let sections = s.sections, !sections.isEmpty {
                ForEach(Array(sections.enumerated()), id: \.offset) { _, section in
                    readinessRow(section.label ?? section.id ?? "check",
                                 detail: section.detail ?? "") { sectionChip(section.status ?? "unknown") }
                }
            }
        }
        .padding(15).background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
    }

    private func readinessRow(_ name: String, detail: String = "",
                              @ViewBuilder trailing: () -> some View) -> some View {
        HStack(spacing: 8) {
            Text(name).font(.system(size: 13.5, weight: .semibold)).foregroundStyle(Sig.text)
            Spacer()
            if !detail.isEmpty {
                Text(detail).font(.system(size: 11, weight: .medium)).foregroundStyle(Sig.faint).lineLimit(1)
            }
            trailing()
        }
        .padding(.horizontal, 13).padding(.vertical, 10)
        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder private var storeChip: some View {
        switch storeHealth?.state {
        case .none:
            ProgressView().controlSize(.small).tint(Sig.accent)
        case .ok(let schema, let integrityOK):
            if let n = storeHealth?.backupCount, n > 0 {
                chip("\(n) backup\(n == 1 ? "" : "s")", "clock.arrow.circlepath", Sig.muted)
            }
            if integrityOK { chip("ok · schema v\(schema)", "checkmark", Sig.ok) }
            else { chip("integrity failed · schema v\(schema)", "xmark", Sig.bad) }
        case .missing:
            chip("not created yet", "circle.dashed", Sig.muted)
        case .refusedNewer(let stored, let build):
            chip("newer than this app · v\(stored) > v\(build)", "exclamationmark.triangle.fill", Sig.warn)
        case .failed:
            chip("unavailable", "xmark", Sig.bad)
        }
    }

    private var micChip: some View {
        switch micPermission {
        case "granted": chip("granted", "checkmark", Sig.ok)
        case "denied": chip("denied", "xmark", Sig.bad)
        default: chip("not asked yet", "questionmark", Sig.muted)
        }
    }

    private var modelsChip: some View {
        localModels.isEmpty
            ? chip("none on device", "circle.dashed", Sig.muted)
            : chip("\(localModels.count) on device", "checkmark", Sig.ok)
    }

    private func overallChip(_ overall: String) -> some View {
        switch overall {
        case "ready": chip("Ready", "checkmark", Sig.ok)
        case "needs_attention": chip("Needs attention", "exclamationmark.triangle.fill", Sig.warn)
        case "blocked": chip("Blocked", "xmark", Sig.bad)
        default: chip(overall.isEmpty ? "unknown" : overall, "questionmark", Sig.muted)
        }
    }

    private func sectionChip(_ status: String) -> some View {
        switch status {
        case "pass": chip("pass", "checkmark", Sig.ok)
        case "warn": chip("warn", "exclamationmark.triangle.fill", Sig.warn)
        case "fail": chip("fail", "xmark", Sig.bad)
        default: chip("unknown", "questionmark", Sig.muted)
        }
    }

    private func appVersion() -> String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "dev"
    }

    private func probeReadiness() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let path = docs.appendingPathComponent("meetings.sqlite").path
        Task.detached {
            let health = StoreHealthProbe.probe(path: path)
            await MainActor.run { withAnimation { storeHealth = health } }
        }
        switch AVAudioApplication.shared.recordPermission {
        case .granted: micPermission = "granted"
        case .denied: micPermission = "denied"
        default: micPermission = ""
        }
        guard let client = DictatePeerStore.shared.client() else { hubProbe = .idle; return }
        hubProbe = .loading
        Task {
            do {
                let status = try await client.setupStatus()
                await MainActor.run { withAnimation { hubProbe = .ok(status) } }
            } catch {
                await MainActor.run { withAnimation { hubProbe = .fail } }
            }
        }
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
