import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — DESK ARKANOID. A pinnable, stylus-playable Breakout you summon onto the desk during a boring
// meeting while everything else keeps running. Built to the DeskOS Component Pattern canon
// (docs/internal/DESKOS_COMPONENT_PATTERN.md) — the nine laws, the ambient-recorder shape:
//
//   • Rest state (Law 1, 3): a tiny tucked launcher token (DeskArkanoidToken). One tap opens the game.
//   • Active body (Law 1, 2, 4): a COMPACT floating window (~340pt) — never full-screen, the desk stays
//     drawn behind it. Draggable to PIN anywhere; the pinned point is its home (persisted in
//     @AppStorage "hs.desk.arkanoid.pos"). It RADIATES from that anchor; a header bar minimizes back to
//     the token or closes it.
//   • Gameplay (Law 5 "act in place"): classic Breakout — slide the paddle with the stylus or a finger
//     (a DragGesture maps x to the paddle), a ball bounces off walls/paddle/bricks, a grid of breakable
//     bricks in DioPal tints, score + lives, clean lose/win + tap-to-play-again. It is actually FUN.
//   • Motion & juice (Law 3, build-checklist #11): a real game loop (TimelineView(.animation) + a fixed
//     physics step), a ball trail, a brick pop-flash/scale, a paddle glow, a screen-shake on life loss.
//   • The badge (Law 8 ADAPTED): a game has no egress, so the one quiet badge is a playful status badge
//     (SCORE / LIVES) instead of a local/cloud egress chip. Nothing acts on the world (Law 9) — every
//     effectful thing is a tap. (Adaptation noted honestly per the canon's "reconcile, don't drift".)
//   • One coordinate space (the trap): the whole component is drawn inside ONE GeometryReader and placed
//     with a single `.position(pin)`; nothing mixes screen-anchored safe-area chrome with it.
//
// Self-contained: reuses DioPal + DeskSprite from the desk, declares no new global mechanism. To wire it
// into DioStage, see the integration snippet in the handover report (a @State + an @AppStorage + a token
// placement + one overlay block).

// MARK: - Model

private struct ArkBrick: Identifiable {
    let id: Int
    let col: Int, row: Int
    var alive: Bool = true
    var hits: Int           // how many hits left (1 or 2)
    let tint: Color
    var popT: Double = 0    // >0 while playing the break flash
}

private enum ArkPhase { case ready, playing, lost, won }

/// The whole game state + the fixed-step physics. Kept in one place so the view is a pure render of it.
private final class ArkGame: ObservableObject {
    // logical play field (points, in the window's content space)
    let fieldW: CGFloat
    let fieldH: CGFloat

    // brick grid
    let cols = 7
    let rows = 4
    let brickH: CGFloat = 18
    let brickGap: CGFloat = 5
    let topInset: CGFloat = 10

    // entities
    @Published var bricks: [ArkBrick] = []
    @Published var paddleX: CGFloat        // center x
    @Published var ballPos: CGPoint
    @Published var ballVel: CGVector
    @Published var trail: [CGPoint] = []
    @Published var score = 0
    @Published var lives = 3
    @Published var phase: ArkPhase = .ready
    @Published var shake: CGFloat = 0      // decays toward 0; drives screen-shake
    @Published var paddleGlow: Double = 0  // flashes on a paddle hit

    let paddleW: CGFloat = 64
    let paddleH: CGFloat = 12
    let ballR: CGFloat = 6
    var paddleY: CGFloat { fieldH - 26 }

    private var lastStep: TimeInterval = 0
    private let speed: CGFloat = 250       // points / sec
    private var ticker: Timer?            // the REAL game loop — drives tick() off the view body

    // Run the loop on a timer in .common mode so it keeps stepping during paddle-drag (touch tracking),
    // and so we NEVER mutate @Published state inside SwiftUI's view-update pass (that stalls + bursts).
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

    init(fieldW: CGFloat, fieldH: CGFloat) {
        self.fieldW = fieldW
        self.fieldH = fieldH
        self.paddleX = fieldW / 2
        self.ballPos = CGPoint(x: fieldW / 2, y: fieldH - 44)
        self.ballVel = .zero
        layoutBricks()
    }

    private let tints: [Color] = [DioPal.accent, DioPal.cobalt, DioPal.violet, DioPal.mint]

    func layoutBricks() {
        var out: [ArkBrick] = []
        let usableW = fieldW - brickGap * CGFloat(cols + 1)
        let bw = usableW / CGFloat(cols)
        _ = bw
        var id = 0
        for r in 0..<rows {
            for c in 0..<cols {
                let tint = tints[r % tints.count]
                let hits = r == 0 ? 2 : 1   // the top row is tougher (two-hit), a little texture
                out.append(ArkBrick(id: id, col: c, row: r, hits: hits, tint: tint))
                id += 1
            }
        }
        bricks = out
    }

    func brickRect(_ b: ArkBrick) -> CGRect {
        let usableW = fieldW - brickGap * CGFloat(cols + 1)
        let bw = usableW / CGFloat(cols)
        let x = brickGap + CGFloat(b.col) * (bw + brickGap)
        let y = topInset + CGFloat(b.row) * (brickH + brickGap)
        return CGRect(x: x, y: y, width: bw, height: brickH)
    }

    // MARK: control

    func reset() {
        score = 0; lives = 3; phase = .ready
        layoutBricks()
        parkBall()
    }

    func parkBall() {
        ballPos = CGPoint(x: paddleX, y: paddleY - ballR - 2)
        ballVel = .zero
    }

    func launch() {
        guard phase == .ready else { return }
        phase = .playing
        // launch up-and-slightly-sideways
        let dir: CGFloat = Bool.random() ? 1 : -1
        ballVel = CGVector(dx: 0.45 * dir, dy: -0.9)
        normalizeVel()
    }

    func tapPlayField() {
        switch phase {
        case .ready: launch()
        case .lost, .won: reset()
        case .playing: break
        }
    }

    func movePaddle(to x: CGFloat) {
        let half = paddleW / 2
        paddleX = min(max(x, half), fieldW - half)
        if phase == .ready { ballPos.x = paddleX }
    }

    private func normalizeVel() {
        let m = sqrt(ballVel.dx * ballVel.dx + ballVel.dy * ballVel.dy)
        guard m > 0 else { return }
        ballVel.dx /= m; ballVel.dy /= m
    }

    // MARK: the fixed-step loop

    func tick(_ now: TimeInterval) {
        if lastStep == 0 { lastStep = now }
        var dt = now - lastStep
        lastStep = now
        // clamp + decay juice regardless of phase
        if shake > 0 { shake = max(0, shake - CGFloat(dt) * 60) }
        if paddleGlow > 0 { paddleGlow = max(0, paddleGlow - dt * 3) }
        for i in bricks.indices where bricks[i].popT > 0 { bricks[i].popT = max(0, bricks[i].popT - dt * 4) }
        guard phase == .playing else { return }
        if dt > 0.05 { dt = 0.05 }   // avoid tunneling on a hitch

        // sub-step for stable collisions
        let steps = 3
        let sdt = CGFloat(dt) / CGFloat(steps)
        for _ in 0..<steps { physicsStep(sdt) }

        // trail
        trail.append(ballPos)
        if trail.count > 12 { trail.removeFirst(trail.count - 12) }
    }

    private func physicsStep(_ dt: CGFloat) {
        ballPos.x += ballVel.dx * speed * dt
        ballPos.y += ballVel.dy * speed * dt

        // walls
        if ballPos.x - ballR < 0 { ballPos.x = ballR; ballVel.dx = abs(ballVel.dx) }
        if ballPos.x + ballR > fieldW { ballPos.x = fieldW - ballR; ballVel.dx = -abs(ballVel.dx) }
        if ballPos.y - ballR < 0 { ballPos.y = ballR; ballVel.dy = abs(ballVel.dy) }

        // floor — lose a life
        if ballPos.y - ballR > fieldH {
            loseLife()
            return
        }

        // paddle
        let pTop = paddleY - paddleH / 2
        let pLeft = paddleX - paddleW / 2
        let pRight = paddleX + paddleW / 2
        if ballVel.dy > 0,
           ballPos.y + ballR >= pTop, ballPos.y - ballR <= paddleY + paddleH / 2,
           ballPos.x >= pLeft - ballR, ballPos.x <= pRight + ballR {
            ballPos.y = pTop - ballR
            // angle by where it struck the paddle (classic Breakout feel)
            let rel = (ballPos.x - paddleX) / (paddleW / 2)   // -1 … 1
            let clamped = min(max(rel, -0.92), 0.92)
            ballVel = CGVector(dx: clamped, dy: -(1 - abs(clamped) * 0.5))
            normalizeVel()
            paddleGlow = 1
            haptic(.light)
        }

        // bricks
        for i in bricks.indices where bricks[i].alive {
            let r = brickRect(bricks[i]).insetBy(dx: -ballR, dy: -ballR)
            if r.contains(ballPos) {
                // decide reflection axis by smaller penetration
                let br = brickRect(bricks[i])
                let dxL = abs(ballPos.x - br.minX), dxR = abs(ballPos.x - br.maxX)
                let dyT = abs(ballPos.y - br.minY), dyB = abs(ballPos.y - br.maxY)
                let minX = min(dxL, dxR), minY = min(dyT, dyB)
                if minX < minY { ballVel.dx = -ballVel.dx } else { ballVel.dy = -ballVel.dy }
                hitBrick(i)
                break   // one brick per sub-step
            }
        }
    }

    private func hitBrick(_ i: Int) {
        bricks[i].hits -= 1
        bricks[i].popT = 1
        if bricks[i].hits <= 0 {
            bricks[i].alive = false
            score += 100
            haptic(.medium)
        } else {
            score += 25
            haptic(.light)
        }
        if !bricks.contains(where: { $0.alive }) {
            phase = .won
            haptic(.heavy)
        }
    }

    private func loseLife() {
        lives -= 1
        shake = 14
        trail.removeAll()
        haptic(.heavy)
        if lives <= 0 {
            phase = .lost
        } else {
            phase = .ready
            parkBall()
        }
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// MARK: - The rest state: a tiny tucked launcher token (Laws 1, 3)

/// Quiet at rest. A little brick-and-paddle glyph + a "Play" whisper. One tap opens the game window.
struct DeskArkanoidToken: View {
    let onOpen: () -> Void
    var body: some View {
        VStack(spacing: 4) {
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                let bob = CGFloat(sin(t * 1.1) * 1.5)
                ZStack {
                    Circle().fill(RadialGradient(colors: [DioPal.violet.opacity(0.4), .clear], center: .center, startRadius: 2, endRadius: 34))
                        .frame(width: 64, height: 64).opacity(0.5 + 0.4 * sin(t * 1.6))
                    // a 2x3 mini brick wall + a paddle + a ball — the game in miniature
                    VStack(spacing: 2) {
                        ForEach(0..<2, id: \.self) { r in
                            HStack(spacing: 2) {
                                ForEach(0..<3, id: \.self) { c in
                                    RoundedRectangle(cornerRadius: 2, style: .continuous)
                                        .fill([DioPal.accent, DioPal.cobalt, DioPal.violet][(r + c) % 3])
                                        .frame(width: 9, height: 5)
                                }
                            }
                        }
                        Circle().fill(.white).frame(width: 4, height: 4).padding(.top, 1)
                        RoundedRectangle(cornerRadius: 2).fill(DioPal.text.opacity(0.85)).frame(width: 18, height: 4)
                    }
                    .frame(width: 46, height: 46)
                    .background(RoundedRectangle(cornerRadius: 13, style: .continuous)
                        .fill(LinearGradient(colors: [Color(hex: 0x1B1626), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                        .overlay(RoundedRectangle(cornerRadius: 13, style: .continuous).strokeBorder(DioPal.violet.opacity(0.55), lineWidth: 1.3)))
                    .offset(y: -bob)
                    .shadow(color: .black.opacity(0.5), radius: 10, y: 6)
                }
                .frame(width: 64, height: 64)
            }
            Text("Play").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
        }
        .contentShape(Rectangle())
        .onTapGesture {
            #if canImport(UIKit)
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
            #endif
            onOpen()
        }
    }
}

// MARK: - The active body: the pinnable floating game window (Laws 1, 2, 4)

struct DeskArkanoidWindow: View {
    let onMinimize: () -> Void
    let onClose: () -> Void
    /// the screen size, so we can clamp the pin inside the desk
    let screen: CGSize
    /// persisted pin, normalized 0…1 of the screen (so it survives rotation/size changes)
    @Binding var pinNX: Double
    @Binding var pinNY: Double

    private let winW: CGFloat = 340
    private var winH: CGFloat { 300 }
    // play field is the window minus the header + the padding
    private let headerH: CGFloat = 44
    private let pad: CGFloat = 14

    @StateObject private var game: ArkGame
    @State private var dragStart: CGPoint? = nil   // header-drag (move the window)

    init(onMinimize: @escaping () -> Void, onClose: @escaping () -> Void,
         screen: CGSize, pinNX: Binding<Double>, pinNY: Binding<Double>,
         seedMidGame: Bool = false) {
        self.onMinimize = onMinimize
        self.onClose = onClose
        self.screen = screen
        self._pinNX = pinNX
        self._pinNY = pinNY
        let fieldW: CGFloat = 340 - 14 * 2
        let fieldH: CGFloat = 300 - 44 - 14
        let g = ArkGame(fieldW: fieldW, fieldH: fieldH)
        if seedMidGame { Self.seed(g) }
        _game = StateObject(wrappedValue: g)
    }

    private static func seed(_ g: ArkGame) {
        // a believable mid-game frame for the Simulator screenshot: some bricks broken, a score, the
        // ball in flight with a trail, lives spent. (We cannot tap/drag in simctl.)
        g.phase = .playing
        g.score = 1450
        g.lives = 2
        for i in g.bricks.indices {
            // clear the bottom-left wedge to look mid-game
            let b = g.bricks[i]
            if (b.row >= 2 && b.col <= 3) || (b.row == 1 && b.col <= 1) { g.bricks[i].alive = false }
            if b.row == 0 && b.col == 5 { g.bricks[i].popT = 0.8 }   // one mid-pop
        }
        g.paddleX = g.fieldW * 0.42
        g.ballPos = CGPoint(x: g.fieldW * 0.5, y: g.fieldH * 0.56)
        g.ballVel = CGVector(dx: 0.6, dy: -0.8)
        g.trail = (0..<10).map { k in
            let f = CGFloat(k) / 10
            return CGPoint(x: g.fieldW * 0.5 - 0.6 * 90 * (1 - f), y: g.fieldH * 0.56 + 0.8 * 90 * (1 - f))
        }
    }

    private var pin: CGPoint {
        CGPoint(x: CGFloat(pinNX) * screen.width, y: CGFloat(pinNY) * screen.height)
    }

    var body: some View {
        // the game LOOP runs on a timer (game.start), NOT in this body — mutating @Published during a view
        // update is what stalled it and made physics fire in bursts. TimelineView here only renders the shake.
        TimelineView(.animation) { tl in
            let s = game.shake
            let sx = s > 0 ? CGFloat(sin(tl.date.timeIntervalSinceReferenceDate * 80)) * s : 0
            let sy = s > 0 ? CGFloat(cos(tl.date.timeIntervalSinceReferenceDate * 73)) * s : 0
            windowBody
                .frame(width: winW, height: winH)
                .background(windowChrome)
                .offset(x: sx, y: sy)
                .position(pin)
        }
        .onAppear {
            game.start()
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_DESK_ARCADE"] == "play" {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { game.tapPlayField() }
            }
            #endif
        }
        .onDisappear { game.stop() }
    }

    // EPHEMERAL container (follows the record-button philosophy): a frosted pane that lets the desk read
    // through it, a hairline edge, a soft short shadow — it floats ON the desk, it is not a heavy window.
    private var windowChrome: some View {
        RoundedRectangle(cornerRadius: 22, style: .continuous)
            .fill(.ultraThinMaterial)
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(DioPal.violet.opacity(0.05)))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
            .shadow(color: .black.opacity(0.28), radius: 12, y: 6)
    }

    private var windowBody: some View {
        VStack(spacing: 0) {
            header
            playField
                .frame(width: winW - pad * 2, height: winH - headerH - pad)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .padding(.horizontal, pad)
                .padding(.bottom, pad)
        }
    }

    // header — title + the score/lives status BADGE + minimize + close. The drag handle that MOVES the
    // window to PIN it lives here (so dragging the play field still slides the paddle).
    private var header: some View {
        HStack(spacing: 9) {
            Image(systemName: "gamecontroller.fill").font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.violet)
            Text("Arkanoid").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            statusBadge
            Spacer(minLength: 0)
            Button(action: onMinimize) {
                Image(systemName: "minus").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9))
                    .frame(width: 28, height: 28).background(Circle().fill(.white.opacity(0.08)))
            }.buttonStyle(.plain)
            Button(action: onClose) {
                Image(systemName: "xmark").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9))
                    .frame(width: 28, height: 28).background(Circle().fill(.white.opacity(0.08)))
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 14)
        .frame(height: headerH)
        .contentShape(Rectangle())
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onChanged { v in
                    if dragStart == nil { dragStart = pin }
                    let np = CGPoint(x: (dragStart?.x ?? pin.x) + v.translation.width,
                                     y: (dragStart?.y ?? pin.y) + v.translation.height)
                    // clamp so the window stays on the desk
                    let cx = min(max(np.x, winW / 2 + 6), screen.width - winW / 2 - 6)
                    let cy = min(max(np.y, winH / 2 + 30), screen.height - winH / 2 - 6)
                    pinNX = Double(cx / screen.width)
                    pinNY = Double(cy / screen.height)
                }
                .onEnded { _ in dragStart = nil }
        )
    }

    // Law 8 ADAPTED — a game has no egress; the one quiet badge is a playful SCORE / LIVES chip.
    private var statusBadge: some View {
        HStack(spacing: 8) {
            HStack(spacing: 3) {
                Image(systemName: "star.fill").font(.system(size: 8, weight: .black))
                Text("\(game.score)").font(.system(size: 11, weight: .heavy, design: .rounded).monospacedDigit()).fixedSize()
            }.foregroundStyle(DioPal.accent)
            HStack(spacing: 2) {
                ForEach(0..<3, id: \.self) { i in
                    Image(systemName: i < game.lives ? "heart.fill" : "heart")
                        .font(.system(size: 8, weight: .black))
                        .foregroundStyle(i < game.lives ? Color(hex: 0xFF4D6D) : DioPal.muted.opacity(0.5))
                }
            }
        }
        .padding(.horizontal, 9).frame(height: 24)
        .background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(0.08), lineWidth: 1)))
    }

    // the play field — the canvas + the paddle-drag + the ready/win/lose overlays
    private var playField: some View {
        ZStack {
            // a whisper of darkening for brick contrast — the frosted pane + desk still read through
            LinearGradient(colors: [Color.black.opacity(0.14), Color.black.opacity(0.06)], startPoint: .top, endPoint: .bottom)

            // bricks
            ForEach(game.bricks) { b in
                if b.alive {
                    let r = game.brickRect(b)
                    let pop = b.popT
                    RoundedRectangle(cornerRadius: 4, style: .continuous)
                        .fill(LinearGradient(colors: [b.tint.opacity(b.hits > 1 ? 1 : 0.92), b.tint.opacity(0.62)], startPoint: .top, endPoint: .bottom))
                        .overlay(RoundedRectangle(cornerRadius: 4, style: .continuous).strokeBorder(.white.opacity(b.hits > 1 ? 0.5 : 0.22), lineWidth: b.hits > 1 ? 1.2 : 0.8))
                        .overlay(RoundedRectangle(cornerRadius: 4, style: .continuous).fill(.white.opacity(pop * 0.85)))   // pop flash
                        .frame(width: r.width, height: r.height)
                        .scaleEffect(1 + pop * 0.12)
                        .shadow(color: b.tint.opacity(0.4), radius: 4, y: 1)
                        .position(x: r.midX, y: r.midY)
                }
            }

            // ball trail
            ForEach(Array(game.trail.enumerated()), id: \.offset) { idx, p in
                let f = CGFloat(idx) / CGFloat(max(1, game.trail.count))
                Circle().fill(DioPal.text.opacity(Double(f) * 0.35))
                    .frame(width: game.ballR * 2 * f, height: game.ballR * 2 * f)
                    .position(p)
            }

            // ball
            Circle()
                .fill(RadialGradient(colors: [.white, Color(hex: 0xFFE3C2)], center: .init(x: 0.35, y: 0.3), startRadius: 0, endRadius: game.ballR))
                .frame(width: game.ballR * 2, height: game.ballR * 2)
                .shadow(color: .white.opacity(0.6), radius: 5)
                .position(game.ballPos)

            // paddle (glows on a hit)
            RoundedRectangle(cornerRadius: game.paddleH / 2, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0xFFB070), DioPal.accent], startPoint: .top, endPoint: .bottom))
                .frame(width: game.paddleW, height: game.paddleH)
                .overlay(RoundedRectangle(cornerRadius: game.paddleH / 2).strokeBorder(.white.opacity(0.4 + game.paddleGlow * 0.5), lineWidth: 1))
                .shadow(color: DioPal.accent.opacity(0.5 + game.paddleGlow * 0.5), radius: 8 + CGFloat(game.paddleGlow) * 8)
                .position(x: game.paddleX, y: game.paddleY)

            // phase overlays — VISUAL ONLY; must not intercept the tap (that blocked "Tap to launch")
            phaseOverlay.allowsHitTesting(false)
        }
        .frame(width: game.fieldW, height: game.fieldH)
        // STYLUS / FINGER control — drag x slides the paddle; a near-stationary press launches / restarts.
        // ONE gesture (no competing onTapGesture) so the tap reliably registers.
        .contentShape(Rectangle())
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { v in game.movePaddle(to: v.location.x) }
                .onEnded { v in
                    if abs(v.translation.width) < 8, abs(v.translation.height) < 8 { game.tapPlayField() }
                }
        )
    }

    @ViewBuilder private var phaseOverlay: some View {
        switch game.phase {
        case .ready:
            overlayCard {
                VStack(spacing: 7) {
                    TimelineView(.animation) { tl in
                        let t = tl.date.timeIntervalSinceReferenceDate
                        Image(systemName: "hand.tap.fill").font(.system(size: 24, weight: .bold))
                            .foregroundStyle(DioPal.violet).offset(y: CGFloat(sin(t * 2) * 3))
                    }
                    Text("Tap to launch").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("slide to move the paddle").font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                }
            }
        case .won:
            overlayCard {
                VStack(spacing: 7) {
                    Image(systemName: "trophy.fill").font(.system(size: 26, weight: .bold)).foregroundStyle(DioPal.accent)
                    Text("Cleared!").font(.system(size: 17, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("\(game.score) pts").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.mint)
                    playAgainPill
                }
            }
        case .lost:
            overlayCard {
                VStack(spacing: 7) {
                    Image(systemName: "xmark.octagon.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(Color(hex: 0xFF4D6D))
                    Text("Game over").font(.system(size: 17, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("\(game.score) pts").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                    playAgainPill
                }
            }
        case .playing:
            EmptyView()
        }
    }

    private var playAgainPill: some View {
        HStack(spacing: 6) {
            Image(systemName: "arrow.clockwise").font(.system(size: 11, weight: .bold))
            Text("Tap to play again").font(.system(size: 12, weight: .heavy, design: .rounded))
        }
        .foregroundStyle(.white).padding(.horizontal, 14).frame(height: 34)
        .background(Capsule().fill(LinearGradient(colors: [DioPal.violet, Color(hex: 0x6B43C2)], startPoint: .top, endPoint: .bottom)))
        .padding(.top, 2)
    }

    @ViewBuilder private func overlayCard(@ViewBuilder _ c: () -> some View) -> some View {
        c()
            .padding(.horizontal, 22).padding(.vertical, 16)
            .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.black.opacity(0.55))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
            .allowsHitTesting(false)   // taps fall through to the play field's tap-to-restart
    }
}
