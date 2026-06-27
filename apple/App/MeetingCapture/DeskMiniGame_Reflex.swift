import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — PULSE. A tiny, glanceable REFLEX / TIMING game you summon onto the desk during a boring meeting
// while everything else keeps running. One of the six council mini-games; this one is the reflex lane.
// Built to the DeskOS Component Pattern canon (docs/internal/DESKOS_COMPONENT_PATTERN.md) — the nine laws,
// the ambient-recorder shape, with the honest game adaptations noted inline.
//
// THE GAME, in one breath: a needle sweeps around a dial. A glowing target arc waits on the ring. TAP the
// instant the needle crosses the glow. A dead-center "PERFECT" stacks a combo and speeds the needle up; a
// graze still scores but resets the combo; a clean miss costs a life. Three lives, then tap-to-play-again.
// Instantly understood ("tap when the needle hits the glow"), forgiving, pausable (it's all taps), no audio,
// no network, premium + juicy. It lives in an even smaller window than Arkanoid — ~260x300.
//
// INTEGRATION CONTRACT (so the launcher can plug all six in):
//   • Public View `MG_Reflex`, init() no args, renders ONLY the content and FILLS its frame. The launcher
//     supplies the frosted ephemeral window + close button — we draw NO window chrome / title bar / close.
//   • `static let title` / `static let icon` (an SF Symbol).
//   • Game state in an internal ObservableObject; the loop runs on a Timer (RunLoop.common) started in
//     .onAppear, invalidated in .onDisappear. NEVER mutate @Published in `body` (the Arkanoid lesson —
//     that stalls SwiftUI and fires the loop in bursts).
//   • Self-contained restart; best persisted via @AppStorage("hs.mg.reflex.best").
//
// THE NINE LAWS, adapted for an ephemeral game (a game has no model call, no egress, no harvestable card):
//   1 Anchored, never modal — fills the launcher's small floating pane; never full-screen; no own scrim.
//   2 Radiate from the anchor — everything blooms from ONE locus: the dial centre. Score/combo/lives orbit it.
//   3 Quiet at rest, alive in motion — the launcher owns the tucked rest token; in-window it BREATHES (needle
//     sweep, target glow pulse, ring shimmer, perfect-ring burst, screen-shake on a miss).
//   4 Intent before action — the only fork is play / play-again, offered as a small hovering card over the dial.
//   5 Act in place, on a scope — the one control is a single tap on the dial; scope is the target window itself.
//   6 Harvest, never dead-end — a game's keepable artifact is the persisted BEST score (the run's afterlife).
//   7 Compose, don't reinvent — reuses the desk grammar: the DioPal palette, .ultraThinMaterial-friendly tints,
//     SF-symbol + rounded type, the same juice vocabulary as the recorder/Arkanoid. No new global mechanism.
//   8 One badge of truth — no egress to state; the one quiet badge is a BEST chip (the score-truth badge),
//     mirroring Arkanoid's adaptation (honest: a game has no local/cloud egress).
//   9 Gated, never autonomous — every effectful thing is a tap; nothing leaves the device or acts on the world.
//   the trap — drawn in ONE coordinate space (a single GeometryReader, dial centred in it); no screen-anchored
//     safe-area chrome mixed in.

// MARK: - Local palette mirror (kept tiny + self-contained per Law 7; the desk's DioPal is the source of truth)

private enum RfxPal {
    static let accent = Color(hex: 0xFF6B35)
    static let cobalt = Color(hex: 0x5B8DEF)
    static let violet = Color(hex: 0x9B6BFF)
    static let mint   = Color(hex: 0x3ECF8E)
    static let text   = Color(hex: 0xF4ECE0)
    static let muted  = Color(hex: 0x9C93A8)
    static let rose   = Color(hex: 0xFF4D6D)
    static let gold   = Color(hex: 0xFFC857)
}

private enum RfxPhase { case ready, playing, over }

// MARK: - The game state + the fixed-step loop (one place; the view is a pure render of it)

private final class RfxGame: ObservableObject {
    // The dial is laid out in a UNIT circle; the view scales it to the geometry. Angles are radians,
    // 0 at the top (12 o'clock), increasing clockwise.
    @Published var needle: Double = 0          // current needle angle (rad, clockwise from top)
    @Published var targetCenter: Double = 0    // centre of the glowing target arc (rad)
    @Published var targetHalf: Double = 0.42   // half-width of the target arc (rad) — shrinks as combo grows

    @Published var score = 0
    @Published var combo = 0
    @Published var bestCombo = 0
    @Published var lives = 3
    @Published var phase: RfxPhase = .ready

    // juice
    @Published var shake: CGFloat = 0          // decays to 0; drives a tiny screen-shake on a miss
    @Published var hitFlash: Double = 0        // >0 just after a hit; expands a ring + flashes the target
    @Published var hitKind: HitKind = .none    // colours the flash / floating word
    @Published var floatT: Double = 0          // 0..1 life of the floating "PERFECT/GOOD/MISS" word
    @Published var floatWord: String = ""
    @Published var floatColor: Color = RfxPal.mint
    @Published var lastResultAngle: Double = 0 // where the needle was at the tap (for the float anchor)

    enum HitKind { case none, perfect, good, miss }

    // tuning
    private let baseSpeed: Double = 1.9        // rad / sec at combo 0
    private var direction: Double = 1          // flips on some rounds for variety
    private var spawnedAfterHit = true

    private var ticker: Timer?
    private var lastStep: TimeInterval = 0

    var best: Int { get { UserDefaults.standard.integer(forKey: "hs.mg.reflex.best") }
                    set { UserDefaults.standard.set(newValue, forKey: "hs.mg.reflex.best") } }

    // The needle's current angular speed — grows with combo, capped so it stays fair/forgiving.
    private var speed: Double {
        let ramp = min(Double(combo) * 0.14, 1.9)   // +0.14 rad/s per combo, capped
        return baseSpeed + ramp
    }
    // The "perfect" window is a generous fraction of the (shrinking) target — forgiving by design.
    private var perfectHalf: Double { max(targetHalf * 0.34, 0.10) }

    // MARK: loop — on a Timer in .common so a finger-drag elsewhere can't starve it; never mutate in body.
    func start() {
        lastStep = 0
        ticker?.invalidate()
        let t = Timer(timeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in
            self?.tick(CACurrentMediaTime())
        }
        RunLoop.main.add(t, forMode: .common)
        ticker = t
    }
    func stop() { ticker?.invalidate(); ticker = nil }
    deinit { ticker?.invalidate() }

    init() { reset() }

    func reset() {
        score = 0; combo = 0; bestCombo = 0; lives = 3
        targetHalf = 0.42
        needle = -.pi / 2 * 0   // start at top
        needle = 0
        direction = 1
        phase = .ready
        spawnTarget(initial: true)
        shake = 0; hitFlash = 0; floatT = 0; hitKind = .none
    }

    func begin() {
        guard phase == .ready else { return }
        phase = .playing
    }

    func tapDial() {
        switch phase {
        case .ready: begin()
        case .over:  reset()
        case .playing: judge()
        }
    }

    // place a fresh target somewhere ahead of the needle so there is always a beat to react to
    private func spawnTarget(initial: Bool) {
        // pick an angle at least ~1.1 rad ahead of the needle in the travel direction, with spread
        let lead = (initial ? 1.6 : (1.1 + Double.random(in: 0...2.0)))
        targetCenter = wrap(needle + direction * lead)
        // every few combos, the target narrows AND the spin may flip — escalating, still fair
        if !initial {
            targetHalf = max(0.18, 0.42 - Double(combo) * 0.012)
            if combo > 0 && combo % 5 == 0 { direction *= -1 }
        }
        spawnedAfterHit = true
    }

    private func judge() {
        let d = angularDist(needle, targetCenter)
        lastResultAngle = needle
        if d <= perfectHalf {
            registerHit(.perfect)
        } else if d <= targetHalf {
            registerHit(.good)
        } else {
            registerHit(.miss)
        }
    }

    private func registerHit(_ kind: HitKind) {
        hitKind = kind
        hitFlash = 1
        floatT = 1
        switch kind {
        case .perfect:
            combo += 1
            bestCombo = max(bestCombo, combo)
            let gained = 100 + combo * 20      // combo multiplier baked into the gain
            score += gained
            floatWord = combo >= 2 ? "PERFECT x\(combo)" : "PERFECT"
            floatColor = RfxPal.mint
            haptic(.medium)
            spawnTarget(initial: false)
        case .good:
            score += 30
            combo = 0
            targetHalf = 0.42                  // ease back off after a graze (forgiving)
            floatWord = "GOOD"
            floatColor = RfxPal.gold
            haptic(.light)
            spawnTarget(initial: false)
        case .miss:
            combo = 0
            lives -= 1
            shake = 12
            targetHalf = 0.42
            floatWord = "MISS"
            floatColor = RfxPal.rose
            haptic(.heavy)
            if lives <= 0 {
                if score > best { best = score }
                phase = .over
            } else {
                spawnTarget(initial: false)
            }
        case .none: break
        }
    }

    func tick(_ now: TimeInterval) {
        if lastStep == 0 { lastStep = now }
        var dt = now - lastStep
        lastStep = now
        if dt > 0.05 { dt = 0.05 }

        // decay juice every frame regardless of phase
        if shake > 0 { shake = max(0, shake - CGFloat(dt) * 48) }
        if hitFlash > 0 { hitFlash = max(0, hitFlash - dt * 2.4) }
        if floatT > 0 { floatT = max(0, floatT - dt * 1.3) }

        guard phase == .playing else { return }
        needle = wrap(needle + direction * speed * dt)
    }

    // MARK: angle helpers
    private func wrap(_ a: Double) -> Double {
        var x = a.truncatingRemainder(dividingBy: 2 * .pi)
        if x < 0 { x += 2 * .pi }
        return x
    }
    private func angularDist(_ a: Double, _ b: Double) -> Double {
        var d = abs(wrap(a) - wrap(b))
        if d > .pi { d = 2 * .pi - d }
        return d
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// MARK: - The public game view

public struct MG_Reflex: View {
    public static let title: String = "Pulse"
    public static let icon: String = "scope"

    @StateObject private var game = RfxGame()
    @AppStorage("hs.mg.reflex.best") private var best: Int = 0

    public init() {}

    public init(seedMidGame: Bool) {
        let g = RfxGame()
        if seedMidGame { Self.seed(g) }
        _game = StateObject(wrappedValue: g)
    }

    // A believable mid-game frame for the Simulator screenshot (simctl can't tap): mid-combo, needle
    // approaching a glowing target, a fresh PERFECT float, two lives, a real best on the badge.
    private static func seed(_ g: RfxGame) {
        g.phase = .playing
        g.score = 1840
        g.combo = 7
        g.bestCombo = 7
        g.lives = 2
        g.targetHalf = 0.30
        g.targetCenter = .pi * 0.18          // upper-right-ish
        g.needle = .pi * 0.10                // just before the target — "about to nail it"
        g.hitFlash = 0.7
        g.hitKind = .perfect
        g.floatT = 0.7
        g.floatWord = "PERFECT x7"
        g.floatColor = RfxPal.mint
        g.lastResultAngle = .pi * 1.18   // lower-left, clear of the HUD, for a legible PERFECT float
        if g.best < 2400 { UserDefaults.standard.set(2400, forKey: "hs.mg.reflex.best") }
    }

    public var body: some View {
        GeometryReader { geo in
            // ONE coordinate space. Everything is anchored to the dial centre.
            let side = min(geo.size.width, geo.size.height)
            let center = CGPoint(x: geo.size.width / 2, y: geo.size.height / 2)
            // the dial radius leaves room for the orbiting HUD
            let R = side * 0.40

            TimelineView(.animation) { tl in
                let now = tl.date.timeIntervalSinceReferenceDate
                let s = game.shake
                let sx = s > 0 ? CGFloat(sin(now * 80)) * s : 0
                let sy = s > 0 ? CGFloat(cos(now * 73)) * s : 0

                ZStack {
                    // a whisper of darkening at the centre so the dial reads on the frosted pane
                    RadialGradient(colors: [Color.black.opacity(0.16), Color.black.opacity(0.02)],
                                   center: .center, startRadius: 2, endRadius: side * 0.6)
                        .allowsHitTesting(false)

                    hud(center: center, R: R, now: now)
                    dial(center: center, R: R, now: now)
                    overlay(center: center, R: R)
                        .allowsHitTesting(false)   // overlays never steal the tap (the Arkanoid lesson)
                }
                .offset(x: sx, y: sy)
                .frame(width: geo.size.width, height: geo.size.height)
                .contentShape(Rectangle())
                // ONE gesture — a single tap on the whole pane. Reflex games are taps, not drags.
                .onTapGesture { game.tapDial() }
            }
        }
        .onAppear {
            game.start()
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_MG_REFLEX"] == "play" {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { game.tapDial() }
            }
            #endif
        }
        .onDisappear { game.stop() }
    }

    // MARK: the dial — the single radiant locus (Law 2)

    @ViewBuilder
    private func dial(center: CGPoint, R: CGFloat, now: Double) -> some View {
        let pulse = 0.5 + 0.5 * sin(now * 2.2)
        ZStack {
            // ambient glow under the dial
            Circle()
                .fill(RadialGradient(colors: [RfxPal.violet.opacity(0.16), .clear], center: .center, startRadius: 2, endRadius: R * 1.7))
                .frame(width: R * 2.2, height: R * 2.2)
                .position(center)

            // the track ring
            Circle()
                .strokeBorder(RfxPal.text.opacity(0.10), lineWidth: 6)
                .frame(width: R * 2, height: R * 2)
                .position(center)

            // tick marks around the ring (texture + read of speed)
            ForEach(0..<36, id: \.self) { i in
                let major = i % 3 == 0
                let a = Double(i) / 36 * 2 * .pi
                Capsule()
                    .fill(RfxPal.text.opacity(major ? 0.28 : 0.12))
                    .frame(width: major ? 2.4 : 1.4, height: major ? 9 : 5)
                    .offset(y: -(R - 2))
                    .rotationEffect(.radians(a))
                    .position(center)
            }

            // the GLOWING TARGET ARC — the thing you aim the tap at
            targetArc(center: center, R: R, pulse: pulse)

            // the hit-flash ring that bursts outward on a perfect/good/miss
            if game.hitFlash > 0 {
                let f = game.hitFlash
                let c: Color = game.hitKind == .perfect ? RfxPal.mint : (game.hitKind == .good ? RfxPal.gold : RfxPal.rose)
                Circle()
                    .strokeBorder(c.opacity(Double(f) * 0.8), lineWidth: 3)
                    .frame(width: R * 2 * CGFloat(1 + (1 - f) * 0.7), height: R * 2 * CGFloat(1 + (1 - f) * 0.7))
                    .position(center)
            }

            // the NEEDLE
            needleView(center: center, R: R)

            // the hub
            Circle()
                .fill(RadialGradient(colors: [RfxPal.text, RfxPal.muted.opacity(0.6)], center: .init(x: 0.35, y: 0.3), startRadius: 0, endRadius: 9))
                .frame(width: 16, height: 16)
                .overlay(Circle().strokeBorder(.white.opacity(0.5), lineWidth: 1))
                .shadow(color: RfxPal.violet.opacity(0.6), radius: 6)
                .position(center)
        }
    }

    // The target arc is drawn as a thick stroked arc segment, glowing & pulsing.
    @ViewBuilder
    private func targetArc(center: CGPoint, R: CGFloat, pulse: Double) -> some View {
        // SwiftUI angles: 0 = +x (3 o'clock), CW in screen space. Our model: 0 = top, CW.
        // model angle m -> screen angle = m - 90°.
        let startDeg = (game.targetCenter - game.targetHalf) * 180 / .pi - 90
        let endDeg = (game.targetCenter + game.targetHalf) * 180 / .pi - 90
        let perfDeg0 = (game.targetCenter - game.targetHalf * 0.34) * 180 / .pi - 90
        let perfDeg1 = (game.targetCenter + game.targetHalf * 0.34) * 180 / .pi - 90
        let pop = game.hitFlash > 0 && game.hitKind != .miss ? game.hitFlash : 0

        ZStack {
            // wide forgiving band
            ArcShape(startDeg: startDeg, endDeg: endDeg, radius: R)
                .stroke(RfxPal.cobalt.opacity(0.5 + 0.25 * pulse + pop * 0.4),
                        style: StrokeStyle(lineWidth: 11, lineCap: .round))
                .shadow(color: RfxPal.cobalt.opacity(0.7), radius: 7 + CGFloat(pulse) * 4)
            // the PERFECT core
            ArcShape(startDeg: perfDeg0, endDeg: perfDeg1, radius: R)
                .stroke(RfxPal.mint.opacity(0.9), style: StrokeStyle(lineWidth: 11, lineCap: .round))
                .shadow(color: RfxPal.mint.opacity(0.9), radius: 8 + CGFloat(pulse) * 5)
        }
        .frame(width: R * 2 + 22, height: R * 2 + 22)
        .position(center)
    }

    @ViewBuilder
    private func needleView(center: CGPoint, R: CGFloat) -> some View {
        // screen angle = model - 90°. Draw a tapering bar from the hub outward, pointing up, then rotate.
        ZStack {
            // soft sweep wedge behind the needle for motion
            Path { p in
                p.move(to: .zero)
                p.addLine(to: CGPoint(x: 0, y: -R))
            }
            // the needle itself
            Capsule()
                .fill(LinearGradient(colors: [RfxPal.accent, Color(hex: 0xFFB070)], startPoint: .bottom, endPoint: .top))
                .frame(width: 4, height: R + 4)
                .offset(y: -(R + 4) / 2)
                .shadow(color: RfxPal.accent.opacity(0.8), radius: 6)
            // a bright tip
            Circle()
                .fill(RadialGradient(colors: [.white, RfxPal.accent], center: .center, startRadius: 0, endRadius: 5))
                .frame(width: 10, height: 10)
                .offset(y: -(R))
                .shadow(color: RfxPal.accent, radius: 6)
        }
        .rotationEffect(.radians(game.needle))   // model 0 = top, CW → matches an up-pointing needle rotated CW
        .position(center)
    }

    // MARK: HUD orbiting the locus (Law 2) — score, combo, lives, the best-chip badge (Law 8 adapted)

    @ViewBuilder
    private func hud(center: CGPoint, R: CGFloat, now: Double) -> some View {
        let topY = center.y - R - 26
        let botY = center.y + R + 24

        // SCORE above the dial
        VStack(spacing: 1) {
            Text("\(game.score)")
                .font(.system(size: 30, weight: .black, design: .rounded).monospacedDigit())
                .foregroundStyle(RfxPal.text)
                .shadow(color: RfxPal.violet.opacity(0.5), radius: 8)
            comboPip(now: now)
        }
        .position(x: center.x, y: topY)

        // LIVES + BEST badge below the dial, on one orbit line
        HStack(spacing: 12) {
            HStack(spacing: 3) {
                ForEach(0..<3, id: \.self) { i in
                    Image(systemName: i < game.lives ? "heart.fill" : "heart")
                        .font(.system(size: 11, weight: .black))
                        .foregroundStyle(i < game.lives ? RfxPal.rose : RfxPal.muted.opacity(0.45))
                }
            }
            // Law 8 ADAPTED — no egress in a game; the one quiet badge is the BEST (score-truth) chip.
            HStack(spacing: 4) {
                Image(systemName: "crown.fill").font(.system(size: 8, weight: .black))
                Text("BEST \(max(best, game.best))")
                    .font(.system(size: 10, weight: .heavy, design: .rounded).monospacedDigit())
            }
            .foregroundStyle(RfxPal.gold)
            .padding(.horizontal, 8).frame(height: 22)
            .background(Capsule().fill(RfxPal.gold.opacity(0.12)).overlay(Capsule().strokeBorder(RfxPal.gold.opacity(0.3), lineWidth: 1)))
        }
        .position(x: center.x, y: botY)
    }

    @ViewBuilder
    private func comboPip(now: Double) -> some View {
        if game.combo >= 2 {
            let beat = 1 + CGFloat(sin(now * 9)) * 0.06
            HStack(spacing: 4) {
                Image(systemName: "flame.fill").font(.system(size: 10, weight: .black))
                Text("\(game.combo)x").font(.system(size: 13, weight: .black, design: .rounded))
            }
            .foregroundStyle(RfxPal.accent)
            .padding(.horizontal, 9).frame(height: 22)
            .background(Capsule().fill(RfxPal.accent.opacity(0.16)).overlay(Capsule().strokeBorder(RfxPal.accent.opacity(0.5), lineWidth: 1)))
            .scaleEffect(beat)
        } else {
            Text("tap when the needle hits the glow")
                .font(.system(size: 9.5, weight: .semibold, design: .rounded))
                .foregroundStyle(RfxPal.muted)
        }
    }

    // MARK: the centred overlays (ready / game-over) + the floating result word

    @ViewBuilder
    private func overlay(center: CGPoint, R: CGFloat) -> some View {
        // floating PERFECT/GOOD/MISS word rising from where the tap landed
        if game.floatT > 0 {
            let life = game.floatT
            let a = game.lastResultAngle - .pi / 2     // to screen space
            let rr = R * 0.62
            let px = center.x + cos(a) * rr
            let py = center.y + sin(a) * rr - CGFloat(1 - life) * 26
            Text(game.floatWord)
                .font(.system(size: 14, weight: .black, design: .rounded))
                .foregroundStyle(game.floatColor)
                .shadow(color: game.floatColor.opacity(0.8), radius: 6)
                .opacity(life)
                .scaleEffect(0.8 + life * 0.4)
                .position(x: px, y: py)
        }

        switch game.phase {
        case .ready:
            overlayCard(center: center) {
                VStack(spacing: 8) {
                    TimelineView(.animation) { tl in
                        let t = tl.date.timeIntervalSinceReferenceDate
                        Image(systemName: "scope").font(.system(size: 26, weight: .bold))
                            .foregroundStyle(RfxPal.violet)
                            .rotationEffect(.degrees(sin(t * 1.6) * 8))
                    }
                    Text("Pulse").font(.system(size: 18, weight: .black, design: .rounded)).foregroundStyle(RfxPal.text)
                    Text("Tap the instant the needle\ncrosses the glowing arc.")
                        .multilineTextAlignment(.center)
                        .font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(RfxPal.muted)
                    startPill(label: "Tap to start", icon: "play.fill")
                }
            }
        case .over:
            overlayCard(center: center) {
                VStack(spacing: 7) {
                    Image(systemName: "scope").font(.system(size: 22, weight: .bold)).foregroundStyle(RfxPal.rose)
                    Text("Time's up").font(.system(size: 16, weight: .black, design: .rounded)).foregroundStyle(RfxPal.text)
                    HStack(spacing: 10) {
                        statTile("\(game.score)", "score", RfxPal.text)
                        statTile("\(game.bestCombo)x", "best combo", RfxPal.accent)
                    }
                    if game.score >= max(best, game.best) && game.score > 0 {
                        Text("NEW BEST").font(.system(size: 10, weight: .black, design: .rounded))
                            .foregroundStyle(RfxPal.gold).tracking(1.5)
                    }
                    startPill(label: "Play again", icon: "arrow.clockwise")
                }
            }
        case .playing:
            EmptyView()
        }
    }

    @ViewBuilder
    private func statTile(_ big: String, _ small: String, _ tint: Color) -> some View {
        VStack(spacing: 1) {
            Text(big).font(.system(size: 16, weight: .black, design: .rounded).monospacedDigit()).foregroundStyle(tint)
            Text(small).font(.system(size: 9, weight: .semibold, design: .rounded)).foregroundStyle(RfxPal.muted)
        }
        .padding(.horizontal, 11).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 11, style: .continuous).fill(.white.opacity(0.05)))
    }

    @ViewBuilder
    private func startPill(label: String, icon: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 11, weight: .bold))
            Text(label).font(.system(size: 12, weight: .heavy, design: .rounded))
        }
        .foregroundStyle(.white).padding(.horizontal, 14).frame(height: 32)
        .background(Capsule().fill(LinearGradient(colors: [RfxPal.violet, Color(hex: 0x6B43C2)], startPoint: .top, endPoint: .bottom)))
        .padding(.top, 2)
    }

    @ViewBuilder
    private func overlayCard(center: CGPoint, @ViewBuilder _ c: () -> some View) -> some View {
        c()
            .padding(.horizontal, 20).padding(.vertical, 15)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.black.opacity(0.62))
                    .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1))
            )
            .position(center)
    }
}

// MARK: - Arc shape (a stroked ring segment), our one drawing primitive

private struct ArcShape: Shape {
    let startDeg: Double
    let endDeg: Double
    let radius: CGFloat
    func path(in rect: CGRect) -> Path {
        var p = Path()
        let c = CGPoint(x: rect.midX, y: rect.midY)
        p.addArc(center: c, radius: radius, startAngle: .degrees(startDeg), endAngle: .degrees(endDeg), clockwise: false)
        return p
    }
}

// MARK: - Color(hex:) — self-contained (the desk defines this too; harmless to mirror locally in this file's scope)
#if HS_MG_REFLEX_STANDALONE
extension Color {
    init(hex: UInt, a: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: a)
    }
}
#endif
