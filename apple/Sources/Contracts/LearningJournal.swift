import Foundation

// HSM Contracts — the dictation learning loop, read side (Phase 19-06).
//
// Faithful Swift models for the desktop hub's two read-only learning routes:
//
//   - GET /api/dictation/journal          → JournalResponse  (newest-first entries
//                                            + the local-only toggle/retention/count)
//   - GET /api/dictation/learning-digest  → LearningDigest    (windowed "what HoldSpeak
//                                            learned" counts + per-correction reach)
//
// These are READ-ONLY on the iPad: no on-device journaling, no correction writes —
// that's Phase 9. The write/delete/correct routes on the hub are intentionally not
// modelled here.
//
// CRITICAL — naive timestamps. The hub stamps `created_at` via
// `datetime.now().isoformat()` (no `Z`, no offset) and the digest's `generated_at`
// the same way. The shared `HoldSpeakContracts.decoder()` uses `.iso8601`, which
// THROWS on a naive string. So every timestamp here is a raw `String?`, never a
// `Date` — exactly the bug just fixed in the meeting clients. Carry the string;
// the view layer formats it.

// MARK: - Journal (GET /api/dictation/journal)

/// One journaled dictation run, as `_journal_to_dict` serializes it. A pure record
/// of a single utterance's trip through the pipeline — what was said, what it became,
/// where it routed, and how long it took.
public struct JournalEntry: Codable, Sendable, Equatable, Identifiable {
    public let id: Int
    /// Naive ISO from `datetime.now().isoformat()` — String, never Date (decoder would throw).
    public let createdAt: String?
    /// "dictation" or "dry_run".
    public let source: String
    public let transcript: String
    public let finalText: String
    public let projectRoot: String?
    public let intent: String?
    public let blockId: String?
    public let targetProfile: String?
    /// Per-stage timings (stage id → ms). May be absent/empty on a bare run.
    public let stageMs: [String: Double]?
    public let totalMs: Double?
    /// Rewriter pass timings, when a rewrite happened.
    public let rewritePassMs: [Double]?
    public let confidence: Double?
    public let warnings: [String]?
    public let corrected: Bool
    public let correctionId: Int?
    /// HS-48-02 inline "learned from N similar" signal — the correction the live
    /// router would apply to this utterance, or `nil` when corrections are off /
    /// nothing matches (the hub stays honest rather than claim learning).
    public let learning: CorrectionSignal?

    public init(
        id: Int, createdAt: String?, source: String, transcript: String, finalText: String,
        projectRoot: String?, intent: String?, blockId: String?, targetProfile: String?,
        stageMs: [String: Double]?, totalMs: Double?, rewritePassMs: [Double]?,
        confidence: Double?, warnings: [String]?, corrected: Bool, correctionId: Int?,
        learning: CorrectionSignal?
    ) {
        self.id = id
        self.createdAt = createdAt
        self.source = source
        self.transcript = transcript
        self.finalText = finalText
        self.projectRoot = projectRoot
        self.intent = intent
        self.blockId = blockId
        self.targetProfile = targetProfile
        self.stageMs = stageMs
        self.totalMs = totalMs
        self.rewritePassMs = rewritePassMs
        self.confidence = confidence
        self.warnings = warnings
        self.corrected = corrected
        self.correctionId = correctionId
        self.learning = learning
    }
}

/// The inline correction signal carried on a journal entry (and the digest's match
/// shape) — `best_correction_signal`'s output. `nil` on an entry means the router
/// would nudge nothing.
public struct CorrectionSignal: Codable, Sendable, Equatable {
    public let matched: Bool
    /// "intent" or "target".
    public let kind: String
    public let value: String
    /// The gist (key) the correction is anchored on.
    public let gist: String
    /// How many journal utterances this correction reaches (Jaccard count).
    public let similar: Int

    public init(matched: Bool, kind: String, value: String, gist: String, similar: Int) {
        self.matched = matched
        self.kind = kind
        self.value = value
        self.gist = gist
        self.similar = similar
    }
}

/// The full `GET /api/dictation/journal` envelope: the entries plus the local-only
/// trust facts the UI shows (is journaling on, how many we keep, the true total).
/// On a bare server `items` is empty and `count` is 0 — never an error.
public struct JournalResponse: Codable, Sendable, Equatable {
    /// Whether journaling is enabled (config `journal_enabled`, default true).
    public let enabled: Bool
    /// How many entries are retained (config `journal_retention`).
    public let retention: Int
    /// The true total in the durable journal (may exceed `items.count` under a limit).
    public let count: Int
    public let items: [JournalEntry]

    public init(enabled: Bool, retention: Int, count: Int, items: [JournalEntry]) {
        self.enabled = enabled
        self.retention = retention
        self.count = count
        self.items = items
    }
}

// MARK: - Learning digest (GET /api/dictation/learning-digest)

/// The "What HoldSpeak learned" digest from `build_learning_digest`. Window scopes
/// the *activity* (corrections made, dictations corrected, breakdowns); per-correction
/// reach ("N similar") is over the whole journal because a correction nudges every
/// matching utterance regardless of when it was said.
public struct LearningDigest: Codable, Sendable, Equatable {
    /// "week" (last 7 days) or "all".
    public let window: String
    /// Whether `corrections_enabled` is on. Counts are real either way; this lets the
    /// view phrase coverage honestly ("now nudged" only when corrections actually route).
    public let enabled: Bool
    /// Naive ISO (`now.isoformat()`) — String, never Date.
    public let generatedAt: String?
    public let totals: Totals
    public let byKind: ByKind
    public let byBlock: [BlockCount]
    public let byTarget: [TargetCount]
    public let corrections: [CorrectionRow]

    public struct Totals: Codable, Sendable, Equatable {
        public let correctionsMade: Int
        public let dictationsCorrected: Int
        public let similarNudged: Int
        public let journalCount: Int

        public init(correctionsMade: Int, dictationsCorrected: Int, similarNudged: Int, journalCount: Int) {
            self.correctionsMade = correctionsMade
            self.dictationsCorrected = dictationsCorrected
            self.similarNudged = similarNudged
            self.journalCount = journalCount
        }
    }

    public struct ByKind: Codable, Sendable, Equatable {
        public let intent: Int
        public let target: Int

        public init(intent: Int, target: Int) {
            self.intent = intent
            self.target = target
        }
    }

    /// A ranked `{block_id, count}` row (corrections that re-route intent to a block).
    public struct BlockCount: Codable, Sendable, Equatable {
        public let blockId: String
        public let count: Int

        public init(blockId: String, count: Int) {
            self.blockId = blockId
            self.count = count
        }
    }

    /// A ranked `{target_profile, count}` row (corrections that re-target output).
    public struct TargetCount: Codable, Sendable, Equatable {
        public let targetProfile: String
        public let count: Int

        public init(targetProfile: String, count: Int) {
            self.targetProfile = targetProfile
            self.count = count
        }
    }

    /// One windowed correction with its whole-journal reach.
    public struct CorrectionRow: Codable, Sendable, Equatable, Identifiable {
        /// `null` when the store is non-durable (in-memory only).
        public let id: Int?
        /// "intent" or "target".
        public let kind: String
        public let gist: String
        public let value: String
        /// Naive ISO or `null` — String, never Date.
        public let createdAt: String?
        /// How many journal utterances this correction reaches.
        public let similar: Int

        public init(id: Int?, kind: String, gist: String, value: String, createdAt: String?, similar: Int) {
            self.id = id
            self.kind = kind
            self.gist = gist
            self.value = value
            self.createdAt = createdAt
            self.similar = similar
        }
    }

    public init(
        window: String, enabled: Bool, generatedAt: String?, totals: Totals, byKind: ByKind,
        byBlock: [BlockCount], byTarget: [TargetCount], corrections: [CorrectionRow]
    ) {
        self.window = window
        self.enabled = enabled
        self.generatedAt = generatedAt
        self.totals = totals
        self.byKind = byKind
        self.byBlock = byBlock
        self.byTarget = byTarget
        self.corrections = corrections
    }
}
