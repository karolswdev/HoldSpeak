import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-15-02 — run ONE Workbench step on the paired desktop. The mesh's per-step
// dispatch rides the hub's ask route (`POST /api/ask`): the step's fully-resolved
// prompt in, the output + the run's honest egress out, NOTHING persisted (a step
// result is intermediate; keep/bin judgments belong to whole outputs, not steps).
// New extension file by design (the equilibrium conflict rule): no edits to
// HTTPDesktopClient.swift.

/// Where a dispatched step actually ran, from the hub's answer — powers the honest
/// job label ("Your Mac · <model>"). Every field optional (robust decode).
public struct HubStepEgress: Codable, Equatable, Sendable {
    public var scope: String?
    public var host: String?

    public init(scope: String? = nil, host: String? = nil) {
        self.scope = scope
        self.host = host
    }
}

/// The hub's answer to a dispatched step.
public struct HubStepResult: Codable, Equatable, Sendable {
    public var output: String?
    public var provider: String?
    public var model: String?
    public var egress: HubStepEgress?

    public init(output: String? = nil, provider: String? = nil,
                model: String? = nil, egress: HubStepEgress? = nil) {
        self.output = output
        self.provider = provider
        self.model = model
        self.egress = egress
    }
}

extension HTTPDesktopClient {

    /// `POST /api/ask` body `{prompt, lens, context: []}` → the step result. The
    /// runner already resolved the step's input INTO the prompt, so the context is
    /// empty (the hub grounds nothing extra) and the hub persists nothing. A non-2xx
    /// throws `DesktopClientError.http`; a missing output decodes as `nil` (the
    /// caller treats it as a failed attempt, riding the failure policy).
    /// `model` (HSM-15-11) pins one of the HUB's models — the hub allow-lists it
    /// against what it can actually run and refuses 400 on anything else.
    public func runStep(prompt: String, lens: String = "Workbench", model: String? = nil) async throws -> HubStepResult {
        var body: [String: Any] = ["prompt": prompt, "lens": lens, "context": []]
        if let model, !model.isEmpty { body["model"] = model }
        let data = try await sendAsk(makeAskRequest(path: "api/ask", body: body))
        do { return try HoldSpeakContracts.decoder().decode(HubStepResult.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (private to this extension, per the conflict rule)

    private func sendAsk(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeAskRequest(path: String, body: [String: Any]) -> URLRequest {
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
