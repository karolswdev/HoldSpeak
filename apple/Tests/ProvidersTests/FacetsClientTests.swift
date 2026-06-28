import XCTest
import Contracts
@testable import Providers

/// HS-55-04 (mobile) — the faceted meeting archive client. Network stubbed via
/// `URLProtocol`; deterministic and offline. Proves: `/api/meetings/facets` decodes
/// into `MeetingFacets`, the searched `/api/meetings` envelope decodes into
/// `[MeetingSummary]`, the Bearer token rides, and the `MeetingFacets` contract type
/// round-trips a realistic hub payload (incl. the empty-archive / partial cases).
final class FacetsClientTests: XCTestCase {

    // MARK: stub (matches on path; query string is stripped by `URLRequest.url.path`)

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastQuery: String?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastQuery = request.url?.query
            let path = request.url?.path ?? ""
            guard let (status, body) = StubProtocol.routes[path] else {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost))
                return
            }
            let resp = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: resp, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: body)
            client?.urlProtocolDidFinishLoading(self)
        }
        override func stopLoading() {}
    }

    private func stubbedSession() -> URLSession {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.protocolClasses = [StubProtocol.self]
        return URLSession(configuration: cfg)
    }

    override func setUp() {
        super.setUp()
        StubProtocol.routes = [:]
        StubProtocol.lastAuth = nil
        StubProtocol.lastQuery = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    // MARK: - MeetingFacets contract decode round-trip

    func testFacetsTypeDecodesRealisticPayload() throws {
        let json = #"{"speakers":["Alex","Dana Lee"],"tags":["q3","standup"]}"#
        let facets = try HoldSpeakContracts.decoder().decode(MeetingFacets.self, from: Data(json.utf8))
        XCTAssertEqual(facets.speakers, ["Alex", "Dana Lee"])
        XCTAssertEqual(facets.tags, ["q3", "standup"])
    }

    func testFacetsTypeToleratesEmptyArchive() throws {
        let facets = try HoldSpeakContracts.decoder().decode(MeetingFacets.self, from: Data(#"{"speakers":[],"tags":[]}"#.utf8))
        XCTAssertTrue(facets.speakers.isEmpty)
        XCTAssertTrue(facets.tags.isEmpty)
    }

    func testFacetsTypeToleratesPartialPayload() throws {
        // A future/partial payload missing one array still decodes (robust posture).
        let facets = try HoldSpeakContracts.decoder().decode(MeetingFacets.self, from: Data(#"{"speakers":["Sam"]}"#.utf8))
        XCTAssertEqual(facets.speakers, ["Sam"])
        XCTAssertTrue(facets.tags.isEmpty)
    }

    // MARK: - listFacets() over the client

    func testListFacetsDecodesAndSendsToken() async throws {
        StubProtocol.routes = [
            "/api/meetings/facets": (200, Data(#"{"speakers":["Alex","Dana"],"tags":["q3"]}"#.utf8)),
        ]
        let facets = try await client(token: "t0ken").listFacets()
        XCTAssertEqual(facets.speakers, ["Alex", "Dana"])
        XCTAssertEqual(facets.tags, ["q3"])
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer t0ken")
    }

    func testListFacetsThrowsHTTPOnNon2xx() async {
        StubProtocol.routes = ["/api/meetings/facets": (500, Data())]
        do {
            _ = try await client().listFacets()
            XCTFail("expected an http error")
        } catch let HTTPDesktopClient.DesktopClientError.http(code) {
            XCTAssertEqual(code, 500)
        } catch {
            XCTFail("unexpected error: \(error)")
        }
    }

    // MARK: - searchMeetings(...) over the client

    func testSearchMeetingsDecodesEnvelopeAndCarriesQuery() async throws {
        // The hub's faceted /api/meetings envelope: summaries + a `total`. The
        // timestamps ride in the REAL naive-ISO shape the hub emits (no `Z`/offset,
        // microsecond fractional), which a `Date?` field would reject and fail the
        // whole decode on — `startedAt`/`endedAt` are `String?` (metal-readiness).
        let body = #"""
        {"meetings":[
          {"id":"m1","title":"Q3 Standup","started_at":"2026-06-27T09:00:00.512000",
           "ended_at":"2026-06-27T09:30:00.004211","duration_seconds":1800.0,
           "segment_count":42,"action_item_count":3,"tags":["q3","standup"],
           "intel_status":"ready","intel_status_detail":null}
        ],"total":1}
        """#
        StubProtocol.routes = ["/api/meetings": (200, Data(body.utf8))]

        let meetings = try await client(token: "t0ken")
            .searchMeetings(query: "roadmap", speaker: "Dana", type: "q3")

        XCTAssertEqual(meetings.count, 1)
        let m = try XCTUnwrap(meetings.first)
        XCTAssertEqual(m.id, "m1")
        XCTAssertEqual(m.title, "Q3 Standup")
        XCTAssertEqual(m.startedAt, "2026-06-27T09:00:00.512000")  // naive ISO survives
        XCTAssertEqual(m.segmentCount, 42)
        XCTAssertEqual(m.actionItemCount, 3)
        XCTAssertEqual(m.intelStatus, "ready")

        // Every supplied facet rides as the hub's expected query param.
        let q = try XCTUnwrap(StubProtocol.lastQuery)
        XCTAssertTrue(q.contains("search=roadmap"), q)
        XCTAssertTrue(q.contains("speaker=Dana"), q)
        XCTAssertTrue(q.contains("tag=q3"), q)
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer t0ken")
    }

    func testSearchMeetingsWithNoFiltersSendsNoQuery() async throws {
        StubProtocol.routes = ["/api/meetings": (200, Data(#"{"meetings":[],"total":0}"#.utf8))]
        let meetings = try await client().searchMeetings()
        XCTAssertTrue(meetings.isEmpty)
        XCTAssertNil(StubProtocol.lastQuery)   // no params → bare path
    }
}
