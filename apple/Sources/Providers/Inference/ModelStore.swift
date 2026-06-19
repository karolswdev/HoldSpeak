import Foundation

/// HSM-5-03 — the on-device model manager (Foundation only). Owns the directory
/// where GGUF weights live and the two ways models get there:
///   1. **Sideload** — `importModel(from:)` copies a `.gguf` the user picked in the
///      Files app (security-scoped URL handled by the host UI) into app storage.
///   2. **Download** — the HF downloader (`InferenceLlama`, which has the engine
///      dep) writes into this same directory.
/// It also resolves which installed model a device should use, per the per-device
/// policy. No engine dependency lives here, so the domain can reason about models
/// without linking llama.cpp.
public struct ModelStore: Sendable {
    public let root: URL

    public init(root: URL) { self.root = root }

    /// The default location: Application Support / HoldSpeak / models (created).
    public static func defaultRoot() throws -> URL {
        let base = try FileManager.default.url(
            for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        let dir = base.appendingPathComponent("HoldSpeak/models", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    public func ensureRoot() throws {
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }

    /// Installed GGUF files, name-sorted (stable for the UI + tests).
    public func installedModels() throws -> [URL] {
        try ensureRoot()
        return try FileManager.default
            .contentsOfDirectory(at: root, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension.lowercased() == "gguf" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    /// Copy a sideloaded `.gguf` into the store (the host UI starts/stops the
    /// security scope around this call for picker URLs). Replaces any same-named file.
    @discardableResult
    public func importModel(from source: URL) throws -> URL {
        try ensureRoot()
        let dest = root.appendingPathComponent(source.lastPathComponent)
        if FileManager.default.fileExists(atPath: dest.path) {
            try FileManager.default.removeItem(at: dest)
        }
        try FileManager.default.copyItem(at: source, to: dest)
        return dest
    }

    public func delete(_ url: URL) throws {
        try FileManager.default.removeItem(at: url)
    }

    /// The installed path for a catalogued artifact, or nil if not present.
    public func path(for artifact: ModelArtifact) -> URL? {
        let candidate = root.appendingPathComponent(artifact.fileName)
        return FileManager.default.fileExists(atPath: candidate.path) ? candidate : nil
    }

    public func isInstalled(_ artifact: ModelArtifact) -> Bool { path(for: artifact) != nil }

    /// The model this device should load per the per-device default (4B iPhone /
    /// 8B iPad), if it's installed. nil ⇒ nothing to load yet (offer download/sideload).
    public func resolveActive(for device: DeviceClass) -> URL? {
        path(for: ModelCatalog.defaultArtifact(for: device))
    }
}
