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
                    targetCard(.homelab, "LAN endpoint", "An OpenAI-compatible server on your network", "server.rack", Sig.accentGradient)
                    if !cfg.isLocal { endpointCard }
                    egressRow
                    label("WHO'S TALKING")
                    diarizeCard
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .onTapGesture { focused = nil }
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
