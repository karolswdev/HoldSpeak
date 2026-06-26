import SwiftUI

// HSM-14-19 — "The Desk" decomposition, step 1: the Signal design system, lifted verbatim out of the
// 8,000-line MeetingCaptureApp.swift into its own module file. Access widened from `private`
// (file-scoped) to module-internal so every app/primitive file in this build shares ONE design system.
// Behaviour is unchanged; this is a move, not a rewrite. `tactile()` stays in the app file (now internal).

enum SigN {
    static let s1 = Color(.sRGB, red: 0x15/255, green: 0x17/255, blue: 0x1D/255, opacity: 1)
    static let line = Color.white.opacity(0.07)
    static let muted = Color(.sRGB, red: 0x9B/255, green: 0xA2/255, blue: 0xB0/255, opacity: 1)
    static let faint = Color(.sRGB, red: 0x76/255, green: 0x7E/255, blue: 0x8D/255, opacity: 1)
    static let accent = Color(.sRGB, red: 0xFF/255, green: 0x6B/255, blue: 0x35/255, opacity: 1)
}

// MARK: - Signal palette

enum Sig {
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
    static let local = Color(hex: 0x5B8DEF)
}
extension Color {
    init(hex: UInt) { self.init(.sRGB, red: Double((hex >> 16) & 0xFF)/255,
                                green: Double((hex >> 8) & 0xFF)/255, blue: Double(hex & 0xFF)/255, opacity: 1) }
}

// MARK: - Signal depth + motion (HSM-14 craft elevation)

extension Sig {
    static let bgTop = Color(hex: 0x191B23)
    /// A cinematic vertical wash — depth instead of a flat fill.
    static var bgGradient: LinearGradient {
        LinearGradient(colors: [bgTop, bg], startPoint: .top, endPoint: .bottom)
    }
    /// The brand accent as a warm diagonal gradient (amber → ember) for hero surfaces.
    static var accentGradient: LinearGradient {
        LinearGradient(colors: [Color(hex: 0xFF9D5C), accent, Color(hex: 0xF24A2E)],
                       startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    static var accentSoft: Color { accent.opacity(0.15) }
    static var localGradient: LinearGradient {
        LinearGradient(colors: [Color(hex: 0x7AA6FF), local], startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    /// A top-lit hairline so cards catch light at the top edge (glass realism).
    static var topHairline: LinearGradient {
        LinearGradient(colors: [Color.white.opacity(0.12), Color.white.opacity(0.035)],
                       startPoint: .top, endPoint: .bottom)
    }
}

/// Elevated Signal surface: layered fill + a top-lit hairline + a soft drop shadow. The one card
/// treatment the whole app shares, so elevation is consistent (not random shadow values).
struct SignalCard: ViewModifier {
    var fill: Color = Sig.s1
    var radius: CGFloat = 18
    var elevated: Bool = true
    func body(content: Content) -> some View {
        content
            .background(fill, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(Sig.topHairline, lineWidth: 1))
            .shadow(color: .black.opacity(elevated ? 0.38 : 0), radius: elevated ? 16 : 0, y: elevated ? 9 : 0)
    }
}
extension View {
    func signalCard(_ fill: Color = Sig.s1, radius: CGFloat = 18, elevated: Bool = true) -> some View {
        modifier(SignalCard(fill: fill, radius: radius, elevated: elevated))
    }
}

/// A guaranteed escape hatch. Any pushed screen that hides the nav bar MUST carry one, or you get
/// trapped (the bug the owner hit on device). A clear top-leading "Back" chip wired to an action.
struct BackChip: View {
    let action: () -> Void
    var label: String = "Back"
    var body: some View {
        Button { tactile(); action() } label: {
            HStack(spacing: 5) {
                Image(systemName: "chevron.left").font(.system(size: 14, weight: .heavy))
                Text(label).font(.system(size: 15, weight: .bold))
            }
            .foregroundStyle(Sig.text)
            .padding(.horizontal, 14).padding(.vertical, 9)
            .background(.ultraThinMaterial, in: Capsule())
            .overlay(Capsule().strokeBorder(Sig.topHairline, lineWidth: 1))
            .shadow(color: .black.opacity(0.4), radius: 8, y: 3)
        }.buttonStyle(PressableCard())
    }
}
extension View {
    /// Overlay a guaranteed top-leading back control over the safe area.
    func topBack(label: String = "Back", _ action: @escaping () -> Void) -> some View {
        overlay(alignment: .topLeading) {
            BackChip(action: action, label: label).padding(.top, 10).padding(.leading, 16)
        }
    }
}

/// A gradient-filled rounded glyph chip — the consistent icon container across rows/CTAs.
struct GlyphChip: View {
    let system: String
    var gradient: LinearGradient = Sig.localGradient
    var size: CGFloat = 46
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.28, style: .continuous).fill(gradient)
                .shadow(color: .black.opacity(0.25), radius: 5, y: 3)
            Image(systemName: system).font(.system(size: size * 0.42, weight: .bold)).foregroundStyle(.white)
        }.frame(width: size, height: size)
    }
}

/// Press feedback every tappable card shares: a subtle scale + dim on a spring (HIG scale-feedback).
struct PressableCard: ButtonStyle {
    var scale: CGFloat = 0.975
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? scale : 1)
            .opacity(configuration.isPressed ? 0.94 : 1)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: configuration.isPressed)
    }
}
