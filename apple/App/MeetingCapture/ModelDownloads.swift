import SwiftUI
import Foundation

// In-app model downloads: a curated suggested list + a Hugging Face search, both pulling
// GGUF weights straight into the app's Documents (where the on-device runtime loads from).
// Reuses the canonical HF resolve URL the engine's ModelDownloader uses; adds a cancellable
// URLSession so a multi-GB download has a progress bar + a Cancel.

// MARK: - Curated suggestions

/// One hand-picked model the app knows runs on this device's bundled llama.cpp.
struct SuggestedModel: Identifiable {
    var id: String { fileName }            // the on-disk name is the stable id
    let name: String
    let detail: String                     // approx size + device fit
    let repo: String                       // Hugging Face "owner/name"
    let fileName: String                   // exact .gguf in the repo
}

enum SuggestedModels {
    // Ordered small → large. Each fileName was verified against the repo's file list.
    static let all: [SuggestedModel] = [
        SuggestedModel(name: "Llama 3.2 3B Instruct",
                       detail: "~2.0 GB · fast, great on iPhone",
                       repo: "bartowski/Llama-3.2-3B-Instruct-GGUF",
                       fileName: "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        SuggestedModel(name: "Qwen3 4B Instruct 2507",
                       detail: "~2.5 GB · recommended",
                       repo: "unsloth/Qwen3-4B-Instruct-2507-GGUF",
                       fileName: "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"),
        SuggestedModel(name: "Gemma 3n E4B",
                       detail: "~4.2 GB · Google, built for on-device",
                       repo: "unsloth/gemma-3n-E4B-it-GGUF",
                       fileName: "gemma-3n-E4B-it-Q4_K_M.gguf"),
        SuggestedModel(name: "Llama 3.1 8B Instruct",
                       detail: "~4.9 GB · best on iPad",
                       repo: "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
                       fileName: "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"),
    ]
}

// MARK: - Download manager

/// One download at a time, with live 0…1 progress and a Cancel. Writes into `ModelFiles.root`
/// (Documents) under the file's own name, so `localGGUF()` finds it immediately.
@MainActor final class ModelDownloadManager: ObservableObject {
    static let shared = ModelDownloadManager()

    @Published var progress: [String: Double] = [:]   // fileName → 0…1 (present only while active/just-done)
    @Published var activeFile: String? = nil           // the fileName currently downloading
    @Published var errorMsg: String? = nil

    private var session: URLSession?

    func isInstalled(_ fileName: String) -> Bool {
        FileManager.default.fileExists(atPath: ModelFiles.root.appendingPathComponent(fileName).path)
    }

    func start(repo: String, fileName: String) {
        guard activeFile == nil else { return }                 // serialize downloads
        if isInstalled(fileName) { return }
        guard let url = URL(string: "https://huggingface.co/\(repo)/resolve/main/\(fileName)?download=true") else {
            errorMsg = "Couldn't build that download URL."; return
        }
        let dest = ModelFiles.root.appendingPathComponent(fileName)
        errorMsg = nil; activeFile = fileName; progress[fileName] = 0.0001
        let delegate = DownloadProxy(
            destination: dest,
            onProgress: { [weak self] p in Task { @MainActor in self?.progress[fileName] = p } },
            onDone: { [weak self] result in Task { @MainActor in self?.finish(fileName, result) } })
        let s = URLSession(configuration: .default, delegate: delegate, delegateQueue: nil)
        delegate.session = s
        session = s
        s.downloadTask(with: url).resume()
    }

    func cancel() {
        session?.invalidateAndCancel(); session = nil
        if let f = activeFile { progress[f] = nil }
        activeFile = nil
    }

    private func finish(_ fileName: String, _ result: Result<Void, Error>) {
        session = nil; activeFile = nil
        switch result {
        case .success:
            progress[fileName] = 1
            // Make a freshly-downloaded model the active one if nothing was chosen yet.
            if InferenceConfigStore.shared.localModelId.isEmpty {
                InferenceConfigStore.shared.localModelId = fileName
            }
        case .failure(let e):
            progress[fileName] = nil
            let ns = e as NSError
            if ns.code == NSURLErrorCancelled { errorMsg = nil }      // user-cancelled: quiet
            else { errorMsg = friendly(ns) }
        }
    }

    private func friendly(_ e: NSError) -> String {
        if let status = (e.userInfo["status"] as? Int) {
            switch status {
            case 401, 403: return "That model is gated — it needs a Hugging Face token to download."
            case 404:      return "Not found — the file may have moved or the name is wrong."
            default:       return "Download failed (HTTP \(status))."
            }
        }
        return "Download failed. Check your connection and try again."
    }
}

/// URLSession delegate that streams to a temp file and atomically moves it into place.
/// Separate object (not the @MainActor manager) so the delegate callbacks stay off the main actor;
/// it forwards to the manager via main-actor closures.
private final class DownloadProxy: NSObject, URLSessionDownloadDelegate, @unchecked Sendable {
    let destination: URL
    let onProgress: @Sendable (Double) -> Void
    let onDone: @Sendable (Result<Void, Error>) -> Void
    var session: URLSession?

    init(destination: URL,
         onProgress: @escaping @Sendable (Double) -> Void,
         onDone: @escaping @Sendable (Result<Void, Error>) -> Void) {
        self.destination = destination; self.onProgress = onProgress; self.onDone = onDone
    }

    func urlSession(_ s: URLSession, downloadTask: URLSessionDownloadTask,
                    didWriteData _: Int64, totalBytesWritten written: Int64,
                    totalBytesExpectedToWrite total: Int64) {
        if total > 0 { onProgress(Double(written) / Double(total)) }
    }

    func urlSession(_ s: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
        defer { s.finishTasksAndInvalidate() }
        if let http = downloadTask.response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            onDone(.failure(NSError(domain: "hf", code: http.statusCode, userInfo: ["status": http.statusCode])))
            return
        }
        do {
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.moveItem(at: location, to: destination)
            onProgress(1); onDone(.success(()))
        } catch { onDone(.failure(error as NSError)) }
    }

    func urlSession(_ s: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error { s.finishTasksAndInvalidate(); onDone(.failure(error as NSError)) }
    }
}

// MARK: - Hugging Face search

/// Searches the public HF model index for GGUF repos, then lists a repo's .gguf files to pick from.
@MainActor final class HFSearch: ObservableObject {
    @Published var query = ""
    @Published var repos: [String] = []
    @Published var files: [String] = []        // .gguf files of the expanded repo
    @Published var expanded: String? = nil      // the repo whose files are shown
    @Published var state: State = .idle
    enum State: Equatable { case idle, searching, loadingFiles, empty, failed }

    private struct Hit: Decodable { let id: String }
    private struct Repo: Decodable { let siblings: [Sib]?; struct Sib: Decodable { let rfilename: String } }

    func search() async {
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard q.count >= 2 else { return }
        state = .searching; repos = []; files = []; expanded = nil
        let enc = q.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? q
        guard let url = URL(string: "https://huggingface.co/api/models?search=\(enc)&filter=gguf&limit=25&sort=downloads&direction=-1") else { state = .failed; return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let hits = try JSONDecoder().decode([Hit].self, from: data)
            repos = hits.map(\.id)
            state = repos.isEmpty ? .empty : .idle
        } catch { state = .failed }
    }

    func loadFiles(_ repo: String) async {
        if expanded == repo { expanded = nil; files = []; return }   // collapse
        expanded = repo; files = []; state = .loadingFiles
        guard let url = URL(string: "https://huggingface.co/api/models/\(repo)") else { state = .failed; return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let r = try JSONDecoder().decode(Repo.self, from: data)
            files = (r.siblings ?? []).map(\.rfilename)
                .filter { $0.lowercased().hasSuffix(".gguf") }
                .sorted()
            state = .idle
        } catch { state = .failed }
    }
}

// MARK: - UI sections (rendered inside ModelsView)

/// The curated "Suggested" section: one row per model with Download → progress → Installed.
struct SuggestedModelsSection: View {
    @ObservedObject var dl = ModelDownloadManager.shared
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("SUGGESTED").font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint)
            ForEach(SuggestedModels.all) { m in
                ModelDownloadRow(name: m.name, detail: m.detail, repo: m.repo, fileName: m.fileName)
            }
        }
    }
}

/// A download row used by both the suggested list and the search file list.
struct ModelDownloadRow: View {
    let name: String
    let detail: String
    let repo: String
    let fileName: String
    @ObservedObject private var dl = ModelDownloadManager.shared

    var body: some View {
        let installed = dl.isInstalled(fileName)
        let prog = dl.progress[fileName]
        let active = dl.activeFile == fileName
        return HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill(Sig.accent.opacity(0.16))
                Image(systemName: installed ? "checkmark" : "arrow.down.circle.fill")
                    .font(.system(size: 18, weight: .bold)).foregroundStyle(installed ? Sig.ok : Sig.accent)
            }.frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text(name).font(.system(size: 15.5, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                if active, let p = prog {
                    ProgressView(value: p).tint(Sig.accent)
                    Text("Downloading… \(Int(p * 100))%").font(.system(size: 11.5, weight: .semibold)).foregroundStyle(Sig.muted)
                } else {
                    Text(installed ? "Installed · on this iPad" : detail)
                        .font(.system(size: 12, weight: .semibold)).foregroundStyle(installed ? Sig.ok : Sig.faint).lineLimit(1)
                }
            }
            Spacer(minLength: 4)
            trailing(installed: installed, active: active)
        }
        .padding(13)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(active ? Sig.accent.opacity(0.5) : Sig.line, lineWidth: 1))
    }

    @ViewBuilder private func trailing(installed: Bool, active: Bool) -> some View {
        if active {
            Button { tactile(); dl.cancel() } label: {
                Image(systemName: "xmark").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.faint)
                    .frame(width: 38, height: 38).background(Sig.s3, in: Circle())
            }
        } else if installed {
            Image(systemName: "checkmark.seal.fill").font(.system(size: 18, weight: .bold)).foregroundStyle(Sig.ok).frame(width: 38, height: 38)
        } else {
            Button { tactile(); dl.start(repo: repo, fileName: fileName) } label: {
                Text("Get").font(.system(size: 14, weight: .heavy)).foregroundStyle(.black)
                    .padding(.horizontal, 16).frame(height: 36)
                    .background(Sig.accent, in: Capsule())
            }.disabled(dl.activeFile != nil)   // one at a time
            .opacity(dl.activeFile != nil ? 0.4 : 1)
        }
    }
}

/// The "Search Hugging Face" section: query → repos → tap a repo → pick a .gguf to download.
struct HFSearchSection: View {
    @StateObject private var hf = HFSearch()
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("SEARCH HUGGING FACE").font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint)
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.faint)
                TextField("e.g. gemma 4, qwen, phi…", text: $hf.query)
                    .font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                    .submitLabel(.search).onSubmit { Task { await hf.search() } }
                if hf.state == .searching || hf.state == .loadingFiles { ProgressView().controlSize(.small).tint(Sig.accent) }
            }
            .padding(.horizontal, 13).padding(.vertical, 12)
            .background(Sig.s2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))

            switch hf.state {
            case .empty:  Text("No GGUF repositories found.").font(.system(size: 12)).foregroundStyle(Sig.faint)
            case .failed: Text("Search failed. Check your connection.").font(.system(size: 12)).foregroundStyle(Sig.warn)
            default: EmptyView()
            }

            ForEach(hf.repos, id: \.self) { repo in
                VStack(alignment: .leading, spacing: 8) {
                    Button { tactile(); Task { await hf.loadFiles(repo) } } label: {
                        HStack(spacing: 8) {
                            Image(systemName: hf.expanded == repo ? "chevron.down" : "chevron.right")
                                .font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint)
                            Text(repo).font(.system(size: 13.5, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                            Spacer(minLength: 0)
                        }
                    }.buttonStyle(.plain)
                    if hf.expanded == repo {
                        if hf.files.isEmpty && hf.state != .loadingFiles {
                            Text("No .gguf files in this repo.").font(.system(size: 11.5)).foregroundStyle(Sig.faint).padding(.leading, 19)
                        }
                        ForEach(hf.files, id: \.self) { file in
                            ModelDownloadRow(name: file, detail: "from \(repo)", repo: repo, fileName: file)
                        }
                        if !hf.files.isEmpty {
                            Text("New architectures may not load on this build.")
                                .font(.system(size: 10.5, weight: .medium)).foregroundStyle(Sig.faint).padding(.leading, 2)
                        }
                    }
                }
                .padding(12)
                .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).stroke(Sig.line, lineWidth: 1))
            }
        }
    }
}
