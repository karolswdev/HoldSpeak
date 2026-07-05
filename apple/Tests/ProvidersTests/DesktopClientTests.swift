import XCTest
import Contracts
@testable import Providers

/// HSM-12-01 — the desktop client seam + pairing. Network stubbed via `URLProtocol`;
/// fully deterministic and offline (no real desktop). Proves: pairing → handshake
/// against /health + /api/runtime/status, an honest egress label, the token rides as
/// a Bearer header, and an unreachable peer fails soft (never throws → `.offline`).
final class DesktopClientTests: XCTestCase {

    // MARK: stub

    final class StubProtocol: URLProtocol {
        /// path -> (status, body). A missing path → network failure (simulated down).
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastMethod: String?
        nonisolated(unsafe) static var failEverything = false
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        nonisolated(unsafe) static var lastBody: Data?
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastMethod = request.httpMethod
            if let stream = request.httpBodyStream {
                stream.open(); defer { stream.close() }
                var data = Data()
                let buf = UnsafeMutablePointer<UInt8>.allocate(capacity: 1024)
                defer { buf.deallocate() }
                while stream.hasBytesAvailable {
                    let n = stream.read(buf, maxLength: 1024)
                    if n <= 0 { break }
                    data.append(buf, count: n)
                }
                StubProtocol.lastBody = data
            } else {
                StubProtocol.lastBody = request.httpBody
            }
            let path = request.url?.path ?? ""
            if StubProtocol.failEverything || StubProtocol.routes[path] == nil {
                client?.urlProtocol(self, didFailWithError: URLError(.cannotConnectToHost))
                return
            }
            let (status, body) = StubProtocol.routes[path]!
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
        StubProtocol.failEverything = false
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    private func runtimeStatus(_ json: String) -> Data { Data(json.utf8) }

    // MARK: pairing

    func testPeerBuildsConfigFromHostPortToken() throws {
        let peer = DesktopPeer(host: "desk.tailnet", port: 8000, token: "t0ken")
        let config = try XCTUnwrap(HTTPDesktopClient.Config(peer: peer))
        XCTAssertEqual(config.baseURL.absoluteString, "http://desk.tailnet:8000")
        XCTAssertEqual(config.token, "t0ken")
    }

    func testMalformedPeerYieldsNoConfig() {
        // An empty host has no valid URL → no config (the client then stays offline).
        XCTAssertNil(HTTPDesktopClient.Config(peer: DesktopPeer(host: "", port: 0)))
    }

    // MARK: handshake — reachable

    func testHandshakeReachableAndRuntimeReady() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok","mode":"web","meeting_active":false}"#)),
        ]
        let conn = await client().handshake()
        XCTAssertTrue(conn.reachable)
        XCTAssertTrue(conn.runtimeReady)
        XCTAssertTrue(conn.detail.contains("web"))   // summary surfaces the mode
    }

    func testHandshakeSurfacesActiveMeeting() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok","mode":"web","meeting_active":true}"#)),
        ]
        let conn = await client().handshake()
        XCTAssertTrue(conn.runtimeReady)
        XCTAssertEqual(conn.detail, "meeting active")
    }

    func testHandshakeReachableButRuntimeStatusUnavailable() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (500, Data()),
        ]
        let conn = await client().handshake()
        XCTAssertTrue(conn.reachable)        // health passed
        XCTAssertFalse(conn.runtimeReady)    // status did not
        XCTAssertEqual(conn.detail, "runtime status unavailable")
    }

    // MARK: handshake — offline (fail soft, never throw)

    func testHandshakeUnreachableFailsSoft() async {
        StubProtocol.failEverything = true   // peer down
        let conn = await client().handshake()   // must NOT throw — no try
        XCTAssertFalse(conn.reachable)
        XCTAssertFalse(conn.runtimeReady)
        XCTAssertTrue(conn.detail.hasPrefix("desktop unreachable"))
    }

    func testHandshakeBadHealthStatusIsOffline() async {
        StubProtocol.routes = ["/health": (404, Data())]
        let conn = await client().handshake()
        XCTAssertFalse(conn.reachable)
        XCTAssertTrue(conn.detail.contains("404"))
    }

    // MARK: egress + token

    func testEgressLabelIsHonest() {
        let label = client().egressLabel
        XCTAssertTrue(label.contains("LAN"))
        XCTAssertTrue(label.contains("desk.tailnet"))
    }

    func testTokenRidesAsBearerAndIsNotInEgress() async {
        StubProtocol.routes = [
            "/health": (200, Data(#"{"status":"ok"}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok"}"#)),
        ]
        let c = client(token: "s3cret")
        _ = await c.handshake()
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer s3cret")   // joined at call time
        XCTAssertFalse(c.egressLabel.contains("s3cret"))         // never leaked to the badge
    }

    // MARK: meetings remote control (HSM-12-02)

    func testListMeetingsDecodesServerShape() async throws {
        // The REAL hub emits `m.started_at.isoformat()` over a NAIVE `datetime.now()`:
        // no `Z`, no offset, microsecond fractional (e.g. 2026-06-27T18:08:21.337333).
        // The shared decoder's `.iso8601` strategy rejects that exact shape, so a
        // `Date?` field would throw and fail the WHOLE list decode on the live archive.
        // `startedAt`/`endedAt` are carried as `String?` (metal-readiness); this feeds
        // the naive shape and asserts it round-trips verbatim.
        StubProtocol.routes = ["/api/meetings": (200, Data(#"""
        {"meetings":[
          {"id":"m1","title":"Arch review","started_at":"2026-06-27T18:08:21.337333","ended_at":null,
           "duration_seconds":1800,"segment_count":42,"action_item_count":3,"intel_status":"ready"},
          {"id":"m2","title":"Standup","started_at":"2026-06-19T09:00:00","duration_seconds":600}
        ],"total":2}
        """#.utf8))]
        let meetings = try await client().listMeetings()
        XCTAssertEqual(meetings.count, 2)
        XCTAssertEqual(meetings[0].id, "m1")
        XCTAssertEqual(meetings[0].title, "Arch review")
        XCTAssertEqual(meetings[0].startedAt, "2026-06-27T18:08:21.337333")  // naive ISO survives
        XCTAssertEqual(meetings[0].actionItemCount, 3)
        XCTAssertEqual(meetings[0].intelStatus, "ready")
        XCTAssertEqual(meetings[1].id, "m2")          // second decodes with fields absent
        XCTAssertNil(meetings[1].endedAt)
    }

    func testRuntimeStateDecodesActiveMeeting() async throws {
        StubProtocol.routes = ["/api/runtime/status": (200,
            runtimeStatus(#"{"status":"ok","mode":"web","meeting_active":true,"meeting_id":"m9"}"#))]
        let s = try await client().runtimeState()
        XCTAssertEqual(s.status, "ok")
        XCTAssertTrue(s.meetingActive)
        XCTAssertEqual(s.meetingId, "m9")
    }

    func testStartMeetingPostsThenReflectsLiveState() async throws {
        StubProtocol.routes = [
            "/api/meeting/start": (200, Data(#"{"success":true}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok","meeting_active":true,"meeting_id":"m1"}"#)),
        ]
        let s = try await client().startMeeting(title: "Kickoff")
        XCTAssertEqual(StubProtocol.lastMethod, "GET")   // last call is the status read-back
        XCTAssertTrue(s.meetingActive)
        XCTAssertEqual(s.meetingId, "m1")
    }

    func testStopMeetingPostsThenReflectsIdle() async throws {
        StubProtocol.routes = [
            "/api/meeting/stop": (200, Data(#"{"success":true}"#.utf8)),
            "/api/runtime/status": (200, runtimeStatus(#"{"status":"ok","meeting_active":false}"#)),
        ]
        let s = try await client().stopMeeting()
        XCTAssertFalse(s.meetingActive)
    }

    func testListMeetingsHTTPErrorThrows() async {
        StubProtocol.routes = ["/api/meetings": (500, Data())]
        do { _ = try await client().listMeetings(); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 500) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: answer the coder (HSM-13-01)

    func testSendRemoteDictationPostsAndDecodes() async throws {
        StubProtocol.routes = ["/api/dictation/remote": (200,
            Data(#"{"success":true,"final_text":"[corrected] ship it","delivered":true}"#.utf8))]
        let result = try await client(token: "tok").sendRemoteDictation(text: "ship it")
        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer tok")        // the mirrored token rides
        XCTAssertTrue(result.success)
        XCTAssertTrue(result.delivered)
        XCTAssertEqual(result.finalText, "[corrected] ship it")    // processed, not raw
    }

    func testSendRemoteDictationHTTPErrorThrows() async {
        StubProtocol.routes = ["/api/dictation/remote": (401, Data())]   // bad/missing token
        do { _ = try await client().sendRemoteDictation(text: "hi"); XCTFail("expected throw") }
        catch HTTPDesktopClient.DesktopClientError.http(let code) { XCTAssertEqual(code, 401) }
        catch { XCTFail("wrong error: \(error)") }
    }

    // MARK: raw (verbatim) delivery for a previewed receipt (HSM-18-01)

    func testRawRidesTheWireOnlyWhenTrue() async throws {
        StubProtocol.routes = ["/api/dictation/remote": (200,
            Data(#"{"success":true,"final_text":"exact words","delivered":true}"#.utf8))]

        _ = try await client().sendRemoteDictation(text: "exact words", target: .focused, raw: true)
        var body = try XCTUnwrap(JSONSerialization.jsonObject(
            with: XCTUnwrap(StubProtocol.lastBody)) as? [String: Any])
        XCTAssertEqual(body["raw"] as? Bool, true)
        XCTAssertEqual(body["target_mode"] as? String, "focused")

        // Default path: no `raw` key at all — the pre-18-01 payload, byte-identical.
        _ = try await client().sendRemoteDictation(text: "hi", target: .focused)
        body = try XCTUnwrap(JSONSerialization.jsonObject(
            with: XCTUnwrap(StubProtocol.lastBody)) as? [String: Any])
        XCTAssertNil(body["raw"])
    }

    // MARK: hub runs return the run-born artifact id (HSM-18-07)

    func testRunAgentDecodesArtifactId() async throws {
        // v6 (Phase 74): the hub persists the run's output as a run-born
        // artifact and returns its id — the desk card must reuse it so a kept
        // card reconciles with the hub's artifact on sync, never duplicates.
        StubProtocol.routes = ["/api/recipes/a-owl/run": (200,
            Data(#"{"output":"the run output","artifact_id":"art_run_1"}"#.utf8))]
        let result = try await client(token: "tok").runRecipe(id: "a-owl", input: "say hi")
        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        XCTAssertEqual(result.output, "the run output")
        XCTAssertEqual(result.artifactId, "art_run_1")
    }

    func testRunChainWithoutArtifactIdStillDecodes() async throws {
        // An older hub omits artifact_id — the decode stays tolerant.
        StubProtocol.routes = ["/api/chains/c1/run": (200,
            Data(#"{"output":"crew says hi","steps":["Scout: hi"]}"#.utf8))]
        let result = try await client().runChain(id: "c1", input: "go")
        XCTAssertEqual(result.output, "crew says hi")
        XCTAssertEqual(result.steps, ["Scout: hi"])
        XCTAssertNil(result.artifactId)
    }
}

// MARK: - HSM-17-02/03: the live coder set

extension DesktopClientTests {

    /// The wire shape below is the REAL payload the hub served during the
    /// HSM-17-02 real-metal proof (a live claude blocked on a permission ask),
    /// trimmed to the fields the client reads plus extras it must tolerate.
    func testCoderSessionsDecodesTheLiveSetWireShape() async throws {
        let wire = """
        {"sessions": [
          {"session": {"agent": "claude", "session_id": "d19676dc-81ee-4",
            "cwd": "/private/tmp/scratch/proof-repo", "updated_at": "2026-07-04T17:20:00Z",
            "hook_event_name": "Notification", "project_name": "proof-repo",
            "model": "claude-fable-5", "last_prompt": "commit it", "last_tool_name": "Bash",
            "awaiting_response": false, "capture_messages": true, "event_count": 7,
            "pinned": false, "lifecycle": "waiting", "question": "Claude needs your permission",
            "state": "waiting"},
           "age_seconds": 12,
           "identity": {"agent_label": "Claude", "target_confidence": "high"}},
          {"session": {"agent": "codex", "session_id": "019f2e2e",
            "cwd": "/private/tmp/scratch/proof-repo", "state": "working",
            "lifecycle": "working", "question": null, "event_count": 5, "pinned": false},
           "age_seconds": 3, "identity": null}
        ], "count": 2}
        """
        StubProtocol.routes["/api/coders/sessions"] = (200, Data(wire.utf8))

        let sessions = try await client().coderSessions()

        XCTAssertEqual(sessions.count, 2)
        let claude = try XCTUnwrap(sessions.first { $0.agent == "claude" })
        XCTAssertEqual(claude.sessionID, "d19676dc-81ee-4")
        XCTAssertEqual(claude.state, "waiting")
        XCTAssertEqual(claude.question, "Claude needs your permission")
        XCTAssertEqual(claude.project, "proof-repo")
        XCTAssertEqual(claude.model, "claude-fable-5")
        XCTAssertEqual(claude.lastPrompt, "commit it")
        XCTAssertEqual(claude.lastTool, "Bash")
        XCTAssertEqual(claude.eventCount, 7)
        XCTAssertEqual(claude.ageSeconds, 12)
        let codex = try XCTUnwrap(sessions.first { $0.agent == "codex" })
        XCTAssertEqual(codex.state, "working")
        XCTAssertNil(codex.question)
    }

    func testCoderSessionsToleratesEmptyAndSkipsMalformedItems() async throws {
        StubProtocol.routes["/api/coders/sessions"] =
            (200, Data(#"{"sessions": [{"session": {"agent": "claude"}}, {}], "count": 2}"#.utf8))

        let sessions = try await client().coderSessions()

        XCTAssertEqual(sessions, [])  // no session_id -> skipped, never invented
    }

    func testCoderSessionsThrowsOnHTTPError() async {
        StubProtocol.routes["/api/coders/sessions"] = (500, Data())

        do {
            _ = try await client().coderSessions()
            XCTFail("expected an error")
        } catch {
            XCTAssertEqual(error as? HTTPDesktopClient.DesktopClientError, .http(500))
        }
    }

    func testDefaultConformerReportsCoderSessionsUnsupported() async {
        struct Bare: IDesktopClient {
            func handshake() async -> DesktopConnection { .offline("test") }
            var egressLabel: String { "test" }
            func listMeetings() async throws -> [MeetingSummary] { [] }
            func runtimeState() async throws -> RuntimeState { RuntimeState(status: "x", mode: nil, meetingActive: false, meetingId: nil) }
            func startMeeting(title: String?) async throws -> RuntimeState { try await runtimeState() }
            func stopMeeting() async throws -> RuntimeState { try await runtimeState() }
            func sendRemoteDictation(text: String, target: DictationTarget, raw: Bool) async throws -> RemoteDictationResult {
                RemoteDictationResult(success: false, finalText: "", delivered: false)
            }
            func companionStatus() async throws -> CompanionBoardState { CompanionBoardState() }
            func selectCompanionTarget(agent: String, sessionID: String) async throws {}
            func dismissCompanionTarget(agent: String, sessionID: String) async throws {}
            func pinCompanionTarget(agent: String, sessionID: String, pinned: Bool) async throws {}
        }

        do {
            _ = try await Bare().coderSessions()
            XCTFail("expected notImplemented")
        } catch {
            XCTAssertEqual(error as? HubRunUnsupported, .notImplemented)
        }
    }
}
