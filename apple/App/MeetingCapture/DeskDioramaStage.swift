import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — THE FRACTAL DESK, wired to the REAL app (v2 on owner feedback). Zones are LOW-PROFILE (a compact
// top shelf, not dominating boxes) so the canvas stays open. A tapped object's intelligence PULLS OUT from
// the right edge as a rich in-world drawer (real summary / actions / topics / transcript) — no centered
// modal, no plain nav window. A big always-on-top Back bar makes escaping a zone unmissable; a focus fog
// catches stray taps (a receded object no longer eats them). Make a place (+ New Zone), DRAG a meeting onto
// a shelf tray to file it, TAP a tray to DIVE in (camera rush, recursive sub-zones), breadcrumb climbs out.
// Reuses CaptureModel / CaptureView / MeetingDetailView / ModelFiles + DeskSprite. 3D desk behind HS_REAL_DESK=1.

enum DioPal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let trayTop = Color(hex: 0x1B1626), trayBot = Color(hex: 0x0C0A12)
    static let accent = Color(hex: 0xFF6B35), cobalt = Color(hex: 0x5B8DEF), violet = Color(hex: 0x9B6BFF)
    static let mint = Color(hex: 0x3ECF8E), text = Color(hex: 0xF4ECE0), muted = Color(hex: 0x9C93A8)
    static let zoneTints: [Color] = [accent, cobalt, violet, mint]
}

enum DioKind { case meeting, model, kb }
struct DioObj: Identifiable { let id: String; let kind: DioKind; let sprite: String; let base: CGFloat; let glow: Color; let title: String }
enum DioMode { case home, focus, recede }

// MARK: - hero object (drag to move/file, tap to open). Gesture on the STABLE outer view, not the TimelineView.
struct DioHero: View {
    let obj: DioObj; let landed: Bool; let mode: DioMode; let index: Int; let pos: CGPoint
    let onTap: () -> Void; let onDrop: (CGSize) -> Void; let onDragChange: (CGPoint?) -> Void
    @State private var drag: CGSize = .zero
    private var modeScale: CGFloat { mode == .focus ? 1.34 : (mode == .recede ? 0.6 : 1) }
    private var dim: Double { mode == .recede ? 0.3 : 1 }
    private let spring = Animation.spring(response: 0.5, dampingFraction: 0.72)
    var body: some View {
        let s = obj.base
        VStack(spacing: 7) {
            DioHeroVisual(obj: obj, focused: mode == .focus).frame(width: s, height: s)
            Text(obj.title).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.85))
                .lineLimit(1).frame(maxWidth: s + 36)
                .padding(.horizontal, 8).padding(.vertical, 3)
                .background(Capsule().fill(.black.opacity(0.32)))
                .opacity(mode == .recede ? 0.0 : 0.95)
        }
        .scaleEffect(landed ? (drag == .zero ? modeScale : modeScale * 1.08) : 0.15)
        .opacity(landed ? dim : 0)
        .offset(y: landed ? 0 : -240)
        .contentShape(Rectangle())
        .animation(.spring(response: 0.72, dampingFraction: 0.54).delay(Double(index) * 0.10), value: landed)
        .animation(spring, value: mode)
        .position(x: pos.x + drag.width, y: pos.y + drag.height)
        .zIndex(drag == .zero ? (mode == .focus ? 10 : 0) : 50)
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged {
                    if mode != .recede {
                        drag = $0.translation
                        onDragChange(CGPoint(x: pos.x + $0.translation.width, y: pos.y + $0.translation.height))
                    }
                }
                .onEnded { v in
                    onDragChange(nil)
                    let d = hypot(v.translation.width, v.translation.height)
                    if mode != .recede {                       // a receded object ignores taps; the fog catches them
                        if d < 9 { onTap() } else { onDrop(v.translation) }
                    }
                    drag = .zero
                }
        )
    }
}

struct DioHeroVisual: View {
    let obj: DioObj; let focused: Bool
    var body: some View {
        let s = obj.base
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate, ph = Double(abs(obj.id.hashValue) % 7)
            let bob = CGFloat(sin(t * 0.9 + ph) * 6)
            let breathe = 1 + CGFloat(sin(t * 1.15 + ph) * 0.018)
            let tilt = sin(t * 0.65 + ph) * 2.0
            let pulse = 0.6 + 0.4 * sin(t * 1.7 + ph)
            ZStack {
                Ellipse().fill(.black.opacity(0.5)).frame(width: s * 0.6, height: s * 0.15)
                    .blur(radius: 11).offset(y: s * 0.45 + bob * 0.25)
                Circle().fill(RadialGradient(colors: [obj.glow.opacity(focused ? 0.75 : 0.5), .clear], center: .center, startRadius: 2, endRadius: s * 0.8))
                    .frame(width: s * 1.8, height: s * 1.8).blur(radius: 12).opacity(pulse)
                DeskSprite(name: obj.sprite, size: s)
                    .rotationEffect(.degrees(tilt)).scaleEffect(breathe).offset(y: -bob)
                    .shadow(color: .black.opacity(0.55), radius: 15, y: 11)
            }
            .frame(width: s, height: s)
        }
    }
}

struct DioTrayMote: View {
    let sprite: String
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let bob = CGFloat(sin(t * 1.3 + Double(sprite.count)) * 2)
            DeskSprite(name: sprite, size: 30).offset(y: -bob)
        }
    }
}

// LOW-PROFILE zone tray — a compact labeled shelf tile (a place that holds meetings). Tap to dive; drop a meeting on it to file.
struct DioZoneTray: View {
    let name: String, tint: Color
    let members: [DioObj]; let subZones: Int; let size: CGSize
    let landed: Bool; let index: Int; let dimmed: Bool; let hot: Bool
    let onDive: () -> Void
    @State private var press = false
    var body: some View {
        let w = size.width, h = size.height
        HStack(spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill(tint.opacity(hot ? 0.4 : 0.18))
                Image(systemName: subZones > 0 ? "square.stack.3d.up.fill" : "tray.full.fill")
                    .font(.system(size: 18, weight: .bold)).foregroundStyle(tint)
            }
            .frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text(name).font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                HStack(spacing: 5) {
                    ForEach(Array(members.prefix(3).enumerated()), id: \.offset) { _, m in DioTrayMote(sprite: m.sprite) }
                    Text(hot ? "drop to file" : "\(members.count)\(subZones > 0 ? " · +\(subZones)" : "")")
                        .font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(tint)
                }
            }
            Spacer(minLength: 0)
            Image(systemName: "arrow.down.forward.and.arrow.up.backward").font(.system(size: 11, weight: .black)).foregroundStyle(tint.opacity(0.85))
        }
        .padding(.horizontal, 13)
        .frame(width: w, height: h)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(LinearGradient(colors: [DioPal.trayTop, DioPal.trayBot], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(tint.opacity(hot ? 1 : 0.45), lineWidth: hot ? 2.5 : 1.5))
                .shadow(color: .black.opacity(0.45), radius: 12, y: 8)
        )
        .scaleEffect(hot ? 1.04 : (press ? 0.96 : (landed ? 1 : 0.4))).opacity(landed ? (dimmed ? 0 : 1) : 0)
        .animation(.spring(response: 0.65, dampingFraction: 0.62).delay(Double(index) * 0.07), value: landed)
        .animation(.spring(response: 0.4, dampingFraction: 0.6), value: press)
        .animation(.spring(response: 0.35, dampingFraction: 0.6), value: hot)
        .allowsHitTesting(!dimmed)
        .contentShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .onTapGesture { press = true; DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { press = false; onDive() } }
    }
}

struct DioCreateTile: View {
    let size: CGSize; let landed: Bool; let dimmed: Bool; let onTap: () -> Void
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "plus.circle.fill").font(.system(size: 17, weight: .bold)).foregroundStyle(DioPal.muted)
            Text("New Zone").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
        }
        .frame(width: size.width, height: size.height)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous)
            .strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 5])).foregroundStyle(DioPal.muted.opacity(0.4)))
        .opacity(landed ? (dimmed ? 0 : 0.9) : 0)
        .allowsHitTesting(!dimmed).contentShape(Rectangle()).onTapGesture(perform: onTap)
    }
}

// The big, always-on-top way OUT of a zone.
struct DioBackBar: View {
    let crumbs: [(String, Color)]
    let onBack: () -> Void; let onJump: (Int) -> Void
    var body: some View {
        HStack(spacing: 10) {
            Button(action: onBack) {
                HStack(spacing: 5) {
                    Image(systemName: "chevron.left").font(.system(size: 15, weight: .black))
                    Text("Back").font(.system(size: 15, weight: .heavy, design: .rounded))
                }
                .foregroundStyle(DioPal.text).padding(.horizontal, 16).frame(height: 44)
                .background(Capsule().fill(.white.opacity(0.10)).overlay(Capsule().strokeBorder(.white.opacity(0.18), lineWidth: 1)))
            }.buttonStyle(.plain)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(Array(crumbs.enumerated()), id: \.offset) { i, c in
                        if i > 0 { Image(systemName: "chevron.right").font(.system(size: 10, weight: .black)).foregroundStyle(DioPal.muted) }
                        let last = i == crumbs.count - 1
                        Button { if !last { onJump(i) } } label: {
                            HStack(spacing: 5) {
                                if i == 0 { Image(systemName: "house.fill").font(.system(size: 11, weight: .bold)) }
                                else { Circle().fill(c.1).frame(width: 7, height: 7) }
                                Text(c.0).font(.system(size: 13, weight: .heavy, design: .rounded))
                            }
                            .foregroundStyle(last ? DioPal.text : DioPal.muted).padding(.horizontal, 11).frame(height: 38)
                            .background(Capsule().fill(.white.opacity(last ? 0.10 : 0.04))
                                .overlay(Capsule().strokeBorder((last ? c.1 : .clear).opacity(0.6), lineWidth: 1)))
                        }.buttonStyle(.plain).disabled(last)
                    }
                }
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 16).frame(maxWidth: .infinity, alignment: .leading)
    }
}

// THE PULL-OUT — a tapped object's contents slide out from the right as a rich in-world drawer (real data).
struct DioPullout: View {
    let obj: DioObj; let meeting: Meeting?; let kbItems: Int
    let onClose: () -> Void; let onFullEditor: () -> Void

    private var subtitle: String {
        guard let m = meeting else { return obj.kind == .model ? "on this iPad" : "\(kbItems) item\(kbItems == 1 ? "" : "s")" }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"
        let spk = Set(m.segments.map(\.speaker)).count
        let dur = m.formattedDuration ?? (m.duration.map { "\(Int($0 / 60)) min" } ?? "")
        return [f.string(from: m.startedAt), dur.isEmpty ? nil : dur, "\(spk) speaker\(spk == 1 ? "" : "s")"].compactMap { $0 }.joined(separator: "  ·  ")
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 11) {
                DeskSprite(name: obj.sprite, size: 40)
                VStack(alignment: .leading, spacing: 2) {
                    Text(obj.title).font(.system(size: 18, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                    Text(subtitle).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                }
                Spacer(minLength: 0)
                HStack(spacing: 5) {
                    Image(systemName: "lock.fill").font(.system(size: 9, weight: .bold))
                    Text("On device").font(.system(size: 10, weight: .heavy, design: .rounded))
                }.foregroundStyle(DioPal.mint).padding(.horizontal, 9).frame(height: 26).background(Capsule().fill(DioPal.mint.opacity(0.14)))
                Button(action: onClose) {
                    Image(systemName: "xmark").font(.system(size: 14, weight: .black)).foregroundStyle(DioPal.text)
                        .frame(width: 36, height: 36).background(Circle().fill(.white.opacity(0.10)))
                }.buttonStyle(.plain)
            }
            .padding(.horizontal, 18).padding(.top, 16).padding(.bottom, 12)
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 16) { content() }
                    .padding(.horizontal, 18).padding(.bottom, 26)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x161320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 28, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 28, x: -10, y: 8)
        )
    }

    @ViewBuilder private func content() -> some View {
        switch obj.kind {
        case .meeting:
            if let m = meeting {
                if let s = m.intel?.summary, !s.isEmpty {
                    DrawerSection(label: "SUMMARY", tint: DioPal.accent) {
                        Text(s).font(.system(size: 14.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.92)).fixedSize(horizontal: false, vertical: true)
                    }
                }
                let acts = m.intel?.actionItems ?? []
                if !acts.isEmpty {
                    DrawerSection(label: "ACTIONS · \(acts.count)", tint: DioPal.mint) {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(acts, id: \.id) { a in
                                HStack(alignment: .top, spacing: 10) {
                                    Image(systemName: "circle").font(.system(size: 15, weight: .bold)).foregroundStyle(DioPal.mint).padding(.top, 1)
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(a.task).font(.system(size: 14, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text).fixedSize(horizontal: false, vertical: true)
                                        if a.owner != nil || a.due != nil {
                                            Text([a.owner, a.due].compactMap { $0 }.joined(separator: " · ")).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                let topics = m.intel?.topics ?? []
                if !topics.isEmpty { DrawerSection(label: "TOPICS", tint: DioPal.violet) { FlowChips(items: topics, tint: DioPal.violet) } }
                if !m.segments.isEmpty {
                    DrawerSection(label: "TRANSCRIPT · \(m.segments.count) lines", tint: DioPal.cobalt) {
                        VStack(alignment: .leading, spacing: 9) {
                            ForEach(Array(m.segments.enumerated()), id: \.offset) { _, seg in
                                VStack(alignment: .leading, spacing: 1) {
                                    Text(seg.speaker.isEmpty ? "Speaker" : seg.speaker).font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.cobalt)
                                    Text(seg.text).font(.system(size: 13.5, weight: .regular, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.88)).fixedSize(horizontal: false, vertical: true)
                                }
                            }
                        }
                    }
                }
                if (m.intel?.summary.isEmpty ?? true) && (m.intel?.actionItems.isEmpty ?? true) && m.segments.isEmpty {
                    Text("No intelligence yet — it's still on the way, or generate it from the meeting.")
                        .font(.system(size: 13, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                        .frame(maxWidth: .infinity, alignment: .center).padding(.vertical, 24)
                }
                Button(action: onFullEditor) {
                    Text("Open full editor").font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        .frame(maxWidth: .infinity).frame(height: 40)
                        .background(Capsule().strokeBorder(DioPal.muted.opacity(0.4), lineWidth: 1))
                }.buttonStyle(.plain).padding(.top, 4)
            }
        case .model:
            DrawerSection(label: "MODEL", tint: DioPal.cobalt) {
                Text("\(obj.title) — loaded and ready. Every meeting is summarised on this iPad; nothing leaves the device.")
                    .font(.system(size: 14, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9)).fixedSize(horizontal: false, vertical: true)
            }
        case .kb:
            DrawerSection(label: "KNOWLEDGE", tint: DioPal.violet) {
                Text("\(kbItems) item\(kbItems == 1 ? "" : "s") filed here. Ask a grounded question and get an answer cited from your own notes.")
                    .font(.system(size: 14, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9)).fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct DrawerSection<Content: View>: View {
    let label: String; let tint: Color; @ViewBuilder let content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: 9) {
            HStack(spacing: 7) {
                RoundedRectangle(cornerRadius: 2).fill(tint).frame(width: 4, height: 13)
                Text(label).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(tint).tracking(1.2)
            }
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading).padding(14)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.04))
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white.opacity(0.06), lineWidth: 1)))
    }
}

struct FlowChips: View {
    let items: [String]; let tint: Color
    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 76), spacing: 8, alignment: .leading)], alignment: .leading, spacing: 8) {
            ForEach(Array(items.enumerated()), id: \.offset) { _, it in
                Text(it).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9))
                    .lineLimit(1).padding(.horizontal, 10).padding(.vertical, 6)
                    .background(Capsule().fill(tint.opacity(0.14)).overlay(Capsule().strokeBorder(tint.opacity(0.35), lineWidth: 1)))
            }
        }
    }
}

struct DioCompanion: View {
    let landed: Bool; let excited: Bool
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let sway = sin(t * (excited ? 3.0 : 1.6)) * (excited ? 7 : 4.5)
            let bob = CGFloat(sin(t * 2.0) * 4)
            let cycle = t.truncatingRemainder(dividingBy: excited ? 1.4 : 3.4)
            let hop = cycle < 0.4 ? CGFloat(sin(cycle / 0.4 * .pi)) * (excited ? 34 : 24) : 0
            ZStack {
                Ellipse().fill(.black.opacity(0.5)).frame(width: 60, height: 14).blur(radius: 9)
                    .offset(y: 46).opacity(landed ? (hop > 1 ? 0.4 : 1) : 0)
                DeskSprite(name: "qlippy", size: 100)
                    .rotationEffect(.degrees(landed ? sway : 0))
                    .offset(y: landed ? -bob - hop : -300)
                    .scaleEffect(landed ? 1 : 0.1).opacity(landed ? 1 : 0)
                    .shadow(color: .black.opacity(0.5), radius: 12, y: 8)
                    .animation(.spring(response: 0.8, dampingFraction: 0.5).delay(0.6), value: landed)
            }
        }
    }
}

struct DioMotes: View {
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            Canvas { ctx, size in
                for i in 0..<16 {
                    let s = Double(i)
                    let x = (sin(t * 0.18 + s * 1.7) * 0.5 + 0.5) * size.width
                    let y = size.height - (t * 9 + s * 57).truncatingRemainder(dividingBy: Double(size.height + 80))
                    let r = 1.4 + s.truncatingRemainder(dividingBy: 3)
                    ctx.opacity = 0.06 + 0.05 * (sin(t + s) * 0.5 + 0.5)
                    ctx.fill(Path(ellipseIn: CGRect(x: x, y: y, width: r, height: r)), with: .color(.white))
                }
            }
        }
    }
}

struct DioRecordOrb: View {
    let onTap: () -> Void
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                ForEach(0..<2) { i in
                    let p = (sin(t * 1.3 + Double(i) * 1.6) * 0.5 + 0.5)
                    Circle().stroke(DioPal.accent.opacity(0.35 * (1 - p)), lineWidth: 2)
                        .frame(width: 64 + CGFloat(p) * 46, height: 64 + CGFloat(p) * 46)
                }
                Circle().fill(RadialGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent, Color(hex: 0xC23C16)],
                                             center: .init(x: 0.4, y: 0.35), startRadius: 2, endRadius: 40))
                    .frame(width: 66, height: 66).shadow(color: DioPal.accent.opacity(0.6), radius: 16, y: 6)
                Image(systemName: "mic.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(.white)
            }
            .scaleEffect(1 + CGFloat(sin(t * 2) * 0.02)).frame(width: 96, height: 96).contentShape(Circle())
        }
        .onTapGesture(perform: onTap)
    }
}

struct DioStage: View {
    @StateObject private var model = CaptureModel()
    @AppStorage("hs.diorama.pos") private var posCSV = ""
    @AppStorage("hs.diorama.zones") private var zonesCSV = ""
    @AppStorage("hs.diorama.filed") private var dfiledCSV = ""
    @AppStorage("hs.desk.kbs") private var kbsCSV = ""
    @AppStorage("hs.desk.filed") private var kbFiledCSV = ""
    @State private var landed = false
    @State private var path: [String] = []
    @State private var diveDir = 1
    @State private var flash = 0.0
    @State private var selected: String? = nil
    @State private var capturing = false
    @State private var openMeeting: Meeting? = nil
    @State private var positions: [String: CGPoint] = [:]
    @State private var zones: [(path: String, color: Int)] = []
    @State private var filed: [String: String] = [:]
    @State private var dragHotZone: String? = nil
    @State private var namingZone = false
    @State private var newZoneName = ""
    private let diveSpring = Animation.spring(response: 0.6, dampingFraction: 0.74)
    private let focusSpring = Animation.spring(response: 0.5, dampingFraction: 0.72)

    private var pathKey: String { path.joined(separator: "/") }
    private var curTint: Color { path.isEmpty ? DioPal.accent : tintFor(pathKey) }
    private func tintFor(_ zpath: String) -> Color {
        if let z = zones.first(where: { $0.path == zpath }) { return DioPal.zoneTints[z.color % DioPal.zoneTints.count] }
        return DioPal.accent
    }
    private func name(of zpath: String) -> String { zpath.split(separator: "/").last.map(String.init) ?? zpath }
    private func parent(of zpath: String) -> String {
        var c = zpath.split(separator: "/").map(String.init); if !c.isEmpty { c.removeLast() }; return c.joined(separator: "/")
    }
    private func childZones() -> [(path: String, color: Int)] { zones.filter { parent(of: $0.path) == pathKey } }

    private var meetings: [Meeting] { model.meetings.sorted { $0.startedAt > $1.startedAt } }
    private var knowledgeBases: [String] { kbsCSV.split(separator: ";").map(String.init).filter { !$0.isEmpty } }
    private func kbCount(_ n: String) -> Int {
        kbFiledCSV.split(separator: ";").compactMap { p -> String? in let kv = p.split(separator: "=", maxSplits: 1); return kv.count == 2 ? String(kv[1]) : nil }.filter { $0 == n }.count
    }
    private func meetingTitle(_ m: Meeting) -> String {
        if let t = m.title, !t.isEmpty { return t }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"; return f.string(from: m.startedAt)
    }
    private func obj(for m: Meeting, _ i: Int) -> DioObj {
        DioObj(id: "m:\(m.id)", kind: .meeting, sprite: i % 2 == 0 ? "cassette" : "cassette2", base: 130, glow: DioPal.accent, title: meetingTitle(m))
    }
    private func members() -> [DioObj] {
        var out: [DioObj] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == pathKey { out.append(obj(for: m, i)) }
        if path.isEmpty {
            for mdl in ModelFiles.installed().prefix(2) {
                out.append(DioObj(id: "model:\(mdl.id)", kind: .model, sprite: "cartridge", base: 162, glow: DioPal.cobalt,
                                  title: mdl.name.replacingOccurrences(of: ".gguf", with: "")))
            }
            for kb in knowledgeBases.prefix(3) {
                out.append(DioObj(id: "kb:\(kb)", kind: .kb, sprite: "crystal", base: 120, glow: DioPal.violet, title: kb))
            }
        }
        return out
    }
    private func membersOf(_ zpath: String) -> [DioObj] {
        var out: [DioObj] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == zpath { out.append(obj(for: m, i)) }
        return out
    }
    private func meeting(forObj id: String) -> Meeting? {
        guard id.hasPrefix("m:") else { return nil }
        let mid = String(id.dropFirst(2)); return model.meetings.first { $0.id == mid }
    }
    private func selectedObj() -> DioObj? { members().first { $0.id == selected } }

    private func mode(_ id: String) -> DioMode { selected == nil ? .home : (selected == id ? .focus : .recede) }

    // MARK: layout — low-profile shelf at top, objects on the open canvas
    private func shelfSize(_ n: Int, _ w: CGFloat) -> CGSize {
        let cols = max(1, min(3, n)); return CGSize(width: (w - 40) / CGFloat(cols) - 10, height: 66)
    }
    private func shelfPos(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let cols = max(1, min(3, n)); let size = shelfSize(n, w)
        let r = i / cols, c = i % cols
        let rowW = CGFloat(cols) * (size.width + 10) - 10
        let x = (w - rowW) / 2 + size.width / 2 + CGFloat(c) * (size.width + 10)
        let y = h * 0.16 + CGFloat(r) * (size.height + 10)
        return CGPoint(x: x, y: y)
    }
    private func looseHome(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let cols = max(1, min(3, n)); let r = i / cols, c = i % cols
        let x = cols == 1 ? 0.5 : 0.22 + 0.56 * Double(c) / Double(cols - 1)
        let rows = max(1, Int(ceil(Double(n) / Double(cols))))
        let y = rows == 1 ? 0.55 : 0.48 + 0.2 * Double(r) / Double(rows - 1)
        return CGPoint(x: w * x, y: h * y)
    }
    private func pos(_ id: String, _ fallback: CGPoint, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        if selected == id { return CGPoint(x: w * 0.24, y: h * 0.44) }   // spotlight to the left, drawer pulls out right
        if let u = positions[id] { return CGPoint(x: w * u.x, y: h * u.y) }
        return fallback
    }

    private var diveTransition: AnyTransition {
        diveDir >= 0
            ? .asymmetric(insertion: .scale(scale: 0.6).combined(with: .opacity), removal: .scale(scale: 1.6).combined(with: .opacity))
            : .asymmetric(insertion: .scale(scale: 1.6).combined(with: .opacity), removal: .scale(scale: 0.6).combined(with: .opacity))
    }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack {
                LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .top, endPoint: .bottom)
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    RadialGradient(colors: [(selected == nil ? curTint : DioPal.cobalt).opacity(0.16 + 0.05 * sin(t * 1.2)), .clear],
                                   center: .init(x: 0.5, y: 0.4), startRadius: 20, endRadius: w * 0.95)
                        .blendMode(.plusLighter).animation(diveSpring, value: pathKey)
                }
                DioMotes()
                Color.clear.contentShape(Rectangle()).onTapGesture {
                    if selected != nil { select(nil) } else if !path.isEmpty { climbOut() }
                }

                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 25, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(members().isEmpty && childZones().isEmpty ? "tap record to capture your first meeting" : "drag a meeting onto a zone · tap to open")
                        .font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                }
                .opacity(landed && selected == nil && path.isEmpty ? 1 : 0)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.05)

                ForEach([pathKey], id: \.self) { _ in level(w, h) }
                    .transition(diveTransition)

                DioCompanion(landed: landed, excited: selected != nil).position(x: w * 0.9, y: h * 0.9)
                if landed && selected == nil {
                    DioRecordOrb { capturing = true }.position(x: w * 0.5, y: h * 0.91).transition(.scale.combined(with: .opacity))
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.5)], center: .center, startRadius: 160, endRadius: 800)
                    .blendMode(.multiply).allowsHitTesting(false)
                RadialGradient(colors: [curTint.opacity(flash), .clear], center: .center, startRadius: 10, endRadius: w)
                    .blendMode(.plusLighter).allowsHitTesting(false)

                if let o = selectedObj() {
                    DioPullout(obj: o, meeting: meeting(forObj: o.id), kbItems: o.kind == .kb ? kbCount(o.title) : 0,
                               onClose: { select(nil) },
                               onFullEditor: { if let m = meeting(forObj: o.id) { openMeeting = m } })
                        .frame(width: min(560, w * 0.62))
                        .padding(.vertical, 22).padding(.trailing, 16)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                        .transition(.move(edge: .trailing).combined(with: .opacity)).zIndex(60)
                }

                if !path.isEmpty && selected == nil {
                    DioBackBar(crumbs: crumbs(), onBack: { climbOut() }, onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.045).zIndex(100)
                }
            }
            .ignoresSafeArea()
            .onAppear { landed = true; load(); model.refresh() }
            .alert("New zone", isPresented: $namingZone) {
                TextField("Name", text: $newZoneName)
                Button("Cancel", role: .cancel) { newZoneName = "" }
                Button("Create") { createZone(newZoneName); newZoneName = "" }
            } message: { Text(path.isEmpty ? "A place on your desk that holds meetings." : "A sub-zone inside \(name(of: pathKey)).") }
            .fullScreenCover(isPresented: $capturing) {
                CaptureView(model: model, done: { capturing = false; model.refresh() })
            }
            .sheet(isPresented: Binding(get: { openMeeting != nil }, set: { if !$0 { openMeeting = nil } })) {
                if let m = openMeeting { NavigationStack { MeetingDetailView(meeting: m) }.preferredColorScheme(.dark) }
            }
        }
        .preferredColorScheme(.dark)
    }

    @ViewBuilder private func level(_ w: CGFloat, _ h: CGFloat) -> some View {
        let zs = childZones(); let ms = members(); let slotN = zs.count + 1
        ZStack {
            ForEach(Array(zs.enumerated()), id: \.element.path) { i, z in
                DioZoneTray(name: name(of: z.path), tint: DioPal.zoneTints[z.color % DioPal.zoneTints.count],
                            members: membersOf(z.path), subZones: zones.filter { parent(of: $0.path) == z.path }.count,
                            size: shelfSize(slotN, w), landed: landed, index: i, dimmed: selected != nil,
                            hot: dragHotZone == z.path, onDive: { dive(into: z.path) })
                    .position(shelfPos(i, slotN, w, h))
            }
            DioCreateTile(size: shelfSize(slotN, w), landed: landed, dimmed: selected != nil) { haptic(.light); namingZone = true }
                .position(shelfPos(zs.count, slotN, w, h))

            ForEach(Array(ms.enumerated()), id: \.element.id) { i, o in
                DioHero(obj: o, landed: landed, mode: mode(o.id), index: i, pos: pos(o.id, looseHome(i, ms.count, w, h), w, h),
                        onTap: { select(selected == o.id ? nil : o.id) },
                        onDrop: { tr in drop(o, looseHome(i, ms.count, w, h), tr, w, h) },
                        onDragChange: { p in updateHot(o, p, zs, slotN, w, h) })
            }

            if selected != nil {
                Color.black.opacity(0.45).ignoresSafeArea().onTapGesture { select(nil) }
                    .zIndex(5).transition(.opacity)
            }
        }
    }

    private func crumbs() -> [(String, Color)] {
        var out: [(String, Color)] = [("Desk", DioPal.accent)]; var acc: [String] = []
        for comp in path { acc.append(comp); let id = acc.joined(separator: "/"); out.append((comp, tintFor(id))) }
        return out
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
    private func whoosh() { flash = 0.5; withAnimation(.easeOut(duration: 0.6)) { flash = 0 } }
    private func dive(into zpath: String) {
        haptic(.heavy); whoosh(); diveDir = 1
        withAnimation(diveSpring) { selected = nil; path = zpath.split(separator: "/").map(String.init) }
    }
    private func climbOut() { guard !path.isEmpty else { return }; haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; path.removeLast() } }
    private func jump(to i: Int) { haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; path = Array(path.prefix(i)) } }
    private func select(_ id: String?) { haptic(id == nil ? .light : .medium); withAnimation(focusSpring) { selected = id } }
    private func createZone(_ raw: String) {
        let nm = raw.replacingOccurrences(of: "/", with: " ").trimmingCharacters(in: .whitespaces)
        guard !nm.isEmpty else { return }
        let zpath = path.isEmpty ? nm : pathKey + "/" + nm
        guard !zones.contains(where: { $0.path == zpath }) else { return }
        haptic(.medium)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) { zones.append((zpath, zones.count)) }
        persistZones()
    }
    private func updateHot(_ o: DioObj, _ p: CGPoint?, _ zs: [(path: String, color: Int)], _ slotN: Int, _ w: CGFloat, _ h: CGFloat) {
        guard o.kind == .meeting, let p = p else { if dragHotZone != nil { dragHotZone = nil }; return }
        dragHotZone = trayHit(p, zs, slotN, w, h)
    }
    private func trayHit(_ p: CGPoint, _ zs: [(path: String, color: Int)], _ slotN: Int, _ w: CGFloat, _ h: CGFloat) -> String? {
        let size = shelfSize(slotN, w)
        for (i, z) in zs.enumerated() {
            let c = shelfPos(i, slotN, w, h)
            let rect = CGRect(x: c.x - size.width / 2, y: c.y - size.height / 2, width: size.width, height: size.height).insetBy(dx: -14, dy: -14)
            if rect.contains(p) { return z.path }
        }
        return nil
    }
    private func drop(_ o: DioObj, _ fallback: CGPoint, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        let start = pos(o.id, fallback, w, h)
        let end = CGPoint(x: start.x + tr.width, y: start.y + tr.height)
        let zs = childZones(); let slotN = zs.count + 1
        if o.kind == .meeting, let z = trayHit(end, zs, slotN, w, h) { file(o.id, into: z) }
        else {
            haptic(.light)
            let u = positions[o.id] ?? CGPoint(x: start.x / w, y: start.y / h)
            positions[o.id] = CGPoint(x: min(0.92, max(0.08, u.x + tr.width / w)), y: min(0.82, max(0.2, u.y + tr.height / h)))
            persistPositions()
        }
        dragHotZone = nil
    }
    private func file(_ id: String, into zpath: String) {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(focusSpring) { filed[id] = zpath; positions[id] = nil }
        persistFiled(); persistPositions()
    }

    private func persistPositions() { posCSV = positions.map { "\($0.key)=\($0.value.x),\($0.value.y)" }.joined(separator: ";") }
    private func persistZones() { zonesCSV = zones.map { "\($0.path)|\($0.color)" }.joined(separator: ";") }
    private func persistFiled() { dfiledCSV = filed.map { "\($0.key)=\($0.value)" }.joined(separator: ";") }
    private func load() {
        var pd: [String: CGPoint] = [:]
        for row in posCSV.split(separator: ";") {
            let kv = row.split(separator: "="); guard kv.count == 2 else { continue }
            let xy = kv[1].split(separator: ","); guard xy.count == 2, let x = Double(xy[0]), let y = Double(xy[1]) else { continue }
            pd[String(kv[0])] = CGPoint(x: x, y: y)
        }
        positions = pd
        zones = zonesCSV.split(separator: ";").compactMap { row in
            let f = row.split(separator: "|"); guard f.count == 2, let ci = Int(f[1]) else { return nil }
            return (String(f[0]), ci)
        }
        var fd: [String: String] = [:]
        for row in dfiledCSV.split(separator: ";") {
            let kv = row.split(separator: "=", maxSplits: 1); guard kv.count == 2 else { continue }
            fd[String(kv[0])] = String(kv[1])
        }
        filed = fd
    }
}
