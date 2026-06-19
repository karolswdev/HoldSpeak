import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

/// HSM-10-02 — the sync transport: an `ISyncProvider` over plain HTTP to the user's
/// own peer (HoldSpeak Desktop / homelab), reached directly over their network
/// (e.g. Tailscale) — no hosted relay. `push` POSTs a change-set; `pull` GETs the
/// peer's. One implementation of the seam, so swapping it never touches the Runtime
/// Core. Offline tolerance is the queue's job (`SyncQueue`); this type just does the
/// round-trip and fails honestly when the peer is unreachable.
public struct HTTPSyncProvider: ISyncProvider {
    public struct Config: Sendable, Equatable {
        public var baseURL: URL
        public var apiKey: String?
        public var timeout: TimeInterval
        public init(baseURL: URL, apiKey: String? = nil, timeout: TimeInterval = 30) {
            self.baseURL = baseURL
            self.apiKey = apiKey
            self.timeout = timeout
        }
    }

    public enum SyncTransportError: Error, Equatable {
        case http(status: Int)
        case malformedResponse
    }

    let config: Config
    let session: URLSession

    public init(config: Config, session: URLSession = .shared) {
        self.config = config
        self.session = session
    }

    /// Honest egress descriptor for the badge: sync leaves the device for a LAN peer.
    public var egressLabel: String { "local + LAN → \(config.baseURL.host ?? config.baseURL.absoluteString)" }

    public func push(_ changeSet: ChangeSet) async throws {
        var request = makeRequest(path: "api/sync/push", method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try HoldSpeakContracts.encoder().encode(changeSet)
        let (_, response) = try await session.data(for: request)
        try check(response)
    }

    public func pull() async throws -> ChangeSet {
        let request = makeRequest(path: "api/sync/pull", method: "GET")
        let (data, response) = try await session.data(for: request)
        try check(response)
        do { return try HoldSpeakContracts.decoder().decode(ChangeSet.self, from: data) }
        catch { throw SyncTransportError.malformedResponse }
    }

    private func makeRequest(path: String, method: String) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let apiKey = config.apiKey, !apiKey.isEmpty {
            request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    private func check(_ response: URLResponse) throws {
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw SyncTransportError.http(status: http.statusCode)
        }
    }
}
