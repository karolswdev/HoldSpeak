import SwiftUI

// Phase 24 (HSM-24-02) — the ONE reusable inline "Runs on" control. The owner's principle: anywhere
// the app touches a model, the resolved profile is SHOWN and CHANGEABLE right there, every time.
// Drop this chip at every model-touch point; in 24-03 it carries an optional override over the
// agent/active default. Here it binds straight to a profile id (e.g. the global active profile).
//
// HSM-15-11: the menu gains a "Your desktop" section — the paired hub's models BY NAME (from the
// synced mesh manifests, node "desktop"), each pinning that model for the run. Unpaired, the
// section stays visible wearing the mesh's blocked state; it never disappears.
struct RunsOnPicker: View {
    @ObservedObject private var cfg = InferenceConfigStore.shared
    @Binding var selectedId: String
    /// When true, an empty `selectedId` means "use the resolved default" and the chip shows it as such
    /// (for per-agent / per-run overrides). When false, the chip always names the selected profile.
    var allowsDefault: Bool = false
    var label: String = "Runs on"

    // The mesh's model availability, cached by the last sync pull (DeskDioramaStage
    // writes it); the peer pairing says whether a desktop run could dial right now.
    @AppStorage("hs.desk.meshModels") private var meshModelsJSON = ""
    @AppStorage("hs.peer.host") private var peerHost = ""
    @AppStorage("hs.peer.name") private var peerName = ""

    private var resolved: RuntimeProfile {
        cfg.profiles.first { $0.id == selectedId } ?? cfg.activeProfile
    }
    private var isDefault: Bool { allowsDefault && selectedId.isEmpty }
    private var paired: Bool { !peerHost.trimmingCharacters(in: .whitespaces).isEmpty }
    private func target(_ profile: RuntimeProfile) -> InferenceTarget {
        profile.inferenceTarget(
            keyPresent: ProfileKeyStore.get(profile.id)?.trimmingCharacters(in: .whitespaces).isEmpty == false,
            paired: paired,
            modelAdvertised: profile.model.isEmpty || hubModels.contains(profile.model)
        )
    }
    private var selectedTarget: InferenceTarget { target(resolved) }

    /// The hub's models by name — only rows the hub itself holds (node "desktop"); a
    /// model some OTHER phone pushed is not runnable there and never listed.
    private var hubModels: [String] {
        guard let data = meshModelsJSON.data(using: .utf8),
              let models = try? JSONDecoder().decode([ModelManifest].self, from: data) else { return [] }
        var seen = Set<String>()
        return models.filter { $0.node == "desktop" && !$0.name.isEmpty && seen.insert($0.name).inserted }
            .map(\.name)
    }

    var body: some View {
        Menu {
            if allowsDefault {
                Button { selectedId = ""; tactile() } label: {
                    pickLabel(target(cfg.activeProfile), on: selectedId.isEmpty)
                }
            }
            ForEach(cfg.profiles.filter { $0.kind != .desktop }) { p in
                let destination = target(p)
                Button { selectedId = p.id; tactile() } label: {
                    pickLabel(destination, on: selectedId == p.id)
                }.disabled(!destination.readiness.available)
            }
            Section(peerName.isEmpty ? "Paired device" : "Paired device · \(peerName)") {
                if hubModels.isEmpty {
                    // Paired but no manifest yet (no pull has landed): the honest row.
                    Label(paired ? "Unavailable · no models synced yet" : "Unavailable · no paired device",
                          systemImage: "desktopcomputer.trianglebadge.exclamationmark")
                } else {
                    ForEach(hubModels, id: \.self) { name in
                        Button {
                            selectedId = cfg.desktopProfile(model: name).id
                            tactile()
                        } label: {
                            Label(name, systemImage: selectedId == "desktop:\(name)" ? "checkmark" : "desktopcomputer")
                        }
                        .disabled(!paired)
                    }
                    if !paired {
                        Label("Unavailable · no paired device", systemImage: "exclamationmark.triangle")
                    }
                }
            }
        } label: {
            HStack(spacing: 7) {
                Image(systemName: chipSymbol).font(.system(size: 11, weight: .bold))
                VStack(alignment: .leading, spacing: 0) {
                    Text(label.uppercased()).font(.system(size: 8.5, weight: .black, design: .rounded)).tracking(0.8).foregroundStyle(Sig.faint)
                    Text(isDefault ? cfg.activeProfile.name : resolved.name)
                        .font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(Sig.text).lineLimit(1)
                    Text("\(kindLabel(selectedTarget.kind)) · \(selectedTarget.boundary)")
                        .font(.system(size: 11, weight: .semibold, design: .rounded))
                        .foregroundStyle(selectedTarget.readiness.available ? Sig.faint : .orange)
                        .lineLimit(2)
                }
                Spacer(minLength: 4)
                Image(systemName: "chevron.up.chevron.down").font(.system(size: 10, weight: .bold)).foregroundStyle(Sig.faint)
            }
            .padding(.horizontal, 12).padding(.vertical, 9)
            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
        }
        .tint(Sig.accent)
    }

    private var chipSymbol: String {
        switch resolved.kind {
        case .onDevice: return "iphone"
        case .desktop: return "desktopcomputer"
        case .openAICompatible: return "cloud.fill"
        case .meshNode: return "antenna.radiowaves.left.and.right"
        }
    }

    private func pickLabel(_ target: InferenceTarget, on: Bool) -> some View {
        Label("\(target.name) · \(kindLabel(target.kind))" +
              (target.readiness.available ? "" : " · \(target.readiness.reason)"),
              systemImage: on ? "checkmark" : symbol(target.kind))
    }

    private func kindLabel(_ kind: InferenceTarget.Kind) -> String {
        switch kind {
        case .thisDevice: return "This device"
        case .pairedDevice: return "Paired device"
        case .privateEndpoint: return "Private endpoint"
        case .meshNode: return "Mesh node"
        case .externalService: return "External service"
        case .unsupported: return "Unsupported"
        }
    }

    private func symbol(_ kind: InferenceTarget.Kind) -> String {
        switch kind {
        case .thisDevice: return "iphone"
        case .pairedDevice: return "desktopcomputer"
        case .privateEndpoint: return "network"
        case .meshNode: return "antenna.radiowaves.left.and.right"
        case .externalService: return "arrow.up.forward.app.fill"
        case .unsupported: return "exclamationmark.triangle"
        }
    }
}
