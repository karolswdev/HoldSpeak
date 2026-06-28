import XCTest
import Contracts
@testable import Providers

/// HS-19-03 (mobile) — the meeting-import client. Network stubbed via `URLProtocol`;
/// deterministic and offline. Proves: `importMeeting(...)` POSTs a well-formed
/// `multipart/form-data` body with the hub's single `file` field and the declared
/// boundary, the Bearer token rides, the `202 {meeting_id, status}` decodes into
/// `MeetingImportResult`, a non-2xx rejection throws `.http`, and the contract type
/// round-trips realistic + partial hub payloads.
final class MeetingImportClientTests: XCTestCase {

    // MARK: stub — captures the auth header, Content-Type, and the full request body.
    // `URLProtocol` exposes a non-stream `httpBody` as `httpBodyStream`, so the body
    // is read off the stream to assert the multipart parts.

    final class StubProtocol: URLProtocol {
        nonisolated(unsafe) static var routes: [String: (Int, Data)] = [:]
        nonisolated(unsafe) static var lastAuth: String??
        nonisolated(unsafe) static var lastContentType: String??
        nonisolated(unsafe) static var lastBody: Data?

        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for r: URLRequest) -> URLRequest { r }
        override func startLoading() {
            StubProtocol.lastAuth = request.value(forHTTPHeaderField: "Authorization")
            StubProtocol.lastContentType = request.value(forHTTPHeaderField: "Content-Type")
            StubProtocol.lastBody = Self.readBody(from: request)
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

        private static func readBody(from request: URLRequest) -> Data? {
            if let body = request.httpBody { return body }
            guard let stream = request.httpBodyStream else { return nil }
            stream.open()
            defer { stream.close() }
            var data = Data()
            let size = 4096
            var buffer = [UInt8](repeating: 0, count: size)
            while stream.hasBytesAvailable {
                let read = stream.read(&buffer, maxLength: size)
                if read <= 0 { break }
                data.append(buffer, count: read)
            }
            return data
        }
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
        StubProtocol.lastContentType = nil
        StubProtocol.lastBody = nil
    }

    private func client(token: String? = nil) -> HTTPDesktopClient {
        HTTPDesktopClient(config: .init(baseURL: URL(string: "http://desk.tailnet:8000")!, token: token),
                          session: stubbedSession())
    }

    /// Write a small payload to a temp file and return its URL (the picked recording).
    private func tempFile(_ bytes: Data, ext: String) throws -> URL {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("hsimport-\(UUID().uuidString).\(ext)")
        try bytes.write(to: url)
        return url
    }

    // MARK: - MeetingImportResult contract decode

    func testResultDecodesRealisticPayload() throws {
        let json = #"{"meeting_id":"a1b2c3d4","status":"importing"}"#
        let result = try HoldSpeakContracts.decoder().decode(MeetingImportResult.self, from: Data(json.utf8))
        XCTAssertEqual(result.meetingID, "a1b2c3d4")
        XCTAssertEqual(result.status, "importing")
    }

    func testResultDefaultsStatusWhenMissing() throws {
        // A partial payload (only the id) still decodes, defaulting to `importing`.
        let result = try HoldSpeakContracts.decoder().decode(MeetingImportResult.self, from: Data(#"{"meeting_id":"x9"}"#.utf8))
        XCTAssertEqual(result.meetingID, "x9")
        XCTAssertEqual(result.status, "importing")
    }

    func testErrorBodyDecodes() throws {
        let body = try HoldSpeakContracts.decoder().decode(MeetingImportErrorBody.self, from: Data(#"{"error":"Unsupported format: .pages"}"#.utf8))
        XCTAssertEqual(body.error, "Unsupported format: .pages")
    }

    // MARK: - importMeeting(...) over the client

    func testImportMeetingSendsMultipartFieldBoundaryAndBearer() async throws {
        StubProtocol.routes = [
            "/api/meetings/import": (202, Data(#"{"meeting_id":"a1b2c3d4","status":"importing"}"#.utf8)),
        ]
        let fileURL = try tempFile(Data("RIFFfake-wav-bytes".utf8), ext: "wav")
        defer { try? FileManager.default.removeItem(at: fileURL) }

        let result = try await client(token: "t0ken")
            .importMeeting(fileURL: fileURL, filename: "standup.wav", mimeType: "audio/wav")

        // Response decodes faithfully.
        XCTAssertEqual(result.meetingID, "a1b2c3d4")
        XCTAssertEqual(result.status, "importing")

        // Bearer rides.
        XCTAssertEqual(StubProtocol.lastAuth, "Bearer t0ken")

        // Content-Type is multipart and declares a boundary the body uses.
        let contentType = try XCTUnwrap(StubProtocol.lastContentType ?? nil)
        XCTAssertTrue(contentType.hasPrefix("multipart/form-data; boundary="), contentType)
        let boundary = String(contentType.dropFirst("multipart/form-data; boundary=".count))
        XCTAssertFalse(boundary.isEmpty)

        // The body carries exactly the hub's `file` field, the filename, the part's
        // declared boundary (open + close), and the file bytes verbatim.
        let body = try XCTUnwrap(StubProtocol.lastBody)
        let text = String(decoding: body, as: UTF8.self)
        XCTAssertTrue(text.contains("--\(boundary)\r\n"), "open boundary missing")
        XCTAssertTrue(text.contains("--\(boundary)--"), "close boundary missing")
        XCTAssertTrue(text.contains("name=\"file\""), "hub field name must be `file`")
        XCTAssertTrue(text.contains("filename=\"standup.wav\""), "filename missing")
        XCTAssertTrue(text.contains("Content-Type: audio/wav"), "part content-type missing")
        XCTAssertTrue(text.contains("RIFFfake-wav-bytes"), "file bytes missing from body")
    }

    func testImportMeetingTranscriptUsesGivenMimeAndFilename() async throws {
        StubProtocol.routes = [
            "/api/meetings/import": (202, Data(#"{"meeting_id":"vtt001","status":"importing"}"#.utf8)),
        ]
        let fileURL = try tempFile(Data("WEBVTT\n\n00:00.000 --> 00:01.000\nhi".utf8), ext: "vtt")
        defer { try? FileManager.default.removeItem(at: fileURL) }

        let result = try await client()
            .importMeeting(fileURL: fileURL, filename: "call.vtt", mimeType: "text/vtt")

        XCTAssertEqual(result.meetingID, "vtt001")
        let text = String(decoding: try XCTUnwrap(StubProtocol.lastBody), as: UTF8.self)
        XCTAssertTrue(text.contains("filename=\"call.vtt\""))
        XCTAssertTrue(text.contains("Content-Type: text/vtt"))
    }

    func testImportMeetingThrowsHTTPOnRejection() async throws {
        // The hub rejects an unsupported format with a 400 + error body.
        StubProtocol.routes = ["/api/meetings/import": (400, Data(#"{"error":"Unsupported format: .pages"}"#.utf8))]
        let fileURL = try tempFile(Data("nope".utf8), ext: "pages")
        defer { try? FileManager.default.removeItem(at: fileURL) }
        do {
            _ = try await client().importMeeting(fileURL: fileURL, filename: "doc.pages", mimeType: "application/octet-stream")
            XCTFail("expected an http error")
        } catch let HTTPDesktopClient.DesktopClientError.http(code) {
            XCTAssertEqual(code, 400)
        } catch {
            XCTFail("unexpected error: \(error)")
        }
    }
}
