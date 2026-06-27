import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM — harness for the LOGIC mini-game (MG_Logic / "Tenfold"). Renders the game inside an ephemeral frosted
// window (~280x320) floating on a desk-like backdrop, exactly as the desk launcher would. swiftc + simctl,
// portrait, iPad Air 11-inch (M4). Set HS_MG_LOGIC=seed to stage a mid-draw board for the screenshot.

private extension Color {
    init(hexH: UInt) {
        self.init(.sRGB, red: Double((hexH >> 16) & 0xFF) / 255, green: Double((hexH >> 8) & 0xFF) / 255,
                  blue: Double(hexH & 0xFF) / 255, opacity: 1)
    }
}

struct HarnessRoot: View {
    private let winW: CGFloat = 280
    private let winH: CGFloat = 320
    var body: some View {
        ZStack {
            // a desk-like backdrop so the frosted window reads as floating ON the desk
            LinearGradient(colors: [Color(hexH: 0x0B0D12), Color(hexH: 0x16111F), Color(hexH: 0x090A0E)],
                           startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()
            // faint desk furniture behind the glass to prove transparency
            VStack(spacing: 24) {
                ForEach(0..<3, id: \.self) { r in
                    HStack(spacing: 24) {
                        ForEach(0..<3, id: \.self) { c in
                            RoundedRectangle(cornerRadius: 18, style: .continuous)
                                .fill(Color.white.opacity(0.03))
                                .frame(width: 120, height: 90)
                                .overlay(RoundedRectangle(cornerRadius: 18).strokeBorder(.white.opacity(0.05), lineWidth: 1))
                        }
                    }
                }
            }

            // THE EPHEMERAL WINDOW (launcher-provided in the real app) — frosted, hairline edge, soft shadow.
            MG_Logic()
                .frame(width: winW, height: winH)
                .background(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .fill(.ultraThinMaterial)
                        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).fill(Color(hexH: 0x9B6BFF).opacity(0.05)))
                        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                        .shadow(color: .black.opacity(0.32), radius: 16, y: 8)
                )
        }
    }
}

@main
struct MGLogicHarnessApp: App {
    var body: some Scene { WindowGroup { HarnessRoot() } }
}
