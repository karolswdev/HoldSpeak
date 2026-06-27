import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-18-01 — the dictation-pipeline client (the teleprompter's spine). Typed calls to the hub's
// dry-run + readiness routes so the iPad can show the rewrite AND its destination BEFORE a single
// keystroke leaves the app. New file (no edits to HTTPDesktopClient.swift, so it never collides with
// the parallel Phase-19 client work); builds its own Bearer-authed request from the internal `config`.
public extension HTTPDesktopClient {
    /// `POST /api/dictation/dry-run {utterance}` -> the routed + rewritten preview (what WOULD be
    /// typed, and where). Preview-not-inject: this never delivers; the teleprompter shows it first.
    func dictationDryRun(utterance: String) async throws -> DictationDryRun {
        let data = try await dictationRequest(path: "api/dictation/dry-run",
                                              method: "POST", body: ["utterance": utterance])
        do { return try HoldSpeakContracts.decoder().decode(DictationDryRun.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// `GET /api/dictation/readiness` -> a setup snapshot for the dictate screen's status strip.
    func dictationReadiness() async throws -> DictationReadiness {
        let data = try await dictationRequest(path: "api/dictation/readiness", method: "GET", body: nil)
        do { return try HoldSpeakContracts.decoder().decode(DictationReadiness.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// Self-contained authed request (the struct's own `send`/`makeRequest` are file-private; this
    /// new file rebuilds the same Bearer pattern off the internal `config`/`session`).
    private func dictationRequest(path: String, method: String, body: [String: Any]?) async throws -> Data {
        let baseString = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        guard let url = URL(string: "\(baseString)/\(path)") else { throw DesktopClientError.malformed }
        var request = URLRequest(url: url)
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
        let code = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(code) else { throw DesktopClientError.http(code) }
        return data
    }
}
