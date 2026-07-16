import SwiftUI
import Foundation
#if canImport(UIKit)
import UIKit
#endif

/// "iPhone" / "iPad" (or "device") — so chrome says the right thing on each device instead of
/// hardcoding "iPad". Use `this \(DeviceLabel.current)` for "this device" phrasings.
enum DeviceLabel {
    static var current: String {
        #if canImport(UIKit)
        switch UIDevice.current.userInterfaceIdiom {
        case .phone: return "iPhone"
        case .pad:   return "iPad"
        default:     return "device"
        }
        #else
        return "device"
        #endif
    }
}

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
    // Qwen3.5 + Gemma 4 need the upgraded engine (scripts/upgrade-llama-xcframework.sh,
    // shipped from build 2) — the 2025-12 llama.cpp lacks their archs and cannot load them.
    static let all: [SuggestedModel] = [
        SuggestedModel(name: "Llama 3.2 3B Instruct",
                       detail: "~2.0 GB · fast, great on iPhone",
                       repo: "bartowski/Llama-3.2-3B-Instruct-GGUF",
                       fileName: "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        SuggestedModel(name: "Qwen3 4B Instruct 2507",
                       detail: "~2.5 GB · proven on-device",
                       repo: "unsloth/Qwen3-4B-Instruct-2507-GGUF",
                       fileName: "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"),
        SuggestedModel(name: "Qwen3.5 4B",
                       detail: "~2.9 GB · recommended · 256K context",
                       repo: "unsloth/Qwen3.5-4B-GGUF",
                       fileName: "Qwen3.5-4B-Q5_K_M.gguf"),
        SuggestedModel(name: "Gemma 3n E4B",
                       detail: "~4.2 GB · Google, built for on-device",
                       repo: "unsloth/gemma-3n-E4B-it-GGUF",
                       fileName: "gemma-3n-E4B-it-Q4_K_M.gguf"),
        SuggestedModel(name: "Gemma 4 E4B",
                       detail: "~4.3 GB · Google's newest mobile-first",
                       repo: "unsloth/gemma-4-E4B-it-GGUF",
                       fileName: "gemma-4-E4B-it-Q4_K_M.gguf"),
        SuggestedModel(name: "Llama 3.1 8B Instruct",
                       detail: "~4.9 GB · best on iPad",
                       repo: "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
                       fileName: "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"),
    ]
}

// MARK: - Download manager

/// One download at a time, on a BACKGROUND URLSession so a multi-GB pull survives the screen
/// locking / the app being suspended or even terminated (iOS keeps transferring and relaunches
/// the app to finish — see `HoldSpeakAppDelegate`). Live 0…1 progress + Cancel; writes into
/// `ModelFiles.root` (Documents) under the file's own name so `localGGUF()` finds it immediately.
@MainActor final class ModelDownloadManager: NSObject, ObservableObject {
    static let shared = ModelDownloadManager()

    @Published var progress: [String: Double] = [:]   // fileName → 0…1 (present only while active/just-done)
    @Published var activeFile: String? = nil           // the fileName currently downloading
    @Published var errorMsg: String? = nil

    /// Set by the app delegate when iOS relaunches us to finish background transfers; called once
    /// the session reports all events delivered.
    var backgroundCompletion: (() -> Void)?

    static let sessionId = "dev.holdspeak.modeldownload"
    private let proxy = BackgroundDownloadProxy()
    private lazy var session: URLSession = {
        let cfg = URLSessionConfiguration.background(withIdentifier: Self.sessionId)
        cfg.sessionSendsLaunchEvents = true     // relaunch the app to deliver completion
        cfg.isDiscretionary = false             // start now, don't wait for "ideal" conditions
        cfg.allowsCellularAccess = true
        return URLSession(configuration: cfg, delegate: proxy, delegateQueue: nil)
    }()

    func isInstalled(_ fileName: String) -> Bool {
        FileManager.default.fileExists(atPath: ModelFiles.root.appendingPathComponent(fileName).path)
    }

    /// Touch the background session early (app launch / relaunch) so in-flight transfers reattach,
    /// then restore the UI to whatever is still downloading.
    func ensureSession() {
        session.getAllTasks { tasks in
            guard let t = tasks.compactMap({ $0 as? URLSessionDownloadTask }).first,
                  let f = t.originalRequest?.url?.lastPathComponent else { return }
            let p = t.countOfBytesExpectedToReceive > 0
                ? Double(t.countOfBytesReceived) / Double(t.countOfBytesExpectedToReceive) : 0.0001
            Task { @MainActor in self.activeFile = f; self.progress[f] = p }
        }
    }

    func start(repo: String, fileName: String) {
        guard activeFile == nil else { return }                 // serialize downloads
        if isInstalled(fileName) { return }
        guard let url = URL(string: "https://huggingface.co/\(repo)/resolve/main/\(fileName)?download=true") else {
            errorMsg = "Couldn't build that download URL."; return
        }
        errorMsg = nil; activeFile = fileName; progress[fileName] = 0.0001
        setKeepAwake(true)
        session.downloadTask(with: url).resume()
    }

    func cancel() {
        session.getAllTasks { tasks in tasks.forEach { $0.cancel() } }
        if let f = activeFile { progress[f] = nil }
        activeFile = nil; setKeepAwake(false)
    }

    // Called by the proxy (on main) as a transfer reports progress / finishes.
    func report(_ fileName: String, progress p: Double) { activeFile = fileName; progress[fileName] = p }

    func succeeded(_ fileName: String) {
        progress[fileName] = 1; activeFile = nil; setKeepAwake(false)
        if InferenceConfigStore.shared.localModelId.isEmpty {   // auto-select the first model
            InferenceConfigStore.shared.localModelId = fileName
        }
    }

    func failed(_ fileName: String, code: Int, cancelled: Bool) {
        progress[fileName] = nil; activeFile = nil; setKeepAwake(false)
        if cancelled { errorMsg = nil; return }
        switch code {
        case 401, 403: errorMsg = "That model is gated — it needs a Hugging Face token to download."
        case 404:      errorMsg = "Not found — the file may have moved or the name is wrong."
        case 0:        errorMsg = "Download failed. Check your connection and try again."
        default:       errorMsg = "Download failed (HTTP \(code))."
        }
    }

    private func setKeepAwake(_ on: Bool) {
        #if canImport(UIKit)
        UIApplication.shared.isIdleTimerDisabled = on   // don't auto-lock mid-download (foreground)
        #endif
    }
}

/// Background-session delegate (off the main actor). Derives the destination from the task's own
/// URL — so it's stateless across an app relaunch — moves the finished file into place, and forwards
/// to the manager on the main actor.
private final class BackgroundDownloadProxy: NSObject, URLSessionDownloadDelegate, @unchecked Sendable {
    func urlSession(_ s: URLSession, downloadTask: URLSessionDownloadTask,
                    didWriteData _: Int64, totalBytesWritten written: Int64,
                    totalBytesExpectedToWrite total: Int64) {
        guard total > 0, let f = downloadTask.originalRequest?.url?.lastPathComponent else { return }
        let p = Double(written) / Double(total)
        Task { @MainActor in ModelDownloadManager.shared.report(f, progress: p) }
    }

    func urlSession(_ s: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
        guard let f = downloadTask.originalRequest?.url?.lastPathComponent else { return }
        if let http = downloadTask.response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            let code = http.statusCode
            Task { @MainActor in ModelDownloadManager.shared.failed(f, code: code, cancelled: false) }
            return
        }
        // Move synchronously — the temp file is gone once this returns.
        let dest = ModelFiles.root.appendingPathComponent(f)
        do {
            try? FileManager.default.createDirectory(at: ModelFiles.root, withIntermediateDirectories: true)
            if FileManager.default.fileExists(atPath: dest.path) { try FileManager.default.removeItem(at: dest) }
            try FileManager.default.moveItem(at: location, to: dest)
            Task { @MainActor in ModelDownloadManager.shared.succeeded(f) }
        } catch {
            Task { @MainActor in ModelDownloadManager.shared.failed(f, code: 0, cancelled: false) }
        }
    }

    func urlSession(_ s: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        guard let error = error as NSError?,
              let f = task.originalRequest?.url?.lastPathComponent else { return }
        let cancelled = error.code == NSURLErrorCancelled
        Task { @MainActor in ModelDownloadManager.shared.failed(f, code: 0, cancelled: cancelled) }
    }

    // All background events for this session delivered — let the app finish (relaunch case).
    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        Task { @MainActor in
            ModelDownloadManager.shared.backgroundCompletion?()
            ModelDownloadManager.shared.backgroundCompletion = nil
        }
    }
}

/// Captures the system's background-URLSession relaunch so a download that finished while the app was
/// suspended/terminated is completed and the OS is told we're done.
final class HoldSpeakAppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     handleEventsForBackgroundURLSession identifier: String,
                     completionHandler: @escaping () -> Void) {
        guard identifier == ModelDownloadManager.sessionId else { completionHandler(); return }
        Task { @MainActor in
            ModelDownloadManager.shared.backgroundCompletion = completionHandler
            ModelDownloadManager.shared.ensureSession()
        }
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
    @State private var showReadme = false

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
                    HStack(spacing: 5) {
                        Text(installed ? "Installed · on this \(DeviceLabel.current)" : detail)
                            .font(.system(size: 12, weight: .semibold)).foregroundStyle(installed ? Sig.ok : Sig.faint).lineLimit(1)
                        Image(systemName: "info.circle").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint.opacity(0.7))
                    }
                }
            }
            Spacer(minLength: 4)
            trailing(installed: installed, active: active)
        }
        .padding(13)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(active ? Sig.accent.opacity(0.5) : Sig.line, lineWidth: 1))
        .contentShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .onTapGesture { tactile(); showReadme = true }   // open the model's README/card
        .sheet(isPresented: $showReadme) {
            NavigationStack { ModelReadmeView(repo: repo, fileName: fileName, name: name) }.preferredColorScheme(.dark)
        }
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
    @State private var size: String? = nil
    private static let sizes = ["1B", "2B", "3B", "4B", "7B", "8B", "12B", "27B", "70B"]
    private var shownRepos: [String] {
        guard let s = size?.lowercased() else { return hf.repos }
        return hf.repos.filter { $0.lowercased().contains(s) }
    }
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

            // Size filter — narrow the results to a parameter class (matches the size token in the repo id).
            if !hf.repos.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 7) {
                        sizeChip("All", value: nil)
                        ForEach(Self.sizes, id: \.self) { sizeChip($0, value: $0) }
                    }
                }
            }

            switch hf.state {
            case .empty:  Text("No GGUF repositories found.").font(.system(size: 12)).foregroundStyle(Sig.faint)
            case .failed: Text("Search on Hugging Face failed. Nothing was downloaded. Check your connection and retry.").font(.system(size: 12)).foregroundStyle(Sig.warn)
            default:
                if !hf.repos.isEmpty && shownRepos.isEmpty {
                    Text("No \(size ?? "") models in these results.").font(.system(size: 12)).foregroundStyle(Sig.faint)
                }
            }

            ForEach(shownRepos, id: \.self) { repo in
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

    @ViewBuilder private func sizeChip(_ label: String, value: String?) -> some View {
        let on = size == value
        Button { tactile(); withAnimation(.easeOut(duration: 0.15)) { size = value } } label: {
            Text(label).font(.system(size: 12.5, weight: .heavy))
                .foregroundStyle(on ? .black : Sig.muted)
                .padding(.horizontal, 12).frame(height: 30)
                .background(on ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.s2), in: Capsule())
                .overlay(Capsule().strokeBorder(Color.white.opacity(on ? 0 : 0.08), lineWidth: 1))
        }.buttonStyle(.plain)
    }
}

// MARK: - Model README (the HF model card, rendered)

/// Pulls a repo's README.md from Hugging Face and renders it as a clean card, with a Download
/// button for the specific file. Reachable by tapping any model row.
struct ModelReadmeView: View {
    let repo: String
    let fileName: String
    let name: String
    @ObservedObject private var dl = ModelDownloadManager.shared
    @Environment(\.dismiss) private var dismiss
    @State private var markdown: String? = nil
    @State private var failed = false
    @State private var loading = true

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(name).font(.system(size: 26, weight: .heavy)).foregroundStyle(Sig.text)
                        Link(destination: URL(string: "https://huggingface.co/\(repo)")!) {
                            HStack(spacing: 5) {
                                Text(repo).font(.system(size: 12.5, weight: .semibold)).foregroundStyle(Sig.accent).lineLimit(1)
                                Image(systemName: "arrow.up.right.square").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.accent)
                            }
                        }
                    }
                    downloadBar
                    Divider().overlay(Sig.line)
                    if loading {
                        HStack(spacing: 8) { ProgressView().tint(Sig.accent); Text("Loading the model card…").font(.system(size: 13)).foregroundStyle(Sig.muted) }
                    } else if failed {
                        Text("Couldn't load this model's README from Hugging Face. Nothing was downloaded. Check your connection and retry.").font(.system(size: 13)).foregroundStyle(Sig.faint)
                    } else if let md = markdown {
                        MarkdownText(raw: md)
                    }
                }
                .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .navigationTitle("Model card").navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .topBarLeading) { Button("Done") { dismiss() } } }
        .task { await load() }
    }

    @ViewBuilder private var downloadBar: some View {
        let installed = dl.isInstalled(fileName)
        let active = dl.activeFile == fileName
        let p = dl.progress[fileName]
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 2) {
                Text(fileName).font(.system(size: 12.5, weight: .semibold, design: .monospaced)).foregroundStyle(Sig.muted).lineLimit(1)
                if active, let p { Text("Downloading… \(Int(p * 100))%").font(.system(size: 11, weight: .heavy)).foregroundStyle(Sig.accent) }
            }
            Spacer(minLength: 8)
            if active {
                Button { tactile(); dl.cancel() } label: { Text("Cancel").font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.muted).padding(.horizontal, 14).frame(height: 36).background(Sig.s2, in: Capsule()) }
            } else if installed {
                HStack(spacing: 5) { Image(systemName: "checkmark.seal.fill"); Text("Installed").font(.system(size: 13, weight: .heavy)) }.foregroundStyle(Sig.ok)
            } else {
                Button { tactile(); dl.start(repo: repo, fileName: fileName) } label: {
                    Text("Get").font(.system(size: 14, weight: .heavy)).foregroundStyle(.black).padding(.horizontal, 18).frame(height: 36).background(Sig.accent, in: Capsule())
                }.disabled(dl.activeFile != nil).opacity(dl.activeFile != nil ? 0.4 : 1)
            }
        }
        .padding(12).background(Sig.s1, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(active ? Sig.accent.opacity(0.5) : Sig.line, lineWidth: 1))
        .animation(.easeOut(duration: 0.2), value: active)
    }

    private func load() async {
        guard let url = URL(string: "https://huggingface.co/\(repo)/raw/main/README.md") else { failed = true; loading = false; return }
        do {
            let (data, resp) = try await URLSession.shared.data(from: url)
            guard let http = resp as? HTTPURLResponse, (200...299).contains(http.statusCode),
                  let text = String(data: data, encoding: .utf8) else { failed = true; loading = false; return }
            markdown = MarkdownText.strip(text); loading = false
        } catch { failed = true; loading = false }
    }
}

/// A lightweight Markdown renderer good enough for HF model cards: headings, paragraphs (with inline
/// bold/code/links), bullet lists, and fenced code. Avoids a dependency; not a full CommonMark engine.
struct MarkdownText: View {
    let raw: String

    /// Strip YAML frontmatter + image/HTML badge lines that don't render as text.
    static func strip(_ s: String) -> String {
        var lines = s.components(separatedBy: "\n")
        if lines.first?.trimmingCharacters(in: .whitespaces) == "---" {
            if let end = lines.dropFirst().firstIndex(where: { $0.trimmingCharacters(in: .whitespaces) == "---" }) {
                lines = Array(lines[(end + 1)...])
            }
        }
        return lines
            .filter { l in
                let t = l.trimmingCharacters(in: .whitespaces)
                if t.hasPrefix("<") { return false }            // raw HTML / badges
                if t.hasPrefix("![") { return false }           // images
                return true
            }
            .joined(separator: "\n")
    }

    private enum Block { case h(Int, String), p(String), bullet(String), code(String) }

    private func blocks() -> [Block] {
        var out: [Block] = []; var inCode = false; var code = ""; var para = ""
        func flushPara() { let t = para.trimmingCharacters(in: .whitespacesAndNewlines); if !t.isEmpty { out.append(.p(t)) }; para = "" }
        for line in raw.components(separatedBy: "\n") {
            let t = line.trimmingCharacters(in: .whitespaces)
            if t.hasPrefix("```") {
                if inCode { out.append(.code(code)); code = ""; inCode = false } else { flushPara(); inCode = true }
                continue
            }
            if inCode { code += (code.isEmpty ? "" : "\n") + line; continue }
            if t.isEmpty { flushPara(); continue }
            if t.hasPrefix("### ") { flushPara(); out.append(.h(3, String(t.dropFirst(4)))) }
            else if t.hasPrefix("## ") { flushPara(); out.append(.h(2, String(t.dropFirst(3)))) }
            else if t.hasPrefix("# ") { flushPara(); out.append(.h(1, String(t.dropFirst(2)))) }
            else if t.hasPrefix("- ") || t.hasPrefix("* ") { flushPara(); out.append(.bullet(String(t.dropFirst(2)))) }
            else { para += (para.isEmpty ? "" : " ") + t }
        }
        if inCode { out.append(.code(code)) }
        flushPara()
        return out
    }

    private func inline(_ s: String) -> AttributedString {
        (try? AttributedString(markdown: s, options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace))) ?? AttributedString(s)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 11) {
            ForEach(Array(blocks().enumerated()), id: \.offset) { _, b in
                switch b {
                case .h(let lvl, let t):
                    Text(t).font(.system(size: lvl == 1 ? 22 : lvl == 2 ? 18 : 15.5, weight: .heavy))
                        .foregroundStyle(Sig.text).padding(.top, lvl == 1 ? 4 : 2)
                case .p(let t):
                    Text(inline(t)).font(.system(size: 14)).foregroundStyle(Sig.muted).tint(Sig.accent)
                        .fixedSize(horizontal: false, vertical: true)
                case .bullet(let t):
                    HStack(alignment: .top, spacing: 8) {
                        Text("•").font(.system(size: 14, weight: .black)).foregroundStyle(Sig.accent)
                        Text(inline(t)).font(.system(size: 14)).foregroundStyle(Sig.muted).tint(Sig.accent)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                case .code(let t):
                    Text(t).font(.system(size: 12.5, design: .monospaced)).foregroundStyle(Sig.text)
                        .frame(maxWidth: .infinity, alignment: .leading).padding(12)
                        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                }
            }
        }
    }
}
