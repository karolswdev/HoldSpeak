import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-12-01 — the desktop client seam + pairing. The spine of the Companion track
// (charter Amendment 1.1, Track M): point an iPhone/iPad at the same server a coding
// session runs against, and drive it over the desktop's existing HTTP API. This file
// is connect / health / egress only; the verb methods (meetings remote control,
// remote-dictation inject) are added by the stories that need them (HSM-12-02 / 13).

/// How the device is paired to a desktop/homelab peer: host + port + an optional
/// token, over the user's own network (LAN / Tailscale) — no hosted relay. This is
/// the "configure a desktop peer" surface; the shell turns it into a `Config`.
public struct DesktopPeer: Sendable, Equatable {
    public var host: String
    public var port: Int
    /// Bearer token for the desktop API. A credential — joined at call time, never
    /// logged, never echoed back to the UI (mirrors the Phase-61 Slack discipline).
    public var token: String?
    /// "http" over a trusted LAN/Tailscale by default; "https" when the peer has TLS.
    public var scheme: String

    public init(host: String, port: Int, token: String? = nil, scheme: String = "http") {
        self.host = host
        self.port = port
        self.token = token
        self.scheme = scheme
    }

    /// The peer's base URL; `nil` when host/port are malformed (an empty host or a
    /// non-positive port — a half-filled pairing form), so the client then stays
    /// permanently offline rather than building a junk URL. Fail soft, never crash.
    public var baseURL: URL? {
        let trimmed = host.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty, port > 0 else { return nil }
        var c = URLComponents()
        c.scheme = scheme
        c.host = trimmed
        c.port = port
        return c.url
    }
}

/// The result of probing the peer. **Never an error** — an unreachable desktop is a
/// rendered state, so the caller needs no try/catch and the on-device runtime is
/// never gated on it.
public struct DesktopConnection: Sendable, Equatable {
    public var reachable: Bool
    public var runtimeReady: Bool
    /// A short, human-readable detail for the UI (e.g. "ready · web", "meeting
    /// active", "desktop unreachable: <reason>"). Never carries the token.
    public var detail: String

    public init(reachable: Bool, runtimeReady: Bool, detail: String) {
        self.reachable = reachable
        self.runtimeReady = runtimeReady
        self.detail = detail
    }

    /// The peer could not be reached at all (network down, bad host, timeout).
    public static func offline(_ reason: String) -> DesktopConnection {
        DesktopConnection(reachable: false, runtimeReady: false, detail: "desktop unreachable: \(reason)")
    }
}

/// `IDesktopClient` over plain HTTP to the user's own desktop/homelab peer, reached
/// directly over their network — the same endpoints the web portal uses. One
/// implementation of the seam, so swapping it never touches the Runtime Core.
public struct HTTPDesktopClient: IDesktopClient {
    public struct Config: Sendable, Equatable {
        public var baseURL: URL
        public var token: String?
        public var timeout: TimeInterval
        public init(baseURL: URL, token: String? = nil, timeout: TimeInterval = 8) {
            self.baseURL = baseURL
            self.token = token
            self.timeout = timeout
        }

        /// Build a config from a paired peer; `nil` if the peer's URL is malformed.
        public init?(peer: DesktopPeer, timeout: TimeInterval = 8) {
            guard let url = peer.baseURL else { return nil }
            self.init(baseURL: url, token: peer.token, timeout: timeout)
        }
    }

    let config: Config
    let session: URLSession

    public init(config: Config, session: URLSession = .shared) {
        self.config = config
        self.session = session
    }

    public var egressLabel: String {
        "local + LAN → \(config.baseURL.host ?? config.baseURL.absoluteString)"
    }

    /// `GET /health` to confirm reachability, then `GET /api/runtime/status` to read
    /// runtime readiness. Any network failure maps to `.offline` — fail soft.
    public func handshake() async -> DesktopConnection {
        // 1) Reachability — /health returns {"status":"ok"}.
        do {
            let (_, response) = try await session.data(for: makeRequest(path: "health"))
            guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
                let code = (response as? HTTPURLResponse)?.statusCode ?? -1
                return .offline("health \(code)")
            }
        } catch {
            return .offline(Self.reason(error))
        }

        // 2) Readiness — /api/runtime/status. Reachable even if this is unavailable.
        do {
            let (data, response) = try await session.data(for: makeRequest(path: "api/runtime/status"))
            guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
                return DesktopConnection(reachable: true, runtimeReady: false, detail: "runtime status unavailable")
            }
            let status = (try? HoldSpeakContracts.decoder().decode(RuntimeStatusDTO.self, from: data)) ?? RuntimeStatusDTO()
            let ready = (status.status ?? "").lowercased() == "ok"
            return DesktopConnection(reachable: true, runtimeReady: ready, detail: status.summary)
        } catch {
            // Health passed but status call failed mid-flight: still reachable.
            return DesktopConnection(reachable: true, runtimeReady: false, detail: "runtime status unavailable")
        }
    }

    // MARK: - internals

    /// Loose decode of `/api/runtime/status` — every field optional so the client
    /// tolerates the desktop payload evolving (the codebase's robust-decode posture).
    /// Keys arrive snake_case and convert via the shared decoder (`meeting_active`).
    struct RuntimeStatusDTO: Decodable {
        var status: String?
        var mode: String?
        var meetingActive: Bool?

        var summary: String {
            if meetingActive == true { return "meeting active" }
            let s = status ?? "unknown"
            return mode.map { "\(s) · \($0)" } ?? s
        }
    }

    private func makeRequest(path: String) -> URLRequest {
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

    private static func reason(_ error: Error) -> String {
        if let url = error as? URLError { return "\(url.code)" }
        return "network error"
    }
}
