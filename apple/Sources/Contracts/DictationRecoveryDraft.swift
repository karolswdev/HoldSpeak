import Foundation

/// Device-local recovery state for one paired dictation delivery.
///
/// The phrase belongs here (the owner's local draft), never in first-value
/// measurement. ``deliveryID`` is minted before the request and survives a
/// timeout/relaunch so the hub can return the prior Receipt without typing the
/// same words twice.
public struct DictationRecoveryDraft: Codable, Sendable, Equatable {
    public static let version = 1

    public var schemaVersion: Int
    public var text: String
    public var deliveryID: String
    public var raw: Bool
    public var destination: String
    public var updatedAt: Date

    public init(
        text: String,
        deliveryID: String,
        raw: Bool = false,
        destination: String,
        updatedAt: Date = Date()
    ) {
        self.schemaVersion = Self.version
        self.text = text
        self.deliveryID = deliveryID
        self.raw = raw
        self.destination = destination
        self.updatedAt = updatedAt
    }
}

/// A narrow UserDefaults adapter. Saving an empty draft clears it; no timer or
/// lifecycle callback is required, so an app-background event cannot race a
/// deferred write.
public struct DictationRecoveryStore {
    public static let defaultKey = "hs.dictate.recovery.v1"

    private let defaults: UserDefaults
    private let key: String

    public init(
        defaults: UserDefaults = .standard,
        key: String = DictationRecoveryStore.defaultKey
    ) {
        self.defaults = defaults
        self.key = key
    }

    public func load() -> DictationRecoveryDraft? {
        guard let data = defaults.data(forKey: key),
              let draft = try? JSONDecoder().decode(DictationRecoveryDraft.self, from: data),
              draft.schemaVersion == DictationRecoveryDraft.version,
              !draft.text.isEmpty,
              !draft.deliveryID.isEmpty else { return nil }
        return draft
    }

    public func save(_ draft: DictationRecoveryDraft) {
        guard !draft.text.isEmpty, !draft.deliveryID.isEmpty,
              let data = try? JSONEncoder().encode(draft) else {
            clear()
            return
        }
        defaults.set(data, forKey: key)
    }

    public func clear() {
        defaults.removeObject(forKey: key)
    }
}
