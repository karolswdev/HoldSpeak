import XCTest
import Contracts
@testable import Providers

/// HSM learning-loop client (read side, Phase 19-06) — decode round-trips + the client
/// verbs over a stubbed network (URLProtocol, fully offline). Proves:
///   - GET /api/dictation/journal          → JournalResponse decodes faithfully, incl.
///     the inline `learning` signal, the local-only toggle/retention/count, and NAIVE
///     `created_at` carried as a String (the .iso8601 decoder would throw on a Date).
///   - GET /api/dictation/learning-digest  → LearningDigest decodes (totals, by_kind,
///     by_block/by_target ranks, per-correction reach, naive generated_at).
///   - Bearer token rides, query params (limit/source/window) are sent, non-2xx throws.
/// Mirrors AftercareClientTests' stub posture.
final class LearningClientTests: XCTestCase {

    // MARK: stub (same shape as DesktopClientTests.StubProtocol)

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastMethod: String?
        nonisolated(unsafe) static var lastURL: URL?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastMethod = request.httpMethod
            StubProtocol.lastURL = request.url
            // Match on path only (the verbs append a query string).
            let path = request.url?.path ?? ""
            guard let (status, body) = StubProtocol.routes[path] else {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost)); return
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
        StubProtocol.lastMethod = nil
        StubProtocol.lastURL = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    // A realistic, fully-populated journal envelope. NOTE the naive created_at
    // ("2026-06-27T12:00:00.123456", no Z / offset) — the .iso8601 decoder throws on
    // a Date, so the contract carries it as a String. One entry has a learning signal,
    // one is bare (learning: null).
    private let journalJSON = #"""
    {
      "enabled": true,
      "retention": 500,
      "count": 7,
      "items": [
        {
          "id": 42,
          "created_at": "2026-06-27T12:00:00.123456",
          "source": "dictation",
          "transcript": "fix the sync transport bug",
          "final_text": "Fix the sync transport bug.",
          "project_root": "/Users/karol/dev/holdspeak",
          "intent": "code",
          "block_id": "code-fix",
          "target_profile": "editor",
          "stage_ms": {"transcribe": 120.5, "route": 4.0, "project-rewriter": 88.0},
          "total_ms": 212.5,
          "rewrite_pass_ms": [88.0],
          "confidence": 0.91,
          "warnings": [],
          "corrected": false,
          "correction_id": null,
          "learning": {
            "matched": true, "kind": "intent", "value": "code-fix",
            "gist": "fix the sync transport bug", "similar": 3
          }
        },
        {
          "id": 41,
          "created_at": "2026-06-27T11:58:30.000001",
          "source": "dry_run",
          "transcript": "book the room",
          "final_text": "Book the room.",
          "project_root": null,
          "intent": null,
          "block_id": null,
          "target_profile": null,
          "stage_ms": {},
          "total_ms": 0.0,
          "rewrite_pass_ms": [],
          "confidence": null,
          "warnings": ["no project context"],
          "corrected": true,
          "correction_id": 9,
          "learning": null
        }
      ]
    }
    """#

    // The digest shape build_learning_digest emits.
    private let digestJSON = #"""
    {
      "window": "week",
      "enabled": true,
      "generated_at": "2026-06-27T12:01:00.500000",
      "totals": {
        "corrections_made": 4,
        "dictations_corrected": 2,
        "similar_nudged": 5,
        "journal_count": 7
      },
      "by_kind": {"intent": 3, "target": 1},
      "by_block": [
        {"block_id": "code-fix", "count": 2},
        {"block_id": "note", "count": 1}
      ],
      "by_target": [
        {"target_profile": "editor", "count": 1}
      ],
      "corrections": [
        {"id": 9, "kind": "intent", "gist": "fix the sync transport bug",
         "value": "code-fix", "created_at": "2026-06-26T09:00:00.000000", "similar": 3},
        {"id": null, "kind": "target", "gist": "send to slack",
         "value": "editor", "created_at": null, "similar": 0}
      ]
    }
    """#

    // MARK: journal decode + client GET

    func testJournalResponseDecodesFaithfully() throws {
        let resp = try HoldSpeakContracts.decoder().decode(JournalResponse.self, from: Data(journalJSON.utf8))

        XCTAssertTrue(resp.enabled)
        XCTAssertEqual(resp.retention, 500)
        XCTAssertEqual(resp.count, 7)               // true total can exceed items.count
        XCTAssertEqual(resp.items.count, 2)

        let first = resp.items[0]
        XCTAssertEqual(first.id, 42)
        // Naive timestamp survives as a raw String (the whole point — Date would throw).
        XCTAssertEqual(first.createdAt, "2026-06-27T12:00:00.123456")
        XCTAssertEqual(first.source, "dictation")
        XCTAssertEqual(first.finalText, "Fix the sync transport bug.")
        XCTAssertEqual(first.intent, "code")
        XCTAssertEqual(first.blockId, "code-fix")
        XCTAssertEqual(first.targetProfile, "editor")
        XCTAssertEqual(first.stageMs?["transcribe"], 120.5)
        XCTAssertEqual(first.totalMs, 212.5)
        XCTAssertEqual(first.rewritePassMs, [88.0])
        XCTAssertEqual(first.confidence, 0.91)
        XCTAssertEqual(first.warnings, [])
        XCTAssertFalse(first.corrected)
        XCTAssertNil(first.correctionId)
        // inline learning signal decoded
        let learning = try XCTUnwrap(first.learning)
        XCTAssertTrue(learning.matched)
        XCTAssertEqual(learning.kind, "intent")
        XCTAssertEqual(learning.value, "code-fix")
        XCTAssertEqual(learning.similar, 3)

        // The bare entry — nullables become nil, learning is absent (router nudges nothing).
        let second = resp.items[1]
        XCTAssertEqual(second.source, "dry_run")
        XCTAssertNil(second.projectRoot)
        XCTAssertNil(second.intent)
        XCTAssertNil(second.confidence)
        XCTAssertEqual(second.warnings, ["no project context"])
        XCTAssertTrue(second.corrected)
        XCTAssertEqual(second.correctionId, 9)
        XCTAssertNil(second.learning)
    }

    func testEmptyJournalDecodes() throws {
        // A bare server: journaling on, nothing recorded yet — empty, never an error.
        let json = #"{"enabled": true, "retention": 500, "count": 0, "items": []}"#
        let resp = try HoldSpeakContracts.decoder().decode(JournalResponse.self, from: Data(json.utf8))
        XCTAssertEqual(resp.count, 0)
        XCTAssertTrue(resp.items.isEmpty)
    }

    func testJournalClientGETsWithLimitAndBearer() async throws {
        StubProtocol.routes = ["/api/dictation/journal": (200, Data(journalJSON.utf8))]
        let resp = try await client(token: "tok").journalEntries(limit: 50)
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")          // Bearer token rides
        XCTAssertEqual(StubProtocol.lastURL?.query, "limit=50")      // limit param sent
        XCTAssertEqual(resp.items.first?.id, 42)
        XCTAssertEqual(resp.items.first?.transcript, "fix the sync transport bug")
    }

    func testJournalClientSendsSourceFilter() async throws {
        StubProtocol.routes = ["/api/dictation/journal": (200, Data(journalJSON.utf8))]
        _ = try await client(token: "tok").journalEntries(limit: 10, source: "dictation")
        let query = try XCTUnwrap(StubProtocol.lastURL?.query)
        XCTAssertTrue(query.contains("limit=10"))
        XCTAssertTrue(query.contains("source=dictation"))
    }

    func testJournalNoTokenSendsNoAuthHeader() async throws {
        StubProtocol.routes = ["/api/dictation/journal": (200, Data(journalJSON.utf8))]
        _ = try await client().journalEntries()
        // No token configured → no Authorization header at all.
        XCTAssertEqual(StubProtocol.lastAuth, .some(.none))
    }

    func testJournal500Throws() async {
        StubProtocol.routes = ["/api/dictation/journal": (500, Data(#"{"error":"boom"}"#.utf8))]
        do { _ = try await client().journalEntries(); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 500) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: digest decode + client GET

    func testLearningDigestDecodesFaithfully() throws {
        let digest = try HoldSpeakContracts.decoder().decode(LearningDigest.self, from: Data(digestJSON.utf8))

        XCTAssertEqual(digest.window, "week")
        XCTAssertTrue(digest.enabled)
        // naive generated_at carried as String
        XCTAssertEqual(digest.generatedAt, "2026-06-27T12:01:00.500000")

        XCTAssertEqual(digest.totals.correctionsMade, 4)
        XCTAssertEqual(digest.totals.dictationsCorrected, 2)
        XCTAssertEqual(digest.totals.similarNudged, 5)
        XCTAssertEqual(digest.totals.journalCount, 7)

        XCTAssertEqual(digest.byKind.intent, 3)
        XCTAssertEqual(digest.byKind.target, 1)

        XCTAssertEqual(digest.byBlock.count, 2)
        XCTAssertEqual(digest.byBlock.first?.blockId, "code-fix")
        XCTAssertEqual(digest.byBlock.first?.count, 2)
        XCTAssertEqual(digest.byTarget.first?.targetProfile, "editor")

        XCTAssertEqual(digest.corrections.count, 2)
        let durable = digest.corrections[0]
        XCTAssertEqual(durable.id, 9)
        XCTAssertEqual(durable.kind, "intent")
        XCTAssertEqual(durable.gist, "fix the sync transport bug")
        XCTAssertEqual(durable.similar, 3)
        XCTAssertEqual(durable.createdAt, "2026-06-26T09:00:00.000000")
        // The in-memory (non-durable) correction: null id, null created_at.
        let inMemory = digest.corrections[1]
        XCTAssertNil(inMemory.id)
        XCTAssertNil(inMemory.createdAt)
        XCTAssertEqual(inMemory.similar, 0)
    }

    func testLearningDigestClientGETsWithWindowAndBearer() async throws {
        StubProtocol.routes = ["/api/dictation/learning-digest": (200, Data(digestJSON.utf8))]
        let digest = try await client(token: "tok").learningDigest(window: "all")
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")
        XCTAssertEqual(StubProtocol.lastURL?.query, "window=all")    // window param sent
        XCTAssertEqual(digest.totals.correctionsMade, 4)
    }

    func testLearningDigest503Throws() async {
        StubProtocol.routes = ["/api/dictation/learning-digest": (503, Data(#"{"error":"down"}"#.utf8))]
        do { _ = try await client().learningDigest(); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 503) }
        catch { XCTFail("wrong error: \(error)") }
    }
}
