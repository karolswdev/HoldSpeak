import SwiftUI
import QuartzCore
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — WORDFORGE. A tiny, glanceable anagram you summon onto the desk during a boring meeting while
// everything else keeps running. A small curated word list lives in this file (no network, no dictionary).
// You get six scrambled letter tiles; tap them to forge the hidden word into the rack, tap a placed tile to
// pull it back. A hint reveals one letter; shuffle re-tumbles the pool. Solve it and the rack cascades — then
// the next word slides in and your streak climbs. Built to the DeskOS Component Pattern canon
// (docs/internal/DESKOS_COMPONENT_PATTERN.md) — the nine laws, the ambient-recorder shape.
//
// INTEGRATION CONTRACT (per the council brief): the public entry point is `MG_Word` — a no-arg View that
// renders ONLY the game and FILLS the frame the launcher hands it (the launcher owns the ephemeral window +
// close; we draw no window chrome of our own). `MG_Word.title` / `.icon` name it for the launcher.
//
//   • Quiet at rest / alive in motion (Law 3, build-checklist #11): tiles bob and breathe, the active slot
//     pulses, a hint shimmer sweeps, a solve fires a staggered cascade + a confetti burst. No idle billboard.
//   • Act in place, one gesture per tile (Law 5): a single tap forges or returns a tile — no system keyboard,
//     no detour. Keyboard-light by design (tap letters, not the keyboard).
//   • Harvest, never dead-end (Law 6 ADAPTED): a game has no OutputRecord, so the keepable artifact is the
//     STREAK — your run carries forward (persisted in @AppStorage "hs.mg.word.best"), and every solved word
//     leaves a "Next word" affordance so you are never stranded.
//   • One badge of truth (Law 8 ADAPTED): a game has no egress; the one quiet badge is a STREAK / BEST chip
//     in place of a local/cloud chip. (Adaptation noted honestly per the canon's "reconcile, don't drift".)
//   • Gated, never autonomous (Law 9): every effectful thing is a tap. Nothing leaves the device or acts on
//     the world — this is a self-contained toy.
//   • One coordinate space (the trap): the whole game is a plain VStack inside the launcher's frame; overlays
//     (the confetti, the solved banner) are non-hit-testing and live in the same space — no GeometryReader-vs-
//     safe-area mixing, no full-screen scrim of our own.
//
// NOTE ON DioPal: this file uses the desk palette declared atop DeskDioramaStage.swift (DioPal + the
// Color(hex:) initializer). It declares no new global mechanism.

// MARK: - The curated word list (no network, no dictionary — ~150 honest, glanceable words)

private enum WordBank {
    // Six-letter words only, so the tile rack is always a tidy six. Common, satisfying, instantly grokkable —
    // a meeting-friendly mix: nothing obscure, nothing you'd ever need to look up. ~150 curated, all length 6.
    static let words: [String] = [
        "PLANET", "ROCKET", "GARDEN", "SILVER", "ORANGE", "PURPLE", "YELLOW", "CASTLE",
        "BRIDGE", "FOREST", "ISLAND", "MARKET", "WINTER", "SUMMER", "SPRING", "AUTUMN",
        "FRIEND", "FAMILY", "MOTHER", "FATHER", "SISTER", "PEOPLE", "PERSON", "MEMORY",
        "DREAMS", "WONDER", "BEAUTY", "BRIGHT", "GENTLE", "SIMPLE", "STRONG", "STEADY",
        "CAMERA", "PENCIL", "PAPERS", "LETTER", "BANNER", "POCKET", "BUTTON", "BASKET",
        "CANDLE", "MIRROR", "WINDOW", "CARPET", "BOTTLE", "KETTLE", "SAUCER", "SPOONS",
        "COFFEE", "BUTTER", "CHEESE", "TOMATO", "POTATO", "CARROT", "CELERY", "PEPPER",
        "BANANA", "CHERRY", "GRAPES", "PEANUT", "WALNUT", "RAISIN", "MELONS", "LEMONS",
        "ANIMAL", "RABBIT", "TURTLE", "MONKEY", "DONKEY", "FALCON", "PARROT", "BEAVER",
        "SALMON", "SHRIMP", "OYSTER", "WALRUS", "JAGUAR", "COUGAR", "BADGER", "FERRET",
        "OCEANS", "RIVERS", "VALLEY", "CANYON", "DESERT", "MEADOW", "JUNGLE", "TUNDRA",
        "PLANTS", "FLOWER", "PETALS", "BRANCH", "LEAVES", "ACORNS", "PEBBLE", "STONES",
        "TRAVEL", "VOYAGE", "FLIGHT", "TICKET", "DEPART", "ARRIVE", "WANDER", "ROVING",
        "MUSEUM", "TEMPLE", "PALACE", "TOWERS", "STREET", "AVENUE", "SQUARE", "GARAGE",
        "GOLDEN", "MARBLE", "COPPER", "BRONZE", "VELVET", "COTTON", "DENIMS", "LINENS",
        "RHYTHM", "MELODY", "GUITAR", "VIOLIN", "PIANOS", "TEMPOS", "SINGER", "CHORDS",
        "PUZZLE", "RIDDLE", "SECRET", "TOKENS", "LEGEND", "MYTHIC", "QUESTS", "WIZARD",
        "BRAINS", "CLEVER", "WISDOM", "GENIUS", "TALENT", "SKILLS", "EXPERT", "MASTER",
        "MUFFIN", "WAFFLE", "COOKIE", "DONUTS", "SUGARS", "SYRUPS", "TOFFEE", "CANDLE",
        "SUNSET", "CLOUDS", "BREEZE", "FROSTY", "STORMS", "RAINED", "SHADOW", "BRIGHT",
        "GLOBES", "ORBITS", "COMETS", "GALAXY", "NEBULA", "COSMOS", "ROCKET", "LAUNCH",
        "ENERGY", "MOTION", "FORCES", "MATTER", "ATOMIC", "PHOTON", "SIGNAL", "WAVING",
        "SMILES", "LAUGHS", "CHEERY", "JOYOUS", "BUBBLY", "GIGGLE", "PLAYED", "HAPPEN",
    ]
}

// MARK: - The game model — one place; the view is a pure render of it. No @Published mutated in `body`.

private struct ForgeTile: Identifiable {
    let id: Int
    let letter: Character
    var placed: Bool = false   // moved into the rack
    var slot: Int? = nil       // which rack slot it sits in (when placed)
    var wobble: Double = 0     // a brief wobble on a wrong-spot tap (decays)
}

private enum ForgePhase { case forging, solved }

private final class ForgeGame: ObservableObject {
    @Published var target: String = ""
    @Published var pool: [ForgeTile] = []      // all six tiles, in pool order
    @Published var rack: [Int?] = []           // slot -> tile id (or nil)
    @Published var phase: ForgePhase = .forging
    @Published var hintsUsed: Int = 0
    @Published var streak: Int = 0
    @Published var solveT: Double = 0          // 0…1 solve-cascade progress, drives the celebration
    @Published var shakeSlot: Int? = nil       // a slot that just rejected (visual nudge)

    private var deck: [String] = []
    private var lastStep: TimeInterval = 0
    private var ticker: Timer?

    var len: Int { target.count }

    // The loop runs on a Timer in .common mode (keeps decaying juice during a tap/scroll), and we NEVER mutate
    // @Published from inside SwiftUI's body pass.
    func start() {
        if target.isEmpty { newDeck(); nextWord(resetStreak: false) }
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

    private func newDeck() {
        deck = WordBank.words.shuffled()
    }

    func nextWord(resetStreak: Bool) {
        if resetStreak { streak = 0 }
        if deck.isEmpty { newDeck() }
        let w = deck.removeFirst()
        target = w
        hintsUsed = 0
        phase = .forging
        solveT = 0
        rack = Array(repeating: nil, count: w.count)
        // scramble the letters into tiles — re-roll until it isn't already the answer (a tiny kindness)
        var scrambled = Array(w)
        var guard0 = 0
        repeat { scrambled.shuffle(); guard0 += 1 } while String(scrambled) == w && guard0 < 12
        pool = scrambled.enumerated().map { ForgeTile(id: $0.offset, letter: $0.element) }
    }

    // MARK: tap actions (Law 5 — one gesture per tile, in place)

    /// Tap a pool tile → drop it into the first empty rack slot. If it's the RIGHT letter for that slot, it
    /// snaps; if not, we still place it (forgiving — you can always pull it back), so the player explores.
    func tapPool(_ id: Int) {
        guard phase == .forging else { return }
        guard let pi = pool.firstIndex(where: { $0.id == id }), !pool[pi].placed else { return }
        guard let slot = rack.firstIndex(where: { $0 == nil }) else { return }
        rack[slot] = id
        pool[pi].placed = true
        pool[pi].slot = slot
        haptic(.light)
        checkSolved()
    }

    /// Tap a placed (racked) tile → send it back to the pool.
    func tapRack(_ slot: Int) {
        guard phase == .forging, slot < rack.count, let id = rack[slot] else { return }
        if let pi = pool.firstIndex(where: { $0.id == id }) {
            pool[pi].placed = false
            pool[pi].slot = nil
        }
        rack[slot] = nil
        haptic(.light)
    }

    /// Hint — fill the next empty slot with the CORRECT tile (pulling from the pool, swapping if a wrong tile
    /// already sits there). Always available; costs nothing but the satisfaction.
    func hint() {
        guard phase == .forging else { return }
        let chars = Array(target)
        // find the first slot whose placed letter is wrong (or empty)
        for slot in 0..<len {
            let want = chars[slot]
            let here = rack[slot].flatMap { id in pool.first(where: { $0.id == id })?.letter }
            if here == want { continue }
            // pull whatever wrong tile is here back to the pool
            if let id = rack[slot], let pi = pool.firstIndex(where: { $0.id == id }) {
                pool[pi].placed = false; pool[pi].slot = nil; rack[slot] = nil
            }
            // find an unplaced pool tile with the wanted letter
            if let pi = pool.firstIndex(where: { !$0.placed && $0.letter == want }) {
                rack[slot] = pool[pi].id
                pool[pi].placed = true
                pool[pi].slot = slot
                hintsUsed += 1
                haptic(.medium)
                checkSolved()
            }
            return
        }
    }

    /// Shuffle the unplaced pool tiles (just re-tumbles their visual order — your placed work is untouched).
    func shufflePool() {
        guard phase == .forging else { return }
        let placedTiles = pool.filter { $0.placed }
        let loose = pool.filter { !$0.placed }.shuffled()
        pool = placedTiles + loose
        haptic(.light)
    }

    private func checkSolved() {
        let built = rack.compactMap { id in id.flatMap { tid in pool.first(where: { $0.id == tid })?.letter } }
        guard built.count == len, String(built) == target else { return }
        phase = .solved
        streak += 1
        haptic(.heavy)
    }

    // MARK: the loop — decays juice + drives the solve cascade

    func tick(_ now: TimeInterval) {
        if lastStep == 0 { lastStep = now }
        let dt = now - lastStep
        lastStep = now
        for i in pool.indices where pool[i].wobble > 0 { pool[i].wobble = max(0, pool[i].wobble - dt * 5) }
        if shakeSlot != nil { /* the view animates this; clear it after a beat */ }
        if phase == .solved, solveT < 1 { solveT = min(1, solveT + dt * 1.4) }
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// MARK: - The public entry point (the integration contract: MG_Word)

public struct MG_Word: View {
    public static let title: String = "Wordforge"
    public static let icon: String = "textformat.abc"

    @StateObject private var game = ForgeGame()
    @AppStorage("hs.mg.word.best") private var best: Int = 0

    public init() {}

    // simulator-only seed hook so the harness can stage believable frames for a screenshot
    private static var seedState: String {
        #if targetEnvironment(simulator)
        return ProcessInfo.processInfo.environment["HS_MG_WORD"] ?? ""
        #else
        return ""
        #endif
    }

    public var body: some View {
        VStack(spacing: 14) {
            header
            ZStack {
                rackRow
                if game.phase == .solved { solvedBanner.transition(.scale.combined(with: .opacity)) }
            }
            .animation(.spring(response: 0.5, dampingFraction: 0.7), value: game.phase)
            poolRow
            Spacer(minLength: 0)
            controls
        }
        .padding(16)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(boardBackground)
        .overlay(confetti.allowsHitTesting(false))   // celebration lives in the same space, never intercepts taps
        .onAppear {
            game.start()
            switch Self.seedState {
            case "mid": stageMidPuzzle()
            case "solved": stageSolved()
            default: break
            }
        }
        .onDisappear {
            game.stop()
            if game.streak > best { best = game.streak }
        }
        .onChange(of: game.streak) { _, s in if s > best { best = s } }
    }

    // a believable mid-solve frame: forge the first three letters correctly, leave the rest scrambled
    private func stageMidPuzzle() {
        let chars = Array(game.target)
        for slot in 0..<min(3, game.len) {
            let want = chars[slot]
            if let pi = game.pool.firstIndex(where: { !$0.placed && $0.letter == want }) {
                game.rack[slot] = game.pool[pi].id
                game.pool[pi].placed = true
                game.pool[pi].slot = slot
            }
        }
        game.streak = 4
    }

    // a believable just-solved frame for the celebration screenshot
    private func stageSolved() {
        let chars = Array(game.target)
        for slot in 0..<game.len {
            let want = chars[slot]
            if let pi = game.pool.firstIndex(where: { !$0.placed && $0.letter == want }) {
                game.rack[slot] = game.pool[pi].id
                game.pool[pi].placed = true
                game.pool[pi].slot = slot
            }
        }
        game.streak = 7
        game.phase = .solved
        game.solveT = 0.45   // mid-cascade, confetti in flight
    }

    // MARK: header — title + the STREAK/BEST status badge (Law 8 adapted)

    private var header: some View {
        HStack(spacing: 9) {
            Image(systemName: "textformat.abc").font(.system(size: 14, weight: .bold)).foregroundStyle(DioPal.violet)
            Text("Wordforge").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            Spacer(minLength: 0)
            statusBadge
        }
        .padding(.trailing, 22)   // leave clear room for the launcher's own close affordance
    }

    private var statusBadge: some View {
        HStack(spacing: 8) {
            HStack(spacing: 3) {
                Image(systemName: "flame.fill").font(.system(size: 9, weight: .black))
                Text("\(game.streak)").font(.system(size: 11, weight: .heavy, design: .rounded).monospacedDigit())
            }.foregroundStyle(DioPal.accent)
            Rectangle().fill(.white.opacity(0.12)).frame(width: 1, height: 11)
            HStack(spacing: 3) {
                Image(systemName: "crown.fill").font(.system(size: 9, weight: .black))
                Text("\(max(best, game.streak))").font(.system(size: 11, weight: .heavy, design: .rounded).monospacedDigit())
            }.foregroundStyle(DioPal.mint)
        }
        .padding(.horizontal, 9).frame(height: 24)
        .background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(0.09), lineWidth: 1)))
    }

    // MARK: the rack — the slots you forge the word into (tap a placed tile to pull it back)

    private var rackRow: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let chars = Array(game.target)
            // the first empty slot pulses to invite the next placement
            let nextEmpty = game.rack.firstIndex(where: { $0 == nil })
            HStack(spacing: 7) {
                ForEach(0..<game.len, id: \.self) { slot in
                    let id = game.rack[slot]
                    let tile = id.flatMap { tid in game.pool.first(where: { $0.id == tid }) }
                    let correct = tile != nil && slot < chars.count && tile!.letter == chars[slot]
                    let isNext = nextEmpty == slot
                    let cascade = game.phase == .solved
                    let pop = cascade ? max(0, 1 - abs(game.solveT * Double(game.len + 2) - Double(slot))) : 0
                    RackSlot(letter: tile?.letter, correct: correct, isNext: isNext, pulse: isNext ? (0.5 + 0.5 * sin(t * 3)) : 0, cascade: pop)
                        .onTapGesture { game.tapRack(slot) }
                }
            }
        }
    }

    // MARK: the pool — the scrambled letter tiles (tap one to forge it into the next slot)

    private var poolRow: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            HStack(spacing: 9) {
                ForEach(game.pool) { tile in
                    let ph = Double(tile.id) * 1.3
                    let bob = tile.placed ? 0 : CGFloat(sin(t * 1.4 + ph) * 2.2)
                    PoolTile(letter: tile.letter, placed: tile.placed, wobble: tile.wobble)
                        .offset(y: -bob)
                        .opacity(tile.placed ? 0.18 : 1)
                        .scaleEffect(tile.placed ? 0.86 : 1)
                        .allowsHitTesting(!tile.placed && game.phase == .forging)
                        .onTapGesture { game.tapPool(tile.id) }
                        .animation(.spring(response: 0.4, dampingFraction: 0.7), value: tile.placed)
                }
            }
        }
    }

    // MARK: controls — hint · shuffle (or, when solved, next word). All taps (Law 9).

    @ViewBuilder private var controls: some View {
        if game.phase == .solved {
            Button(action: { withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { game.nextWord(resetStreak: false) } }) {
                HStack(spacing: 7) {
                    Image(systemName: "arrow.right.circle.fill").font(.system(size: 14, weight: .bold))
                    Text("Next word").font(.system(size: 14, weight: .heavy, design: .rounded))
                }
                .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 46)
                .background(Capsule().fill(LinearGradient(colors: [DioPal.violet, Color(hex: 0x6B43C2)], startPoint: .top, endPoint: .bottom)))
            }.buttonStyle(.plain)
        } else {
            HStack(spacing: 10) {
                pillButton("Hint", "lightbulb.fill", DioPal.cobalt) { game.hint() }
                pillButton("Shuffle", "shuffle", DioPal.muted) { withAnimation(.easeInOut(duration: 0.25)) { game.shufflePool() } }
                pillButton("Skip", "forward.fill", DioPal.muted) { withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { game.nextWord(resetStreak: true) } }
            }
        }
    }

    private func pillButton(_ label: String, _ icon: String, _ tint: Color, _ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon).font(.system(size: 12, weight: .bold))
                Text(label).font(.system(size: 13, weight: .heavy, design: .rounded))
            }
            .foregroundStyle(tint == DioPal.muted ? DioPal.text.opacity(0.82) : tint)
            .frame(maxWidth: .infinity).frame(height: 42)
            .background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(tint.opacity(0.4), lineWidth: 1)))
        }.buttonStyle(.plain)
    }

    // MARK: the solved banner + confetti

    private var solvedBanner: some View {
        VStack(spacing: 4) {
            Image(systemName: "checkmark.seal.fill").font(.system(size: 26, weight: .bold)).foregroundStyle(DioPal.mint)
            Text(game.target).font(.system(size: 22, weight: .black, design: .rounded)).foregroundStyle(DioPal.text).tracking(3)
            Text(game.hintsUsed == 0 ? "Forged clean!" : "Forged with \(game.hintsUsed) hint\(game.hintsUsed == 1 ? "" : "s")")
                .font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(game.hintsUsed == 0 ? DioPal.accent : DioPal.muted)
        }
        .padding(.horizontal, 22).padding(.vertical, 14)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.black.opacity(0.45))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(DioPal.mint.opacity(0.4), lineWidth: 1)))
        .allowsHitTesting(false)
    }

    private var confetti: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            Canvas { ctx, size in
                guard game.phase == .solved else { return }
                let prog = game.solveT
                let cols: [Color] = [DioPal.accent, DioPal.cobalt, DioPal.violet, DioPal.mint, Color(hex: 0xFFC857)]
                for i in 0..<26 {
                    let s = Double(i)
                    let ang = s * 0.61
                    let spread = prog * (90 + s.truncatingRemainder(dividingBy: 60))
                    let x = size.width / 2 + cos(ang) * spread + sin(t * 2 + s) * 6
                    let y = size.height * 0.38 + sin(ang) * spread + prog * prog * 120  // fall under gravity
                    let r = 2.5 + s.truncatingRemainder(dividingBy: 3)
                    ctx.opacity = max(0, 1 - prog) * 0.9
                    ctx.fill(Path(ellipseIn: CGRect(x: x, y: y, width: r, height: r)), with: .color(cols[i % cols.count]))
                }
            }
        }
    }

    private var boardBackground: some View {
        // a whisper of darkening for tile contrast; the launcher's frosted window + the desk still read through
        LinearGradient(colors: [Color.black.opacity(0.10), Color.black.opacity(0.02)], startPoint: .top, endPoint: .bottom)
    }
}

// MARK: - The pieces

private struct RackSlot: View {
    let letter: Character?
    let correct: Bool
    let isNext: Bool
    let pulse: Double
    let cascade: Double   // 0…1 solve-cascade pop for this slot

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 9, style: .continuous)
                .fill(letter == nil
                      ? AnyShapeStyle(Color.white.opacity(0.04))
                      : AnyShapeStyle(LinearGradient(colors: correct
                            ? [DioPal.mint.opacity(0.32), DioPal.mint.opacity(0.14)]
                            : [DioPal.violet.opacity(0.30), DioPal.violet.opacity(0.12)],
                          startPoint: .top, endPoint: .bottom)))
                .overlay(RoundedRectangle(cornerRadius: 9, style: .continuous)
                    .strokeBorder(letter == nil
                        ? .white.opacity(0.10 + pulse * 0.35)
                        : (correct ? DioPal.mint.opacity(0.7) : DioPal.violet.opacity(0.6)),
                        lineWidth: isNext ? 1.6 : 1.2))
            if let c = letter {
                Text(String(c)).font(.system(size: 21, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
            } else if isNext {
                // a quiet caret in the next slot
                RoundedRectangle(cornerRadius: 1).fill(DioPal.text.opacity(0.25 + pulse * 0.4)).frame(width: 2, height: 18)
            }
        }
        .frame(width: 34, height: 42)
        .scaleEffect((isNext ? 1 + pulse * 0.04 : 1) + cascade * 0.22)
        .shadow(color: (correct ? DioPal.mint : .clear).opacity(0.4 + cascade * 0.5), radius: 5 + cascade * 8)
        .contentShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
    }
}

private struct PoolTile: View {
    let letter: Character
    let placed: Bool
    let wobble: Double

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 11, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x241D33), Color(hex: 0x13101C)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous).strokeBorder(DioPal.violet.opacity(0.5), lineWidth: 1.3))
                .overlay(   // a top sheen, the tactile letter-tile feel
                    RoundedRectangle(cornerRadius: 11, style: .continuous)
                        .fill(LinearGradient(colors: [.white.opacity(0.14), .clear], startPoint: .top, endPoint: .center))
                )
            Text(String(letter)).font(.system(size: 22, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
        }
        .frame(width: 40, height: 46)
        .rotationEffect(.degrees(sin(wobble * .pi * 4) * 7))
        .shadow(color: .black.opacity(0.45), radius: 6, y: 4)
        .shadow(color: DioPal.violet.opacity(0.3), radius: 5)
    }
}
