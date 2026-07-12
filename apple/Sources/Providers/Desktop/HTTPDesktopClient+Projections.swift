import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

/// A non-sensitive read model over an authoritative desktop source record.
public struct DeskProjectionDTO: Codable, Equatable, Sendable, Identifiable {
    public var id: String
    public var projectionKind: String
    public var subjectRef: String
    public var subjectLabel: String
    public var title: String
    public var summary: String
    public var reasonCode: String
    public var decisionKind: String
    public var attentionState: String
    public var actualDestination: String?
    public var authorityBasis: String?
    public var attempt: Int?
    public var outcome: String
    public var timestamp: String
    public var correlationId: String?
    public var sourceKind: String
    public var sourceId: String
    public var sourceApi: String
    public var detailUrl: String
    public var controlMode: String?
    public var policyVersion: String?
    public var effectClass: String?
    public var severity: String
    public var dismissed: Bool
}

public struct DeskProjectionPage: Codable, Equatable, Sendable {
    public var offset: Int
    public var limit: Int
    public var total: Int
    public var hasMore: Bool
}

public struct DeskProjectionEnvelope: Codable, Equatable, Sendable {
    public var projections: [DeskProjectionDTO]
    public var counts: [String: Int]
    public var page: DeskProjectionPage
}

extension HTTPDesktopClient {
    public func deskProjections(offset: Int = 0, limit: Int = 50) async throws -> DeskProjectionEnvelope {
        let path = "api/desk/projections?offset=\(max(0, offset))&limit=\(max(1, min(limit, 200)))"
        return try await projectionSend(path: path)
    }

    public func updateProjectionPresentation(
        id: String, action: String
    ) async throws {
        let escaped = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        let request = try projectionRequest(
            path: "api/desk/projections/\(escaped)/presentation", method: "PUT",
            body: ["action": action]
        )
        let (_, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
    }

    private func projectionSend<T: Decodable>(
        path: String, method: String = "GET", body: [String: String]? = nil
    ) async throws -> T {
        let request = try projectionRequest(path: path, method: method, body: body)
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        do { return try HoldSpeakContracts.decoder().decode(T.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    private func projectionRequest(
        path: String, method: String, body: [String: String]?
    ) throws -> URLRequest {
        let base = config.baseURL.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        return request
    }
}
