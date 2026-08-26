import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// The opaque server-issued material that authorizes precisely one physical
/// companion transport. It intentionally names neither a deployment nor an
/// alternate route; that selection is frozen in the server reservation.
public struct AdmittedInferenceAttempt: Codable, Equatable, Sendable {
    public let schema: String
    public let authorization: String
    public let transport: AdmittedInferenceTransport

    public init(
        schema: String = "AppleAdmittedAttempt@1",
        authorization: String,
        transport: AdmittedInferenceTransport
    ) {
        self.schema = schema
        self.authorization = authorization
        self.transport = transport
    }

    public var isValid: Bool {
        schema == "AppleAdmittedAttempt@1" && !authorization.isEmpty
            && transport.schema == "AppleAdmittedTransport@1"
    }
}

public struct AdmittedInferenceTransport: Codable, Equatable, Sendable {
    public let schema: String
    public let beginPath: String
    public let reconcilePath: String

    public init(
        schema: String = "AppleAdmittedTransport@1",
        beginPath: String = "/api/inference/apple/attempts/begin",
        reconcilePath: String = "/api/inference/apple/attempts/reconcile"
    ) {
        self.schema = schema
        self.beginPath = beginPath
        self.reconcilePath = reconcilePath
    }

    enum CodingKeys: String, CodingKey { case schema, beginPath, reconcilePath }
}

/// Closed client-side observation vocabulary. The server maps these values to
/// the frozen route policy; this enum is not a retry or alternate-route API.
public enum AdmittedInferenceDisposition: String, Codable, Equatable, Sendable {
    case succeeded
    case malformedOutput = "malformed_output"
    case unavailable
    case disconnected
    case stopped
    case failed
}

public struct AdmittedInferenceReceipt: Codable, Equatable, Sendable {
    public let attemptID: String
    public let disposition: AdmittedInferenceDisposition
    public let terminal: Bool

    public init(attemptID: String, disposition: AdmittedInferenceDisposition, terminal: Bool) {
        self.attemptID = attemptID
        self.disposition = disposition
        self.terminal = terminal
    }

    enum CodingKeys: String, CodingKey { case attemptID = "attempt_id", disposition, terminal }
}

public enum AdmittedInferenceClientError: Error, Equatable, Sendable {
    case reservationRequired
    case reservationConsumed
    case malformedOutput
    case unavailable
    case disconnected
    case stopped
}

/// Only the application endpoint implements this protocol. A provider closure
/// cannot choose a path, dispatch before `begin`, or elect a next attempt.
public protocol AdmittedInferenceBridgeWire: Sendable {
    func begin(authorization: String) async throws
    func reconcile(
        authorization: String,
        disposition: AdmittedInferenceDisposition,
        result: String?
    ) async throws -> AdmittedInferenceReceipt
}

/// Typed error a named physical transport may throw. It carries no retry
/// instruction: the client only reports it once to the server controller.
public enum AdmittedInferenceTransportError: Error, Equatable, Sendable {
    case unavailable
    case disconnected
    case stopped
    case failed
}

/// One reservation, one named transport, one reconciliation. This actor is the
/// sole Swift location permitted to sequence those facts.
public actor AdmittedInferenceClient {
    private let wire: any AdmittedInferenceBridgeWire
    private var consumed: Set<String> = []

    public init(wire: any AdmittedInferenceBridgeWire) { self.wire = wire }

    public func perform(
        attempt: AdmittedInferenceAttempt?,
        transport: @Sendable () async throws -> String,
        validate: @Sendable (String) throws -> Void
    ) async throws -> String {
        guard let attempt, attempt.isValid else { throw AdmittedInferenceClientError.reservationRequired }
        guard !consumed.contains(attempt.authorization) else { throw AdmittedInferenceClientError.reservationConsumed }
        // `begin` is the server's durable pre-dispatch fence. Do not consume a
        // ticket if that request did not reach the server: no transport ran.
        try await wire.begin(authorization: attempt.authorization)
        consumed.insert(attempt.authorization)
        let raw: String
        do {
            raw = try await transport()
        } catch let error as AdmittedInferenceTransportError {
            let disposition: AdmittedInferenceDisposition = switch error {
            case .unavailable: .unavailable
            case .disconnected: .disconnected
            case .stopped: .stopped
            case .failed: .failed
            }
            _ = try await wire.reconcile(authorization: attempt.authorization, disposition: disposition, result: nil)
            throw error
        } catch {
            _ = try await wire.reconcile(authorization: attempt.authorization, disposition: .failed, result: nil)
            throw error
        }

        do {
            try validate(raw)
        } catch {
            _ = try await wire.reconcile(authorization: attempt.authorization, disposition: .malformedOutput, result: nil)
            throw error
        }
        _ = try await wire.reconcile(authorization: attempt.authorization, disposition: .succeeded, result: raw)
        return raw
    }
}

/// The production application wire. It speaks only the two narrow bridge
/// endpoints, never a database, route-plan, or controller ledger API.
public struct HTTPAdmittedInferenceBridgeWire: AdmittedInferenceBridgeWire, Sendable {
    public let baseURL: URL
    public let bearerToken: String?
    public let session: URLSession

    public init(baseURL: URL, bearerToken: String? = nil, session: URLSession = .shared) {
        self.baseURL = baseURL; self.bearerToken = bearerToken; self.session = session
    }

    public func begin(authorization: String) async throws {
        _ = try await send(path: "/api/inference/apple/attempts/begin", body: ["authorization": authorization])
    }

    public func reconcile(authorization: String, disposition: AdmittedInferenceDisposition, result: String?) async throws -> AdmittedInferenceReceipt {
        var body: [String: String] = ["authorization": authorization, "outcome": disposition.rawValue]
        if let result { body["result"] = result }
        let data = try await send(path: "/api/inference/apple/attempts/reconcile", body: body)
        // The execution receipt is server truth. The compact local receipt only
        // records that this client completed its one report; consumers never use
        // it to choose a next leg.
        _ = data
        return AdmittedInferenceReceipt(attemptID: "", disposition: disposition, terminal: disposition == .succeeded || disposition == .disconnected || disposition == .stopped)
    }

    private func send(path: String, body: [String: String]) async throws -> Data {
        let base = baseURL.absoluteString.hasSuffix("/") ? String(baseURL.absoluteString.dropLast()) : baseURL.absoluteString
        guard let url = URL(string: base + path) else { throw AdmittedInferenceTransportError.unavailable }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let bearerToken, !bearerToken.isEmpty { request.setValue("Bearer \(bearerToken)", forHTTPHeaderField: "Authorization") }
        request.httpBody = try JSONEncoder().encode(body)
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else { throw AdmittedInferenceTransportError.unavailable }
            return data
        } catch let error as AdmittedInferenceTransportError { throw error }
        catch { throw AdmittedInferenceTransportError.disconnected }
    }
}
