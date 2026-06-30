import SwiftUI

// The desk's icon system. Two ideas the owner asked for:
//   1. VARIETY — each object gets a stable-but-varied sprite drawn from a per-kind pool, so a desk of
//      meetings isn't ten identical cassettes. The pick is deterministic per id (a stable hash, NOT
//      Swift's per-launch-randomized hashValue) so it never changes between launches.
//   2. CHOICE — the user can override any object's icon; the override wins and persists.
//
// Drop a new `<name>.png` into App/, bundle it in gen-meeting-capture.rb, and add it to the kind's
// list below — it instantly joins the variety pool AND the picker. Sprites render via DeskSprite.

enum DeskSprites {
    /// Every sprite a kind can wear, in display order (first = the classic default).
    static func variants(_ kind: PrimitiveKind) -> [String] {
        // Counts must match the shipped art (`<base>.png` + `<base>2.png`…`<base>N.png`); a gap renders
        // DeskSprite's placeholder. Bump N when more variety art is bundled.
        switch kind {
        case .meeting:   return numbered("cassette", 17)
        case .note:      return numbered("note", 16)
        case .kb:        return numbered("crystal", 16)
        case .model:     return ["cartridge"]
        default:         return [kind.glyph]
        }
    }

    /// ["cassette", "cassette2", … "cassetteN"] — the first asset has no numeric suffix.
    private static func numbered(_ base: String, _ count: Int) -> [String] {
        count <= 1 ? [base] : [base] + (2...count).map { "\(base)\($0)" }
    }

    /// A stable hash (djb2) — UNLIKE `String.hashValue`, which is seeded per process launch and would
    /// reshuffle every object's icon on every cold start.
    static func stableHash(_ s: String) -> Int {
        var h = 5381
        for b in s.utf8 { h = (h &* 33) &+ Int(b) }
        return h
    }
}

/// Per-object icon overrides, persisted in UserDefaults. A plain enum (nonisolated, no shared mutable
/// actor state) so the struct primitives can read it from their `glyph` getter. The desk re-renders
/// naturally when the picker closes (a state change), so glyphs recompute against the fresh value.
enum SpriteStore {
    private static let key = "hs.desk.spriteOverride"
    private static var map: [String: String] {
        get { (UserDefaults.standard.dictionary(forKey: key) as? [String: String]) ?? [:] }
        set { UserDefaults.standard.set(newValue, forKey: key) }
    }

    /// The sprite a primitive should wear: an explicit override, else a stable variant from its pool.
    static func sprite(id: String, kind: PrimitiveKind, fallback: String) -> String {
        if let chosen = map[id] { return chosen }
        let pool = DeskSprites.variants(kind)
        guard pool.count > 1 else { return pool.first ?? fallback }
        return pool[abs(DeskSprites.stableHash(id)) % pool.count]
    }

    static func chosen(_ id: String) -> String? { map[id] }

    static func set(_ id: String, to name: String?) {
        var m = map
        if let name { m[id] = name } else { m.removeValue(forKey: id) }
        map = m
    }
}

struct IconPickTarget: Identifiable { let id: String; let kind: PrimitiveKind; let title: String }

/// The in-world icon picker — a gallery of the kind's sprites + an "Auto" cell that clears the override
/// back to the stable variety pick. Reuses the desk's dark panel look.
struct DioIconPicker: View {
    let target: IconPickTarget
    let current: String?              // the active override, or nil when on auto
    let onPick: (String?) -> Void     // nil = back to Auto
    let onClose: () -> Void
    var body: some View {
        let pool = DeskSprites.variants(target.kind)
        ZStack {
            Color.black.opacity(0.5).ignoresSafeArea().contentShape(Rectangle()).onTapGesture { onClose() }
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Choose an icon").font(.system(size: 17, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text(target.title).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                    Spacer()
                    Button(action: onClose) {
                        Image(systemName: "xmark").font(.system(size: 13, weight: .black)).foregroundStyle(DioPal.text)
                            .frame(width: 32, height: 32).background(Circle().fill(.white.opacity(0.1)))
                    }.buttonStyle(.plain)
                }
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 78), spacing: 12)], spacing: 12) {
                    cell(content: AnyView(Image(systemName: "wand.and.stars").font(.system(size: 24, weight: .bold)).foregroundStyle(DioPal.accent).frame(width: 52, height: 52)),
                         label: "Auto", selected: current == nil) { onPick(nil) }
                    ForEach(pool, id: \.self) { n in
                        cell(content: AnyView(DeskSprite(name: n, size: 52)), label: nil, selected: current == n) { onPick(n) }
                    }
                }
            }
            .padding(20).frame(maxWidth: 360)
            .background(RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
            .padding(24)
        }
    }
    private func cell(content: AnyView, label: String?, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: 5) {
                content
                if let label { Text(label).font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted) }
            }
            .frame(maxWidth: .infinity).padding(.vertical, 10)
            .background(RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(selected ? DioPal.accent.opacity(0.18) : .white.opacity(0.04))
                .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(selected ? DioPal.accent : .white.opacity(0.08), lineWidth: selected ? 2 : 1)))
        }.buttonStyle(.plain)
    }
}
