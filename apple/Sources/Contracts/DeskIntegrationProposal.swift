import Foundation

/// One external-effect proposal initiated from selected Desk material.
///
/// The source reference is identity only. It binds the host Receipt to the
/// originating Meeting, Note, or Artifact without placing authored material in
/// a URL or granting authority. The host resolves the canonical source label.
public struct DeskIntegrationProposalRequest: Codable, Equatable, Sendable {
    public let text: String
    public let title: String?
    public let sourceRef: QualifiedRef?
    public let sourceLabel: String?

    public init(
        text: String,
        title: String? = nil,
        sourceRef: QualifiedRef? = nil,
        sourceLabel: String? = nil
    ) {
        self.text = text
        self.title = title
        self.sourceRef = sourceRef
        self.sourceLabel = sourceLabel
    }

    private enum CodingKeys: String, CodingKey {
        case text, title
        case sourceRef = "source_ref"
        case sourceLabel = "source_label"
    }
}
