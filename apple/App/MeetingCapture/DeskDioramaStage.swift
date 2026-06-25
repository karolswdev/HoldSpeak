import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — THE DESK as a premium 2.5D, motion-first DIORAMA, wired to the REAL app (the engine, not a demo).
// Your real meetings are living cassettes, installed models are AI-core cartridges, knowledge bases are
// crystals. DRAG to arrange (persisted), TAP to open each object's own real intelligence, the record orb
// runs the real capture loop → a new meeting springs onto the desk. Reuses CaptureModel / CaptureView /
// MeetingDetailView / ModelFiles + DeskSprite + the app's Color(hex:). 3D desk behind HS_REAL_DESK=1.

enum DioPal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let accent = Color(hex: 0xFF6B35), cobalt = Color(hex: 0x5B8DEF), violet = Color(hex: 0x9B6BFF)
    static let mint = Color(hex: 0x3ECF8E), text = Color(hex: 0xF4ECE0), muted = Color(hex: 0x9C93A8)
}

enum DioKind { case meeting, model, kb }
struct DioObj: Identifiable { let id: String; let kind: DioKind; let sprite: String; let base: CGFloat; let glow: Color; let title: String; let home: CGPoint }
enum DioMode { case home, focus, recede }

// A hero object. CRITICAL: the drag/tap gesture lives on the STABLE outer view, NOT inside the per-frame
// idle TimelineView (which rebuilds ~60x/s and was tearing down the in-progress drag — the "can't drag" bug).
struct DioHero: View {
    let obj: DioObj; let landed: Bool; let mode: DioMode; let index: Int; let pos: CGPoint
    let onTap: () -> Void; let onMoved: (CGSize) -> Void
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
        .scaleEffect(landed ? modeScale : 0.15)
        .opacity(landed ? dim : 0)
        .offset(y: landed ? 0 : -240)
        .contentShape(Rectangle())
        .animation(.spring(response: 0.72, dampingFraction: 0.54).delay(Double(index) * 0.10), value: landed)
        .animation(spring, value: mode)
        .position(x: pos.x + drag.width, y: pos.y + drag.height)
        .animation(spring, value: mode)
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { if mode != .recede { drag = $0.translation } }
                .onEnded { v in
                    let d = hypot(v.translation.width, v.translation.height)
                    if d < 9 { onTap() } else if mode != .recede { onMoved(v.translation) }
                    drag = .zero
                }
        )
    }
}

// Purely visual idle — the per-frame breathe/drift/tilt/glow. No gestures live here.
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
    @AppStorage("hs.diorama.pos") private var posCSV = ""        // drag positions: "id=x,y;..." (persisted)
    @AppStorage("hs.desk.kbs") private var kbsCSV = ""
    @AppStorage("hs.desk.filed") private var filedCSV = ""
    @State private var landed = false
    @State private var selected: String? = nil
    @State private var cardsIn = false
    @State private var capturing = false
    @State private var openMeeting: Meeting? = nil
    @State private var positions: [String: CGPoint] = [:]
    private let spring = Animation.spring(response: 0.55, dampingFraction: 0.62)

    // MARK: real data → objects
    private var meetings: [Meeting] {
        model.meetings.sorted { $0.startedAt > $1.startedAt }
    }
    private var knowledgeBases: [String] { kbsCSV.split(separator: ";").map(String.init).filter { !$0.isEmpty } }
    private func kbCount(_ name: String) -> Int {
        filedCSV.split(separator: ";").compactMap { p -> String? in let kv = p.split(separator: "=", maxSplits: 1); return kv.count == 2 ? String(kv[1]) : nil }.filter { $0 == name }.count
    }
    private var objects: [DioObj] {
        var out: [DioObj] = []
        for (i, m) in meetings.prefix(6).enumerated() {
            out.append(DioObj(id: "m:\(m.id)", kind: .meeting, sprite: i % 2 == 0 ? "cassette" : "cassette2",
                              base: 138, glow: DioPal.accent, title: meetingTitle(m), home: .zero))
        }
        for mdl in ModelFiles.installed().prefix(2) {
            out.append(DioObj(id: "model:\(mdl.id)", kind: .model, sprite: "cartridge", base: 174, glow: DioPal.cobalt,
                              title: mdl.name.replacingOccurrences(of: ".gguf", with: ""), home: .zero))
        }
        for kb in knowledgeBases.prefix(3) {
            out.append(DioObj(id: "kb:\(kb)", kind: .kb, sprite: "crystal", base: 132, glow: DioPal.violet, title: kb, home: .zero))
        }
        return out
    }
    private func meetingTitle(_ m: Meeting) -> String {
        if let t = m.title, !t.isEmpty { return t }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"; return f.string(from: m.startedAt)
    }
    private func meeting(forObj id: String) -> Meeting? {
        guard id.hasPrefix("m:") else { return nil }
        let mid = String(id.dropFirst(2)); return model.meetings.first { $0.id == mid }
    }

    // each object opens its OWN real intelligence
    private func cards(for obj: DioObj) -> [(String, String, String, Color, Bool)] {
        switch obj.kind {
        case .meeting:
            guard let m = meeting(forObj: obj.id) else { return [] }
            var c: [(String, String, String, Color, Bool)] = []
            if let s = m.intel?.summary, !s.isEmpty { c.append(("sparkles", "Summary", String(s.prefix(60)), DioPal.accent, true)) }
            let acts = m.intel?.actionItems ?? []
            if !acts.isEmpty { c.append(("checkmark.circle.fill", "\(acts.count) Action\(acts.count == 1 ? "" : "s")", acts.first?.task ?? "", DioPal.mint, true)) }
            let spk = Set(m.segments.map(\.speaker)).count
            c.append(("text.alignleft", "Transcript", "\(m.segments.count) lines · \(spk) speaker\(spk == 1 ? "" : "s")", DioPal.cobalt, true))
            if c.count == 1 { c.insert(("doc.text", "Open meeting", "see everything", DioPal.accent, true), at: 0) }
            return c
        case .model:
            return [("cpu.fill", obj.title, "on device · ready", DioPal.cobalt, false),
                    ("checkmark.seal.fill", "Private", "nothing leaves this iPad", DioPal.mint, false)]
        case .kb:
            let n = kbCount(obj.title)
            return [("doc.on.doc.fill", "\(n) item\(n == 1 ? "" : "s")", "filed here", DioPal.violet, false),
                    ("magnifyingglass", "Ask the KB", "grounded answers", DioPal.violet, false)]
        }
    }

    private func mode(_ id: String) -> DioMode { selected == nil ? .home : (selected == id ? .focus : .recede) }
    private func home(_ i: Int, _ n: Int) -> CGPoint {
        let cols = max(1, min(4, n))
        let rows = max(1, Int(ceil(Double(n) / Double(cols))))
        let r = i / cols, c = i % cols
        let x = cols == 1 ? 0.5 : 0.18 + 0.64 * Double(c) / Double(cols - 1)
        let y = rows == 1 ? 0.40 : 0.28 + 0.40 * Double(r) / Double(rows - 1)
        let jx = Double((abs(("x" + String(i)).hashValue) % 7) - 3) * 0.006
        return CGPoint(x: x + jx, y: y)
    }
    private func unit(_ id: String, _ fallback: CGPoint) -> CGPoint { positions[id] ?? fallback }
    private func pos(_ id: String, _ fallback: CGPoint, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        if selected == id { return CGPoint(x: w * 0.5, y: h * 0.26) }
        let u = unit(id, fallback); return CGPoint(x: w * u.x, y: h * u.y)
    }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            let objs = objects
            ZStack {
                LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .top, endPoint: .bottom)
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    RadialGradient(colors: [(selected == nil ? DioPal.accent : DioPal.cobalt).opacity(0.18 + 0.05 * sin(t * 1.2)), .clear],
                                   center: .init(x: 0.5, y: selected == nil ? 0.42 : 0.26), startRadius: 20, endRadius: w * 0.95)
                        .blendMode(.plusLighter).animation(spring, value: selected)
                }
                DioMotes()
                Color.clear.contentShape(Rectangle()).onTapGesture { if selected != nil { select(nil) } }

                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 26, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(objs.isEmpty ? "tap record to capture your first meeting" : "drag to arrange · tap to open")
                        .font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                }
                .opacity(landed && selected == nil ? 1 : 0).offset(y: landed ? 0 : -14)
                .animation(.easeOut(duration: 0.5), value: selected)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.09)

                if let sel = selected, let o = objs.first(where: { $0.id == sel }) {
                    VStack(spacing: 11) {
                        ForEach(Array(cards(for: o).enumerated()), id: \.offset) { i, c in
                            DioInfoCard(icon: c.0, title: c.1, line: c.2, tint: c.3, chevron: c.4) {
                                if c.4, let m = meeting(forObj: o.id) { openMeeting = m }
                            }
                            .scaleEffect(cardsIn ? 1 : 0.4).opacity(cardsIn ? 1 : 0).offset(y: cardsIn ? 0 : 40)
                            .animation(.spring(response: 0.5, dampingFraction: 0.6).delay(0.08 + Double(i) * 0.07), value: cardsIn)
                        }
                    }
                    .position(x: w * 0.5, y: h * 0.65)
                }

                ForEach(Array(objs.enumerated()), id: \.element.id) { i, o in
                    DioHero(obj: o, landed: landed, mode: mode(o.id), index: i, pos: pos(o.id, home(i, objs.count), w, h),
                            onTap: { select(selected == o.id ? nil : o.id) },
                            onMoved: { tr in move(o.id, home(i, objs.count), tr, w, h) })
                        .zIndex(selected == o.id ? 10 : 0)
                }

                DioCompanion(landed: landed, excited: selected != nil).position(x: w * 0.87, y: h * 0.88)
                if landed && selected == nil {
                    DioRecordOrb { capturing = true }.position(x: w * 0.5, y: h * 0.91).transition(.scale.combined(with: .opacity))
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.55)], center: .center, startRadius: 140, endRadius: 760)
                    .blendMode(.multiply).allowsHitTesting(false)
            }
            .ignoresSafeArea()
            .onAppear { landed = true; loadPositions(); model.refresh() }
            .fullScreenCover(isPresented: $capturing) {
                CaptureView(model: model, done: { capturing = false; model.refresh() })
            }
            .sheet(isPresented: Binding(get: { openMeeting != nil }, set: { if !$0 { openMeeting = nil } })) {
                if let m = openMeeting { NavigationStack { MeetingDetailView(meeting: m) }.preferredColorScheme(.dark) }
            }
        }
        .preferredColorScheme(.dark)
    }

    private func haptic(_ s: UIImpactFeedbackGenerator.FeedbackStyle) {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: s).impactOccurred()
        #endif
    }
    private func select(_ id: String?) {
        haptic(id == nil ? .light : .medium)
        withAnimation(spring) { selected = id }
        cardsIn = false
        if id != nil { withAnimation { cardsIn = true } }
    }
    private func move(_ id: String, _ fallback: CGPoint, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        haptic(.light)
        let u = unit(id, fallback)
        positions[id] = CGPoint(x: min(0.92, max(0.08, u.x + tr.width / w)), y: min(0.84, max(0.16, u.y + tr.height / h)))
        persist()
    }
    private func persist() {
        posCSV = positions.map { "\($0.key)=\($0.value.x),\($0.value.y)" }.joined(separator: ";")
    }
    private func loadPositions() {
        var d: [String: CGPoint] = [:]
        for row in posCSV.split(separator: ";") {
            let kv = row.split(separator: "="); guard kv.count == 2 else { continue }
            let xy = kv[1].split(separator: ","); guard xy.count == 2, let x = Double(xy[0]), let y = Double(xy[1]) else { continue }
            d[String(kv[0])] = CGPoint(x: x, y: y)
        }
        positions = d
    }
}
