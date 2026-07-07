import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

#if canImport(UIKit)
private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
    UIImpactFeedbackGenerator(style: s).impactOccurred()
}
#else
private enum HapticStub { case light, medium }
private func haptic(_ s: HapticStub) {}
#endif

// HSM-15-12 — "Ground this ask". The attach surface on the chat composer and the
// run sheet: pick meetings, expand each one (digest / transcript / its bound
// artifacts, independently toggleable), watch the gauge price the selection live.
// The selection persists per CONVERSATION (the chat keeps its grounding); the
// envelope itself is assembled by ContextEnvelope — the ONE assembler every run
// target calls.
struct GroundingPicker: View {
    let meetings: [Meeting]                        // newest first (the stage sorts)
    let artifactsFor: (Meeting) -> [OutputRecord]  // the meeting's drawer (bound artifacts)
    let contextLimit: Int                          // the run target's usable window
    let tokensFor: (GroundingSelection) -> Int     // the stage's envelope estimator
    @Binding var selection: GroundingSelection
    let onDone: () -> Void

    @State private var expanded: Set<String> = []

    var body: some View {
        DioAtelierPanel(maxW: 520, maxH: 720, dismiss: onDone) { panelBody }
            .onAppear { expanded.formUnion(selection.meetings.map(\.id)) }
    }

    private var panelBody: some View {
        VStack(spacing: 0) {
            header
            Rectangle().fill(.white.opacity(0.06)).frame(height: 1)
            ContextGauge(used: tokensFor(selection), limit: contextLimit)
                .padding(.horizontal, 18).padding(.vertical, 12)
            Rectangle().fill(.white.opacity(0.06)).frame(height: 1)
            list
            footer
        }
    }

    private var header: some View {
        HStack(spacing: 11) {
            Image(systemName: "square.stack.3d.up.fill")
                .font(.system(size: 20, weight: .bold)).foregroundStyle(DioPal.cobalt)
            VStack(alignment: .leading, spacing: 1) {
                Text("Ground this ask").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                Text(selection.isEmpty ? "Pick the meetings this question is about" : selection.summaryLabel)
                    .font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            }
            Spacer(minLength: 0)
            if !selection.isEmpty {
                Button { haptic(.light); withAnimation { selection = GroundingSelection() } } label: {
                    Text("Clear").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        .padding(.horizontal, 12).frame(height: 30).background(Capsule().fill(.white.opacity(0.06)))
                }.buttonStyle(.plain)
            }
            Button { onDone() } label: {
                Image(systemName: "xmark.circle.fill").font(.system(size: 22)).foregroundStyle(DioPal.muted)
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 18).padding(.vertical, 14)
    }

    private var list: some View {
        ScrollView {
            VStack(spacing: 8) {
                if meetings.isEmpty {
                    VStack(spacing: 9) {
                        DeskSprite(name: "cassette", size: 44)
                        Text("No meetings on this desk yet")
                            .font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                    }.frame(maxWidth: .infinity).padding(.top, 40)
                }
                ForEach(meetings, id: \.id) { m in meetingRow(m) }
            }
            .padding(.horizontal, 14).padding(.vertical, 12)
        }
        .frame(maxHeight: .infinity)
    }

    private func meetingRow(_ m: Meeting) -> some View {
        let picked = selection.meetings.first(where: { $0.id == m.id })
        let isOpen = expanded.contains(m.id)
        let arts = artifactsFor(m)
        return VStack(spacing: 0) {
            Button { toggleMeeting(m) } label: {
                HStack(spacing: 11) {
                    Image(systemName: picked != nil ? "checkmark.circle.fill" : "circle")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundStyle(picked != nil ? DioPal.cobalt : DioPal.muted.opacity(0.55))
                    DeskSprite(name: "cassette", size: 30)
                    VStack(alignment: .leading, spacing: 1) {
                        Text(displayTitle(m)).font(.system(size: 13.5, weight: .heavy, design: .rounded))
                            .foregroundStyle(DioPal.text).lineLimit(1)
                        Text(rowSubtitle(m, artifacts: arts.count))
                            .font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                    Spacer(minLength: 0)
                    Button { withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) { toggleExpand(m.id) } } label: {
                        Image(systemName: "chevron.down").font(.system(size: 12, weight: .black))
                            .foregroundStyle(DioPal.muted).rotationEffect(.degrees(isOpen ? 180 : 0))
                            .frame(width: 34, height: 34).background(Circle().fill(.white.opacity(0.05)))
                    }.buttonStyle(.plain)
                }
                .padding(.horizontal, 12).padding(.vertical, 10)
            }.buttonStyle(.plain)
            if isOpen {
                expansionRows(m, picked: picked, artifacts: arts)
                    .padding(.leading, 43).padding(.trailing, 12).padding(.bottom, 11)
            }
        }
        .background(RoundedRectangle(cornerRadius: 15, style: .continuous)
            .fill(picked != nil ? DioPal.cobalt.opacity(0.09) : Color.white.opacity(0.035))
            .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous)
                .strokeBorder(picked != nil ? DioPal.cobalt.opacity(0.4) : Color.white.opacity(0.07), lineWidth: 1)))
    }

    @ViewBuilder
    private func expansionRows(_ m: Meeting, picked: GroundingSelection.Meeting?, artifacts: [OutputRecord]) -> some View {
        let hasIntel = (m.intel?.summary.isEmpty == false)
        let lines = m.segments.count
        VStack(alignment: .leading, spacing: 7) {
            HStack(spacing: 7) {
                pill("Digest", icon: "sparkles", on: picked?.includeIntel ?? false, enabled: hasIntel && picked != nil) {
                    mutate(m) { $0.includeIntel.toggle() }
                }
                pill(lines > 0 ? "Transcript · \(lines)" : "Transcript", icon: "text.alignleft",
                     on: picked?.includeTranscript ?? false, enabled: lines > 0 && picked != nil) {
                    mutate(m) { $0.includeTranscript.toggle() }
                }
            }
            if !artifacts.isEmpty {
                FlowChips(items: artifacts.map { a in
                    (id: a.id, label: (a.lens.isEmpty || a.lens == a.title) ? a.title : "\(a.lens) · \(a.title)",
                     on: picked?.artifactIds.contains(a.id) ?? false, enabled: picked != nil)
                }) { aid in
                    mutate(m) { gm in
                        if let i = gm.artifactIds.firstIndex(of: aid) { gm.artifactIds.remove(at: i) }
                        else { gm.artifactIds.append(aid) }
                    }
                }
            }
        }
    }

    private func pill(_ label: String, icon: String, on: Bool, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button { if enabled { haptic(.light); withAnimation { action() } } } label: {
            HStack(spacing: 5) {
                Image(systemName: on ? "checkmark" : icon).font(.system(size: 10, weight: .black))
                Text(label).font(.system(size: 11.5, weight: .heavy, design: .rounded)).lineLimit(1)
            }
            .foregroundStyle(on ? DioPal.text : DioPal.muted.opacity(enabled ? 1 : 0.45))
            .padding(.horizontal, 11).frame(height: 30)
            .background(Capsule().fill(on ? DioPal.cobalt.opacity(0.3) : .white.opacity(0.05))
                .overlay(Capsule().strokeBorder(on ? DioPal.cobalt.opacity(0.7) : .clear, lineWidth: 1)))
        }.buttonStyle(.plain).disabled(!enabled)
    }

    private var footer: some View {
        Button { haptic(.medium); onDone() } label: {
            Text(selection.isEmpty ? "Done" : "Ground on \(selection.summaryLabel)")
                .font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(.white)
                .frame(maxWidth: .infinity).frame(height: 46)
                .background(Capsule().fill(LinearGradient(colors: [DioPal.cobalt, Color(hex: 0x3D6BD8)], startPoint: .top, endPoint: .bottom)))
        }.buttonStyle(.plain)
            .padding(.horizontal, 16).padding(.vertical, 12)
    }

    // MARK: - selection mechanics

    private func toggleMeeting(_ m: Meeting) {
        haptic(.light)
        withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
            if let i = selection.meetings.firstIndex(where: { $0.id == m.id }) {
                selection.meetings.remove(at: i)
                expanded.remove(m.id)
            } else {
                let df = DateFormatter(); df.dateFormat = "yyyy-MM-dd"
                selection.meetings.append(.init(
                    id: m.id, title: displayTitle(m), day: df.string(from: m.startedAt),
                    includeTranscript: false,
                    includeIntel: m.intel?.summary.isEmpty == false,
                    artifactIds: []))
                expanded.insert(m.id)
            }
        }
    }

    private func mutate(_ m: Meeting, _ change: (inout GroundingSelection.Meeting) -> Void) {
        guard let i = selection.meetings.firstIndex(where: { $0.id == m.id }) else { return }
        change(&selection.meetings[i])
    }

    private func toggleExpand(_ id: String) {
        if expanded.contains(id) { expanded.remove(id) } else { expanded.insert(id) }
    }

    private func displayTitle(_ m: Meeting) -> String {
        if let t = m.title, !t.isEmpty { return t }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"; return f.string(from: m.startedAt)
    }

    private func rowSubtitle(_ m: Meeting, artifacts: Int) -> String {
        let f = DateFormatter(); f.dateFormat = "MMM d"
        var parts = [f.string(from: m.startedAt)]
        if !m.segments.isEmpty { parts.append("\(m.segments.count) lines") }
        if artifacts > 0 { parts.append("\(artifacts) artifact\(artifacts == 1 ? "" : "s")") }
        return parts.joined(separator: "  ·  ")
    }
}

/// Wrapping chip row for a meeting's bound artifacts (each independently toggleable).
private struct FlowChips: View {
    let items: [(id: String, label: String, on: Bool, enabled: Bool)]
    let onTap: (String) -> Void
    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 130), spacing: 7)], alignment: .leading, spacing: 7) {
            ForEach(items, id: \.id) { item in
                Button { if item.enabled { haptic(.light); onTap(item.id) } } label: {
                    HStack(spacing: 5) {
                        Image(systemName: item.on ? "checkmark" : "doc.text").font(.system(size: 9, weight: .black))
                        Text(item.label).font(.system(size: 11, weight: .heavy, design: .rounded)).lineLimit(1)
                    }
                    .foregroundStyle(item.on ? DioPal.text : DioPal.muted.opacity(item.enabled ? 1 : 0.45))
                    .frame(maxWidth: .infinity).frame(height: 30)
                    .background(Capsule().fill(item.on ? DioPal.violet.opacity(0.28) : .white.opacity(0.05))
                        .overlay(Capsule().strokeBorder(item.on ? DioPal.violet.opacity(0.7) : .clear, lineWidth: 1)))
                }.buttonStyle(.plain).disabled(!item.enabled)
            }
        }
    }
}
