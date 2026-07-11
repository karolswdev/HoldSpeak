import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — RECIPES. A Recipe is a DeskPrimitive you BUILD: an avatar + a name + how it
// behaves (system prompt) + what to ask (a user template) + the context it always carries (manual notes,
// the current zone's meetings, a knowledge base). Once built it lives on the desk as a character you can
// ASK a question, or ROUTE a card through (it answers grounded in its system prompt + context). The whole
// thing runs on the SAME inference seam as everything else (on-device GGUF or an OpenAI-compatible endpoint).

// MARK: - the persisted record

// The persisted RecipeRecord lives in Sources/RuntimeCore/Desk/DeskRecords.swift (HS-72-09),
// embedding the canonical `Recipe` contract. Only the App-flavoured convenience lives here:
// a blank draft picks its avatar from the App's `RecipeAvatars` gallery.
extension RecipeRecord {
    static func blank() -> RecipeRecord {
        RecipeRecord(id: UUID().uuidString, name: "", avatar: RecipeAvatars.all.first!.id, role: "",
                    systemPrompt: "", userTemplate: "{input}", manualContext: "", useZoneContext: false, kb: "")
    }
}

// One turn in a conversation with a recipe. Threads are persisted per recipe (hs.diorama.recipechats).
struct RecipeMessage: Codable, Identifiable, Equatable {
    var id: String; var role: String /* "you" | "recipe" */; var text: String
    var isYou: Bool { role == "you" }
    var isError: Bool { text.hasPrefix("⚠️") }
}

// MARK: - the avatar gallery (grouped — pick a group, then a face)

enum AvatarArt: Equatable { case symbol(String); case pixel(String) }   // SF-symbol glyph OR a bundled pixel-art PNG
struct RecipeAvatar: Identifiable { let id: String; let art: AvatarArt; let hue: Double }
struct RecipeAvatarGroup: Identifiable { let id: String; let title: String; let avatars: [RecipeAvatar] }

enum RecipeAvatars {
    // GROUP 1 "Glyphs" — each an SF-symbol face + a baked hue, so the set reads as distinct characters.
    static let symbols: [String] = [
        "brain.head.profile", "brain", "sparkles", "wand.and.stars", "bolt.fill", "flame.fill",
        "leaf.fill", "drop.fill", "snowflake", "sun.max.fill", "moon.stars.fill", "cloud.fill",
        "wind", "atom", "function", "infinity", "cpu", "memorychip",
        "gearshape.2.fill", "puzzlepiece.fill", "lightbulb.fill", "magnifyingglass", "scope", "binoculars.fill",
        "chart.line.uptrend.xyaxis", "book.fill", "graduationcap.fill", "pencil.and.outline", "paintbrush.pointed.fill", "paintpalette.fill",
        "theatermasks.fill", "music.note", "guitars.fill", "camera.fill", "film.fill", "gamecontroller.fill",
        "die.face.5.fill", "crown.fill", "shield.fill", "flag.fill", "star.fill", "heart.fill",
        "bell.fill", "globe", "hare.fill", "tortoise.fill", "ladybug.fill", "fish.fill",
        "bird.fill", "pawprint.fill", "ant.fill", "sailboat.fill",
    ]
    // GROUPS 2-4 — bespoke PixelLab pixel-art characters bundled as `agent_<prefix><N>.png` (see DeskSprite).
    static let glyphs: [RecipeAvatar] = symbols.enumerated().map { i, s in
        RecipeAvatar(id: "a\(i)", art: .symbol(s), hue: Double(i) / Double(symbols.count))
    }
    private static func pixelSet(_ prefix: String, _ count: Int) -> [RecipeAvatar] {
        (0..<count).map { i in RecipeAvatar(id: "\(prefix)\(i)", art: .pixel("agent_\(prefix)\(i)"), hue: Double(i) / Double(count)) }
    }
    static let critters: [RecipeAvatar] = pixelSet("p", 16)   // robot/owl/fox/wizard/dragon/…
    static let objects: [RecipeAvatar]  = pixelSet("o", 16)   // school bus/mug/lamp/… brought to life
    static let snacks: [RecipeAvatar]   = pixelSet("s", 16)   // donut/taco/avocado/… brought to life
    static let groups: [RecipeAvatarGroup] = [
        .init(id: "glyph",   title: "Glyphs",   avatars: glyphs),
        .init(id: "critter", title: "Critters", avatars: critters),
        .init(id: "object",  title: "Objects",  avatars: objects),
        .init(id: "snack",   title: "Snacks",   avatars: snacks),
    ]
    static let all: [RecipeAvatar] = glyphs + critters + objects + snacks

    static func avatar(_ id: String) -> RecipeAvatar { all.first { $0.id == id } ?? glyphs[0] }
    static func symbol(_ id: String) -> String { if case .symbol(let s) = avatar(id).art { return s }; return "sparkles" }
    static func color(_ id: String) -> Color { Color(hue: avatar(id).hue, saturation: 0.66, brightness: 0.95) }
    static func deep(_ id: String) -> Color { Color(hue: avatar(id).hue, saturation: 0.74, brightness: 0.55) }
}

// One avatar badge — a premium gradient tile carrying either an SF symbol or a pixel-art sprite. Reused on
// the chip, the gallery, the builder preview, and the cards.
struct RecipeAvatarView: View {
    let avatarId: String
    var size: CGFloat = 64
    var selected: Bool = false
    var body: some View {
        let av = RecipeAvatars.avatar(avatarId)
        let c = RecipeAvatars.color(avatarId), d = RecipeAvatars.deep(avatarId)
        ZStack {
            if selected {
                RoundedRectangle(cornerRadius: size * 0.32, style: .continuous)
                    .fill(c.opacity(0.35)).blur(radius: size * 0.18).scaleEffect(1.16)
            }
            RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                .fill(LinearGradient(colors: [c, d, Color(hex: 0x14121C)], startPoint: .topLeading, endPoint: .bottomTrailing))
                .overlay(
                    RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                        .fill(RadialGradient(colors: [.white.opacity(0.30), .clear], center: .init(x: 0.3, y: 0.22), startRadius: 1, endRadius: size * 0.55))
                )
                .overlay(RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                    .strokeBorder(.white.opacity(selected ? 0.9 : 0.18), lineWidth: selected ? 2 : 1))
                .shadow(color: d.opacity(0.6), radius: size * 0.12, y: size * 0.06)
            switch av.art {
            case .symbol(let s):
                Image(systemName: s).font(.system(size: size * 0.42, weight: .bold)).foregroundStyle(.white)
                    .shadow(color: .black.opacity(0.4), radius: 2, y: 1)
            case .pixel(let asset):
                DeskSprite(name: asset, size: size * 0.92)
                    .shadow(color: .black.opacity(0.45), radius: 2, y: 1)
            }
        }
        .frame(width: size, height: size)
    }
}

// MARK: - the primitive (every desk concept is one declaration)

struct RecipePrimitive: DeskPrimitive {
    let rec: RecipeRecord
    var id: String { "recipe:\(rec.id)" }
    var kind: PrimitiveKind { .recipe }
    var glyph: String { RecipeAvatars.symbol(rec.avatar) }
    var isSymbol: Bool { true }
    var color: Color { RecipeAvatars.color(rec.avatar) }
    var base: CGFloat { 104 }
    var title: String { rec.name.isEmpty ? ProductLanguage.label(.persona) : rec.name }
    var subtitle: String { rec.role.isEmpty ? "your Persona" : rec.role }
    var preview: String? { rec.role.isEmpty ? "tap to ask" : rec.role }
    var sections: [PrimitiveSection] {
        var out: [PrimitiveSection] = []
        out.append(.init(label: "ROLE", tint: RecipeAvatars.color(rec.avatar),
                         body: .text(rec.systemPrompt.isEmpty ? "A general assistant." : rec.systemPrompt)))
        var ctx: [String] = []
        if !rec.manualContext.isEmpty { ctx.append("Pinned notes") }
        if rec.useZoneContext { ctx.append("This zone's meetings") }
        if !rec.kb.isEmpty { ctx.append("Knowledge · \(rec.kb)") }
        if !ctx.isEmpty { out.append(.init(label: "CONTEXT", tint: DioPal.muted, body: .chips(ctx))) }
        out.append(.init(label: "CAPABILITY", tint: DioPal.mint, body: .chips([
            "Ask \(rec.name.isEmpty ? "Persona" : rec.name)", "Input · text or Desk object",
            "Runs on · selected target", "Effect · creates Artifact", "Ready",
        ])))
        return out
    }
    var accepts: [PrimitiveKind] { [.meeting, .summary, .actions, .topics, .transcript, .artifact, .note] }
    var emits: [PrimitiveKind] { [.artifact] }
}

// MARK: - starter presets (one tap to a working recipe — the "fun + easy" on-ramp)

struct RecipePreset { let name: String; let role: String; let avatar: String; let system: String; let template: String }
enum RecipePresets {
    static let all: [RecipePreset] = [
        .init(name: "Scout", role: "digs for the facts", avatar: "a21",
              system: "You are a sharp researcher. Pull out the concrete facts, names, numbers and open questions. Be precise; never invent details.",
              template: "{input}"),
        .init(name: "Editor", role: "tightens your words", avatar: "a27",
              system: "You are a ruthless editor. Make the text clearer and tighter without changing its meaning. Prefer plain words and short sentences.",
              template: "Edit this:\n{input}"),
        .init(name: "Critic", role: "finds the holes", avatar: "a22",
              system: "You are a constructive critic. Surface the weakest assumptions, risks, and gaps. Be specific and fair; suggest a fix for each.",
              template: "{input}"),
        .init(name: "Coach", role: "keeps you moving", avatar: "a5",
              system: "You are an encouraging coach. Turn the input into one clear next step and a short, motivating nudge. Keep it warm and brief.",
              template: "{input}"),
        .init(name: "Planner", role: "turns talk into a plan", avatar: "a24",
              system: "You are a pragmatic planner. Produce a short, ordered plan with owners and rough timing where implied. No fluff.",
              template: "Make a plan from this:\n{input}"),
        .init(name: "Muse", role: "sparks new ideas", avatar: "a20",
              system: "You are an imaginative brainstorm partner. Offer several distinct, bold ideas. Range wide; one line each.",
              template: "{input}"),
    ]
}

// MARK: - personality traits (tap to stack a behaviour clause — no blank-page prompt writing)

struct RecipeTrait { let label: String; let icon: String; let clause: String }
enum RecipeTraits {
    static let all: [RecipeTrait] = [
        .init(label: "Concise", icon: "scissors", clause: "Keep answers short and to the point."),
        .init(label: "Warm", icon: "heart.fill", clause: "Be warm and encouraging."),
        .init(label: "Skeptical", icon: "exclamationmark.triangle.fill", clause: "Question assumptions and call out risks."),
        .init(label: "Creative", icon: "sparkles", clause: "Offer bold, imaginative ideas."),
        .init(label: "Formal", icon: "briefcase.fill", clause: "Use a professional, formal tone."),
        .init(label: "Playful", icon: "face.smiling.inverse", clause: "Keep a light, playful tone."),
        .init(label: "Thorough", icon: "list.bullet.rectangle.fill", clause: "Be thorough and cover the edge cases."),
        .init(label: "Step-by-step", icon: "arrow.down.right.circle.fill", clause: "Explain your reasoning step by step."),
        .init(label: "Witty", icon: "theatermasks.fill", clause: "Add a touch of wit."),
        .init(label: "Action-first", icon: "bolt.fill", clause: "Lead with the next concrete action."),
    ]
}

// MARK: - the desk roster rail (your characters, always to hand on the right edge)

struct DioRecipeRail: View {
    let recipes: [RecipeRecord]; let chains: [ChainRecord]; let dimmed: Bool
    let onOpen: (RecipeRecord) -> Void; let onCreate: () -> Void
    let onRunChain: (ChainRecord) -> Void; let onCreateChain: () -> Void
    let onPlay: (String) -> Void   // launch a game by id ("arkanoid" or a MiniGames id)
    let onPlace: (String) -> Void  // place a game on the desk as a primitive (long-press)
    @State private var tab = 0   // 0 = recipes · 1 = chains · 2 = play
    var body: some View {
        VStack(spacing: 11) {
            // tiny tabs — Recipes / Chains / Play
            HStack(spacing: 4) {
                ForEach(Array([ProductLanguage.label(.persona, plural: true), ProductLanguage.label(.sequence, plural: true), "Play"].enumerated()), id: \.offset) { i, t in
                    Button { withAnimation(.spring(response: 0.3, dampingFraction: 0.82)) { tab = i }; haptic() } label: {
                        Text(t).font(.system(size: 8.5, weight: .black, design: .rounded)).tracking(0.6)
                            .foregroundStyle(tab == i ? .white : DioPal.muted.opacity(0.8))
                            .padding(.horizontal, 8).frame(height: 22)
                            .background(Capsule().fill(tab == i ? DioPal.accent.opacity(0.8) : .white.opacity(0.05)))
                    }.buttonStyle(.plain)
                }
            }
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 13) {
                    if tab == 0 {
                        ForEach(recipes) { a in Button { onOpen(a) } label: { DioRecipeChip(recipe: a) }.buttonStyle(.plain) }
                        plusTile(onCreate)
                    } else if tab == 1 {
                        ForEach(chains) { c in Button { onRunChain(c) } label: { DioChainChip(chain: c, recipes: recipes) }.buttonStyle(.plain) }
                        plusTile(onCreateChain)
                        if chains.isEmpty {
                            Text("Build a\nSequence").font(.system(size: 9, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).multilineTextAlignment(.center)
                        }
                    } else {
                        // PLAY — every game lives here (tap to play, long-press to place on the desk)
                        Button { onPlay("arkanoid"); haptic() } label: { DioGameChip(id: "arkanoid", title: "Arkanoid", icon: "gamecontroller.fill") }.buttonStyle(.plain)
                            .contextMenu { Button { onPlace("arkanoid") } label: { Label("Add to desk", systemImage: "plus.rectangle.on.rectangle") } }
                        ForEach(MiniGames.all) { g in
                            Button { onPlay(g.id); haptic() } label: { DioGameChip(id: g.id, title: g.title, icon: g.icon) }.buttonStyle(.plain)
                                .contextMenu { Button { onPlace(g.id) } label: { Label("Add to desk", systemImage: "plus.rectangle.on.rectangle") } }
                        }
                        Text("Long-press a game\nto add it to the desk")
                            .font(.system(size: 8.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.7))
                            .multilineTextAlignment(.center).padding(.top, 2)
                    }
                }
                .padding(.vertical, 4)
            }
            .frame(maxHeight: 388)
        }
        .padding(.vertical, 12).padding(.horizontal, 9)
        .background(RoundedRectangle(cornerRadius: 22, style: .continuous)
            .fill(.black.opacity(0.32)).overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
        .opacity(dimmed ? 0 : 1).allowsHitTesting(!dimmed)
        #if targetEnvironment(simulator)
        .onAppear { if let t = ProcessInfo.processInfo.environment["HS_DESK_RAILTAB"], let i = Int(t) { tab = i } }
        #endif
    }
    private func plusTile(_ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            ZStack {
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .strokeBorder(style: StrokeStyle(lineWidth: 1.6, dash: [5, 4]))
                    .foregroundStyle(DioPal.muted.opacity(0.55)).frame(width: 54, height: 54)
                Image(systemName: "plus").font(.system(size: 20, weight: .black)).foregroundStyle(DioPal.muted)
            }
        }.buttonStyle(.plain)
    }
    private func haptic() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        #endif
    }
}

struct DioRecipeChip: View {
    let recipe: RecipeRecord
    var body: some View {
        VStack(spacing: 4) {
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                let bob = CGFloat(sin(t * 1.1 + Double(abs(recipe.id.hashValue % 7))) * 2)
                RecipeAvatarView(avatarId: recipe.avatar, size: 54).offset(y: -bob)
            }
            Text(recipe.name.isEmpty ? ProductLanguage.label(.persona) : recipe.name)
                .font(.system(size: 9.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9))
                .lineLimit(1).frame(width: 60)
        }
    }
}

// a game entry in the rail's Play column — its PixelLab cover on a soft tile + the title
struct DioGameChip: View {
    let id: String; let title: String; let icon: String
    var body: some View {
        VStack(spacing: 4) {
            ZStack {
                RoundedRectangle(cornerRadius: 15, style: .continuous)
                    .fill(LinearGradient(colors: [DioPal.violet.opacity(0.32), Color(hex: 0x14121C)], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 1))
                GameCover(id: id, fallback: icon, size: 42)
            }.frame(width: 54, height: 54)
            Text(title).font(.system(size: 9.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9)).lineLimit(1).frame(width: 60)
        }
    }
}

// MARK: - the builder (create / edit) — engaging, sectioned, with a live preview

// MARK: - the in-world panel (HSM-17-08, the first-class Recipe experience)

/// The Recipe surfaces' presentation: the desk STAYS VISIBLE and alive behind a
/// right-docked panel over a transparent tap-away catcher — never a dimming
/// scrim (the no-modals law). Depth comes from shadow and hairline, not darkness.
struct DioAtelierPanel<Content: View>: View {
    var maxW: CGFloat = 600
    var maxH: CGFloat? = nil
    var dismissable: Bool = true
    var dismiss: () -> Void
    @ViewBuilder var content: () -> Content
    var body: some View {
        ZStack {
            Color.clear.contentShape(Rectangle()).ignoresSafeArea()
                .onTapGesture { if dismissable { dismiss() } }
            content()
                .frame(maxWidth: maxW, maxHeight: maxH)
                .background(
                    RoundedRectangle(cornerRadius: 30, style: .continuous).fill(Color(hex: 0x14121B).opacity(0.98))
                        .overlay(RoundedRectangle(cornerRadius: 30, style: .continuous)
                            .strokeBorder(LinearGradient(colors: [.white.opacity(0.16), .white.opacity(0.05)],
                                                         startPoint: .top, endPoint: .bottom), lineWidth: 1))
                        .shadow(color: .black.opacity(0.55), radius: 34, x: -10, y: 14)
                )
                .padding(.vertical, 28).padding(.trailing, 16).padding(.leading, 12)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                .transition(.move(edge: .trailing).combined(with: .opacity))
        }
    }
}

struct DioRecipeBuilder: View {
    @State var draft: RecipeRecord
    let knowledgeBases: [String]
    let onSave: (RecipeRecord) -> Void
    let onCancel: () -> Void
    var isNew: Bool
    var contextLimit: Int = 16_384         // the chosen runtime's usable context (on-device budget)
    var zoneTokens: Int = 0                // est. tokens the current zone's meetings would add

    /// Tokens the grounding context costs at rest — exactly what `recipeRoleAndContext` assembles:
    /// the role (system prompt) + the notes + the zone's meetings (the KB injects only a hint today).
    private var groundingTokens: Int {
        OnDeviceBudget.estimateTokens(draft.systemPrompt)
        + OnDeviceBudget.estimateTokens(draft.manualContext)
        + (draft.useZoneContext ? zoneTokens : 0)
        + (draft.kb.isEmpty ? 0 : 12)
    }
    @State private var avatarGroup = 0
    @State private var showAdvanced = false
    @State private var showRawPrompt = false
    @State private var showFaces = false
    @State private var step = 0          // 0 = what it does · 1 = name & face
    @State private var pop = false

    private let cols = Array(repeating: GridItem(.flexible(), spacing: 12), count: 6)
    private let traitCols = [GridItem(.adaptive(minimum: 118), spacing: 8)]
    private var tint: Color { RecipeAvatars.color(draft.avatar) }

    var body: some View {
        DioAtelierPanel(maxW: 600, dismiss: onCancel) {
            VStack(spacing: 0) {
                header
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 22) {
                        if step == 0 { step1Behavior } else { step2Identity }
                    }
                    .padding(.horizontal, 22).padding(.top, 4).padding(.bottom, 18)
                    .transition(.opacity)
                }
                bottomBar
            }
        }
        .onAppear { avatarGroup = RecipeAvatars.groups.firstIndex { $0.avatars.contains { $0.id == draft.avatar } } ?? 0 }
        .onChange(of: draft.avatar) { _ in pop = true; DispatchQueue.main.asyncAfter(deadline: .now() + 0.18) { pop = false } }
    }

    private func advance() { withAnimation(.spring(response: 0.4, dampingFraction: 0.86)) { step = 1 } }

    // A light step-aware header — the title tells you where you are; close lives here.
    private var header: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 3) {
                Text("STEP \(step + 1) OF 2").font(.system(size: 11, weight: .black, design: .rounded)).tracking(1).foregroundStyle(tint)
                Text(step == 0 ? "What should it do?" : "Name & face").font(.system(size: 22, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
            }
            Spacer(minLength: 0)
            Button { onCancel() } label: { Image(systemName: "xmark.circle.fill").font(.system(size: 26)).foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
        }
        .padding(.horizontal, 22).padding(.top, 18).padding(.bottom, 12)
    }

    // STEP 1 — what it does: describe it, or tap a recipe (which jumps straight to naming).
    private var step1Behavior: some View {
        VStack(alignment: .leading, spacing: 22) {
            section("DESCRIBE IT, IN YOUR WORDS") {
                editor($draft.systemPrompt, placeholder: "e.g. a sharp researcher who pulls out the facts, names and open questions…", minH: 92)
            }
            section("OR START FROM A RECIPE") {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 150), spacing: 10)], spacing: 10) {
                    ForEach(RecipePresets.all, id: \.name) { p in
                        Button { applyPreset(p); advance() } label: { recipeCard(p) }.buttonStyle(.plain)
                    }
                }
            }
        }
    }

    private func recipeCard(_ p: RecipePreset) -> some View {
        HStack(spacing: 10) {
            RecipeAvatarView(avatarId: p.avatar, size: 38)
            VStack(alignment: .leading, spacing: 1) {
                Text(p.name).font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                Text(p.role).font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(2).multilineTextAlignment(.leading)
            }
            Spacer(minLength: 0)
        }
        .padding(11).frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.05))
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
    }

    // The model this recipe runs on (per-recipe override of the active default). Empty = the active
    // profile. The gauge below reads THIS profile's window — Scout on Claude vs a local 3B differ.
    private var runsOnSection: some View {
        section("RUNS ON") {
            RunsOnPicker(selectedId: $draft.profileId, allowsDefault: true, label: "Model")
        }
    }

    /// The context window the gauge measures against: the recipe's chosen profile's limit, or — when it
    /// uses the active default — the accurate RAM-aware budget the host passed in.
    private var effectiveLimit: Int {
        let cfg = InferenceConfigStore.shared
        let p = cfg.resolveProfile(recipeProfileId: draft.profileId.isEmpty ? nil : draft.profileId)
        return p.id == cfg.activeProfile.id ? contextLimit : p.contextLimit
    }

    // STEP 2 — make it yours: the hero, name + vibe, where it runs, grounding, personality, face.
    private var step2Identity: some View {
        VStack(alignment: .leading, spacing: 22) {
            heroRow
            section("NAME") { field("Name", text: $draft.name, placeholder: "e.g. Scout") }
            section("VIBE · ONE LINE") { field("Vibe", text: $draft.role, placeholder: "e.g. digs for the facts") }
            runsOnSection
            knowsSection
            personality
            faceCollapsible
            advanced
        }
    }

    // GROUNDING CONTEXT — first-class, not buried: point it at a knowledge base, pin facts it
    // always carries, and optionally feed it the zone's meetings.
    private var knowsSection: some View {
        section("GROUNDING CONTEXT") {
            Text("Knowledge your Persona always uses.").font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            ContextGauge(used: groundingTokens, limit: effectiveLimit)
                .padding(11)
                .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(.white.opacity(0.04)).overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(.white.opacity(0.07), lineWidth: 1)))
            Text("KNOWLEDGE BASE").font(.system(size: 9.5, weight: .black, design: .rounded)).tracking(1).foregroundStyle(DioPal.muted.opacity(0.8)).padding(.top, 2)
            if knowledgeBases.isEmpty {
                Text("Create Knowledge on the Desk, then connect this Persona to it.")
                    .font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.8))
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        kbChip("None", icon: "nosign", on: draft.kb.isEmpty) { draft.kb = "" }
                        ForEach(knowledgeBases, id: \.self) { k in
                            kbChip(k, icon: "diamond.fill", on: draft.kb == k) { draft.kb = k }
                        }
                    }.padding(.horizontal, 2)
                }
            }
            Text("NOTES").font(.system(size: 9.5, weight: .black, design: .rounded)).tracking(1).foregroundStyle(DioPal.muted.opacity(0.8)).padding(.top, 6)
            editor($draft.manualContext, placeholder: "Facts it should always have on hand — names, preferences, project context…", minH: 64)
            Toggle(isOn: $draft.useZoneContext) {
                Text("Read this zone's meetings").font(.system(size: 13.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            }.tint(tint).padding(.top, 2)
        }
    }

    private func kbChip(_ label: String, icon: String, on: Bool, _ tap: @escaping () -> Void) -> some View {
        Button { haptic(); tap() } label: {
            HStack(spacing: 6) {
                Image(systemName: icon).font(.system(size: 10, weight: .bold))
                Text(label).font(.system(size: 12.5, weight: .heavy, design: .rounded)).lineLimit(1)
                if on { Image(systemName: "checkmark").font(.system(size: 9, weight: .black)) }
            }
            .foregroundStyle(on ? .white : DioPal.text.opacity(0.85))
            .padding(.horizontal, 12).frame(height: 34)
            .background(Capsule().fill(on ? tint.opacity(0.85) : .white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(on ? 0 : 0.1), lineWidth: 1)))
        }.buttonStyle(.plain)
    }

    // the playful hero — a big bobbing avatar that pops when you change it, with a dice to reroll
    private var heroRow: some View {
        HStack(spacing: 14) {
            TimelineView(.animation) { tl in
                let bob = CGFloat(sin(tl.date.timeIntervalSinceReferenceDate * 1.4) * 3)
                RecipeAvatarView(avatarId: draft.avatar, size: 64).offset(y: -bob)
                    .scaleEffect(pop ? 1.18 : 1).animation(.spring(response: 0.3, dampingFraction: 0.5), value: pop)
            }
            .frame(width: 70, height: 70)
            VStack(alignment: .leading, spacing: 2) {
                Text(draft.name.isEmpty ? "Unnamed" : draft.name).font(.system(size: 20, weight: .black, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                Text(draft.role.isEmpty ? "give it a vibe" : draft.role).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
            }
            Spacer(minLength: 0)
            Button { surprise() } label: {
                Image(systemName: "dice.fill").font(.system(size: 16, weight: .bold)).foregroundStyle(.white)
                    .frame(width: 38, height: 38).background(Circle().fill(tint.opacity(0.85)))
            }.buttonStyle(.plain)
        }
    }

    // the face picker, collapsed by default (100 faces shouldn't dominate the screen)
    private var faceCollapsible: some View {
        section("FACE") {
            Button { withAnimation(.spring(response: 0.35, dampingFraction: 0.85)) { showFaces.toggle() } } label: {
                HStack(spacing: 11) {
                    RecipeAvatarView(avatarId: draft.avatar, size: 40)
                    Text(showFaces ? "Hide faces" : "Change face").font(.system(size: 13.5, weight: .heavy, design: .rounded)).foregroundStyle(tint)
                    Spacer(minLength: 0)
                    Image(systemName: showFaces ? "chevron.up" : "chevron.down").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.muted)
                }
                .padding(.horizontal, 13).frame(height: 56)
                .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(.white.opacity(0.05)).overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
            }.buttonStyle(.plain)
            if showFaces {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(Array(RecipeAvatars.groups.enumerated()), id: \.element.id) { i, g in
                            Button { withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) { avatarGroup = i }; haptic() } label: {
                                Text("\(g.title) · \(g.avatars.count)")
                                    .font(.system(size: 12.5, weight: .heavy, design: .rounded))
                                    .foregroundStyle(avatarGroup == i ? .white : DioPal.muted)
                                    .padding(.horizontal, 14).frame(height: 34)
                                    .background(Capsule().fill(avatarGroup == i ? tint.opacity(0.85) : .white.opacity(0.06)))
                            }.buttonStyle(.plain)
                        }
                    }.padding(.horizontal, 2)
                }
                LazyVGrid(columns: cols, spacing: 12) {
                    ForEach(RecipeAvatars.groups[avatarGroup].avatars) { av in
                        Button { draft.avatar = av.id; haptic() } label: {
                            RecipeAvatarView(avatarId: av.id, size: 44, selected: draft.avatar == av.id)
                        }.buttonStyle(.plain)
                    }
                }
            }
        }
    }

    // PERSONALITY — tap trait chips to stack behaviour clauses; raw prompt is an optional fine-tune
    private var personality: some View {
        section("GIVE THEM A PERSONALITY") {
            LazyVGrid(columns: traitCols, spacing: 8) {
                ForEach(RecipeTraits.all, id: \.label) { t in
                    let on = hasTrait(t)
                    Button { toggleTrait(t) } label: {
                        HStack(spacing: 6) {
                            Image(systemName: t.icon).font(.system(size: 11, weight: .bold))
                            Text(t.label).font(.system(size: 12.5, weight: .heavy, design: .rounded)); Spacer(minLength: 0)
                            if on { Image(systemName: "checkmark").font(.system(size: 10, weight: .black)) }
                        }
                        .foregroundStyle(on ? .white : DioPal.text.opacity(0.85))
                        .padding(.horizontal, 12).frame(height: 38)
                        .background(Capsule().fill(on ? tint.opacity(0.85) : .white.opacity(0.06))
                            .overlay(Capsule().strokeBorder(.white.opacity(on ? 0 : 0.1), lineWidth: 1)))
                    }.buttonStyle(.plain)
                }
            }
            Button { withAnimation { showRawPrompt.toggle() } } label: {
                HStack(spacing: 6) {
                    Image(systemName: showRawPrompt ? "chevron.down" : "chevron.right").font(.system(size: 10, weight: .black))
                    Text(showRawPrompt ? "Hide the raw instructions" : "Fine-tune in your own words").font(.system(size: 11.5, weight: .heavy, design: .rounded))
                }.foregroundStyle(DioPal.muted)
            }.buttonStyle(.plain)
            if showRawPrompt {
                editor($draft.systemPrompt, placeholder: "You are a sharp researcher who…", minH: 88)
            } else if !draft.systemPrompt.isEmpty {
                Text(draft.systemPrompt).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                    .padding(.horizontal, 13).padding(.vertical, 10).frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(.white.opacity(0.04)))
            }
        }
    }

    // ADVANCED — folded away so the default path stays short
    private var advanced: some View {
        VStack(alignment: .leading, spacing: 14) {
            Button { withAnimation { showAdvanced.toggle() } } label: {
                HStack(spacing: 7) {
                    Image(systemName: showAdvanced ? "chevron.down" : "chevron.right").font(.system(size: 11, weight: .black))
                    Text("ADVANCED").font(.system(size: 10.5, weight: .black, design: .rounded)).tracking(1.2)
                    Text("prompt template").font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.7))
                    Spacer(minLength: 0)
                }.foregroundStyle(DioPal.muted)
            }.buttonStyle(.plain)
            if showAdvanced {
                Text("WHAT TO ASK").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1).foregroundStyle(DioPal.muted)
                editor($draft.userTemplate, placeholder: "{input}", minH: 52)
                Text("Use {input} for your question.")
                    .font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            }
        }
    }

    private var bottomBar: some View {
        HStack(spacing: 12) {
            if step == 0 {
                Button { onCancel() } label: { mutedCap("Cancel") }.buttonStyle(.plain)
                Button { advance() } label: {
                    HStack(spacing: 7) { Text("Next").font(.system(size: 15.5, weight: .heavy, design: .rounded)); Image(systemName: "arrow.right") }
                        .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 50)
                        .background(Capsule().fill(LinearGradient(colors: [tint, RecipeAvatars.deep(draft.avatar)], startPoint: .top, endPoint: .bottom)))
                }.buttonStyle(.plain)
            } else {
                Button { withAnimation(.spring(response: 0.4, dampingFraction: 0.86)) { step = 0 } } label: {
                    HStack(spacing: 6) { Image(systemName: "arrow.left"); Text("Back").font(.system(size: 15, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 50).background(Capsule().fill(.white.opacity(0.06)))
                }.buttonStyle(.plain)
                Button { save() } label: {
                    HStack(spacing: 7) {
                        Image(systemName: isNew ? "sparkles" : "checkmark")
                        Text(isNew ? "Bring to life" : "Save").font(.system(size: 15.5, weight: .heavy, design: .rounded))
                    }
                    .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 50)
                    .background(Capsule().fill(LinearGradient(colors: [tint, RecipeAvatars.deep(draft.avatar)], startPoint: .top, endPoint: .bottom)))
                    .opacity(canSave ? 1 : 0.45)
                }.buttonStyle(.plain).disabled(!canSave)
            }
        }
        .padding(.horizontal, 22).padding(.vertical, 16)
    }

    private func mutedCap(_ t: String) -> some View {
        Text(t).font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
            .frame(maxWidth: .infinity).frame(height: 50).background(Capsule().fill(.white.opacity(0.06)))
    }

    private var canSave: Bool { !draft.name.trimmingCharacters(in: .whitespaces).isEmpty }
    private func save() { guard canSave else { return }; haptic(.medium); onSave(draft) }
    private func applyPreset(_ p: RecipePreset) {
        haptic()
        if draft.name.trimmingCharacters(in: .whitespaces).isEmpty { draft.name = p.name }
        withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
            draft.role = p.role; draft.avatar = p.avatar; draft.systemPrompt = p.system; draft.userTemplate = p.template
            avatarGroup = RecipeAvatars.groups.firstIndex { $0.avatars.contains { $0.id == p.avatar } } ?? avatarGroup
        }
    }
    private func surprise() {
        haptic(.medium)
        let p = RecipePresets.all.randomElement()!
        let face = RecipeAvatars.all.randomElement()!
        withAnimation(.spring(response: 0.4, dampingFraction: 0.65)) {
            draft.avatar = face.id
            if draft.name.trimmingCharacters(in: .whitespaces).isEmpty { draft.name = p.name }
            draft.role = p.role; draft.systemPrompt = p.system
            avatarGroup = RecipeAvatars.groups.firstIndex { $0.avatars.contains { $0.id == face.id } } ?? avatarGroup
        }
    }
    private func hasTrait(_ t: RecipeTrait) -> Bool { draft.systemPrompt.contains(t.clause) }
    private func toggleTrait(_ t: RecipeTrait) {
        haptic()
        var s = draft.systemPrompt
        if let r = s.range(of: t.clause) {
            s.removeSubrange(r)
        } else {
            s = s.isEmpty ? t.clause : s + " " + t.clause
        }
        draft.systemPrompt = s.replacingOccurrences(of: "  ", with: " ").trimmingCharacters(in: .whitespacesAndNewlines)
    }

    @ViewBuilder private func section<C: View>(_ title: String, @ViewBuilder _ content: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title).font(.system(size: 10.5, weight: .black, design: .rounded)).tracking(1.2).foregroundStyle(DioPal.muted)
            content()
        }
    }
    @ViewBuilder private func field(_ label: String, text: Binding<String>, placeholder: String) -> some View {
        HStack(spacing: 8) {
            TextField("", text: text, prompt: Text(placeholder).foregroundColor(DioPal.muted.opacity(0.7)))
                .font(.system(size: 15, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text)
            VoiceFillMic(text: text, tint: DioPal.mint, size: 26)
        }
        .padding(.horizontal, 14).frame(height: 46)
        .background(RoundedRectangle(cornerRadius: 13, style: .continuous).fill(.white.opacity(0.05)).overlay(RoundedRectangle(cornerRadius: 13, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
    }
    @ViewBuilder private func editor(_ text: Binding<String>, placeholder: String, minH: CGFloat) -> some View {
        ZStack(alignment: .topLeading) {
            if text.wrappedValue.isEmpty {
                Text(placeholder).font(.system(size: 14, weight: .regular, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.6))
                    .padding(.horizontal, 16).padding(.top, 14).allowsHitTesting(false)
            }
            TextEditor(text: text)
                .font(.system(size: 14, weight: .regular, design: .rounded)).foregroundStyle(DioPal.text)
                .scrollContentBackground(.hidden).padding(.horizontal, 11).padding(.vertical, 7).frame(minHeight: minH)
        }
        .background(RoundedRectangle(cornerRadius: 13, style: .continuous).fill(.white.opacity(0.05)).overlay(RoundedRectangle(cornerRadius: 13, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
        .overlay(alignment: .bottomTrailing) { VoiceFillMic(text: text, tint: DioPal.mint, size: 28).padding(9) }
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// A ring gauge: how much of the recipe's context its grounding eats before you even ask. Green under
// 60%, amber to 85%, red past it — a live "this knowledge base alone fills it" signal.
struct ContextGauge: View {
    let used: Int
    let limit: Int
    private var frac: Double { limit <= 0 ? 0 : min(1, Double(used) / Double(limit)) }
    private var color: Color { frac < 0.6 ? DioPal.mint : (frac < 0.85 ? Color(hex: 0xF5A623) : Color(hex: 0xFF6B6B)) }
    private func fmt(_ n: Int) -> String { n >= 1000 ? String(format: "%.1fk", Double(n) / 1000) : "\(n)" }
    var body: some View {
        HStack(spacing: 13) {
            ZStack {
                Circle().stroke(.white.opacity(0.08), lineWidth: 6)
                Circle().trim(from: 0, to: frac).stroke(color, style: StrokeStyle(lineWidth: 6, lineCap: .round))
                    .rotationEffect(.degrees(-90)).animation(.easeOut(duration: 0.3), value: frac)
                Text("\(Int(frac * 100))%").font(.system(size: 12.5, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
            }
            .frame(width: 48, height: 48)
            VStack(alignment: .leading, spacing: 1) {
                Text("\(fmt(used)) / \(fmt(limit)) tokens").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                Text("filled before you ask a thing").font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(color)
            }
            Spacer(minLength: 0)
        }
    }
}

// MARK: - the recipe's home — a LIVING CONVERSATION (multi-turn; the avatar emotes; harvest replies to the desk)

struct DioRecipeChat: View {
    let recipe: RecipeRecord
    @State var messages: [RecipeMessage]
    var grounding = GroundingSelection()           // HSM-15-12 — this conversation's records
    var onEditGrounding: () -> Void = {}
    var isTransient = false                        // HSM-15-13 — a model chat has no recipe to edit/delete
    let onInfer: (_ history: [RecipeMessage], _ question: String) async -> String   // assembles + calls the LLM
    let onChange: ([RecipeMessage]) -> Void        // persist the thread
    let onSaveCard: (String) -> Void              // harvest a reply onto the desk
    let onEdit: () -> Void
    let onDelete: () -> Void
    let onClose: () -> Void

    @State private var input = ""
    @State private var thinking = false
    @FocusState private var focused: Bool
    private var tint: Color { RecipeAvatars.color(recipe.avatar) }

    var body: some View {
        DioAtelierPanel(maxW: 560, maxH: 760, dismissable: !thinking, dismiss: onClose) {
            VStack(spacing: 0) {
                header
                Rectangle().fill(.white.opacity(0.06)).frame(height: 1)
                transcript
                inputBar
            }
        }
    }

    private var header: some View {
        HStack(spacing: 13) {
            ZStack {
                if thinking {
                    TimelineView(.animation) { tl in
                        let r = 0.5 + 0.5 * sin(tl.date.timeIntervalSinceReferenceDate * 5)
                        Circle().strokeBorder(tint.opacity(0.7), lineWidth: 2).frame(width: 58 + 10 * r, height: 58 + 10 * r)
                    }
                }
                RecipeAvatarView(avatarId: recipe.avatar, size: 50)
            }
            VStack(alignment: .leading, spacing: 1) {
                Text(recipe.name).font(.system(size: 18, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                Text(thinking ? "thinking…" : (recipe.role.isEmpty ? "your Persona" : recipe.role))
                    .font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(thinking ? tint : DioPal.muted)
            }
            Spacer(minLength: 0)
            Menu {
                if !isTransient { Button { onEdit() } label: { Label("Edit Persona", systemImage: "slider.horizontal.3") } }
                if !messages.isEmpty { Button { clearChat() } label: { Label("Clear chat", systemImage: "eraser") } }
                if !isTransient { Button(role: .destructive) { onDelete() } label: { Label("Delete Persona", systemImage: "trash") } }
            } label: { Image(systemName: "ellipsis.circle.fill").font(.system(size: 23)).foregroundStyle(DioPal.muted) }
            Button { onClose() } label: { Image(systemName: "xmark.circle.fill").font(.system(size: 23)).foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
        }
        .padding(.horizontal, 18).padding(.vertical, 14)
    }

    private var transcript: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    if messages.isEmpty && !thinking { emptyState }
                    ForEach(messages) { m in bubble(m).id(m.id) }
                    if thinking { thinkingBubble.id("thinking") }
                }
                .padding(.horizontal, 16).padding(.vertical, 16)
            }
            .onChange(of: messages.count) { _ in withAnimation { proxy.scrollTo(messages.last?.id ?? "thinking", anchor: .bottom) } }
            .onChange(of: thinking) { _ in if thinking { withAnimation { proxy.scrollTo("thinking", anchor: .bottom) } } }
        }
        .frame(maxHeight: .infinity)
    }

    private var emptyState: some View {
        VStack(spacing: 11) {
            RecipeAvatarView(avatarId: recipe.avatar, size: 66)
            Text("Say hi to \(recipe.name)").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            if hasContext {
                HStack(spacing: 7) {
                    if recipe.useZoneContext { tag("This zone", "tray.full.fill") }
                    if !recipe.kb.isEmpty { tag(recipe.kb, "crystal.fill") }
                    if !recipe.manualContext.isEmpty { tag("Pinned notes", "note.text") }
                    if !grounding.isEmpty { tag(grounding.summaryLabel, "square.stack.3d.up.fill") }
                }
            }
            Text("Long-press a desk card to use \(recipe.name).")
                .font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.8)).multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity).padding(.top, 28)
    }

    private func bubble(_ m: RecipeMessage) -> some View {
        HStack(alignment: .bottom, spacing: 8) {
            if m.isYou { Spacer(minLength: 44) } else { RecipeAvatarView(avatarId: recipe.avatar, size: 26) }
            VStack(alignment: m.isYou ? .trailing : .leading, spacing: 5) {
                Text(m.text)
                    .font(.system(size: 14, weight: .medium, design: .rounded))
                    .foregroundStyle(m.isYou ? .white : (m.isError ? Color(hex: 0xFFB4A0) : DioPal.text))
                    .padding(.horizontal, 13).padding(.vertical, 10)
                    .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(
                        m.isYou ? AnyShapeStyle(LinearGradient(colors: [tint, RecipeAvatars.deep(recipe.avatar)], startPoint: .top, endPoint: .bottom))
                                : AnyShapeStyle(Color.white.opacity(0.06))))
                if !m.isYou && !m.isError {
                    Button { onSaveCard(m.text) } label: {
                        HStack(spacing: 4) { Image(systemName: "tray.and.arrow.down.fill").font(.system(size: 9, weight: .bold)); Text("Save to desk").font(.system(size: 10, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(DioPal.muted)
                    }.buttonStyle(.plain)
                }
            }
            if !m.isYou { Spacer(minLength: 44) }
        }
    }

    private var thinkingBubble: some View {
        HStack(alignment: .bottom, spacing: 8) {
            RecipeAvatarView(avatarId: recipe.avatar, size: 26)
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                HStack(spacing: 5) {
                    ForEach(0..<3) { i in Circle().fill(tint.opacity(0.35 + 0.55 * (0.5 + 0.5 * sin(t * 4 + Double(i) * 0.7)))).frame(width: 7, height: 7) }
                }
                .padding(.horizontal, 14).padding(.vertical, 12)
                .background(RoundedRectangle(cornerRadius: 16).fill(.white.opacity(0.06)))
            }
            Spacer(minLength: 44)
        }
    }

    private var inputBar: some View {
        VStack(spacing: 8) {
            if !grounding.isEmpty {
                Button { onEditGrounding() } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "square.stack.3d.up.fill").font(.system(size: 10, weight: .bold))
                        Text("Grounded on \(grounding.summaryLabel)")
                            .font(.system(size: 11, weight: .heavy, design: .rounded)).lineLimit(1)
                        Image(systemName: "chevron.right").font(.system(size: 8, weight: .black)).opacity(0.7)
                    }
                    .foregroundStyle(DioPal.cobalt)
                    .padding(.horizontal, 11).frame(height: 28)
                    .background(Capsule().fill(DioPal.cobalt.opacity(0.12))
                        .overlay(Capsule().strokeBorder(DioPal.cobalt.opacity(0.4), lineWidth: 1)))
                    .frame(maxWidth: .infinity, alignment: .leading)
                }.buttonStyle(.plain)
            }
            HStack(spacing: 10) {
            Button { onEditGrounding() } label: {
                Image(systemName: grounding.isEmpty ? "square.stack.3d.up" : "square.stack.3d.up.fill")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(grounding.isEmpty ? DioPal.muted : DioPal.cobalt)
                    .frame(width: 36, height: 36).background(Circle().fill(.white.opacity(0.06)))
            }.buttonStyle(.plain)
            TextField("", text: $input, prompt: Text("Message \(recipe.name)…").foregroundColor(DioPal.muted.opacity(0.7)), axis: .vertical)
                .lineLimit(1...4)
                .font(.system(size: 15, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text).focused($focused)
                .padding(.horizontal, 14).padding(.vertical, 10)
                .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.white.opacity(0.06)).overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
            VoiceFillMic(text: $input, tint: tint, size: 36)
            Button { send() } label: {
                Image(systemName: "arrow.up").font(.system(size: 17, weight: .black)).foregroundStyle(.white)
                    .frame(width: 44, height: 44).background(Circle().fill(canSend ? AnyShapeStyle(tint) : AnyShapeStyle(Color.white.opacity(0.1))))
            }.buttonStyle(.plain).disabled(!canSend)
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 12)
    }

    private var canSend: Bool { !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !thinking }
    private var hasContext: Bool { recipe.useZoneContext || !recipe.kb.isEmpty || !recipe.manualContext.isEmpty || !grounding.isEmpty }
    private func clearChat() { haptic(); messages = []; onChange(messages) }
    private func send() {
        let q = input.trimmingCharacters(in: .whitespacesAndNewlines); guard !q.isEmpty, !thinking else { return }
        haptic()
        let history = messages
        messages.append(RecipeMessage(id: UUID().uuidString, role: "you", text: q))
        onChange(messages); input = ""; thinking = true; focused = false
        Task {
            let reply = await onInfer(history, q)
            await MainActor.run {
                thinking = false
                messages.append(RecipeMessage(id: UUID().uuidString, role: "recipe", text: reply))
                onChange(messages)
            }
        }
    }
    private func tag(_ s: String, _ icon: String) -> some View {
        HStack(spacing: 5) { Image(systemName: icon).font(.system(size: 9, weight: .bold)); Text(s).font(.system(size: 11, weight: .heavy, design: .rounded)) }
            .foregroundStyle(tint).padding(.horizontal, 10).padding(.vertical, 5)
            .background(Capsule().fill(tint.opacity(0.14)))
    }
    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// MARK: - RECIPE CHAINS — Scout → Critic → Editor, one tap. Each recipe's output feeds the next.
//
// The persisted ChainRecord lives in Sources/RuntimeCore/Desk/DeskRecords.swift (HS-72-09),
// embedding the canonical `Chain` contract.

// A chain as a routable primitive (route a card → run it through the chain).
struct ChainPrimitive: DeskPrimitive {
    let rec: ChainRecord
    var id: String { "chain:\(rec.id)" }
    var kind: PrimitiveKind { .chain }
    var glyph: String { "arrow.triangle.branch" }
    var isSymbol: Bool { true }
    var color: Color { DioPal.accent }
    var base: CGFloat { 110 }
    var title: String { rec.name.isEmpty ? ProductLanguage.label(.sequence) : rec.name }
    var subtitle: String { "\(rec.steps.count)-Persona Sequence · drop to run" }
    var preview: String? { "drop to run" }
    var sections: [PrimitiveSection] {
        [.init(label: "CAPABILITY", tint: DioPal.accent, body: .chips([
            "Run \(rec.name.isEmpty ? "Sequence" : rec.name)", "Input · text or Desk object",
            "Runs on · selected target", "Effect · creates Artifact",
            rec.steps.isEmpty ? "Unavailable · add a Persona" : "Ready · linear Sequence",
        ]))]
    }
    var accepts: [PrimitiveKind] { [.meeting, .summary, .actions, .topics, .transcript, .artifact, .note] }
    var emits: [PrimitiveKind] { [.artifact] }
}

// the rail chip — the chain's members overlapping like a team photo
struct DioChainChip: View {
    let chain: ChainRecord; let recipes: [RecipeRecord]
    private var members: [RecipeRecord] { chain.steps.compactMap { sid in recipes.first { $0.id == sid } } }
    var body: some View {
        VStack(spacing: 4) {
            ZStack {
                let show = Array(members.prefix(3))
                if show.isEmpty {
                    RoundedRectangle(cornerRadius: 14).fill(.white.opacity(0.08)).frame(width: 54, height: 54)
                        .overlay(Image(systemName: "arrow.triangle.branch").foregroundStyle(DioPal.muted))
                } else {
                    ForEach(Array(show.enumerated()), id: \.offset) { i, a in
                        RecipeAvatarView(avatarId: a.avatar, size: 34)
                            .offset(x: CGFloat(i) * 14 - CGFloat(show.count - 1) * 7)
                            .zIndex(Double(show.count - i))
                    }
                }
            }
            .frame(width: 60, height: 54)
            Text(chain.name.isEmpty ? ProductLanguage.label(.sequence) : chain.name)
                .font(.system(size: 9.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9))
                .lineLimit(1).frame(width: 64)
        }
    }
}

// the run/manage sheet — see the flow, give it something to chew on, run it
struct DioChainSheet: View {
    let chain: ChainRecord; let recipes: [RecipeRecord]
    let onRun: (String) -> Void
    let onEdit: () -> Void; let onDelete: () -> Void; let onClose: () -> Void
    @State private var input = ""
    private var members: [RecipeRecord] { chain.steps.compactMap { sid in recipes.first { $0.id == sid } } }
    private var ready: Bool { !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !members.isEmpty }
    var body: some View {
        DioAtelierPanel(maxW: 520, dismiss: onClose) {
            VStack(alignment: .leading, spacing: 15) {
                HStack(spacing: 12) {
                    Image(systemName: "arrow.triangle.branch").font(.system(size: 20, weight: .bold)).foregroundStyle(DioPal.accent)
                        .frame(width: 46, height: 46).background(RoundedRectangle(cornerRadius: 14).fill(DioPal.accent.opacity(0.16)))
                    VStack(alignment: .leading, spacing: 1) {
                        Text(chain.name).font(.system(size: 19, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                        Text("\(members.count)-Persona Sequence · runs in order").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                    }
                    Spacer(minLength: 0)
                    Menu {
                        Button { onEdit() } label: { Label("Edit Sequence", systemImage: "slider.horizontal.3") }
                        Button(role: .destructive) { onDelete() } label: { Label("Delete Sequence", systemImage: "trash") }
                    } label: { Image(systemName: "ellipsis.circle.fill").font(.system(size: 22)).foregroundStyle(DioPal.muted) }
                    Button { onClose() } label: { Image(systemName: "xmark.circle.fill").font(.system(size: 22)).foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
                }
                flowPreview
                Text("WHAT SHOULD THE CHAIN WORK ON?").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1).foregroundStyle(DioPal.muted)
                ZStack(alignment: .topLeading) {
                    if input.isEmpty { Text("e.g. our Q3 plan, the rough idea, the notes…").font(.system(size: 14, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.6)).padding(.horizontal, 16).padding(.top, 13).allowsHitTesting(false) }
                    TextEditor(text: $input).font(.system(size: 14, design: .rounded)).foregroundStyle(DioPal.text).scrollContentBackground(.hidden).padding(.horizontal, 11).padding(.vertical, 6).frame(height: 80)
                }.background(RoundedRectangle(cornerRadius: 14).fill(.white.opacity(0.05)).overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
                    .overlay(alignment: .bottomTrailing) { VoiceFillMic(text: $input, tint: DioPal.accent, size: 28).padding(9) }
                Button { let q = input.trimmingCharacters(in: .whitespacesAndNewlines); guard ready else { return }; onRun(q) } label: {
                    HStack(spacing: 8) { Image(systemName: "play.fill"); Text("Run the Sequence").font(.system(size: 16, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 52)
                        .background(Capsule().fill(LinearGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent], startPoint: .top, endPoint: .bottom)))
                        .opacity(ready ? 1 : 0.45)
                }.buttonStyle(.plain)
                Text("Long-press a Desk card to run this Sequence.").font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.8))
            }
            .padding(20)
        }
    }
    private var flowPreview: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(Array(members.enumerated()), id: \.offset) { i, a in
                    VStack(spacing: 3) { RecipeAvatarView(avatarId: a.avatar, size: 42); Text(a.name).font(.system(size: 9, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1).frame(width: 54) }
                    if i < members.count - 1 { Image(systemName: "arrow.right").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.muted.opacity(0.7)) }
                }
            }.padding(.vertical, 8).padding(.horizontal, 12)
        }
        .background(RoundedRectangle(cornerRadius: 16).fill(.white.opacity(0.04)))
    }
}

// the builder — name the chain, stack recipes in order
struct DioChainBuilder: View {
    @State var draft: ChainRecord
    let recipes: [RecipeRecord]
    let onSave: (ChainRecord) -> Void; let onCancel: () -> Void; var isNew: Bool
    var body: some View {
        DioAtelierPanel(maxW: 560, dismiss: onCancel) {
            VStack(spacing: 0) {
                HStack(spacing: 12) {
                    Image(systemName: "arrow.triangle.branch").font(.system(size: 20, weight: .bold)).foregroundStyle(DioPal.accent).frame(width: 46, height: 46).background(RoundedRectangle(cornerRadius: 14).fill(DioPal.accent.opacity(0.16)))
                    VStack(alignment: .leading, spacing: 1) {
                        Text(isNew ? "Build a Sequence" : "Edit Sequence").font(.system(size: 11.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.accent)
                        Text(draft.name.isEmpty ? "Unnamed Sequence" : draft.name).font(.system(size: 20, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    }
                    Spacer(minLength: 0)
                    Button { onCancel() } label: { Image(systemName: "xmark.circle.fill").font(.system(size: 24)).foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
                }.padding(.horizontal, 20).padding(.top, 18).padding(.bottom, 8)
                // the LIVE pipeline strip — the chain assembles under your fingers (HSM-17-08):
                // avatars flow left-to-right with arrows as steps are added / reordered.
                if !draft.steps.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(Array(draft.steps.enumerated()), id: \.offset) { i, sid in
                                if let a = recipes.first(where: { $0.id == sid }) {
                                    VStack(spacing: 3) {
                                        RecipeAvatarView(avatarId: a.avatar, size: 38)
                                        Text(a.name).font(.system(size: 8.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1).frame(width: 50)
                                    }
                                    if i < draft.steps.count - 1 {
                                        Image(systemName: "arrow.right").font(.system(size: 10, weight: .black)).foregroundStyle(DioPal.accent.opacity(0.7))
                                    }
                                }
                            }
                        }.padding(.vertical, 7).padding(.horizontal, 12)
                    }
                    .background(RoundedRectangle(cornerRadius: 14).fill(DioPal.accent.opacity(0.05))
                        .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(DioPal.accent.opacity(0.14), lineWidth: 1)))
                    .padding(.horizontal, 20).padding(.bottom, 10)
                    .transition(.opacity)
                }
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 18) {
                        sec("NAME") { field($draft.name, "e.g. Refine") }
                        sec("THE PIPELINE · runs top to bottom") {
                            if draft.steps.isEmpty {
                                Text("Add Personas to the Sequence.").font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                            }
                            ForEach(Array(draft.steps.enumerated()), id: \.offset) { i, sid in
                                if let a = recipes.first(where: { $0.id == sid }) {
                                    HStack(spacing: 10) {
                                        Text("\(i + 1)").font(.system(size: 12, weight: .black, design: .rounded)).foregroundStyle(.white).frame(width: 22, height: 22).background(Circle().fill(DioPal.accent.opacity(0.7)))
                                        RecipeAvatarView(avatarId: a.avatar, size: 34)
                                        VStack(alignment: .leading, spacing: 0) { Text(a.name).font(.system(size: 13.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text); Text(a.role).font(.system(size: 9.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1) }
                                        Spacer(minLength: 0)
                                        Button { move(i, -1) } label: { Image(systemName: "chevron.up").font(.system(size: 12, weight: .black)).foregroundStyle(i == 0 ? DioPal.muted.opacity(0.3) : DioPal.muted) }.buttonStyle(.plain).disabled(i == 0)
                                        Button { move(i, 1) } label: { Image(systemName: "chevron.down").font(.system(size: 12, weight: .black)).foregroundStyle(i == draft.steps.count - 1 ? DioPal.muted.opacity(0.3) : DioPal.muted) }.buttonStyle(.plain).disabled(i == draft.steps.count - 1)
                                        Button { draft.steps.remove(at: i) } label: { Image(systemName: "minus.circle.fill").font(.system(size: 16)).foregroundStyle(Color(hex: 0xFF6B6B)) }.buttonStyle(.plain)
                                    }
                                    .padding(.horizontal, 12).padding(.vertical, 8)
                                    .background(RoundedRectangle(cornerRadius: 13).fill(.white.opacity(0.05)))
                                }
                            }
                        }
                        sec("ADD A RECIPE") {
                            if recipes.isEmpty {
                                Text("Create a Persona first.").font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                            } else {
                                LazyVGrid(columns: [GridItem(.adaptive(minimum: 120), spacing: 8)], spacing: 8) {
                                    ForEach(recipes) { a in
                                        Button { draft.steps.append(a.id); haptic() } label: {
                                            HStack(spacing: 7) { RecipeAvatarView(avatarId: a.avatar, size: 26); Text(a.name).font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text); Spacer(minLength: 0); Image(systemName: "plus").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.muted) }
                                                .padding(.horizontal, 10).frame(height: 40).background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(.white.opacity(0.1), lineWidth: 1)))
                                        }.buttonStyle(.plain)
                                    }
                                }
                            }
                        }
                    }.padding(.horizontal, 20).padding(.bottom, 16)
                }
                HStack(spacing: 12) {
                    Button { onCancel() } label: { Text("Cancel").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 50).background(Capsule().fill(.white.opacity(0.06))) }.buttonStyle(.plain)
                    Button { save() } label: { HStack(spacing: 7) { Image(systemName: "checkmark"); Text(isNew ? "Create Sequence" : "Save").font(.system(size: 15.5, weight: .heavy, design: .rounded)) }.foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 50).background(Capsule().fill(LinearGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent], startPoint: .top, endPoint: .bottom))).opacity(canSave ? 1 : 0.45) }.buttonStyle(.plain).disabled(!canSave)
                }.padding(.horizontal, 20).padding(.vertical, 14)
            }
        }
    }
    private var canSave: Bool { !draft.name.trimmingCharacters(in: .whitespaces).isEmpty && !draft.steps.isEmpty }
    private func save() { guard canSave else { return }; haptic(.medium); onSave(draft) }
    private func move(_ i: Int, _ d: Int) { let j = i + d; guard draft.steps.indices.contains(j) else { return }; haptic(); draft.steps.swapAt(i, j) }
    @ViewBuilder private func sec<C: View>(_ t: String, @ViewBuilder _ c: () -> C) -> some View { VStack(alignment: .leading, spacing: 10) { Text(t).font(.system(size: 10.5, weight: .black, design: .rounded)).tracking(1.2).foregroundStyle(DioPal.muted); c() } }
    @ViewBuilder private func field(_ b: Binding<String>, _ p: String) -> some View {
        HStack(spacing: 8) {
            TextField("", text: b, prompt: Text(p).foregroundColor(DioPal.muted.opacity(0.7))).font(.system(size: 15, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text)
            VoiceFillMic(text: b, tint: DioPal.mint, size: 26)
        }.padding(.horizontal, 14).frame(height: 46).background(RoundedRectangle(cornerRadius: 13).fill(.white.opacity(0.05)).overlay(RoundedRectangle(cornerRadius: 13).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
    }
    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle = .light) { 
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
}

// the relay — the gamified payoff: each recipe lights up in turn, a checkmark drops, the baton passes down
struct DioChainRelay: View {
    let chain: ChainRecord; let recipes: [RecipeRecord]
    let step: Int               // current step (== count when finished)
    let results: [String]       // completed outputs so far
    private var members: [RecipeRecord] { chain.steps.compactMap { sid in recipes.first { $0.id == sid } } }
    var body: some View {
        ZStack {
            Color.black.opacity(0.8).ignoresSafeArea()
            VStack(spacing: 18) {
                Text(step >= members.count ? "Done" : "Running \(chain.name)…").font(.system(size: 18, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                VStack(spacing: 0) {
                    ForEach(Array(members.enumerated()), id: \.offset) { i, a in
                        HStack(spacing: 12) {
                            ZStack {
                                if i == step {
                                    TimelineView(.animation) { tl in let r = 0.5 + 0.5 * sin(tl.date.timeIntervalSinceReferenceDate * 5); Circle().strokeBorder(RecipeAvatars.color(a.avatar).opacity(0.8), lineWidth: 2).frame(width: 50 + 10 * r, height: 50 + 10 * r) }
                                }
                                RecipeAvatarView(avatarId: a.avatar, size: 46)
                                if i < step { Circle().fill(DioPal.mint).frame(width: 18, height: 18).overlay(Image(systemName: "checkmark").font(.system(size: 10, weight: .black)).foregroundStyle(.white)).offset(x: 18, y: -18) }
                            }
                            VStack(alignment: .leading, spacing: 2) {
                                Text(a.name).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                                Text(i < step ? String((i < results.count ? results[i] : "").prefix(64)) : (i == step ? "working…" : "waiting"))
                                    .font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(i == step ? RecipeAvatars.color(a.avatar) : DioPal.muted).lineLimit(2)
                            }
                            Spacer(minLength: 0)
                        }
                        .padding(.vertical, 8).opacity(i <= step ? 1 : 0.5)
                        if i < members.count - 1 { Rectangle().fill(i < step ? DioPal.mint.opacity(0.6) : DioPal.muted.opacity(0.3)).frame(width: 2, height: 18).padding(.leading, 22) }
                    }
                }
                .padding(18).frame(maxWidth: 420)
                .background(RoundedRectangle(cornerRadius: 22).fill(Color(hex: 0x14121B)).overlay(RoundedRectangle(cornerRadius: 22).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
            }
        }
    }
}
