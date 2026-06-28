import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-18-01 — the rest of the dictation-pipeline client the iPad never had: blocks (read + full CRUD),
// block-templates, and project-context. Typed calls to the hub's
// `/api/dictation/blocks*`, `/api/dictation/block-templates`, `/api/dictation/project-context`
// (modeled in Contracts/DictationBlocks.swift). New file (no edits to HTTPDesktopClient.swift, so it
// never collides with the parallel client work); builds its own Bearer-authed request off the internal
// `config`, mirroring +Dictation.swift's pattern.
//
// CRUD parity with blocks.py: GET (list) / POST {block} (create) / PUT /{id} {block} (update) /
// DELETE /{id}. The hub also exposes POST /blocks/from-template (with an optional dry-run); the iPad
// builds from a template by reading block-templates + create, so it is not surfaced here.
public extension HTTPDesktopClient {

    /// `GET /api/dictation/blocks?scope=&project_root=` -> the resolved blocks document (the YAML the
    /// hub reads back) plus scope/path/exists/project envelope.
    func dictationBlocks(scope: String = "global", projectRoot: String? = nil) async throws -> DictationBlocksResult {
        var query = [URLQueryItem(name: "scope", value: scope)]
        if let projectRoot, !projectRoot.isEmpty { query.append(URLQueryItem(name: "project_root", value: projectRoot)) }
        let data = try await blocksRequest(path: "api/dictation/blocks", method: "GET", query: query, body: nil)
        return try decodeBlocks(DictationBlocksResult.self, from: data)
    }

    /// `GET /api/dictation/block-templates` -> the starter templates (`templates[]`).
    func blockTemplates() async throws -> [DictationBlockTemplate] {
        let data = try await blocksRequest(path: "api/dictation/block-templates", method: "GET", query: [], body: nil)
        let envelope = try decodeBlocks(BlockTemplatesEnvelope.self, from: data)
        return envelope.templates
    }

    /// `GET /api/dictation/project-context?project_root=` -> the resolved project + its config paths.
    func projectContext(projectRoot: String? = nil) async throws -> DictationProjectContext {
        var query: [URLQueryItem] = []
        if let projectRoot, !projectRoot.isEmpty { query.append(URLQueryItem(name: "project_root", value: projectRoot)) }
        let data = try await blocksRequest(path: "api/dictation/project-context", method: "GET", query: query, body: nil)
        return try decodeBlocks(DictationProjectContext.self, from: data)
    }

    // MARK: - CRUD (blocks.py exposes POST / PUT /{id} / DELETE /{id})

    /// `POST /api/dictation/blocks {block}` -> the updated document. 409 (id already exists) surfaces
    /// as `DesktopClientError.http(409)`.
    @discardableResult
    func createBlock(_ block: DictationBlock, scope: String = "global", projectRoot: String? = nil) async throws -> DictationBlocksResult {
        let data = try await blocksRequest(path: "api/dictation/blocks", method: "POST",
                                           query: blocksQuery(scope: scope, projectRoot: projectRoot),
                                           body: ["block": try encodeBlock(block)])
        return try decodeBlocks(DictationBlocksResult.self, from: data)
    }

    /// `PUT /api/dictation/blocks/{blockId} {block}` -> the updated document. Unknown id surfaces as a
    /// 404; an id collision on rename as a 409.
    @discardableResult
    func updateBlock(_ blockId: String, with block: DictationBlock, scope: String = "global", projectRoot: String? = nil) async throws -> DictationBlocksResult {
        let encoded = blockId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? blockId
        let data = try await blocksRequest(path: "api/dictation/blocks/\(encoded)", method: "PUT",
                                           query: blocksQuery(scope: scope, projectRoot: projectRoot),
                                           body: ["block": try encodeBlock(block)])
        return try decodeBlocks(DictationBlocksResult.self, from: data)
    }

    /// `DELETE /api/dictation/blocks/{blockId}` -> the updated document. Note: the hub rejects deleting
    /// the last block (save requires >= 1) with a 422, surfaced as `DesktopClientError.http(422)`.
    @discardableResult
    func deleteBlock(_ blockId: String, scope: String = "global", projectRoot: String? = nil) async throws -> DictationBlocksResult {
        let encoded = blockId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? blockId
        let data = try await blocksRequest(path: "api/dictation/blocks/\(encoded)", method: "DELETE",
                                           query: blocksQuery(scope: scope, projectRoot: projectRoot), body: nil)
        return try decodeBlocks(DictationBlocksResult.self, from: data)
    }

    // MARK: - internals

    /// The `GET /api/dictation/block-templates` envelope.
    private struct BlockTemplatesEnvelope: Codable {
        var templates: [DictationBlockTemplate]
    }

    private func blocksQuery(scope: String, projectRoot: String?) -> [URLQueryItem] {
        var query = [URLQueryItem(name: "scope", value: scope)]
        if let projectRoot, !projectRoot.isEmpty { query.append(URLQueryItem(name: "project_root", value: projectRoot)) }
        return query
    }

    private func decodeBlocks<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
        do { return try HoldSpeakContracts.decoder().decode(T.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// Round-trip a `DictationBlock` back to a JSON object for the create/update bodies (the hub wants
    /// `{"block": {...}}` with snake_case keys, matching the decoder's `.convertFromSnakeCase`).
    private func encodeBlock(_ block: DictationBlock) throws -> [String: Any] {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        let data = try encoder.encode(block)
        guard let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw DesktopClientError.malformed
        }
        return obj
    }

    /// Self-contained authed request (the struct's own `send`/`makeRequest` are file-private; this new
    /// file rebuilds the same Bearer pattern off the internal `config`/`session`).
    private func blocksRequest(path: String, method: String, query: [URLQueryItem], body: [String: Any]?) async throws -> Data {
        let baseString = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        guard var components = URLComponents(string: "\(baseString)/\(path)") else { throw DesktopClientError.malformed }
        if !query.isEmpty { components.queryItems = query }
        guard let url = components.url else { throw DesktopClientError.malformed }
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
