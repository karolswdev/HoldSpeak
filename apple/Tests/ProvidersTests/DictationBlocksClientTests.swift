import XCTest
import Contracts
@testable import Providers

/// HSM-18-01 — the rest of the dictation-pipeline client: blocks (read + CRUD), block-templates,
/// project-context. Network stubbed via `URLProtocol`; deterministic and offline. Proves the
/// snake_case hub wire decodes into the Contracts types, the Bearer token rides, the query params
/// (scope / project_root) are carried, the CRUD verbs/paths are right, and the create/update bodies
/// round-trip a block back to snake_case JSON.
final class DictationBlocksClientTests: XCTestCase {

    // MARK: stub (matches on path; query carried separately)

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastQuery: String?
        nonisolated(unsafe) static var lastMethod: String?
        nonisolated(unsafe) static var lastBody: [String: Any]?
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastQuery = request.url?.query
            StubProtocol.lastMethod = request.httpMethod
            // URLProtocol strips httpBody onto the body stream; read it back.
            if let stream = request.httpBodyStream {
                stream.open()
                var data = Data()
                let bufSize = 4096
                let buf = UnsafeMutablePointer<UInt8>.allocate(capacity: bufSize)
                while stream.hasBytesAvailable {
                    let read = stream.read(buf, maxLength: bufSize)
                    if read <= 0 { break }
                    data.append(buf, count: read)
                }
                buf.deallocate()
                stream.close()
                StubProtocol.lastBody = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            } else if let body = request.httpBody {
                StubProtocol.lastBody = (try? JSONSerialization.jsonObject(with: body)) as? [String: Any]
            } else {
                StubProtocol.lastBody = nil
            }
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
        StubProtocol.lastMethod = nil
        StubProtocol.lastBody = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    // MARK: - contract decode round-trips (faithful to blocks.py / agent.py)

    func testBlocksResultDecodesRealEnvelope() throws {
        let json = #"""
        {
          "scope": "global",
          "path": "/home/me/.holdspeak/blocks.yaml",
          "exists": true,
          "project": null,
          "document": {
            "version": 1,
            "default_match_confidence": 0.6,
            "blocks": [
              {
                "id": "action_item",
                "description": "User is capturing a task.",
                "match": {
                  "examples": ["follow up with Sam"],
                  "negative_examples": ["write a paragraph"],
                  "threshold": 0.7
                },
                "inject": { "mode": "replace", "template": "Action item: {raw_text}" }
              }
            ]
          }
        }
        """#
        let result = try HoldSpeakContracts.decoder().decode(DictationBlocksResult.self, from: Data(json.utf8))
        XCTAssertEqual(result.scope, "global")
        XCTAssertEqual(result.exists, true)
        XCTAssertEqual(result.document.version, 1)
        XCTAssertEqual(result.document.defaultMatchConfidence, 0.6)
        XCTAssertEqual(result.document.blocks.count, 1)
        let block = try XCTUnwrap(result.document.blocks.first)
        XCTAssertEqual(block.id, "action_item")
        XCTAssertEqual(block.match?.examples, ["follow up with Sam"])
        XCTAssertEqual(block.match?.negativeExamples, ["write a paragraph"])
        XCTAssertEqual(block.match?.threshold, 0.7)
        XCTAssertEqual(block.inject?.mode, "replace")
        XCTAssertEqual(block.inject?.template, "Action item: {raw_text}")
    }

    func testBlocksDocumentToleratesMissingDefaults() throws {
        // A bare document (only blocks) still decodes — robust against shape drift.
        let json = #"{"document": {"blocks": [{"id": "only"}]}}"#
        let result = try HoldSpeakContracts.decoder().decode(DictationBlocksResult.self, from: Data(json.utf8))
        XCTAssertNil(result.document.version)
        XCTAssertEqual(result.document.blocks.first?.id, "only")
        XCTAssertNil(result.document.blocks.first?.match)
    }

    func testBlockTemplateDecodesMetadataAndBlock() throws {
        let json = #"""
        {"templates": [
          {
            "id": "action_item",
            "title": "Action item",
            "description": "Turn task dictation into a line.",
            "sample_utterance": "follow up with Sam about the launch checklist",
            "requires_project": false,
            "block": { "id": "action_item", "inject": { "mode": "replace", "template": "Action item: {raw_text}" } }
          }
        ]}
        """#
        struct Envelope: Codable { var templates: [DictationBlockTemplate] }
        let env = try HoldSpeakContracts.decoder().decode(Envelope.self, from: Data(json.utf8))
        let t = try XCTUnwrap(env.templates.first)
        XCTAssertEqual(t.id, "action_item")
        XCTAssertEqual(t.title, "Action item")
        XCTAssertEqual(t.sampleUtterance, "follow up with Sam about the launch checklist")
        XCTAssertEqual(t.requiresProject, false)
        XCTAssertEqual(t.block?.inject?.mode, "replace")
    }

    func testProjectContextDecodesProjectAndPaths() throws {
        let json = #"""
        {
          "project": { "name": "holdspeak", "root": "/Users/me/holdspeak", "anchor": ".git" },
          "paths": {
            "blocks": "/Users/me/holdspeak/.holdspeak/blocks.yaml",
            "project_kb": "/Users/me/holdspeak/.holdspeak/project.yaml"
          }
        }
        """#
        let ctx = try HoldSpeakContracts.decoder().decode(DictationProjectContext.self, from: Data(json.utf8))
        XCTAssertEqual(ctx.project.name, "holdspeak")
        XCTAssertEqual(ctx.project.root, "/Users/me/holdspeak")
        XCTAssertEqual(ctx.project.anchor, ".git")
        XCTAssertEqual(ctx.paths?.blocks, "/Users/me/holdspeak/.holdspeak/blocks.yaml")
        XCTAssertEqual(ctx.paths?.projectKb, "/Users/me/holdspeak/.holdspeak/project.yaml")
    }

    // MARK: - over the client (Bearer + query + verb/path)

    func testDictationBlocksSendsTokenScopeAndDecodes() async throws {
        StubProtocol.routes = [
            "/api/dictation/blocks": (200, Data(#"{"scope":"project","document":{"blocks":[{"id":"b1"}]}}"#.utf8)),
        ]
        let result = try await client(token: "t0ken").dictationBlocks(scope: "project", projectRoot: "/Users/me/app")
        XCTAssertEqual(result.scope, "project")
        XCTAssertEqual(result.document.blocks.first?.id, "b1")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer t0ken")
        XCTAssertEqual(StubProtocol.lastMethod, "GET")
        let q = try XCTUnwrap(StubProtocol.lastQuery)
        XCTAssertTrue(q.contains("scope=project"), q)
        XCTAssertTrue(q.contains("project_root=") && q.contains("app"), q)
    }

    func testBlockTemplatesUnwrapsEnvelope() async throws {
        StubProtocol.routes = [
            "/api/dictation/block-templates": (200, Data(#"{"templates":[{"id":"action_item","title":"Action item"}]}"#.utf8)),
        ]
        let templates = try await client(token: "abc").blockTemplates()
        XCTAssertEqual(templates.count, 1)
        XCTAssertEqual(templates.first?.id, "action_item")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer abc")
    }

    func testProjectContextSendsProjectRootQuery() async throws {
        StubProtocol.routes = [
            "/api/dictation/project-context": (200, Data(#"{"project":{"name":"holdspeak","root":"/r"}}"#.utf8)),
        ]
        let ctx = try await client(token: "xyz").projectContext(projectRoot: "/r")
        XCTAssertEqual(ctx.project.name, "holdspeak")
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer xyz")
        XCTAssertEqual(try XCTUnwrap(StubProtocol.lastQuery), "project_root=/r")
    }

    func testCreateBlockPostsSnakeCaseBlockBody() async throws {
        StubProtocol.routes = [
            "/api/dictation/blocks": (201, Data(#"{"scope":"global","document":{"blocks":[{"id":"new"}]}}"#.utf8)),
        ]
        let block = DictationBlock(
            id: "new",
            description: "a new block",
            match: .init(examples: ["hi"], negativeExamples: ["bye"], threshold: 0.7),
            inject: .init(mode: "append", template: "x")
        )
        let result = try await client(token: "t").createBlock(block)
        XCTAssertEqual(result.document.blocks.first?.id, "new")
        XCTAssertEqual(StubProtocol.lastMethod, "POST")
        let body = try XCTUnwrap(StubProtocol.lastBody)
        let sent = try XCTUnwrap(body["block"] as? [String: Any])
        XCTAssertEqual(sent["id"] as? String, "new")
        // .convertToSnakeCase: negativeExamples -> negative_examples on the wire.
        let match = try XCTUnwrap(sent["match"] as? [String: Any])
        XCTAssertNotNil(match["negative_examples"])
        XCTAssertNil(match["negativeExamples"])
    }

    func testUpdateBlockUsesPutAndIdInPath() async throws {
        StubProtocol.routes = [
            "/api/dictation/blocks/action_item": (200, Data(#"{"document":{"blocks":[{"id":"action_item"}]}}"#.utf8)),
        ]
        let result = try await client(token: "t").updateBlock("action_item",
                                                               with: DictationBlock(id: "action_item", description: "edited"))
        XCTAssertEqual(result.document.blocks.first?.id, "action_item")
        XCTAssertEqual(StubProtocol.lastMethod, "PUT")
        XCTAssertNotNil(StubProtocol.lastBody?["block"])
    }

    func testDeleteBlockUsesDeleteVerb() async throws {
        StubProtocol.routes = [
            "/api/dictation/blocks/stale": (200, Data(#"{"document":{"blocks":[{"id":"keep"}]}}"#.utf8)),
        ]
        let result = try await client(token: "t").deleteBlock("stale", scope: "project", projectRoot: "/p")
        XCTAssertEqual(result.document.blocks.first?.id, "keep")
        XCTAssertEqual(StubProtocol.lastMethod, "DELETE")
        let q = try XCTUnwrap(StubProtocol.lastQuery)
        XCTAssertTrue(q.contains("scope=project"), q)
    }

    func testDeleteLastBlock422SurfacesAsHTTPError() async {
        // blocks.py rejects deleting the last block (save requires >= 1) with a 422.
        StubProtocol.routes = ["/api/dictation/blocks/only": (422, Data(#"{"error":"at least one block required"}"#.utf8))]
        do {
            _ = try await client(token: "t").deleteBlock("only")
            XCTFail("expected an http error")
        } catch let HTTPDesktopClient.DesktopClientError.http(code) {
            XCTAssertEqual(code, 422)
        } catch {
            XCTFail("unexpected error: \(error)")
        }
    }

    func testBlocksThrowsMalformedOnBadJSON() async {
        StubProtocol.routes = ["/api/dictation/blocks": (200, Data(#"{ not json"#.utf8))]
        do {
            _ = try await client().dictationBlocks()
            XCTFail("expected malformed")
        } catch HTTPDesktopClient.DesktopClientError.malformed {
            // expected
        } catch {
            XCTFail("unexpected error: \(error)")
        }
    }
}
