import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-25-01 — the serving node's wire: the three token-guarded relay routes a
// mesh worker speaks (desktop HS-85-01). Claim stamps THIS node's liveness on
// every poll — the mesh's only heartbeat; complete/fail post the run's outcome
// verbatim. New extension file by design (the conflict rule).

/// One relayed run addressed to THIS node. Tolerant decode of the hub's
/// snake_case row; timestamps stay ISO strings (the timestamps rule).
public struct MeshRelayJob: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var node: String?
    public var taskKind: String?        // "llm" in v1
    public var systemPrompt: String?
    public var userPrompt: String?
    public var temperature: Double?
    public var maxTokens: Int?
    public var modelHint: String?
    public var deadlineAt: String?

    public init(id: String, node: String? = nil, taskKind: String? = nil,
                systemPrompt: String? = nil, userPrompt: String? = nil,
                temperature: Double? = nil, maxTokens: Int? = nil,
                modelHint: String? = nil, deadlineAt: String? = nil) {
        self.id = id; self.node = node; self.taskKind = taskKind
        self.systemPrompt = systemPrompt; self.userPrompt = userPrompt
        self.temperature = temperature; self.maxTokens = maxTokens
        self.modelHint = modelHint; self.deadlineAt = deadlineAt
    }
}

/// The whole envelope `POST /api/mesh/relay/claim` answers with: the oldest
/// queued job addressed to this node, or `job: null` when the queue is idle.
private struct MeshRelayClaimEnvelope: Codable {
    var job: MeshRelayJob?
}

extension HTTPDesktopClient {
    /// One worker poll: stamps this node's liveness hub-side (polling IS the
    /// heartbeat) and claims the oldest queued job addressed to it, or nil.
    public func claimMeshRelay(node: String) async throws -> MeshRelayJob? {
        let request = meshServeRequest(path: "api/mesh/relay/claim",
                                       jsonBody: ["node": node])
        let data = try await meshServeSend(request)
        do {
            return try HoldSpeakContracts.decoder()
                .decode(MeshRelayClaimEnvelope.self, from: data).job
        } catch { throw DesktopClientError.malformed }
    }

    /// Post the run's answer verbatim. A late answer (the job already expired
    /// hub-side) surfaces as `.http(409)` — the caller logs, never retries.
    public func completeMeshRelay(jobID: String, result: String) async throws {
        _ = try await meshServeSend(meshServeRequest(
            path: "api/mesh/relay/\(meshServeEscape(jobID))/complete",
            jsonBody: ["result": result]))
    }

    /// Report the node-side failure verbatim, so the caller's surface names it.
    public func failMeshRelay(jobID: String, error: String) async throws {
        _ = try await meshServeSend(meshServeRequest(
            path: "api/mesh/relay/\(meshServeEscape(jobID))/fail",
            jsonBody: ["error": error]))
    }

    // MARK: - internals (private to this extension, per the conflict rule)

    private func meshServeEscape(_ segment: String) -> String {
        segment.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? segment
    }

    private func meshServeSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func meshServeRequest(path: String, jsonBody: [String: String]) -> URLRequest {
        let absolute = config.baseURL.absoluteString
        let base = absolute.hasSuffix("/") ? String(absolute.dropLast()) : absolute
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = "POST"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: jsonBody)
        return request
    }
}
