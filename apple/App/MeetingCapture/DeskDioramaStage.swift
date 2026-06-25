import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — THE FRACTAL DESK, wired to the REAL app. The 2.5D motion-first diorama now has PLACES.
// Named zone trays HOLD your meetings: make a zone (+ New Zone), DRAG a meeting onto a tray to file it
// (drop-to-tag), then TAP the tray to DIVE in — the camera rushes, the zone becomes the whole desk with
// its members and its own sub-zones (recursive). A breadcrumb shows where you are and climbs back out.
// Meetings live where you file them; models (AI-core cartridges) and knowledge bases (crystals) stay at
// root. Reuses CaptureModel / CaptureView / MeetingDetailView / ModelFiles + DeskSprite. Composed +
// proven in the Simulator harness (scripts/diorama) first. 3D desk behind HS_REAL_DESK=1.

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
    private var modeScale: CGFloat { mode == .focus ? 1.3 : (mode == .recede ? 0.6 : 1) }
    private var dim: Double { mode == .recede ? 0.32 : 1 }
    private let spring = Animation.spring(response: 0.55, dampingFraction: 0.62)
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
        .zIndex(drag == .zero ? 0 : 50)
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
                    if d < 9 { onTap() } else if mode != .recede { onDrop(v.translation) }
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
                Circle().fill(RadialGradient(colors: [obj.glow.opacity(focused ? 0.7 : 0.5), .clear], center: .center, startRadius: 2, endRadius: s * 0.8))
                    .frame(width: s * 1.8, height: s * 1.8).blur(radius: 12).opacity(pulse)
                DeskSprite(name: obj.sprite, size: s)
                    .rotationEffect(.degrees(tilt)).scaleEffect(breathe).offset(y: -bob)
                    .shadow(color: .black.opacity(0.55), radius: 15, y: 11)
            }
            .frame(width: s, height: s)
        }
    }
}

// MARK: - a premium recessed zone tray (a place that holds meetings). Tap to dive in; a meeting can be dropped on it.
struct DioZoneTray: View {
    let name: String, tint: Color
    let members: [DioObj]; let subZones: Int; let size: CGSize
    let landed: Bool; let index: Int; let dimmed: Bool; let hot: Bool   // hot = a meeting is hovering over it
    let onDive: () -> Void
    @State private var press = false
    var body: some View {
        let w = size.width, h = size.height
        ZStack {
            RoundedRectangle(cornerRadius: 26, style: .continuous).fill(tint.opacity(hot ? 0.4 : 0.20))
                .blur(radius: 26).frame(width: w * 0.96, height: h * 0.9)
            ZStack {
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(LinearGradient(colors: [DioPal.trayTop, DioPal.trayBot], startPoint: .top, endPoint: .bottom))
                RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.05), lineWidth: 1)
                RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(tint.opacity(hot ? 1 : 0.5), lineWidth: hot ? 2.5 : 1.5)
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .stroke(.black.opacity(0.55), lineWidth: 7).blur(radius: 6).offset(y: 4)
                    .mask(RoundedRectangle(cornerRadius: 24, style: .continuous))
            }
            .shadow(color: .black.opacity(0.55), radius: 18, y: 14)
            VStack(spacing: 0) {
                HStack(spacing: 7) {
                    Circle().fill(tint).frame(width: 9, height: 9).shadow(color: tint, radius: 4)
                    Text(name).font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                    Spacer(minLength: 0)
                    Text("\(members.count)").font(.system(size: 12, weight: .black, design: .rounded)).foregroundStyle(tint)
                        .padding(.horizontal, 7).padding(.vertical, 2).background(Capsule().fill(tint.opacity(0.16)))
                }
                .padding(.horizontal, 14).padding(.top, 12)
                Spacer(minLength: 0)
                if members.isEmpty && subZones == 0 {
                    Text(hot ? "drop to file here" : "empty · drag a meeting in")
                        .font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(tint.opacity(0.8))
                } else {
                    HStack(spacing: 8) {
                        ForEach(Array(members.prefix(3).enumerated()), id: \.offset) { _, m in
                            DioTrayMote(sprite: m.sprite)
                        }
                        if subZones > 0 {
                            ZStack {
                                RoundedRectangle(cornerRadius: 10).fill(.white.opacity(0.06)).frame(width: 46, height: 46)
                                    .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(tint.opacity(0.4), lineWidth: 1))
                                VStack(spacing: 1) {
                                    Image(systemName: "square.stack.3d.up.fill").font(.system(size: 16)).foregroundStyle(tint)
                                    Text("+\(subZones)").font(.system(size: 8, weight: .black, design: .rounded)).foregroundStyle(tint)
                                }
                            }
                        }
                    }
                }
                Spacer(minLength: 0)
                HStack(spacing: 5) {
                    Image(systemName: "arrow.down.forward.and.arrow.up.backward").font(.system(size: 9, weight: .black))
                    Text("DIVE IN").font(.system(size: 10, weight: .heavy, design: .rounded)).tracking(1.6)
                }
                .foregroundStyle(tint.opacity(0.92)).padding(.bottom, 11)
            }
            .frame(width: w, height: h)
        }
        .frame(width: w, height: h)
        .scaleEffect(hot ? 1.04 : (press ? 0.95 : (landed ? 1 : 0.3)))
        .opacity(landed ? (dimmed ? 0 : 1) : 0)
        .animation(.spring(response: 0.7, dampingFraction: 0.6).delay(Double(index) * 0.08), value: landed)
        .animation(.spring(response: 0.4, dampingFraction: 0.6), value: press)
        .animation(.spring(response: 0.35, dampingFraction: 0.6), value: hot)
        .allowsHitTesting(!dimmed)
        .contentShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .onTapGesture {
            press = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { press = false; onDive() }
        }
    }
}

struct DioTrayMote: View {
    let sprite: String
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let bob = CGFloat(sin(t * 1.3 + Double(sprite.count)) * 3)
            ZStack {
                Ellipse().fill(.black.opacity(0.45)).frame(width: 34, height: 8).blur(radius: 4).offset(y: 22)
                DeskSprite(name: sprite, size: 46).offset(y: -bob).shadow(color: .black.opacity(0.5), radius: 5, y: 4)
            }
            .frame(width: 52, height: 60)
        }
    }
}

// The invitation to make a place.
struct DioCreateTile: View {
    let size: CGSize; let landed: Bool; let index: Int; let dimmed: Bool
    let onTap: () -> Void
    var body: some View {
        let w = size.width, h = size.height
        VStack(spacing: 8) {
            Image(systemName: "plus").font(.system(size: 22, weight: .black)).foregroundStyle(DioPal.muted)
            Text("New Zone").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
        }
        .frame(width: w, height: h)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [7, 6]))
                .foregroundStyle(DioPal.muted.opacity(0.4))
        )
        .opacity(landed ? (dimmed ? 0 : 0.9) : 0)
        .scaleEffect(landed ? 1 : 0.3)
        .animation(.spring(response: 0.7, dampingFraction: 0.6).delay(Double(index) * 0.08), value: landed)
        .allowsHitTesting(!dimmed)
        .contentShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .onTapGesture(perform: onTap)
    }
}

struct DioBreadcrumb: View {
    let crumbs: [(String, Color)]
    let onJump: (Int) -> Void
    var body: some View {
        HStack(spacing: 6) {
            ForEach(Array(crumbs.enumerated()), id: \.offset) { i, c in
                if i > 0 { Image(systemName: "chevron.right").font(.system(size: 10, weight: .black)).foregroundStyle(DioPal.muted) }
                let last = i == crumbs.count - 1
                Button { if !last { onJump(i) } } label: {
                    HStack(spacing: 5) {
                        if i == 0 { Image(systemName: "house.fill").font(.system(size: 10, weight: .bold)) }
                        else { Circle().fill(c.1).frame(width: 7, height: 7) }
                        Text(c.0).font(.system(size: 12.5, weight: .heavy, design: .rounded))
                    }
                    .foregroundStyle(last ? DioPal.text : DioPal.muted)
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(Capsule().fill(.white.opacity(last ? 0.10 : 0.04))
                        .overlay(Capsule().strokeBorder((last ? c.1 : .clear).opacity(0.5), lineWidth: 1)))
                }.buttonStyle(.plain).disabled(last)
            }
        }
    }
}

struct DioInfoCard: View {
    let icon: String, title: String, line: String, tint: Color; var chevron = false
    let onTap: () -> Void
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 11) {
                Image(systemName: icon).font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                    .frame(width: 34, height: 34).background(Circle().fill(tint))
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(line).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                }
                Spacer(minLength: 0)
                if chevron { Image(systemName: "chevron.right").font(.system(size: 12, weight: .bold)).foregroundStyle(DioPal.muted) }
            }
            .padding(.horizontal, 13).padding(.vertical, 11).frame(width: 300)
            .background(
                RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.white.opacity(0.06))
                    .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.black.opacity(0.3)))
                    .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(tint.opacity(0.35), lineWidth: 1))
                    .shadow(color: .black.opacity(0.5), radius: 16, y: 10)
            )
        }.buttonStyle(.plain)
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
                Ellipse().fill(.black.opacity(0.5)).frame(width: 66, height: 15).blur(radius: 9)
                    .offset(y: 50).opacity(landed ? (hop > 1 ? 0.4 : 1) : 0)
                DeskSprite(name: "qlippy", size: 104)
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
            .scaleEffect(1 + CGFloat(sin(t * 2) * 0.02))
            .frame(width: 96, height: 96).contentShape(Circle())
        }
        .onTapGesture(perform: onTap)
    }
}

struct DioStage: View {
    @StateObject private var model = CaptureModel()
    @AppStorage("hs.diorama.pos") private var posCSV = ""           // free-placed object positions
    @AppStorage("hs.diorama.zones") private var zonesCSV = ""       // "path|colorIdx;..." (path-based, recursive)
    @AppStorage("hs.diorama.filed") private var dfiledCSV = ""      // "objId=zonePath;..." (meetings → a zone)
    @AppStorage("hs.desk.kbs") private var kbsCSV = ""
    @AppStorage("hs.desk.filed") private var kbFiledCSV = ""
    @State private var landed = false
    @State private var path: [String] = []
    @State private var diveDir = 1
    @State private var flash = 0.0
    @State private var selected: String? = nil
    @State private var cardsIn = false
    @State private var capturing = false
    @State private var openMeeting: Meeting? = nil
    @State private var positions: [String: CGPoint] = [:]
    @State private var zones: [(path: String, color: Int)] = []
    @State private var filed: [String: String] = [:]
    @State private var dragHotZone: String? = nil                  // tray currently under a dragged meeting
    @State private var namingZone = false
    @State private var newZoneName = ""
    private let spring = Animation.spring(response: 0.55, dampingFraction: 0.62)
    private let diveSpring = Animation.spring(response: 0.6, dampingFraction: 0.74)

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

    // MARK: real data
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
        DioObj(id: "m:\(m.id)", kind: .meeting, sprite: i % 2 == 0 ? "cassette" : "cassette2", base: 134, glow: DioPal.accent, title: meetingTitle(m))
    }
    // members of the CURRENT level: meetings filed here (root also shows unfiled); models + KBs only at root
    private func members() -> [DioObj] {
        var out: [DioObj] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == pathKey { out.append(obj(for: m, i)) }
        if path.isEmpty {
            for mdl in ModelFiles.installed().prefix(2) {
                out.append(DioObj(id: "model:\(mdl.id)", kind: .model, sprite: "cartridge", base: 168, glow: DioPal.cobalt,
                                  title: mdl.name.replacingOccurrences(of: ".gguf", with: "")))
            }
            for kb in knowledgeBases.prefix(3) {
                out.append(DioObj(id: "kb:\(kb)", kind: .kb, sprite: "crystal", base: 122, glow: DioPal.violet, title: kb))
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

    private func cards(for o: DioObj) -> [(String, String, String, Color, Bool)] {
        switch o.kind {
        case .meeting:
            guard let m = meeting(forObj: o.id) else { return [] }
            var c: [(String, String, String, Color, Bool)] = []
            if let s = m.intel?.summary, !s.isEmpty { c.append(("sparkles", "Summary", String(s.prefix(60)), DioPal.accent, true)) }
            let acts = m.intel?.actionItems ?? []
            if !acts.isEmpty { c.append(("checkmark.circle.fill", "\(acts.count) Action\(acts.count == 1 ? "" : "s")", acts.first?.task ?? "", DioPal.mint, true)) }
            let spk = Set(m.segments.map(\.speaker)).count
            c.append(("text.alignleft", "Transcript", "\(m.segments.count) lines · \(spk) speaker\(spk == 1 ? "" : "s")", DioPal.cobalt, true))
            if c.count == 1 { c.insert(("doc.text", "Open meeting", "see everything", DioPal.accent, true), at: 0) }
            return c
        case .model:
            return [("cpu.fill", o.title, "on device · ready", DioPal.cobalt, false),
                    ("checkmark.seal.fill", "Private", "nothing leaves this iPad", DioPal.mint, false)]
        case .kb:
            let n = kbCount(o.title)
            return [("doc.on.doc.fill", "\(n) item\(n == 1 ? "" : "s")", "filed here", DioPal.violet, false),
                    ("magnifyingglass", "Ask the KB", "grounded answers", DioPal.violet, false)]
        }
    }

    private func mode(_ id: String) -> DioMode { selected == nil ? .home : (selected == id ? .focus : .recede) }

    // MARK: layout
    private func zoneSize(_ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGSize {
        let width = n <= 1 ? w * 0.58 : w * 0.43
        return CGSize(width: width, height: width * 0.66)
    }
    private func zonePos(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let x = n == 1 ? 0.5 : 0.27 + 0.46 * Double(i) / Double(max(1, n - 1))
        return CGPoint(x: w * x, y: h * 0.34)
    }
    private func looseHome(_ i: Int, _ n: Int, _ hasZones: Bool, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let cols = max(1, min(4, n))
        let r = i / cols, c = i % cols
        let rows = max(1, Int(ceil(Double(n) / Double(cols))))
        let y0 = hasZones ? 0.62 : 0.42
        let x = cols == 1 ? 0.5 : 0.18 + 0.64 * Double(c) / Double(cols - 1)
        let y = rows == 1 ? y0 : y0 + 0.18 * Double(r) / Double(rows - 1)
        return CGPoint(x: w * x, y: h * y)
    }
    private func pos(_ id: String, _ fallback: CGPoint, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        if selected == id { return CGPoint(x: w * 0.5, y: h * 0.24) }
        if let u = positions[id] { return CGPoint(x: w * u.x, y: h * u.y) }
        return fallback
    }

    private var diveTransition: AnyTransition {
        diveDir >= 0
            ? .asymmetric(insertion: .scale(scale: 0.55).combined(with: .opacity), removal: .scale(scale: 1.7).combined(with: .opacity))
            : .asymmetric(insertion: .scale(scale: 1.7).combined(with: .opacity), removal: .scale(scale: 0.55).combined(with: .opacity))
    }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack {
                LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .top, endPoint: .bottom)
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    RadialGradient(colors: [(selected == nil ? curTint : DioPal.cobalt).opacity(0.18 + 0.05 * sin(t * 1.2)), .clear],
                                   center: .init(x: 0.5, y: selected == nil ? 0.4 : 0.26), startRadius: 20, endRadius: w * 0.95)
                        .blendMode(.plusLighter).animation(diveSpring, value: pathKey)
                }
                DioMotes()
                Color.clear.contentShape(Rectangle()).onTapGesture {
                    if selected != nil { select(nil) } else if !path.isEmpty { climbOut() }
                }

                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 26, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(members().isEmpty && childZones().isEmpty ? "tap record to capture your first meeting" : "drag a meeting onto a zone · tap to open")
                        .font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                }
                .opacity(landed && selected == nil && path.isEmpty ? 1 : 0).offset(y: landed ? 0 : -14)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.055)

                if !path.isEmpty {
                    DioBreadcrumb(crumbs: crumbs(), onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.05).opacity(selected == nil ? 1 : 0)
                }

                ForEach([pathKey], id: \.self) { _ in level(w, h) }
                    .transition(diveTransition)

                DioCompanion(landed: landed, excited: selected != nil).position(x: w * 0.87, y: h * 0.88)
                if landed && selected == nil {
                    DioRecordOrb { capturing = true }.position(x: w * 0.5, y: h * 0.91).transition(.scale.combined(with: .opacity))
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.55)], center: .center, startRadius: 140, endRadius: 760)
                    .blendMode(.multiply).allowsHitTesting(false)
                RadialGradient(colors: [curTint.opacity(flash), .clear], center: .center, startRadius: 10, endRadius: w)
                    .blendMode(.plusLighter).allowsHitTesting(false)
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
        let zs = childZones(); let ms = members(); let slotN = zs.count + 1; let hasZones = !zs.isEmpty
        ZStack {
            ForEach(Array(zs.enumerated()), id: \.element.path) { i, z in
                DioZoneTray(name: name(of: z.path), tint: DioPal.zoneTints[z.color % DioPal.zoneTints.count],
                            members: membersOf(z.path), subZones: zones.filter { parent(of: $0.path) == z.path }.count,
                            size: zoneSize(slotN, w, h), landed: landed, index: i, dimmed: selected != nil,
                            hot: dragHotZone == z.path, onDive: { dive(into: z.path) })
                    .position(zonePos(i, slotN, w, h))
            }
            DioCreateTile(size: zoneSize(slotN, w, h), landed: landed, index: zs.count, dimmed: selected != nil) {
                haptic(.light); namingZone = true
            }
            .position(zonePos(zs.count, slotN, w, h))

            ForEach(Array(ms.enumerated()), id: \.element.id) { i, o in
                DioHero(obj: o, landed: landed, mode: mode(o.id), index: i, pos: pos(o.id, looseHome(i, ms.count, hasZones, w, h), w, h),
                        onTap: { select(selected == o.id ? nil : o.id) },
                        onDrop: { tr in drop(o, looseHome(i, ms.count, hasZones, w, h), tr, w, h) },
                        onDragChange: { p in updateHot(o, p, zs, slotN, w, h) })
                    .zIndex(selected == o.id ? 10 : 0)
            }

            if let sel = selected, let o = ms.first(where: { $0.id == sel }) {
                VStack(spacing: 11) {
                    ForEach(Array(cards(for: o).enumerated()), id: \.offset) { i, c in
                        DioInfoCard(icon: c.0, title: c.1, line: c.2, tint: c.3, chevron: c.4) {
                            if c.4, let m = meeting(forObj: o.id) { openMeeting = m }
                        }
                        .scaleEffect(cardsIn ? 1 : 0.4).opacity(cardsIn ? 1 : 0).offset(y: cardsIn ? 0 : 40)
                        .animation(.spring(response: 0.5, dampingFraction: 0.6).delay(0.08 + Double(i) * 0.07), value: cardsIn)
                    }
                }
                .position(x: w * 0.5, y: h * 0.62)
            }
        }
    }

    private func crumbs() -> [(String, Color)] {
        var out: [(String, Color)] = [("Desk", DioPal.accent)]
        var acc: [String] = []
        for comp in path { acc.append(comp); let id = acc.joined(separator: "/"); out.append((comp, tintFor(id))) }
        return out
    }

    // MARK: interactions
    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
    private func whoosh() { flash = 0.5; withAnimation(.easeOut(duration: 0.6)) { flash = 0 } }
    private func dive(into zpath: String) {
        haptic(.heavy); whoosh(); diveDir = 1
        withAnimation(diveSpring) { selected = nil; cardsIn = false; path = zpath.split(separator: "/").map(String.init) }
    }
    private func climbOut() {
        guard !path.isEmpty else { return }
        haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; cardsIn = false; path.removeLast() }
    }
    private func jump(to crumbIndex: Int) {
        haptic(.medium); whoosh(); diveDir = -1
        withAnimation(diveSpring) { selected = nil; cardsIn = false; path = Array(path.prefix(crumbIndex)) }
    }
    private func select(_ id: String?) {
        haptic(id == nil ? .light : .medium)
        withAnimation(spring) { selected = id }
        cardsIn = false
        if id != nil { withAnimation { cardsIn = true } }
    }
    private func createZone(_ raw: String) {
        let nm = raw.replacingOccurrences(of: "/", with: " ").trimmingCharacters(in: .whitespaces)
        guard !nm.isEmpty else { return }
        let zpath = path.isEmpty ? nm : pathKey + "/" + nm
        guard !zones.contains(where: { $0.path == zpath }) else { return }
        haptic(.medium)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) { zones.append((zpath, zones.count)) }
        persistZones()
    }
    // a dragged meeting hovering over a tray → highlight it
    private func updateHot(_ o: DioObj, _ p: CGPoint?, _ zs: [(path: String, color: Int)], _ slotN: Int, _ w: CGFloat, _ h: CGFloat) {
        guard o.kind == .meeting, let p = p else { if dragHotZone != nil { dragHotZone = nil }; return }
        dragHotZone = trayHit(p, zs, slotN, w, h)
    }
    private func trayHit(_ p: CGPoint, _ zs: [(path: String, color: Int)], _ slotN: Int, _ w: CGFloat, _ h: CGFloat) -> String? {
        let size = zoneSize(slotN, w, h)
        for (i, z) in zs.enumerated() {
            let c = zonePos(i, slotN, w, h)
            let rect = CGRect(x: c.x - size.width / 2, y: c.y - size.height / 2, width: size.width, height: size.height)
            if rect.contains(p) { return z.path }
        }
        return nil
    }
    private func drop(_ o: DioObj, _ fallback: CGPoint, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        let start = pos(o.id, fallback, w, h)
        let end = CGPoint(x: start.x + tr.width, y: start.y + tr.height)
        let zs = childZones(); let slotN = zs.count + 1
        if o.kind == .meeting, let z = trayHit(end, zs, slotN, w, h) {
            file(o.id, into: z)
        } else {
            haptic(.light)
            let u = positions[o.id] ?? CGPoint(x: start.x / w, y: start.y / h)
            positions[o.id] = CGPoint(x: min(0.92, max(0.08, u.x + tr.width / w)), y: min(0.84, max(0.16, u.y + tr.height / h)))
            persistPositions()
        }
        dragHotZone = nil
    }
    private func file(_ id: String, into zpath: String) {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(spring) { filed[id] = zpath; positions[id] = nil }
        persistFiled(); persistPositions()
    }

    // MARK: persistence
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
