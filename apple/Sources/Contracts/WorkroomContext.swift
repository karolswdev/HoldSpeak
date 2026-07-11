import Foundation

/// Identity and orientation for a focused room entered from the Desk.
///
/// The wire shape carries references only. Authored speech, prompts, bodies,
/// and transcripts are deliberately outside this contract and outside URLs.
public struct WorkroomContext: Codable, Equatable, Sendable {
    public static let currentVersion = 1

    public enum Origin: String, Codable, Sendable { case desk }
    public enum ReturnDestination: String, Codable, Sendable { case desk }

    public let version: Int
    public let origin: Origin
    public let subjectRef: QualifiedRef?
    public let action: String
    public let draftRef: QualifiedRef?
    public let runRef: QualifiedRef?
    public let returnTo: ReturnDestination
    public let returnRef: QualifiedRef?

    public init?(
        version: Int = WorkroomContext.currentVersion,
        origin: Origin = .desk,
        subjectRef: QualifiedRef? = nil,
        action: String,
        draftRef: QualifiedRef? = nil,
        runRef: QualifiedRef? = nil,
        returnTo: ReturnDestination = .desk,
        returnRef: QualifiedRef? = nil
    ) {
        guard (1...999).contains(version), Self.validAction(action) else { return nil }
        self.version = version
        self.origin = origin
        self.subjectRef = subjectRef
        self.action = action
        self.draftRef = draftRef
        self.runRef = runRef
        self.returnTo = returnTo
        self.returnRef = returnRef ?? subjectRef
    }

    private enum CodingKeys: String, CodingKey {
        case version, origin, action
        case subjectRef = "subject_ref"
        case draftRef = "draft_ref"
        case runRef = "run_ref"
        case returnTo = "return_to"
        case returnRef = "return_ref"
    }

    private struct AnyKey: CodingKey {
        let stringValue: String
        let intValue: Int? = nil
        init?(stringValue: String) { self.stringValue = stringValue }
        init?(intValue: Int) { return nil }
    }

    public init(from decoder: Decoder) throws {
        let all = try decoder.container(keyedBy: AnyKey.self)
        let contentKeys: Set<String> = [
            "body", "content", "draft", "input", "prompt", "text",
            "transcript", "utterance",
        ]
        guard !all.allKeys.contains(where: { contentKeys.contains($0.stringValue.lowercased()) }) else {
            throw DecodingError.dataCorrupted(
                .init(codingPath: decoder.codingPath,
                      debugDescription: "Workroom context cannot contain authored content")
            )
        }

        let values = try decoder.container(keyedBy: CodingKeys.self)
        let version = try values.decodeIfPresent(Int.self, forKey: .version) ?? Self.currentVersion
        let origin = try values.decode(Origin.self, forKey: .origin)
        let subject = try values.decodeIfPresent(QualifiedRef.self, forKey: .subjectRef)
        let action = try values.decode(String.self, forKey: .action)
        let draft = try values.decodeIfPresent(QualifiedRef.self, forKey: .draftRef)
        let run = try values.decodeIfPresent(QualifiedRef.self, forKey: .runRef)
        let returnTo = try values.decode(ReturnDestination.self, forKey: .returnTo)
        let returnRef = try values.decodeIfPresent(QualifiedRef.self, forKey: .returnRef)
        guard let valid = WorkroomContext(
            version: version, origin: origin, subjectRef: subject, action: action,
            draftRef: draft, runRef: run, returnTo: returnTo, returnRef: returnRef
        ) else {
            throw DecodingError.dataCorrupted(
                .init(codingPath: decoder.codingPath,
                      debugDescription: "Invalid workroom identity context")
            )
        }
        self = valid
    }

    private static func validAction(_ value: String) -> Bool {
        value.range(
            of: #"^[a-z][a-z0-9._-]{0,63}$"#,
            options: .regularExpression
        ) != nil
    }
}
