import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-18-02 — the iPad CommandsBoard client. The hub half (macros firing on the
// remote relay) shipped first; this is the authoring side: read and write
// `dictation.macros` through the settings routes and verify one action through
// the board's test route, against the shapes in `holdspeak/web/routes/system.py`:
//
//   GET  /api/settings        → full config dict; `dictation.macros` is ours
//   PUT  /api/settings        → deep-merged partial: {"dictation": {"macros": …}}
//   POST /api/commands/test   → fire one action to verify it (HS-52-05)
//
// Self-contained off the internal `config`/`session` (the file-private request
// helpers on the base type are not reachable here); the Bearer token joins at
// call time and is never logged or echoed.
extension HTTPDesktopClient {

    // MARK: - Macro settings

    /// `GET /api/settings` → just the `dictation.macros` block. Absent (an older
    /// hub) decodes as the default off/empty settings rather than throwing.
    public func macroSettings() async throws -> VoiceMacroSettings {
        let data = try await commandsSend(commandsRequest(path: "api/settings"))
        let envelope = try? HoldSpeakContracts.decoder().decode(SettingsEnvelope.self, from: data)
        return envelope?.dictation?.macros ?? VoiceMacroSettings()
    }

    /// `PUT /api/settings` with only the macros block — the hub deep-merges, so
    /// nothing else in the config is touched. The hub validates every macro
    /// (unknown kind / empty keyword / empty payload are clean 400s).
    public func updateMacroSettings(_ settings: VoiceMacroSettings) async throws {
        let body: [String: Any] = ["dictation": ["macros": [
            "enabled": settings.enabled,
            "items": settings.items.map {
                ["keyword": $0.keyword,
                 "action": ["kind": $0.action.kind, "payload": $0.action.payload]]
            },
        ]]]
        _ = try await commandsSend(commandsJSONRequest(path: "api/settings", method: "PUT", body: body))
    }

    /// `POST /api/commands/test` — fire one action on the Mac to verify it
    /// (`type_text` returns a preview instead; nothing to run).
    public func testMacro(kind: String, payload: String) async throws -> VoiceMacroTestResult {
        let data = try await commandsSend(commandsJSONRequest(
            path: "api/commands/test", method: "POST",
            body: ["kind": kind, "payload": payload]))
        guard let result = try? HoldSpeakContracts.decoder().decode(VoiceMacroTestResult.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return result
    }

    // MARK: - internals

    /// Only the slice of `/api/settings` this client reads.
    private struct SettingsEnvelope: Decodable {
        struct Dictation: Decodable { var macros: VoiceMacroSettings? }
        var dictation: Dictation?
    }

    private func commandsSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func commandsRequest(path: String, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: commandsURL(path: path))
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    private func commandsJSONRequest(path: String, method: String, body: [String: Any]) -> URLRequest {
        var request = URLRequest(url: commandsURL(path: path))
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        return request
    }

    private func commandsURL(path: String) -> URL {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        return URL(string: "\(base)/\(path)") ?? config.baseURL
    }
}
