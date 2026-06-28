import Foundation
#if canImport(Security)
import Security
#endif

// Phase 24 (HSM-24-01) — the device-local custodian for a RuntimeProfile's API key.
//
// The KEY NEVER LIVES ON `RuntimeProfile` AND NEVER SYNCS. The profile's *shape* travels the mesh
// (`SyncKind.profile`); the key is stored here in the Keychain, keyed by the profile id, and joined
// to an `EndpointConfig` only at request time. Each device holds its own key for a shared profile.
enum ProfileKeyStore {
    private static let service = "dev.holdspeak.runtimeprofile.key"

    /// Store (or replace) the API key for a profile. An empty key deletes it.
    static func set(_ key: String, for profileId: String) {
        let trimmed = key.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { delete(profileId); return }
        #if canImport(Security)
        let base: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                   kSecAttrService as String: service,
                                   kSecAttrAccount as String: profileId]
        SecItemDelete(base as CFDictionary)
        var add = base
        add[kSecValueData as String] = Data(trimmed.utf8)
        add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly  // never leaves this device
        SecItemAdd(add as CFDictionary, nil)
        #endif
    }

    /// The API key for a profile, or nil if none is stored.
    static func get(_ profileId: String) -> String? {
        #if canImport(Security)
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrService as String: service,
                                    kSecAttrAccount as String: profileId,
                                    kSecReturnData as String: true,
                                    kSecMatchLimit as String: kSecMatchLimitOne]
        var out: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &out) == errSecSuccess,
              let data = out as? Data, let s = String(data: data, encoding: .utf8) else { return nil }
        return s
        #else
        return nil
        #endif
    }

    static func delete(_ profileId: String) {
        #if canImport(Security)
        SecItemDelete([kSecClass as String: kSecClassGenericPassword,
                       kSecAttrService as String: service,
                       kSecAttrAccount as String: profileId] as CFDictionary)
        #endif
    }

    static func has(_ profileId: String) -> Bool { get(profileId) != nil }
}
