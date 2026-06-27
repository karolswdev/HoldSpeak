import SwiftUI

// HSM-14 — self-contained Simulator harness for the WORD mini-game (MG_Word). Mirrors the diorama harness:
// it copies the desk palette locally (DioPal + Color(hex:)) so DeskMiniGame_Word.swift compiles standalone,
// renders MG_Word inside a launcher-shaped ephemeral frosted window (~260x320) on the desk gradient, and is
// shot via simctl. The real launcher supplies the window + close; here we draw a faux one to judge the fit.

// Copied locally from DeskDioramaStage.swift / Diorama.swift (no global mechanism duplicated into the app).
extension Color {
    init(hex: UInt, a: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: a)
    }
}

enum DioPal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let trayTop = Color(hex: 0x1B1626), trayBot = Color(hex: 0x0C0A12)
    static let accent = Color(hex: 0xFF6B35), cobalt = Color(hex: 0x5B8DEF), violet = Color(hex: 0x9B6BFF)
    static let mint = Color(hex: 0x3ECF8E), text = Color(hex: 0xF4ECE0), muted = Color(hex: 0x9C93A8)
}

// A faux launcher window so the screenshot shows MG_Word at its real size, framed the way the desk frames it.
struct HarnessStage: View {
    private let winW: CGFloat = 260
    private let winH: CGFloat = 320
    var body: some View {
        ZStack {
            // the desk behind the ephemeral window (Law 1 — the desk stays visible)
            LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .topLeading, endPoint: .bottomTrailing)
                .ignoresSafeArea()
            // a hint of desk clutter so the frosting has something to read through
            Canvas { ctx, size in
                for i in 0..<40 {
                    let s = Double(i)
                    let x = (sin(s * 1.7) * 0.5 + 0.5) * size.width
                    let y = (cos(s * 2.3) * 0.5 + 0.5) * size.height
                    ctx.opacity = 0.05
                    ctx.fill(Path(ellipseIn: CGRect(x: x, y: y, width: 3, height: 3)), with: .color(.white))
                }
            }.ignoresSafeArea()

            // the launcher-supplied ephemeral window (frosted pane + hairline + soft shadow + a close)
            VStack(spacing: 0) {
                MG_Word()
            }
            .frame(width: winW, height: winH)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(DioPal.violet.opacity(0.05)))
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                    .shadow(color: .black.opacity(0.32), radius: 14, y: 8)
            )
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay(alignment: .topTrailing) {
                // the launcher's close affordance (not the game's)
                Image(systemName: "xmark").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.text.opacity(0.85))
                    .frame(width: 26, height: 26).background(Circle().fill(.white.opacity(0.10)))
                    .offset(x: 13, y: -13)
            }
        }
    }
}

@main
struct MGWordHarnessApp: App {
    var body: some Scene { WindowGroup { HarnessStage() } }
}
