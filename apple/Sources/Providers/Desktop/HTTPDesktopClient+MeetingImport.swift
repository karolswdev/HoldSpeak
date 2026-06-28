import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HS-19-03 (mobile) — import a recording or transcript from the iPad into the
// desktop hub's full intel pipeline (`POST /api/meetings/import`). The hub's
// route reads ONE multipart field named `file` (`file: UploadFile = File(...)`),
// refuses unsupported formats up front, creates the meeting row immediately in a
// visible `importing` state, and returns `202 {meeting_id, status}` while Whisper
// (audio) or the parser (.vtt/.srt/.txt) runs on a background thread.
//
// Kept in a SEPARATE extension file (no edits to HTTPDesktopClient.swift) so this
// slice lands without colliding with the other client methods in the same wave.
// The Bearer auth + non-2xx → `DesktopClientError.http` mirror the base client, but
// the multipart body is built inline here so this file owns no dependency on the
// base type's private JSON helpers.
extension HTTPDesktopClient {

    /// `POST /api/meetings/import` — upload an on-device recording or transcript file
    /// as `multipart/form-data` (the single hub field `file`) and get back the
    /// created meeting's id + initial status.
    ///
    /// - Parameters:
    ///   - fileURL: a readable local file (the picked recording / transcript).
    ///   - filename: the name the hub sees in `Content-Disposition` — its suffix
    ///     drives format validation (audio vs `.vtt`/`.srt`/`.txt`) and the default
    ///     meeting title, so pass the real on-device name, not the temp path.
    ///   - mimeType: the part's `Content-Type` (e.g. `audio/wav`, `text/vtt`); the
    ///     hub validates by suffix, but a faithful type keeps the part well-formed.
    /// - Returns: `MeetingImportResult` with the `meeting_id` to poll and the
    ///   `importing` status.
    /// - Throws: `DesktopClientError.http(code)` on a non-2xx (the hub's rejection —
    ///   unsupported format / empty file), `.malformed` if the 2xx body is not the
    ///   `{meeting_id, status}` shape.
    public func importMeeting(fileURL: URL,
                              filename: String,
                              mimeType: String) async throws -> MeetingImportResult {
        let fileData = try Data(contentsOf: fileURL)
        let boundary = "Boundary-\(UUID().uuidString)"
        let body = Self.multipartBody(fieldName: "file",
                                      filename: filename,
                                      mimeType: mimeType,
                                      fileData: fileData,
                                      boundary: boundary)

        let request = importRequest(path: "api/meetings/import", boundary: boundary, body: body)
        let data = try await importSend(request)
        do { return try HoldSpeakContracts.decoder().decode(MeetingImportResult.self, from: data) }
        catch { throw DesktopClientError.malformed }
    }

    // MARK: - internals (file-private to this slice; no shared-helper dependency)

    /// Build a single-file `multipart/form-data` body for `fieldName`. Each line is
    /// CRLF-terminated per RFC 7578; the closing boundary carries the trailing `--`.
    static func multipartBody(fieldName: String,
                              filename: String,
                              mimeType: String,
                              fileData: Data,
                              boundary: String) -> Data {
        var body = Data()
        let crlf = "\r\n"
        body.append("--\(boundary)\(crlf)".data(using: .utf8)!)
        body.append(("Content-Disposition: form-data; name=\"\(fieldName)\"; " +
                     "filename=\"\(filename)\"\(crlf)").data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\(crlf)\(crlf)".data(using: .utf8)!)
        body.append(fileData)
        body.append("\(crlf)--\(boundary)--\(crlf)".data(using: .utf8)!)
        return body
    }

    /// A POST against the configured peer carrying the multipart body, mirroring the
    /// base client's Bearer-auth + timeout. Built inline so the slice carries no
    /// dependency on the base type's private `makeRequest`.
    private func importRequest(path: String, boundary: String, body: Data) -> URLRequest {
        let absolute = config.baseURL.absoluteString
        let base = absolute.hasSuffix("/") ? String(absolute.dropLast()) : absolute
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = "POST"
        request.timeoutInterval = config.timeout
        request.setValue("multipart/form-data; boundary=\(boundary)",
                         forHTTPHeaderField: "Content-Type")
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = body
        return request
    }

    /// Run the upload, throwing `DesktopClientError.http` on a non-2xx (so the
    /// view-model can render the hub's rejection). Mirrors the base client's `send`.
    private func importSend(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }
}
