import SwiftUI

// HSM-17 — AGENT SYNC. A live Claude/Codex coding session, mirrored on the desk richly enough to
// RECREATE the running session — not a presence badge, a session mirror. Our hooks
// (holdspeak/agent_context + agent_hook.py) capture the full event stream Claude/Codex emit; the
// contract below carries it; the desk replays it as a live "running coder" feed and lets you answer /
// approve inline. The session is an append-log (events accumulate), persisted for replay.
//
// Kept as kind `.coder` (not `.agent`) for now: reclaiming `.agent` cascades through the whole
// Tailored-Agents subsystem and deserves its own pass.

// MARK: - the contract (robust: a session header + a typed event stream)

enum CoderTool: String, Equatable {
    case read, edit, write, bash, search, web, task
    var verb: String {
        switch self {
        case .read: return "Reading"; case .edit: return "Editing"; case .write: return "Writing"
        case .bash: return "Running"; case .search: return "Searching"; case .web: return "Fetching"
        case .task: return "Delegating"
        }
    }
    var icon: String {
        switch self {
        case .read: return "doc.text"; case .edit: return "pencil"; case .write: return "square.and.pencil"
        case .bash: return "terminal"; case .search: return "magnifyingglass"; case .web: return "globe"
        case .task: return "person.2.fill"
        }
    }
    var tint: Color {
        switch self {
        case .read, .search, .web: return DioPal.cobalt
        case .edit, .write: return DioPal.mint
        case .bash: return DioPal.violet
        case .task: return DioPal.accent
        }
    }
}

struct CoderEvent: Identifiable, Equatable {
    enum Kind: Equatable {
        case userPrompt(String)                                            // what the driver asked
        case assistant(String)                                             // the coder's narration / plan
        case tool(CoderTool, target: String, detail: String?)              // a tool call in flight
        case result(ok: Bool, summary: String, added: Int?, removed: Int?) // its outcome (diff stats / status)
        case command(cmd: String, exit: Int?, output: String?)             // a shell run
        case approval(question: String, command: String?)                  // the blocking ask (drives .waiting)
        case notification(String)
        case usage(tokens: Int)
        case ended
    }
    var id: String
    var ts: Date?
    var kind: Kind
}

struct CoderSession: Identifiable, Equatable {
    enum State: String { case working, waiting, idle, ended }
    var agent: String              // "claude" / "codex"
    var sessionId: String
    var project: String?
    var model: String?
    var tokensUsed: Int?
    var state: State
    var events: [CoderEvent]

    var id: String { "coder:\(agent)/\(sessionId)" }
    var isClaude: Bool { agent.lowercased() != "codex" }
    var display: String { isClaude ? "Claude" : "Codex" }

    // the pending ask the desk must surface + you resolve
    var pendingApproval: CoderEvent? {
        guard state == .waiting else { return nil }
        return events.last { if case .approval = $0.kind { return true }; return false }
    }
    var question: String? {
        if case .approval(let q, _)? = pendingApproval?.kind { return q }
        return nil
    }

    init(agent: String, sessionId: String, project: String? = nil, model: String? = nil,
         tokensUsed: Int? = nil, state: State, events: [CoderEvent] = []) {
        self.agent = agent; self.sessionId = sessionId; self.project = project; self.model = model
        self.tokensUsed = tokensUsed; self.state = state; self.events = events
    }
    // the minimal live wire shape today (the companion target) → a header-only session
    init(from t: CompanionTarget) {
        agent = t.agent; sessionId = t.sessionID; project = t.project; model = nil; tokensUsed = nil
        state = t.question != nil ? .waiting : (t.stale ? .idle : .working)
        events = t.question.map { [CoderEvent(id: "ask", ts: nil, kind: .approval(question: $0, command: nil))] } ?? []
    }

    // the full live set (HSM-17-02, GET /api/coders/sessions) → a session with an
    // honest minimal feed built from what the hub actually captured. The rich
    // per-event stream is the 17-01 transport follow-on; nothing here is invented.
    init(from live: LiveCoderSession) {
        agent = live.agent
        sessionId = live.sessionID
        project = live.project ?? live.cwd.map { URL(fileURLWithPath: $0).lastPathComponent }
        model = live.model
        tokensUsed = nil
        state = State(rawValue: live.state) ?? .working
        var evts: [CoderEvent] = []
        if let p = live.lastPrompt {
            evts.append(CoderEvent(id: "prompt", ts: nil, kind: .userPrompt(p)))
        }
        if let t = live.lastTool, let tool = CoderTool(hookName: t) {
            evts.append(CoderEvent(id: "tool", ts: nil, kind: .tool(tool, target: "", detail: nil)))
        }
        if state == .ended {
            evts.append(CoderEvent(id: "end", ts: nil, kind: .ended))
        }
        // last, so pendingApproval (events.last matching .approval) finds it
        if let q = live.question {
            evts.append(CoderEvent(id: "ask", ts: nil, kind: .approval(question: q, command: nil)))
        }
        events = evts
    }
}

extension CoderTool {
    /// A hub hook tool name ("Bash", "Edit", "Write", "Task", "Read"…) → the desk's
    /// tool vocabulary. Unknown names return nil (the feed simply omits the row).
    init?(hookName: String) {
        switch hookName.lowercased() {
        case "read": self = .read
        case "edit", "apply_patch", "multiedit": self = .edit
        case "write": self = .write
        case "bash", "shell": self = .bash
        case "grep", "glob", "search": self = .search
        case "webfetch", "websearch", "web": self = .web
        case "task", "agent": self = .task
        default: return nil
        }
    }
}

// MARK: - the desk primitive

struct AgentSessionPrimitive: DeskPrimitive {
    let session: CoderSession
    var id: String { session.id }
    var kind: PrimitiveKind { .coder }
    var glyph: String { session.isClaude ? "sparkles" : "chevron.left.forwardslash.chevron.right" }
    var isSymbol: Bool { true }
    var base: CGFloat { 118 }
    var color: Color { session.state == .waiting ? DioPal.accent : DioPal.cobalt }
    var title: String { session.display + (session.project.map { " · \($0)" } ?? "") }
    var subtitle: String {
        switch session.state {
        case .working: return "coding · working"
        case .waiting: return "waiting on you"
        case .idle:    return "idle"
        case .ended:   return "ended"
        }
    }
    var preview: String? { session.question ?? subtitle }
    var sections: [PrimitiveSection] {
        if let q = session.question {
            return [.init(label: "NEEDS YOU", tint: DioPal.accent, body: .text(q))]
        }
        let last = session.events.reversed().compactMap { CoderFeedRow.line(for: $0) }.first
        let proj = session.project.map { " in \($0)" } ?? ""
        let fallback = "A live \(session.display) session\(proj). Tap to open the running session."
        return [.init(label: session.display.uppercased(), tint: DioPal.cobalt, body: .text(last ?? fallback))]
    }
    var actions: [PrimitiveAction] {
        var a = [PrimitiveAction(label: "Open live session", icon: "rectangle.expand.vertical", role: .custom("opensession"))]
        if session.state == .waiting { a.append(PrimitiveAction(label: "Answer", icon: "arrowshape.turn.up.left.fill", role: .custom("answer"))) }
        return a
    }
    var accepts: [PrimitiveKind] { session.state == .waiting ? [.meeting, .artifact, .summary, .actions, .topics, .note] : [] }
    // A live coding session runs on the paired Mac; answers you drop here cross the LAN (HSM-21-01).
    var egress: EgressScope { .mixed("your desktop") }
}

// MARK: - the live session feed (the "running coder" window)

enum CoderFeedRow {
    // a compact one-line description of an event, for the primitive preview
    static func line(for e: CoderEvent) -> String? {
        switch e.kind {
        case .userPrompt: return nil
        case .assistant(let t): return t
        case .tool(let k, let target, _): return "\(k.verb) \(target)"
        case .result(let ok, let s, let add, let rem):
            if let a = add, let r = rem { return "\(s) +\(a) −\(r)" }
            return (ok ? "" : "⚠ ") + s
        case .command(let c, _, _): return "$ \(c)"
        case .approval(let q, _): return q
        case .notification(let n): return n
        case .usage: return nil
        case .ended: return "session ended"
        }
    }
}

struct DioCoderSession: View {
    let session: CoderSession
    var maxW: CGFloat = 480       // clamped by the caller's DeskCamera so it fits the lane (HSM-20-04)
    var maxH: CGFloat = 560
    let onAnswer: () -> Void
    let onApprove: () -> Void
    let onClose: () -> Void
    private var accent: Color { session.isClaude ? DioPal.accent : DioPal.cobalt }
    var body: some View {
        ZStack {
            Color.black.opacity(0.74).ignoresSafeArea().onTapGesture { onClose() }
            VStack(spacing: 0) {
                header
                Divider().overlay(.white.opacity(0.08))
                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(session.events) { ev in eventRow(ev).id(ev.id) }
                            if session.state == .working {
                                HStack(spacing: 7) {
                                    ProgressView().controlSize(.mini).tint(DioPal.muted)
                                    Text("\(session.display) is working…").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                                }.padding(.top, 2).id("tail")
                            }
                            Color.clear.frame(height: 1).id("bottom")
                        }
                        .frame(maxWidth: .infinity, alignment: .leading).padding(16)
                    }
                    .onAppear { DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { withAnimation { proxy.scrollTo("bottom", anchor: .bottom) } } }
                    .onChange(of: session.events.count) { _ in withAnimation { proxy.scrollTo("bottom", anchor: .bottom) } }
                }
                if session.state == .waiting, let q = session.question { footer(q) }
            }
            .frame(width: maxW, height: maxH)
            .background(RoundedRectangle(cornerRadius: 24, style: .continuous).fill(.ultraThinMaterial)
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).fill(DioPal.cobalt.opacity(0.05)))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                .shadow(color: .black.opacity(0.4), radius: 22, y: 10))
        }
    }

    private var header: some View {
        HStack(spacing: 11) {
            Image(systemName: session.isClaude ? "sparkles" : "chevron.left.forwardslash.chevron.right")
                .font(.system(size: 16, weight: .bold)).foregroundStyle(accent)
                .frame(width: 38, height: 38).background(Circle().fill(accent.opacity(0.16)))
            VStack(alignment: .leading, spacing: 1) {
                Text(session.display + (session.project.map { " · \($0)" } ?? ""))
                    .font(.system(size: 16, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                HStack(spacing: 8) {
                    statePill
                    if let m = session.model { Text(m).font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted) }
                    if let tk = session.tokensUsed { Text("\(tk) tok").font(.system(size: 10, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(DioPal.muted) }
                }
            }
            Spacer(minLength: 0)
            Button(action: onClose) {
                Image(systemName: "xmark").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9))
                    .frame(width: 30, height: 30).background(Circle().fill(.white.opacity(0.1)))
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 16).padding(.vertical, 13)
    }
    private var statePill: some View {
        let (label, tint): (String, Color) = {
            switch session.state {
            case .working: return ("● working", DioPal.mint)
            case .waiting: return ("● needs you", DioPal.accent)
            case .idle:    return ("○ idle", DioPal.muted)
            case .ended:   return ("ended", DioPal.muted)
            }
        }()
        return Text(label).font(.system(size: 10, weight: .black, design: .rounded)).foregroundStyle(tint)
            .padding(.horizontal, 8).padding(.vertical, 2).background(Capsule().fill(tint.opacity(0.14)))
    }

    @ViewBuilder private func eventRow(_ e: CoderEvent) -> some View {
        switch e.kind {
        case .userPrompt(let t):
            row(icon: "person.fill", tint: DioPal.muted) {
                Text(t).font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.85))
            }
        case .assistant(let t):
            HStack(alignment: .top, spacing: 9) {
                Image(systemName: "sparkle").font(.system(size: 12, weight: .bold)).foregroundStyle(accent).frame(width: 20)
                Text(t).font(.system(size: 13.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text).fixedSize(horizontal: false, vertical: true)
            }
        case .tool(let k, let target, let detail):
            row(icon: k.icon, tint: k.tint) {
                (Text(k.verb + " ").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                 + Text(target).font(.system(size: 13, weight: .heavy, design: .rounded).monospaced()).foregroundStyle(DioPal.text))
                if let d = detail { Text(d).font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted) }
            }
        case .result(let ok, let s, let add, let rem):
            row(icon: ok ? "checkmark" : "exclamationmark.triangle.fill", tint: ok ? DioPal.mint : Color(hex: 0xFF6B6B)) {
                HStack(spacing: 8) {
                    Text(s).font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.85))
                    if let a = add, let r = rem {
                        Text("+\(a)").font(.system(size: 12, weight: .black, design: .rounded).monospacedDigit()).foregroundStyle(DioPal.mint)
                        Text("−\(r)").font(.system(size: 12, weight: .black, design: .rounded).monospacedDigit()).foregroundStyle(Color(hex: 0xFF6B6B))
                    }
                }
            }
        case .command(let c, let exit, let output):
            VStack(alignment: .leading, spacing: 4) {
                row(icon: "terminal", tint: DioPal.violet) {
                    Text("$ \(c)").font(.system(size: 12.5, weight: .heavy, design: .monospaced)).foregroundStyle(DioPal.text)
                }
                if let o = output, !o.isEmpty {
                    Text(o).font(.system(size: 11, weight: .regular, design: .monospaced)).foregroundStyle(DioPal.muted)
                        .lineLimit(3).padding(.leading, 29)
                }
                if let x = exit { Text(x == 0 ? "exit 0" : "exit \(x)").font(.system(size: 10, weight: .black, design: .rounded)).foregroundStyle(x == 0 ? DioPal.mint : Color(hex: 0xFF6B6B)).padding(.leading, 29) }
            }
        case .approval(let q, let cmd):
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 7) { Image(systemName: "hand.raised.fill").font(.system(size: 12, weight: .bold)); Text("NEEDS YOU").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1.2) }
                    .foregroundStyle(DioPal.accent)
                Text(q).font(.system(size: 13.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).fixedSize(horizontal: false, vertical: true)
                if let c = cmd { Text("$ \(c)").font(.system(size: 12, weight: .heavy, design: .monospaced)).foregroundStyle(DioPal.muted) }
            }
            .padding(12).frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(DioPal.accent.opacity(0.1))
                .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(DioPal.accent.opacity(0.4), lineWidth: 1)))
        case .notification(let n):
            row(icon: "bell.fill", tint: DioPal.muted) {
                Text(n).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            }
        case .usage(let tk):
            Text("\(tk) tokens").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted.opacity(0.7)).padding(.leading, 29)
        case .ended:
            row(icon: "stop.circle.fill", tint: DioPal.muted) {
                Text("Session ended").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
            }
        }
    }
    @ViewBuilder private func row<C: View>(icon: String, tint: Color, @ViewBuilder _ content: () -> C) -> some View {
        HStack(alignment: .top, spacing: 9) {
            Image(systemName: icon).font(.system(size: 11, weight: .bold)).foregroundStyle(tint).frame(width: 20, height: 18)
            VStack(alignment: .leading, spacing: 2) { content() }
            Spacer(minLength: 0)
        }
    }

    private func footer(_ q: String) -> some View {
        HStack(spacing: 11) {
            Button(action: onApprove) {
                HStack(spacing: 7) { Image(systemName: "checkmark"); Text("Approve").font(.system(size: 14.5, weight: .heavy, design: .rounded)) }
                    .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 50)
                    .background(Capsule().fill(LinearGradient(colors: [DioPal.mint, DioPal.mint.opacity(0.6)], startPoint: .top, endPoint: .bottom)))
            }.buttonStyle(.plain)
            Button(action: onAnswer) {
                HStack(spacing: 7) { Image(systemName: "arrowshape.turn.up.left.fill"); Text("Answer").font(.system(size: 14.5, weight: .heavy, design: .rounded)) }
                    .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 50)
                    .background(Capsule().fill(LinearGradient(colors: [DioPal.accent, DioPal.accent.opacity(0.6)], startPoint: .top, endPoint: .bottom)))
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 16).padding(.vertical, 13)
        .background(Rectangle().fill(.black.opacity(0.2)).overlay(Rectangle().fill(.white.opacity(0.03))))
    }
}

// MARK: - the answer composer (typed → send; voice / dropped-context / AI-draft fold in here next)

struct DioCoderAnswer: View {
    let session: CoderSession
    var maxW: CGFloat = 400       // clamped by the caller's DeskCamera so it fits the lane (HSM-20-04)
    let onSend: (String) -> Void
    let onCancel: () -> Void
    @State private var text = ""
    @FocusState private var focused: Bool
    var body: some View {
        ZStack {
            Color.black.opacity(0.78).ignoresSafeArea().onTapGesture { onCancel() }
            RadialGradient(colors: [DioPal.accent.opacity(0.16), .clear], center: .center, startRadius: 4, endRadius: 360)
                .ignoresSafeArea().allowsHitTesting(false)
            VStack(spacing: 16) {
                HStack(spacing: 9) {
                    Image(systemName: session.isClaude ? "sparkles" : "chevron.left.forwardslash.chevron.right")
                        .font(.system(size: 15, weight: .bold)).foregroundStyle(DioPal.accent)
                    Text("ANSWER \(session.display.uppercased())").font(.system(size: 11, weight: .black, design: .rounded)).tracking(1.6).foregroundStyle(DioPal.accent)
                    Spacer(minLength: 0)
                }
                if let q = session.question {
                    VStack(alignment: .leading, spacing: 5) {
                        Text("THE QUESTION").font(.system(size: 9, weight: .black, design: .rounded)).tracking(1.2).foregroundStyle(DioPal.muted)
                        Text(q).font(.system(size: 14, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text).fixedSize(horizontal: false, vertical: true)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading).padding(13)
                    .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.05))
                        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(DioPal.accent.opacity(0.22), lineWidth: 1)))
                }
                ZStack(alignment: .topLeading) {
                    if text.isEmpty {
                        Text("Type your reply…").font(.system(size: 15, weight: .medium, design: .rounded))
                            .foregroundStyle(DioPal.muted.opacity(0.7)).padding(.top, 8).padding(.leading, 5)
                    }
                    TextEditor(text: $text)
                        .font(.system(size: 15, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text)
                        .scrollContentBackground(.hidden).background(.clear).focused($focused)
                        .frame(minHeight: 120, maxHeight: 200)
                }
                .padding(13)
                .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.05))
                    .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
                HStack(spacing: 13) {
                    Button { onCancel() } label: {
                        Text("Cancel").font(.system(size: 15, weight: .heavy, design: .rounded))
                            .foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 54).background(Capsule().fill(.white.opacity(0.06)))
                    }.buttonStyle(.plain)
                    Button { onSend(text) } label: {
                        HStack(spacing: 8) { Image(systemName: "paperplane.fill"); Text("Send").font(.system(size: 16.5, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 54)
                            .background(Capsule().fill(LinearGradient(colors: [DioPal.accent, DioPal.accent.opacity(0.6)], startPoint: .top, endPoint: .bottom)))
                            .shadow(color: DioPal.accent.opacity(0.45), radius: 10, y: 4)
                    }.buttonStyle(.plain).opacity(text.trimmingCharacters(in: .whitespaces).isEmpty ? 0.5 : 1)
                }
            }
            .frame(width: maxW).padding(.vertical, 8)
        }
    }
}
