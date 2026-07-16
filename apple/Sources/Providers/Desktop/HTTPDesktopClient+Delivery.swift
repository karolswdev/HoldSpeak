import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HS-94-09 — the native Desk reads the v2 Delivery Runtime (§10 hub API):
// the coherent snapshot, the source registry view, node presence, work
// attempts, and story dossiers. Read-only, byte-honest: the desk renders
// what the hub said, never scrapes. New extension file by the equilibrium
// conflict rule — no edits to HTTPDesktopClient.swift; own request helpers
// (the +Ask / +MissionControl precedent).

/// A dossier refusal surfaced as a TYPED error: the hub's 404/409/413/503
/// bodies carry `{refusal, detail, manifest?}` — the caller reads the code
/// and, on bundle_changed / hash_mismatch, keeps rendering the preserved
/// manifest metadata (§13) while re-fetching.
public struct DeliveryRefusalError: Error, Equatable, Sendable {
    public var refusal: DeliveryRefusal
    public init(_ refusal: DeliveryRefusal) { self.refusal = refusal }
}

extension HTTPDesktopClient {

    /// `GET /api/delivery/snapshot` — the coherent cached read model
    /// (delivery_schema: 1): one revision, one opaque replayable cursor,
    /// every registered source with typed freshness.
    public func deliverySnapshot() async throws -> DeliverySnapshot {
        let data = try await sendDelivery(makeDeliveryRequest(path: "api/delivery/snapshot"))
        guard let snap = try? HoldSpeakContracts.decoder().decode(DeliverySnapshot.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return snap
    }

    /// `GET /api/delivery/sources` — registry + freshness (registry_schema: 1):
    /// labels, opaque IDs, fingerprints, typed statuses. Never a path.
    public func deliverySources() async throws -> DeliverySourcesView {
        let data = try await sendDelivery(makeDeliveryRequest(path: "api/delivery/sources"))
        guard let view = try? HoldSpeakContracts.decoder().decode(DeliverySourcesView.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return view
    }

    /// `GET /api/delivery/nodes` — node presence (nodes_schema: 1): typed
    /// liveness with last-seen retained; legacy-direct rows labeled honestly.
    public func deliveryNodes() async throws -> DeliveryNodesView {
        let data = try await sendDelivery(makeDeliveryRequest(path: "api/delivery/nodes"))
        guard let view = try? HoldSpeakContracts.decoder().decode(DeliveryNodesView.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return view
    }

    /// `GET /api/delivery/attempts` — durable work attempts (attempts_schema: 1)
    /// with explicit provenance, honest states, and replayable history.
    public func deliveryAttempts(sourceId: String? = nil, project: String? = nil,
                                 storyId: String? = nil, sessionId: String? = nil,
                                 activeOnly: Bool = false) async throws -> WorkAttemptsView {
        var query: [String] = []
        if let v = sourceId, !v.isEmpty { query.append("source_id=\(deliveryEncoded(v))") }
        if let v = project, !v.isEmpty { query.append("project=\(deliveryEncoded(v))") }
        if let v = storyId, !v.isEmpty { query.append("story_id=\(deliveryEncoded(v))") }
        if let v = sessionId, !v.isEmpty { query.append("session_id=\(deliveryEncoded(v))") }
        if activeOnly { query.append("active_only=true") }
        var path = "api/delivery/attempts"
        if !query.isEmpty { path += "?" + query.joined(separator: "&") }
        let data = try await sendDelivery(makeDeliveryRequest(path: path))
        guard let view = try? HoldSpeakContracts.decoder().decode(WorkAttemptsView.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return view
    }

    /// `GET /api/delivery/stories/{project}/{story}/dossier` — the story
    /// dossier (dossier_schema: 1). `source` pins one source; omitted, the
    /// hub tries every registered source. A typed refusal (404/409/413/503
    /// `{refusal, detail, manifest?}`) throws `DeliveryRefusalError` so the
    /// caller keeps the §13-preserved manifest; any other failure is
    /// `DesktopClientError`.
    public func storyDossier(project: String, story: String,
                             source: String? = nil) async throws -> StoryDossier {
        var path = "api/delivery/stories/\(deliveryEncoded(project))/\(deliveryEncoded(story))/dossier"
        if let s = source, !s.isEmpty { path += "?source=\(deliveryEncoded(s))" }
        let (data, status) = try await sendDeliveryRaw(makeDeliveryRequest(path: path))
        if (200...299).contains(status) {
            guard let dossier = try? HoldSpeakContracts.decoder().decode(StoryDossier.self, from: data) else {
                throw DesktopClientError.malformed
            }
            return dossier
        }
        if let refusal = try? HoldSpeakContracts.decoder().decode(DeliveryRefusal.self, from: data) {
            throw DeliveryRefusalError(refusal)
        }
        throw DesktopClientError.http(status)
    }

    // MARK: - internals (mirror the +MissionControl request helpers)

    private func deliveryEncoded(_ s: String) -> String {
        s.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? s
    }

    private func sendDelivery(_ request: URLRequest) async throws -> Data {
        let (data, status) = try await sendDeliveryRaw(request)
        if !(200...299).contains(status) {
            throw DesktopClientError.http(status)
        }
        return data
    }

    private func sendDeliveryRaw(_ request: URLRequest) async throws -> (Data, Int) {
        let (data, response) = try await session.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 200
        return (data, status)
    }

    private func makeDeliveryRequest(path: String) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = "GET"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }
}
