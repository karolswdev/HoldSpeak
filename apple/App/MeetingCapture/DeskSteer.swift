import SwiftUI

// HSM-27-02 — the terminal surface on the diorama. The iPad's counterpart to
// the web desk's SessionPullout: attach to a pane (peek, read-only), then
// consume the Hub's policy decision. Secure/Normal use an exact pane grant;
// YOLO can steer a registered pane directly while identity, allowed keys,
// audit, and Receipts remain mandatory.
//
// This view is presentational: DioStage owns the async client calls + the
// peek poll and passes the state in, so the surface stays testable and the
// HS_DESK_STEER sim seed renders it fully offline.

private let INTERRUPT = Color(hex: 0xFF5A5A)

/// A key on the palette — a labeled cap and the SteerKey it sends.
private struct SteerCap: Identifiable {
    let id = UUID()
    let label: String
    let key: SteerKey
    var loud: Bool = false
}
private let STEER_CAPS: [SteerCap] = [
    SteerCap(label: "^C", key: .interrupt, loud: true),
    SteerCap(label: "Esc", key: .escape),
    SteerCap(label: "Tab", key: .named("Tab")),
    SteerCap(label: "⏎", key: .enter),
    SteerCap(label: "↑", key: .up),
    SteerCap(label: "↓", key: .down),
    SteerCap(label: "←", key: .left),
    SteerCap(label: "→", key: .right),
]

/// The state DioStage feeds the sheet (the peek + the grant + the machine).
struct SteerSheetState: Equatable {
    var paneKey: String            // "pane:%3" or "claude:abc"
    var title: String              // "pane · %3"
    var lines: [String]            // the peek's pane content
    var question: String?          // an awaiting-response question
    var armed: Bool
    var remaining: Int             // grant seconds left
    var node: String               // "" = this Mac, else the node name
    var nodes: [String]            // configured node names
    var panes: [PaneInfo]          // the machine's pane list (the picker)
    var fate: String               // the last act's fate, in place ("" = none)
    var fateOK: Bool
    var paneId: String? = nil
    var operation: CoderSteeringOperation? = nil
    var policy: CoderSteeringPolicy? = nil
    var commitment: CoderSteeringCommitment? = nil
    var armCommitment: String = "Arm this pane"

    var postureAuthorized: Bool { policy?.usesControlPosture == true }
    var canSteer: Bool { armed || postureAuthorized }
}

struct DioSteerSheet: View {
    let state: SteerSheetState
    var maxW: CGFloat = 460
    var maxH: CGFloat = 620
    let onArm: () -> Void
    let onDisarm: () -> Void
    let onKey: (SteerKey, String) -> Void
    let onSteer: (String, Bool) -> Void
    let onSpawn: (String) -> Void
    let onAttach: (String) -> Void
    let onKill: () -> Void
    let onCycleNode: () -> Void
    let onClose: () -> Void
    var startPanesOpen: Bool = false

    @State private var text: String = ""
    @State private var submitOn: Bool = true
    @State private var spawnName: String = ""
    @State private var showPanes: Bool = false
    @State private var confirmKill: Bool = false

    var body: some View {
        ZStack {
            Color.black.opacity(0.74).ignoresSafeArea().onTapGesture { onClose() }
            VStack(spacing: 0) {
                header
                Divider().overlay(.white.opacity(0.08))
                if showPanes { paneStrip }
                paneView
                if state.canSteer { armedFoot }
            }
            .frame(width: maxW, height: maxH)
            .background(RoundedRectangle(cornerRadius: 24, style: .continuous).fill(.ultraThinMaterial)
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).fill(DioPal.violet.opacity(0.05)))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                .shadow(color: .black.opacity(0.4), radius: 22, y: 10))
        }
        .onAppear { if startPanesOpen { showPanes = true } }
    }

    // MARK: header — title, panes, node chip, ARM

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "terminal.fill").font(.system(size: 15, weight: .bold)).foregroundStyle(DioPal.violet)
                .frame(width: 36, height: 36).background(Circle().fill(DioPal.violet.opacity(0.16)))
            VStack(alignment: .leading, spacing: 1) {
                Text(state.title).font(.system(size: 15, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                Button(action: onCycleNode) {
                    Text("⧉ " + (state.node.isEmpty ? "this Mac" : state.node))
                        .font(.system(size: 10, weight: .heavy, design: .rounded))
                        .foregroundStyle(state.node.isEmpty ? DioPal.muted : DioPal.accent)
                }.buttonStyle(.plain)
            }
            Spacer(minLength: 0)
            Button { withAnimation { showPanes.toggle() } } label: {
                Image(systemName: "square.grid.2x2.fill").font(.system(size: 12, weight: .bold))
                    .foregroundStyle(showPanes ? DioPal.accent : DioPal.muted)
                    .frame(width: 30, height: 30).background(Circle().fill(.white.opacity(0.08)))
            }.buttonStyle(.plain)
            armChip
            Button(action: onClose) {
                Image(systemName: "xmark").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9))
                    .frame(width: 30, height: 30).background(Circle().fill(.white.opacity(0.1)))
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 16).padding(.vertical, 12)
    }

    private var armChip: some View {
        Group {
            if state.postureAuthorized {
                HStack(spacing: 6) {
                    PostureBadge(mode: state.policy?.mode ?? "yolo")
                    if state.armed {
                        Button(action: onDisarm) {
                            Text("Controls \(mmss(state.remaining))")
                                .font(.system(size: 10, weight: .black, design: .monospaced))
                                .foregroundStyle(DioPal.muted)
                        }.buttonStyle(.plain)
                    }
                }
            } else if state.armed {
                Button(action: onDisarm) {
                    Text("⏻ \(mmss(state.remaining))")
                        .font(.system(size: 12, weight: .black, design: .monospaced)).foregroundStyle(DioPal.accent)
                        .padding(.horizontal, 11).frame(height: 30)
                        .background(Capsule().fill(DioPal.accent.opacity(0.14)).overlay(Capsule().strokeBorder(DioPal.accent.opacity(0.5), lineWidth: 1)))
                }.buttonStyle(.plain)
            } else {
                Button(action: onArm) {
                    Text(state.armCommitment)
                        .font(.system(size: 12, weight: .black, design: .rounded)).tracking(1).foregroundStyle(DioPal.text)
                        .padding(.horizontal, 13).frame(height: 30)
                        .background(Capsule().fill(.white.opacity(0.08))
                            .overlay(Capsule().strokeBorder(.white.opacity(0.18), lineWidth: 1)))
                }.buttonStyle(.plain)
            }
        }
    }

    private func mmss(_ s: Int) -> String { "\(max(0, s) / 60):" + String(format: "%02d", max(0, s) % 60) }

    // MARK: the pane picker (attach to any) + spawn

    private var paneStrip: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                TextField("new session name", text: $spawnName)
                    .font(.system(size: 12, weight: .semibold, design: .monospaced)).foregroundStyle(DioPal.text)
                    .padding(.horizontal, 9).frame(height: 30)
                    .background(RoundedRectangle(cornerRadius: 8).fill(.white.opacity(0.06)))
                Button {
                    let n = spawnName.trimmingCharacters(in: .whitespaces); guard !n.isEmpty else { return }
                    onSpawn(n); spawnName = ""; withAnimation { showPanes = false }
                } label: {
                    Text("+ Spawn").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.mint)
                        .padding(.horizontal, 10).frame(height: 30)
                        .background(Capsule().fill(DioPal.mint.opacity(0.14)))
                }.buttonStyle(.plain).disabled(spawnName.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            ForEach(state.panes, id: \.paneId) { p in
                Button { onAttach("pane:\(p.paneId)"); withAnimation { showPanes = false } } label: {
                    HStack(spacing: 8) {
                        Text(p.paneId).font(.system(size: 12, weight: .black, design: .monospaced)).foregroundStyle(DioPal.accent).frame(width: 34, alignment: .leading)
                        Text(p.session + (p.command.map { " · \($0)" } ?? "")).font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                        Spacer(minLength: 0)
                    }
                    .padding(.horizontal, 9).frame(height: 30)
                    .background(RoundedRectangle(cornerRadius: 8).fill((p.active ?? false) ? DioPal.accent.opacity(0.08) : .white.opacity(0.02)))
                }.buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .background(Rectangle().fill(.black.opacity(0.18)))
    }

    private var paneView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 8) {
                if let q = state.question, !q.isEmpty {
                    HStack(spacing: 7) { Image(systemName: "hand.raised.fill").font(.system(size: 11, weight: .bold)); Text(q).font(.system(size: 13, weight: .heavy, design: .rounded)).fixedSize(horizontal: false, vertical: true) }
                        .foregroundStyle(DioPal.accent).frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10).background(RoundedRectangle(cornerRadius: 12).fill(DioPal.accent.opacity(0.1)))
                }
                Text(state.lines.joined(separator: "\n"))
                    .font(.system(size: 11.5, weight: .regular, design: .monospaced)).foregroundStyle(DioPal.text.opacity(0.92))
                    .frame(maxWidth: .infinity, alignment: .leading).textSelection(.enabled)
            }.padding(14)
        }
    }

    // MARK: the authorized foot — key palette, composer, factory

    private var armedFoot: some View {
        VStack(spacing: 9) {
            if let operation = state.operation, let policy = state.policy {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Pane \(operation.destination ?? "unresolved") · \(ProductLanguage.controlModeLabel(policy.mode ?? "yolo"))")
                        .font(.system(size: 10.5, weight: .heavy, design: .rounded))
                        .foregroundStyle(DioPal.text.opacity(0.85))
                    Text("Authority: \(policy.authorityBasis == "control_posture" ? "Control posture" : "Armed pane grant") · Receipt: after every attempt")
                        .font(.system(size: 9.5, weight: .semibold, design: .rounded))
                        .foregroundStyle(DioPal.muted)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            // KEY PALETTE
            HStack(spacing: 6) {
                Text("KEYS").font(.system(size: 9, weight: .black, design: .monospaced)).tracking(1).foregroundStyle(DioPal.muted)
                ForEach(STEER_CAPS) { cap in
                    Button { onKey(cap.key, cap.label) } label: {
                        Text(cap.label).font(.system(size: 13, weight: .heavy, design: .monospaced))
                            .foregroundStyle(cap.loud ? INTERRUPT : DioPal.text)
                            .frame(minWidth: 30, minHeight: 28)
                            .background(RoundedRectangle(cornerRadius: 7).fill(.white.opacity(0.06))
                                .overlay(RoundedRectangle(cornerRadius: 7).strokeBorder(cap.loud ? INTERRUPT.opacity(0.5) : .white.opacity(0.14), lineWidth: 1)))
                    }.buttonStyle(.plain)
                }
                Spacer(minLength: 0)
            }
            // COMPOSER
            HStack(spacing: 8) {
                TextField("Steer", text: $text, axis: .vertical)
                    .font(.system(size: 12, weight: .medium, design: .monospaced)).foregroundStyle(DioPal.text).lineLimit(1...3)
                    .padding(.horizontal, 10).padding(.vertical, 7)
                    .background(RoundedRectangle(cornerRadius: 9).fill(.white.opacity(0.06)))
                Button { submitOn.toggle() } label: {
                    Image(systemName: "return").font(.system(size: 13, weight: .bold)).foregroundStyle(submitOn ? DioPal.accent : DioPal.muted)
                        .frame(width: 34, height: 34).background(RoundedRectangle(cornerRadius: 9).fill(.white.opacity(0.06)))
                }.buttonStyle(.plain)
                Button {
                    let t = text.trimmingCharacters(in: .whitespaces); guard !t.isEmpty else { return }
                    onSteer(t, submitOn); text = ""
                } label: {
                    Text("Send").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(.white)
                        .padding(.horizontal, 14).frame(height: 34)
                        .background(Capsule().fill(DioPal.accent))
                }.buttonStyle(.plain).disabled(text.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            // SESSION — kill (rename lives here on the couch build)
            HStack(spacing: 8) {
                Text("SESSION").font(.system(size: 9, weight: .black, design: .monospaced)).tracking(1).foregroundStyle(DioPal.muted)
                if !state.armed {
                    Button(action: onArm) {
                        Text("Arm pane for rename and kill")
                            .font(.system(size: 11, weight: .heavy, design: .rounded))
                            .foregroundStyle(DioPal.muted)
                    }.buttonStyle(.plain)
                } else if confirmKill {
                    Button(action: onKill) {
                        Text("⌫ Kill — sure?").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(.white)
                            .padding(.horizontal, 11).frame(height: 30).background(Capsule().fill(INTERRUPT))
                    }.buttonStyle(.plain)
                    Button { confirmKill = false } label: { Image(systemName: "xmark").font(.system(size: 11, weight: .bold)).foregroundStyle(DioPal.muted).frame(width: 30, height: 30) }.buttonStyle(.plain)
                } else {
                    Button { confirmKill = true } label: {
                        Text("⌫ Kill").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(INTERRUPT)
                            .padding(.horizontal, 11).frame(height: 30)
                            .background(Capsule().fill(.white.opacity(0.06)).overlay(Capsule().strokeBorder(INTERRUPT.opacity(0.4), lineWidth: 1)))
                    }.buttonStyle(.plain)
                }
                Spacer(minLength: 0)
                if !state.fate.isEmpty {
                    Text((state.fateOK ? "✓ " : "✕ ") + state.fate)
                        .font(.system(size: 11, weight: .heavy, design: .monospaced)).foregroundStyle(state.fateOK ? DioPal.mint : INTERRUPT)
                }
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 12)
        .background(Rectangle().fill(.black.opacity(0.22)))
    }
}

#if DEBUG
extension SteerSheetState {
    /// A sim-seed sample so the terminal surface renders on glass without a
    /// live hub (HS_DESK_STEER). Mirrors a real armed pane.
    static func sample() -> SteerSheetState {
        SteerSheetState(
            paneKey: "pane:%3", title: "pane · %3",
            lines: [
                "$ npm run build",
                "  vite v5.4.2 building for production...",
                "  ✓ 214 modules transformed.",
                "  dist/assets/index-a1b2.js   142.8 kB",
                "  ✓ built in 6.47s",
                "$ ⏳ running the suite before I push — continue?",
            ],
            question: "running the suite before I push — continue?",
            armed: true, remaining: 842, node: "", nodes: ["beta"],
            panes: [
                PaneInfo(paneId: "%3", session: "holdspeak", window: "0", command: "claude", title: "", active: true),
                PaneInfo(paneId: "%7", session: "web-build", window: "1", command: "npm", title: "", active: false),
                PaneInfo(paneId: "%9", session: "scratch", window: "0", command: "bash", title: "", active: false),
            ],
            fate: "", fateOK: true)
    }
}
#endif
