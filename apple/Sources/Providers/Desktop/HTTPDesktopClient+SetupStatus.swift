import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-21-04 — the setup-status client: one pure read of the hub's posture snapshot
// (`GET /api/setup/status`, HS-42-01) for the ambient trust chip. New extension file
// by design (the equilibrium conflict rule): no edits to HTTPDesktopClient.swift;
// the request/decode posture mirrors the base client (Bearer auth, shared decoder,
// non-2xx → `DesktopClientError.http`, decode miss → `.malformed`).
extension HTTPDesktopClient {

    /// `GET /api/setup/status` → the posture snapshot the trust chip renders. Pure
    /// read, no side effects; cheap on the hub (`skip_network=True` there).
    public func setupStatus() async throws -> SetupStatus {
        let data = try await sendSetupStatus(makeSetupStatusRequest(path: "api/setup/status"))
        do { return try HoldSpeakContracts.decoder().decode(SetupStatus.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (private to this extension, per the conflict rule)

    private func sendSetupStatus(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeSetupStatusRequest(path: String) -> URLRequest {
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
