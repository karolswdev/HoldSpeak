import Foundation

/// The result of `POST /api/meetings/import` (HS-19-03, mobile).
///
/// The hub creates the meeting row **immediately** in a visible `importing`
/// state and runs Whisper/parse on a background thread, so the upload returns
/// `202 Accepted` with just the freshly-minted id and that initial status:
///
/// ```json
/// {"meeting_id": "a1b2c3d4", "status": "importing"}
/// ```
///
/// The id is the handle the iPad polls (`/history`, `/api/meetings/{id}`) to
/// watch the import move `importing` → `queued`/`disabled` (success) or
/// `import_failed` (the actionable failure stays, honestly labeled). The created
/// meeting carries no timestamps in this response; any timestamp that later
/// rides on the meeting summary is a raw `String?` (the hub emits naive
/// `datetime.now().isoformat()` with no `Z`, which the `.iso8601` decoder
/// rejects — never decode it as a `Date`).
public struct MeetingImportResult: Sendable, Equatable, Decodable {
    /// The id of the meeting row the hub created for this upload — the handle the
    /// client polls to follow the import to completion.
    public var meetingID: String
    /// The lifecycle state at acceptance — `"importing"` on the happy path. Carried
    /// verbatim so a future state never breaks the decode.
    public var status: String

    public init(meetingID: String, status: String) {
        self.meetingID = meetingID
        self.status = status
    }

    /// The hub sends `meeting_id` (snake_case) and `status`. The shared decoder runs
    /// `.convertFromSnakeCase`, which rewrites the wire key `meeting_id` to
    /// `meetingId` BEFORE matching — so the CodingKey is the camelCase `meetingId`,
    /// not the literal `meeting_id` (matching the wire key directly would never
    /// hit). A missing `status` decodes to the honest `importing` default rather
    /// than throwing.
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        self.meetingID = try c.decode(String.self, forKey: .meetingID)
        self.status = try c.decodeIfPresent(String.self, forKey: .status) ?? "importing"
    }

    enum CodingKeys: String, CodingKey {
        case meetingID = "meetingId"
        case status
    }
}

/// The error body the hub returns on a rejected upload (a non-2xx) — an
/// unsupported format, an empty file, or the honest missing-ffmpeg message:
///
/// ```json
/// {"error": "Unsupported format: .pages"}
/// ```
///
/// Decoded only on the failure path so the client can surface the hub's own
/// actionable message instead of a bare status code.
public struct MeetingImportErrorBody: Sendable, Equatable, Decodable {
    public var error: String
    public init(error: String) { self.error = error }
}
