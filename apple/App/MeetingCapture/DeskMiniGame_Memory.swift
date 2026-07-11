import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — DESK MINI-GAME: ECHO. A tiny Simon-style memory game you summon onto the desk during a boring
// meeting while everything else keeps running. Watch a growing sequence of glowing gem-pads light up, then
// tap it back in order. Get it right and the chain grows by one; get it wrong and you start over. Built to
// the DeskOS Component Pattern canon (docs/internal/DESKOS_COMPONENT_PATTERN.md) — the nine laws and the
// ambient-recorder shape. This file renders ONLY the game content and FILLS the frame the launcher gives it
// (the launcher supplies the ephemeral floating window + close button; we draw NO window chrome here).
//
// Nine-law honesty (this is a self-contained ephemeral game; some laws ADAPT — "reconcile, don't drift"):
//   • Law 1/2/3 (anchored, radiates, quiet at rest): the launcher anchors us; INSIDE the frame the board
//     radiates from its center and everything breathes. There is no rest-state token here because the
//     launcher owns rest/summon — our job is the active body only.
//   • Law 4 (intent before action): there is no fork — one game, one tap to begin. Skipped honestly.
//   • Law 5 (act in place): the whole game IS in place; one tap per pad, no detour, no config.
//   • Law 6 (harvest): a game has no routable artifact. We keep the spirit by persisting your BEST round
//     (@AppStorage "hs.mg.memory.best") and crowning a new best in-place. Adapted honestly.
//   • Law 7 (compose, don't reinvent): reuses the desk's DioPal palette and the ephemeral frosted look;
//     declares no new global mechanism.
//   • Law 8 (one badge of truth): a game has no egress; the one quiet badge is a playful ROUND / BEST chip
//     instead of a local/cloud egress chip. Adapted honestly per the canon.
//   • Law 9 (gated, never autonomous): nothing acts on the world; every effectful thing is a tap.
//   • The trap (one coordinate space + the loop): the sequence "playback" runs on a Timer started in
//     .onAppear and invalidated in .onDisappear — NEVER mutating @Published inside `body`. The win/lose
//     overlay .allowsHitTesting(false); there is ONE gesture path (tap a pad).
//   • Felt in motion (#11): pads bloom on flash, ripple on tap, the board does a victory pulse on a cleared
//     round, and a red screen-shake punishes a miss.

// MARK: - The public surface (the launcher integration contract)

public struct MG_Memory: View {
    public static let title = "Echo"
    public static let icon = "circle.grid.2x2.fill"

    @StateObject private var game = EchoGame()
    @AppStorage("hs.mg.memory.best") private var best: Int = 0

    public init() {}

    public var body: some View {
        GeometryReader { geo in
            // the victory/shake juice is rendered from the timeline; the LOGIC runs on game's own Timer.
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                let s = game.shake
                let sx = s > 0 ? CGFloat(sin(t * 82)) * s : 0
                let sy = s > 0 ? CGFloat(cos(t * 71)) * s : 0
                content(in: geo.size, now: t)
                    .offset(x: sx, y: sy)
            }
        }
        .onAppear { game.bind(best: best) { newBest in best = newBest }; game.begin() }
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

    // a square board that fits the frame minus the status row + pips
    private func boardSize(in size: CGSize) -> CGFloat {
        let avail = min(size.width - 32, size.height - 110)
        return max(120, avail)
    }

    // MARK: status row — the title + the playful ROUND / BEST badge (Law 8 ADAPTED)
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

    // MARK: sequence pips — a row of dots showing how long the chain is + how far you've echoed it
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

    // MARK: phase overlays (ready / lost / new-best). Visual only — taps fall through to the board.
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
                    Text(game.round > best ? "New best!" : "Sequence ended")
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

// MARK: - The board (the four gem-pads)

private struct EchoBoard: View {
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
        // the whole board breathes faintly + does a victory pulse when a round clears
        .scaleEffect(1 + CGFloat(game.victoryPulse) * 0.05)
        .animation(.spring(response: 0.4, dampingFraction: 0.5), value: game.victoryPulse)
    }

    private func padView(_ i: Int, _ s: CGFloat) -> some View {
        let lit = game.litPad == i
        let tint = EchoGame.tints[i]
        let pressed = game.pressedPad == i
        return ZStack {
            // base gem
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(LinearGradient(colors: [tint.opacity(lit ? 1 : 0.42), tint.opacity(lit ? 0.7 : 0.18)],
                                     startPoint: .topLeading, endPoint: .bottomTrailing))
                .overlay(
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .strokeBorder(.white.opacity(lit ? 0.8 : 0.18), lineWidth: lit ? 2 : 1)
                )
                // a glossy top highlight (premium gem feel)
                .overlay(alignment: .top) {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(LinearGradient(colors: [.white.opacity(lit ? 0.4 : 0.14), .clear], startPoint: .top, endPoint: .bottom))
                        .frame(height: s * 0.42).padding(8)
                }
                .shadow(color: tint.opacity(lit ? 0.85 : 0.25), radius: lit ? 22 : 8, y: 3)

            // the lit core glow
            Circle()
                .fill(RadialGradient(colors: [.white.opacity(lit ? 0.9 : 0), tint.opacity(lit ? 0.5 : 0), .clear],
                                     center: .center, startRadius: 1, endRadius: s * 0.5))
                .frame(width: s * 0.9, height: s * 0.9)
                .opacity(lit ? 1 : 0)

            // a one-shot ripple on a player tap
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
        .onTapGesture { game.tap(pad: i) }   // ONE gesture per pad; the only effectful path
    }
}

// MARK: - The game state + the playback loop (lives off the view body, on a Timer)

private enum EchoPhase { case ready, showing, awaiting, lost }

private struct EchoRipple { let pad: Int; let start: TimeInterval }

private final class EchoGame: ObservableObject {
    static let tints: [Color] = [DioPal.accent, DioPal.cobalt, DioPal.violet, DioPal.mint]

    @Published private(set) var sequence: [Int] = []
    @Published private(set) var inputCount = 0
    @Published private(set) var round = 0
    @Published private(set) var phase: EchoPhase = .ready
    @Published private(set) var litPad: Int? = nil      // which pad is currently glowing
    @Published private(set) var flashIndex = -1         // which step of the sequence is showing (for pips)
    @Published private(set) var pressedPad: Int? = nil  // brief press feedback
    @Published private(set) var ripple: EchoRipple? = nil
    @Published private(set) var shake: CGFloat = 0
    @Published private(set) var victoryPulse: Double = 0

    private var best = 0
    private var onNewBest: ((Int) -> Void)?

    // playback driver
    private var ticker: Timer?
    private var queue: [(at: TimeInterval, action: () -> Void)] = []   // scheduled playback events
    private var clockStart: TimeInterval = 0

    func bind(best: Int, onNewBest: @escaping (Int) -> Void) {
        self.best = best
        self.onNewBest = onNewBest
    }

    // Run a single timer in .common mode. It (a) decays the juice, (b) fires scheduled playback events.
    // We NEVER mutate @Published inside SwiftUI's body — all mutation happens here on the RunLoop.
    func begin() {
        ticker?.invalidate()
        clockStart = CACurrentMediaTime()
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
        // fire any due playback events
        while let first = queue.first, now >= first.at {
            queue.removeFirst()
            first.action()
        }
    }

    private func schedule(_ delay: TimeInterval, _ action: @escaping () -> Void) {
        queue.append((at: CACurrentMediaTime() + delay, action: action))
    }

    // MARK: rounds

    private func nextRound() {
        sequence.append(Int.random(in: 0..<4))
        round = sequence.count
        inputCount = 0
        playSequence()
    }

    private func playSequence() {
        phase = .showing
        litPad = nil
        flashIndex = -1
        queue.removeAll()
        // each step: a beat of "lit" then a gap. Tempo eases slightly faster as the chain grows.
        let lit = max(0.32, 0.5 - Double(sequence.count) * 0.012)
        let gap = max(0.14, 0.24 - Double(sequence.count) * 0.006)
        var cursor: TimeInterval = 0.45   // a breath before it starts
        for (idx, pad) in sequence.enumerated() {
            schedule(cursor) { [weak self] in self?.litPad = pad; self?.flashIndex = idx; self?.haptic(.light) }
            cursor += lit
            schedule(cursor) { [weak self] in self?.litPad = nil }
            cursor += gap
        }
        schedule(cursor) { [weak self] in
            self?.phase = .awaiting
            self?.flashIndex = -1
        }
    }

    // MARK: input

    func tap(pad: Int) {
        switch phase {
        case .ready:
            // first tap begins the game
            start()
        case .lost:
            start()
        case .awaiting:
            register(pad)
        case .showing:
            break   // ignore taps while the sequence is playing back
        }
    }

    private func start() {
        sequence.removeAll()
        round = 0
        inputCount = 0
        victoryPulse = 0
        shake = 0
        phase = .ready
        // brief beat, then the first round
        schedule(0.2) { [weak self] in self?.nextRound() }
    }

    private func register(_ pad: Int) {
        // press + ripple feedback
        pressedPad = pad
        ripple = EchoRipple(pad: pad, start: CACurrentMediaTime())
        litPad = pad
        schedule(0.16) { [weak self] in self?.pressedPad = nil; self?.litPad = nil }

        if pad == sequence[inputCount] {
            inputCount += 1
            haptic(.light)
            if inputCount == sequence.count {
                // round cleared
                victoryPulse = 1
                haptic(.medium)
                if sequence.count > best {
                    best = sequence.count
                    onNewBest?(best)
                }
                schedule(0.6) { [weak self] in self?.nextRound() }
            }
        } else {
            // wrong — break the chain
            phase = .lost
            shake = 12
            haptic(.heavy)
            if round > best {
                best = round
                onNewBest?(best)
            }
        }
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}
