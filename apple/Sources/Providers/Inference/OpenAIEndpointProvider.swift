import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// An `ILLMProvider` backed by any OpenAI-compatible `chat/completions` endpoint —
/// the charter's Mode B (homelab) and Mode C (endpoint). Foundation/URLSession
/// only: no native engine, no resident model, so selecting it costs the device no
/// unified memory (owner steer 2026-06-19). Pointed at a self-hosted llama.cpp
/// server it gives a phone or iPad access to a model far larger than it could ever
/// load locally.
///
/// The provider is engine-agnostic by construction: it speaks only the wire API,
/// so the Runtime Core sees the same `complete(prompt:)` it gets from the on-device
/// engine. Anything endpoint-specific stays here.
public struct OpenAIEndpointProvider: ILLMProvider {
    let config: EndpointConfig
    let session: URLSession

    public init(config: EndpointConfig, session: URLSession = .shared) {
        self.config = config
        self.session = session
    }

    public enum ProviderError: Error, Equatable {
        case http(status: Int, body: String)
        case malformedResponse
        case emptyCompletion
    }

    public func complete(prompt: String) async throws -> String {
        var request = URLRequest(url: chatCompletionsURL())
        request.httpMethod = "POST"
        request.timeoutInterval = config.timeout
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let apiKey = config.apiKey, !apiKey.isEmpty {
            request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try JSONEncoder().encode(
            ChatRequest(
                model: config.model,
                messages: [.init(role: "user", content: prompt)],
                temperature: config.temperature,
                stream: false
            )
        )

        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw ProviderError.http(status: http.statusCode, body: String(body.prefix(500)))
        }

        let decoded: ChatResponse
        do { decoded = try JSONDecoder().decode(ChatResponse.self, from: data) }
        catch { throw ProviderError.malformedResponse }

        guard let content = decoded.choices.first?.message.content else {
            throw ProviderError.emptyCompletion
        }
        return content
    }

    /// Resolve `{baseURL}` to its `chat/completions` route, tolerating a base that
    /// already includes the route or a trailing slash.
    func chatCompletionsURL() -> URL {
        let s = config.baseURL.absoluteString
        if s.hasSuffix("/chat/completions") { return config.baseURL }
        let trimmed = s.hasSuffix("/") ? String(s.dropLast()) : s
        return URL(string: trimmed + "/chat/completions") ?? config.baseURL
    }

    // MARK: - Wire shapes (minimal OpenAI chat surface)

    struct ChatRequest: Encodable {
        let model: String
        let messages: [Message]
        let temperature: Double
        let stream: Bool
        struct Message: Encodable { let role: String; let content: String }
    }

    struct ChatResponse: Decodable {
        let choices: [Choice]
        struct Choice: Decodable { let message: Message }
        struct Message: Decodable { let content: String }
    }
}
