import SwiftUI
import Foundation
import UniformTypeIdentifiers

// HSM-14-19 "The Desk" decomposition: the on-device model manager (import / list / delete .gguf via
// Files/AirDrop) lifted verbatim out of MeetingCaptureApp.swift. Same module; Sig/tactile resolve internally.

// MARK: - Models (import & manage — front and center, owner-requested)

/// An on-device model file in the app's container.
struct InstalledModel: Identifiable {
    let url: URL
    var sizeBytes: Int
    var id: String { url.lastPathComponent }
    var name: String { url.deletingPathExtension().lastPathComponent }
    enum Kind { case language, visionProjector
        var label: String { self == .visionProjector ? "Vision projector" : "Language / vision model" }
        var glyph: String { self == .visionProjector ? "eye.fill" : "brain.head.profile" }
        var tint: Color { self == .visionProjector ? Sig.local : Sig.accent }
    }
    var kind: Kind { url.lastPathComponent.lowercased().contains("mmproj") ? .visionProjector : .language }
}

/// The app-side model-files helper: imports/lists/deletes `.gguf` in the app's **Documents**
/// (where the on-device runtime's `localGGUF()` loads from + where pushes land). Delegates to
/// the tested Providers `ModelStore` (HSM-5-03), wrapping the security scope for picker URLs.
enum ModelFiles {
    static var root: URL { FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0] }
    static var store: ModelStore { ModelStore(root: root) }

    static func installed() -> [InstalledModel] {
        ((try? store.installedModels()) ?? [])
            .map { InstalledModel(url: $0, sizeBytes: (try? $0.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0) }
    }

    /// Copy an imported/AirDropped file into the container (the host owns the security scope).
    @discardableResult
    static func importModel(from src: URL) throws -> URL {
        let scoped = src.startAccessingSecurityScopedResource()
        defer { if scoped { src.stopAccessingSecurityScopedResource() } }
        return try store.importModel(from: src)
    }

    static func delete(_ m: InstalledModel) { try? store.delete(m.url) }

    static func size(_ bytes: Int) -> String {
        let f = ByteCountFormatter(); f.allowedUnits = [.useGB, .useMB]; f.countStyle = .file
        return f.string(fromByteCount: Int64(bytes))
    }
    static var ggufTypes: [UTType] { [UTType(filenameExtension: "gguf") ?? .data] }
}

struct ModelsView: View {
    @State private var models: [InstalledModel] = []
    @State private var importing = false
    @State private var note = ""
    @State private var busy = false
    @ObservedObject private var dl = ModelDownloadManager.shared
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Button { dismiss() } label: {
                        HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Home") }
                            .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                            .padding(.vertical, 8).padding(.trailing, 12)
                    }
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Models").font(.system(size: 32, weight: .heavy)).foregroundStyle(Sig.text)
                        Text("Download one, or import a .gguf.")
                            .font(.system(size: 14)).foregroundStyle(Sig.faint)
                    }
                    SuggestedModelsSection()
                    if let err = dl.errorMsg {
                        Text(err).font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.warn)
                    }
                    HFSearchSection()
                    Text("OR IMPORT YOUR OWN").font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint).padding(.top, 4)
                    Button { importing = true } label: { importCta }.disabled(busy)
                    if !note.isEmpty {
                        HStack(spacing: 7) {
                            if busy { ProgressView().tint(Sig.accent) }
                            Text(note).font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.muted)
                        }
                    }
                    if !models.isEmpty {
                        Text("ON THIS \(DeviceLabel.current.uppercased())").font(.system(size: 11, weight: .heavy)).tracking(1.2).foregroundStyle(Sig.faint).padding(.top, 4)
                        ForEach(models) { modelCard($0) }
                    }
                }
                .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .fileImporter(isPresented: $importing, allowedContentTypes: ModelFiles.ggufTypes, allowsMultipleSelection: true) { result in
            guard case .success(let urls) = result, !urls.isEmpty else { return }
            busy = true; note = "Importing \(urls.count) file\(urls.count == 1 ? "" : "s")…"; tactile()
            Task.detached {
                var ok = 0
                for u in urls { if (try? ModelFiles.importModel(from: u)) != nil { ok += 1 } }
                await MainActor.run {
                    busy = false; note = "Imported \(ok) model\(ok == 1 ? "" : "s")."; refresh()
                }
            }
        }
        .onAppear(perform: refresh)
        .onChange(of: dl.activeFile) { _, now in if now == nil { refresh() } }   // a download just finished → relist
    }

    private func refresh() { withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) { models = ModelFiles.installed() } }

    private var importCta: some View {
        HStack(spacing: 12) {
            Image(systemName: "square.and.arrow.down.fill").font(.system(size: 20, weight: .bold)).foregroundStyle(Sig.accent)
            VStack(alignment: .leading, spacing: 2) {
                Text("Import a model").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
                Text("Pick a .gguf from Files").font(.system(size: 12)).foregroundStyle(Sig.faint)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
        }
        .padding(16)
        .frame(maxWidth: .infinity)
        .background(Sig.accent.opacity(0.12), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [7, 5])).foregroundStyle(Sig.accent.opacity(0.5)))
    }

    private func modelCard(_ m: InstalledModel) -> some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill(m.kind.tint.opacity(0.16))
                Image(systemName: m.kind.glyph).font(.system(size: 18, weight: .bold)).foregroundStyle(m.kind.tint)
            }.frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text(m.name).font(.system(size: 15.5, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 6) {
                    Text(m.kind.label).font(.system(size: 12, weight: .heavy)).foregroundStyle(m.kind.tint)
                    Text("·").foregroundStyle(Sig.faint)
                    Text(ModelFiles.size(m.sizeBytes)).font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.faint)
                }
            }
            Spacer(minLength: 4)
            Button { tactile(); ModelFiles.delete(m); refresh() } label: {
                Image(systemName: "trash").font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.faint)
                    .frame(width: 38, height: 38).background(Sig.s3, in: Circle())
            }
        }
        .padding(13)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Sig.line, lineWidth: 1))
    }
}
