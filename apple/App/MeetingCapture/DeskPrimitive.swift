import SwiftUI

// HSM-14 — THE PRIMITIVE CONTRACT (story-25). Literally everything on the desk is a `DeskPrimitive` that
// declares the same small facet set; the ENTIRE UI is derived from that declaration — the canvas object, the
// card, the pull-out, the menu, and (next) the routing — so every primitive looks and behaves the same.
// Add a concept to the platform = declare one primitive; its whole UI appears for free. This is the
// "standard UI integration pattern you can rely on." Routing (`accepts`/`emits`/receive) is declared here so
// the keystone gesture (drag onto the AI core → LLM → new primitive) becomes trivial to add next.

enum PrimitiveKind: String {
    case meeting, summary, actions, transcript, topics, note, artifact, model, kb, workflow, connector, agent, chain, game, coder

    var glyph: String {                       // the sprite asset (one source of truth → canvas + card + pull-out)
        switch self {
        case .meeting: return "cassette"
        case .model:   return "cartridge"
        case .kb:      return "crystal"
        case .note:    return "note"
        case .agent:   return "sparkles"      // overridden per-agent by its chosen avatar
        case .chain:   return "arrow.triangle.branch"
        case .game:    return "gamecontroller.fill"   // overridden per-game by its cover art
        case .coder:   return "sparkles"              // a live coding session; overridden per-agent
        default:       return "cassette"
        }
    }
    var color: Color {
        switch self {
        case .meeting, .summary, .artifact: return DioPal.accent
        case .actions, .note:               return DioPal.mint
        case .transcript, .model:           return DioPal.cobalt
        case .topics, .kb, .workflow:       return DioPal.violet
        case .connector:                    return DioPal.cobalt
        case .agent:                        return DioPal.mint   // overridden per-agent by its avatar hue
        case .chain:                        return DioPal.accent
        case .game:                         return DioPal.cobalt
        case .coder:                        return DioPal.cobalt
        }
    }
    var badge: String { rawValue.uppercased() }
    var base: CGFloat {                       // canvas sprite size
        switch self { case .model: return 162; case .kb: return 120; case .note: return 106; case .agent: return 104; case .chain: return 110; case .game: return 122; case .coder: return 118; default: return 130 }
    }
}

// A uniform pull-out section — data only; ONE renderer (DioPullout) knows how to draw each body. The
// primitive never builds views, so every section looks identical across types.
enum SectionBody {
    case text(String)
    case actions([(task: String, meta: String?)])
    case chips([String])
    case transcript([(who: String, what: String)])
    // A meeting's derived primitives (summaries, decisions, agent replies…) shown as tappable cards
    // INSIDE the meeting's drawer — the meeting owns its outputs instead of scattering them on the desk.
    case derivatives([(id: String, title: String, lens: String, snippet: String)])
}
struct PrimitiveSection { let label: String; let tint: Color; let body: SectionBody }

enum ActionRole: Equatable { case openEditor, route, send, custom(String) }
struct PrimitiveAction { let label: String; let icon: String; let role: ActionRole }

// The contract every desk concept conforms to.
protocol DeskPrimitive {
    var id: String { get }
    var kind: PrimitiveKind { get }
    var title: String { get }
    var subtitle: String { get }              // the pull-out header's second line
    var preview: String? { get }              // one-line snippet (the card face)
    var sections: [PrimitiveSection] { get }  // the pull-out body
    var actions: [PrimitiveAction] { get }    // long-press menu / drawer buttons
    var emits: [PrimitiveKind] { get }        // outputs you can pull off / drag away
    var accepts: [PrimitiveKind] { get }      // what it consumes when something is dropped on it
    // These MUST be protocol requirements (not extension-only): accessed through `any DeskPrimitive`,
    // an extension-only member dispatches STATICALLY to the default and ignores a conformer's override —
    // which silently rendered every connector/workflow as a cassette (glyph→default, isSymbol→false).
    var glyph: String { get }                 // the sprite asset OR SF-symbol name
    var color: Color { get }
    var base: CGFloat { get }                 // canvas sprite size
    var isSymbol: Bool { get }                // glyph is an SF Symbol (a tool/connector), not a pixel sprite
}

// Derived defaults so a primitive only declares what's distinctive.
extension DeskPrimitive {
    var glyph: String { kind.glyph }
    var color: Color { kind.color }
    var base: CGFloat { kind.base }
    var subtitle: String { preview ?? "" }
    var preview: String? { nil }
    var sections: [PrimitiveSection] { [] }
    var actions: [PrimitiveAction] { [] }
    var emits: [PrimitiveKind] { [] }
    var accepts: [PrimitiveKind] { [] }
    func canReceive(_ other: DeskPrimitive) -> Bool { accepts.contains(other.kind) }
    var isSymbol: Bool { false }              // glyph is an SF Symbol (a tool/connector), not a pixel sprite

    // The text you feed to an LLM when this primitive is routed — derived from its sections, generically.
    var routableText: String {
        sections.map { sec -> String in
            switch sec.body {
            case .text(let s):        return s
            case .actions(let rows):  return rows.map { "- \($0.task)" }.joined(separator: "\n")
            case .chips(let c):       return c.joined(separator: ", ")
            case .transcript(let l):  return l.map { "\($0.who): \($0.what)" }.joined(separator: "\n")
            case .derivatives(let d): return d.map { "\($0.lens): \($0.title)" }.joined(separator: "\n")
            }
        }.joined(separator: "\n\n")
    }
}

// MARK: - conformers (every desk concept is one declaration)

struct MeetingPrimitive: DeskPrimitive {
    let meeting: Meeting; let index: Int
    var derivatives: [OutputRecord] = []   // the meeting's own outputs (grouped by lineage), shown in its drawer
    var id: String { "m:\(meeting.id)" }
    var kind: PrimitiveKind { .meeting }
    var glyph: String { SpriteStore.sprite(id: id, kind: .meeting, fallback: index % 2 == 0 ? "cassette" : "cassette2") }
    var title: String {
        if let t = meeting.title, !t.isEmpty { return t }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"; return f.string(from: meeting.startedAt)
    }
    var preview: String? {
        if let s = meeting.intel?.summary, !s.isEmpty { return s }
        if let t = meeting.intel?.topics.first { return t }
        return meeting.segments.first?.text
    }
    var sections: [PrimitiveSection] {
        var out: [PrimitiveSection] = []
        if !derivatives.isEmpty {
            out.append(.init(label: "DERIVATIVES · \(derivatives.count)", tint: DioPal.accent,
                             body: .derivatives(derivatives.map { (id: "out:\($0.id)", title: $0.title, lens: $0.lens, snippet: String($0.body.prefix(120))) })))
        }
        if let s = meeting.intel?.summary, !s.isEmpty { out.append(.init(label: "SUMMARY", tint: DioPal.accent, body: .text(s))) }
        let acts = meeting.intel?.actionItems ?? []
        if !acts.isEmpty {
            out.append(.init(label: "ACTIONS · \(acts.count)", tint: DioPal.mint,
                             body: .actions(acts.map { ($0.task, [$0.owner, $0.due].compactMap { $0 }.joined(separator: " · ").nilIfEmpty) })))
        }
        let topics = meeting.intel?.topics ?? []
        if !topics.isEmpty { out.append(.init(label: "TOPICS", tint: DioPal.violet, body: .chips(topics))) }
        if !meeting.segments.isEmpty {
            out.append(.init(label: "TRANSCRIPT · \(meeting.segments.count) lines", tint: DioPal.cobalt,
                             body: .transcript(meeting.segments.map { ($0.speaker.isEmpty ? "Speaker" : $0.speaker, $0.text) })))
        }
        return out
    }
    var actions: [PrimitiveAction] { [PrimitiveAction(label: "Open full editor", icon: "rectangle.expand.vertical", role: .openEditor)] }
    var emits: [PrimitiveKind] { [.summary, .actions, .transcript, .topics] }
    var subtitle: String {
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"
        let spk = Set(meeting.segments.map(\.speaker)).count
        let dur = meeting.formattedDuration ?? (meeting.duration.map { "\(Int($0 / 60)) min" } ?? "")
        let deriv = derivatives.isEmpty ? nil : "\(derivatives.count) artifact\(derivatives.count == 1 ? "" : "s")"
        return [f.string(from: meeting.startedAt), dur.isEmpty ? nil : dur, "\(spk) speaker\(spk == 1 ? "" : "s")", deriv].compactMap { $0 }.joined(separator: "  ·  ")
    }
}

struct ModelPrimitive: DeskPrimitive {
    let modelId: String; let name: String
    var id: String { "model:\(modelId)" }
    var kind: PrimitiveKind { .model }
    var title: String { name }
    var preview: String? { "on device · ready" }
    var sections: [PrimitiveSection] {
        [.init(label: "MODEL", tint: DioPal.cobalt, body: .text("\(name) — loaded and ready."))]
    }
    var accepts: [PrimitiveKind] { [.meeting, .summary, .actions, .transcript, .topics, .note, .artifact] } // the AI core eats anything
}

// A KNOWLEDGE BASE — a typed container you ground answers in. Now a full desk primitive (stable id,
// placeable, filable into zones, rename/delete on-desk). Persisted as a KBRecord (HS-72-09: lives in
// Sources/RuntimeCore/Desk/DeskRecords.swift, embedding the canonical `KB` contract); `items` is how
// many cards have been routed into it.
struct KBPrimitive: DeskPrimitive {
    let rec: KBRecord
    var id: String { "kb:\(rec.id)" }
    var kind: PrimitiveKind { .kb }
    var glyph: String { SpriteStore.sprite(id: id, kind: .kb, fallback: "crystal") }
    var title: String { rec.name }
    var preview: String? { "\(rec.items) item\(rec.items == 1 ? "" : "s")" }
    var sections: [PrimitiveSection] {
        [.init(label: "KNOWLEDGE", tint: DioPal.violet, body: .text("\(rec.items) item\(rec.items == 1 ? "" : "s") filed here."))]
    }
    var actions: [PrimitiveAction] {
        [PrimitiveAction(label: "Rename", icon: "pencil", role: .openEditor),
         PrimitiveAction(label: "Delete", icon: "trash", role: .custom("delete"))]
    }
    var accepts: [PrimitiveKind] { [.note, .artifact, .summary, .actions, .topics] }
}

// A GAME placed on the desk — a first-class primitive (placeable, filable, deletable) with a "play"
// capability and a harvestable score. Persisted as a GameRecord; `best` is read live from the game's
// own UserDefaults so the card always shows the current high score.
struct GameRecord: Codable, Identifiable, Equatable {
    var gameId: String; var path: String
    var id: String { gameId }
}
struct GamePrimitive: DeskPrimitive {
    let gameId: String; let name: String; let best: Int; let path: String
    var id: String { "game:\(gameId)" }
    var kind: PrimitiveKind { .game }
    var glyph: String { "game_\(gameId)" }    // the PixelLab cover art, rendered via DeskSprite
    var base: CGFloat { 122 }
    var title: String { name }
    var subtitle: String { best > 0 ? "best \(best) · tap to play" : "tap to play" }
    var preview: String? { best > 0 ? "Best: \(best)" : "Tap to play" }
    var sections: [PrimitiveSection] {
        [.init(label: "GAME", tint: DioPal.cobalt, body: .text(best > 0 ? "Your best: \(best)." : "A quick desk game."))]
    }
    var actions: [PrimitiveAction] {
        [PrimitiveAction(label: "Play", icon: "play.fill", role: .custom("play")),
         PrimitiveAction(label: "Harvest score", icon: "tray.and.arrow.down.fill", role: .custom("harvest")),
         PrimitiveAction(label: "Remove from desk", icon: "trash", role: .custom("delete"))]
    }
    var emits: [PrimitiveKind] { [.artifact] }
}

// A generated output — the result of routing a primitive through the AI core. It's a first-class primitive
// itself, so you can route it AGAIN (every output is also an input). Persisted as an OutputRecord
// (HS-72-09: lives in Sources/RuntimeCore/Desk/DeskRecords.swift, embedding the canonical `Artifact`
// contract; its `RunProvenance` lineage moved with it).
struct OutputPrimitive: DeskPrimitive {
    let rec: OutputRecord
    var id: String { "out:\(rec.id)" }
    var kind: PrimitiveKind { .artifact }
    var glyph: String { "note" }
    var base: CGFloat { 112 }
    var title: String { rec.title }
    // The pull-out subtitle leads with lineage ("from <source card> · via Scout") when this
    // output came from a routed run; otherwise the classic "from <source> · <lens>".
    var subtitle: String {
        if let p = rec.provenance, !p.line.isEmpty { return p.line }
        return "from \(rec.source) · \(rec.lens.lowercased())"
    }
    var preview: String? { rec.body }
    var sections: [PrimitiveSection] { [.init(label: rec.lens.uppercased(), tint: DioPal.accent, body: .text(rec.body))] }
    var emits: [PrimitiveKind] { [.artifact] }
}

// A NOTE — a first-class jotting you write and place on the desk yourself (vs an Output, which the AI
// generates). It files into zones, routes through the AI core, and deletes — like everything else.
// Persisted as a NoteRecord (HS-72-09: lives in Sources/RuntimeCore/Desk/DeskRecords.swift, embedding
// the canonical `Note` contract); its zone lives on `path` (same model as OutputRecord).
struct NotePrimitive: DeskPrimitive {
    let rec: NoteRecord
    var id: String { "note:\(rec.id)" }
    var kind: PrimitiveKind { .note }
    var glyph: String { SpriteStore.sprite(id: id, kind: .note, fallback: "note") }
    var base: CGFloat { 108 }
    var title: String { rec.title.isEmpty ? "Note" : rec.title }
    var subtitle: String { "a note · tap to edit" }
    var preview: String? { rec.body.isEmpty ? "Empty note — tap to write" : rec.body }
    var sections: [PrimitiveSection] {
        [.init(label: "NOTE", tint: DioPal.mint, body: .text(rec.body.isEmpty ? "Tap Edit to write this note." : rec.body))]
    }
    var actions: [PrimitiveAction] {
        [PrimitiveAction(label: "Edit note", icon: "pencil", role: .openEditor),
         PrimitiveAction(label: "Delete", icon: "trash", role: .custom("delete"))]
    }
    var emits: [PrimitiveKind] { [.note, .artifact] }
}

// A CONNECTOR — a tool on the desk that sends an output OUT of the app (the integrations half). Same
// grammar as the AI core: drop a primitive on it → it `accepts` it → propose→approve→execute. Rendered from
// an SF Symbol (it's a tool, not a recording). Configured by a webhook URL the user pastes.
struct ConnectorPrimitive: DeskPrimitive {
    let connId: String; let name: String; let symbol: String; let tint: Color; let configured: Bool; let detail: String
    var id: String { "conn:\(connId)" }
    var kind: PrimitiveKind { .connector }
    var glyph: String { symbol }
    var isSymbol: Bool { true }
    var color: Color { tint }
    var base: CGFloat { 116 }
    var title: String { name }
    var subtitle: String { configured ? "via your desktop · \(detail)" : "tap to pair your desktop" }
    var preview: String? { configured ? "via your desktop" : "pair your desktop" }
    var sections: [PrimitiveSection] {
        [.init(label: "CONNECTOR", tint: tint, body: .text(configured
            ? "Sends to \(name) via your desktop (\(detail))."
            : "Pair your desktop to send to \(name)."))]
    }
    var actions: [PrimitiveAction] {
        [PrimitiveAction(label: configured ? "Your desktop ·\(detail)" : "Pair your desktop", icon: "desktopcomputer", role: .custom("connect"))]
    }
    var accepts: [PrimitiveKind] { configured ? [.artifact, .summary, .actions, .topics, .meeting] : [] }
}

// A WORKFLOW — a saved Ask, turned into a reusable tool on the desk. Drop a meeting/output on it and it runs
// the saved prompt through the AI core (no sheet). The desk becomes a place where you BUILD tools, not just
// one-shot asks. Persisted as a WorkflowRecord (HS-72-09: lives in
// Sources/RuntimeCore/Desk/DeskRecords.swift, embedding the canonical `WorkflowDefinition`
// contract); every output it makes is itself a routable primitive.
struct WorkflowPrimitive: DeskPrimitive {
    let rec: WorkflowRecord
    var id: String { "wf:\(rec.id)" }
    var kind: PrimitiveKind { .workflow }
    var glyph: String { "gearshape.2.fill" }
    var isSymbol: Bool { true }
    var color: Color { DioPal.violet }
    var base: CGFloat { 118 }
    var title: String { rec.name }
    var subtitle: String { "a saved Ask · drop to run" }
    var preview: String? { "drop to run" }
    var sections: [PrimitiveSection] {
        [.init(label: "WORKFLOW", tint: DioPal.violet, body: .text("A saved Ask.")),
         .init(label: "PROMPT", tint: DioPal.muted, body: .text(rec.prompt))]
    }
    var accepts: [PrimitiveKind] { [.meeting, .summary, .actions, .topics, .artifact] }
}

// The lenses you can route a primitive through (the prompt presets). "Ask…" is a free prompt.
struct RouteLens: Identifiable { let id = UUID(); let name: String; let icon: String; let instruction: String }
enum RouteLenses {
    static let all: [RouteLens] = [
        .init(name: "Summarize", icon: "sparkles", instruction: "Summarize the following in 3–4 tight sentences. Be concrete."),
        .init(name: "Action items", icon: "checkmark.circle", instruction: "Extract the concrete action items as a short list, each as 'task — owner — due' when known."),
        .init(name: "Risks", icon: "exclamationmark.triangle", instruction: "List the top risks, blockers, and open questions implied by the following. Be specific and brief."),
        .init(name: "Decisions", icon: "flag", instruction: "List the decisions that were made in the following. One line each."),
        .init(name: "Draft email", icon: "envelope", instruction: "Write a short, friendly follow-up email summarizing the following and its next steps."),
    ]
}

private extension String { var nilIfEmpty: String? { isEmpty ? nil : self } }
