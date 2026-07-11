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
    public let id: String
    public let registryVersion: Int
    public let kind: String
    public let path: String
    public let terms: [String]
    public let reason: String
}

public struct ProductCopyPattern: Codable, Equatable, Sendable {
    public let id: String
    public let pattern: String
    public let reason: String
}

public struct ProductCopyException: Codable, Equatable, Sendable {
    public let id: String
    public let path: String
    public let literals: [String]
    public let reason: String
}

public struct ProductCopyContract: Codable, Equatable, Sendable {
    public let version: Int
    public let classifications: [String]
    public let genericConsequentialVerbs: [String]
    public let prohibitedOperationalPatterns: [ProductCopyPattern]
    public let failureRequirements: [String]
    public let primarySurfaces: [String: [String]]
    public let exceptions: [ProductCopyException]
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
    public let controlModeLabels: [String: String]
    public let controlModeDescriptions: [String: String]
    public let destinationClassLabels: [String: String]
    public let lifecycleLabels: [String: [String: String]]
    public let meetingProjections: [String]
    public let guardedTerms: [String]
    public let copyContract: ProductCopyContract
    public let compatibilityExceptions: [ProductLanguageException]

    private enum CodingKeys: String, CodingKey {
        case registryVersion, product, terms, legacyAliases, lifecycleAxes
        case destinationClasses, decisionKinds, controlModes, meetingProjections
        case controlModeLabels, controlModeDescriptions, destinationClassLabels
        case lifecycleLabels, guardedTerms, copyContract, compatibilityExceptions
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
    public static let version = 2

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

    public static let controlModeLabels: [ControlMode: String] = [
        .safe: "Secure", .neutral: "Normal", .yolo: "YOLO"
    ]

    public static let controlModeDescriptions: [ControlMode: String] = [
        .safe: "Reviews consequential work before it runs.",
        .neutral: "Runs routine configured work and asks at consequential boundaries.",
        .yolo: "Runs eligible configured work without HoldSpeak approval prompts."
    ]

    public static let destinationClassLabels: [ProductDestinationClass: String] = [
        .thisDevice: "This device", .pairedDevice: "Paired device",
        .privateEndpoint: "Private endpoint", .externalService: "External service"
    ]

    public static let lifecycleLabels: [String: [String: String]] = [
        "readiness": [
            "unconfigured": "Not set up", "configured": "Configured",
            "ready": "Ready", "unavailable": "Unavailable"
        ],
        "availability": [
            "offline": "Offline", "connecting": "Connecting",
            "available": "Available", "degraded": "Degraded"
        ],
        "sync": [
            "local_only": "This device only", "pending_sync": "Pending sync",
            "synced": "Synced", "sync_error": "Sync failed"
        ],
        "work": [
            "queued": "Queued", "running": "Running", "succeeded": "Succeeded",
            "failed": "Failed", "cancelled": "Cancelled"
        ],
        "review": [
            "unreviewed": "Needs review", "accepted": "Accepted", "dismissed": "Dismissed"
        ],
        "authority": [
            "not_requested": "No authority requested", "proposed": "Needs approval",
            "approved": "Approved", "rejected": "Rejected", "expired": "Expired",
            "revoked": "Revoked"
        ],
        "attention": [
            "unseen": "New", "needs_attention": "Needs attention",
            "acknowledged": "Acknowledged", "resolved": "Resolved"
        ]
    ]

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

    public static func controlMode(for value: String) throws -> ControlMode {
        let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if let mode = ControlMode(rawValue: normalized) { return mode }
        if let mode = controlModeLabels.first(where: { $0.value.lowercased() == normalized })?.key {
            return mode
        }
        throw ProductLanguageError.unknownTerm(value)
    }

    public static func controlModeLabel(_ value: String) -> String {
        guard let mode = try? controlMode(for: value), let label = controlModeLabels[mode] else {
            return value
        }
        return label
    }

    public static func controlModeDescription(_ value: String) -> String? {
        guard let mode = try? controlMode(for: value) else { return nil }
        return controlModeDescriptions[mode]
    }

    public static func destinationClassLabel(_ value: ProductDestinationClass) -> String {
        guard let label = destinationClassLabels[value] else {
            preconditionFailure("Missing destination-class label: \(value.rawValue)")
        }
        return label
    }

    public static func lifecycleLabel(axis: String, value: String) -> String? {
        lifecycleLabels[axis]?[value]
    }
}
