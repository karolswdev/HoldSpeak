import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

/// The desktop's one authority preset. It affects future operations only.
public struct AuthorityPolicy: Codable, Equatable, Sendable {
    public var controlMode: String
    public var controlModeLabel: String?
    public var controlModeDescription: String?
    public var policyVersion: String?
    public var source: String?
    public var appliesTo: String?
    public var precedence: [String]?
    public var hardInvariants: [String]?
    public var supportedFamilies: [String]?
    public var unsupportedFamilyBehavior: String?

}

extension HTTPDesktopClient {
    public func authorityPolicy() async throws -> AuthorityPolicy {
        try await authoritySend(path: "api/authority/policy")
    }

    public func setControlMode(_ mode: String) async throws -> AuthorityPolicy {
        try await authoritySend(
            path: "api/authority/control-mode",
            method: "PUT",
            body: ["control_mode": mode]
        )
    }

    private func authoritySend<T: Decodable>(
        path: String, method: String = "GET", body: [String: String]? = nil
    ) async throws -> T {
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
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        do { return try HoldSpeakContracts.decoder().decode(T.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }
}
