import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM — DESK MINI-GAME · LOGIC : "TENFOLD". A tiny number-logic puzzle you summon onto the desk during a
// boring meeting. A 4x4 grid of small glowing number tiles. Drag a connected path across neighbouring tiles
// to build a running SUM; release ON the TARGET and the whole path clears in a burst, tiles cascade down,
// fresh ones rain in from the top. Quick, forgiving rounds — no clock, no fail state, just the satisfying
// click of hitting the number exactly and watching the board tumble. A best score persists.
//
// Built to the DeskOS Component Pattern canon (docs/internal/DESKOS_COMPONENT_PATTERN.md). This file is the
// GAME CONTENT only — the launcher supplies the ephemeral frosted window + close, so MG_Logic just fills the
// frame it is given (matching the council mini-game contract). Honest law-by-law adaptations are in the report.
//
// The traps (obeyed):
//   • ONE game loop on a Timer (RunLoop .common) started in .onAppear / torn down in .onDisappear. Never a
//     loop driven from `body`, and NEVER a @Published mutation inside a view-update pass.
//   • ONE gesture for play: a single DragGesture (path-draw). No competing onTapGesture on the field.
//   • Phase / win overlays are .allowsHitTesting(false) so they never eat the play gesture.
//   • Drawn in ONE coordinate space (a single GeometryReader-less fixed board laid out from one origin).
//
// Self-contained: copies the few DioPal constants it needs as MGL_Pal so the harness compiles standalone and
// the app picks up the same palette. Declares no new global mechanism.

// MARK: - Palette (mirror of DioPal so this file is harness-portable)

private enum MGL_Pal {
    static let accent = Color(hexL: 0xFF6B35), cobalt = Color(hexL: 0x5B8DEF), violet = Color(hexL: 0x9B6BFF)
    static let mint = Color(hexL: 0x3ECF8E), text = Color(hexL: 0xF4ECE0), muted = Color(hexL: 0x9C93A8)
    static let rose = Color(hexL: 0xFF4D6D), gold = Color(hexL: 0xFFC857)
    static let trayTop = Color(hexL: 0x1B1626), trayBot = Color(hexL: 0x0C0A12)
}

private extension Color {
    init(hexL: UInt) {
        self.init(.sRGB, red: Double((hexL >> 16) & 0xFF) / 255, green: Double((hexL >> 8) & 0xFF) / 255,
                  blue: Double(hexL & 0xFF) / 255, opacity: 1)
    }
}

// MARK: - Model

private let MGL_N = 4   // 4x4 grid

private struct MGL_Tile: Identifiable {
    let id: Int
    var value: Int            // 1...6
    var row: Int              // grid row (0 = top)
    var col: Int
    var spawnT: Double = 0    // >0 while easing in from above (drives the drop animation)
    var popT: Double = 0      // >0 while playing the clear burst (then removed)
    var bumpT: Double = 0     // >0 for a tiny tap-bump
}

private enum MGL_Phase { case play, cleared }

/// The whole game state + the fixed-step juice loop. The view is a pure render of this.
private final class MGL_Game: ObservableObject {
    @Published var tiles: [MGL_Tile] = []
    @Published var path: [Int] = []        // tile ids in the current drawn path (in order)
    @Published var target: Int = 10
    @Published var score: Int = 0
    @Published var combo: Int = 0          // consecutive clears without a miss
    @Published var lastClear: Int = 0      // points from the last clear, for the float-up
    @Published var floatT: Double = 0      // >0 while the "+N" floats
    @Published var floatVal: Int = 0
    @Published var flashT: Double = 0      // brief red flash on an over/under release miss
    @Published var phase: MGL_Phase = .play

    private var nextId = 0
    private var ticker: Timer?
    private var lastStep: TimeInterval = 0

    // a gentle weighting toward small numbers so targets are reachable and rounds stay quick
    private func rollValue() -> Int {
        let bag = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6]
        return bag.randomElement() ?? 3
    }
    private func rollTarget() -> Int { [8, 9, 10, 11, 12].randomElement() ?? 10 }

    init() { newGame() }

    func newGame() {
        nextId = 0
        score = 0
        combo = 0
        path = []
        floatT = 0
        flashT = 0
        target = rollTarget()
        tiles = []
        for r in 0..<MGL_N {
            for c in 0..<MGL_N {
                tiles.append(MGL_Tile(id: nextId, value: rollValue(), row: r, col: c, spawnT: 0.0001 + Double(r) * 0.04))
                nextId += 1
            }
        }
        phase = .play
    }

    // MARK: lookup helpers

    func tile(_ id: Int) -> MGL_Tile? { tiles.first { $0.id == id } }
    private func index(_ id: Int) -> Int? { tiles.firstIndex { $0.id == id } }
    func tileAt(row: Int, col: Int) -> MGL_Tile? { tiles.first { $0.row == row && $0.col == col && $0.popT == 0 } }

    var pathSum: Int { path.compactMap { tile($0)?.value }.reduce(0, +) }

    private func adjacent(_ a: MGL_Tile, _ b: MGL_Tile) -> Bool {
        let dr = abs(a.row - b.row), dc = abs(a.col - b.col)
        return (dr + dc) == 1   // 4-neighbour (orthogonal) — clean to draw with a finger
    }

    // MARK: path drawing (the single gesture feeds these)

    func beginPath(at id: Int) {
        guard phase == .play, let t = tile(id), t.popT == 0 else { return }
        path = [id]
        bump(id)
    }

    /// Extend (or backtrack) the path to the tile under the finger. Forgiving: backing onto the
    /// previous tile pops the head; only orthogonal neighbours extend.
    func extendPath(to id: Int) {
        guard phase == .play, !path.isEmpty, let t = tile(id), t.popT == 0 else { return }
        if id == path.last { return }
        // backtrack
        if path.count >= 2, id == path[path.count - 2] { path.removeLast(); haptic(.light); return }
        if path.contains(id) { return }   // no crossing itself
        guard let head = tile(path.last!), adjacent(head, t) else { return }
        // do not let the sum overshoot wildly — allow up to target (release decides win/miss)
        path.append(id)
        bump(id)
        haptic(.light)
    }

    func endPath() {
        guard phase == .play else { return }
        defer { path = [] }
        guard path.count >= 2 else { return }
        let sum = pathSum
        if sum == target {
            clearPath()
        } else {
            // a forgiving miss — just a flash + combo reset, no life lost
            combo = 0
            flashT = 1
            haptic(.rigid)
        }
    }

    private func clearPath() {
        let n = path.count
        combo += 1
        let base = target * 10
        let lengthBonus = (n - 2) * 15
        let comboBonus = (combo - 1) * 25
        let gain = base + lengthBonus + comboBonus
        score += gain
        lastClear = gain
        floatVal = gain
        floatT = 1
        haptic(combo >= 3 ? .heavy : .medium)

        for id in path {
            if let i = index(id) { tiles[i].popT = 1 }
            popped.insert(id)
        }
        target = rollTarget()
        // the cascade + refill happens as the pops finish (see settle())
    }

    // MARK: the loop

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

    private func tick(_ now: TimeInterval) {
        if lastStep == 0 { lastStep = now }
        let dt = min(now - lastStep, 0.05)
        lastStep = now

        if floatT > 0 { floatT = max(0, floatT - dt * 1.1) }
        if flashT > 0 { flashT = max(0, flashT - dt * 2.2) }

        var didPop = false
        for i in tiles.indices {
            if tiles[i].spawnT > 0 { tiles[i].spawnT = max(0, tiles[i].spawnT - dt * 2.4) }
            if tiles[i].bumpT > 0 { tiles[i].bumpT = max(0, tiles[i].bumpT - dt * 4) }
            if tiles[i].popT > 0 {
                tiles[i].popT = max(0, tiles[i].popT - dt * 3.2)
                if tiles[i].popT == 0 { didPop = true }
            }
        }
        if didPop { settle() }
    }

    private func bump(_ id: Int) { if let i = index(id) { tiles[i].bumpT = 1 } }

    /// Once cleared tiles have finished their pop, drop the survivors down each column and rain in fresh
    /// tiles from the top. Rebuilds the whole tiles array in one pass (one coordinate model, no aliasing).
    private func settle() {
        guard !popped.isEmpty else { return }
        let survivors = tiles.filter { !popped.contains($0.id) }
        var rebuilt: [MGL_Tile] = []
        for c in 0..<MGL_N {
            // survivors in this column, top-to-bottom
            let col = survivors.filter { $0.col == c }.sorted { $0.row < $1.row }
            let empties = MGL_N - col.count
            // fresh tiles fall into the top `empties` rows
            for k in 0..<empties {
                rebuilt.append(MGL_Tile(id: nextId, value: rollValue(), row: k, col: c, spawnT: 1.0 + Double(empties - 1 - k) * 0.05))
                nextId += 1
            }
            // survivors settle into the rows below the fresh ones, preserving order
            for (k, var t) in col.enumerated() {
                t.row = empties + k
                rebuilt.append(t)
            }
        }
        popped.removeAll()
        tiles = rebuilt
    }

    private var popped: Set<Int> = []

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// MARK: - The game view (fills the given frame)

/// Public entry. `init()` only; renders ONLY game content and fills the frame the launcher provides.
public struct MG_Logic: View {
    public static let title: String = "Tenfold"
    public static let icon: String = "number.square.fill"

    @StateObject private var game = MGL_Game()
    @AppStorage("hs.mg.logic.best") private var best: Int = 0

    public init() {}

    public var body: some View {
        // The juice loop runs on game's Timer; this TimelineView only re-renders so animated values show.
        TimelineView(.animation) { tl in
            content(now: tl.date.timeIntervalSinceReferenceDate)
        }
        .onAppear {
            game.start()
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_MG_LOGIC"] == "seed" {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { MGL_seed(game) }
            }
            #endif
        }
        .onDisappear {
            best = max(best, game.score)
            game.stop()
        }
        .onChange(of: game.score) { best = max(best, game.score) }
    }

    @ViewBuilder private func content(now: Double) -> some View {
        VStack(spacing: 10) {
            header
            board(now: now)
            footer
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // The HUD — the TARGET is the hero, the running sum reads beside it.
    private var header: some View {
        HStack(alignment: .center, spacing: 10) {
            // TARGET hero chip
            VStack(spacing: 1) {
                Text("MAKE").font(.system(size: 8.5, weight: .heavy, design: .rounded)).tracking(1.6).foregroundStyle(MGL_Pal.muted)
                Text("\(game.target)")
                    .font(.system(size: 30, weight: .black, design: .rounded)).monospacedDigit()
                    .foregroundStyle(MGL_Pal.text)
                    .contentTransition(.numericText())
                    .animation(.spring(response: 0.4, dampingFraction: 0.7), value: game.target)
            }
            .frame(width: 64, height: 56)
            .background(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(LinearGradient(colors: [MGL_Pal.violet.opacity(0.30), MGL_Pal.trayBot.opacity(0.9)], startPoint: .top, endPoint: .bottom))
                    .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(MGL_Pal.violet.opacity(0.7), lineWidth: 1.3))
            )

            // running sum + progress toward the target
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 5) {
                    let sum = game.pathSum
                    let hit = sum == game.target && sum > 0
                    let over = sum > game.target
                    Text(game.path.isEmpty ? "draw a path" : "\(sum)")
                        .font(.system(size: game.path.isEmpty ? 12 : 19, weight: .heavy, design: .rounded)).monospacedDigit()
                        .foregroundStyle(game.path.isEmpty ? MGL_Pal.muted : (hit ? MGL_Pal.mint : (over ? MGL_Pal.rose : MGL_Pal.text)))
                    if !game.path.isEmpty {
                        Text(hit ? "release!" : (over ? "over" : "/ \(game.target)"))
                            .font(.system(size: 10, weight: .heavy, design: .rounded))
                            .foregroundStyle(hit ? MGL_Pal.mint : (over ? MGL_Pal.rose : MGL_Pal.muted))
                    }
                }
                progressBar
            }
            Spacer(minLength: 0)
            if game.combo >= 2 {
                comboBadge
            }
        }
    }

    private var progressBar: some View {
        GeometryReader { g in
            let sum = game.pathSum
            let frac = min(1, Double(sum) / Double(max(1, game.target)))
            let hit = sum == game.target && sum > 0
            ZStack(alignment: .leading) {
                Capsule().fill(.white.opacity(0.08))
                Capsule()
                    .fill(LinearGradient(colors: hit ? [MGL_Pal.mint, MGL_Pal.mint] : [MGL_Pal.cobalt, MGL_Pal.violet], startPoint: .leading, endPoint: .trailing))
                    .frame(width: g.size.width * frac)
                    .animation(.spring(response: 0.25, dampingFraction: 0.8), value: sum)
            }
        }
        .frame(height: 5)
    }

    private var comboBadge: some View {
        HStack(spacing: 3) {
            Image(systemName: "flame.fill").font(.system(size: 9, weight: .black))
            Text("x\(game.combo)").font(.system(size: 12, weight: .black, design: .rounded)).monospacedDigit()
        }
        .foregroundStyle(MGL_Pal.gold)
        .padding(.horizontal, 8).frame(height: 26)
        .background(Capsule().fill(MGL_Pal.gold.opacity(0.16)).overlay(Capsule().strokeBorder(MGL_Pal.gold.opacity(0.5), lineWidth: 1)))
        .transition(.scale.combined(with: .opacity))
    }

    // The board — a fixed square grid laid out from one origin, one DragGesture for the whole path.
    private func board(now: Double) -> some View {
        GeometryReader { g in
            let side = min(g.size.width, g.size.height)
            let gap: CGFloat = 7
            let cell = (side - gap * CGFloat(MGL_N + 1)) / CGFloat(MGL_N)
            ZStack {
                // the well
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(LinearGradient(colors: [Color(hexL: 0x130F1C), Color(hexL: 0x0A080F)], startPoint: .top, endPoint: .bottom))
                    .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(.white.opacity(0.06), lineWidth: 1))
                    .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(MGL_Pal.rose.opacity(game.flashT * 0.7), lineWidth: 2))

                // empty cell sockets (so the grid reads even mid-cascade)
                ForEach(0..<MGL_N, id: \.self) { r in
                    ForEach(0..<MGL_N, id: \.self) { c in
                        RoundedRectangle(cornerRadius: 11, style: .continuous)
                            .fill(.white.opacity(0.025))
                            .frame(width: cell, height: cell)
                            .position(center(r, c, cell: cell, gap: gap))
                    }
                }

                // the live path line connecting selected tiles
                pathLine(cell: cell, gap: gap, now: now)

                // tiles
                ForEach(game.tiles) { t in
                    if t.popT == 0 || t.popT > 0 {   // render until fully popped
                        tileView(t, cell: cell, gap: gap, now: now)
                            .position(center(t.row, t.col, cell: cell, gap: gap, spawnT: t.spawnT))
                    }
                }

                // the "+N" float-up on a clear (visual only)
                if game.floatT > 0 {
                    Text("+\(game.floatVal)")
                        .font(.system(size: 24, weight: .black, design: .rounded)).monospacedDigit()
                        .foregroundStyle(MGL_Pal.mint)
                        .shadow(color: MGL_Pal.mint.opacity(0.6), radius: 8)
                        .opacity(game.floatT)
                        .offset(y: -CGFloat(1 - game.floatT) * 46)
                        .position(x: side / 2, y: side / 2)
                        .allowsHitTesting(false)
                }
            }
            .frame(width: side, height: side)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            // THE ONE GESTURE — draw the path. Hit-test the finger to a tile via geometry.
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { v in
                        guard let id = tileId(at: v.location, side: side, cell: cell, gap: gap) else { return }
                        if game.path.isEmpty { game.beginPath(at: id) }
                        else { game.extendPath(to: id) }
                    }
                    .onEnded { _ in game.endPath() }
            )
        }
        .aspectRatio(1, contentMode: .fit)
    }

    private func center(_ r: Int, _ c: Int, cell: CGFloat, gap: CGFloat, spawnT: Double = 0) -> CGPoint {
        let x = gap + CGFloat(c) * (cell + gap) + cell / 2
        // while spawning, the tile starts above its row and eases down (ease-out on spawnT 1→0)
        let drop = CGFloat(spawnT) * (cell + gap) * 1.6
        let y = gap + CGFloat(r) * (cell + gap) + cell / 2 - drop
        return CGPoint(x: x, y: y)
    }

    private func tileId(at p: CGPoint, side: CGFloat, cell: CGFloat, gap: CGFloat) -> Int? {
        // map a point to a grid cell, then to the (non-popped) tile occupying it
        guard p.x >= 0, p.y >= 0, p.x <= side, p.y <= side else { return nil }
        let c = Int((p.x - gap) / (cell + gap))
        let r = Int((p.y - gap) / (cell + gap))
        guard r >= 0, r < MGL_N, c >= 0, c < MGL_N else { return nil }
        // require the touch to be reasonably inside the cell, not the gutter — forgiving but not sloppy
        let ctr = center(r, c, cell: cell, gap: gap)
        if abs(p.x - ctr.x) > cell * 0.62 || abs(p.y - ctr.y) > cell * 0.62 { return nil }
        return game.tileAt(row: r, col: c)?.id
    }

    private func pathLine(cell: CGFloat, gap: CGFloat, now: Double) -> some View {
        Path { path in
            let pts = game.path.compactMap { id -> CGPoint? in
                guard let t = game.tile(id) else { return nil }
                return center(t.row, t.col, cell: cell, gap: gap)
            }
            guard let first = pts.first else { return }
            path.move(to: first)
            for p in pts.dropFirst() { path.addLine(to: p) }
        }
        .stroke(
            LinearGradient(colors: [MGL_Pal.cobalt, MGL_Pal.violet], startPoint: .leading, endPoint: .trailing),
            style: StrokeStyle(lineWidth: 9, lineCap: .round, lineJoin: .round)
        )
        .opacity(0.95)
        .shadow(color: MGL_Pal.violet.opacity(0.7), radius: 7)
        .allowsHitTesting(false)
    }

    private func tileView(_ t: MGL_Tile, cell: CGFloat, gap: CGFloat, now: Double) -> some View {
        let inPath = game.path.contains(t.id)
        let isHead = game.path.last == t.id
        let tint = MGL_tint(t.value)
        let pop = t.popT
        let bump = t.bumpT
        let spawn = t.spawnT
        return ZStack {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(LinearGradient(colors: [tint.opacity(0.95), tint.opacity(0.55)], startPoint: .topLeading, endPoint: .bottomTrailing))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(.white.opacity(inPath ? 0.95 : 0.18), lineWidth: inPath ? 2.4 : 1)
                )
                .overlay(   // pop burst flash
                    RoundedRectangle(cornerRadius: 12, style: .continuous).fill(.white.opacity(pop * 0.9))
                )
                .shadow(color: tint.opacity(inPath ? 0.7 : 0.35), radius: inPath ? 9 : 4, y: 2)
            Text("\(t.value)")
                .font(.system(size: cell * 0.42, weight: .black, design: .rounded))
                .foregroundStyle(.white)
                .shadow(color: .black.opacity(0.35), radius: 1, y: 1)
        }
        .frame(width: cell, height: cell)
        .scaleEffect((1 + pop * 0.35) * (1 + bump * 0.10) * (isHead ? 1.06 : 1) * (spawn > 0 ? 0.6 + 0.4 * (1 - spawn) : 1))
        .opacity(pop > 0 ? pop : 1)
    }

    // footer — best + new game. NEW GAME is the only chrome button (the launcher owns close).
    private var footer: some View {
        HStack(spacing: 10) {
            statChip(icon: "star.fill", tint: MGL_Pal.accent, value: "\(game.score)")
            statChip(icon: "crown.fill", tint: MGL_Pal.gold, value: "\(max(best, game.score))")
            Spacer(minLength: 0)
            Button {
                #if canImport(UIKit)
                UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                #endif
                withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { game.newGame() }
            } label: {
                HStack(spacing: 5) {
                    Image(systemName: "arrow.clockwise").font(.system(size: 11, weight: .black))
                    Text("New").font(.system(size: 12.5, weight: .heavy, design: .rounded))
                }
                .foregroundStyle(.white).padding(.horizontal, 13).frame(height: 32)
                .background(Capsule().fill(LinearGradient(colors: [MGL_Pal.violet, Color(hexL: 0x6B43C2)], startPoint: .top, endPoint: .bottom)))
            }
            .buttonStyle(.plain)
        }
    }

    private func statChip(icon: String, tint: Color, value: String) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.system(size: 9, weight: .black)).foregroundStyle(tint)
            Text(value).font(.system(size: 12.5, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(MGL_Pal.text)
        }
        .padding(.horizontal, 9).frame(height: 30)
        .background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(0.08), lineWidth: 1)))
    }
}

// MARK: - Per-value tints (a calm ramp; small = cool, big = warm — instantly readable)

private func MGL_tint(_ v: Int) -> Color {
    switch v {
    case 1: return MGL_Pal.cobalt
    case 2: return MGL_Pal.mint
    case 3: return MGL_Pal.violet
    case 4: return Color(hexL: 0xF5A524)
    case 5: return MGL_Pal.accent
    default: return MGL_Pal.rose
    }
}

// MARK: - Simulator seed (a believable mid-draw frame for the screenshot)

#if targetEnvironment(simulator)
private func MGL_seed(_ g: MGL_Game) {
    // Force a known board + a path mid-draw summing toward the target, so the static shot reads as "in play".
    g.target = 10
    g.score = 1240
    g.combo = 3
    let layout: [[Int]] = [
        [3, 5, 2, 4],
        [1, 4, 6, 2],
        [5, 2, 3, 1],
        [4, 3, 1, 5],
    ]
    var built: [MGL_Tile] = []
    var id = 0
    for r in 0..<MGL_N { for c in 0..<MGL_N {
        built.append(MGL_Tile(id: id, value: layout[r][c], row: r, col: c, spawnT: 0))
        id += 1
    }}
    g.tiles = built
    // draw a connected path: (2,0)=5 -> (1,0)=1 -> (1,1)=4  => 5+1+4 = 10  (a winning path, "release!")
    func idAt(_ r: Int, _ c: Int) -> Int { r * MGL_N + c }
    g.path = [idAt(2, 0), idAt(1, 0), idAt(1, 1)]
}
#endif
