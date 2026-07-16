import XCTest
import Contracts
@testable import Providers

/// HS-94-09 — the Delivery Runtime client over a stubbed network (URLProtocol,
/// fully offline; the SteeringClientTests precedent). Proves the native Desk
/// reads the §10 hub API: the coherent snapshot, the registry view, node
/// presence, work attempts (with query filters), and story dossiers — where a
/// typed refusal is a TYPED error carrying the §13-preserved manifest, never
/// an opaque status code.
final class DeliveryClientTests: XCTestCase {

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastURL: URL?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastURL = request.url
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
        StubProtocol.lastURL = nil
    }

    private func client() -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: "t"),
                          session: stubbedSession())
    }

    private func route(_ path: String, _ status: Int, _ json: String) {
        StubProtocol.routes[path] = (status, Data(json.utf8))
    }

    func testSnapshotDecodes() async throws {
        route("/api/delivery/snapshot", 200, #"""
        {"delivery_schema":1,"revision":"rev_9c2f4b8a1d3e5f70",
         "cursor":"cur_eyJzcmNfMWIyYzNkNGU1ZjYwNzE4MiI6IjQyIn0",
         "generated_at":"2026-07-15T09:30:00Z",
         "sources":[{"source_id":"src_1b2c3d4e5f607182","node_id":"node_9f8e7d6c5b4a3921",
          "label":"holdspeak","status":"live","detail":"","observed_at":"2026-07-15T09:29:58Z",
          "capabilities":null,
          "worktrees":[{"worktree_id":"wt_0a1b2c3d4e5f6071","branch":"main"}],
          "projects":null,"sessions":null}]}
        """#)
        let snap = try await client().deliverySnapshot()
        XCTAssertEqual(snap.deliverySchema, 1)
        XCTAssertEqual(snap.revision, "rev_9c2f4b8a1d3e5f70")
        XCTAssertEqual(snap.sources.count, 1)
        XCTAssertEqual(snap.sources[0].status, .live)
        XCTAssertEqual(snap.sources[0].worktrees?[0].worktreeId, "wt_0a1b2c3d4e5f6071")
    }

    func testSourcesViewDecodes() async throws {
        route("/api/delivery/sources", 200, #"""
        {"registry_schema":1,"sources":[{"source_id":"src_1b2c3d4e5f607182","node_id":null,
         "label":"holdspeak","fingerprint":"sha256:7f3a","worktrees":[],
         "status":"stale","detail":"dw timed out","observed_at":"2026-07-15T09:12:04Z"}]}
        """#)
        let view = try await client().deliverySources()
        XCTAssertEqual(view.registrySchema, 1)
        XCTAssertEqual(view.sources[0].status, .stale)
        XCTAssertEqual(view.sources[0].fingerprint, "sha256:7f3a")
    }

    func testNodesDecode() async throws {
        route("/api/delivery/nodes", 200, #"""
        {"nodes_schema":1,"nodes":[
         {"name":"intel-43","node_id":"node_9f8e7d6c5b4a3921","kind":"node-link","status":"live",
          "last_seen":"2026-07-15T09:29:57Z","instance_id":"abc","capabilities":["coder.steering"],
          "commands_enabled":true,"compat":null,"cursor":42,"clock_skew_seconds":-0.412},
         {"name":"beta","node_id":null,"kind":"legacy-direct","status":"unknown","last_seen":"",
          "instance_id":"","capabilities":["coder.steering"],"commands_enabled":true,
          "compat":"legacy-direct","cursor":0,"clock_skew_seconds":null}]}
        """#)
        let view = try await client().deliveryNodes()
        XCTAssertEqual(view.nodesSchema, 1)
        XCTAssertEqual(view.nodes[0].status, .live)
        XCTAssertEqual(view.nodes[0].commandsEnabled, true)
        XCTAssertEqual(view.nodes[1].kind, "legacy-direct")
        XCTAssertEqual(view.nodes[1].status, .unknown)
    }

    func testAttemptsCarryTheFilterQuery() async throws {
        route("/api/delivery/attempts", 200, #"""
        {"attempts_schema":1,"attempts":[
         {"attempt_id":"att_5f6e7d8c9b0a1122",
          "story_ref":{"source_id":"src_1b2c3d4e5f607182","project":"holdspeak","story_id":"HS-94-09"},
          "node_id":"node_9f8e7d6c5b4a3921","worktree_id":"wt_78695a4b3c2d1e0f",
          "session_id":"claude:hs-94-09","target_id":"%12",
          "association":{"kind":"rider_claim","claimed_by":"rider:claude","claimed_at":"2026-07-15T08:02:11Z"},
          "exact":true,"state":"working","started_at":"2026-07-15T08:02:11Z",
          "updated_at":"2026-07-15T09:29:50Z","ended_at":null,
          "history":[{"from":null,"to":"starting","reason":"created:rider_claim","occurred_at":"2026-07-15T08:02:11Z"}]}]}
        """#)
        let view = try await client().deliveryAttempts(
            project: "holdspeak", storyId: "HS-94-09", activeOnly: true
        )
        XCTAssertEqual(view.attemptsSchema, 1)
        XCTAssertEqual(view.attempts[0].association?.kind, .riderClaim)
        XCTAssertEqual(view.attempts[0].state, .working)
        XCTAssertEqual(view.attempts[0].history?.count, 1)
        let query = StubProtocol.lastURL?.query ?? ""
        XCTAssertTrue(query.contains("project=holdspeak"))
        XCTAssertTrue(query.contains("story_id=HS-94-09"))
        XCTAssertTrue(query.contains("active_only=true"))
    }

    func testStoryDossierDecodes() async throws {
        route("/api/delivery/stories/holdspeak/HS-94-05/dossier", 200, #"""
        {"dossier_schema":1,"bundle_id":"bundle-3c4d5e6f708192a3","bundle_changed":false,
         "live_bundle_id":null,"freshness":"live","detail":"",
         "source_id":"src_1b2c3d4e5f607182","project":"holdspeak","story_id":"HS-94-05",
         "phase":94,"status":"done",
         "source_revision":{"head_sha":"174aa374","index_tree":"9a8b7c6d"},
         "summary":{"passing_captures":1,"failing_captures":0,"assets":2},
         "members":[{"asset_id":"a-1a2b3c4d5e6f7081","role":"story_markdown","label":"Story",
          "media_type":"text/markdown","bytes":3412,"sha256":"sha256:aa11"}],
         "captured_runs":[{"timestamp":"2026-07-14T16:41:02Z","command":"uv run pytest -q",
          "exit_code":0,"passed":true}],
         "trace":{"story_asset_id":"a-1a2b3c4d5e6f7081","evidence_asset_id":null,
          "phase_status_asset_id":null,"final_summary_asset_id":null},
         "story":{"asset_id":"a-1a2b3c4d5e6f7081","state":"ready","markdown":"# HS-94-05"},
         "evidence":[]}
        """#)
        let dossier = try await client().storyDossier(project: "holdspeak", story: "HS-94-05")
        XCTAssertEqual(dossier.dossierSchema, 1)
        XCTAssertEqual(dossier.freshness, .live)
        XCTAssertEqual(dossier.capturedRuns?[0].passed, true)
        XCTAssertEqual(dossier.story?.state, "ready")
    }

    func testStoryDossierPinsTheSourceInTheQuery() async throws {
        route("/api/delivery/stories/holdspeak/HS-94-05/dossier", 200,
              #"{"dossier_schema":1,"bundle_id":"bundle-3c4d5e6f708192a3"}"#)
        _ = try await client().storyDossier(
            project: "holdspeak", story: "HS-94-05", source: "src_1b2c3d4e5f607182"
        )
        XCTAssertEqual(StubProtocol.lastURL?.query, "source=src_1b2c3d4e5f607182")
    }

    func testDossierRefusalIsTypedAndPreservesTheManifest() async throws {
        // bundle_changed answers 409 with the CACHED manifest riding the body
        // (§13) — the client surfaces it typed, never an opaque status code.
        route("/api/delivery/stories/holdspeak/HS-94-05/dossier", 409, #"""
        {"refusal":"bundle_changed","detail":"the source moved past this bundle; re-fetch the dossier",
         "manifest":{"bundle_id":"bundle-3c4d5e6f708192a3","bundle_changed":true,
          "live_bundle_id":"bundle-99887766554433aa","freshness":"cached",
          "members":[{"asset_id":"a-4d5e6f708192a3b4","role":"asset","label":"proof.png",
           "media_type":"image/png","bytes":48213,"sha256":"sha256:dd44"}]}}
        """#)
        do {
            _ = try await client().storyDossier(project: "holdspeak", story: "HS-94-05")
            XCTFail("a typed refusal must throw DeliveryRefusalError")
        } catch let error as DeliveryRefusalError {
            XCTAssertEqual(error.refusal.refusal, .bundleChanged)
            XCTAssertEqual(error.refusal.manifest?.liveBundleId, "bundle-99887766554433aa")
            XCTAssertEqual(error.refusal.manifest?.members?.count, 1)  // metadata preserved
        }
    }

    func testDossierServerFailureStaysAnHTTPError() async throws {
        // A classified 500 carries {"error": ...}, not a refusal envelope —
        // it surfaces as the plain HTTP error, never a fake refusal.
        route("/api/delivery/stories/holdspeak/HS-94-05/dossier", 500,
              #"{"error":"story dossier failed"}"#)
        do {
            _ = try await client().storyDossier(project: "holdspeak", story: "HS-94-05")
            XCTFail("a 500 must throw")
        } catch let error as HTTPDesktopClient.DesktopClientError {
            XCTAssertEqual(error, .http(500))
        }
    }
}
