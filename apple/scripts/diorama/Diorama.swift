import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — DELIGHT, expanded. The owner's bar: "premium = I'm delighted when I use it," and the alive
// spring-stage landed it. Now it RESPONDS: tap a meeting and it springs forward to centre, the rest recede,
// and its intelligence blooms out with the same springy character; tap empty and everything springs home.
// Built interactive for the device AND auto-played (env DIO_DEMO=1) so the whole flow records in motion.

extension Color {
    init(hex: UInt, a: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: a)
    }
}

enum Pal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
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

struct Obj: Identifiable { let id: String; let sprite: String; let base: CGFloat; let glow: Color; let home: CGPoint }

enum Mode { case home, focus, recede }

// A hero object: springs in (overshoot), idles forever (breathe/drift/tilt), and reacts to selection —
// growing to centre when focused, shrinking + dimming when something else is.
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
            .contentShape(Rectangle())
            .onTapGesture(perform: onTap)
        }
    }
}

// A clean intelligence card that blooms out of a focused meeting.
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

// The invitation to create: a breathing accent orb with a mic and expanding rings — tap to record.
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

// The listening state — a voice core (breathing orb + expanding rings + a ring of reactive bars), live
// words rising and fading, and a stop control. Premium, calm, alive.
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
                // reactive bars around a circle
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
                    let local = cycle - Double(i) * 0.0
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
    @State private var selected: String? = nil
    @State private var cardsIn = false
    @State private var recording = false
    @State private var born = false                 // a freshly-captured cassette has popped onto the stage
    @State private var newPos = CGPoint(x: 0.5, y: 0.5)

    private let objects = [
        Obj(id: "cassette", sprite: "cassette", base: 150, glow: Pal.accent, home: CGPoint(x: 0.27, y: 0.34)),
        Obj(id: "crystal",  sprite: "crystal",  base: 150, glow: Pal.violet, home: CGPoint(x: 0.74, y: 0.33)),
        Obj(id: "cartridge", sprite: "cartridge", base: 210, glow: Pal.cobalt, home: CGPoint(x: 0.5, y: 0.52)),
    ]
    private let cards: [(String, String, String, Color)] = [
        ("sparkles", "Summary", "Shipped the beta Friday; pricing next week", Pal.accent),
        ("checkmark.circle.fill", "3 Actions", "Send the finance deck to Priya · EOD", Pal.mint),
        ("text.alignleft", "Transcript", "32 min · 3 speakers", Pal.cobalt),
    ]
    private let spring = Animation.spring(response: 0.55, dampingFraction: 0.62)

    private func mode(_ id: String) -> Mode { selected == nil ? .home : (selected == id ? .focus : .recede) }
    private func pos(_ o: Obj, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        selected == o.id ? CGPoint(x: w * 0.5, y: h * 0.27) : CGPoint(x: w * o.home.x, y: h * o.home.y)
    }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack {
                LinearGradient(colors: [Pal.bgTop, Pal.bgMid, Pal.bgBot], startPoint: .top, endPoint: .bottom)
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    RadialGradient(colors: [(selected == nil ? Pal.accent : Pal.cobalt).opacity(0.20 + 0.05 * sin(t * 1.2)), .clear],
                                   center: .init(x: 0.5, y: selected == nil ? 0.43 : 0.27), startRadius: 20, endRadius: w * 0.95)
                        .blendMode(.plusLighter).animation(spring, value: selected)
                }
                Motes()
                Color.clear.contentShape(Rectangle()).onTapGesture { select(nil) }   // tap empty -> home

                // title (hides when focused)
                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 26, weight: .black, design: .rounded)).foregroundStyle(Pal.text)
                    Text("your meetings, alive").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(Pal.muted).tracking(1)
                }
                .opacity(landed && selected == nil ? 1 : 0).offset(y: landed ? 0 : -14)
                .animation(.easeOut(duration: 0.5), value: selected)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.10)

                ForEach(objects.filter { mode($0.id) != .focus }) { o in
                    Hero(obj: o, landed: landed, mode: mode(o.id)) { select(o.id) }
                        .position(pos(o, w, h)).animation(spring, value: selected)
                        .animation(.spring(response: 0.72, dampingFraction: 0.54).delay(idx(o) * 0.13), value: landed)
                }

                // the intelligence cards bloom under the focused object
                if selected != nil {
                    VStack(spacing: 11) {
                        ForEach(Array(cards.enumerated()), id: \.offset) { i, c in
                            InfoCard(icon: c.0, title: c.1, line: c.2, tint: c.3)
                                .scaleEffect(cardsIn ? 1 : 0.4).opacity(cardsIn ? 1 : 0)
                                .offset(y: cardsIn ? 0 : 40)
                                .animation(.spring(response: 0.5, dampingFraction: 0.6).delay(0.08 + Double(i) * 0.07), value: cardsIn)
                        }
                    }
                    .position(x: w * 0.5, y: h * 0.66)
                }

                // the focused object draws on TOP of its cards' origin
                ForEach(objects.filter { mode($0.id) == .focus }) { o in
                    Hero(obj: o, landed: landed, mode: .focus) { select(nil) }
                        .position(pos(o, w, h)).animation(spring, value: selected)
                }

                // a freshly-captured meeting, popped onto the stage
                if born {
                    VStack(spacing: 7) {
                        Sprite(name: "cassette2", size: 132).shadow(color: .black.opacity(0.55), radius: 16, y: 12)
                        Text("New Meeting").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(Pal.text)
                            .padding(.horizontal, 10).padding(.vertical, 5).background(Capsule().fill(.black.opacity(0.35)))
                    }
                    .position(x: w * newPos.x, y: h * newPos.y)
                    .transition(.scale(scale: 0.2).combined(with: .opacity))
                }

                Companion(landed: landed, excited: selected != nil || recording).position(x: w * 0.84, y: h * 0.88)
                if landed && !recording && selected == nil {
                    RecordOrb { startRecord() }.position(x: w * 0.5, y: h * 0.9)
                        .transition(.scale.combined(with: .opacity))
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.55)], center: .center, startRadius: 140, endRadius: 760)
                    .blendMode(.multiply).allowsHitTesting(false)

                // listening — a calm, alive voice state
                if recording {
                    ZStack {
                        Color.black.opacity(0.6).ignoresSafeArea().transition(.opacity)
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
            }
            .ignoresSafeArea()
            .onAppear { landed = true; if ProcessInfo.processInfo.environment["DIO_DEMO"] == "1" { runDemo() } }
        }
        .preferredColorScheme(.dark)
    }

    private func idx(_ o: Obj) -> Double { Double(objects.firstIndex { $0.id == o.id } ?? 0) }
    private func select(_ id: String?) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: id == nil ? .light : .medium).impactOccurred()
        #endif
        withAnimation(spring) { selected = id }
        cardsIn = false
        if id != nil { withAnimation { cardsIn = true } }
    }
    private func startRecord() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        #endif
        withAnimation(.easeInOut(duration: 0.35)) { recording = true }
    }
    private func stopRecord() {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(.easeInOut(duration: 0.3)) { recording = false }
        // the recording crystallises into a new cassette: pop at centre, then settle to a slot
        newPos = CGPoint(x: 0.5, y: 0.5)
        withAnimation(.spring(response: 0.55, dampingFraction: 0.55)) { born = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.45) {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.62)) { newPos = CGPoint(x: 0.5, y: 0.34) }
        }
    }
    private func runDemo() {
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 2_600_000_000); startRecord()      // tap record
            try? await Task.sleep(nanoseconds: 4_200_000_000); stopRecord()       // listen, then stop -> a cassette is born
            try? await Task.sleep(nanoseconds: 2_600_000_000); select("cassette") // open it
            try? await Task.sleep(nanoseconds: 3_200_000_000); select(nil)        // back home
        }
    }
}

@main
struct DioramaApp: App {
    var body: some Scene { WindowGroup { Stage() } }
}
