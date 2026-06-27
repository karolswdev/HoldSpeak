import SwiftUI

// HSM-14 — standalone harness for MG_Aim (Orbit Gate). Renders the game in a small ephemeral-window-sized
// pane (~260x320) like the launcher would, on a desk-ish backdrop, so we can swiftc + simctl screenshot it.
// The real DeskMiniGame_Aim.swift is copied in alongside this file by the shot script (compiled with
// -DHS_MG_AIM_STANDALONE so its file-local Color(hex:) is available).

@main
struct AimHarnessApp: App {
    var body: some Scene {
        WindowGroup { HarnessRoot() }
    }
}

private struct HarnessRoot: View {
    var body: some View {
        ZStack {
            // a desk-ish dark gradient so the frosted launcher window reads against it
            LinearGradient(colors: [Color(hex: 0x0B0D12), Color(hex: 0x16111F), Color(hex: 0x090A0E)],
                           startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            // the ephemeral launcher window the council contract describes: frosted pane + close affordance,
            // supplied by the LAUNCHER (not the game). The game just fills it.
            VStack(spacing: 0) {
                HStack {
                    Image(systemName: MG_Aim.icon).font(.system(size: 13, weight: .bold)).foregroundStyle(Color(hex: 0x9B6BFF))
                    Text(MG_Aim.title).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(Color(hex: 0xF4ECE0))
                    Spacer()
                    Image(systemName: "xmark").font(.system(size: 11, weight: .black)).foregroundStyle(Color(hex: 0xF4ECE0).opacity(0.8))
                        .frame(width: 26, height: 26).background(Circle().fill(.white.opacity(0.08)))
                }
                .padding(.horizontal, 14).frame(height: 40)

                MG_Aim()
                    .frame(width: 260, height: 320)
            }
            .frame(width: 260, height: 360)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                    .shadow(color: .black.opacity(0.4), radius: 16, y: 8)
            )
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        }
    }
}
