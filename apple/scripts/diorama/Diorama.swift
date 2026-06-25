import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — THE FRACTAL DESK (harness). The owner's most-excited idea, into the 2.5D diorama: the stage now
// has PLACES. Named zone trays HOLD objects; tap a tray and you DIVE in — the camera rushes, the zone
// becomes the whole desk, showing its members and its own sub-zones (recursive). A breadcrumb shows where
// you are and jumps you back out; tap empty to climb a level. The dive is gamified motion, not a cut.
// Keeps the delight: objects spring/breathe, the record→listen→born loop, Qlippy with character.
// Compose here in the Simulator, then port to the app's DioStage. Auto-tour with env DIO_DEMO=1.

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

// MARK: - The zone world (a path-keyed tree). Zone ids ARE their full path ("Atlas", "Atlas/Q3").
enum World {
    static let name: [String: String] = ["Atlas": "Project Atlas", "Personal": "Personal",
                                          "Atlas/Q3": "Q3 Planning"]
    static let tint: [String: Color] = ["Atlas": Pal.accent, "Personal": Pal.mint, "Atlas/Q3": Pal.cobalt]
    static let children: [String: [String]] = ["": ["Atlas", "Personal"], "Atlas": ["Atlas/Q3"],
                                               "Atlas/Q3": [], "Personal": []]
    static let members: [String: [Obj]] = [
        "": [Obj(id: "standup", sprite: "cassette", base: 132, glow: Pal.accent, title: "Standup"),
             Obj(id: "core",    sprite: "cartridge", base: 168, glow: Pal.cobalt, title: "AI Core"),
             Obj(id: "docs",    sprite: "crystal",  base: 122, glow: Pal.violet, title: "Docs KB")],
        "Atlas": [Obj(id: "kickoff", sprite: "cassette",  base: 132, glow: Pal.accent, title: "Kickoff"),
                  Obj(id: "roadmap", sprite: "cassette2", base: 132, glow: Pal.accent, title: "Roadmap")],
        "Atlas/Q3": [Obj(id: "sprint1", sprite: "cassette",  base: 128, glow: Pal.accent, title: "Sprint 1"),
                     Obj(id: "sprint2", sprite: "cassette2", base: 128, glow: Pal.accent, title: "Sprint 2"),
                     Obj(id: "notes",   sprite: "note",      base: 108, glow: Pal.mint,   title: "Notes")],
        "Personal": [Obj(id: "oneonone", sprite: "cassette2", base: 132, glow: Pal.mint, title: "1:1 w/ Sam")],
    ]
}

// A hero object: springs in (overshoot), idles forever, reacts to selection.
struct Hero: View {
    let obj: Obj; let landed: Bool; let mode: Mode
    let onTap: () -> Void
    private var modeScale: CGFloat { mode == .focus ? 1.32 : (mode == .recede ? 0.62 : 1) }
    private var dim: Double { mode == .recede ? 0.34 : 1 }
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
                    Circle().fill(RadialGradient(colors: [obj.glow.opacity(mode == .focus ? 0.7 : 0.5), .clear], center: .center, startRadius: 2, endRadius: s * 0.8))
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
            .onTapGesture(perform: onTap)
        }
    }
}

// A small breathing object preview that sits inside a zone tray.
struct TrayMote: View {
    let sprite: String; let seed: Int
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate, ph = Double(seed)
            let bob = CGFloat(sin(t * 1.3 + ph) * 3)
            ZStack {
                Ellipse().fill(.black.opacity(0.45)).frame(width: 34, height: 8).blur(radius: 4).offset(y: 22)
                Sprite(name: sprite, size: 46).offset(y: -bob).shadow(color: .black.opacity(0.5), radius: 5, y: 4)
            }
            .frame(width: 52, height: 60)
        }
    }
}

// A premium recessed zone tray — a named place on the desk that HOLDS objects. Tap to dive in.
struct ZoneTray: View {
    let zid: String, name: String, tint: Color
    let members: [Obj]; let subZones: Int; let size: CGSize
    let landed: Bool; let index: Int; let dimmed: Bool
    let onDive: () -> Void
    @State private var press = false
    var body: some View {
        let w = size.width, h = size.height
        ZStack {
            RoundedRectangle(cornerRadius: 26, style: .continuous).fill(tint.opacity(0.20))
                .blur(radius: 26).frame(width: w * 0.96, height: h * 0.9)
            ZStack {
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(LinearGradient(colors: [Pal.trayTop, Pal.trayBot], startPoint: .top, endPoint: .bottom))
                RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.05), lineWidth: 1)
                RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(tint.opacity(0.5), lineWidth: 1.5)
                RoundedRectangle(cornerRadius: 24, style: .continuous)            // inner recess shadow
                    .stroke(.black.opacity(0.55), lineWidth: 7).blur(radius: 6).offset(y: 4)
                    .mask(RoundedRectangle(cornerRadius: 24, style: .continuous))
            }
            .shadow(color: .black.opacity(0.55), radius: 18, y: 14)

            VStack(spacing: 0) {
                HStack(spacing: 7) {                                              // label tab
                    Circle().fill(tint).frame(width: 9, height: 9).shadow(color: tint, radius: 4)
                    Text(name).font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text).lineLimit(1)
                    Spacer(minLength: 0)
                    Text("\(members.count)").font(.system(size: 12, weight: .black, design: .rounded)).foregroundStyle(tint)
                        .padding(.horizontal, 7).padding(.vertical, 2).background(Capsule().fill(tint.opacity(0.16)))
                }
                .padding(.horizontal, 14).padding(.top, 12)
                Spacer(minLength: 0)
                HStack(spacing: 8) {                                              // members idling inside
                    ForEach(Array(members.prefix(3).enumerated()), id: \.offset) { i, m in
                        TrayMote(sprite: m.sprite, seed: i + zid.count)
                    }
                    if subZones > 0 {
                        ZStack {
                            RoundedRectangle(cornerRadius: 10).fill(.white.opacity(0.06)).frame(width: 46, height: 46)
                                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(tint.opacity(0.4), lineWidth: 1))
                            VStack(spacing: 1) {
                                Image(systemName: "square.stack.3d.up.fill").font(.system(size: 16)).foregroundStyle(tint)
                                Text("+\(subZones)").font(.system(size: 8, weight: .black, design: .rounded)).foregroundStyle(tint)
                            }
                        }
                    }
                }
                Spacer(minLength: 0)
                HStack(spacing: 5) {                                              // teach the affordance
                    Image(systemName: "arrow.down.forward.and.arrow.up.backward").font(.system(size: 9, weight: .black))
                    Text("DIVE IN").font(.system(size: 10, weight: .heavy, design: .rounded)).tracking(1.6)
                }
                .foregroundStyle(tint.opacity(0.92)).padding(.bottom, 11)
            }
            .frame(width: w, height: h)
        }
        .frame(width: w, height: h)
        .scaleEffect(press ? 0.95 : (landed ? 1 : 0.3))
        .opacity(landed ? (dimmed ? 0 : 1) : 0)
        .animation(.spring(response: 0.7, dampingFraction: 0.6).delay(Double(index) * 0.08), value: landed)
        .animation(.spring(response: 0.4, dampingFraction: 0.6), value: press)
        .allowsHitTesting(!dimmed)
        .contentShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .onTapGesture {
            press = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { press = false; onDive() }
        }
    }
}

// Where am I — a tappable trail that climbs back out.
struct Breadcrumb: View {
    let crumbs: [(String, Color)]            // (display, tint) ; index 0 = "Desk"
    let onJump: (Int) -> Void
    var body: some View {
        HStack(spacing: 6) {
            ForEach(Array(crumbs.enumerated()), id: \.offset) { i, c in
                if i > 0 { Image(systemName: "chevron.right").font(.system(size: 10, weight: .black)).foregroundStyle(Pal.muted) }
                let last = i == crumbs.count - 1
                Button { if !last { onJump(i) } } label: {
                    HStack(spacing: 5) {
                        if i == 0 { Image(systemName: "house.fill").font(.system(size: 10, weight: .bold)) }
                        else { Circle().fill(c.1).frame(width: 7, height: 7) }
                        Text(c.0).font(.system(size: 12.5, weight: .heavy, design: .rounded))
                    }
                    .foregroundStyle(last ? Pal.text : Pal.muted)
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(Capsule().fill(.white.opacity(last ? 0.10 : 0.04))
                        .overlay(Capsule().strokeBorder((last ? c.1 : .clear).opacity(0.5), lineWidth: 1)))
                }.buttonStyle(.plain).disabled(last)
            }
        }
    }
}

struct InfoCard: View {
    let icon: String, title: String, line: String, tint: Color
    var body: some View {
        HStack(spacing: 11) {
            Image(systemName: icon).font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                .frame(width: 34, height: 34).background(Circle().fill(tint))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text)
                Text(line).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(Pal.muted).lineLimit(1)
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 13).padding(.vertical, 11).frame(width: 264)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.06))
                .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.black.opacity(0.3)))
                .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(tint.opacity(0.35), lineWidth: 1))
                .shadow(color: .black.opacity(0.5), radius: 16, y: 10)
        )
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
                Ellipse().fill(.black.opacity(0.5)).frame(width: 66, height: 15).blur(radius: 9)
                    .offset(y: 50).opacity(landed ? (hop > 1 ? 0.4 : 1) : 0)
                Sprite(name: "qlippy", size: 112)
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
                for i in 0..<18 {
                    let s = Double(i)
                    let x = (sin(t * 0.18 + s * 1.7) * 0.5 + 0.5) * size.width
                    let y = size.height - (t * 9 + s * 57).truncatingRemainder(dividingBy: Double(size.height + 80))
                    let r = 1.4 + s.truncatingRemainder(dividingBy: 3)
                    ctx.opacity = 0.07 + 0.06 * (sin(t + s) * 0.5 + 0.5)
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
            .scaleEffect(1 + CGFloat(sin(t * 2) * 0.02))
            .contentShape(Circle()).onTapGesture(perform: onTap)
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
                    Capsule().fill(Pal.accent.opacity(0.85))
                        .frame(width: 3, height: 10 + CGFloat(lvl) * 22)
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
                        .opacity(vis ? max(0, 1 - local / 1.6) : 0)
                        .offset(y: vis ? CGFloat(-local * 40) : 40)
                }
            }
        }
    }
}

struct Stage: View {
    @State private var landed = false
    @State private var path: [String] = []          // current zone path (ids); [] = root desk
    @State private var diveDir = 1                   // +1 dive in, -1 climb out (transition asymmetry)
    @State private var flash = 0.0                   // dive "whoosh"
    @State private var selected: String? = nil
    @State private var cardsIn = false
    @State private var recording = false
    @State private var born = false
    @State private var newPos = CGPoint(x: 0.5, y: 0.34)

    private let cards: [(String, String, String, Color)] = [
        ("sparkles", "Summary", "Shipped the beta Friday; pricing next week", Pal.accent),
        ("checkmark.circle.fill", "3 Actions", "Send the finance deck to Priya · EOD", Pal.mint),
        ("text.alignleft", "Transcript", "32 min · 3 speakers", Pal.cobalt),
    ]
    private let spring = Animation.spring(response: 0.55, dampingFraction: 0.62)
    private let diveSpring = Animation.spring(response: 0.6, dampingFraction: 0.74)

    private var pathKey: String { path.joined(separator: "/") }
    private var curTint: Color { path.isEmpty ? Pal.accent : (World.tint[pathKey] ?? Pal.accent) }
    private func zones() -> [String] { World.children[pathKey] ?? [] }
    private func members() -> [Obj] { World.members[pathKey] ?? [] }
    private func mode(_ id: String) -> Mode { selected == nil ? .home : (selected == id ? .focus : .recede) }

    private var diveTransition: AnyTransition {
        diveDir >= 0
            ? .asymmetric(insertion: .scale(scale: 0.55).combined(with: .opacity),
                          removal:   .scale(scale: 1.7).combined(with: .opacity))
            : .asymmetric(insertion: .scale(scale: 1.7).combined(with: .opacity),
                          removal:   .scale(scale: 0.55).combined(with: .opacity))
    }

    private func zoneSize(_ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGSize {
        let width = n <= 1 ? w * 0.58 : w * 0.43
        return CGSize(width: width, height: width * 0.66)
    }
    private func zonePos(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let x = n == 1 ? 0.5 : 0.27 + 0.46 * Double(i) / Double(max(1, n - 1))
        return CGPoint(x: w * x, y: h * 0.37)
    }
    private func loosePos(_ i: Int, _ n: Int, _ hasZones: Bool, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let y = hasZones ? 0.67 : 0.47
        let x = n == 1 ? 0.5 : 0.2 + 0.6 * Double(i) / Double(max(1, n - 1))
        return CGPoint(x: w * x, y: h * y)
    }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack {
                LinearGradient(colors: [Pal.bgTop, Pal.bgMid, Pal.bgBot], startPoint: .top, endPoint: .bottom)
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    RadialGradient(colors: [(selected == nil ? curTint : Pal.cobalt).opacity(0.20 + 0.05 * sin(t * 1.2)), .clear],
                                   center: .init(x: 0.5, y: selected == nil ? 0.4 : 0.27), startRadius: 20, endRadius: w * 0.95)
                        .blendMode(.plusLighter).animation(diveSpring, value: pathKey)
                }
                Motes()
                Color.clear.contentShape(Rectangle()).onTapGesture {
                    if selected != nil { select(nil) } else if !path.isEmpty { climbOut() }
                }

                // title (root only), else breadcrumb
                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 26, weight: .black, design: .rounded)).foregroundStyle(Pal.text)
                    Text("your meetings, alive").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(Pal.muted).tracking(1)
                }
                .opacity(landed && selected == nil && path.isEmpty ? 1 : 0).offset(y: landed ? 0 : -14)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.055)

                if !path.isEmpty {
                    Breadcrumb(crumbs: crumbs(), onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.06)
                        .opacity(selected == nil ? 1 : 0)
                }

                // THE LEVEL — keyed by path so a dive triggers the camera transition
                ForEach([pathKey], id: \.self) { _ in level(w, h) }
                    .transition(diveTransition)

                Companion(landed: landed, excited: selected != nil || recording).position(x: w * 0.85, y: h * 0.88)
                if landed && !recording && selected == nil {
                    RecordOrb { startRecord() }.position(x: w * 0.5, y: h * 0.91)
                        .transition(.scale.combined(with: .opacity))
                }

                // freshly-captured cassette pops onto the current desk
                if born {
                    VStack(spacing: 7) {
                        Sprite(name: "cassette2", size: 128).shadow(color: .black.opacity(0.55), radius: 16, y: 12)
                        Text("New Meeting").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text)
                            .padding(.horizontal, 10).padding(.vertical, 5).background(Capsule().fill(.black.opacity(0.35)))
                    }
                    .position(x: w * newPos.x, y: h * newPos.y)
                    .transition(.scale(scale: 0.2).combined(with: .opacity))
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.55)], center: .center, startRadius: 140, endRadius: 760)
                    .blendMode(.multiply).allowsHitTesting(false)

                // the dive whoosh
                RadialGradient(colors: [curTint.opacity(flash), .clear], center: .center, startRadius: 10, endRadius: w)
                    .blendMode(.plusLighter).allowsHitTesting(false)

                if recording { listeningOverlay() }
            }
            .ignoresSafeArea()
            .onAppear {
                landed = true
                let env = ProcessInfo.processInfo.environment
                if let p = env["DIO_PATH"], !p.isEmpty { path = p.split(separator: "/").map(String.init) }
                if env["DIO_DEMO"] == "1" { runDemo() }
            }
        }
        .preferredColorScheme(.dark)
    }

    @ViewBuilder private func level(_ w: CGFloat, _ h: CGFloat) -> some View {
        let zs = zones(); let ms = members(); let hasZones = !zs.isEmpty
        ZStack {
            ForEach(Array(zs.enumerated()), id: \.element) { i, zid in
                ZoneTray(zid: zid, name: World.name[zid] ?? zid, tint: World.tint[zid] ?? Pal.accent,
                         members: World.members[zid] ?? [], subZones: (World.children[zid] ?? []).count,
                         size: zoneSize(zs.count, w, h), landed: landed, index: i, dimmed: selected != nil,
                         onDive: { dive(into: zid) })
                    .position(zonePos(i, zs.count, w, h))
            }
            ForEach(Array(ms.enumerated()), id: \.element.id) { i, o in
                Hero(obj: o, landed: landed, mode: mode(o.id)) { select(selected == o.id ? nil : o.id) }
                    .position(selected == o.id ? CGPoint(x: w * 0.5, y: h * 0.24) : loosePos(i, ms.count, hasZones, w, h))
                    .animation(spring, value: selected)
                    .zIndex(selected == o.id ? 10 : 0)
            }
            if let sel = selected, ms.contains(where: { $0.id == sel }) {
                VStack(spacing: 11) {
                    ForEach(Array(cards.enumerated()), id: \.offset) { i, c in
                        InfoCard(icon: c.0, title: c.1, line: c.2, tint: c.3)
                            .scaleEffect(cardsIn ? 1 : 0.4).opacity(cardsIn ? 1 : 0).offset(y: cardsIn ? 0 : 40)
                            .animation(.spring(response: 0.5, dampingFraction: 0.6).delay(0.08 + Double(i) * 0.07), value: cardsIn)
                    }
                }
                .position(x: w * 0.5, y: h * 0.62)
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
        var out: [(String, Color)] = [("Desk", Pal.accent)]
        var acc: [String] = []
        for comp in path {
            acc.append(comp)
            let id = acc.joined(separator: "/")
            out.append((World.name[id] ?? comp, World.tint[id] ?? Pal.accent))
        }
        return out
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
    private func whoosh() {
        flash = 0.5; withAnimation(.easeOut(duration: 0.6)) { flash = 0 }
    }
    private func dive(into id: String) {
        haptic(.heavy); whoosh(); diveDir = 1
        withAnimation(diveSpring) { selected = nil; cardsIn = false; path = id.split(separator: "/").map(String.init) }
    }
    private func climbOut() {
        guard !path.isEmpty else { return }
        haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; cardsIn = false; path.removeLast() }
    }
    private func jump(to crumbIndex: Int) {
        haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; cardsIn = false; path = Array(path.prefix(crumbIndex)) }
    }
    private func select(_ id: String?) {
        haptic(id == nil ? .light : .medium)
        withAnimation(spring) { selected = id }
        cardsIn = false
        if id != nil { withAnimation { cardsIn = true } }
    }
    private func startRecord() {
        haptic(.medium); withAnimation(.easeInOut(duration: 0.35)) { recording = true }
    }
    private func stopRecord() {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(.easeInOut(duration: 0.3)) { recording = false }
        newPos = CGPoint(x: 0.5, y: 0.5)
        withAnimation(.spring(response: 0.55, dampingFraction: 0.55)) { born = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.45) {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.62)) { newPos = CGPoint(x: 0.78, y: 0.5) }
        }
    }
    private func runDemo() {
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 2_400_000_000); dive(into: "Atlas")        // dive into a zone
            try? await Task.sleep(nanoseconds: 2_600_000_000); dive(into: "Atlas/Q3")     // deeper (recursive)
            try? await Task.sleep(nanoseconds: 2_600_000_000); select("sprint1")          // open an object inside
            try? await Task.sleep(nanoseconds: 2_800_000_000); select(nil)
            try? await Task.sleep(nanoseconds: 1_000_000_000); jump(to: 0)                // breadcrumb home
        }
    }
}

@main
struct DioramaApp: App {
    var body: some Scene { WindowGroup { Stage() } }
}
