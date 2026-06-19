import Foundation

/// The 15 shipped artifact types (+ the plugin_output fallback), from the desktop
/// `plugins/synthesis.py` `_ARTIFACT_TYPE_BY_PLUGIN` map. Raw values are the wire
/// strings (key-conversion does not touch enum values).
public enum ArtifactType: String, Codable, Sendable, CaseIterable {
    case requirements
    case actionItems = "action_items"
    case diagram
    case decisions
    case adr
    case milestonePlan = "milestone_plan"
    case dependencyMap = "dependency_map"
    case scopeReview = "scope_review"
    case customerSignals = "customer_signals"
    case incidentTimeline = "incident_timeline"
    case riskRegister = "risk_register"
    case stakeholderUpdate = "stakeholder_update"
    case runbookDelta = "runbook_delta"
    case decisionAnnouncement = "decision_announcement"
    case projectAssociation = "project_association"
    case pluginOutput = "plugin_output"
}

public enum ArtifactStatus: String, Codable, Sendable {
    case draft
    case needsReview = "needs_review"
    case accepted
    case rejected
}

public enum ActionStatus: String, Codable, Sendable {
    case pending, done, dismissed
}

public enum ReviewState: String, Codable, Sendable {
    case pending, accepted
}

/// The MIR *meeting* routing profile. NOT the dictation `target_profile`
/// (contract §6 forbids a bare `profile`).
public enum MIRProfile: String, Codable, Sendable, CaseIterable {
    case balanced, architect, delivery, product, incident
}

public enum MIRIntent: String, Codable, Sendable, CaseIterable {
    case architecture, delivery, product, incident, comms
}

public enum ActuatorStatus: String, Codable, Sendable {
    case proposed, approved, executed, rejected, failed
}

public enum IntelProvider: String, Codable, Sendable {
    case local, cloud, auto
}
