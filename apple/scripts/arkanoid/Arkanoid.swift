import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — DESK ARKANOID harness (one self-contained SwiftUI module, @main) for the iOS Simulator.
// Mirrors App/MeetingCapture/DeskArkanoid.swift's look + layout so the pinnable window + mid-game frame
// can be screenshot WITHOUT touching the shared xcodeproj. Copies only the DioPal constants it needs.
// Loop: edit DeskArkanoid.swift + this mirror → ./scripts/arkanoid-shot.sh /tmp/x.png → Read it → iterate.

extension Color {
    init(hex: UInt, a: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255, opacity: a)
    }
}

enum DioPal {   // copied from DeskDioramaStage.swift
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let trayTop = Color(hex: 0x1B1626), trayBot = Color(hex: 0x0C0A12)
    static let accent = Color(hex: 0xFF6B35), cobalt = Color(hex: 0x5B8DEF), violet = Color(hex: 0x9B6BFF)
    static let mint = Color(hex: 0x3ECF8E), text = Color(hex: 0xF4ECE0), muted = Color(hex: 0x9C93A8)
}

// ---- the game model (mirror of DeskArkanoid.swift's ArkGame) ----

struct ArkBrick: Identifiable {
    let id: Int; let col: Int, row: Int
    var alive = true; var hits: Int; let tint: Color; var popT: Double = 0
}
enum ArkPhase { case ready, playing, lost, won }

final class ArkGame: ObservableObject {
    let fieldW: CGFloat, fieldH: CGFloat
    let cols = 7, rows = 4
    let brickH: CGFloat = 18, brickGap: CGFloat = 5, topInset: CGFloat = 10
    @Published var bricks: [ArkBrick] = []
    @Published var paddleX: CGFloat
    @Published var ballPos: CGPoint
    @Published var ballVel = CGVector.zero
    @Published var trail: [CGPoint] = []
    @Published var score = 0
    @Published var lives = 3
    @Published var phase: ArkPhase = .ready
    @Published var shake: CGFloat = 0
    @Published var paddleGlow: Double = 0
    let paddleW: CGFloat = 64, paddleH: CGFloat = 12, ballR: CGFloat = 6
    var paddleY: CGFloat { fieldH - 26 }
    private let tints: [Color] = [DioPal.accent, DioPal.cobalt, DioPal.violet, DioPal.mint]
    private var lastStep: TimeInterval = 0
    private let speed: CGFloat = 250
    var frozen = false   // harness-only: hold a stable mid-flight frame for the screenshot

    init(fieldW: CGFloat, fieldH: CGFloat) {
        self.fieldW = fieldW; self.fieldH = fieldH
        self.paddleX = fieldW / 2
        self.ballPos = CGPoint(x: fieldW / 2, y: fieldH - 44)
        layoutBricks()
    }
    func layoutBricks() {
        var out: [ArkBrick] = []; var id = 0
        for r in 0..<rows { for c in 0..<cols {
            out.append(ArkBrick(id: id, col: c, row: r, hits: r == 0 ? 2 : 1, tint: tints[r % tints.count])); id += 1
        } }
        bricks = out
    }
    func brickRect(_ b: ArkBrick) -> CGRect {
        let usableW = fieldW - brickGap * CGFloat(cols + 1)
        let bw = usableW / CGFloat(cols)
        return CGRect(x: brickGap + CGFloat(b.col) * (bw + brickGap),
                      y: topInset + CGFloat(b.row) * (brickH + brickGap), width: bw, height: brickH)
    }
    func tick(_ now: TimeInterval) {
        if lastStep == 0 { lastStep = now }
        var dt = now - lastStep; lastStep = now
        if shake > 0 { shake = max(0, shake - CGFloat(dt) * 60) }
        if paddleGlow > 0 { paddleGlow = max(0, paddleGlow - dt * 3) }
        for i in bricks.indices where bricks[i].popT > 0 { bricks[i].popT = max(0, bricks[i].popT - dt * 4) }
        guard phase == .playing, !frozen else { return }
        if dt > 0.05 { dt = 0.05 }
        let steps = 3; let sdt = CGFloat(dt) / CGFloat(steps)
        for _ in 0..<steps { step(sdt) }
        trail.append(ballPos); if trail.count > 12 { trail.removeFirst(trail.count - 12) }
    }
    private func norm() { let m = sqrt(ballVel.dx*ballVel.dx + ballVel.dy*ballVel.dy); if m > 0 { ballVel.dx /= m; ballVel.dy /= m } }
    private func step(_ dt: CGFloat) {
        ballPos.x += ballVel.dx * speed * dt; ballPos.y += ballVel.dy * speed * dt
        if ballPos.x - ballR < 0 { ballPos.x = ballR; ballVel.dx = abs(ballVel.dx) }
        if ballPos.x + ballR > fieldW { ballPos.x = fieldW - ballR; ballVel.dx = -abs(ballVel.dx) }
        if ballPos.y - ballR < 0 { ballPos.y = ballR; ballVel.dy = abs(ballVel.dy) }
        if ballPos.y - ballR > fieldH { lives -= 1; shake = 14; trail.removeAll(); phase = lives <= 0 ? .lost : .ready; return }
        let pTop = paddleY - paddleH/2
        if ballVel.dy > 0, ballPos.y + ballR >= pTop, ballPos.y - ballR <= paddleY + paddleH/2,
           ballPos.x >= paddleX - paddleW/2 - ballR, ballPos.x <= paddleX + paddleW/2 + ballR {
            ballPos.y = pTop - ballR
            let rel = min(max((ballPos.x - paddleX)/(paddleW/2), -0.92), 0.92)
            ballVel = CGVector(dx: rel, dy: -(1 - abs(rel)*0.5)); norm(); paddleGlow = 1
        }
        for i in bricks.indices where bricks[i].alive {
            if brickRect(bricks[i]).insetBy(dx: -ballR, dy: -ballR).contains(ballPos) {
                let br = brickRect(bricks[i])
                let minX = min(abs(ballPos.x - br.minX), abs(ballPos.x - br.maxX))
                let minY = min(abs(ballPos.y - br.minY), abs(ballPos.y - br.maxY))
                if minX < minY { ballVel.dx = -ballVel.dx } else { ballVel.dy = -ballVel.dy }
                bricks[i].hits -= 1; bricks[i].popT = 1
                if bricks[i].hits <= 0 { bricks[i].alive = false; score += 100 } else { score += 25 }
                if !bricks.contains(where: { $0.alive }) { phase = .won }
                break
            }
        }
    }
    func movePaddle(to x: CGFloat) { paddleX = min(max(x, paddleW/2), fieldW - paddleW/2); if phase == .ready { ballPos.x = paddleX } }
    func tapField() { switch phase { case .ready: phase = .playing; ballVel = CGVector(dx: 0.45, dy: -0.9); norm(); case .lost, .won: score = 0; lives = 3; phase = .ready; layoutBricks(); ballPos = CGPoint(x: paddleX, y: paddleY - ballR - 2); ballVel = .zero; case .playing: break } }
}

// ---- the window (mirror of DeskArkanoidWindow) ----

struct ArkWindow: View {
    let screen: CGSize
    @State private var pinNX: Double
    @State private var pinNY: Double
    private let winW: CGFloat = 340, headerH: CGFloat = 44, pad: CGFloat = 14
    private var winH: CGFloat { 300 }
    @StateObject private var game: ArkGame

    init(screen: CGSize, pinNX: Double, pinNY: Double) {
        self.screen = screen; _pinNX = State(initialValue: pinNX); _pinNY = State(initialValue: pinNY)
        let g = ArkGame(fieldW: 340 - 28, fieldH: 300 - 44 - 14)
        // mid-game seed — frozen so the screenshot holds a stable in-flight frame (simctl can't tap/drag)
        g.frozen = true
        g.phase = .playing; g.score = 1450; g.lives = 2
        for i in g.bricks.indices { let b = g.bricks[i]
            if (b.row >= 2 && b.col <= 3) || (b.row == 1 && b.col <= 1) { g.bricks[i].alive = false }
            if b.row == 0 && b.col == 5 { g.bricks[i].popT = 0.8 } }
        g.paddleX = g.fieldW * 0.42
        g.ballPos = CGPoint(x: g.fieldW * 0.5, y: g.fieldH * 0.56)
        g.ballVel = CGVector(dx: 0.6, dy: -0.8)
        g.trail = (0..<10).map { k in let f = CGFloat(k)/10; return CGPoint(x: g.fieldW*0.5 - 0.6*90*(1-f), y: g.fieldH*0.56 + 0.8*90*(1-f)) }
        _game = StateObject(wrappedValue: g)
    }
    private var pin: CGPoint { CGPoint(x: CGFloat(pinNX) * screen.width, y: CGFloat(pinNY) * screen.height) }

    var body: some View {
        TimelineView(.animation) { tl in
            let _ = game.tick(tl.date.timeIntervalSinceReferenceDate)
            VStack(spacing: 0) { header; field }
                .frame(width: winW, height: winH)
                .background(RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0B0A11)], startPoint: .top, endPoint: .bottom))
                    .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(DioPal.violet.opacity(0.35), lineWidth: 1.2))
                    .shadow(color: .black.opacity(0.6), radius: 26, y: 14))
                .position(pin)
        }
    }
    private var header: some View {
        HStack(spacing: 9) {
            Image(systemName: "gamecontroller.fill").font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.violet)
            Text("Arkanoid").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            HStack(spacing: 8) {
                HStack(spacing: 3) { Image(systemName: "star.fill").font(.system(size: 8, weight: .black)); Text("\(game.score)").font(.system(size: 11, weight: .heavy, design: .rounded).monospacedDigit()).fixedSize() }.foregroundStyle(DioPal.accent)
                HStack(spacing: 2) { ForEach(0..<3, id: \.self) { i in Image(systemName: i < game.lives ? "heart.fill" : "heart").font(.system(size: 8, weight: .black)).foregroundStyle(i < game.lives ? Color(hex: 0xFF4D6D) : DioPal.muted.opacity(0.5)) } }
            }.padding(.horizontal, 9).frame(height: 24).background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(0.08), lineWidth: 1)))
            Spacer(minLength: 0)
            Image(systemName: "minus").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9)).frame(width: 28, height: 28).background(Circle().fill(.white.opacity(0.08)))
            Image(systemName: "xmark").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9)).frame(width: 28, height: 28).background(Circle().fill(.white.opacity(0.08)))
        }
        .padding(.horizontal, 14).frame(height: headerH)
    }
    private var field: some View {
        ZStack {
            LinearGradient(colors: [Color(hex: 0x0E0C16), Color(hex: 0x080710)], startPoint: .top, endPoint: .bottom)
            ForEach(game.bricks) { b in if b.alive {
                let r = game.brickRect(b)
                RoundedRectangle(cornerRadius: 4, style: .continuous)
                    .fill(LinearGradient(colors: [b.tint.opacity(b.hits > 1 ? 1 : 0.92), b.tint.opacity(0.62)], startPoint: .top, endPoint: .bottom))
                    .overlay(RoundedRectangle(cornerRadius: 4, style: .continuous).strokeBorder(.white.opacity(b.hits > 1 ? 0.5 : 0.22), lineWidth: b.hits > 1 ? 1.2 : 0.8))
                    .overlay(RoundedRectangle(cornerRadius: 4, style: .continuous).fill(.white.opacity(b.popT * 0.85)))
                    .frame(width: r.width, height: r.height).scaleEffect(1 + b.popT * 0.12)
                    .shadow(color: b.tint.opacity(0.4), radius: 4, y: 1).position(x: r.midX, y: r.midY)
            } }
            ForEach(Array(game.trail.enumerated()), id: \.offset) { idx, p in
                let f = CGFloat(idx)/CGFloat(max(1, game.trail.count))
                Circle().fill(DioPal.text.opacity(Double(f) * 0.35)).frame(width: game.ballR*2*f, height: game.ballR*2*f).position(p)
            }
            Circle().fill(RadialGradient(colors: [.white, Color(hex: 0xFFE3C2)], center: .init(x: 0.35, y: 0.3), startRadius: 0, endRadius: game.ballR))
                .frame(width: game.ballR*2, height: game.ballR*2).shadow(color: .white.opacity(0.6), radius: 5).position(game.ballPos)
            RoundedRectangle(cornerRadius: game.paddleH/2, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0xFFB070), DioPal.accent], startPoint: .top, endPoint: .bottom))
                .frame(width: game.paddleW, height: game.paddleH)
                .overlay(RoundedRectangle(cornerRadius: game.paddleH/2).strokeBorder(.white.opacity(0.4), lineWidth: 1))
                .shadow(color: DioPal.accent.opacity(0.6), radius: 9).position(x: game.paddleX, y: game.paddleY)
        }
        .frame(width: game.fieldW, height: game.fieldH)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .padding(.horizontal, pad).padding(.bottom, pad)
    }
}

// ---- the rest-state token (mirror of DeskArkanoidToken) ----

struct ArkToken: View {
    var body: some View {
        VStack(spacing: 4) {
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate; let bob = CGFloat(sin(t * 1.1) * 1.5)
                ZStack {
                    Circle().fill(RadialGradient(colors: [DioPal.violet.opacity(0.4), .clear], center: .center, startRadius: 2, endRadius: 34)).frame(width: 64, height: 64).opacity(0.5 + 0.4 * sin(t * 1.6))
                    VStack(spacing: 2) {
                        ForEach(0..<2, id: \.self) { r in HStack(spacing: 2) { ForEach(0..<3, id: \.self) { c in RoundedRectangle(cornerRadius: 2).fill([DioPal.accent, DioPal.cobalt, DioPal.violet][(r+c)%3]).frame(width: 9, height: 5) } } }
                        Circle().fill(.white).frame(width: 4, height: 4).padding(.top, 1)
                        RoundedRectangle(cornerRadius: 2).fill(DioPal.text.opacity(0.85)).frame(width: 18, height: 4)
                    }
                    .frame(width: 46, height: 46)
                    .background(RoundedRectangle(cornerRadius: 13, style: .continuous).fill(LinearGradient(colors: [Color(hex: 0x1B1626), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom)).overlay(RoundedRectangle(cornerRadius: 13, style: .continuous).strokeBorder(DioPal.violet.opacity(0.55), lineWidth: 1.3)))
                    .offset(y: -bob).shadow(color: .black.opacity(0.5), radius: 10, y: 6)
                }.frame(width: 64, height: 64)
            }
            Text("Play").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
        }
    }
}

// ---- the harness scene: a faux desk behind the window, proving "anchored, never modal" ----

struct DeskBackdrop: View {
    var body: some View {
        ZStack {
            LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .top, endPoint: .bottom).ignoresSafeArea()
            // a few faint desk objects so the screenshot shows the desk STAYS ALIVE behind the window
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 12) {
                    ForEach(["Standup", "Kickoff", "Docs KB"], id: \.self) { name in
                        VStack(spacing: 6) {
                            RoundedRectangle(cornerRadius: 10).fill(DioPal.accent.opacity(0.2)).overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(DioPal.accent.opacity(0.4), lineWidth: 1)).frame(width: 70, height: 48)
                            Text(name).font(.system(size: 9, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        }
                    }
                }
                Spacer()
            }
            .padding(40).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            // the rest-state token tucked in a corner (so the screenshot shows BOTH states)
            ArkToken().position(x: 56, y: 120)
        }
    }
}

struct ArkRoot: View {
    var body: some View {
        GeometryReader { geo in
            ZStack {
                DeskBackdrop()
                ArkWindow(screen: geo.size, pinNX: 0.5, pinNY: 0.46)
            }
        }
    }
}

@main
struct ArkApp: App {
    var body: some Scene { WindowGroup { ArkRoot().preferredColorScheme(.dark) } }
}
