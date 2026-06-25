import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — THE FRACTAL DESK (harness), v2 on owner feedback: zones are LOW-PROFILE (a compact top shelf,
// not dominating boxes) so the canvas stays open for PULL-OUTS. A tapped object's intelligence now PULLS
// OUT from the right edge as a rich in-world drawer (no centered modal, no plain nav window). A big
// always-on-top Back bar makes escaping a zone unmissable; a focus fog catches stray taps. Keeps the
// delight: spring-in objects, idle motion, record→listen→born, Qlippy. Compose here, then port to DioStage.

extension Color {
    init(hex: UInt, a: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: a)
    }
}

enum Pal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let trayTop = Color(hex: 0x1B1626), trayBot = Color(hex: 0x0C0A12)
    static let accent = Color(hex: 0xFF6B35), cobalt = Color(hex: 0x5B8DEF), violet = Color(hex: 0x9B6BFF)
    static let mint = Color(hex: 0x3ECF8E), text = Color(hex: 0xF4ECE0), muted = Color(hex: 0x9C93A8)
}

struct Sprite: View {
    let name: String; var size: CGFloat = 120
    var body: some View {
        if let path = Bundle.main.path(forResource: name, ofType: "png"), let ui = UIImage(contentsOfFile: path) {
            Image(uiImage: ui).interpolation(.none).resizable().scaledToFit().frame(width: size, height: size)
        } else { RoundedRectangle(cornerRadius: 12).fill(.gray.opacity(0.3)).frame(width: size, height: size) }
    }
}

struct Obj: Identifiable { let id: String; let sprite: String; let base: CGFloat; let glow: Color; let title: String }
enum Mode { case home, focus, recede }

enum World {
    static let name: [String: String] = ["Atlas": "Project Atlas", "Personal": "Personal", "Atlas/Q3": "Q3 Planning"]
    static let tint: [String: Color] = ["Atlas": Pal.accent, "Personal": Pal.mint, "Atlas/Q3": Pal.cobalt]
    static let children: [String: [String]] = ["": ["Atlas", "Personal"], "Atlas": ["Atlas/Q3"], "Atlas/Q3": [], "Personal": []]
    static let members: [String: [Obj]] = [
        "": [Obj(id: "standup", sprite: "cassette", base: 130, glow: Pal.accent, title: "Standup"),
             Obj(id: "core",    sprite: "cartridge", base: 162, glow: Pal.cobalt, title: "AI Core"),
             Obj(id: "docs",    sprite: "crystal",  base: 120, glow: Pal.violet, title: "Docs KB")],
        "Atlas": [Obj(id: "kickoff", sprite: "cassette",  base: 130, glow: Pal.accent, title: "Kickoff"),
                  Obj(id: "roadmap", sprite: "cassette2", base: 130, glow: Pal.accent, title: "Roadmap")],
        "Atlas/Q3": [Obj(id: "sprint1", sprite: "cassette",  base: 126, glow: Pal.accent, title: "Sprint 1"),
                     Obj(id: "sprint2", sprite: "cassette2", base: 126, glow: Pal.accent, title: "Sprint 2"),
                     Obj(id: "notes",   sprite: "note",      base: 106, glow: Pal.mint,   title: "Notes")],
        "Personal": [Obj(id: "oneonone", sprite: "cassette2", base: 130, glow: Pal.mint, title: "1:1 w/ Sam")],
    ]
}

struct Hero: View {
    let obj: Obj; let landed: Bool; let mode: Mode
    let onTap: () -> Void
    private var modeScale: CGFloat { mode == .focus ? 1.34 : (mode == .recede ? 0.6 : 1) }
    private var dim: Double { mode == .recede ? 0.3 : 1 }
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate, ph = Double(abs(obj.id.hashValue) % 7)
            let bob = CGFloat(sin(t * 0.9 + ph) * 7)
            let breathe = 1 + CGFloat(sin(t * 1.15 + ph) * 0.018)
            let tilt = sin(t * 0.65 + ph) * 2.0
            let pulse = 0.6 + 0.4 * sin(t * 1.7 + ph)
            let s = obj.base
            VStack(spacing: 6) {
                ZStack {
                    Ellipse().fill(.black.opacity(0.5)).frame(width: s * 0.62, height: s * 0.15)
                        .blur(radius: 11).offset(y: s * 0.46 * modeScale + bob * 0.25).opacity(landed ? dim : 0)
                    Circle().fill(RadialGradient(colors: [obj.glow.opacity(mode == .focus ? 0.75 : 0.5), .clear], center: .center, startRadius: 2, endRadius: s * 0.8))
                        .frame(width: s * 1.9, height: s * 1.9).blur(radius: 12).opacity(landed ? pulse * dim : 0)
                    Sprite(name: obj.sprite, size: s)
                        .rotationEffect(.degrees(landed ? tilt : -8))
                        .scaleEffect(landed ? modeScale * breathe : 0.15)
                        .offset(y: landed ? -bob : -260)
                        .opacity(landed ? dim : 0)
                        .shadow(color: .black.opacity(0.55), radius: 16, y: 12)
                }
                .frame(width: s, height: s)
                Text(obj.title).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text.opacity(0.85))
                    .padding(.horizontal, 9).padding(.vertical, 3).background(Capsule().fill(.black.opacity(0.32)))
                    .opacity(landed && mode != .recede ? 0.95 : 0)
            }
            .contentShape(Rectangle())
            .onTapGesture { if mode != .recede { onTap() } }   // a receded object ignores taps (the fog handles them)
        }
    }
}

struct TrayMote: View {
    let sprite: String; let seed: Int
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate, ph = Double(seed)
            let bob = CGFloat(sin(t * 1.3 + ph) * 2)
            Sprite(name: sprite, size: 30).offset(y: -bob)
        }
    }
}

// LOW-PROFILE zone tray — a compact labeled shelf tile (a place that holds meetings). Tap to dive; drop a meeting on it to file.
struct ZoneTray: View {
    let zid: String, name: String, tint: Color
    let members: [Obj]; let subZones: Int; let size: CGSize
    let landed: Bool; let index: Int; let dimmed: Bool
    let onDive: () -> Void
    @State private var press = false
    var body: some View {
        let w = size.width, h = size.height
        HStack(spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill(tint.opacity(0.18))
                Image(systemName: subZones > 0 ? "square.stack.3d.up.fill" : "tray.full.fill")
                    .font(.system(size: 18, weight: .bold)).foregroundStyle(tint)
            }
            .frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text(name).font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text).lineLimit(1)
                HStack(spacing: 5) {
                    ForEach(Array(members.prefix(3).enumerated()), id: \.offset) { i, m in TrayMote(sprite: m.sprite, seed: i) }
                    Text("\(members.count)\(subZones > 0 ? " · +\(subZones)" : "")")
                        .font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(tint)
                }
            }
            Spacer(minLength: 0)
            Image(systemName: "arrow.down.forward.and.arrow.up.backward").font(.system(size: 11, weight: .black)).foregroundStyle(tint.opacity(0.85))
        }
        .padding(.horizontal, 13)
        .frame(width: w, height: h)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(LinearGradient(colors: [Pal.trayTop, Pal.trayBot], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(tint.opacity(0.45), lineWidth: 1.5))
                .shadow(color: .black.opacity(0.45), radius: 12, y: 8)
        )
        .scaleEffect(press ? 0.96 : (landed ? 1 : 0.4)).opacity(landed ? (dimmed ? 0 : 1) : 0)
        .animation(.spring(response: 0.65, dampingFraction: 0.62).delay(Double(index) * 0.07), value: landed)
        .animation(.spring(response: 0.4, dampingFraction: 0.6), value: press)
        .allowsHitTesting(!dimmed)
        .contentShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .onTapGesture { press = true; DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { press = false; onDive() } }
    }
}

struct CreateTile: View {
    let size: CGSize; let landed: Bool; let dimmed: Bool; let onTap: () -> Void
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "plus.circle.fill").font(.system(size: 17, weight: .bold)).foregroundStyle(Pal.muted)
            Text("New Zone").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(Pal.muted)
        }
        .frame(width: size.width, height: size.height)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous)
            .strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 5])).foregroundStyle(Pal.muted.opacity(0.4)))
        .opacity(landed ? (dimmed ? 0 : 0.9) : 0)
        .allowsHitTesting(!dimmed).contentShape(Rectangle()).onTapGesture(perform: onTap)
    }
}

// The big, always-on-top way OUT.
struct BackBar: View {
    let crumbs: [(String, Color)]
    let onBack: () -> Void; let onJump: (Int) -> Void
    var body: some View {
        HStack(spacing: 10) {
            Button(action: onBack) {
                HStack(spacing: 5) {
                    Image(systemName: "chevron.left").font(.system(size: 15, weight: .black))
                    Text("Back").font(.system(size: 15, weight: .heavy, design: .rounded))
                }
                .foregroundStyle(Pal.text).padding(.horizontal, 16).frame(height: 44)
                .background(Capsule().fill(.white.opacity(0.10)).overlay(Capsule().strokeBorder(.white.opacity(0.18), lineWidth: 1)))
            }.buttonStyle(.plain)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(Array(crumbs.enumerated()), id: \.offset) { i, c in
                        if i > 0 { Image(systemName: "chevron.right").font(.system(size: 10, weight: .black)).foregroundStyle(Pal.muted) }
                        let last = i == crumbs.count - 1
                        Button { if !last { onJump(i) } } label: {
                            HStack(spacing: 5) {
                                if i == 0 { Image(systemName: "house.fill").font(.system(size: 11, weight: .bold)) }
                                else { Circle().fill(c.1).frame(width: 7, height: 7) }
                                Text(c.0).font(.system(size: 13, weight: .heavy, design: .rounded))
                            }
                            .foregroundStyle(last ? Pal.text : Pal.muted).padding(.horizontal, 11).frame(height: 38)
                            .background(Capsule().fill(.white.opacity(last ? 0.10 : 0.04))
                                .overlay(Capsule().strokeBorder((last ? c.1 : .clear).opacity(0.6), lineWidth: 1)))
                        }.buttonStyle(.plain).disabled(last)
                    }
                }
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 16).frame(maxWidth: .infinity, alignment: .leading)
    }
}

// THE PULL-OUT — a tapped object's contents slide out from the right as a rich in-world drawer.
struct Pullout: View {
    let obj: Obj; let onClose: () -> Void
    private var isMeeting: Bool { obj.sprite.hasPrefix("cassette") }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 11) {
                Sprite(name: obj.sprite, size: 40)
                VStack(alignment: .leading, spacing: 2) {
                    Text(obj.title).font(.system(size: 18, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text).lineLimit(1)
                    Text(isMeeting ? "32 min · 3 speakers" : "on this iPad").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(Pal.muted)
                }
                Spacer(minLength: 0)
                HStack(spacing: 5) {
                    Image(systemName: "lock.fill").font(.system(size: 9, weight: .bold))
                    Text("On device").font(.system(size: 10, weight: .heavy, design: .rounded))
                }.foregroundStyle(Pal.mint).padding(.horizontal, 9).frame(height: 26).background(Capsule().fill(Pal.mint.opacity(0.14)))
                Button(action: onClose) {
                    Image(systemName: "xmark").font(.system(size: 14, weight: .black)).foregroundStyle(Pal.text)
                        .frame(width: 36, height: 36).background(Circle().fill(.white.opacity(0.10)))
                }.buttonStyle(.plain)
            }
            .padding(.horizontal, 18).padding(.top, 16).padding(.bottom, 12)
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 16) {
                    if isMeeting {
                        Section("SUMMARY", Pal.accent) { Text("Shipped the beta Friday. Pricing is the open call for next week; Priya owns the customer deck and finance needs the numbers by EOD.").font(.system(size: 14.5, weight: .medium, design: .rounded)).foregroundStyle(Pal.text.opacity(0.92)).fixedSize(horizontal: false, vertical: true) }
                        Section("ACTIONS · 3", Pal.mint) {
                            VStack(alignment: .leading, spacing: 10) {
                                ActionRow("Send the finance deck to Priya", "you · EOD")
                                ActionRow("Lock pricing tiers before the all-hands", "Priya · Mon")
                                ActionRow("Email finance the beta numbers", "you")
                            }
                        }
                        Section("TOPICS", Pal.violet) { Chips(["pricing", "beta launch", "finance", "deck", "all-hands"]) }
                        Section("TRANSCRIPT · 4 lines", Pal.cobalt) {
                            VStack(alignment: .leading, spacing: 9) {
                                Line("Sam", "Let's ship the beta Friday and decide pricing next week.")
                                Line("Priya", "I'll own the customer deck.")
                                Line("Sam", "Finance needs the numbers by end of day.")
                                Line("You", "On it — I'll email them after this.")
                            }
                        }
                    } else {
                        Section(obj.sprite == "crystal" ? "KNOWLEDGE" : "MODEL", obj.glow) {
                            Text(obj.sprite == "crystal" ? "12 documents filed here. Ask a grounded question and get an answer cited from your own notes." : "Qwen3-4B-Instruct, loaded and ready. Every meeting is summarised on this iPad — nothing leaves the device.")
                                .font(.system(size: 14, weight: .medium, design: .rounded)).foregroundStyle(Pal.text.opacity(0.9)).fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.horizontal, 18).padding(.bottom, 26)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x161320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 28, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 28, x: -10, y: 8)
        )
    }
    @ViewBuilder private func Section(_ label: String, _ tint: Color, @ViewBuilder _ c: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 7) { RoundedRectangle(cornerRadius: 2).fill(tint).frame(width: 4, height: 13)
                Text(label).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(tint).tracking(1.2) }
            c()
        }
        .frame(maxWidth: .infinity, alignment: .leading).padding(14)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.04))
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white.opacity(0.06), lineWidth: 1)))
    }
    @ViewBuilder private func ActionRow(_ task: String, _ meta: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "circle").font(.system(size: 15, weight: .bold)).foregroundStyle(Pal.mint).padding(.top, 1)
            VStack(alignment: .leading, spacing: 2) {
                Text(task).font(.system(size: 14, weight: .semibold, design: .rounded)).foregroundStyle(Pal.text)
                Text(meta).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(Pal.muted)
            }
        }
    }
    @ViewBuilder private func Line(_ who: String, _ what: String) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(who).font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(Pal.cobalt)
            Text(what).font(.system(size: 13.5, weight: .regular, design: .rounded)).foregroundStyle(Pal.text.opacity(0.88)).fixedSize(horizontal: false, vertical: true)
        }
    }
    @ViewBuilder private func Chips(_ items: [String]) -> some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 72), spacing: 8, alignment: .leading)], alignment: .leading, spacing: 8) {
            ForEach(Array(items.enumerated()), id: \.offset) { _, it in
                Text(it).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(Pal.text.opacity(0.9))
                    .padding(.horizontal, 10).padding(.vertical, 6)
                    .background(Capsule().fill(Pal.violet.opacity(0.14)).overlay(Capsule().strokeBorder(Pal.violet.opacity(0.35), lineWidth: 1)))
            }
        }
    }
}

struct Companion: View {
    let landed: Bool; let excited: Bool
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let sway = sin(t * (excited ? 3.0 : 1.6)) * (excited ? 7 : 4.5)
            let bob = CGFloat(sin(t * 2.0) * 4)
            let cycle = t.truncatingRemainder(dividingBy: excited ? 1.4 : 3.4)
            let hop = cycle < 0.4 ? CGFloat(sin(cycle / 0.4 * .pi)) * (excited ? 34 : 24) : 0
            ZStack {
                Ellipse().fill(.black.opacity(0.5)).frame(width: 60, height: 14).blur(radius: 9)
                    .offset(y: 46).opacity(landed ? (hop > 1 ? 0.4 : 1) : 0)
                Sprite(name: "qlippy", size: 100)
                    .rotationEffect(.degrees(landed ? sway : 0))
                    .offset(y: landed ? -bob - hop : -300)
                    .scaleEffect(landed ? 1 : 0.1).opacity(landed ? 1 : 0)
                    .shadow(color: .black.opacity(0.5), radius: 12, y: 8)
                    .animation(.spring(response: 0.8, dampingFraction: 0.5).delay(0.6), value: landed)
            }
        }
    }
}

struct Motes: View {
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            Canvas { ctx, size in
                for i in 0..<16 {
                    let s = Double(i)
                    let x = (sin(t * 0.18 + s * 1.7) * 0.5 + 0.5) * size.width
                    let y = size.height - (t * 9 + s * 57).truncatingRemainder(dividingBy: Double(size.height + 80))
                    let r = 1.4 + s.truncatingRemainder(dividingBy: 3)
                    ctx.opacity = 0.06 + 0.05 * (sin(t + s) * 0.5 + 0.5)
                    ctx.fill(Path(ellipseIn: CGRect(x: x, y: y, width: r, height: r)), with: .color(.white))
                }
            }
        }
    }
}

struct RecordOrb: View {
    let onTap: () -> Void
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                ForEach(0..<2) { i in
                    let p = (sin(t * 1.3 + Double(i) * 1.6) * 0.5 + 0.5)
                    Circle().stroke(Pal.accent.opacity(0.35 * (1 - p)), lineWidth: 2)
                        .frame(width: 64 + CGFloat(p) * 46, height: 64 + CGFloat(p) * 46)
                }
                Circle().fill(RadialGradient(colors: [Color(hex: 0xFF8A5B), Pal.accent, Color(hex: 0xC23C16)],
                                             center: .init(x: 0.4, y: 0.35), startRadius: 2, endRadius: 40))
                    .frame(width: 66, height: 66).shadow(color: Pal.accent.opacity(0.6), radius: 16, y: 6)
                Image(systemName: "mic.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(.white)
            }
            .scaleEffect(1 + CGFloat(sin(t * 2) * 0.02)).contentShape(Circle()).onTapGesture(perform: onTap)
        }
    }
}

struct VoiceCore: View {
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                ForEach(0..<3) { i in
                    let p = ((t * 0.6 + Double(i) * 0.33).truncatingRemainder(dividingBy: 1))
                    Circle().stroke(Pal.accent.opacity(0.4 * (1 - p)), lineWidth: 2)
                        .frame(width: 120 + CGFloat(p) * 150, height: 120 + CGFloat(p) * 150)
                }
                ForEach(0..<40) { i in
                    let a = Double(i) / 40 * 2 * .pi
                    let lvl = 0.5 + 0.5 * sin(t * 6 + Double(i) * 0.7)
                    Capsule().fill(Pal.accent.opacity(0.85)).frame(width: 3, height: 10 + CGFloat(lvl) * 22)
                        .offset(y: -78).rotationEffect(.radians(a))
                }
                Circle().fill(RadialGradient(colors: [Color(hex: 0xFFB070), Pal.accent.opacity(0.7), .clear],
                                             center: .center, startRadius: 4, endRadius: 70))
                    .frame(width: 120, height: 120).scaleEffect(1 + CGFloat(sin(t * 2.4) * 0.06)).blur(radius: 2)
            }
        }
    }
}

struct RisingWords: View {
    let words = ["let's ship the beta…", "Priya owns the deck", "decision: pricing next week", "action: email finance"]
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                ForEach(0..<words.count, id: \.self) { i in
                    let cycle = (t * 0.5 + Double(i) * 0.9).truncatingRemainder(dividingBy: Double(words.count) * 0.9)
                    let local = cycle
                    let vis = local > 0 && local < 1.6
                    Text(words[i]).font(.system(size: 13, weight: .bold, design: .rounded)).foregroundStyle(Pal.text.opacity(0.85))
                        .opacity(vis ? max(0, 1 - local / 1.6) : 0).offset(y: vis ? CGFloat(-local * 40) : 40)
                }
            }
        }
    }
}

struct Stage: View {
    @State private var landed = false
    @State private var path: [String] = []
    @State private var diveDir = 1
    @State private var flash = 0.0
    @State private var selected: String? = nil
    @State private var recording = false
    @State private var born = false
    @State private var newPos = CGPoint(x: 0.78, y: 0.5)

    private let diveSpring = Animation.spring(response: 0.6, dampingFraction: 0.74)
    private let focusSpring = Animation.spring(response: 0.5, dampingFraction: 0.72)

    private var pathKey: String { path.joined(separator: "/") }
    private var curTint: Color { path.isEmpty ? Pal.accent : (World.tint[pathKey] ?? Pal.accent) }
    private func zones() -> [String] { World.children[pathKey] ?? [] }
    private func members() -> [Obj] { World.members[pathKey] ?? [] }
    private func mode(_ id: String) -> Mode { selected == nil ? .home : (selected == id ? .focus : .recede) }
    private func selectedObj() -> Obj? { members().first { $0.id == selected } }

    private var diveTransition: AnyTransition {
        diveDir >= 0
            ? .asymmetric(insertion: .scale(scale: 0.6).combined(with: .opacity), removal: .scale(scale: 1.6).combined(with: .opacity))
            : .asymmetric(insertion: .scale(scale: 1.6).combined(with: .opacity), removal: .scale(scale: 0.6).combined(with: .opacity))
    }

    // a compact zone shelf row, plus a "+ New Zone" tile, near the top
    private func shelfSize(_ n: Int, _ w: CGFloat) -> CGSize {
        let cols = max(1, min(3, n)); return CGSize(width: (w - 40) / CGFloat(cols) - 10, height: 66)
    }
    private func shelfPos(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let cols = max(1, min(3, n)); let size = shelfSize(n, w)
        let r = i / cols, c = i % cols
        let rowW = CGFloat(cols) * (size.width + 10) - 10
        let x = (w - rowW) / 2 + size.width / 2 + CGFloat(c) * (size.width + 10)
        let y = h * 0.16 + CGFloat(r) * (size.height + 10)
        return CGPoint(x: x, y: y)
    }
    private func loosePos(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let cols = max(1, min(3, n)); let r = i / cols, c = i % cols
        let x = cols == 1 ? 0.5 : 0.22 + 0.56 * Double(c) / Double(cols - 1)
        let rows = max(1, Int(ceil(Double(n) / Double(cols))))
        let y = rows == 1 ? 0.55 : 0.48 + 0.2 * Double(r) / Double(rows - 1)
        return CGPoint(x: w * x, y: h * y)
    }
    private func focusPos(_ w: CGFloat, _ h: CGFloat) -> CGPoint { CGPoint(x: w * 0.24, y: h * 0.44) }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack {
                LinearGradient(colors: [Pal.bgTop, Pal.bgMid, Pal.bgBot], startPoint: .top, endPoint: .bottom)
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    RadialGradient(colors: [(selected == nil ? curTint : Pal.cobalt).opacity(0.18 + 0.05 * sin(t * 1.2)), .clear],
                                   center: .init(x: 0.5, y: 0.4), startRadius: 20, endRadius: w * 0.95)
                        .blendMode(.plusLighter).animation(diveSpring, value: pathKey)
                }
                Motes()
                Color.clear.contentShape(Rectangle()).onTapGesture {
                    if selected != nil { select(nil) } else if !path.isEmpty { climbOut() }
                }

                // title at root only
                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 25, weight: .black, design: .rounded)).foregroundStyle(Pal.text)
                    Text("your meetings, alive").font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(Pal.muted).tracking(1)
                }
                .opacity(landed && selected == nil && path.isEmpty ? 1 : 0)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.05)

                ForEach([pathKey], id: \.self) { _ in level(w, h) }
                    .transition(diveTransition)

                Companion(landed: landed, excited: selected != nil || recording).position(x: w * 0.9, y: h * 0.9)
                if landed && !recording && selected == nil {
                    RecordOrb { startRecord() }.position(x: w * 0.5, y: h * 0.91).transition(.scale.combined(with: .opacity))
                }

                if born {
                    VStack(spacing: 7) {
                        Sprite(name: "cassette2", size: 124).shadow(color: .black.opacity(0.55), radius: 16, y: 12)
                        Text("New Meeting").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text)
                            .padding(.horizontal, 10).padding(.vertical, 5).background(Capsule().fill(.black.opacity(0.35)))
                    }
                    .position(x: w * newPos.x, y: h * newPos.y).transition(.scale(scale: 0.2).combined(with: .opacity))
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.5)], center: .center, startRadius: 160, endRadius: 800)
                    .blendMode(.multiply).allowsHitTesting(false)
                RadialGradient(colors: [curTint.opacity(flash), .clear], center: .center, startRadius: 10, endRadius: w)
                    .blendMode(.plusLighter).allowsHitTesting(false)

                // the PULL-OUT (right edge) for the selected object
                if let o = selectedObj() {
                    Pullout(obj: o, onClose: { select(nil) })
                        .frame(width: min(560, w * 0.62))
                        .padding(.vertical, 22).padding(.trailing, 16)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                        .transition(.move(edge: .trailing).combined(with: .opacity))
                        .zIndex(60)
                }

                // the big, always-on-top Back bar (above EVERYTHING so no tile steals its tap)
                if !path.isEmpty && selected == nil {
                    BackBar(crumbs: crumbs(), onBack: { climbOut() }, onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.045).zIndex(100)
                }

                if recording { listeningOverlay() }
            }
            .ignoresSafeArea()
            .onAppear {
                landed = true
                let env = ProcessInfo.processInfo.environment
                if let p = env["DIO_PATH"], !p.isEmpty { path = p.split(separator: "/").map(String.init) }
                if let s = env["DIO_SELECT"], !s.isEmpty { DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { select(s) } }
                if env["DIO_DEMO"] == "1" { runDemo() }
            }
        }
        .preferredColorScheme(.dark)
    }

    @ViewBuilder private func level(_ w: CGFloat, _ h: CGFloat) -> some View {
        let zs = zones(); let ms = members(); let slotN = zs.count + 1
        ZStack {
            // low-profile zone shelf + create tile
            ForEach(Array(zs.enumerated()), id: \.element) { i, zid in
                ZoneTray(zid: zid, name: World.name[zid] ?? zid, tint: World.tint[zid] ?? Pal.accent,
                         members: World.members[zid] ?? [], subZones: (World.children[zid] ?? []).count,
                         size: shelfSize(slotN, w), landed: landed, index: i, dimmed: selected != nil,
                         onDive: { dive(into: zid) })
                    .position(shelfPos(i, slotN, w, h))
            }
            CreateTile(size: shelfSize(slotN, w), landed: landed, dimmed: selected != nil) {}
                .position(shelfPos(zs.count, slotN, w, h))

            // objects
            ForEach(Array(ms.enumerated()), id: \.element.id) { i, o in
                Hero(obj: o, landed: landed, mode: mode(o.id)) { select(selected == o.id ? nil : o.id) }
                    .position(selected == o.id ? focusPos(w, h) : loosePos(i, ms.count, w, h))
                    .animation(focusSpring, value: selected)
                    .zIndex(selected == o.id ? 10 : 0)
            }

            // focus fog — catches stray taps, dims the desk behind the pull-out
            if selected != nil {
                Color.black.opacity(0.45).ignoresSafeArea().onTapGesture { select(nil) }
                    .zIndex(5).transition(.opacity)
            }
        }
    }

    @ViewBuilder private func listeningOverlay() -> some View {
        ZStack {
            Color.black.opacity(0.6).ignoresSafeArea()
            VStack(spacing: 24) {
                Text("Listening…").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text).tracking(1)
                VoiceCore().frame(height: 300)
                RisingWords().frame(height: 70)
                Button { stopRecord() } label: {
                    HStack(spacing: 8) {
                        RoundedRectangle(cornerRadius: 3).fill(.white).frame(width: 13, height: 13)
                        Text("Stop").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(.white)
                    }
                    .padding(.horizontal, 22).padding(.vertical, 12)
                    .background(Capsule().fill(.white.opacity(0.12)).overlay(Capsule().strokeBorder(.white.opacity(0.25), lineWidth: 1)))
                }
            }
        }
        .transition(.opacity)
    }

    private func crumbs() -> [(String, Color)] {
        var out: [(String, Color)] = [("Desk", Pal.accent)]; var acc: [String] = []
        for comp in path { acc.append(comp); let id = acc.joined(separator: "/"); out.append((World.name[id] ?? comp, World.tint[id] ?? Pal.accent)) }
        return out
    }
    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
    private func whoosh() { flash = 0.5; withAnimation(.easeOut(duration: 0.6)) { flash = 0 } }
    private func dive(into id: String) {
        haptic(.heavy); whoosh(); diveDir = 1
        withAnimation(diveSpring) { selected = nil; path = id.split(separator: "/").map(String.init) }
    }
    private func climbOut() { guard !path.isEmpty else { return }; haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; path.removeLast() } }
    private func jump(to i: Int) { haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; path = Array(path.prefix(i)) } }
    private func select(_ id: String?) { haptic(id == nil ? .light : .medium); withAnimation(focusSpring) { selected = id } }
    private func startRecord() { haptic(.medium); withAnimation(.easeInOut(duration: 0.35)) { recording = true } }
    private func stopRecord() {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(.easeInOut(duration: 0.3)) { recording = false }
        withAnimation(.spring(response: 0.6, dampingFraction: 0.6)) { born = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { withAnimation(.spring(response: 0.7, dampingFraction: 0.62)) { newPos = CGPoint(x: 0.78, y: 0.55) } }
    }
    private func runDemo() {
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 2_200_000_000); select("standup")     // pull out intelligence
            try? await Task.sleep(nanoseconds: 3_000_000_000); select(nil)
            try? await Task.sleep(nanoseconds: 1_200_000_000); dive(into: "Atlas")    // dive into a zone
            try? await Task.sleep(nanoseconds: 2_600_000_000); dive(into: "Atlas/Q3") // deeper
            try? await Task.sleep(nanoseconds: 2_600_000_000); jump(to: 0)            // back home
        }
    }
}

@main
struct DioramaApp: App {
    var body: some Scene { WindowGroup { Stage() } }
}
