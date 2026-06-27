import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — ORBIT GATE. A tiny one-finger AIM / DEXTERITY game you summon onto the desk during a boring
// meeting. A glowing comet circles a central well at a fixed angular speed; rotating "gate" arcs sweep the
// ring with you. HOLD anywhere to push the comet OUTWARD against the well's pull; RELEASE and it falls back
// IN. Thread the comet through the GAP in each gate as it sweeps past — touch the solid part of an arc and
// the run ends. The longer you survive the faster it spins and the tighter the gaps. Twitchy, fair, ~20–60s
// rounds, instantly grokkable. Built to the DeskOS Component Pattern (docs/internal/DESKOS_COMPONENT_PATTERN.md).
//
// Integration contract (the launcher supplies an ephemeral window + close; we render ONLY game content and
// FILL the frame):
//   • public struct MG_Aim: View  — init() no args, MG_Aim.title, MG_Aim.icon.
//   • internal AimGame state object; the game LOOP runs on a Timer (RunLoop .common) via .onAppear /
//     .onDisappear — NEVER tick or mutate @Published inside `body` (that stalls SwiftUI + bursts physics).
//   • ONE gesture: a single DragGesture(minimumDistance: 0) — pressed = hold (push out), released = fall in.
//   • Restart on lose; best score via @AppStorage("hs.mg.aim.best").
//
// Per-law honesty (a game has no LLM/egress, so a few laws adapt — reconcile, don't drift):
//   • Law 1/2 fill the launcher's anchored ephemeral window (no full-screen of our own, no window chrome).
//   • Law 3 alive-in-motion: orbit spin, comet trail, gate sweep, pull-string to center, win/lose juice.
//   • Law 8 "one badge of truth": no egress for a game; the single quiet badge is a SCORE / BEST chip.
//   • Law 9 gated: every effectful thing is a touch; nothing leaves the device or acts on the world.

// MARK: - Palette (mirrors DioPal locally so the harness can compile standalone; in the app target the
// real DioPal + Color(hex:) exist — these names are file-private so there is no collision).

private enum AimPal {
    static let accent = Color(hex: 0xFF6B35)
    static let cobalt = Color(hex: 0x5B8DEF)
    static let violet = Color(hex: 0x9B6BFF)
    static let mint   = Color(hex: 0x3ECF8E)
    static let text   = Color(hex: 0xF4ECE0)
    static let muted  = Color(hex: 0x9C93A8)
    static let danger = Color(hex: 0xFF4D6D)
    static let gold   = Color(hex: 0xFFC857)
}

// MARK: - Model

private enum AimPhase { case ready, playing, dead }

/// One sweeping ring of obstacle: a solid arc with a single GAP the comet must thread.
private struct Gate: Identifiable {
    let id: Int
    var radius: CGFloat        // distance from center (the comet shares this same ring family)
    var angle: CGFloat         // current rotation of the gate (radians)
    var spin: CGFloat          // angular velocity (radians / sec) — signed
    var gapCenter: CGFloat     // gap center offset from `angle` (radians)
    var gapHalf: CGFloat       // half-width of the gap (radians)
    var tint: Color
    var passed: Bool = false   // scored once the comet's angle has crossed it cleanly
    var bornT: Double = 0      // grow-in animation 0→1
}

/// All game state + the fixed-step "physics". The view is a pure render of this; the Timer drives tick().
private final class AimGame: ObservableObject {
    // Logical field is a square; center is the well.
    let field: CGFloat
    var center: CGPoint { CGPoint(x: field / 2, y: field / 2) }
    var maxR: CGFloat { field / 2 - 14 }      // outer travel limit for the comet
    let minR: CGFloat = 26                     // inner limit (just outside the well)

    // The comet rides one ring radius `r`, sweeping at a fixed angular speed; HOLD pushes r out.
    @Published var cometAngle: CGFloat = -.pi / 2   // start at top
    @Published var cometR: CGFloat = 64
    @Published var holding = false
    @Published var trail: [CGPoint] = []

    @Published var gates: [Gate] = []
    @Published var score = 0
    @Published var phase: AimPhase = .ready
    @Published var shake: CGFloat = 0
    @Published var flash: Double = 0          // green pulse on a clean thread
    @Published var wellPulse: Double = 0      // the central well bobs on a near-miss / score
    @Published var elapsed: Double = 0

    let cometRadius: CGFloat = 7
    private var gateId = 0
    private var spawnAccum: Double = 0

    // tuning — the comet's own constant orbital sweep + the radial spring
    private let cometSpin: CGFloat = 1.55      // rad/sec the comet travels around the ring
    private let pullSpeed: CGFloat = 150       // rad-independent: radius units/sec inward when released
    private let pushSpeed: CGFloat = 165       // radius units/sec outward while held

    private var ticker: Timer?
    private var lastStep: TimeInterval = 0
    var frozen = false   // simulator-only: pose a mid-run frame without physics advancing

    init(field: CGFloat) {
        self.field = field
        cometR = (minR + maxR) / 2
    }

    // The REAL game loop. .common mode so it keeps stepping during the steering touch.
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

    // MARK: control (one finger)

    func press() {
        switch phase {
        case .ready:  begin()
        case .dead:   reset(); begin()
        case .playing: holding = true
        }
    }
    func release() { holding = false }

    private func begin() {
        phase = .playing
        holding = true              // the press that started us also counts as a hold
        cometAngle = -.pi / 2
        cometR = (minR + maxR) / 2
        gates.removeAll()
        trail.removeAll()
        score = 0
        elapsed = 0
        spawnAccum = 0.9            // first gate arrives soon
    }

    func reset() {
        phase = .ready
        gates.removeAll()
        trail.removeAll()
        score = 0
        elapsed = 0
        shake = 0
    }

    func cometPoint() -> CGPoint {
        CGPoint(x: center.x + cos(cometAngle) * cometR,
                y: center.y + sin(cometAngle) * cometR)
    }

    // difficulty ramps gently with time survived
    private var difficulty: Double { min(1, elapsed / 45) }
    private var spawnEvery: Double { 1.35 - 0.55 * difficulty }    // 1.35s → 0.80s
    private var gapHalfNow: CGFloat { CGFloat(0.46 - 0.16 * difficulty) }  // radians
    private var gateSpinNow: CGFloat { CGFloat(0.55 + 0.85 * difficulty) }

    private func spawnGate() {
        gateId += 1
        // place the gate on a ring band the comet can reach; alternate inner/outer for variety
        let band = Double.random(in: 0...1)
        let r = minR + (maxR - minR) * CGFloat(0.25 + 0.65 * band)
        let dir: CGFloat = Bool.random() ? 1 : -1
        let g = Gate(id: gateId,
                     radius: r,
                     angle: CGFloat.random(in: 0...(2 * .pi)),
                     spin: gateSpinNow * dir,
                     gapCenter: CGFloat.random(in: 0...(2 * .pi)),
                     gapHalf: gapHalfNow,
                     tint: [AimPal.cobalt, AimPal.violet, AimPal.mint, AimPal.gold].randomElement()!,
                     bornT: 0)
        gates.append(g)
    }

    // MARK: the fixed-step loop

    func tick(_ now: TimeInterval) {
        if lastStep == 0 { lastStep = now }
        var dt = now - lastStep
        lastStep = now

        // decay juice regardless of phase
        if shake > 0 { shake = max(0, shake - CGFloat(dt) * 55) }
        if flash > 0 { flash = max(0, flash - dt * 3) }
        if wellPulse > 0 { wellPulse = max(0, wellPulse - dt * 4) }
        for i in gates.indices where gates[i].bornT < 1 { gates[i].bornT = min(1, gates[i].bornT + dt * 4) }

        guard phase == .playing, !frozen else { return }
        if dt > 0.05 { dt = 0.05 }
        let fdt = CGFloat(dt)
        elapsed += dt

        // radial motion — held pushes out, released falls in (toward the well's pull)
        if holding { cometR += pushSpeed * fdt } else { cometR -= pullSpeed * fdt }
        if cometR > maxR { cometR = maxR }
        if cometR < minR {                 // sucked into the well = dead
            cometR = minR
            die()
            return
        }
        // constant orbital sweep
        cometAngle += cometSpin * fdt
        if cometAngle > 2 * .pi { cometAngle -= 2 * .pi }

        // advance gates, spawn, collide, score
        for i in gates.indices {
            gates[i].angle += gates[i].spin * fdt
        }
        spawnAccum += dt
        if spawnAccum >= spawnEvery {
            spawnAccum = 0
            spawnGate()
            // cull the oldest if the field is busy
            if gates.count > 5 { gates.removeFirst() }
        }
        collideAndScore()

        // trail
        trail.append(cometPoint())
        if trail.count > 14 { trail.removeFirst(trail.count - 14) }
    }

    private func angDiff(_ a: CGFloat, _ b: CGFloat) -> CGFloat {
        var d = (a - b).truncatingRemainder(dividingBy: 2 * .pi)
        if d > .pi { d -= 2 * .pi }
        if d < -.pi { d += 2 * .pi }
        return abs(d)
    }

    private func collideAndScore() {
        let ringBand: CGFloat = 9          // how "thick" a gate ring is for collision
        for i in gates.indices {
            let g = gates[i]
            // is the comet currently overlapping this gate's ring radius?
            if abs(cometR - g.radius) <= ringBand + cometRadius {
                // the gap's absolute center on the ring is angle + gapCenter
                let gapAbs = g.angle + g.gapCenter
                let d = angDiff(cometAngle, gapAbs)
                if d <= g.gapHalf {
                    // threading the gap cleanly — score once
                    if !gates[i].passed {
                        gates[i].passed = true
                        score += 1
                        flash = 1
                        wellPulse = 1
                        haptic(.light)
                    }
                } else {
                    // hit the solid arc
                    die()
                    return
                }
            }
        }
    }

    private func die() {
        phase = .dead
        shake = 16
        wellPulse = 1
        holding = false
        haptic(.heavy)
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// MARK: - The public game view (FILLS the launcher's frame; no chrome of its own)

public struct MG_Aim: View {
    public static let title = "Orbit Gate"
    public static let icon  = "circle.dotted.circle"

    @AppStorage("hs.mg.aim.best") private var best = 0
    @StateObject private var game = AimGame(field: 280)

    public init() {}

    public var body: some View {
        GeometryReader { geo in
            let side = min(geo.size.width, geo.size.height)
            ZStack {
                backdrop
                // the play field is a centered square; everything is drawn in ITS coordinate space.
                fieldView
                    .frame(width: game.field, height: game.field)
                    .scaleEffect(side / (game.field + 16))     // fit the field to the smaller dimension
                hud(width: geo.size.width)
            }
            .frame(width: geo.size.width, height: geo.size.height)
            .contentShape(Rectangle())
            // ONE gesture: pressed = hold, released = fall.
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in if !game.holding && game.phase == .playing { /* keep held */ }; game.press() }
                    .onEnded { _ in game.release() }
            )
        }
        .onAppear {
            game.start()
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_MG_AIM"] == "play" { game.seedMidRun() }
            #endif
        }
        .onDisappear { game.stop() }
        .onChange(of: game.score) { _, s in if s > best { best = s } }
        .onChange(of: game.phase) { _, p in if p == .dead, game.score > best { best = game.score } }
    }

    // a soft radial vignette so the orbit pops; the desk reads through the launcher window behind us.
    private var backdrop: some View {
        RadialGradient(colors: [AimPal.violet.opacity(0.10), Color.black.opacity(0.18)],
                       center: .center, startRadius: 8, endRadius: 220)
    }

    // MARK: field

    private var fieldView: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let s = game.shake
            let sx = s > 0 ? CGFloat(sin(t * 80)) * s : 0
            let sy = s > 0 ? CGFloat(cos(t * 73)) * s : 0
            ZStack {
                orbitGuide
                gatesLayer
                cometTrail
                comet
                well(t: t)
                phaseOverlay.allowsHitTesting(false)
            }
            .frame(width: game.field, height: game.field)
            .offset(x: sx, y: sy)
        }
    }

    // faint reference ring at the comet's current radius — reads as the "track" the comet rides.
    private var orbitGuide: some View {
        Circle()
            .strokeBorder(AimPal.text.opacity(0.06), lineWidth: 1)
            .frame(width: game.cometR * 2, height: game.cometR * 2)
            .position(game.center)
            .animation(.linear(duration: 0.02), value: game.cometR)
    }

    private var gatesLayer: some View {
        ForEach(game.gates) { g in
            GateArc(gate: g, center: game.center)
                .opacity(g.bornT)
        }
    }

    private var cometTrail: some View {
        ForEach(Array(game.trail.enumerated()), id: \.offset) { idx, p in
            let f = CGFloat(idx) / CGFloat(max(1, game.trail.count))
            Circle()
                .fill(AimPal.accent.opacity(Double(f) * 0.45))
                .frame(width: game.cometRadius * 2 * f, height: game.cometRadius * 2 * f)
                .position(p)
        }
    }

    private var comet: some View {
        let p = game.cometPoint()
        return ZStack {
            Circle()
                .fill(AimPal.accent.opacity(0.30))
                .frame(width: game.cometRadius * 4, height: game.cometRadius * 4)
                .blur(radius: 4)
            Circle()
                .fill(RadialGradient(colors: [.white, AimPal.gold, AimPal.accent],
                                     center: .init(x: 0.35, y: 0.3), startRadius: 0, endRadius: game.cometRadius))
                .frame(width: game.cometRadius * 2, height: game.cometRadius * 2)
                .overlay(Circle().strokeBorder(.white.opacity(0.7), lineWidth: 1))
                .shadow(color: AimPal.accent.opacity(0.8), radius: 6)
        }
        .position(p)
    }

    // the central well: a gravity sink that bobs on score/death; a thin "pull string" to the comet shows
    // the inward force the player is fighting (juicy + legible).
    private func well(t: TimeInterval) -> some View {
        let breathe = 1 + 0.05 * sin(t * 1.6) + game.wellPulse * 0.18
        let p = game.cometPoint()
        return ZStack {
            // pull string
            Path { path in
                path.move(to: game.center)
                path.addLine(to: p)
            }
            .stroke(LinearGradient(colors: [AimPal.violet.opacity(0.45), AimPal.accent.opacity(0.0)],
                                   startPoint: .center, endPoint: .topTrailing),
                    style: StrokeStyle(lineWidth: 1.5, dash: [2, 4]))
            .opacity(game.phase == .playing ? 0.9 : 0.0)

            Circle()
                .fill(RadialGradient(colors: [AimPal.violet, Color(hex: 0x3A2A66), Color.black.opacity(0.85)],
                                     center: .center, startRadius: 1, endRadius: 22))
                .frame(width: 30, height: 30)
                .overlay(Circle().strokeBorder(AimPal.violet.opacity(0.7), lineWidth: 1.5))
                .overlay(Circle().fill(.white.opacity(game.wellPulse * 0.4)))
                .scaleEffect(breathe)
                .shadow(color: AimPal.violet.opacity(0.7), radius: 10 + game.wellPulse * 8)
                .position(game.center)
        }
    }

    @ViewBuilder private var phaseOverlay: some View {
        switch game.phase {
        case .ready:
            overlayCard {
                VStack(spacing: 7) {
                    TimelineView(.animation) { tl in
                        let t = tl.date.timeIntervalSinceReferenceDate
                        Image(systemName: "hand.point.up.left.fill")
                            .font(.system(size: 24, weight: .bold))
                            .foregroundStyle(AimPal.accent)
                            .scaleEffect(1 + 0.12 * sin(t * 2.4))
                    }
                    Text("Hold to push out").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(AimPal.text)
                    Text("release to fall in · thread the gaps").font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(AimPal.muted)
                }
            }
        case .dead:
            overlayCard {
                VStack(spacing: 6) {
                    Image(systemName: "burst.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(AimPal.danger)
                    Text("Lost in the well").font(.system(size: 16, weight: .black, design: .rounded)).foregroundStyle(AimPal.text)
                    Text("\(game.score) gates").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(AimPal.mint)
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise").font(.system(size: 11, weight: .bold))
                        Text("Tap to play again").font(.system(size: 12, weight: .heavy, design: .rounded))
                    }
                    .foregroundStyle(.white).padding(.horizontal, 14).frame(height: 32)
                    .background(Capsule().fill(LinearGradient(colors: [AimPal.accent, Color(hex: 0xC24A1E)], startPoint: .top, endPoint: .bottom)))
                    .padding(.top, 2)
                }
            }
        case .playing:
            EmptyView()
        }
    }

    @ViewBuilder private func overlayCard(@ViewBuilder _ c: () -> some View) -> some View {
        c()
            .padding(.horizontal, 20).padding(.vertical, 15)
            .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.black.opacity(0.55))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
            .position(game.center)
    }

    // MARK: HUD — the single quiet badge (Law 8 adapted): SCORE / BEST.
    private func hud(width: CGFloat) -> some View {
        VStack {
            HStack(spacing: 8) {
                badge(icon: "circle.hexagongrid.fill", value: "\(game.score)", tint: AimPal.accent)
                badge(icon: "crown.fill", value: "\(max(best, game.score))", tint: AimPal.gold)
                Spacer(minLength: 0)
            }
            .padding(.horizontal, 12)
            .padding(.top, 10)
            Spacer()
        }
        .frame(width: width)
        // a green ring pulse on a clean thread
        .overlay(
            Circle()
                .strokeBorder(AimPal.mint.opacity(game.flash * 0.5), lineWidth: 3)
                .frame(width: game.field * 0.9, height: game.field * 0.9)
                .allowsHitTesting(false)
        )
    }

    private func badge(icon: String, value: String, tint: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.system(size: 9, weight: .black)).foregroundStyle(tint)
            Text(value).font(.system(size: 12, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(AimPal.text)
        }
        .padding(.horizontal, 9).frame(height: 24)
        .background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(0.08), lineWidth: 1)))
    }
}

// MARK: - A single gate arc (solid ring with a gap), drawn as a stroked Path.

private struct GateArc: View {
    let gate: Gate
    let center: CGPoint

    var body: some View {
        let gapAbs = gate.angle + gate.gapCenter
        // the solid part runs from gapEnd around to gapStart (i.e. everywhere EXCEPT the gap)
        let start = gapAbs + gate.gapHalf
        let end = gapAbs - gate.gapHalf + 2 * .pi
        ZStack {
            // soft underglow
            Path { p in
                p.addArc(center: center, radius: gate.radius,
                         startAngle: .radians(Double(start)), endAngle: .radians(Double(end)), clockwise: false)
            }
            .stroke(gate.tint.opacity(0.30), style: StrokeStyle(lineWidth: 12, lineCap: .round))
            .blur(radius: 4)

            // the solid arc
            Path { p in
                p.addArc(center: center, radius: gate.radius,
                         startAngle: .radians(Double(start)), endAngle: .radians(Double(end)), clockwise: false)
            }
            .stroke(LinearGradient(colors: [gate.tint, gate.tint.opacity(0.7)], startPoint: .top, endPoint: .bottom),
                    style: StrokeStyle(lineWidth: 7, lineCap: .round))
            .shadow(color: gate.tint.opacity(0.5), radius: 3)

            // tiny bright caps at the gap mouth so the opening is unmistakable
            ForEach([start, end - 2 * .pi], id: \.self) { a in
                Circle()
                    .fill(.white.opacity(0.85))
                    .frame(width: 4, height: 4)
                    .position(x: center.x + cos(a) * gate.radius, y: center.y + sin(a) * gate.radius)
            }
        }
    }
}

// MARK: - Simulator staging (mid-run frame for screenshots; never touches device behavior)

extension AimGame {
    func seedMidRun() {
        phase = .playing
        holding = true
        frozen = true
        score = 9
        elapsed = 14
        // comet up-and-right, mid-band, threading a gap
        let ca: CGFloat = -.pi / 3
        cometAngle = ca
        cometR = 92
        // place a gate the comet is actively threading: its gap centered on the comet's angle
        gates = [
            Gate(id: 1, radius: 58,  angle: 0.0, spin: 0.9,  gapCenter: 1.2,  gapHalf: 0.46, tint: AimPal.cobalt, bornT: 1),
            Gate(id: 2, radius: 92,  angle: 0.0, spin: -1.0, gapCenter: ca,   gapHalf: 0.40, tint: AimPal.violet, bornT: 1),
            Gate(id: 3, radius: 124, angle: 0.0, spin: 0.8,  gapCenter: 2.4,  gapHalf: 0.42, tint: AimPal.mint,   bornT: 0.7),
        ]
        flash = 0.85
        wellPulse = 0.5
        trail = (0..<12).map { k in
            let f = CGFloat(k) / 12
            let a = ca - 0.55 * (1 - f)
            let r = cometR - 26 * (1 - f)
            return CGPoint(x: center.x + cos(a) * r, y: center.y + sin(a) * r)
        }
    }
}

// MARK: - Color(hex:) — only when compiled standalone in the harness; the app target already defines it.
#if HS_MG_AIM_STANDALONE
extension Color {
    init(hex: UInt) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: 1)
    }
}
#endif
