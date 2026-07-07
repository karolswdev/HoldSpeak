import Foundation

/// HSM-15-12 — the context envelope. ONE assembler turns a grounding selection
/// into ordered, provenance-headed blocks appended to a run's `[CONTEXT]`, so
/// the on-device, endpoint, and desktop paths ship the same shape. Pure and
/// host-testable: hydration (reading the synced records) happens at the call
/// site; budget refusal happens HERE, before any run — never a silent trim.
public enum ContextEnvelope {

    /// One grounded block. `detail` is the meeting's date, or an artifact's
    /// parent meeting title; empty detail drops the suffix.
    public struct Block: Equatable, Sendable {
        public enum Kind: String, Sendable { case meeting, artifact, note, kb }
        public var kind: Kind
        public var title: String
        public var detail: String
        public var body: String

        public init(kind: Kind, title: String, detail: String = "", body: String) {
            self.kind = kind; self.title = title; self.detail = detail; self.body = body
        }

        /// `[MEETING: Q3 kickoff — 2026-07-01]` / `[ARTIFACT: Decisions — Q3 kickoff]`
        public var header: String {
            let label = kind.rawValue.uppercased()
            return detail.isEmpty ? "[\(label): \(title)]" : "[\(label): \(title) — \(detail)]"
        }

        public var rendered: String { body.isEmpty ? header : header + "\n" + body }
    }

    public enum Failure: Error, Equatable {
        /// The selection does not fit the run's budget. The gauge said so
        /// BEFORE the run; the fix is picking less, not a hidden truncation.
        case overBudget(needed: Int, budget: Int)
    }

    /// The envelope text, or the honest refusal. `budgetTokens` nil = the run
    /// target hydrates elsewhere (hub refs) and no client budget applies.
    public static func assemble(_ blocks: [Block], budgetTokens: Int? = nil) -> Result<String, Failure> {
        let text = blocks.map(\.rendered).joined(separator: "\n\n")
        if let budget = budgetTokens {
            let needed = OnDeviceBudget.estimateTokens(text)
            if needed > budget { return .failure(.overBudget(needed: needed, budget: budget)) }
        }
        return .success(text)
    }

    /// The gauge's number for a selection — same estimator the run refusal uses.
    public static func estimateTokens(_ blocks: [Block]) -> Int {
        blocks.isEmpty ? 0 : OnDeviceBudget.estimateTokens(blocks.map(\.rendered).joined(separator: "\n\n"))
    }

    /// The KB honesty rider: real hydrated content, or an explicit marker —
    /// the "lean on the knowledge base" hint string is dead.
    public static func kbBlock(name: String, content: String?) -> Block {
        let body = (content ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        return Block(kind: .kb, title: name,
                     detail: body.isEmpty ? "not hydrated on this device" : "",
                     body: body)
    }
}

/// What a conversation is grounded on — persists PER CONVERSATION (the chat
/// keeps its grounding), never per recipe: the recipe's standing context
/// (manual text / zone / KB) stays authorship, this stays the ask's records.
public struct GroundingSelection: Codable, Equatable, Sendable {
    public struct Meeting: Codable, Equatable, Sendable {
        public var id: String
        public var title: String
        public var day: String                 // "2026-07-01" or ""
        public var includeTranscript: Bool     // full transcript vs digest
        public var includeIntel: Bool
        public var artifactIds: [String]       // the bound artifacts toggled ON

        public init(id: String, title: String, day: String = "",
                    includeTranscript: Bool = false, includeIntel: Bool = true,
                    artifactIds: [String] = []) {
            self.id = id; self.title = title; self.day = day
            self.includeTranscript = includeTranscript
            self.includeIntel = includeIntel
            self.artifactIds = artifactIds
        }
    }

    public var meetings: [Meeting]

    public init(meetings: [Meeting] = []) { self.meetings = meetings }

    public var isEmpty: Bool { meetings.isEmpty }

    /// The wire half (HSM-15-11 pairing): a desktop run ships REFERENCES and
    /// the hub hydrates from its own store — ids, never bodies, over DERP.
    public var hubMeetingIds: [String] { meetings.map(\.id) }
    public var hubArtifactIds: [String] { meetings.flatMap(\.artifactIds) }
    public var hubExpand: String { meetings.contains(where: \.includeTranscript) ? "full" : "summary" }

    /// The picker chip's label: `Grounded on 2 meetings · 3 artifacts`.
    public var summaryLabel: String {
        guard !isEmpty else { return "" }
        var parts = ["\(meetings.count) meeting" + (meetings.count == 1 ? "" : "s")]
        let arts = hubArtifactIds.count
        if arts > 0 { parts.append("\(arts) artifact" + (arts == 1 ? "" : "s")) }
        return parts.joined(separator: " · ")
    }
}
