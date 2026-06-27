import Foundation

/// The faceted-archive filter values (`GET /api/meetings/facets`, HS-55-04).
///
/// The hub returns the distinct *values* that can filter the history archive —
/// every speaker that has spoken and every tag that has been applied — drawn in
/// SQL across the whole archive (`db.meetings.list_facet_values()`). The wire
/// shape is two plain string arrays:
///
/// ```json
/// {"speakers": ["Alex", "Dana"], "tags": ["q3", "standup"]}
/// ```
///
/// These are the chips the archive filter row offers; feeding a chosen value back
/// as `speaker=`/`tag=` on `GET /api/meetings` narrows the list server-side.
public struct MeetingFacets: Sendable, Equatable, Decodable {
    /// Distinct speaker names across the archive, ordered case-insensitively by the
    /// hub. Empty when no segments carry a speaker yet (honest at N=0).
    public var speakers: [String]
    /// Distinct meeting tags across the archive, ordered case-insensitively.
    public var tags: [String]

    public init(speakers: [String] = [], tags: [String] = []) {
        self.speakers = speakers
        self.tags = tags
    }

    /// Both arrays default to empty so a partial/evolving payload still decodes —
    /// the client's robust-decode posture (a future field never breaks the existing
    /// two, and an archive with no tags is a normal empty chip row, not an error).
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        self.speakers = try c.decodeIfPresent([String].self, forKey: .speakers) ?? []
        self.tags = try c.decodeIfPresent([String].self, forKey: .tags) ?? []
    }

    /// Both keys already arrive as lower-case single words, so no snake_case mapping
    /// is needed; the explicit map isolates this type from the shared decoder's
    /// `.convertFromSnakeCase` strategy.
    enum CodingKeys: String, CodingKey {
        case speakers
        case tags
    }
}
