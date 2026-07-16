import SwiftUI

// Phase 24 (HSM-24-03) — advanced: manage runtime profiles. Add an on-device profile or any
// OpenAI-compatible endpoint (OpenRouter, Claude, a LAN box) with its own key. The key is written to
// the Keychain (ProfileKeyStore), never onto the profile shape. Reached from Settings.
struct ProfilesView: View {
    @ObservedObject private var cfg = InferenceConfigStore.shared
    @Environment(\.dismiss) private var dismiss
    @State private var editing: RuntimeProfile? = nil
    @State private var showEditor = false

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Button { dismiss() } label: {
                        HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Settings") }
                            .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted).padding(.vertical, 8)
                    }
                    VStack(alignment: .leading, spacing: 6) {
                        Text(ProductLanguage.label(.runsOn)).font(.system(size: 32, weight: .heavy)).foregroundStyle(Sig.text)
                        Text("Where intelligence runs. Set one default or choose a destination for each Persona.")
                            .font(.system(size: 14)).foregroundStyle(Sig.faint)
                    }
                    ForEach(cfg.profiles) { p in row(p) }
                    Button { editing = nil; showEditor = true; tactile() } label: {
                        HStack(spacing: 10) {
                            Image(systemName: "plus.circle.fill").font(.system(size: 20, weight: .bold)).foregroundStyle(Sig.accent)
                            Text("New destination").font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                            Spacer()
                        }
                        .padding(16).frame(maxWidth: .infinity)
                        .background(Sig.accent.opacity(0.12), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [7, 5])).foregroundStyle(Sig.accent.opacity(0.5)))
                    }
                }
                .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .sheet(isPresented: $showEditor) {
            NavigationStack { ProfileEditor(existing: editing) }.preferredColorScheme(.dark)
        }
    }

    private func row(_ p: RuntimeProfile) -> some View {
        let active = cfg.activeProfileId == p.id
        return HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill((p.isLocal ? Sig.local : Sig.accent).opacity(0.16))
                Image(systemName: p.isLocal ? "iphone" : (p.kind == .desktop ? "desktopcomputer" : "cloud.fill"))
                    .font(.system(size: 18, weight: .bold)).foregroundStyle(p.isLocal ? Sig.local : Sig.accent)
            }.frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text(p.name).font(.system(size: 15.5, weight: .bold)).foregroundStyle(Sig.text).lineLimit(1)
                Text(p.isLocal ? "On-device · \(p.contextLimit / 1000)k ctx"
                     : p.kind == .desktop ? (p.model.isEmpty ? "Your desktop" : "Your desktop · \(p.model)")
                     : "\(p.egressHost ?? "endpoint") · \(p.contextLimit / 1000)k ctx")
                    .font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.faint).lineLimit(1)
            }
            Spacer(minLength: 4)
            if active {
                Text("ACTIVE").font(.system(size: 9.5, weight: .black)).tracking(0.8).foregroundStyle(.black)
                    .padding(.horizontal, 8).frame(height: 22).background(Sig.ok, in: Capsule())
            } else {
                Button { tactile(); cfg.activeProfileId = p.id } label: {
                    Text("Set active").font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.accent)
                        .padding(.horizontal, 11).frame(height: 30).background(Sig.s2, in: Capsule())
                }
            }
        }
        .padding(13)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(active ? Sig.ok.opacity(0.4) : Sig.line, lineWidth: 1))
        .contentShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .onTapGesture { editing = p; showEditor = true; tactile() }
        .contextMenu {
            if cfg.profiles.count > 1 { Button(role: .destructive) { cfg.deleteProfile(p.id) } label: { Label("Delete", systemImage: "trash") } }
        }
    }
}

/// Add or edit one profile. The API key writes to the Keychain on save, never onto the shape.
struct ProfileEditor: View {
    let existing: RuntimeProfile?
    @ObservedObject private var cfg = InferenceConfigStore.shared
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var isLocal = true
    @State private var modelFile = ""
    @State private var baseURL = ""
    @State private var model = ""
    @State private var apiKey = ""
    @State private var contextLimit = 16_384
    private let limits = [8_192, 16_384, 32_768, 131_072, 200_000]
    private var localModels: [InstalledModel] { ModelFiles.installed().filter { $0.kind == .language } }

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text(existing == nil ? "New destination" : "Edit destination").font(.system(size: 26, weight: .heavy)).foregroundStyle(Sig.text)
                    field("NAME", text: $name, placeholder: "e.g. Claude, OpenRouter, Studio box")
                    Picker("", selection: $isLocal) { Text("This device").tag(true); Text("OpenAI-compatible").tag(false) }
                        .pickerStyle(.segmented)
                    if isLocal {
                        label("MODEL")
                        Menu {
                            ForEach(localModels) { m in Button(m.name) { modelFile = m.id } }
                        } label: { pickerChip(modelFile.isEmpty ? (localModels.first?.name ?? "No models — download one") : modelFile) }
                    } else {
                        field("BASE URL", text: $baseURL, placeholder: "https://openrouter.ai/api/v1")
                        field("MODEL", text: $model, placeholder: "anthropic/claude-3.5-sonnet")
                        label("API KEY · stored in this device's Keychain, never synced")
                        SecureField("sk-…", text: $apiKey)
                            .padding(13).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12)).foregroundStyle(Sig.text)
                            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
                        label("CONTEXT WINDOW")
                        Menu {
                            ForEach(limits, id: \.self) { l in Button("\(l / 1000)k tokens") { contextLimit = l } }
                        } label: { pickerChip("\(contextLimit / 1000)k tokens") }
                    }
                    Button { save() } label: {
                        Text("Save destination").font(.system(size: 16, weight: .heavy)).foregroundStyle(.black)
                            .frame(maxWidth: .infinity).frame(height: 52).background(Sig.accent, in: Capsule())
                            .opacity(canSave ? 1 : 0.4)
                    }.disabled(!canSave)
                }
                .padding(20).frame(maxWidth: 640).frame(maxWidth: .infinity)
            }
        }
        .toolbar { ToolbarItem(placement: .topBarLeading) { Button("Cancel") { dismiss() } } }
        .navigationTitle(existing == nil ? "New" : "Edit").navigationBarTitleDisplayMode(.inline)
        .onAppear(perform: load)
    }

    private var canSave: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty &&
        (isLocal || URL(string: baseURL.trimmingCharacters(in: .whitespaces))?.host != nil)
    }

    private func load() {
        guard let e = existing else { modelFile = localModels.first?.id ?? ""; return }
        name = e.name; isLocal = e.isLocal; modelFile = e.modelFile; baseURL = e.baseURL
        model = e.model; contextLimit = e.contextLimit
        apiKey = ProfileKeyStore.get(e.id) ?? ""
    }

    private func save() {
        let id = existing?.id ?? "profile.\(UUID().uuidString.prefix(8))"
        let p = RuntimeProfile(id: id, name: name.trimmingCharacters(in: .whitespaces),
                               kind: isLocal ? .onDevice : .openAICompatible,
                               modelFile: isLocal ? modelFile : "",
                               baseURL: isLocal ? "" : baseURL.trimmingCharacters(in: .whitespaces),
                               model: isLocal ? "" : model.trimmingCharacters(in: .whitespaces),
                               contextLimit: isLocal ? 16_384 : contextLimit,
                               requiresKey: !isLocal && !apiKey.trimmingCharacters(in: .whitespaces).isEmpty,
                               createdAt: existing?.createdAt ?? Date(), updatedAt: Date())
        if !isLocal { ProfileKeyStore.set(apiKey, for: id) }   // key → Keychain, never on `p`
        cfg.upsertProfile(p)
        tactile(.medium); dismiss()
    }

    private func field(_ l: String, text: Binding<String>, placeholder: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            label(l)
            HStack(spacing: 8) {
                TextField(placeholder, text: text).font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                VoiceFillMic(text: text, tint: Sig.local, size: 26)
            }
            .padding(13).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
        }
    }
    private func label(_ s: String) -> some View {
        Text(s).font(.system(size: 9.5, weight: .black, design: .rounded)).tracking(1).foregroundStyle(Sig.faint)
    }
    private func pickerChip(_ s: String) -> some View {
        HStack { Text(s).font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.text).lineLimit(1); Spacer(); Image(systemName: "chevron.up.chevron.down").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint) }
            .padding(13).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12)).overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(Color.white.opacity(0.08), lineWidth: 1))
    }
}
