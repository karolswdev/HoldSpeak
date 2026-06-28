import Foundation

// HSM-18-01 — the rest of the dictation pipeline surface the iPad never called: blocks (CRUD),
// block-templates, and project-context. Modeled faithfully against
// holdspeak/web/routes/dictation/blocks.py + agent.py + _helpers.py. Decoded with
// HoldSpeakContracts.decoder() (.convertFromSnakeCase), so the snake_case wire
// (default_match_confidence, requires_project, sample_utterance, project_kb) maps to these camelCase
// properties automatically. Lenient (most fields optional / open blobs) so a hub shape drift degrades
// gracefully on the dictate screen rather than throwing.

// MARK: - Blocks

/// The match clause of a dictation block (`block.match` in blocks.yaml). Open-ended by design — the
/// hub validates the real shape; the iPad keeps the known knobs typed and the rest as a raw blob so a
/// richer match config still round-trips.
public struct DictationBlockMatch: Codable, Sendable, Equatable {
    public var examples: [String]?
    public var negativeExamples: [String]?
    public var threshold: Double?

    public init(examples: [String]? = nil, negativeExamples: [String]? = nil, threshold: Double? = nil) {
        self.examples = examples
        self.negativeExamples = negativeExamples
        self.threshold = threshold
    }
}

/// The inject clause of a dictation block (`block.inject`). `mode` is "append" / "replace" / etc. on
/// the hub; kept as a string so a new mode does not break decoding.
public struct DictationBlockInject: Codable, Sendable, Equatable {
    public var mode: String?
    public var template: String?

    public init(mode: String? = nil, template: String? = nil) {
        self.mode = mode
        self.template = template
    }
}

/// One dictation block (an entry in `document.blocks`). `id` is the only field the hub guarantees;
/// everything else is optional so a partial / future block still decodes.
public struct DictationBlock: Codable, Sendable, Equatable, Identifiable {
    public var id: String
    public var description: String?
    public var match: DictationBlockMatch?
    public var inject: DictationBlockInject?

    public init(id: String, description: String? = nil,
                match: DictationBlockMatch? = nil, inject: DictationBlockInject? = nil) {
        self.id = id
        self.description = description
        self.match = match
        self.inject = inject
    }
}

/// The raw blocks document (`document` in the blocks-list envelope): the YAML mapping the hub reads
/// back, with the defaults it fills in (`version`, `default_match_confidence`, `blocks`).
public struct DictationBlocksDocument: Codable, Sendable, Equatable {
    public var version: Int?
    public var defaultMatchConfidence: Double?
    public var blocks: [DictationBlock]

    public init(version: Int? = nil, defaultMatchConfidence: Double? = nil, blocks: [DictationBlock] = []) {
        self.version = version
        self.defaultMatchConfidence = defaultMatchConfidence
        self.blocks = blocks
    }

    enum CodingKeys: String, CodingKey {
        case version, defaultMatchConfidence, blocks
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        version = try c.decodeIfPresent(Int.self, forKey: .version)
        defaultMatchConfidence = try c.decodeIfPresent(Double.self, forKey: .defaultMatchConfidence)
        blocks = try c.decodeIfPresent([DictationBlock].self, forKey: .blocks) ?? []
    }
}

/// The `GET /api/dictation/blocks` envelope: the resolved scope/path, whether the file exists, the
/// optional project context, and the parsed document.
public struct DictationBlocksResult: Codable, Sendable, Equatable {
    public var scope: String?
    public var path: String?
    public var exists: Bool?
    public var project: DictationProjectInfo?
    public var document: DictationBlocksDocument

    public init(scope: String? = nil, path: String? = nil, exists: Bool? = nil,
                project: DictationProjectInfo? = nil,
                document: DictationBlocksDocument = .init()) {
        self.scope = scope
        self.path = path
        self.exists = exists
        self.project = project
        self.document = document
    }

    enum CodingKeys: String, CodingKey {
        case scope, path, exists, project, document
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        scope = try c.decodeIfPresent(String.self, forKey: .scope)
        path = try c.decodeIfPresent(String.self, forKey: .path)
        exists = try c.decodeIfPresent(Bool.self, forKey: .exists)
        project = try c.decodeIfPresent(DictationProjectInfo.self, forKey: .project)
        document = try c.decodeIfPresent(DictationBlocksDocument.self, forKey: .document) ?? .init()
    }
}

// MARK: - Block templates

/// One starter block template (`GET /api/dictation/block-templates` -> `templates[]`). The metadata
/// is typed; the `block` payload is the same open shape as a saved block.
public struct DictationBlockTemplate: Codable, Sendable, Equatable, Identifiable {
    public var id: String
    public var title: String?
    public var description: String?
    public var sampleUtterance: String?
    public var requiresProject: Bool?
    public var block: DictationBlock?

    public init(id: String, title: String? = nil, description: String? = nil,
                sampleUtterance: String? = nil, requiresProject: Bool? = nil,
                block: DictationBlock? = nil) {
        self.id = id
        self.title = title
        self.description = description
        self.sampleUtterance = sampleUtterance
        self.requiresProject = requiresProject
        self.block = block
    }
}

// MARK: - Project context

/// The detected/manual project the dictation APIs resolved (`project` in the responses). `anchor` is
/// "manual" for a hand-picked root; otherwise the detector's anchor file.
public struct DictationProjectInfo: Codable, Sendable, Equatable {
    public var name: String?
    public var root: String?
    public var anchor: String?

    public init(name: String? = nil, root: String? = nil, anchor: String? = nil) {
        self.name = name
        self.root = root
        self.anchor = anchor
    }
}

/// The on-disk config paths the hub reports for the active project
/// (`GET /api/dictation/project-context` -> `paths`).
public struct DictationProjectPaths: Codable, Sendable, Equatable {
    public var blocks: String?
    public var projectKb: String?

    public init(blocks: String? = nil, projectKb: String? = nil) {
        self.blocks = blocks
        self.projectKb = projectKb
    }
}

/// `GET /api/dictation/project-context`: the resolved project plus its config paths. Lets the iPad
/// confirm which project the dictation pipeline is grounded in before it routes a single word.
public struct DictationProjectContext: Codable, Sendable, Equatable {
    public var project: DictationProjectInfo
    public var paths: DictationProjectPaths?

    public init(project: DictationProjectInfo = .init(), paths: DictationProjectPaths? = nil) {
        self.project = project
        self.paths = paths
    }

    enum CodingKeys: String, CodingKey {
        case project, paths
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        project = try c.decodeIfPresent(DictationProjectInfo.self, forKey: .project) ?? .init()
        paths = try c.decodeIfPresent(DictationProjectPaths.self, forKey: .paths)
    }
}
