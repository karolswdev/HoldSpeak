import Foundation

/// HS-92-01 — canonical product language shared by Swift hosts.
///
/// Codable model names and wire keys remain compatible (`Recipe`, `Directory`,
/// `KB`, `Chain`, `RuntimeProfile`). Views use these product terms instead.
public enum CanonicalProductTerm: String, Codable, CaseIterable, Sendable {
    case desk, meeting, transcript, actionItem = "action_item", result, artifact, note
    case zone, knowledge, project, persona, coderSession = "coder_session"
    case workflow, sequence, integration, runsOn = "runs_on"
    case proposedAction = "proposed_action", review, approval, grant, receipt
}

public enum ProductDestinationClass: String, Codable, CaseIterable, Sendable {
    case thisDevice = "this_device"
    case pairedDevice = "paired_device"
    case privateEndpoint = "private_endpoint"
    case externalService = "external_service"
}

public enum ProductDecisionKind: String, Codable, CaseIterable, Sendable {
    case review, approval, grant
}

public enum ControlMode: String, Codable, CaseIterable, Sendable {
    case safe, neutral, yolo
}

public struct ProductLanguageTerm: Codable, Equatable, Sendable {
    public let singular: String
    public let plural: String
    public let category: String
    public let meaning: String
}

public struct ProductLanguageException: Codable, Equatable, Sendable {
    public let path: String
    public let terms: [String]
    public let reason: String
}

public struct ProductLanguageRegistry: Codable, Equatable, Sendable {
    public let registryVersion: Int
    public let product: String
    public let terms: [String: ProductLanguageTerm]
    public let legacyAliases: [String: String]
    public let lifecycleAxes: [String: [String]]
    public let destinationClasses: [ProductDestinationClass]
    public let decisionKinds: [ProductDecisionKind]
    public let controlModes: [ControlMode]
    public let meetingProjections: [String]
    public let guardedTerms: [String]
    public let compatibilityExceptions: [ProductLanguageException]

    private enum CodingKeys: String, CodingKey {
        case registryVersion, product, terms, legacyAliases, lifecycleAxes
        case destinationClasses, decisionKinds, controlModes, meetingProjections
        case guardedTerms, compatibilityExceptions
    }

    public func canonicalTerm(for value: String) throws -> CanonicalProductTerm {
        let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased().replacingOccurrences(of: "-", with: "_")
            .replacingOccurrences(of: " ", with: "_")
        let resolved = terms[normalized] == nil ? legacyAliases[normalized] : normalized
        guard let resolved, terms[resolved] != nil,
              let term = CanonicalProductTerm(rawValue: resolved) else {
            throw ProductLanguageError.unknownTerm(value)
        }
        return term
    }
}

public enum ProductLanguageError: Error, Equatable {
    case unknownTerm(String)
}

public enum ProductLanguage {
    public static let version = 1

    public static let labels: [CanonicalProductTerm: (singular: String, plural: String)] = [
        .desk: ("Desk", "Desks"), .meeting: ("Meeting", "Meetings"),
        .transcript: ("Transcript", "Transcripts"), .actionItem: ("Action item", "Action items"),
        .result: ("Result", "Results"), .artifact: ("Artifact", "Artifacts"),
        .note: ("Note", "Notes"), .zone: ("Zone", "Zones"),
        .knowledge: ("Knowledge", "Knowledge collections"), .project: ("Project", "Projects"),
        .persona: ("Persona", "Personas"), .coderSession: ("Coder session", "Coder sessions"),
        .workflow: ("Workflow", "Workflows"), .sequence: ("Sequence", "Sequences"),
        .integration: ("Integration", "Integrations"), .runsOn: ("Runs on", "Runs on"),
        .proposedAction: ("Proposed action", "Proposed actions"), .review: ("Review", "Reviews"),
        .approval: ("Approval", "Approvals"), .grant: ("Grant", "Grants"),
        .receipt: ("Receipt", "Receipts")
    ]

    public static let legacyAliases: [String: CanonicalProductTerm] = [
        "agent": .persona, "recipe": .persona, "coder": .coderSession,
        "directory": .zone, "folder": .zone, "kb": .knowledge,
        "knowledge_base": .knowledge, "chain": .sequence,
        "connector": .integration, "plugin": .integration, "profile": .runsOn
    ]

    public static let lifecycleAxes: [String: [String]] = [
        "readiness": ["unconfigured", "configured", "ready", "unavailable"],
        "availability": ["offline", "connecting", "available", "degraded"],
        "sync": ["local_only", "pending_sync", "synced", "sync_error"],
        "work": ["queued", "running", "succeeded", "failed", "cancelled"],
        "review": ["unreviewed", "accepted", "dismissed"],
        "authority": ["not_requested", "proposed", "approved", "rejected", "expired", "revoked"],
        "attention": ["unseen", "needs_attention", "acknowledged", "resolved"]
    ]

    public static let meetingProjections = ["summary", "action_items", "transcript", "topics"]

    public static func label(_ term: CanonicalProductTerm, plural: Bool = false) -> String {
        guard let value = labels[term] else { preconditionFailure("Missing product-language label: \(term)") }
        return plural ? value.plural : value.singular
    }

    public static func canonicalTerm(for value: String) throws -> CanonicalProductTerm {
        let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased().replacingOccurrences(of: "-", with: "_")
            .replacingOccurrences(of: " ", with: "_")
        if let term = CanonicalProductTerm(rawValue: normalized) { return term }
        if let term = legacyAliases[normalized] { return term }
        throw ProductLanguageError.unknownTerm(value)
    }
}
