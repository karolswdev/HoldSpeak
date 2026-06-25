import SwiftUI

// HSM-14 — THE PRIMITIVE CONTRACT (story-25). Literally everything on the desk is a `DeskPrimitive` that
// declares the same small facet set; the ENTIRE UI is derived from that declaration — the canvas object, the
// card, the pull-out, the menu, and (next) the routing — so every primitive looks and behaves the same.
// Add a concept to the platform = declare one primitive; its whole UI appears for free. This is the
// "standard UI integration pattern you can rely on." Routing (`accepts`/`emits`/receive) is declared here so
// the keystone gesture (drag onto the AI core → LLM → new primitive) becomes trivial to add next.

enum PrimitiveKind: String {
    case meeting, summary, actions, transcript, topics, note, artifact, model, kb, workflow, connector

    var glyph: String {                       // the sprite asset (one source of truth → canvas + card + pull-out)
        switch self {
        case .meeting: return "cassette"
        case .model:   return "cartridge"
        case .kb:      return "crystal"
        case .note:    return "note"
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
        }
    }
    var badge: String { rawValue.uppercased() }
    var base: CGFloat {                       // canvas sprite size
        switch self { case .model: return 162; case .kb: return 120; case .note: return 106; default: return 130 }
    }
}

// A uniform pull-out section — data only; ONE renderer (DioPullout) knows how to draw each body. The
// primitive never builds views, so every section looks identical across types.
enum SectionBody {
    case text(String)
    case actions([(task: String, meta: String?)])
    case chips([String])
    case transcript([(who: String, what: String)])
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
}

// MARK: - conformers (every desk concept is one declaration)

struct MeetingPrimitive: DeskPrimitive {
    let meeting: Meeting; let index: Int
    var id: String { "m:\(meeting.id)" }
    var kind: PrimitiveKind { .meeting }
    var glyph: String { index % 2 == 0 ? "cassette" : "cassette2" }
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
        return [f.string(from: meeting.startedAt), dur.isEmpty ? nil : dur, "\(spk) speaker\(spk == 1 ? "" : "s")"].compactMap { $0 }.joined(separator: "  ·  ")
    }
}

struct ModelPrimitive: DeskPrimitive {
    let modelId: String; let name: String
    var id: String { "model:\(modelId)" }
    var kind: PrimitiveKind { .model }
    var title: String { name }
    var preview: String? { "on device · ready" }
    var sections: [PrimitiveSection] {
        [.init(label: "MODEL", tint: DioPal.cobalt, body: .text("\(name) — loaded and ready. Every meeting is summarised on this iPad; nothing leaves the device."))]
    }
    var accepts: [PrimitiveKind] { [.meeting, .summary, .actions, .transcript, .topics, .note, .artifact] } // the AI core eats anything
}

struct KBPrimitive: DeskPrimitive {
    let name: String; let items: Int
    var id: String { "kb:\(name)" }
    var kind: PrimitiveKind { .kb }
    var title: String { name }
    var preview: String? { "\(items) item\(items == 1 ? "" : "s")" }
    var sections: [PrimitiveSection] {
        [.init(label: "KNOWLEDGE", tint: DioPal.violet, body: .text("\(items) item\(items == 1 ? "" : "s") filed here. Ask a grounded question and get an answer cited from your own notes."))]
    }
    var accepts: [PrimitiveKind] { [.note, .artifact, .summary] }
}

private extension String { var nilIfEmpty: String? { isEmpty ? nil : self } }
