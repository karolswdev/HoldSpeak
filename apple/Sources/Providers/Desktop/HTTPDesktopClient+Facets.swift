import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HS-55-04 (mobile) — the faceted meeting archive over the desktop's HTTP API.
// The /history filter row on the iPad: read the distinct filter values the hub
// offers (`/api/meetings/facets`), then narrow the archive server-side by feeding
// a chosen speaker/tag (and/or a full-text query) back through `/api/meetings`.
//
// Kept in a SEPARATE extension file (no edits to HTTPDesktopClient.swift) so this
// slice lands without colliding with the other client methods landing in the same
// wave. The request + decode style mirrors the base client (Bearer auth, the shared
// snake_case decoder, a non-2xx → `DesktopClientError.http`), built inline here so
// this file owns no dependency on the base type's private helpers.
extension HTTPDesktopClient {

    /// `GET /api/meetings/facets` → the distinct speakers + tags that can filter the
    /// archive (HS-55-04). Throws `DesktopClientError.http` on a non-2xx and
    /// `.malformed` if the body is not the expected `{speakers, tags}` shape.
    public func listFacets() async throws -> MeetingFacets {
        let data = try await facetsSend(facetsRequest(path: "api/meetings/facets"))
        do { return try HoldSpeakContracts.decoder().decode(MeetingFacets.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    /// `GET /api/meetings?search=&speaker=&tag=` → the faceted/searched summaries.
    /// Every argument is optional; passing none returns the unfiltered archive (the
    /// same summary shape `listMeetings()` returns — the hub routes search and facets
    /// through one query so both branches share the `MeetingSummary` payload).
    ///
    /// - Parameters:
    ///   - query: full-text transcript search (the hub's `search=` param).
    ///   - speaker: narrow to meetings a given speaker spoke in (`speaker=`).
    ///   - type: a facet value carried as the hub's `tag=` param (the archive's
    ///     meeting "type" facet is a tag in the schema).
    public func searchMeetings(query: String? = nil,
                               speaker: String? = nil,
                               type: String? = nil) async throws -> [MeetingSummary] {
        var items: [URLQueryItem] = []
        if let query, !query.isEmpty { items.append(URLQueryItem(name: "search", value: query)) }
        if let speaker, !speaker.isEmpty { items.append(URLQueryItem(name: "speaker", value: speaker)) }
        if let type, !type.isEmpty { items.append(URLQueryItem(name: "tag", value: type)) }

        let data = try await facetsSend(facetsRequest(path: "api/meetings", query: items))
        do {
            return try HoldSpeakContracts.decoder()
                .decode(FacetedMeetingsEnvelope.self, from: data).meetings
        } catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (file-private to this slice; no shared-helper dependency)

    /// The `/api/meetings` list envelope: the summaries plus an archive `total`. A
    /// private mirror so this file never reaches into the base client's
    /// `MeetingsEnvelope`.
    private struct FacetedMeetingsEnvelope: Decodable {
        var meetings: [MeetingSummary]
        var total: Int?
    }

    /// Build a GET against the configured peer with optional query items, mirroring
    /// the base client's Bearer-auth + timeout. Built inline so the slice carries no
    /// dependency on the base type's private `makeRequest`.
    private func facetsRequest(path: String, query: [URLQueryItem] = []) -> URLRequest {
        let absolute = config.baseURL.absoluteString
        let base = absolute.hasSuffix("/") ? String(absolute.dropLast()) : absolute
        var components = URLComponents(string: "\(base)/\(path)")
        if !query.isEmpty { components?.queryItems = query }
        var request = URLRequest(url: components?.url ?? config.baseURL)
        request.httpMethod = "GET"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    /// Run a request, throwing `DesktopClientError.http` on a non-2xx (so the
    /// view-model can render an honest unreachable/failed state). Mirrors the base
    /// client's `send`.
    private func facetsSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }
}
