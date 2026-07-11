import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-22-04 — run a WORKFLOW (the travelling graph) on the hub. New extension file
// by design (the equilibrium conflict rule): no edits to HTTPDesktopClient.swift.
// A graph run's `steps` are OBJECTS (node_id/kind/policy/status), not the chain
// run's strings, so this carries its own result type instead of `HubRunResult`.

/// One node of the hub's run trail. Every field optional (robust decode); the
/// timestamps rule holds — nothing here decodes as `Date`.
public struct HubWorkflowRunStep: Codable, Equatable, Sendable {
    public var nodeId: String?
    public var kind: String?
    public var provider: String?
    public var failurePolicy: String?
    public var runsOn: String?
    public var status: String?
}

/// The graph run's envelope: the threaded output, the per-node trail, the honest
/// legacy `warning` from older hubs, plus the
/// persisted run-born artifact id (reuse it — the 18-07 duplicate-on-sync lesson).
public struct HubWorkflowRunResult: Codable, Equatable, Sendable {
    public var output: String?
    public var provider: String?
    public var steps: [HubWorkflowRunStep]?
    public var warning: String?
    public var artifactId: String?
    public var resultRef: String?
    public var invocationId: String?
    public var correlationId: String?
    public var invocation: CapabilityInvocation?

    public init(output: String? = nil, provider: String? = nil,
                steps: [HubWorkflowRunStep]? = nil, warning: String? = nil,
                artifactId: String? = nil, resultRef: String? = nil,
                invocationId: String? = nil, correlationId: String? = nil,
                invocation: CapabilityInvocation? = nil) {
        self.output = output
        self.provider = provider
        self.steps = steps
        self.warning = warning
        self.artifactId = artifactId
        self.resultRef = resultRef
        self.invocationId = invocationId
        self.correlationId = correlationId
        self.invocation = invocation
    }
}

extension HTTPDesktopClient {

    /// `POST /api/workflows/{id}/run` body `{input}` → the graph run envelope. The
    /// hub runs its faithful subset and returns 409 before execution when unsupported;
    /// a non-2xx throws `DesktopClientError.http`.
    public func runWorkflow(id: String, input: String) async throws -> HubWorkflowRunResult {
        let data = try await sendWorkflowRun(makeWorkflowRunRequest(
            path: "api/workflows/\(id)/run",
            body: ["input": input, "inference_target_id": "paired_device"]))
        do { return try HoldSpeakContracts.decoder().decode(HubWorkflowRunResult.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (private to this extension, per the conflict rule)

    private func sendWorkflowRun(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeWorkflowRunRequest(path: String, body: [String: Any]) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = "POST"
        request.timeoutInterval = config.timeout
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        return request
    }
}
