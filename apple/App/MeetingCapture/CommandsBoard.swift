import SwiftUI

// HSM-18-02 — the iPad CommandsBoard: author the voice command macros the Mac fires
// when a keyword is spoken (here or at the desk). The iPad authors and triggers; it
// never executes — every action runs on the Mac, and the board says so. Mirrors the
// web /commands board: the four kinds, Test via /api/commands/test, the canonical
// preview line (config.py `VoiceMacroAction.preview()` — kept in lockstep).

@MainActor final class CommandsBoardModel: ObservableObject {
    struct Draft: Identifiable {
        let id = UUID()
        var keyword = ""
        var kind = "open_url"
        var payload = ""
        var testOK: Bool?
        var testLine = ""
    }

    static let kinds: [(kind: String, label: String, glyph: String)] = [
        ("open_url", "Open URL", "globe"),
        ("launch_app", "Launch app", "app.badge"),
        ("shell", "Shell", "terminal"),
        ("type_text", "Type text", "keyboard"),
    ]

    @Published var enabled = false
    @Published var drafts: [Draft] = []
    @Published var loading = false
    @Published var saving = false
    @Published var savedTick = false
    @Published var boardError = ""

    private let peers = DictatePeerStore.shared
    var macName: String { peers.displayName }
    var isPaired: Bool { peers.isPaired }

    func load() async {
        guard let client = peers.client() else { boardError = "Pair your desktop first."; return }
        loading = true; defer { loading = false }
        do {
            let s = try await client.macroSettings()
            enabled = s.enabled
            drafts = s.items.map { Draft(keyword: $0.keyword, kind: $0.action.kind, payload: $0.action.payload) }
            boardError = ""
        } catch { boardError = "Couldn't reach \(macName)." }
    }

    /// PUT only the macros slice; the hub validates every macro (a clean 400 shows
    /// as the board error, never a silent drop).
    func save() async {
        guard let client = peers.client() else { boardError = "Pair your desktop first."; return }
        saving = true; defer { saving = false }
        let items = drafts.compactMap { d -> VoiceMacroSpec? in
            let keyword = d.keyword.trimmingCharacters(in: .whitespaces).lowercased()
            let payload = d.payload.trimmingCharacters(in: .whitespaces)
            guard !keyword.isEmpty, !payload.isEmpty else { return nil }
            return VoiceMacroSpec(keyword: keyword, action: VoiceMacroActionSpec(kind: d.kind, payload: payload))
        }
        do {
            try await client.updateMacroSettings(VoiceMacroSettings(enabled: enabled, items: items))
            boardError = ""
            withAnimation { savedTick = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) { [weak self] in
                withAnimation { self?.savedTick = false }
            }
        } catch { boardError = "Save failed — \(macName) rejected it or is unreachable." }
    }

    func test(_ id: UUID) async {
        guard let client = peers.client() else { boardError = "Pair your desktop first."; return }
        guard let i = drafts.firstIndex(where: { $0.id == id }) else { return }
        let d = drafts[i]
        do {
            let r = try await client.testMacro(kind: d.kind, payload: d.payload)
            drafts[i].testOK = r.ok
            if r.ok {
                drafts[i].testLine = r.tested == false ? (r.note ?? r.preview ?? "ok")
                                                       : (r.output?.isEmpty == false ? r.output! : (r.preview ?? "ok"))
            } else {
                drafts[i].testLine = r.error ?? "failed"
            }
        } catch {
            drafts[i].testOK = false
            drafts[i].testLine = "\(macName) unreachable"
        }
    }

    func remove(_ id: UUID) { drafts.removeAll { $0.id == id } }
    func add() { drafts.append(Draft()) }

    #if targetEnvironment(simulator)
    func seedDemo() {
        enabled = true
        drafts = [
            Draft(keyword: "standup", kind: "type_text", payload: "## Standup\n- ", testOK: true,
                  testLine: "types into the focused app"),
            Draft(keyword: "logs", kind: "shell", payload: "tail -n 50 /tmp/holdspeak.log"),
            Draft(keyword: "board", kind: "open_url", payload: "https://github.com/karolswdev/HoldSpeak/pulls"),
        ]
    }
    #endif
}

/// A text field with the speak-to-fill mic — every input on this board is speakable
/// ([[feedback_voice_mic_every_input]]); spoken symbols apply on the fill path.
struct MicFillField: View {
    let placeholder: String
    @Binding var text: String
    var axis: Axis = .horizontal
    @StateObject private var voice = VoiceCaptureState()

    var body: some View {
        HStack(spacing: 8) {
            TextField(placeholder, text: $text, axis: axis == .vertical ? .vertical : .horizontal)
                .font(.system(size: 15)).foregroundStyle(Sig.text)
                .autocorrectionDisabled()
                .textInputAutocapitalization(.never)
            Button {
                Task {
                    if voice.recording { await voice.stopAndTranscribe() } else { await voice.start() }
                }
            } label: {
                Image(systemName: voice.recording ? "waveform" : "mic.fill")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundStyle(voice.recording ? Sig.bad : Sig.accent)
                    .frame(width: 30, height: 30)
                    .background((voice.recording ? Sig.bad : Sig.accent).opacity(0.12), in: Circle())
            }
            .buttonStyle(.plain)
            .disabled(voice.transcribing)
        }
        .padding(.horizontal, 12).padding(.vertical, 9)
        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous)
            .strokeBorder(voice.recording ? Sig.bad.opacity(0.5) : Sig.line, lineWidth: 1))
        .onChange(of: voice.text) { _, t in if !t.isEmpty { text = t } }
    }
}

struct CommandsBoard: View {
    @StateObject private var model = CommandsBoardModel()
    @State private var appeared = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    header
                    enableRow
                    ForEach($model.drafts) { $draft in macroCard($draft) }
                    addButton
                    if !model.boardError.isEmpty {
                        Text(model.boardError).font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.warn)
                    }
                    saveBar
                }
                .padding(22).frame(maxWidth: 760).frame(maxWidth: .infinity)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .tint(Sig.accent)
        .onAppear {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.85)) { appeared = true }
            #if targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["HS_DEMO_COMMANDS"] == "1" { model.seedDemo(); return }
            #endif
            Task { await model.load() }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 9) {
            Button { dismiss() } label: {
                HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Dictate") }
                    .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
            }
            .buttonStyle(.plain)
            // The honesty mark: actions run on the Mac, never on this device.
            HStack(spacing: 6) {
                Image(systemName: "bolt.horizontal.fill").font(.system(size: 9, weight: .black))
                Text("RUNS ON \(model.macName.uppercased())").font(.system(size: 10, weight: .heavy)).tracking(1.0)
            }
            .foregroundStyle(Sig.warn)
            .padding(.horizontal, 10).padding(.vertical, 5)
            .background(Sig.warn.opacity(0.12), in: Capsule())
            .overlay(Capsule().strokeBorder(Sig.warn.opacity(0.25), lineWidth: 1))
            Text("Commands").font(.system(size: 38, weight: .heavy)).foregroundStyle(Sig.text)
            Text("Speak a keyword · the action fires").font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.faint)
        }
        .opacity(appeared ? 1 : 0)
    }

    private var enableRow: some View {
        Toggle(isOn: $model.enabled) {
            VStack(alignment: .leading, spacing: 3) {
                Text("Voice commands").font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                Text(model.enabled ? "Keywords fire" : "Off · keywords dictate as words")
                    .font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.faint)
            }
        }
        .tint(Sig.accent)
        .padding(16)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
    }

    private func macroCard(_ draft: Binding<CommandsBoardModel.Draft>) -> some View {
        let d = draft.wrappedValue
        let action = VoiceMacroActionSpec(kind: d.kind, payload: d.payload)
        return VStack(alignment: .leading, spacing: 11) {
            HStack(spacing: 8) {
                MicFillField(placeholder: "keyword — say this word", text: draft.keyword)
                Button { model.remove(d.id) } label: {
                    Image(systemName: "trash").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.faint)
                        .frame(width: 34, height: 34)
                        .background(Sig.s2, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                }
                .buttonStyle(.plain)
            }
            HStack(spacing: 8) {
                ForEach(CommandsBoardModel.kinds, id: \.kind) { k in
                    Button { draft.wrappedValue.kind = k.kind } label: {
                        HStack(spacing: 5) {
                            Image(systemName: k.glyph).font(.system(size: 11, weight: .bold))
                            Text(k.label).font(.system(size: 12, weight: .heavy))
                        }
                        .foregroundStyle(d.kind == k.kind ? .black : Sig.muted)
                        .padding(.horizontal, 11).padding(.vertical, 7)
                        .background(d.kind == k.kind ? AnyShapeStyle(Sig.accent) : AnyShapeStyle(Sig.s2), in: Capsule())
                        .overlay(Capsule().strokeBorder(d.kind == k.kind ? Color.clear : Sig.line, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }
            MicFillField(placeholder: payloadPlaceholder(d.kind), text: draft.payload,
                         axis: d.kind == "type_text" ? .vertical : .horizontal)
            HStack(spacing: 8) {
                // The canonical preview line — identical to the hub's audit string.
                if !d.payload.trimmingCharacters(in: .whitespaces).isEmpty {
                    Text(action.preview).font(.system(size: 12, weight: .semibold)).foregroundStyle(Sig.muted)
                        .lineLimit(1)
                }
                if d.kind == "shell" {
                    HStack(spacing: 4) {
                        Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 9, weight: .black))
                        Text("runs code on your Mac").font(.system(size: 10, weight: .heavy))
                    }
                    .foregroundStyle(Sig.warn)
                    .padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Sig.warn.opacity(0.12), in: Capsule())
                }
                Spacer(minLength: 0)
                Button { Task { await model.test(d.id) } } label: {
                    HStack(spacing: 5) {
                        Image(systemName: "play.fill").font(.system(size: 10, weight: .bold))
                        Text("Test").font(.system(size: 12, weight: .heavy))
                    }
                    .foregroundStyle(Sig.accent)
                    .padding(.horizontal, 12).padding(.vertical, 7)
                    .background(Sig.accent.opacity(0.12), in: Capsule())
                    .overlay(Capsule().strokeBorder(Sig.accent.opacity(0.3), lineWidth: 1))
                }
                .buttonStyle(.plain)
                .disabled(d.payload.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            if let ok = d.testOK {
                HStack(spacing: 6) {
                    Image(systemName: ok ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(ok ? Sig.ok : Sig.warn)
                    Text(d.testLine).font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(ok ? Sig.muted : Sig.warn).lineLimit(2)
                }
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Sig.line, lineWidth: 1))
        .opacity(appeared ? 1 : 0)
    }

    private func payloadPlaceholder(_ kind: String) -> String {
        switch kind {
        case "open_url": return "https://…"
        case "launch_app": return "app name or path"
        case "shell": return "shell command"
        default: return "the snippet to type"
        }
    }

    private var addButton: some View {
        Button { withAnimation { model.add() } } label: {
            HStack(spacing: 7) {
                Image(systemName: "plus.circle.fill").font(.system(size: 14, weight: .bold))
                Text("Add a command").font(.system(size: 14, weight: .heavy))
            }
            .foregroundStyle(Sig.accent)
            .frame(maxWidth: .infinity).padding(.vertical, 13)
            .background(Sig.accent.opacity(0.1), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(Sig.accent.opacity(0.3), style: StrokeStyle(lineWidth: 1, dash: [5, 4])))
        }
        .buttonStyle(.plain)
    }

    private var saveBar: some View {
        Button { Task { await model.save() } } label: {
            HStack(spacing: 8) {
                if model.saving { ProgressView().controlSize(.mini).tint(.black) }
                else { Image(systemName: model.savedTick ? "checkmark.circle.fill" : "arrow.down.doc.fill").font(.system(size: 14, weight: .bold)) }
                Text(model.savedTick ? "Saved to \(model.macName)" : "Save to \(model.macName)")
                    .font(.system(size: 15, weight: .heavy))
            }
            .foregroundStyle(.black)
            .frame(maxWidth: .infinity).padding(.vertical, 14)
            .background(Sig.accentGradient, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(Color.white.opacity(0.2), lineWidth: 1))
        }
        .buttonStyle(.plain)
        .disabled(model.saving || !model.isPaired)
    }
}
