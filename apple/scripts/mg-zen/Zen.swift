import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HARNESS MIRROR of App/MeetingCapture/DeskMiniGame_Zen.swift — a self-contained @main app that renders
// MG_Zen inside the same frosted ephemeral window the desk launcher supplies, so it can be screenshot in
// the iOS Simulator WITHOUT touching the shared xcodeproj. Keep this in sync with the component. The only
// additions here are the Color(hex:) helper (the app gets it from DesignSystem) and the @main app at the
// bottom. Loop: edit both → ./scripts/mg-zen-shot.sh /tmp/x.png → Read it → iterate to premium + serene.

extension Color {
    init(hex: UInt, a: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: a)
    }
}

// HSM-14 — STILLWATER. A zen reflecting-pond fidget you summon onto the desk during a boring meeting.
// Tap the water to drop a ripple; drag a finger / stylus to draw a trailing wake of ripples. Concentric
// rings expand, soften, and fade, gently overlapping. Beneath, a slow breathing aurora and a drift of
// luminous motes keep the surface alive even when untouched. There is NO score, NO timer, NO fail state —
// it is endlessly idle and soothing, a place to rest your eyes, not a thing to win.
//
// Built to the DeskOS Component Pattern (docs/internal/DESKOS_COMPONENT_PATTERN.md). Honest adaptations
// of the nine laws (a calming toy has no egress, no model call, no harvestable artifact) are noted in the
// handover table. The launcher supplies the ephemeral window + close chrome; MG_Zen renders ONLY content
// and FILLS the frame it is given. Motion is pure-render via TimelineView(.animation) reading a ripple
// store; @Published state is mutated ONLY in gesture handlers + a low-rate prune timer, never in `body`.
//
// One coordinate space (the trap): everything draws inside one Canvas sized to the given GeometryReader,
// in that local space. No screen-anchored, safe-area-ignoring chrome is mixed in.

// MARK: - Model

/// One expanding ring on the water. Stored with a birth time; its radius/opacity are PURE functions of the
/// current clock, so the render is a function of (ripples, now) and we never tick per-frame state.
private struct ZenRipple: Identifiable {
    let id: Int
    let center: CGPoint   // normalized 0…1 of the pond, so it survives resize
    let born: TimeInterval
    let strength: CGFloat // 0.5 (light tap) … 1 (firm); scales reach + brightness
    let tint: Color
}

/// The pond's living state. Ripples are added on touch; an ambient auto-ripple keeps the water breathing
/// when you leave it alone. A timer prunes dead ripples (off the view body). The render itself is stateless.
private final class ZenPond: ObservableObject {
    @Published private(set) var ripples: [ZenRipple] = []
    private var seq = 0
    private var pruneTimer: Timer?
    private var ambientTimer: Timer?

    // a ripple lives this long, then it has fully faded
    static let life: TimeInterval = 4.2
    // calm spectrum the rings are tinted from (cool water tones + the desk's mint/cobalt/violet)
    private let spectrum: [Color] = [
        Color(hex: 0x7FD8E8), Color(hex: 0x5B8DEF), Color(hex: 0x9B6BFF), Color(hex: 0x3ECF8E), Color(hex: 0x86E3D0)
    ]

    /// Simulator-only: drop a believable spray of ripples at varied ages so a screenshot shows the pond
    /// mid-motion (simctl cannot tap). Ages are set in the past so they're already expanded.
    func seedForShot() {
        let now = CACurrentMediaTime()
        let drops: [(CGFloat, CGFloat, TimeInterval, CGFloat)] = [
            (0.46, 0.40, 1.4, 1.0), (0.30, 0.62, 0.7, 0.9), (0.70, 0.32, 0.25, 1.0),
            (0.64, 0.68, 1.9, 0.7), (0.40, 0.34, 2.5, 0.6), (0.78, 0.60, 0.05, 1.0)
        ]
        seq = 0
        ripples = drops.map { d in
            seq += 1
            return ZenRipple(id: seq, center: CGPoint(x: d.0, y: d.1), born: now - d.2,
                             strength: d.3, tint: spectrum[seq % spectrum.count])
        }
    }

    func start() {
        pruneTimer?.invalidate()
        let p = Timer(timeInterval: 1.0, repeats: true) { [weak self] _ in self?.prune() }
        RunLoop.main.add(p, forMode: .common)
        pruneTimer = p

        // ambient breath — a soft ripple drops on its own every few seconds so an untouched pond is never
        // dead. Slightly randomized so it feels like nature, not a metronome.
        scheduleAmbient()
    }
    func stop() { pruneTimer?.invalidate(); pruneTimer = nil; ambientTimer?.invalidate(); ambientTimer = nil }
    deinit { stop() }

    private func scheduleAmbient() {
        ambientTimer?.invalidate()
        let wait = Double.random(in: 2.6...4.4)
        let t = Timer(timeInterval: wait, repeats: false) { [weak self] _ in
            guard let self else { return }
            self.add(at: CGPoint(x: .random(in: 0.18...0.82), y: .random(in: 0.18...0.82)),
                     strength: CGFloat.random(in: 0.4...0.62), ambient: true)
            self.scheduleAmbient()
        }
        RunLoop.main.add(t, forMode: .common)
        ambientTimer = t
    }

    private func prune() {
        let now = CACurrentMediaTime()
        ripples.removeAll { now - $0.born > Self.life }
    }

    /// Add a ripple. `ambient` ones are quieter and don't haptic-buzz.
    func add(at normalized: CGPoint, strength: CGFloat, ambient: Bool = false) {
        seq += 1
        let tint = spectrum[seq % spectrum.count]
        ripples.append(ZenRipple(id: seq, center: normalized, born: CACurrentMediaTime(),
                                 strength: strength, tint: tint))
        // gentle cap so a frantic scribble never costs us
        if ripples.count > 48 { ripples.removeFirst(ripples.count - 48) }
        #if canImport(UIKit)
        if !ambient {
            let g = UIImpactFeedbackGenerator(style: strength > 0.7 ? .light : .soft)
            g.impactOccurred(intensity: 0.5 + Double(strength) * 0.4)
        }
        #endif
    }
}

// MARK: - The view: MG_Zen (the integration contract)

/// Stillwater — the zen reflecting pond. Renders ONLY content and fills the frame the launcher gives it.
public struct MG_Zen: View {
    public static let title = "Stillwater"
    public static let icon = "drop.fill"

    public init() {}

    @StateObject private var pond = ZenPond()
    // for the drag-wake: only spawn a new ripple once the finger has travelled a little, so a drag draws an
    // even string of rings instead of a solid smear. Tracked here, mutated only in the gesture handler.
    @State private var lastWake: CGPoint? = nil

    public var body: some View {
        GeometryReader { geo in
            let size = geo.size
            ZStack {
                // 1. the water bed — a deep, slowly breathing aurora the rings sit in
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    waterBed(t: t, size: size)
                }
                .allowsHitTesting(false)

                // 2. the living surface — motes + every ripple, drawn in ONE Canvas as pure functions of now
                TimelineView(.animation) { tl in
                    let now = tl.date.timeIntervalSinceReferenceDate
                    Canvas { ctx, sz in
                        drawMotes(&ctx, size: sz, t: now)
                        drawRipples(&ctx, size: sz, now: CACurrentMediaTime())
                    }
                }
                .allowsHitTesting(false)

                // 3. a feather-soft vignette + a hairline glass rim so it reads as a pool, not a rectangle
                rim(size: size).allowsHitTesting(false)

                // 4. a barely-there resting hint that dissolves the instant you touch the water
                if pond.ripples.isEmpty {
                    restingHint.transition(.opacity).allowsHitTesting(false)
                }
            }
            .frame(width: size.width, height: size.height)
            .contentShape(Rectangle())
            // ONE gesture (Law: a single gesture). minimumDistance 0 → a tap drops one ripple; a drag draws
            // a wake. Coordinates are normalized so ripples are resize-stable.
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { v in
                        if lastWake == nil {
                            // the first touch — a firm, satisfying drop
                            pond.add(at: norm(v.location, in: size), strength: 1.0)
                            lastWake = v.location
                        } else if let l = lastWake, hypot(v.location.x - l.x, v.location.y - l.y) > 26 {
                            // travelled far enough — leave another bead in the wake
                            pond.add(at: norm(v.location, in: size), strength: 0.7)
                            lastWake = v.location
                        }
                    }
                    .onEnded { _ in lastWake = nil }
            )
        }
        .onAppear {
            pond.start()
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_DESK_ZEN"] == "shot" { pond.seedForShot() }
            #endif
        }
        .onDisappear { pond.stop() }
    }

    private func norm(_ p: CGPoint, in size: CGSize) -> CGPoint {
        CGPoint(x: min(max(p.x / max(size.width, 1), 0), 1),
                y: min(max(p.y / max(size.height, 1), 0), 1))
    }

    // MARK: water bed (breathing aurora)

    private func waterBed(t: TimeInterval, size: CGSize) -> some View {
        // two slow lobes of cool light, drifting on offset sines — gives the deep "lit from within" feel
        let b1 = CGFloat(sin(t * 0.23))
        let b2 = CGFloat(cos(t * 0.17))
        return ZStack {
            // base depth
            LinearGradient(colors: [Color(hex: 0x0A1620), Color(hex: 0x081019), Color(hex: 0x05080D)],
                           startPoint: .top, endPoint: .bottom)
            RadialGradient(colors: [Color(hex: 0x123244).opacity(0.85), .clear], center: .center,
                           startRadius: 4, endRadius: max(size.width, size.height) * 0.8)
            // drifting cool lobe
            RadialGradient(colors: [Color(hex: 0x1E5A6E).opacity(0.55), .clear],
                           center: UnitPoint(x: 0.5 + Double(b1) * 0.28, y: 0.36 + Double(b2) * 0.18),
                           startRadius: 2, endRadius: size.width * 0.62)
            // a violet undertow, slower
            RadialGradient(colors: [Color(hex: 0x3A2A66).opacity(0.4), .clear],
                           center: UnitPoint(x: 0.5 - Double(b2) * 0.26, y: 0.7 + Double(b1) * 0.14),
                           startRadius: 2, endRadius: size.width * 0.7)
        }
        .blur(radius: 0.5)
    }

    // MARK: motes — slow luminous flecks drifting on the surface

    private func drawMotes(_ ctx: inout GraphicsContext, size: CGSize, t: TimeInterval) {
        let count = 14
        for i in 0..<count {
            let fi = Double(i)
            // each mote has its own slow lissajous drift + a breathing twinkle
            let px = 0.5 + 0.42 * sin(t * (0.07 + fi * 0.004) + fi * 1.7)
            let py = 0.5 + 0.42 * cos(t * (0.05 + fi * 0.0035) + fi * 2.3)
            let twinkle = 0.35 + 0.45 * (0.5 + 0.5 * sin(t * (0.6 + fi * 0.05) + fi))
            let r = 1.1 + 1.6 * (0.5 + 0.5 * sin(t * 0.3 + fi))
            let c = CGPoint(x: px * size.width, y: py * size.height)
            let dot = Path(ellipseIn: CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2))
            ctx.fill(dot, with: .color(Color(hex: 0xBFEFFF).opacity(twinkle * 0.5)))
            // a soft halo
            let hr = r * 3.5
            let halo = Path(ellipseIn: CGRect(x: c.x - hr, y: c.y - hr, width: hr * 2, height: hr * 2))
            ctx.fill(halo, with: .radialGradient(
                Gradient(colors: [Color(hex: 0x9FE6FF).opacity(twinkle * 0.16), .clear]),
                center: c, startRadius: 0, endRadius: hr))
        }
    }

    // MARK: ripples — concentric expanding rings, radius/opacity pure functions of (born, now)

    private func drawRipples(_ ctx: inout GraphicsContext, size: CGSize, now: TimeInterval) {
        let maxR = min(size.width, size.height) * 0.92
        for rp in pond.ripples {
            let age = now - rp.born
            guard age >= 0, age <= ZenPond.life else { continue }
            let p = age / ZenPond.life                       // 0 → 1 over the life
            let ease = 1 - pow(1 - p, 2.2)                    // expand fast then settle (ease-out)
            let center = CGPoint(x: rp.center.x * size.width, y: rp.center.y * size.height)
            let baseR = ease * maxR * (0.5 + Double(rp.strength) * 0.5)
            // hold the ring bright for the first third, then fall away (sqrt-ish tail) — rings linger
            // long enough to overlap and read as real water, instead of vanishing in a blink.
            let fade = p < 0.18 ? 1.0 : pow(1 - (p - 0.18) / 0.82, 1.4)
            let str = Double(0.5 + rp.strength * 0.5)
            // three nested rings, each trailing the last, so one touch reads as a real water ring set
            for k in 0..<3 {
                let lag = Double(k) * 0.13
                let lp = p - lag
                guard lp > 0 else { continue }
                let lr = baseR - Double(k) * 15
                guard lr > 1 else { continue }
                let ringFade = max(0, fade) * (1 - Double(k) * 0.22)
                let alpha = ringFade * str
                let lw = (3.0 - Double(k) * 0.7) * (0.7 + Double(rp.strength) * 0.5)
                let ring = Path(ellipseIn: CGRect(x: center.x - lr, y: center.y - lr, width: lr * 2, height: lr * 2))
                // a soft glow halo just behind the crisp stroke gives the ring a wet, luminous edge
                ctx.stroke(ring, with: .color(rp.tint.opacity(alpha * 0.32)), lineWidth: lw * 3.2)
                ctx.stroke(ring, with: .color(rp.tint.opacity(min(1, alpha * 1.25))), lineWidth: lw)
            }
            // a soft inner glow at the impact point that blooms then fades — the "plink" of the drop
            let glowP = min(1, p * 2.2)
            let glowFade = max(0, 1 - glowP) * Double(rp.strength)
            if glowFade > 0.01 {
                let gr = 12.0 + ease * 30
                let glow = Path(ellipseIn: CGRect(x: center.x - gr, y: center.y - gr, width: gr * 2, height: gr * 2))
                ctx.fill(glow, with: .radialGradient(
                    Gradient(colors: [rp.tint.opacity(glowFade * 0.55), .clear]),
                    center: center, startRadius: 0, endRadius: gr))
            }
        }
    }

    // MARK: rim + vignette

    private func rim(size: CGSize) -> some View {
        ZStack {
            // inward vignette to seat the pool
            RadialGradient(colors: [.clear, .clear, Color.black.opacity(0.32)],
                           center: .center, startRadius: min(size.width, size.height) * 0.34,
                           endRadius: max(size.width, size.height) * 0.72)
            // a hairline glass meniscus
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .strokeBorder(
                    LinearGradient(colors: [.white.opacity(0.16), .white.opacity(0.03)],
                                   startPoint: .top, endPoint: .bottom), lineWidth: 0.75)
                .padding(0.5)
        }
    }

    // MARK: resting hint

    private var restingHint: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let pulse = 0.45 + 0.35 * sin(t * 1.3)
            VStack(spacing: 9) {
                Image(systemName: "hand.draw")
                    .font(.system(size: 20, weight: .regular))
                    .foregroundStyle(Color(hex: 0xBFEFFF).opacity(pulse))
                Text("touch the water")
                    .font(.system(size: 12, weight: .semibold, design: .rounded))
                    .foregroundStyle(Color(hex: 0xBFEFFF).opacity(pulse * 0.9))
                    .tracking(1.5)
            }
        }
    }
}

// MARK: - Harness app — the desk behind, the ephemeral window the launcher would supply, MG_Zen inside.

@main
struct ZenHarnessApp: App {
    var body: some Scene {
        WindowGroup { ZenHarnessRoot() }
    }
}

private struct ZenHarnessRoot: View {
    var body: some View {
        ZStack {
            // a stand-in for the live desk so we judge MG_Zen as it floats ON the desk, not on black.
            LinearGradient(colors: [Color(hex: 0x0B0D12), Color(hex: 0x16111F), Color(hex: 0x090A0E)],
                           startPoint: .top, endPoint: .bottom).ignoresSafeArea()
            // a couple of faint desk "objects" for context behind the frosted pane
            ForEach(0..<3, id: \.self) { i in
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(Color.white.opacity(0.04))
                    .frame(width: 120, height: 80)
                    .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(.white.opacity(0.06), lineWidth: 1))
                    .rotationEffect(.degrees(Double(i) * 7 - 7))
                    .offset(x: CGFloat(i) * 70 - 80, y: CGFloat(i) * 120 - 180)
            }

            // THE EPHEMERAL WINDOW (what the launcher supplies): a frosted pane, a tiny title bar + close,
            // and MG_Zen filling the content. ~260x300.
            VStack(spacing: 0) {
                HStack(spacing: 7) {
                    Image(systemName: MG_Zen.icon).font(.system(size: 12, weight: .bold))
                        .foregroundStyle(Color(hex: 0x7FD8E8))
                    Text(MG_Zen.title).font(.system(size: 13, weight: .heavy, design: .rounded))
                        .foregroundStyle(Color(hex: 0xF4ECE0))
                    Spacer(minLength: 0)
                    Image(systemName: "xmark").font(.system(size: 10, weight: .black))
                        .foregroundStyle(Color(hex: 0xF4ECE0).opacity(0.85))
                        .frame(width: 24, height: 24).background(Circle().fill(.white.opacity(0.08)))
                }
                .padding(.horizontal, 12).frame(height: 38)

                MG_Zen()
                    .frame(width: 260 - 12, height: 300 - 38 - 12)
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    .padding(.horizontal, 6).padding(.bottom, 12)
            }
            .frame(width: 260, height: 300)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(Color(hex: 0x123244).opacity(0.05)))
                    .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                    .shadow(color: .black.opacity(0.3), radius: 14, y: 8)
            )
        }
    }
}
