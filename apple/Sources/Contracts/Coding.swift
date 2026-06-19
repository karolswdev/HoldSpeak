import Foundation

/// The one place the contract's wire rules become a configured coder.
///
/// - Keys: snake_case on the wire ⇄ camelCase Swift (contract §1).
/// - Instants: ISO-8601 UTC `Z` (contract §2). Intra-meeting offsets stay numeric.
///
/// Caveat (v0): `.convertFromSnakeCase` also runs over free-form blob dictionary
/// keys (`structuredJson`/`payload`/`metadata`). The shipped blobs carry no
/// snake_case keys, so this is a no-op today; hardening to explicit `CodingKeys`
/// for blob isolation is a follow-up.
public enum HoldSpeakContracts {
    /// Independent of any DB `SCHEMA_VERSION` (contract §9).
    public static let contractVersion = "0.1.0"

    public static func decoder() -> JSONDecoder {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        d.dateDecodingStrategy = .iso8601
        return d
    }

    public static func encoder() -> JSONEncoder {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        e.dateEncodingStrategy = .iso8601   // emits UTC `Z`
        return e
    }
}
