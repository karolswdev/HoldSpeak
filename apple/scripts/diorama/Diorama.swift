import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — "THE DESK", reborn as a premium 2.5D DIORAMA (owner direction: rethink the approach — the
// hand-rolled real-time 3D read as alpha). A crafted, art-directed desk that recedes into space; the
// bespoke PixelLab objects (cassette = meeting, AI-core cartridge = model, crystal = knowledge) rest on
// it with real grounding shadows, warm lamp light, depth, and elegant zone trays. Composed + verified in
// the iOS Simulator (full fidelity), not guessed in a dark offscreen renderer.

extension Color {
    init(hex: UInt, alpha: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: alpha)
    }
}

enum Pal {
    static let wallTop   = Color(hex: 0x140F0C)
    static let wallBot   = Color(hex: 0x241913)
    static let deskBack  = Color(hex: 0x2A1D15)
    static let deskFront = Color(hex: 0x43301F)
    static let deskEdge  = Color(hex: 0x1C130C)
    static let lamp      = Color(hex: 0xFFCB8A)
    static let accent    = Color(hex: 0xFF6B35)
    static let cobalt    = Color(hex: 0x5B8DEF)
    static let violet    = Color(hex: 0x9B6BFF)
    static let text      = Color(hex: 0xF4ECE0)
    static let muted     = Color(hex: 0xB7A892)
}

struct Sprite: View {
    let name: String
    var size: CGFloat = 120
    var body: some View {
        if let path = Bundle.main.path(forResource: name, ofType: "png"), let ui = UIImage(contentsOfFile: path) {
            Image(uiImage: ui).interpolation(.none).resizable().scaledToFit().frame(width: size, height: size)
        } else {
            RoundedRectangle(cornerRadius: 12).fill(.gray.opacity(0.3)).frame(width: size, height: size)
                .overlay(Text(name).font(.system(size: 10)).foregroundStyle(.white))
        }
    }
}

// An object resting on the desk: a soft contact shadow grounds it, a gentle float lifts it, a glow halo
// (optional) gives capability objects presence, and an elegant name plate sits beneath.
struct DeskItem: View {
    let sprite: String
    var size: CGFloat = 130
    let title: String
    var sub: String = ""
    var tint: Color = Pal.accent
    var glow: Bool = false
    var lift: CGFloat = 0
    var tilt: Double = 0
    var body: some View {
        VStack(spacing: 9) {
            ZStack {
                // contact shadow on the desk
                Ellipse().fill(.black.opacity(0.42)).frame(width: size * 0.82, height: size * 0.22)
                    .blur(radius: 10).offset(y: size * 0.46)
                if glow {
                    Circle().fill(RadialGradient(colors: [tint.opacity(0.55), .clear], center: .center, startRadius: 2, endRadius: size * 0.7))
                        .frame(width: size * 1.5, height: size * 1.5).blur(radius: 8)
                }
                Sprite(name: sprite, size: size)
                    .rotationEffect(.degrees(tilt))
                    .shadow(color: .black.opacity(0.5), radius: 12, y: 9)
                    .offset(y: -lift)
            }
            .frame(height: size * 1.15)
            VStack(spacing: 1) {
                Text(title).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text)
                if !sub.isEmpty { Text(sub).font(.system(size: 10.5, weight: .bold, design: .rounded)).foregroundStyle(Pal.muted) }
            }
            .padding(.horizontal, 12).padding(.vertical, 6)
            .background(Capsule().fill(.black.opacity(0.34)).overlay(Capsule().strokeBorder(tint.opacity(0.35), lineWidth: 1)))
        }
    }
}

// A premium zone tray — a soft, slightly-inset region of the desk with a header, holding its objects.
struct ZoneTray<Content: View>: View {
    let title: String
    let count: Int
    var tint: Color = Pal.accent
    @ViewBuilder var content: () -> Content
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 7) {
                Circle().fill(tint).frame(width: 7, height: 7)
                Text(title.uppercased()).font(.system(size: 11, weight: .black, design: .rounded)).tracking(1.4).foregroundStyle(Pal.text)
                Text("\(count)").font(.system(size: 10, weight: .heavy)).foregroundStyle(Pal.muted)
                    .padding(.horizontal, 6).padding(.vertical, 1).background(Capsule().fill(.black.opacity(0.3)))
            }
            HStack(spacing: 26) { content() }
        }
        .padding(.horizontal, 22).padding(.top, 14).padding(.bottom, 18)
        .background(
            RoundedRectangle(cornerRadius: 26, style: .continuous)
                .fill(.white.opacity(0.04))
                .background(RoundedRectangle(cornerRadius: 26, style: .continuous).fill(.black.opacity(0.16)))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white.opacity(0.07), lineWidth: 1))
        )
    }
}

struct DeskDiorama: View {
    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack {
                surface(w: w, h: h)
                // warm lamp pool over the work area
                RadialGradient(colors: [Pal.lamp.opacity(0.30), Pal.lamp.opacity(0.05), .clear],
                               center: .init(x: 0.5, y: 0.42), startRadius: 40, endRadius: h * 0.5)
                    .blendMode(.plusLighter).allowsHitTesting(false)

                content(w: w, h: h)

                vignette
                topBar.frame(maxHeight: .infinity, alignment: .top)
            }
            .ignoresSafeArea()
        }
        .preferredColorScheme(.dark)
    }

    // The 2.5D desk: a dark back wall, a desk top that widens toward the viewer (perspective), a leather
    // work mat, a warm depth haze pushing the back into space, and a lit front lip.
    private func deskTop(_ w: CGFloat, _ h: CGFloat, _ horizon: CGFloat) -> Path {
        Path { p in
            p.move(to: CGPoint(x: w * 0.16, y: horizon))
            p.addLine(to: CGPoint(x: w * 0.84, y: horizon))
            p.addLine(to: CGPoint(x: w * 1.10, y: h))
            p.addLine(to: CGPoint(x: -w * 0.10, y: h))
            p.closeSubpath()
        }
    }
    private func surface(w: CGFloat, h: CGFloat) -> some View {
        let horizon = h * 0.15
        return ZStack {
            // back wall + a warm glow as if a lamp sat just off the top edge
            LinearGradient(colors: [Pal.wallTop, Pal.wallBot], startPoint: .top, endPoint: .bottom)
            RadialGradient(colors: [Pal.lamp.opacity(0.22), .clear], center: .init(x: 0.5, y: 0.02), startRadius: 8, endRadius: w * 0.7)
                .blendMode(.plusLighter)
            // desk top
            deskTop(w, h, horizon).fill(LinearGradient(colors: [Pal.deskBack, Pal.deskFront], startPoint: .top, endPoint: .bottom))
            // wood planks receding to the horizon (very subtle)
            Canvas { ctx, _ in
                for k in 0...9 {
                    let f = CGFloat(k) / 9
                    var path = Path()
                    path.move(to: CGPoint(x: w * (-0.10 + 1.20 * f), y: h))
                    path.addLine(to: CGPoint(x: w * (0.16 + 0.68 * f), y: horizon))
                    ctx.stroke(path, with: .color(.black.opacity(0.10)), lineWidth: 1)
                }
            }
            .clipShape(deskTop(w, h, horizon))
            // depth haze: the back of the desk fades into warm air
            deskTop(w, h, horizon).fill(LinearGradient(colors: [Pal.wallBot.opacity(0.9), .clear],
                                                       startPoint: .top, endPoint: UnitPoint(x: 0.5, y: 0.45)))
            // leather work mat in the central front area
            Path { p in
                p.move(to: CGPoint(x: w * 0.20, y: h * 0.50))
                p.addLine(to: CGPoint(x: w * 0.80, y: h * 0.50))
                p.addLine(to: CGPoint(x: w * 0.92, y: h * 0.96))
                p.addLine(to: CGPoint(x: w * 0.08, y: h * 0.96))
                p.closeSubpath()
            }
            .fill(LinearGradient(colors: [Color(hex: 0x241812), Color(hex: 0x16100B)], startPoint: .top, endPoint: .bottom))
            .overlay(
                Path { p in
                    p.move(to: CGPoint(x: w * 0.20, y: h * 0.50)); p.addLine(to: CGPoint(x: w * 0.80, y: h * 0.50))
                    p.addLine(to: CGPoint(x: w * 0.92, y: h * 0.96)); p.addLine(to: CGPoint(x: w * 0.08, y: h * 0.96)); p.closeSubpath()
                }.stroke(.white.opacity(0.05), lineWidth: 1)
            )
            // front lip highlight
            Rectangle().fill(LinearGradient(colors: [.clear, Pal.lamp.opacity(0.06)], startPoint: .top, endPoint: .bottom))
                .frame(height: h * 0.1).frame(maxHeight: .infinity, alignment: .bottom)
        }
    }

    private var vignette: some View {
        RadialGradient(colors: [.clear, .clear, .black.opacity(0.5)], center: .center, startRadius: 120, endRadius: 720)
            .blendMode(.multiply).allowsHitTesting(false)
    }

    private var topBar: some View {
        HStack(spacing: 10) {
            RoundedRectangle(cornerRadius: 9).fill(LinearGradient(colors: [Pal.accent, Color(hex: 0xC23C16)], startPoint: .top, endPoint: .bottom))
                .frame(width: 30, height: 30)
                .overlay(Image(systemName: "square.stack.3d.up.fill").font(.system(size: 14, weight: .bold)).foregroundStyle(.white))
            VStack(alignment: .leading, spacing: 0) {
                Text("HoldSpeak").font(.system(size: 17, weight: .black, design: .rounded)).foregroundStyle(Pal.text)
                Text("All Meetings").font(.system(size: 11, weight: .bold)).foregroundStyle(Pal.muted)
            }
            Spacer()
            HStack(spacing: 6) {
                Image(systemName: "lock.fill").font(.system(size: 9, weight: .black))
                Text("ON-DEVICE").font(.system(size: 10, weight: .heavy)).tracking(1)
            }
            .foregroundStyle(Color(hex: 0x3ECF8E))
            .padding(.horizontal, 11).padding(.vertical, 7)
            .background(Capsule().fill(.black.opacity(0.3)).overlay(Capsule().strokeBorder(Color(hex: 0x3ECF8E).opacity(0.3), lineWidth: 1)))
        }
        .padding(.horizontal, 22).padding(.top, 16)
    }

    private func content(w: CGFloat, h: CGFloat) -> some View {
        ZStack {
            // BACK of the desk (smaller, hazed): a week tray + the knowledge crystal
            ZoneTray(title: "This Week", count: 1, tint: Pal.cobalt) {
                DeskItem(sprite: "cassette", size: 104, title: "1:1 · Priya", sub: "24m · 2 spk", tint: Pal.cobalt, lift: 4, tilt: 3)
            }
            .position(x: w * 0.34, y: h * 0.30)

            DeskItem(sprite: "crystal", size: 116, title: "Architecture", sub: "knowledge base", tint: Pal.violet, glow: true, lift: 8, tilt: 4)
                .position(x: w * 0.76, y: h * 0.27)

            // MID: the model, glowing, the hero capability object
            DeskItem(sprite: "cartridge", size: 150, title: "AI Core", sub: "Qwen3-4B · on device", tint: Pal.cobalt, glow: true, lift: 12, tilt: -2)
                .position(x: w * 0.70, y: h * 0.52)

            // FRONT (larger): today's meetings on the leather mat
            ZoneTray(title: "Today", count: 2, tint: Pal.accent) {
                DeskItem(sprite: "cassette", size: 132, title: "Studio Mix", sub: "32m · 3 spk", tint: Pal.accent, lift: 8, tilt: -3)
                DeskItem(sprite: "cassette2", size: 132, title: "Standup", sub: "12m · 5 spk", tint: Pal.accent, lift: 4, tilt: 2)
            }
            .position(x: w * 0.40, y: h * 0.74)

            // the companion, perched at the desk's front edge
            Sprite(name: "qlippy", size: 86).shadow(color: .black.opacity(0.55), radius: 9, y: 7)
                .position(x: w * 0.86, y: h * 0.88)
        }
    }
}

@main
struct DioramaApp: App {
    var body: some Scene { WindowGroup { DeskDiorama() } }
}
