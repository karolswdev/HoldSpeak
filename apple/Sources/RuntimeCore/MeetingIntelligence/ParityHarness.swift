import Foundation
import Contracts

/// HSM-6-04 — the parity baseline harness.
///
/// The Track-G gate is "parity with the desktop quality baseline" — meaningless
/// until parity is operationally defined. Intel is non-deterministic, so a string
/// diff is wrong. This scores mobile output on **substance coverage**: a rubric
/// names, per category, the key facts a good artifact MUST cover (grounded in what
/// is actually in the transcript / the desktop baseline); the scorer checks how
/// many are covered, phrasing-tolerant, and is a **pure function** — rerun → an
/// identical verdict (the non-determinism is in generation, not in judging).
///
/// The rubric values (the must-cover facts + the pass threshold) are owner-signed
/// (HSM-6-04 acceptance); HSM-6-05 runs this and records the gate verdict.

/// A parity category: the four core artifact types, ADR candidates, or the summary
/// (which is an `IntelSnapshot`, not an `artifact_type` — kept honest).
public enum ParityCategory: Sendable, Equatable, Hashable {
    case artifact(ArtifactType)
    case summary
}

public struct ParityRubric: Sendable, Equatable {
    public struct Expectation: Sendable, Equatable {
        public let category: ParityCategory
        /// Key facts a good artifact must cover. A fact is "covered" if all its
        /// significant tokens appear in the mobile output for that category.
        public let mustCover: [String]
        public init(category: ParityCategory, mustCover: [String]) {
            self.category = category; self.mustCover = mustCover
        }
    }
    public let meetingId: String
    public let expectations: [Expectation]
    public let threshold: Double   // pass if overall coverage >= threshold
    public init(meetingId: String, expectations: [Expectation], threshold: Double) {
        self.meetingId = meetingId; self.expectations = expectations; self.threshold = threshold
    }
}

public struct ParityReport: Sendable, Equatable {
    public struct CategoryScore: Sendable, Equatable {
        public let category: ParityCategory
        public let covered: Int
        public let total: Int
        public let missing: [String]
        public var coverage: Double { total == 0 ? 1.0 : Double(covered) / Double(total) }
    }
    public let perCategory: [CategoryScore]
    public let threshold: Double
    /// Coverage across every fact in the rubric (not an average of ratios), so a
    /// type with more facts weighs proportionally.
    public var overallCoverage: Double {
        let total = perCategory.reduce(0) { $0 + $1.total }
        let covered = perCategory.reduce(0) { $0 + $1.covered }
        return total == 0 ? 1.0 : Double(covered) / Double(total)
    }
    public var passed: Bool { overallCoverage >= threshold }
}

public enum ParityScorer {

    /// Score the mobile output against the rubric. Pure + deterministic.
    public static func score(
        artifacts: [Artifact], summary: IntelSnapshot?, rubric: ParityRubric
    ) -> ParityReport {
        // Stable category order so the report is identical across reruns.
        let scores = rubric.expectations.map { exp -> ParityReport.CategoryScore in
            let haystack = tokens(in: searchText(for: exp.category, artifacts: artifacts, summary: summary))
            var missing: [String] = []
            for fact in exp.mustCover where !covers(haystack, fact: fact) { missing.append(fact) }
            return .init(category: exp.category,
                         covered: exp.mustCover.count - missing.count,
                         total: exp.mustCover.count, missing: missing)
        }
        return ParityReport(perCategory: scores, threshold: rubric.threshold)
    }

    /// All searchable text the mobile run produced for a category.
    static func searchText(for category: ParityCategory, artifacts: [Artifact], summary: IntelSnapshot?) -> String {
        switch category {
        case .summary:
            guard let s = summary else { return "" }
            return ([s.summary] + s.topics).joined(separator: " ")
        case .artifact(let type):
            return artifacts.filter { $0.artifactType == type }
                .map { $0.title + " " + $0.bodyMarkdown + " " + flatten($0.structuredJson) }
                .joined(separator: " ")
        }
    }

    /// A fact is covered when every significant token of it is present.
    static func covers(_ haystack: Set<String>, fact: String) -> Bool {
        let needles = tokens(in: fact)
        guard !needles.isEmpty else { return true }
        return needles.isSubset(of: haystack)
    }

    /// Lowercased alphanumeric tokens of length >= 3 (drops stopword-ish noise so
    /// matching is tolerant of phrasing, punctuation, and case).
    static func tokens(in text: String) -> Set<String> {
        let lowered = text.lowercased()
        let parts = lowered.split { !$0.isLetter && !$0.isNumber }
        return Set(parts.map(String.init).filter { $0.count >= 3 })
    }

    /// Collect every scalar (string/number) in a JSONValue into searchable text.
    static func flatten(_ value: JSONValue) -> String {
        switch value {
        case .string(let s): return s
        case .number(let n): return String(n)
        case .bool(let b): return String(b)
        case .null: return ""
        case .array(let a): return a.map(flatten).joined(separator: " ")
        case .object(let o): return o.values.map(flatten).joined(separator: " ")
        }
    }
}
