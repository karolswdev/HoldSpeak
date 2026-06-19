import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// HSM-5-03 — the Hugging Face download path (the "just works" default).
///
/// Pure Foundation: it builds the **canonical HF resolve URL** from the pinned
/// repo + filename and streams it to the `ModelStore`, reporting 0…1 progress. No
/// HTML scraping (that's fragile against HF page changes) and no engine dependency,
/// so the download path stays engine-agnostic — Mode A weights and any future
/// engine's weights come down the same way.
public struct ModelDownloader: Sendable {
    public init() {}

    public enum DownloadError: Error, Equatable { case http(status: Int) }

    /// `https://huggingface.co/{repo}/resolve/{revision}/{fileName}?download=true`
    public func huggingFaceURL(for artifact: ModelArtifact, revision: String = "main") -> URL {
        URL(string: "https://huggingface.co/\(artifact.huggingFaceRepo)/resolve/\(revision)/\(artifact.fileName)?download=true")!
    }

    /// Download a catalogued artifact into the store under its `fileName`. If the
    /// file is already present, it's a no-op (progress → 1). `progress` is 0…1.
    @discardableResult
    public func download(
        _ artifact: ModelArtifact,
        into store: ModelStore,
        progress: @Sendable @escaping (Double) -> Void = { _ in }
    ) async throws -> URL {
        try store.ensureRoot()
        let dest = store.root.appendingPathComponent(artifact.fileName)
        if FileManager.default.fileExists(atPath: dest.path) { progress(1); return dest }
        try await downloadFile(from: huggingFaceURL(for: artifact), to: dest, progress: progress)
        return dest
    }

    func downloadFile(from url: URL, to dest: URL,
                      progress: @Sendable @escaping (Double) -> Void) async throws {
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            let delegate = DownloadDelegate(destination: dest, onProgress: progress, continuation: cont)
            let session = URLSession(configuration: .default, delegate: delegate, delegateQueue: nil)
            delegate.session = session
            session.downloadTask(with: url).resume()
        }
    }
}

/// URLSession download delegate: efficient streamed download (no per-byte loop),
/// real progress, atomic move into place. `@unchecked Sendable` — the mutable
/// continuation is only touched on the session's serial delegate queue.
private final class DownloadDelegate: NSObject, URLSessionDownloadDelegate, @unchecked Sendable {
    let destination: URL
    let onProgress: @Sendable (Double) -> Void
    var continuation: CheckedContinuation<Void, Error>?
    var session: URLSession?

    init(destination: URL, onProgress: @escaping @Sendable (Double) -> Void,
         continuation: CheckedContinuation<Void, Error>) {
        self.destination = destination
        self.onProgress = onProgress
        self.continuation = continuation
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didWriteData bytesWritten: Int64, totalBytesWritten: Int64,
                    totalBytesExpectedToWrite: Int64) {
        if totalBytesExpectedToWrite > 0 {
            onProgress(Double(totalBytesWritten) / Double(totalBytesExpectedToWrite))
        }
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didFinishDownloadingTo location: URL) {
        defer { session.finishTasksAndInvalidate() }
        if let http = downloadTask.response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            finish(.failure(ModelDownloader.DownloadError.http(status: http.statusCode)))
            return
        }
        do {
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.moveItem(at: location, to: destination)
            onProgress(1)
            finish(.success(()))
        } catch { finish(.failure(error)) }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error { session.finishTasksAndInvalidate(); finish(.failure(error)) }
    }

    private func finish(_ result: Result<Void, Error>) {
        guard let cont = continuation else { return }
        continuation = nil
        cont.resume(with: result)
    }
}
