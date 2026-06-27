import SwiftUI

// HSM-14 — harness @main app that renders the REAL MG_Reflex (the app's reflex mini-game) in a small
// ~260x300 frosted ephemeral pane, exactly as the launcher will host it, for Simulator screenshots.
// It compiles App/MeetingCapture/DeskMiniGame_Reflex.swift unchanged alongside this file. The game's
// own Color(hex:) is gated behind HS_MG_REFLEX_STANDALONE (so it is defined exactly once here for the
// standalone build), avoiding a duplicate-symbol clash with the desk's definition in the real app.

private enum HPal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let violet = Color(hex: 0x9B6BFF), text = Color(hex: 0xF4ECE0)
}

// The frosted ephemeral window + close button the LAUNCHER supplies (the game draws none of this itself).
struct HostPane: View {
    var body: some View {
        ZStack {
            // a believable desk backdrop so the frosted pane reads through (Law 1 — the desk stays visible)
            LinearGradient(colors: [HPal.bgTop, HPal.bgMid, HPal.bgBot], startPoint: .topLeading, endPoint: .bottomTrailing)
                .ignoresSafeArea()
            // a couple of soft desk glows behind the pane
            Circle().fill(RadialGradient(colors: [Color(hex: 0xFF6B35).opacity(0.18), .clear], center: .center, startRadius: 2, endRadius: 220))
                .frame(width: 360, height: 360).offset(x: -120, y: -240)
            Circle().fill(RadialGradient(colors: [Color(hex: 0x5B8DEF).opacity(0.16), .clear], center: .center, startRadius: 2, endRadius: 220))
                .frame(width: 360, height: 360).offset(x: 130, y: 260)

            // the ephemeral frosted pane (the launcher's chrome)
            ZStack(alignment: .topTrailing) {
                MG_Reflex(seedMidGame: true)
                    .frame(width: 260, height: 300)

                // launcher's close button (top-right), drawn OVER the game content
                Image(systemName: "xmark")
                    .font(.system(size: 11, weight: .black))
                    .foregroundStyle(HPal.text.opacity(0.9))
                    .frame(width: 28, height: 28)
                    .background(Circle().fill(.white.opacity(0.10)))
                    .padding(8)
            }
            .frame(width: 260, height: 300)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(HPal.violet.opacity(0.05)))
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                    .shadow(color: .black.opacity(0.4), radius: 18, y: 10)
            )
        }
    }
}

@main
struct ReflexHarnessApp: App {
    var body: some Scene {
        WindowGroup { HostPane() }
    }
}
