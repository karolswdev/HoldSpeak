import SwiftUI

// HSM-14 — "4096": a 2048-style swipe-merge for the desk arcade. Content-only MG_* per the launcher contract
// (the ephemeral window + close come from DioGameWindow). Swipe to slide all tiles; equal neighbours merge and
// double; a fresh 2 (sometimes 4) appears each move. Reach 4096 to win; jam the board to lose. Turn-based, so
// no game loop — state mutates only in the swipe handler, never in `body`. One DragGesture.

public struct MG_Merge: View {
    public static let title = "4096"
    public static let icon = "square.grid.3x3.fill"
    public init() {}
    @StateObject private var g = MergeGame()

    public var body: some View {
        GeometryReader { geo in
            let side = min(geo.size.width, geo.size.height - 44)
            let gap: CGFloat = 7
            let cell = (side - gap * 5) / 4
            VStack(spacing: 8) {
                // HUD — score + best, the canon's quiet status badge
                HStack(spacing: 8) {
                    Text("4096").font(.system(size: 15, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Spacer(minLength: 0)
                    badge("SCORE", g.score, DioPal.accent)
                    badge("BEST", g.best, DioPal.violet)
                }
                .padding(.horizontal, 4)
                ZStack {
                    RoundedRectangle(cornerRadius: 12, style: .continuous).fill(.white.opacity(0.05))
                    // empty cell wells
                    ForEach(0..<16, id: \.self) { i in
                        RoundedRectangle(cornerRadius: 8, style: .continuous).fill(.white.opacity(0.04))
                            .frame(width: cell, height: cell).position(pos(i % 4, i / 4, cell, gap))
                    }
                    // tiles
                    ForEach(0..<16, id: \.self) { i in
                        let v = g.board[i / 4][i % 4]
                        if v > 0 {
                            tile(v, cell).position(pos(i % 4, i / 4, cell, gap))
                                .transition(.scale.combined(with: .opacity))
                        }
                    }
                }
                .frame(width: side, height: side)
                .overlay { if g.won || g.lost { endCard } }
                .animation(.spring(response: 0.32, dampingFraction: 0.74), value: g.board)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 18).onEnded { v in
                guard !g.lost else { return }
                if abs(v.translation.width) > abs(v.translation.height) { g.move(v.translation.width > 0 ? .right : .left) }
                else { g.move(v.translation.height > 0 ? .down : .up) }
            })
        }
    }
    private func pos(_ c: Int, _ r: Int, _ cell: CGFloat, _ gap: CGFloat) -> CGPoint {
        CGPoint(x: gap + cell / 2 + CGFloat(c) * (cell + gap), y: gap + cell / 2 + CGFloat(r) * (cell + gap))
    }
    private func badge(_ label: String, _ n: Int, _ tint: Color) -> some View {
        VStack(spacing: 0) {
            Text(label).font(.system(size: 7, weight: .black, design: .rounded)).tracking(0.5).foregroundStyle(tint)
            Text("\(n)").font(.system(size: 13, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(DioPal.text)
        }
        .padding(.horizontal, 9).padding(.vertical, 3).background(Capsule().fill(.white.opacity(0.06)))
    }
    private func tile(_ v: Int, _ cell: CGFloat) -> some View {
        let tint = MergeGame.color(v)
        return RoundedRectangle(cornerRadius: 8, style: .continuous)
            .fill(LinearGradient(colors: [tint, MergeGame.deep(v)], startPoint: .topLeading, endPoint: .bottomTrailing))
            .overlay(RoundedRectangle(cornerRadius: 8, style: .continuous).strokeBorder(.white.opacity(0.18), lineWidth: 1))
            .overlay(Text("\(v)").font(.system(size: v >= 1000 ? cell * 0.26 : cell * 0.36, weight: .black, design: .rounded)).foregroundStyle(.white).shadow(color: .black.opacity(0.35), radius: 1, y: 1))
            .frame(width: cell, height: cell)
            .shadow(color: tint.opacity(0.4), radius: 3, y: 1)
    }
    private var endCard: some View {
        VStack(spacing: 8) {
            Image(systemName: g.won ? "crown.fill" : "arrow.counterclockwise.circle.fill").font(.system(size: 26, weight: .bold)).foregroundStyle(g.won ? DioPal.accent : DioPal.muted)
            Text(g.won ? "4096!" : "No moves").font(.system(size: 17, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
            Text("\(g.score) pts").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.mint)
            Button { g.reset() } label: {
                Text("Play again").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(.white)
                    .padding(.horizontal, 16).frame(height: 38).background(Capsule().fill(LinearGradient(colors: [DioPal.violet, DioPal.violet.opacity(0.6)], startPoint: .top, endPoint: .bottom)))
            }.buttonStyle(.plain)
        }
        .padding(20).background(RoundedRectangle(cornerRadius: 18).fill(.black.opacity(0.6)).overlay(RoundedRectangle(cornerRadius: 18).strokeBorder(.white.opacity(0.12), lineWidth: 1)))
    }
}

final class MergeGame: ObservableObject {
    enum Dir { case left, right, up, down }
    @Published var board: [[Int]] = Array(repeating: Array(repeating: 0, count: 4), count: 4)
    @Published var score = 0
    @Published var won = false
    @Published var lost = false
    private(set) var best = UserDefaults.standard.integer(forKey: "hs.mg.merge.best")

    init() { reset() }

    func reset() {
        board = Array(repeating: Array(repeating: 0, count: 4), count: 4)
        score = 0; won = false; lost = false
        spawn(); spawn()
    }
    private func spawn() {
        let empties = (0..<16).filter { board[$0 / 4][$0 % 4] == 0 }
        guard let i = empties.randomElement() else { return }
        board[i / 4][i % 4] = Double.random(in: 0...1) < 0.9 ? 2 : 4
    }
    func move(_ dir: Dir) {
        let before = board
        var b = board
        for k in 0..<4 {
            var line: [Int]
            switch dir {
            case .left:  line = b[k]
            case .right: line = b[k].reversed()
            case .up:    line = (0..<4).map { b[$0][k] }
            case .down:  line = (0..<4).map { b[3 - $0][k] }
            }
            let (slid, gained) = Self.slide(line)
            score += gained
            for j in 0..<4 {
                let v = slid[j]
                switch dir {
                case .left:  b[k][j] = v
                case .right: b[k][3 - j] = v
                case .up:    b[j][k] = v
                case .down:  b[3 - j][k] = v
                }
            }
        }
        guard b != before else { return }     // only a real change spawns + advances
        board = b
        if board.flatMap({ $0 }).contains(4096) { won = true }
        if score > best { best = score; UserDefaults.standard.set(best, forKey: "hs.mg.merge.best") }
        spawn()
        if !anyMove() { lost = true }
    }
    private static func slide(_ line: [Int]) -> ([Int], Int) {
        let t = line.filter { $0 != 0 }
        var out: [Int] = []; var gained = 0; var i = 0
        while i < t.count {
            if i + 1 < t.count, t[i] == t[i + 1] { let v = t[i] * 2; out.append(v); gained += v; i += 2 }
            else { out.append(t[i]); i += 1 }
        }
        while out.count < 4 { out.append(0) }
        return (out, gained)
    }
    private func anyMove() -> Bool {
        if board.flatMap({ $0 }).contains(0) { return true }
        for r in 0..<4 { for c in 0..<4 {
            if c < 3, board[r][c] == board[r][c + 1] { return true }
            if r < 3, board[r][c] == board[r + 1][c] { return true }
        } }
        return false
    }
    static func color(_ v: Int) -> Color {
        let idx = max(0, Int(log2(Double(max(2, v)))) - 1)
        return DioPal.zonePalette[idx % DioPal.zonePalette.count]
    }
    static func deep(_ v: Int) -> Color { color(v).opacity(0.55) }
}
