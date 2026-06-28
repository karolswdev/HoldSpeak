import SwiftUI

// Phase 24 (HSM-24-02) — the ONE reusable inline "Runs on" control. The owner's principle: anywhere
// the app touches a model, the resolved profile is SHOWN and CHANGEABLE right there, every time.
// Drop this chip at every model-touch point; in 24-03 it carries an optional override over the
// agent/active default. Here it binds straight to a profile id (e.g. the global active profile).
struct RunsOnPicker: View {
    @ObservedObject private var cfg = InferenceConfigStore.shared
    @Binding var selectedId: String
    /// When true, an empty `selectedId` means "use the resolved default" and the chip shows it as such
    /// (for per-agent / per-run overrides). When false, the chip always names the selected profile.
    var allowsDefault: Bool = false
    var label: String = "Runs on"

    private var resolved: RuntimeProfile {
        cfg.profiles.first { $0.id == selectedId } ?? cfg.activeProfile
    }
    private var isDefault: Bool { allowsDefault && selectedId.isEmpty }

    var body: some View {
        Menu {
            if allowsDefault {
                Button { selectedId = ""; tactile() } label: { pickLabel("Default · \(cfg.activeProfile.name)", on: selectedId.isEmpty) }
            }
            ForEach(cfg.profiles) { p in
                Button { selectedId = p.id; tactile() } label: { pickLabel(p.name, on: selectedId == p.id) }
            }
        } label: {
            HStack(spacing: 7) {
                Image(systemName: resolved.isLocal ? "iphone" : "cloud.fill").font(.system(size: 11, weight: .bold))
                VStack(alignment: .leading, spacing: 0) {
                    Text(label.uppercased()).font(.system(size: 8.5, weight: .black, design: .rounded)).tracking(0.8).foregroundStyle(Sig.faint)
                    Text(isDefault ? "Default · \(resolved.name)" : resolved.name)
                        .font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(Sig.text).lineLimit(1)
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

    private func pickLabel(_ name: String, on: Bool) -> some View {
        Label(name, systemImage: on ? "checkmark" : (resolved.isLocal ? "iphone" : "cloud.fill"))
    }
}
