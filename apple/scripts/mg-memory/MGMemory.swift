import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — MG_Memory ("Echo") harness (one self-contained SwiftUI module, @main) for the iOS Simulator.
// Mirrors App/MeetingCapture/DeskMiniGame_Memory.swift's look + layout so a mid-game frame can be
// screenshot WITHOUT touching the shared xcodeproj. Copies only the DioPal constants it needs and renders
// MG_Memory at ~260x300 inside a faux ephemeral window on a faux desk (proving "anchored, never modal").
// Loop: edit DeskMiniGame_Memory.swift + this mirror → ./scripts/mg-memory-shot.sh /tmp/x.png → Read it.

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

// ===== MIRROR OF DeskMiniGame_Memory.swift (with a harness-only mid-game seed) =====

struct MG_Memory: View {
    static let title = "Echo"
    static let icon = "circle.grid.2x2.fill"

    @StateObject private var game = EchoGame()
    @State private var best: Int = 4   // harness: a believable prior best

    var body: some View {
        GeometryReader { geo in
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                let s = game.shake
                let sx = s > 0 ? CGFloat(sin(t * 82)) * s : 0
                let sy = s > 0 ? CGFloat(cos(t * 71)) * s : 0
                content(in: geo.size, now: t)
                    .offset(x: sx, y: sy)
            }
        }
        .onAppear { game.bind(best: best) { newBest in best = newBest }; game.seedMidGame() }
        .onDisappear { game.stop() }
    }

    @ViewBuilder
    private func content(in size: CGSize, now t: TimeInterval) -> some View {
        let board = boardSize(in: size)
        VStack(spacing: 14) {
            statusRow
            EchoBoard(game: game, side: board, now: t)
                .frame(width: board, height: board)
            sequencePips
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .overlay { phaseOverlay(in: size).allowsHitTesting(false) }
    }

    private func boardSize(in size: CGSize) -> CGFloat {
        let avail = min(size.width - 32, size.height - 110)
        return max(120, avail)
    }

    private var statusRow: some View {
        HStack(spacing: 9) {
            Image(systemName: MG_Memory.icon).font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.violet)
            Text(MG_Memory.title).font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            Spacer(minLength: 0)
            HStack(spacing: 8) {
                badgeChip(icon: "waveform.path", value: "\(game.round)", tint: DioPal.accent)
                badgeChip(icon: "crown.fill", value: "\(max(best, game.round))", tint: Color(hex: 0xFFC857))
            }
        }
    }

    private func badgeChip(icon: String, value: String, tint: Color) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.system(size: 9, weight: .black))
            Text(value).font(.system(size: 12, weight: .heavy, design: .rounded).monospacedDigit())
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 9).frame(height: 24)
        .background(Capsule().fill(tint.opacity(0.14)).overlay(Capsule().strokeBorder(tint.opacity(0.3), lineWidth: 1)))
    }

    private var sequencePips: some View {
        HStack(spacing: 6) {
            ForEach(0..<max(1, game.sequence.count), id: \.self) { i in
                let done = i < game.inputCount
                let isLit = game.phase == .showing && game.flashIndex == i
                Circle()
                    .fill(done ? DioPal.mint : (isLit ? DioPal.text : DioPal.muted.opacity(0.35)))
                    .frame(width: isLit ? 9 : 7, height: isLit ? 9 : 7)
                    .shadow(color: (done ? DioPal.mint : .clear).opacity(0.6), radius: 4)
                    .animation(.spring(response: 0.25, dampingFraction: 0.6), value: done)
            }
        }
        .frame(height: 14)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: game.sequence.count)
    }

    @ViewBuilder
    private func phaseOverlay(in size: CGSize) -> some View {
        switch game.phase {
        case .ready:
            overlayCard {
                VStack(spacing: 8) {
                    TimelineView(.animation) { tl in
                        let t = tl.date.timeIntervalSinceReferenceDate
                        Image(systemName: "eye.fill").font(.system(size: 26, weight: .bold))
                            .foregroundStyle(DioPal.violet).scaleEffect(1 + CGFloat(sin(t * 2.4) * 0.08))
                    }
                    Text("Watch & repeat").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("tap any pad to start").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                }
            }
        case .lost:
            overlayCard {
                VStack(spacing: 7) {
                    Image(systemName: "xmark.octagon.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(Color(hex: 0xFF4D6D))
                    Text(game.round > best ? "New best!" : "Broke the chain")
                        .font(.system(size: 17, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("reached round \(game.round)")
                        .font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(game.round > best ? DioPal.mint : DioPal.muted)
                    playAgainPill
                }
            }
        default:
            EmptyView()
        }
    }

    private var playAgainPill: some View {
        HStack(spacing: 6) {
            Image(systemName: "arrow.clockwise").font(.system(size: 11, weight: .bold))
            Text("Tap to try again").font(.system(size: 12, weight: .heavy, design: .rounded))
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
    }
}

struct EchoBoard: View {
    @ObservedObject var game: EchoGame
    let side: CGFloat
    let now: TimeInterval

    var body: some View {
        let gap: CGFloat = 12
        let pad = (side - gap) / 2
        VStack(spacing: gap) {
            HStack(spacing: gap) { padView(0, pad); padView(1, pad) }
            HStack(spacing: gap) { padView(2, pad); padView(3, pad) }
        }
        .frame(width: side, height: side)
        .scaleEffect(1 + CGFloat(game.victoryPulse) * 0.05)
        .animation(.spring(response: 0.4, dampingFraction: 0.5), value: game.victoryPulse)
    }

    private func padView(_ i: Int, _ s: CGFloat) -> some View {
        let lit = game.litPad == i
        let tint = EchoGame.tints[i]
        let pressed = game.pressedPad == i
        return ZStack {
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(LinearGradient(colors: [tint.opacity(lit ? 1 : 0.42), tint.opacity(lit ? 0.7 : 0.18)],
                                     startPoint: .topLeading, endPoint: .bottomTrailing))
                .overlay(
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .strokeBorder(.white.opacity(lit ? 0.8 : 0.18), lineWidth: lit ? 2 : 1)
                )
                .overlay(alignment: .top) {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(LinearGradient(colors: [.white.opacity(lit ? 0.4 : 0.14), .clear], startPoint: .top, endPoint: .bottom))
                        .frame(height: s * 0.42).padding(8)
                }
                .shadow(color: tint.opacity(lit ? 0.85 : 0.25), radius: lit ? 22 : 8, y: 3)

            Circle()
                .fill(RadialGradient(colors: [.white.opacity(lit ? 0.9 : 0), tint.opacity(lit ? 0.5 : 0), .clear],
                                     center: .center, startRadius: 1, endRadius: s * 0.5))
                .frame(width: s * 0.9, height: s * 0.9)
                .opacity(lit ? 1 : 0)

            if let r = game.ripple, r.pad == i {
                let p = min(1, max(0, (now - r.start) / 0.45))
                Circle()
                    .strokeBorder(tint.opacity(0.7 * (1 - p)), lineWidth: 3)
                    .frame(width: s * 0.3 + s * CGFloat(p) * 0.9, height: s * 0.3 + s * CGFloat(p) * 0.9)
            }
        }
        .frame(width: s, height: s)
        .scaleEffect(lit ? 1.06 : (pressed ? 0.94 : 1))
        .animation(.spring(response: 0.18, dampingFraction: 0.55), value: lit)
        .animation(.spring(response: 0.18, dampingFraction: 0.55), value: pressed)
        .contentShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .onTapGesture { game.tap(pad: i) }
    }
}

enum EchoPhase { case ready, showing, awaiting, lost }
struct EchoRipple { let pad: Int; let start: TimeInterval }

final class EchoGame: ObservableObject {
    static let tints: [Color] = [DioPal.accent, DioPal.cobalt, DioPal.violet, DioPal.mint]

    @Published private(set) var sequence: [Int] = []
    @Published private(set) var inputCount = 0
    @Published private(set) var round = 0
    @Published private(set) var phase: EchoPhase = .ready
    @Published private(set) var litPad: Int? = nil
    @Published private(set) var flashIndex = -1
    @Published private(set) var pressedPad: Int? = nil
    @Published private(set) var ripple: EchoRipple? = nil
    @Published private(set) var shake: CGFloat = 0
    @Published private(set) var victoryPulse: Double = 0

    private var best = 0
    private var onNewBest: ((Int) -> Void)?
    private var ticker: Timer?
    private var queue: [(at: TimeInterval, action: () -> Void)] = []

    func bind(best: Int, onNewBest: @escaping (Int) -> Void) { self.best = best; self.onNewBest = onNewBest }

    func begin() {
        ticker?.invalidate()
        let t = Timer(timeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in self?.tick() }
        RunLoop.main.add(t, forMode: .common)
        ticker = t
    }
    func stop() { ticker?.invalidate(); ticker = nil }
    deinit { ticker?.invalidate() }

    private func tick() {
        let now = CACurrentMediaTime()
        if shake > 0 { shake = max(0, shake - 0.5) }
        if victoryPulse > 0 { victoryPulse = max(0, victoryPulse - 0.04) }
        while let first = queue.first, now >= first.at { queue.removeFirst(); first.action() }
    }
    private func schedule(_ delay: TimeInterval, _ action: @escaping () -> Void) {
        queue.append((at: CACurrentMediaTime() + delay, action: action))
    }

    // HARNESS ONLY: hold a believable, looping mid-game frame — round 6, two pads already echoed,
    // the third pad lit by a player tap (a fresh ripple), the chain in progress. Loops so the screenshot
    // never lands on a blank gap; the ripple replays on a gentle cadence.
    func seedMidGame() {
        begin()
        sequence = [0, 3, 1, 2, 0, 3]   // 6-long chain
        round = 6
        inputCount = 2                  // echoed the first two correctly
        phase = .awaiting
        loopShowcase()
    }
    private func loopShowcase() {
        // hold pad 1 (the 3rd step, the correct next) LIT for the hero frame, re-arming a fresh ripple
        // every ~0.55s so there is always an expanding ring in the shot. Stays lit (no rest gap).
        litPad = 1
        ripple = EchoRipple(pad: 1, start: CACurrentMediaTime())
        schedule(0.55) { [weak self] in self?.loopShowcase() }
    }

    private func nextRound() {
        sequence.append(Int.random(in: 0..<4)); round = sequence.count; inputCount = 0; playSequence()
    }
    private func playSequence() {
        phase = .showing; litPad = nil; flashIndex = -1; queue.removeAll()
        let lit = max(0.32, 0.5 - Double(sequence.count) * 0.012)
        let gap = max(0.14, 0.24 - Double(sequence.count) * 0.006)
        var cursor: TimeInterval = 0.45
        for (idx, pad) in sequence.enumerated() {
            schedule(cursor) { [weak self] in self?.litPad = pad; self?.flashIndex = idx; self?.haptic(.light) }
            cursor += lit
            schedule(cursor) { [weak self] in self?.litPad = nil }
            cursor += gap
        }
        schedule(cursor) { [weak self] in self?.phase = .awaiting; self?.flashIndex = -1 }
    }

    func tap(pad: Int) {
        switch phase {
        case .ready, .lost: start()
        case .awaiting: register(pad)
        case .showing: break
        }
    }
    private func start() {
        sequence.removeAll(); round = 0; inputCount = 0; victoryPulse = 0; shake = 0; phase = .ready
        schedule(0.2) { [weak self] in self?.nextRound() }
    }
    private func register(_ pad: Int) {
        pressedPad = pad; ripple = EchoRipple(pad: pad, start: CACurrentMediaTime()); litPad = pad
        schedule(0.16) { [weak self] in self?.pressedPad = nil; self?.litPad = nil }
        if pad == sequence[inputCount] {
            inputCount += 1; haptic(.light)
            if inputCount == sequence.count {
                victoryPulse = 1; haptic(.medium)
                if sequence.count > best { best = sequence.count; onNewBest?(best) }
                schedule(0.6) { [weak self] in self?.nextRound() }
            }
        } else {
            phase = .lost; shake = 12; haptic(.heavy)
            if round > best { best = round; onNewBest?(best) }
        }
    }
    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// ===== the harness scene: a faux ephemeral window (~260x300) on a faux desk =====

struct DeskBackdrop: View {
    var body: some View {
        ZStack {
            LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .top, endPoint: .bottom).ignoresSafeArea()
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 12) {
                    ForEach(["Standup", "Kickoff", "Docs KB"], id: \.self) { name in
                        VStack(spacing: 6) {
                            RoundedRectangle(cornerRadius: 10).fill(DioPal.accent.opacity(0.2))
                                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(DioPal.accent.opacity(0.4), lineWidth: 1)).frame(width: 70, height: 48)
                            Text(name).font(.system(size: 9, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        }
                    }
                }
                Spacer()
            }
            .padding(40).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }
}

// the ephemeral window the LAUNCHER supplies (frosted pane + close). We screenshot MG_Memory INSIDE it.
struct FauxWindow: View {
    private let winW: CGFloat = 260, winH: CGFloat = 300
    var body: some View {
        VStack(spacing: 0) {
            // a slim launcher-style header (NOT part of MG_Memory — proving the contract: launcher draws chrome)
            HStack {
                Spacer()
                Image(systemName: "xmark").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.text.opacity(0.85))
                    .frame(width: 26, height: 26).background(Circle().fill(.white.opacity(0.08)))
            }
            .padding(.horizontal, 10).padding(.top, 8)
            MG_Memory()
        }
        .frame(width: winW, height: winH)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(DioPal.violet.opacity(0.05)))
                .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                .shadow(color: .black.opacity(0.28), radius: 12, y: 6)
        )
    }
}

struct MGRoot: View {
    var body: some View {
        GeometryReader { geo in
            ZStack {
                DeskBackdrop()
                FauxWindow().position(x: geo.size.width / 2, y: geo.size.height * 0.46)
            }
        }
    }
}

@main
struct MGApp: App {
    var body: some Scene { WindowGroup { MGRoot().preferredColorScheme(.dark) } }
}
