import Foundation

/// HS-92-07 — the canonical destination identity presented as "Runs on".
/// RuntimeProfile remains the v1 synced alias; this view keeps placement apart
/// from engine/model selection and never carries secret material.
public struct InferenceTarget: Codable, Equatable, Sendable, Identifiable {
    public enum Kind: String, Codable, Sendable {
        case thisDevice = "this_device"
        case pairedDevice = "paired_device"
        case privateEndpoint = "private_endpoint"
        case meshNode = "mesh_node"
        case externalService = "external_service"
        case unsupported
    }

    public struct Readiness: Codable, Equatable, Sendable {
        public var state: String
        public var available: Bool
        public var reason: String
        public init(state: String = "ready", available: Bool = true, reason: String = "") {
            self.state = state; self.available = available; self.reason = reason
        }
    }

    public struct DataScope: Codable, Equatable, Sendable {
        public var sent: [String]
        public var returned: [String]
        public init(sent: [String] = ["instruction", "selected_context", "grounding"],
                    returned: [String] = ["generated_output"]) {
            self.sent = sent; self.returned = returned
        }
    }

    public var version: Int
    public var id: String
    public var profileId: String?
    public var name: String
    public var kind: Kind
    public var boundary: String
    public var owner: String
    public var transport: String
    public var dataScope: DataScope
    public var engine: String
    public var model: String
    public var contextLimit: Int
    public var readiness: Readiness

    public init(version: Int = 1, id: String, profileId: String?, name: String,
                kind: Kind, boundary: String, owner: String, transport: String,
                dataScope: DataScope = DataScope(), engine: String, model: String,
                contextLimit: Int, readiness: Readiness = Readiness()) {
        self.version = version; self.id = id; self.profileId = profileId; self.name = name
        self.kind = kind; self.boundary = boundary; self.owner = owner
        self.transport = transport; self.dataScope = dataScope; self.engine = engine
        self.model = model; self.contextLimit = contextLimit; self.readiness = readiness
    }

    public static let thisDevice = InferenceTarget(
        id: "this_machine", profileId: nil, name: "This device", kind: .thisDevice,
        boundary: "same_device", owner: "you", transport: "in_process",
        engine: "local", model: "", contextLimit: 16_384
    )
}

public struct InferencePlacementReceipt: Codable, Equatable, Sendable {
    public var targetId: String
    public var targetName: String
    public var targetKind: String
    public var boundary: String
    public var owner: String
    public var transport: String
    public var dataClasses: [String]
    public var engine: String
    public var model: String
    public var fallbackReason: String?
}

public extension RuntimeProfile {
    /// Pure v1 Profile → InferenceTarget adapter. Callers supply readiness facts
    /// already held locally; this function never probes a destination.
    func inferenceTarget(keyPresent: Bool = false, paired: Bool = true,
                         modelAdvertised: Bool = true, nodeLive: Bool = true) -> InferenceTarget {
        var readiness = InferenceTarget.Readiness()
        let mapped: (InferenceTarget.Kind, String, String, String, String)
        switch kind {
        case .onDevice:
            mapped = (.thisDevice, "same_device", "you", "in_process", "local")
        case .desktop:
            mapped = (.pairedDevice, "paired_device", "you", "paired_https", "paired_runtime")
            if !paired {
                readiness = .init(state: "offline", available: false,
                                  reason: "Paired device is not connected")
            } else if !modelAdvertised {
                readiness = .init(state: "stale_manifest", available: false,
                                  reason: "Paired device no longer advertises model '\(model)'")
            }
        case .meshNode:
            mapped = (.meshNode, "private_mesh", "you", "mesh_relay", "node_runtime")
            if node.isEmpty || !nodeLive {
                readiness = .init(state: "offline", available: false,
                                  reason: node.isEmpty ? "Destination names no mesh node" : "Mesh node '\(node)' is offline")
            }
        case .openAICompatible:
            let host = URL(string: baseURL)?.host?.lowercased() ?? ""
            let privateHost = host == "localhost" || host.hasSuffix(".local")
                || host.hasPrefix("10.") || host.hasPrefix("192.168.")
                || (host.hasPrefix("172.") && (16...31).contains(Int(host.split(separator: ".").dropFirst().first ?? "0") ?? 0))
            mapped = privateHost
                ? (.privateEndpoint, "private_network", "you", "https", "openai_compatible")
                : (.externalService, "external_service", "service_provider", "https", "openai_compatible")
            if host.isEmpty {
                readiness = .init(state: "unsupported", available: false,
                                  reason: "Destination '\(name)' has no valid endpoint URL")
            } else if requiresKey && !keyPresent {
                readiness = .init(state: "needs_key", available: false,
                                  reason: "Destination '\(name)' needs its Keychain key")
            }
        }
        return InferenceTarget(id: id, profileId: id, name: name, kind: mapped.0,
                               boundary: mapped.1, owner: mapped.2, transport: mapped.3,
                               engine: mapped.4, model: model.isEmpty ? modelFile : model,
                               contextLimit: contextLimit, readiness: readiness)
    }
}
