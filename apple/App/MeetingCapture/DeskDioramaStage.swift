import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — THE FRACTAL DESK, now PRIMITIVE-DRIVEN (story-25). Every object on the desk is a `DeskPrimitive`
// (see DeskPrimitive.swift); the canvas object, the card, and the right-edge intelligence PULL-OUT are all
// DERIVED from the contract — one renderer, no per-type screens. Zones are a low-profile top shelf; tap an
// object → its `sections` pull out from the right; tap a tray → DIVE (recursive); a big always-on-top Back
// bar + a focus fog. Drag a meeting onto a tray to file it. Reuses CaptureModel / CaptureView /
// MeetingDetailView / ModelFiles + DeskSprite. 3D desk behind HS_REAL_DESK=1.

enum DioPal {
    static let bgTop = Color(hex: 0x0B0D12), bgMid = Color(hex: 0x16111F), bgBot = Color(hex: 0x090A0E)
    static let trayTop = Color(hex: 0x1B1626), trayBot = Color(hex: 0x0C0A12)
    static let accent = Color(hex: 0xFF6B35), cobalt = Color(hex: 0x5B8DEF), violet = Color(hex: 0x9B6BFF)
    static let mint = Color(hex: 0x3ECF8E), text = Color(hex: 0xF4ECE0), muted = Color(hex: 0x9C93A8)
    static let zoneTints: [Color] = [accent, cobalt, violet, mint]
}

enum DioMode { case home, focus, recede }

// THE FIRST BOOT — an empty desk is not a void; it is a desk that teaches itself. A calm guided
// spine orients you to the spatial model (objects · the AI core · zones) and points to the one
// action that begins everything: record. Felt in motion — a breathing core, a staggered spine.
struct DioFirstBootStep: Identifiable { let id: Int; let glyph: String; let tint: Color; let title: String; let line: String }

// An empty zone you dived into. You file meetings INTO a zone from the desk (drag onto its tray), so the
// honest guidance from inside is: file from your desk, or nest a sub-zone here. Never a blank dead-end.
struct DioZoneEmpty: View {
    let name: String; let tint: Color; let onNewSubzone: () -> Void
    @State private var shown = false
    var body: some View {
        TimelineView(.animation) { tl in
            let breathe = 1 + CGFloat(sin(tl.date.timeIntervalSinceReferenceDate * 1.1) * 0.02)
            VStack(spacing: 16) {
                ZStack {
                    ForEach(0..<2) { i in
                        RoundedRectangle(cornerRadius: 22, style: .continuous)
                            .strokeBorder(tint.opacity(0.22 - Double(i) * 0.08), style: StrokeStyle(lineWidth: 1.5, dash: [5, 6]))
                            .frame(width: 92 + CGFloat(i) * 26, height: 92 + CGFloat(i) * 26).scaleEffect(breathe)
                    }
                    Image(systemName: "tray").font(.system(size: 34, weight: .regular)).foregroundStyle(tint.opacity(0.9))
                }
                .frame(height: 130)
                VStack(spacing: 7) {
                    Text("\(name) is empty").font(.system(size: 20, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("Drag a meeting onto this zone from your desk to file it here.")
                        .font(.system(size: 13, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                        .multilineTextAlignment(.center).frame(maxWidth: 300)
                }
                Button(action: onNewSubzone) {
                    HStack(spacing: 7) { Image(systemName: "plus.circle.fill").font(.system(size: 14, weight: .bold)); Text("New sub-zone here").font(.system(size: 13.5, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(.white).padding(.horizontal, 18).frame(height: 46)
                        .background(Capsule().fill(LinearGradient(colors: [tint.opacity(0.95), tint.opacity(0.7)], startPoint: .top, endPoint: .bottom)))
                }.buttonStyle(.plain)
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.left").font(.system(size: 11, weight: .bold))
                    Text("tap the breadcrumb to climb back out").font(.system(size: 11.5, weight: .semibold, design: .rounded))
                }.foregroundStyle(DioPal.muted.opacity(0.8))
            }
            .opacity(shown ? 1 : 0).scaleEffect(shown ? 1 : 0.96)
            .animation(.spring(response: 0.5, dampingFraction: 0.8), value: shown)
        }
        .onAppear { shown = true }
    }
}

struct DioFirstBoot: View {
    let w: CGFloat; let h: CGFloat
    @State private var shown = false
    private let steps: [DioFirstBootStep] = [
        DioFirstBootStep(id: 0, glyph: "rectangle.stack.fill", tint: DioPal.accent, title: "Meetings become objects", line: "Capture one and it lands right here."),
        DioFirstBootStep(id: 1, glyph: "cpu",                  tint: DioPal.cobalt, title: "Your AI core waits below", line: "Drop an object on it to ask."),
        DioFirstBootStep(id: 2, glyph: "square.dashed",        tint: DioPal.violet, title: "Zones file your work", line: "Drag a meeting into a place to keep it."),
    ]

    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let breathe = 1 + CGFloat(sin(t * 1.1) * 0.022)
            VStack(spacing: 0) {
                Text("HoldSpeak").font(.system(size: 22, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    .padding(.bottom, 18)
                // the hero core — a quiet, ready pulse
                ZStack {
                    ForEach(0..<3) { i in
                        Circle().strokeBorder(DioPal.accent.opacity(0.20 - Double(i) * 0.055), lineWidth: 1.4)
                            .frame(width: 78 + CGFloat(i) * 30, height: 78 + CGFloat(i) * 30).scaleEffect(breathe)
                    }
                    Circle().fill(RadialGradient(colors: [DioPal.accent.opacity(0.9), DioPal.accent.opacity(0.18)], center: .center, startRadius: 1, endRadius: 40))
                        .frame(width: 58, height: 58)
                    Circle().fill(.white.opacity(0.92)).frame(width: 13, height: 13).shadow(color: DioPal.accent, radius: 9)
                }
                .frame(height: 140)
                VStack(spacing: 6) {
                    Text("Your desk is ready").font(.system(size: 21, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("An empty desk, waiting for your first meeting.").font(.system(size: 13, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                }
                .padding(.bottom, 26)
                // the guided spine
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(steps) { s in
                        HStack(alignment: .top, spacing: 14) {
                            VStack(spacing: 0) {
                                ZStack {
                                    RoundedRectangle(cornerRadius: 13, style: .continuous)
                                        .fill(LinearGradient(colors: [s.tint.opacity(0.34), Color(hex: 0x14121C)], startPoint: .top, endPoint: .bottom))
                                        .overlay(RoundedRectangle(cornerRadius: 13, style: .continuous).strokeBorder(s.tint.opacity(0.72), lineWidth: 1.3))
                                        .frame(width: 46, height: 46)
                                    Image(systemName: s.glyph).font(.system(size: 19, weight: .bold)).foregroundStyle(.white)
                                }
                                if s.id < steps.count - 1 {
                                    Rectangle().fill(LinearGradient(colors: [s.tint.opacity(0.55), steps[s.id + 1].tint.opacity(0.55)], startPoint: .top, endPoint: .bottom))
                                        .frame(width: 2, height: 24)
                                }
                            }
                            VStack(alignment: .leading, spacing: 3) {
                                Text(s.title).font(.system(size: 15.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                                Text(s.line).font(.system(size: 12.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.muted)
                            }.padding(.top, 4)
                            Spacer(minLength: 0)
                        }
                        .opacity(shown ? 1 : 0).offset(y: shown ? 0 : 14)
                        .animation(.spring(response: 0.6, dampingFraction: 0.78).delay(0.15 + Double(s.id) * 0.12), value: shown)
                    }
                }
                .frame(maxWidth: 326, alignment: .leading)
            }
            .frame(maxWidth: .infinity)
        }
        .onAppear { shown = true }
    }
}

// A long-press menu entry — the discoverable twin of a drag-route/drag-send.
struct DioMenuItem: Identifiable { let id = UUID(); let label: String; let icon: String; let action: () -> Void }

// A zone is a resizable, free-placed AREA: a path (recursion), a colour, a unit-centre (cx,cy) and a size
// (w,h in points). Drag to arrange (tetris), corner-grip to resize. Persisted in hs.diorama.zones.
struct ZoneRec: Equatable { var path: String; var color: Int; var cx: Double; var cy: Double; var w: Double; var h: Double }

// MARK: - canvas object — derived ENTIRELY from a DeskPrimitive (glyph/colour/title/id). Gesture on the stable outer view.
struct DioHero: View {
    let prim: any DeskPrimitive; let landed: Bool; let mode: DioMode; let index: Int; let pos: CGPoint
    var hot: Bool = false                          // a compatible primitive is hovering over me → I'm a route target
    var picked: Bool = false                       // selected by the lasso (part of an Ask bundle)
    var onSummon: () -> Void = {}                   // long-press → radial summon (route/send)
    let onTap: () -> Void; let onDrop: (CGSize) -> Void; let onDragChange: (CGPoint?) -> Void
    @State private var drag: CGSize = .zero
    private var modeScale: CGFloat { hot ? 1.12 : (mode == .focus ? 1.34 : (mode == .recede ? 0.6 : 1)) }
    private var dim: Double { mode == .recede ? 0.3 : 1 }
    private let spring = Animation.spring(response: 0.5, dampingFraction: 0.72)
    var body: some View {
        let s = prim.base
        VStack(spacing: 7) {
            DioHeroVisual(glyph: prim.glyph, glow: prim.color, base: s, seed: prim.id, focused: mode == .focus, hot: hot, symbol: prim.isSymbol, picked: picked).frame(width: s, height: s)
            Text(prim.title).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.85))
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
                    if mode != .recede { if d < 9 { onTap() } else { onDrop(v.translation) } }
                    drag = .zero
                }
        )
        .simultaneousGesture(LongPressGesture(minimumDuration: 0.32).onEnded { _ in if mode != .recede { onSummon() } })
    }
}

struct DioHeroVisual: View {
    let glyph: String; let glow: Color; let base: CGFloat; let seed: String; let focused: Bool
    var hot: Bool = false; var symbol: Bool = false; var picked: Bool = false
    var body: some View {
        let s = base
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate, ph = Double(abs(seed.hashValue) % 7)
            let bob = CGFloat(sin(t * 0.9 + ph) * 6)
            let breathe = 1 + CGFloat(sin(t * 1.15 + ph) * 0.018)
            let tilt = sin(t * 0.65 + ph) * 2.0
            let pulse = 0.6 + 0.4 * sin(t * 1.7 + ph)
            let ring = 0.5 + 0.5 * sin(t * 5)
            ZStack {
                Ellipse().fill(.black.opacity(0.5)).frame(width: s * 0.6, height: s * 0.15)
                    .blur(radius: 11).offset(y: s * 0.45 + bob * 0.25)
                Circle().fill(RadialGradient(colors: [(hot ? DioPal.accent : glow).opacity(focused || hot ? 0.8 : 0.5), .clear], center: .center, startRadius: 2, endRadius: s * 0.8))
                    .frame(width: s * 1.8, height: s * 1.8).blur(radius: 12).opacity(hot ? 0.9 : pulse)
                if hot {
                    Circle().strokeBorder(DioPal.accent.opacity(0.7 + 0.3 * ring), lineWidth: 3)
                        .frame(width: s * (1.1 + 0.08 * ring), height: s * (1.1 + 0.08 * ring))
                }
                if picked {
                    Circle().fill(DioPal.accent.opacity(0.12)).frame(width: s * 1.05, height: s * 1.05)
                        .overlay(Circle().strokeBorder(DioPal.accent.opacity(0.9), lineWidth: 3))
                }
                Group {
                    if symbol {
                        ZStack {
                            RoundedRectangle(cornerRadius: s * 0.24, style: .continuous)
                                .fill(LinearGradient(colors: [glow.opacity(0.42), Color(hex: 0x12101A)], startPoint: .top, endPoint: .bottom))
                                .overlay(RoundedRectangle(cornerRadius: s * 0.24, style: .continuous).strokeBorder(glow.opacity(0.7), lineWidth: 1.5))
                            Image(systemName: glyph).font(.system(size: s * 0.38, weight: .bold)).foregroundStyle(.white)
                        }.frame(width: s * 0.84, height: s * 0.84)
                    } else {
                        DeskSprite(name: glyph, size: s)
                    }
                }
                .rotationEffect(.degrees(tilt)).scaleEffect(breathe).offset(y: -bob)
                .shadow(color: .black.opacity(0.55), radius: 15, y: 11)
            }
            .frame(width: s, height: s)
        }
    }
}

struct DioTrayMote: View {
    let glyph: String
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let bob = CGFloat(sin(t * 1.3 + Double(glyph.count)) * 2)
            DeskSprite(name: glyph, size: 30).offset(y: -bob)
        }
    }
}

// LOW-PROFILE zone tray — a compact labeled shelf tile that holds primitives. Tap to dive; drop a meeting on it to file.
// A resizable, movable 2D AREA — drag the body to arrange (tetris), drag the corner grip to resize, tap to
// dive. Holds meetings; a meeting dropped inside it files there. `drag`/`rsz` give live feedback; commit on end.
struct DioZoneTray: View {
    let name: String, tint: Color
    let members: [any DeskPrimitive]; let subZones: Int; let size: CGSize
    let landed: Bool; let index: Int; let dimmed: Bool; let hot: Bool
    let onDive: () -> Void; let onMove: (CGSize) -> Void; let onResize: (CGSize) -> Void
    @State private var drag: CGSize = .zero
    @State private var rsz: CGSize = .zero
    var body: some View {
        let w = max(120, size.width + rsz.width), h = max(78, size.height + rsz.height)
        let cap = max(1, Int((w - 26) / 40))
        ZStack(alignment: .bottomTrailing) {
            VStack(alignment: .leading, spacing: 7) {
                HStack(spacing: 7) {
                    Image(systemName: subZones > 0 ? "square.stack.3d.up.fill" : "tray.full.fill").font(.system(size: 14, weight: .bold)).foregroundStyle(tint)
                    Text(name).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                    Spacer(minLength: 0)
                    Text("\(members.count)\(subZones > 0 ? "·+\(subZones)" : "")").font(.system(size: 11, weight: .black, design: .rounded)).foregroundStyle(tint)
                        .padding(.horizontal, 6).padding(.vertical, 2).background(Capsule().fill(tint.opacity(0.16)))
                }
                HStack(spacing: 8) { ForEach(Array(members.prefix(cap).enumerated()), id: \.offset) { _, m in DioTrayMote(glyph: m.glyph) } }
                Spacer(minLength: 0)
                HStack(spacing: 4) {
                    Image(systemName: "arrow.down.forward.and.arrow.up.backward").font(.system(size: 9, weight: .black))
                    Text(hot ? "DROP TO FILE" : "TAP TO DIVE").font(.system(size: 9, weight: .heavy, design: .rounded)).tracking(1)
                }.foregroundStyle(tint.opacity(0.9))
            }
            .padding(13).frame(width: w, height: h, alignment: .topLeading)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(LinearGradient(colors: [tint.opacity(hot ? 0.2 : 0.1), DioPal.trayBot.opacity(0.9)], startPoint: .top, endPoint: .bottom))
                    .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(tint.opacity(hot ? 1 : 0.5), lineWidth: hot ? 2.5 : 1.5))
                    .shadow(color: .black.opacity(0.4), radius: 12, y: 8)
            )
            .contentShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { if hypot($0.translation.width, $0.translation.height) > 6 { drag = $0.translation } }
                .onEnded { v in
                    let d = hypot(v.translation.width, v.translation.height)
                    if d < 9 { onDive() } else { onMove(v.translation) }
                    drag = .zero
                })
            // corner resize grip
            Image(systemName: "arrow.up.left.and.arrow.down.right")
                .font(.system(size: 12, weight: .black)).foregroundStyle(tint)
                .frame(width: 30, height: 30).background(Circle().fill(.black.opacity(0.4)).overlay(Circle().strokeBorder(tint.opacity(0.6), lineWidth: 1)))
                .offset(x: 6, y: 6)
                .gesture(DragGesture(minimumDistance: 1)
                    .onChanged { rsz = CGSize(width: max(120 - size.width, $0.translation.width), height: max(78 - size.height, $0.translation.height)) }
                    .onEnded { v in onResize(CGSize(width: v.translation.width, height: v.translation.height)); rsz = .zero })
        }
        .frame(width: w, height: h)
        .scaleEffect(hot ? 1.03 : (landed ? 1 : 0.4)).opacity(landed ? (dimmed ? 0 : 1) : 0)
        .offset(drag)
        .animation(.spring(response: 0.65, dampingFraction: 0.62).delay(Double(index) * 0.06), value: landed)
        .animation(.spring(response: 0.35, dampingFraction: 0.6), value: hot)
        .allowsHitTesting(!dimmed)
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

// THE PULL-OUT — ONE renderer for ANY primitive. Header (glyph/title/egress) + the primitive's `sections`
// (each SectionBody drawn one way, here) + its `actions`. No per-type code — the contract drives it.
struct DioPullout: View {
    let prim: any DeskPrimitive
    let onClose: () -> Void; let onAction: (PrimitiveAction) -> Void; let onRouteSection: (String, String) -> Void
    var onActItem: ((String, String) -> Void)? = nil      // act on a single action row → send/file
    private func sectionText(_ body: SectionBody) -> String {
        switch body {
        case .text(let s): return s
        case .actions(let r): return r.map { "- \($0.task)" + ($0.meta.map { " (\($0))" } ?? "") }.joined(separator: "\n")
        case .chips(let c): return c.joined(separator: ", ")
        case .transcript(let l): return l.map { "\($0.who): \($0.what)" }.joined(separator: "\n")
        }
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 11) {
                DeskSprite(name: prim.glyph, size: 40)
                VStack(alignment: .leading, spacing: 2) {
                    Text(prim.title).font(.system(size: 18, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                    Text(prim.subtitle).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
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
                let canRoute = !prim.emits.isEmpty
                VStack(alignment: .leading, spacing: 16) {
                    ForEach(Array(prim.sections.enumerated()), id: \.offset) { _, sec in
                        VStack(alignment: .leading, spacing: 8) {
                            DrawerSection(label: sec.label, tint: sec.tint) { sectionBody(sec.body) }
                            if canRoute {
                                Button { onRouteSection("\(prim.title) · \(sec.label.capitalized)", sectionText(sec.body)) } label: {
                                    HStack(spacing: 5) { Image(systemName: "wand.and.stars").font(.system(size: 11, weight: .bold)); Text("Route this to AI").font(.system(size: 11.5, weight: .heavy, design: .rounded)) }
                                        .foregroundStyle(DioPal.accent).padding(.horizontal, 11).frame(height: 30)
                                        .background(Capsule().strokeBorder(DioPal.accent.opacity(0.5), lineWidth: 1))
                                }.buttonStyle(.plain)
                            }
                        }
                    }
                    if prim.sections.isEmpty {
                        Text("Nothing here yet.").font(.system(size: 13, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                            .frame(maxWidth: .infinity, alignment: .center).padding(.vertical, 24)
                    }
                    ForEach(Array(prim.actions.enumerated()), id: \.offset) { _, act in
                        Button { onAction(act) } label: {
                            HStack(spacing: 7) {
                                Image(systemName: act.icon).font(.system(size: 12, weight: .bold))
                                Text(act.label).font(.system(size: 12.5, weight: .heavy, design: .rounded))
                            }.foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 40)
                                .background(Capsule().strokeBorder(DioPal.muted.opacity(0.4), lineWidth: 1))
                        }.buttonStyle(.plain)
                    }
                }
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

    // the ONE place that knows how to draw each section body
    @ViewBuilder private func sectionBody(_ body: SectionBody) -> some View {
        switch body {
        case .text(let s):
            Text(s).font(.system(size: 14.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.92)).fixedSize(horizontal: false, vertical: true)
        case .actions(let rows):
            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(rows.enumerated()), id: \.offset) { _, r in
                    HStack(alignment: .top, spacing: 10) {
                        Image(systemName: "circle").font(.system(size: 15, weight: .bold)).foregroundStyle(DioPal.mint).padding(.top, 1)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(r.task).font(.system(size: 14, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text).fixedSize(horizontal: false, vertical: true)
                            if let meta = r.meta { Text(meta).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted) }
                        }
                        Spacer(minLength: 6)
                        if let act = onActItem {
                            Button { act(r.task, r.task + (r.meta.map { "\n\($0)" } ?? "")) } label: {
                                Image(systemName: "arrow.up.forward").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.mint)
                                    .frame(width: 30, height: 30)
                                    .background(Circle().fill(DioPal.mint.opacity(0.13)).overlay(Circle().strokeBorder(DioPal.mint.opacity(0.4), lineWidth: 1)))
                            }.buttonStyle(.plain)
                        }
                    }
                }
            }
        case .chips(let items):
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 76), spacing: 8, alignment: .leading)], alignment: .leading, spacing: 8) {
                ForEach(Array(items.enumerated()), id: \.offset) { _, it in
                    Text(it).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9))
                        .lineLimit(1).padding(.horizontal, 10).padding(.vertical, 6)
                        .background(Capsule().fill(DioPal.violet.opacity(0.14)).overlay(Capsule().strokeBorder(DioPal.violet.opacity(0.35), lineWidth: 1)))
                }
            }
        case .transcript(let lines):
            VStack(alignment: .leading, spacing: 9) {
                ForEach(Array(lines.enumerated()), id: \.offset) { _, ln in
                    VStack(alignment: .leading, spacing: 1) {
                        Text(ln.who).font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.cobalt)
                        Text(ln.what).font(.system(size: 13.5, weight: .regular, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.88)).fixedSize(horizontal: false, vertical: true)
                    }
                }
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

// THE IN-DESK RECORDING CONSOLE — recording happens ON the desk, not in a separate window. A live
// waveform off the real mic, the words as they're heard, the elapsed time, and one big stop. When you
// stop, the meeting weaves on-device and a cassette lands on the desk.
struct DioRecordingConsole: View {
    @ObservedObject var model: CaptureModel
    let onStop: () -> Void
    @State private var reveal = false        // tap the waveform → the recent segments push out (the "tape")
    @State private var expanded = false      // pull it up into the full live-transcript modal
    private func timeString(_ s: Double) -> String { let i = Int(s); return String(format: "%d:%02d", i / 60, i % 60) }
    private func tapHaptic() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred()
        #endif
    }
    private var segments: [String] {
        model.liveTranscript.replacingOccurrences(of: "\n", with: " ")
            .components(separatedBy: CharacterSet(charactersIn: ".?!"))
            .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
    }
    private var caption: String {
        if model.transcribing { return "Weaving your meeting on this iPad…" }
        if !model.partial.isEmpty { return model.partial }
        return segments.last ?? "Listening…"
    }
    var body: some View {
        ZStack {
            LinearGradient(colors: [DioPal.bgTop, DioPal.bgMid, DioPal.bgBot], startPoint: .top, endPoint: .bottom).ignoresSafeArea().opacity(0.96)
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                RadialGradient(colors: [(model.transcribing ? DioPal.cobalt : Color(hex: 0xFF4D4D)).opacity(0.14 + 0.05 * sin(t * 1.5)), .clear], center: .center, startRadius: 20, endRadius: 460)
                    .ignoresSafeArea().blendMode(.plusLighter)
            }
            VStack(spacing: 22) {
                Spacer()
                TimelineView(.animation) { tl in
                    let blink = 0.4 + 0.6 * abs(sin(tl.date.timeIntervalSinceReferenceDate * 2))
                    HStack(spacing: 10) {
                        Circle().fill(model.transcribing ? DioPal.cobalt : Color(hex: 0xFF4D4D)).frame(width: 11, height: 11).opacity(model.recording ? blink : 1)
                        Text(model.transcribing ? "WEAVING" : "REC").font(.system(size: 13, weight: .heavy, design: .rounded)).tracking(3).foregroundStyle(DioPal.text)
                        Text(timeString(model.elapsedSeconds)).font(.system(size: 15, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(DioPal.muted)
                    }
                }
                // the waveform is a button — tap it to pull the transcript tape out
                Button { tapHaptic(); withAnimation(.spring(response: 0.5, dampingFraction: 0.78)) { reveal.toggle() } } label: {
                    VStack(spacing: 6) {
                        MicWaveform(level: CGFloat(model.level), active: model.recording, bars: 34, height: 76).frame(maxWidth: 340).padding(.horizontal, 28)
                        HStack(spacing: 5) {
                            Image(systemName: reveal ? "chevron.up" : "text.alignleft").font(.system(size: 9, weight: .black))
                            Text(reveal ? "hide" : "tap to read what it's hearing").font(.system(size: 10, weight: .heavy, design: .rounded))
                        }.foregroundStyle(DioPal.muted)
                    }
                }.buttonStyle(.plain).disabled(model.transcribing)
                // the transcript TAPE — recent segments unspool; pull it up for the full modal
                if reveal && !model.transcribing {
                    DioTranscriptTape(segments: Array(segments.suffix(3)), partial: model.partial, onExpand: { tapHaptic(); withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { expanded = true } })
                        .transition(.move(edge: .top).combined(with: .opacity)).padding(.horizontal, 22)
                } else {
                    Text(caption).font(.system(size: 16, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.92))
                        .multilineTextAlignment(.center).lineLimit(3).frame(maxWidth: 360, minHeight: 60).padding(.horizontal, 24)
                }
                HStack(spacing: 6) {
                    Image(systemName: "lock.fill").font(.system(size: 9, weight: .bold))
                    Text("On device").font(.system(size: 10, weight: .heavy, design: .rounded))
                }.foregroundStyle(DioPal.mint).padding(.horizontal, 10).frame(height: 26).background(Capsule().fill(DioPal.mint.opacity(0.14)))
                Spacer()
                if model.transcribing {
                    HStack(spacing: 11) { ProgressView().tint(DioPal.text); Text("Weaving your meeting…").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text) }
                        .padding(.bottom, 60)
                } else {
                    VStack(spacing: 12) {
                        Button(action: onStop) {
                            ZStack {
                                TimelineView(.animation) { tl in
                                    Circle().stroke(Color(hex: 0xFF4D4D).opacity(0.5), lineWidth: 2)
                                        .frame(width: 100, height: 100).scaleEffect(1 + CGFloat(min(1, model.level)) * 0.35)
                                        .opacity(0.5 + 0.5 * abs(sin(tl.date.timeIntervalSinceReferenceDate * 1.6)))
                                }
                                Circle().fill(Color(hex: 0xFF4D4D)).frame(width: 84, height: 84).shadow(color: Color(hex: 0xFF4D4D).opacity(0.6), radius: 20, y: 6)
                                RoundedRectangle(cornerRadius: 7, style: .continuous).fill(.white).frame(width: 30, height: 30)
                            }
                        }.buttonStyle(.plain)
                        Text("tap to stop & save").font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                    }.padding(.bottom, 50)
                }
            }
            if !model.error.isEmpty {
                Text(model.error).font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(.white)
                    .padding(12).background(RoundedRectangle(cornerRadius: 12).fill(Color(hex: 0xFF4D4D).opacity(0.9)))
                    .frame(maxHeight: .infinity, alignment: .top).padding(.top, 70)
            }
            #if targetEnvironment(simulator)
            Color.clear.onAppear {
                let r = ProcessInfo.processInfo.environment["HS_DESK_RECORD"] ?? ""
                if r == "tape" || r == "modal" { reveal = true }
                if r == "modal" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { expanded = true } }
            }
            #endif
            // the full live-transcript modal — pulled up from the tape
            if expanded {
                DioLiveTranscriptModal(segments: segments, partial: model.partial, elapsed: timeString(model.elapsedSeconds),
                                       onClose: { tapHaptic(); withAnimation(.spring(response: 0.5, dampingFraction: 0.84)) { expanded = false } })
                    .transition(.move(edge: .bottom).combined(with: .opacity)).zIndex(10)
            }
        }
    }
}

// The transcript TAPE — the last few heard segments, unspooling like a printout; tap to pull up the full modal.
struct DioTranscriptTape: View {
    let segments: [String]; let partial: String; let onExpand: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: "waveform").font(.system(size: 10, weight: .bold)).foregroundStyle(DioPal.accent)
                Text("JUST HEARD").font(.system(size: 10, weight: .heavy, design: .rounded)).tracking(2).foregroundStyle(DioPal.muted)
                Spacer(minLength: 0)
                Button(action: onExpand) {
                    HStack(spacing: 4) { Text("Expand").font(.system(size: 11, weight: .heavy, design: .rounded)); Image(systemName: "arrow.up.left.and.arrow.down.right").font(.system(size: 9, weight: .black)) }
                        .foregroundStyle(DioPal.accent)
                }.buttonStyle(.plain)
            }
            if segments.isEmpty && partial.isEmpty {
                Text("…nothing yet").font(.system(size: 14, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            } else {
                ForEach(Array(segments.enumerated()), id: \.offset) { i, s in
                    HStack(alignment: .top, spacing: 8) {
                        Circle().fill(DioPal.accent.opacity(0.5)).frame(width: 5, height: 5).padding(.top, 7)
                        Text(s + ".").font(.system(size: 14.5, weight: i == segments.count - 1 ? .semibold : .regular, design: .rounded))
                            .foregroundStyle(DioPal.text.opacity(i == segments.count - 1 ? 0.95 : 0.6))
                    }
                }
                if !partial.isEmpty {
                    HStack(alignment: .top, spacing: 8) {
                        Circle().fill(DioPal.accent).frame(width: 5, height: 5).padding(.top, 7)
                        Text(partial).font(.system(size: 14.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.accent)
                    }
                }
            }
        }
        .frame(maxWidth: 380, alignment: .leading).padding(16)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.white.opacity(0.05))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(.white.opacity(0.09), lineWidth: 1)))
    }
}

// The full live transcript, pulled up — the whole meeting so far, scrolling, while you keep recording.
struct DioLiveTranscriptModal: View {
    let segments: [String]; let partial: String; let elapsed: String; let onClose: () -> Void
    var body: some View {
        ZStack(alignment: .bottom) {
            Color.black.opacity(0.6).ignoresSafeArea().contentShape(Rectangle()).onTapGesture(perform: onClose)
            VStack(spacing: 0) {
                Capsule().fill(.white.opacity(0.3)).frame(width: 46, height: 5).padding(.top, 12).padding(.bottom, 14)
                HStack(spacing: 8) {
                    Image(systemName: "text.alignleft").font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.accent)
                    Text("Live transcript").font(.system(size: 17, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Spacer(minLength: 0)
                    Text(elapsed).font(.system(size: 13, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(DioPal.muted)
                    Button(action: onClose) { Image(systemName: "xmark").font(.system(size: 13, weight: .black)).foregroundStyle(DioPal.text).frame(width: 32, height: 32).background(Circle().fill(.white.opacity(0.1))) }.buttonStyle(.plain)
                }.padding(.horizontal, 20).padding(.bottom, 12)
                ScrollViewReader { proxy in
                    ScrollView(showsIndicators: false) {
                        VStack(alignment: .leading, spacing: 11) {
                            ForEach(Array(segments.enumerated()), id: \.offset) { i, s in
                                Text(s + ".").font(.system(size: 15.5, weight: .regular, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9))
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            if !partial.isEmpty {
                                Text(partial).font(.system(size: 15.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.accent)
                                    .frame(maxWidth: .infinity, alignment: .leading).id("tail")
                            }
                        }.padding(.horizontal, 20).padding(.bottom, 24)
                    }
                    .onAppear { withAnimation { proxy.scrollTo("tail", anchor: .bottom) } }
                }
                HStack(spacing: 6) {
                    Image(systemName: "lock.fill").font(.system(size: 9, weight: .bold)); Text("Still recording · on device").font(.system(size: 10.5, weight: .heavy, design: .rounded))
                }.foregroundStyle(DioPal.mint).padding(.horizontal, 11).frame(height: 28).background(Capsule().fill(DioPal.mint.opacity(0.14))).padding(.bottom, 22)
            }
            .frame(maxWidth: .infinity).frame(height: UIScreen.main.bounds.height * 0.62)
            .background(UnevenRoundedRectangle(topLeadingRadius: 30, topTrailingRadius: 30, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x191522), Color(hex: 0x0B0910)], startPoint: .top, endPoint: .bottom))
                .overlay(UnevenRoundedRectangle(topLeadingRadius: 30, topTrailingRadius: 30, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)).ignoresSafeArea(edges: .bottom))
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

// THE ROUTE SHEET — drop a primitive on the AI core → pick a lens (or write a prompt) → Ask.
struct DioRouteSheet: View {
    let sourceTitle: String; let onAsk: (String, String) -> Void; let onCancel: () -> Void; let onSaveTool: (String) -> Void
    @State private var lens = RouteLenses.all.first!.name
    @State private var prompt = RouteLenses.all.first!.instruction
    var body: some View {
        ZStack {
            Color.black.opacity(0.55).ignoresSafeArea().onTapGesture { onCancel() }
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 9) {
                    DeskSprite(name: "cartridge", size: 34)
                    VStack(alignment: .leading, spacing: 1) {
                        Text("Route through the AI core").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text(sourceTitle).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                    Spacer(minLength: 0)
                    HStack(spacing: 5) {
                        Image(systemName: "lock.fill").font(.system(size: 9, weight: .bold))
                        Text("On device").font(.system(size: 10, weight: .heavy, design: .rounded))
                    }.foregroundStyle(DioPal.mint).padding(.horizontal, 9).frame(height: 26).background(Capsule().fill(DioPal.mint.opacity(0.14)))
                }
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 110), spacing: 8)], spacing: 8) {
                    ForEach(RouteLenses.all) { l in
                        Button { lens = l.name; prompt = l.instruction } label: {
                            HStack(spacing: 6) {
                                Image(systemName: l.icon).font(.system(size: 12, weight: .bold))
                                Text(l.name).font(.system(size: 12.5, weight: .heavy, design: .rounded)).lineLimit(1)
                            }
                            .foregroundStyle(lens == l.name ? DioPal.text : DioPal.muted)
                            .frame(maxWidth: .infinity).frame(height: 38)
                            .background(Capsule().fill(lens == l.name ? DioPal.accent.opacity(0.22) : .white.opacity(0.04))
                                .overlay(Capsule().strokeBorder((lens == l.name ? DioPal.accent : .clear).opacity(0.6), lineWidth: 1)))
                        }.buttonStyle(.plain)
                    }
                }
                VStack(alignment: .leading, spacing: 6) {
                    Text("PROMPT").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(1.4)
                    TextEditor(text: $prompt).font(.system(size: 13.5, weight: .medium, design: .rounded))
                        .scrollContentBackground(.hidden).foregroundStyle(DioPal.text).frame(height: 78)
                        .padding(10).background(RoundedRectangle(cornerRadius: 12).fill(.white.opacity(0.05))
                            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
                }
                HStack(spacing: 10) {
                    Button(action: onCancel) { Text("Cancel").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 46).background(Capsule().fill(.white.opacity(0.06))) }.buttonStyle(.plain)
                    Button { onAsk(lens, prompt) } label: {
                        HStack(spacing: 6) { Image(systemName: "wand.and.stars").font(.system(size: 14, weight: .bold)); Text("Ask").font(.system(size: 15, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 46)
                            .background(Capsule().fill(LinearGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent], startPoint: .top, endPoint: .bottom)))
                    }.buttonStyle(.plain)
                }
                Button { onSaveTool(prompt) } label: {
                    HStack(spacing: 6) { Image(systemName: "gearshape.2.fill").font(.system(size: 12, weight: .bold)); Text("Save as a reusable tool").font(.system(size: 12.5, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(DioPal.violet).frame(maxWidth: .infinity).frame(height: 38)
                        .background(Capsule().strokeBorder(DioPal.violet.opacity(0.5), lineWidth: 1))
                }.buttonStyle(.plain)
            }
            .padding(20).frame(maxWidth: 460)
            .background(RoundedRectangle(cornerRadius: 26, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 30, y: 16))
            .padding(.horizontal, 18)
        }
        .transition(.opacity)
    }
}

// THE THEATER — the route running through the AI core, on this iPad (or the endpoint).
// On-desk routing: the cable runs from the source to the target (which pulses as it works) — no modal.
struct DioRoutingTheater: View {
    let from: CGPoint, to: CGPoint; let sourceTitle: String; let lens: String; let local: Bool; let tint: Color
    var body: some View {
        ZStack {
            Color.black.opacity(0.42).ignoresSafeArea()
            RouteArc(from: from, to: to, tint: tint)
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                ForEach(0..<3) { i in
                    let p = ((t * 0.7 + Double(i) * 0.33).truncatingRemainder(dividingBy: 1))
                    Circle().stroke(tint.opacity(0.55 * (1 - p)), lineWidth: 2)
                        .frame(width: 70 + CGFloat(p) * 90, height: 70 + CGFloat(p) * 90).position(to)
                }
            }
            VStack(spacing: 3) {
                Text("Routing \(sourceTitle)").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                Text("\(lens) · \(local ? "on this iPad · no network" : "endpoint")").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            }
            .padding(.horizontal, 16).padding(.vertical, 9).background(Capsule().fill(.black.opacity(0.55)))
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom).padding(.bottom, 130)
        }
        .transition(.opacity)
    }
}

// THE PRINTED CARD — the new primitive that just came out of the core. Keep it (lands on the desk) or bin it.
struct DioPrintedCard: View {
    let rec: OutputRecord; let onKeep: () -> Void; let onBin: () -> Void
    @State private var shown = false
    var body: some View {
        ZStack {
            Color.black.opacity(0.7).ignoresSafeArea().onTapGesture { onBin() }
            VStack(spacing: 0) {
                HStack(spacing: 11) {
                    DeskSprite(name: "note", size: 38)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(rec.title).font(.system(size: 17, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text("fresh from the AI core · from \(rec.source)").font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                    Spacer(minLength: 0)
                }.padding(.horizontal, 18).padding(.top, 16).padding(.bottom, 10)
                ScrollView(showsIndicators: false) {
                    Text(rec.body).font(.system(size: 14.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.92))
                        .frame(maxWidth: .infinity, alignment: .leading).fixedSize(horizontal: false, vertical: true).padding(.horizontal, 18)
                }
                HStack(spacing: 10) {
                    Button(action: onBin) { HStack(spacing: 6) { Image(systemName: "trash"); Text("Bin") }.font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 46).background(Capsule().fill(.white.opacity(0.06))) }.buttonStyle(.plain)
                    Button(action: onKeep) { HStack(spacing: 6) { Image(systemName: "tray.and.arrow.down.fill"); Text("Keep on desk") }.font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 46).background(Capsule().fill(LinearGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent], startPoint: .top, endPoint: .bottom))) }.buttonStyle(.plain)
                }.padding(16)
            }
            .frame(maxWidth: 480, maxHeight: 520)
            .background(RoundedRectangle(cornerRadius: 26, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(DioPal.accent.opacity(0.4), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 30, y: 16))
            .padding(.horizontal, 18).scaleEffect(shown ? 1 : 0.85).opacity(shown ? 1 : 0)
        }
        .onAppear { withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) { shown = true } }
    }
}

// THE ROUTE ARC — a glowing cable from a source primitive to its target with tokens traveling the wire
// while the route runs (the Blueprints "token travels wires" viz, on the desk).
func dioQuad(_ a: CGPoint, _ c: CGPoint, _ b: CGPoint, _ t: Double) -> CGPoint {
    let u = 1 - t
    return CGPoint(x: u * u * a.x + 2 * u * t * c.x + t * t * b.x,
                   y: u * u * a.y + 2 * u * t * c.y + t * t * b.y)
}
struct RouteArc: View {
    let from: CGPoint, to: CGPoint, tint: Color
    var body: some View {
        let ctrl = CGPoint(x: (from.x + to.x) / 2, y: min(from.y, to.y) - 90)
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            Canvas { ctx, _ in
                var path = Path(); path.move(to: from); path.addQuadCurve(to: to, control: ctrl)
                ctx.stroke(path, with: .color(tint.opacity(0.22)), style: StrokeStyle(lineWidth: 9, lineCap: .round))
                ctx.stroke(path, with: .color(tint.opacity(0.8)), style: StrokeStyle(lineWidth: 2.5, lineCap: .round, dash: [2, 7]))
                for k in 0..<3 {
                    let p = (t * 0.85 + Double(k) * 0.34).truncatingRemainder(dividingBy: 1)
                    let pt = dioQuad(from, ctrl, to, p)
                    ctx.fill(Path(ellipseIn: CGRect(x: pt.x - 8, y: pt.y - 8, width: 16, height: 16)), with: .color(tint.opacity(0.3)))
                    ctx.fill(Path(ellipseIn: CGRect(x: pt.x - 3.5, y: pt.y - 3.5, width: 7, height: 7)), with: .color(.white))
                }
            }
        }
        .allowsHitTesting(false)
    }
}

// The ONE egress badge (POSITIONING canon): local / local+cloud / cloud+target. No privacy prose.
struct EgressBadge: View {
    enum Scope { case local; case cloud(String) }
    let scope: Scope
    var body: some View {
        let (icon, label, tint): (String, String, Color) = {
            switch scope {
            case .local: return ("lock.fill", "On device", DioPal.mint)
            case .cloud(let t): return ("arrow.up.forward.app.fill", "Cloud · \(t)", Color(hex: 0xF5A524))
            }
        }()
        HStack(spacing: 5) {
            Image(systemName: icon).font(.system(size: 9, weight: .bold))
            Text(label).font(.system(size: 10, weight: .heavy, design: .rounded))
        }.foregroundStyle(tint).padding(.horizontal, 9).frame(height: 26).background(Capsule().fill(tint.opacity(0.14)))
    }
}

// THE SEND CARD — propose→approve→execute for a connector. Shows what, where, and the egress badge.
struct DioSendCard: View {
    let sourceTitle: String, preview: String, connName: String
    let sending: Bool
    let onApprove: () -> Void; let onCancel: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.7).ignoresSafeArea().onTapGesture { if !sending { onCancel() } }
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 9) {
                    Image(systemName: "paperplane.fill").font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                        .frame(width: 36, height: 36).background(Circle().fill(DioPal.cobalt))
                    VStack(alignment: .leading, spacing: 1) {
                        Text("Send to \(connName)").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text("you approve every send").font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                    }
                    Spacer(minLength: 0)
                    EgressBadge(scope: .cloud(connName))
                }
                VStack(alignment: .leading, spacing: 6) {
                    Text(sourceTitle).font(.system(size: 13.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(preview).font(.system(size: 13, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.82)).lineLimit(5).fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .leading).padding(13)
                .background(RoundedRectangle(cornerRadius: 14).fill(.white.opacity(0.04)).overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(.white.opacity(0.07), lineWidth: 1)))
                HStack(spacing: 10) {
                    Button(action: onCancel) { Text("Cancel").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 46).background(Capsule().fill(.white.opacity(0.06))) }.buttonStyle(.plain).disabled(sending)
                    Button(action: onApprove) {
                        HStack(spacing: 6) {
                            if sending { ProgressView().tint(.white) } else { Image(systemName: "checkmark").font(.system(size: 14, weight: .bold)) }
                            Text(sending ? "Sending…" : "Approve & send").font(.system(size: 14.5, weight: .heavy, design: .rounded))
                        }.foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 46)
                            .background(Capsule().fill(LinearGradient(colors: [Color(hex: 0x7AA2F7), DioPal.cobalt], startPoint: .top, endPoint: .bottom)))
                    }.buttonStyle(.plain).disabled(sending)
                }
            }
            .padding(20).frame(maxWidth: 460)
            .background(RoundedRectangle(cornerRadius: 26, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 30, y: 16))
            .padding(.horizontal, 18)
        }
    }
}

// THE ACT SHEET — an action item is not a dead bullet; act on it. Turn it into tracked work (a host-gated
// connector → propose→approve→execute, the credential stays on the Mac) or keep it as a card on your desk.
struct DioActSheet: View {
    let itemText: String
    let connectors: [(connId: String, name: String, symbol: String, tint: Color)]
    let configured: Bool
    let onSend: (String, String) -> Void
    let onFile: () -> Void
    let onCancel: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.7).ignoresSafeArea().onTapGesture { onCancel() }
            VStack(alignment: .leading, spacing: 13) {
                HStack(spacing: 9) {
                    Image(systemName: "bolt.fill").font(.system(size: 14, weight: .bold)).foregroundStyle(.white)
                        .frame(width: 34, height: 34).background(Circle().fill(DioPal.mint))
                    VStack(alignment: .leading, spacing: 1) {
                        Text("Act on this").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text("turn it into tracked work, or keep it").font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                    }
                    Spacer(minLength: 0)
                }
                Text(itemText).font(.system(size: 13.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9))
                    .lineLimit(4).fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading).padding(12)
                    .background(RoundedRectangle(cornerRadius: 13).fill(.white.opacity(0.04)).overlay(RoundedRectangle(cornerRadius: 13).strokeBorder(.white.opacity(0.07), lineWidth: 1)))
                if !configured {
                    HStack(spacing: 6) {
                        Image(systemName: "desktopcomputer").font(.system(size: 10, weight: .bold))
                        Text("Pair your Mac to send · tap a connector tile on the desk").font(.system(size: 10.5, weight: .heavy, design: .rounded))
                    }.foregroundStyle(DioPal.muted).padding(.horizontal, 10).frame(height: 28).background(Capsule().fill(.white.opacity(0.05)))
                }
                Text("SEND TO").font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(1.4)
                VStack(spacing: 8) {
                    ForEach(connectors, id: \.connId) { c in
                        Button { onSend(c.connId, c.name) } label: {
                            actRow(symbol: c.symbol, tint: c.tint, name: "Send to \(c.name)", sub: configured ? "via your Mac" : "needs your Mac", egress: .cloud(c.name))
                        }.buttonStyle(.plain).disabled(!configured).opacity(configured ? 1 : 0.45)
                    }
                }
                Text("OR KEEP IT").font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(1.4).padding(.top, 2)
                Button { onFile() } label: {
                    actRow(symbol: "tray.and.arrow.down.fill", tint: DioPal.accent, name: "Keep as a card", sub: "on your desk, to route again", egress: .local)
                }.buttonStyle(.plain)
                Button(action: onCancel) {
                    Text("Cancel").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        .frame(maxWidth: .infinity).frame(height: 44).background(Capsule().fill(.white.opacity(0.06)))
                }.buttonStyle(.plain).padding(.top, 2)
            }
            .padding(20).frame(maxWidth: 460)
            .background(RoundedRectangle(cornerRadius: 26, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 30, y: 16))
            .padding(.horizontal, 18)
        }
    }
    @ViewBuilder private func actRow(symbol: String, tint: Color, name: String, sub: String, egress: EgressBadge.Scope) -> some View {
        HStack(spacing: 11) {
            Image(systemName: symbol).font(.system(size: 14, weight: .bold)).foregroundStyle(.white)
                .frame(width: 34, height: 34).background(RoundedRectangle(cornerRadius: 10, style: .continuous).fill(tint.opacity(0.9)))
            VStack(alignment: .leading, spacing: 1) {
                Text(name).font(.system(size: 14.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                Text(sub).font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            }
            Spacer(minLength: 0)
            EgressBadge(scope: egress)
        }
        .padding(.horizontal, 12).frame(height: 54)
        .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(.white.opacity(0.04))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(.white.opacity(0.07), lineWidth: 1)))
    }
}

// The link to the paired Mac (host PC). Connectors route THROUGH it: the iPad proposes + approves; the host
// executes with the Slack credential joined in memory ON THE MAC — the iPad never holds it. Grounded in the
// HoldSpeak actuator framework (propose→approve→execute, Phase 37/38/61) via /api/companion/slack/*.
struct DeskHostLink {
    let host: String; let port: Int
    enum HostError: Error { case message(String) }
    private var base: URL? { URL(string: "http://\(host):\(port)") }

    func reachable() async -> Bool {
        guard let u = base?.appendingPathComponent("health") else { return false }
        var r = URLRequest(url: u); r.timeoutInterval = 4
        if let (_, resp) = try? await URLSession.shared.data(for: r), (resp as? HTTPURLResponse)?.statusCode == 200 { return true }
        return false
    }
    /// Propose an arbitrary-text send on the host for a target ("slack"/"webhook") → (proposalId, preview).
    func propose(target: String, title: String, text: String) async throws -> (id: String, preview: String) {
        var body: [String: Any] = ["text": text]
        if !title.isEmpty { body["title"] = title }
        let (data, resp) = try await post("api/companion/\(target)/propose", body)
        try Self.check(data, resp, "Your Mac refused the send.")
        let p = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["proposal"] as? [String: Any]
        return (p?["id"] as? String ?? "", p?["preview"] as? String ?? text)
    }
    /// Approve (→ execute) or reject the proposal on the host → (status, error?).
    func decide(target: String, id: String, approved: Bool) async throws -> (status: String, error: String?) {
        let (data, resp) = try await post("api/companion/\(target)/\(id)/decision",
                                          ["decision": approved ? "approved" : "rejected", "decided_by": "ipad-desk"])
        try Self.check(data, resp, "Your Mac refused the decision.")
        let p = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["proposal"] as? [String: Any]
        return (p?["status"] as? String ?? "", p?["error"] as? String)
    }
    private func post(_ path: String, _ body: [String: Any]) async throws -> (Data, URLResponse) {
        guard let u = base?.appendingPathComponent(path) else { throw HostError.message("No Mac paired.") }
        var r = URLRequest(url: u); r.httpMethod = "POST"; r.timeoutInterval = 14
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await URLSession.shared.data(for: r)
    }
    private static func check(_ data: Data, _ resp: URLResponse, _ fallback: String) throws {
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(code) else {
            let msg = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["error"] as? String
            throw HostError.message(msg ?? fallback)
        }
    }
}

// A tool's glyph (SF-symbol tool or pixel sprite) at any size — used in the dock.
struct DioToolGlyph: View {
    let prim: any DeskPrimitive; let size: CGFloat
    var body: some View {
        Group {
            if prim.isSymbol {
                ZStack {
                    RoundedRectangle(cornerRadius: size * 0.26, style: .continuous)
                        .fill(LinearGradient(colors: [prim.color.opacity(0.42), Color(hex: 0x12101A)], startPoint: .top, endPoint: .bottom))
                        .overlay(RoundedRectangle(cornerRadius: size * 0.26, style: .continuous).strokeBorder(prim.color.opacity(0.7), lineWidth: 1.5))
                    Image(systemName: prim.glyph).font(.system(size: size * 0.4, weight: .bold)).foregroundStyle(.white)
                }.frame(width: size, height: size)
            } else {
                DeskSprite(name: prim.glyph, size: size)
            }
        }
    }
}

// One tool blooming in the radial summon — a lit satellite around the card; tap to route.
struct DioSummonSatellite: View {
    let prim: any DeskPrimitive; let index: Int; let onTap: () -> Void
    @State private var shown = false
    var body: some View {
        VStack(spacing: 6) {
            DioToolGlyph(prim: prim, size: 60)
                .background(Circle().fill(prim.color.opacity(0.18)).frame(width: 80, height: 80))
                .shadow(color: prim.color.opacity(0.55), radius: 13)
            Text(prim.title).font(.system(size: 11.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                .lineLimit(1).padding(.horizontal, 9).padding(.vertical, 3).background(Capsule().fill(.black.opacity(0.45)))
        }
        .scaleEffect(shown ? 1 : 0.2).opacity(shown ? 1 : 0)
        .contentShape(Circle()).onTapGesture(perform: onTap)
        .onAppear { withAnimation(.spring(response: 0.42, dampingFraction: 0.68).delay(Double(index) * 0.05)) { shown = true } }
    }
}

// One tool tile in the open dock — a drop target (highlights "hot") + tap to inspect.
struct DioDockTile: View {
    let prim: any DeskPrimitive; let hot: Bool; let onTap: () -> Void
    var body: some View {
        VStack(spacing: 6) {
            DioToolGlyph(prim: prim, size: 60)
                .scaleEffect(hot ? 1.12 : 1)
                .overlay(hot ? Circle().strokeBorder(DioPal.accent, lineWidth: 3).frame(width: 70, height: 70) : nil)
                .animation(.spring(response: 0.3, dampingFraction: 0.6), value: hot)
            Text(prim.title).font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.85)).lineLimit(1).frame(maxWidth: 78)
        }
        .contentShape(Rectangle()).onTapGesture(perform: onTap)
    }
}

// The COLLAPSED dock handle (the "Tools" pill with peek icons). The OPEN dock is drawn by the parent
// (DioStage) entirely in the GeometryReader's coordinate space — backdrop + header + tiles all share ONE
// space, the same one the drag-hit math uses, so nothing drifts apart from the safe-area inset (the old bug).
let kDioDockOpenHeight: CGFloat = 150
struct DioDockHandle: View {
    let tools: [any DeskPrimitive]; let onOpen: () -> Void
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "chevron.up").font(.system(size: 13, weight: .black)).foregroundStyle(DioPal.accent)
            Text("Tools").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            Spacer(minLength: 0)
            HStack(spacing: 9) { ForEach(Array(tools.prefix(5).enumerated()), id: \.element.id) { _, t in DioToolGlyph(prim: t, size: 28) } }
        }
        .padding(.horizontal, 18).frame(height: 56)
        .background(Capsule().fill(.white.opacity(0.08)).overlay(Capsule().strokeBorder(.white.opacity(0.13), lineWidth: 1))
            .shadow(color: .black.opacity(0.4), radius: 12, y: 4))
        .padding(.horizontal, 16).padding(.bottom, 14)
        .contentShape(Rectangle())
        .onTapGesture(perform: onOpen)
        .gesture(DragGesture(minimumDistance: 12).onEnded { if $0.translation.height < -20 { onOpen() } })    // swipe up to open
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
        .transition(.move(edge: .bottom).combined(with: .opacity))
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
    @State private var showSettings = false
    @State private var openMeeting: Meeting? = nil
    @State private var positions: [String: CGPoint] = [:]
    @State private var zones: [ZoneRec] = []
    @State private var filed: [String: String] = [:]
    @State private var dragHotZone: String? = nil
    @State private var namingZone = false
    @State private var newZoneName = ""
    // lasso → bundle → Ask (the Ask-AI atom): select many primitives, route them through the core together
    @State private var lassoStart: CGPoint? = nil
    @State private var lassoEnd: CGPoint? = nil
    @State private var selectedSet: Set<String> = []
    @State private var bundleTitle = ""
    @State private var bundleText = ""
    // workflows: saved Asks as reusable desk tools (drop a primitive → runs the saved prompt)
    @AppStorage("hs.diorama.workflows") private var workflowsJSON = ""
    @State private var workflows: [WorkflowRecord] = []
    @State private var savingTool = false
    @State private var toolName = ""
    @State private var pendingToolPrompt = ""
    // routing (the keystone: drag a primitive onto the AI core → LLM → a new primitive)
    @AppStorage("hs.diorama.outputs") private var outputsJSON = ""
    @State private var outputs: [OutputRecord] = []
    @State private var dragHotObjectId: String? = nil          // a compatible route target under a dragged primitive
    @State private var routeSourceId: String? = nil
    @State private var routeLensRun = ""
    @State private var showRouteSheet = false
    @State private var routing = false
    @State private var routeFrom: CGPoint = .zero
    @State private var routeTo: CGPoint = .zero
    @State private var printed: OutputRecord? = nil
    @State private var routeError: String? = nil
    // connectors (the integrations half: drop an output on Slack → approve → the MAC sends).
    // Routed through the paired host PC — the iPad holds no credential. Reuses the desk's Mac pairing.
    @AppStorage("hs.peer.host") private var peerHost = ""
    @AppStorage("hs.peer.port") private var peerPort = "8000"
    @State private var sendSourceId: String? = nil
    @State private var sendTargetName = ""
    @State private var sendTargetConn = "slack"          // which host connector ("slack" / "webhook")
    @State private var sendOverride: (title: String, text: String)? = nil   // act-on-item: send THIS, not a whole card
    @State private var actItem: (title: String, text: String, source: String)? = nil   // the row being acted on
    @State private var showActSheet = false
    @State private var showSendCard = false
    @State private var sending = false
    @State private var connecting = false
    @State private var connectURL = ""
    @State private var sentToast: String? = nil
    @State private var summonSource: String? = nil       // the card being routed (radial summon active)
    @State private var summonAt: CGPoint = .zero          // where the radial centers (the card's position)
    private let diveSpring = Animation.spring(response: 0.6, dampingFraction: 0.74)
    private let focusSpring = Animation.spring(response: 0.5, dampingFraction: 0.72)
    private let dockSpring = Animation.spring(response: 0.5, dampingFraction: 0.84)

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
    private func childZones() -> [ZoneRec] { zones.filter { parent(of: $0.path) == pathKey } }
    // a fresh desk: at root with nothing you've captured yet (tools like the AI core are always present)
    private var firstRun: Bool { path.isEmpty && contentMembers().isEmpty && childZones().isEmpty }
    // a place you dived into that holds nothing yet — teach how to fill it, don't dead-end
    private var emptyZone: Bool { !path.isEmpty && contentMembers().isEmpty && childZones().isEmpty }

    private var meetings: [Meeting] { model.meetings.sorted { $0.startedAt > $1.startedAt } }
    private var knowledgeBases: [String] { kbsCSV.split(separator: ";").map(String.init).filter { !$0.isEmpty } }
    private func kbCount(_ n: String) -> Int {
        kbFiledCSV.split(separator: ";").compactMap { p -> String? in let kv = p.split(separator: "=", maxSplits: 1); return kv.count == 2 ? String(kv[1]) : nil }.filter { $0 == n }.count
    }

    // EVERYTHING is a DeskPrimitive — built here from the live model.
    // CONTENT lives on the desk (meetings, generated outputs, knowledge); TOOLS live in the dock.
    private func contentMembers() -> [any DeskPrimitive] {
        var out: [any DeskPrimitive] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == pathKey { out.append(MeetingPrimitive(meeting: m, index: i)) }
        for rec in outputs where rec.path == pathKey { out.append(OutputPrimitive(rec: rec)) }
        if path.isEmpty { for kb in knowledgeBases.prefix(3) { out.append(KBPrimitive(name: kb, items: kbCount(kb))) } }
        return out
    }
    private func toolMembers() -> [any DeskPrimitive] {
        // tools are GLOBAL — the AI core / connectors / workflows live in the dock at EVERY level, not just
        // the root. (Owner walk: "under the main pane the tools toolbar loses its stuff" — it was root-gated.)
        var out: [any DeskPrimitive] = []
        for mdl in ModelFiles.installed().prefix(2) {
            out.append(ModelPrimitive(modelId: mdl.id, name: mdl.name.replacingOccurrences(of: ".gguf", with: "")))
        }
        out.append(ConnectorPrimitive(connId: "slack", name: "Slack", symbol: "number", tint: DioPal.violet,
                                      configured: hostLink != nil, detail: peerHost.isEmpty ? "" : peerHost))
        out.append(ConnectorPrimitive(connId: "webhook", name: "Webhook", symbol: "bolt.horizontal.fill", tint: DioPal.cobalt,
                                      configured: hostLink != nil, detail: peerHost.isEmpty ? "" : peerHost))
        out.append(ConnectorPrimitive(connId: "github", name: "GitHub", symbol: "exclamationmark.bubble.fill", tint: DioPal.mint,
                                      configured: hostLink != nil, detail: peerHost.isEmpty ? "" : peerHost))
        for wf in workflows { out.append(WorkflowPrimitive(rec: wf)) }
        return out
    }
    private func members() -> [any DeskPrimitive] { contentMembers() + toolMembers() }
    private var hostLink: DeskHostLink? {
        let h = peerHost.trimmingCharacters(in: .whitespaces)
        guard !h.isEmpty, let p = Int(peerPort.trimmingCharacters(in: .whitespaces)), p > 0 else { return nil }
        return DeskHostLink(host: h, port: p)
    }
    private func membersOf(_ zpath: String) -> [any DeskPrimitive] {
        var out: [any DeskPrimitive] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == zpath { out.append(MeetingPrimitive(meeting: m, index: i)) }
        return out
    }
    private func meeting(forObj id: String) -> Meeting? {
        guard id.hasPrefix("m:") else { return nil }
        let mid = String(id.dropFirst(2)); return model.meetings.first { $0.id == mid }
    }
    private func selectedPrim() -> (any DeskPrimitive)? { members().first { $0.id == selected } }
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
        if selected == id { return CGPoint(x: w * 0.24, y: h * 0.44) }
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
                // the desk surface: a tap deselects/climbs out; a drag on empty space LASSOS objects into a bundle
                Color.clear.contentShape(Rectangle())
                    .gesture(
                        DragGesture(minimumDistance: 0)
                            .onChanged { v in
                                if selected != nil { select(nil) }
                                lassoStart = v.startLocation; lassoEnd = v.location
                                if hypot(v.translation.width, v.translation.height) > 12 {
                                    selectedSet = primitivesIn(lassoRect(), contentMembers(), w, h)
                                }
                            }
                            .onEnded { v in
                                let moved = hypot(v.translation.width, v.translation.height)
                                lassoStart = nil; lassoEnd = nil
                                if moved < 12 {                       // a tap, not a lasso
                                    if !selectedSet.isEmpty { selectedSet = [] }
                                    else if selected != nil { select(nil) }
                                    else if !path.isEmpty { climbOut() }
                                }
                            }
                    )

                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 25, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("drag a meeting onto a zone · tap to open")
                        .font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                }
                .opacity(landed && selected == nil && path.isEmpty && !firstRun ? 1 : 0)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.05)

                // THE FIRST BOOT — the cold-start ritual: an empty desk that teaches itself
                if firstRun && landed && selected == nil && summonSource == nil {
                    DioFirstBoot(w: w, h: h)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.035).transition(.opacity).zIndex(5)
                    // the guiding trail — energy flows down from the lesson to the one action
                    TimelineView(.animation) { tl in
                        let phase = tl.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: 1) * -10
                        Path { p in p.move(to: CGPoint(x: w * 0.5, y: h * 0.50)); p.addLine(to: CGPoint(x: w * 0.5, y: h * 0.735)) }
                            .stroke(LinearGradient(colors: [DioPal.violet.opacity(0.0), DioPal.violet.opacity(0.55), DioPal.accent.opacity(0.8)], startPoint: .top, endPoint: .bottom),
                                    style: StrokeStyle(lineWidth: 2, lineCap: .round, dash: [2.5, 8], dashPhase: phase))
                    }
                    .allowsHitTesting(false).zIndex(5)
                    Text("Press to record your first meeting")
                        .font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        .position(x: w * 0.5, y: h * 0.745).zIndex(6).allowsHitTesting(false)
                }

                // an empty zone you dived into — teach how to fill it (you file from the desk; or nest deeper)
                if emptyZone && landed && selected == nil {
                    DioZoneEmpty(name: name(of: pathKey), tint: curTint, onNewSubzone: { haptic(.light); namingZone = true })
                        .frame(maxWidth: .infinity, maxHeight: .infinity).zIndex(5).transition(.opacity)
                }

                ForEach([pathKey], id: \.self) { _ in level(w, h) }
                    .transition(diveTransition)

                // the live lasso rectangle while dragging on empty desk
                if let r = lassoStart, let e = lassoEnd, hypot(e.x - r.x, e.y - r.y) > 12 {
                    let rect = lassoRect()
                    RoundedRectangle(cornerRadius: 16).strokeBorder(DioPal.accent.opacity(0.85), style: StrokeStyle(lineWidth: 2, dash: [7, 6]))
                        .background(RoundedRectangle(cornerRadius: 16).fill(DioPal.accent.opacity(0.06)))
                        .frame(width: rect.width, height: rect.height).position(x: rect.midX, y: rect.midY)
                        .allowsHitTesting(false).zIndex(40)
                }
                // the bundle bar: Ask the selected primitives together
                if !selectedSet.isEmpty && selected == nil && !showRouteSheet && !routing {
                    HStack(spacing: 12) {
                        Text("\(selectedSet.count) selected").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        Button { askBundle(w, h) } label: {
                            HStack(spacing: 7) { Image(systemName: "wand.and.stars").font(.system(size: 14, weight: .bold)); Text("Ask AI about these").font(.system(size: 14.5, weight: .heavy, design: .rounded)) }
                                .foregroundStyle(.white).padding(.horizontal, 18).frame(height: 46)
                                .background(Capsule().fill(LinearGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent], startPoint: .top, endPoint: .bottom)))
                        }.buttonStyle(.plain)
                        Button { selectedSet = [] } label: { Text("Clear").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).padding(.horizontal, 14).frame(height: 46).background(Capsule().fill(.white.opacity(0.06))) }.buttonStyle(.plain)
                    }
                    .padding(.horizontal, 16).padding(.vertical, 8).background(Capsule().fill(.black.opacity(0.6)))
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom).padding(.bottom, h * 0.12).zIndex(116)
                }

                DioCompanion(landed: landed, excited: selected != nil).position(x: w * 0.9, y: h * 0.86)
                if landed && selected == nil && summonSource == nil && !capturing {
                    DioRecordOrb { startCapture() }.position(x: w * 0.5, y: h * 0.8).transition(.scale.combined(with: .opacity))
                }
                // a desk-native settings entry (no bouncing to an old screen)
                if landed && selected == nil && summonSource == nil && !capturing && path.isEmpty {
                    Button { haptic(.light); showSettings = true } label: {
                        Image(systemName: "gearshape.fill").font(.system(size: 16, weight: .bold)).foregroundStyle(DioPal.text.opacity(0.85))
                            .frame(width: 42, height: 42).background(Circle().fill(.white.opacity(0.08)).overlay(Circle().strokeBorder(.white.opacity(0.12), lineWidth: 1)))
                    }.buttonStyle(.plain)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading).padding(.top, h * 0.045).padding(.leading, 18).zIndex(70)
                }
                // recording lives ON the desk now (not a separate window)
                if capturing {
                    DioRecordingConsole(model: model, onStop: { stopCapture() })
                        .transition(.opacity).zIndex(150)
                }

                // THE RADIAL SUMMON — long-press a card and its VALID tools bloom around it; tap one to route.
                // No drawer, no menu: the targets come to your finger, and only the tools that accept the card show.
                if let src = summonSource, let srcPrim = members().first(where: { $0.id == src }) {
                    let targets = summonTargets(for: srcPrim)
                    Color.black.opacity(0.55).ignoresSafeArea().contentShape(Rectangle())
                        .onTapGesture { dismissSummon() }.transition(.opacity).zIndex(118)
                    Circle().strokeBorder(DioPal.accent.opacity(0.9), lineWidth: 3)
                        .frame(width: srcPrim.base * 1.12, height: srcPrim.base * 1.12)
                        .shadow(color: DioPal.accent.opacity(0.7), radius: 14)
                        .position(summonAt).allowsHitTesting(false).zIndex(119)
                    if targets.isEmpty {
                        VStack(spacing: 6) {
                            Image(systemName: "tray").font(.system(size: 26)).foregroundStyle(DioPal.muted)
                            Text("No tool can take this yet").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                            Text("Add a model in Settings, or pair your Mac for connectors.").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).multilineTextAlignment(.center)
                        }.padding(18).background(RoundedRectangle(cornerRadius: 18).fill(.black.opacity(0.8)))
                        .frame(maxWidth: 280).position(x: w / 2, y: max(140, summonAt.y - 150)).zIndex(121)
                    } else {
                        ForEach(Array(targets.enumerated()), id: \.element.id) { i, t in
                            let p = summonPos(i, targets.count, summonAt, w, h)
                            Path { pa in pa.move(to: summonAt); pa.addLine(to: p) }
                                .stroke(t.color.opacity(0.55), style: StrokeStyle(lineWidth: 2, lineCap: .round, dash: [2, 6]))
                                .allowsHitTesting(false).zIndex(119)
                            DioSummonSatellite(prim: t, index: i) { routeFrom = summonAt; routeTo = p; let s = srcPrim; dismissSummon(); beginRoute(sourceId: s.id, target: t) }
                                .position(p).zIndex(122)
                        }
                        Text("tap a tool to route").font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                            .padding(.horizontal, 12).padding(.vertical, 6).background(Capsule().fill(.black.opacity(0.5)))
                            .position(x: w / 2, y: min(h - 36, summonAt.y + srcPrim.base * 0.7 + 26)).allowsHitTesting(false).zIndex(121)
                    }
                }

                RadialGradient(colors: [.clear, .clear, .black.opacity(0.5)], center: .center, startRadius: 160, endRadius: 800)
                    .blendMode(.multiply).allowsHitTesting(false)
                RadialGradient(colors: [curTint.opacity(flash), .clear], center: .center, startRadius: 10, endRadius: w)
                    .blendMode(.plusLighter).allowsHitTesting(false)

                if let p = selectedPrim() {
                    DioPullout(prim: p, onClose: { select(nil) }, onAction: { handle($0, on: p) },
                               onRouteSection: { t, x in routeFacet(t, x, w, h) },
                               onActItem: { task, text in beginActOnItem(from: p, task: task, text: text) })
                        .frame(width: min(560, w * 0.62))
                        .padding(.vertical, 22).padding(.trailing, 16)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                        .transition(.move(edge: .trailing).combined(with: .opacity)).zIndex(60)
                }

                if !path.isEmpty && selected == nil && !showRouteSheet && !routing && printed == nil && !showSendCard {
                    DioBackBar(crumbs: crumbs(), onBack: { climbOut() }, onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.045).zIndex(100)
                }

                // the keystone routing flow: sheet → theater → printed card (keep/bin)
                if showRouteSheet {
                    DioRouteSheet(sourceTitle: routeSourceTitle(),
                                  onAsk: { l, p in runRoute(lens: l, prompt: p) },
                                  onCancel: { withAnimation { showRouteSheet = false }; routeSourceId = nil },
                                  onSaveTool: { p in pendingToolPrompt = p; toolName = ""; withAnimation { showRouteSheet = false }; savingTool = true })
                        .zIndex(120)
                }
                if routing {
                    DioRoutingTheater(from: routeFrom, to: routeTo, sourceTitle: routeSourceTitle(),
                                      lens: routeLensRun, local: InferenceConfigStore.shared.isLocal, tint: DioPal.accent).zIndex(125)
                }
                if let rec = printed {
                    DioPrintedCard(rec: rec, onKeep: { keepPrinted() }, onBin: { binPrinted() }).zIndex(130)
                }
                if showSendCard {
                    let member = members().first(where: { $0.id == sendSourceId })
                    let sTitle = sendOverride?.title ?? member?.title
                    let sText = sendOverride?.text ?? member?.routableText
                    if let sTitle, let sText {
                        DioSendCard(sourceTitle: sTitle, preview: String(sText.prefix(220)), connName: sendTargetName, sending: sending,
                                    onApprove: { sendNow(title: sTitle, text: sText) },
                                    onCancel: { if !sending { withAnimation { showSendCard = false }; sendSourceId = nil; sendOverride = nil } }).zIndex(135)
                    }
                }
                if showActSheet, let item = actItem {
                    DioActSheet(itemText: item.text, connectors: actConnectors(), configured: hostLink != nil,
                                onSend: { cid, nm in actSend(connId: cid, name: nm) },
                                onFile: { actFile() },
                                onCancel: { withAnimation { showActSheet = false }; actItem = nil }).zIndex(136)
                }
                if let t = sentToast {
                    HStack(spacing: 7) { Image(systemName: "checkmark.circle.fill"); Text(t).font(.system(size: 13, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(.white).padding(.horizontal, 16).frame(height: 40).background(Capsule().fill(DioPal.mint.opacity(0.92)))
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, h * 0.04)
                        .transition(.move(edge: .top).combined(with: .opacity)).zIndex(200)
                }
            }
            .ignoresSafeArea()
            .onAppear { landed = true; load(); model.refresh()
                #if targetEnvironment(simulator)
                if let r = ProcessInfo.processInfo.environment["HS_DESK_RECORD"], r == "1" || r == "tape" || r == "modal" {
                    model.liveTranscript = "Welcome everyone to the Q3 kickoff. The big bet this quarter is shipping the desk to the web. Karol will own the mesh sync and the approval contract. We agreed to demo the air-gapped proof by Friday"
                    model.partial = "and then we will"
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { withAnimation { capturing = true }; model.recording = true; model.level = 0.6 }
                }
                if ProcessInfo.processInfo.environment["HS_DESK_SUMMON"] == "1" {
                    outputs = [OutputRecord(id: "demo", title: "Standup notes", body: "Shipped the egress badge; review the dock by Friday.", source: "Standup", lens: "Note", path: "")]
                    let b = UIScreen.main.bounds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
                        summonAt = CGPoint(x: b.width * 0.5, y: b.height * 0.5)
                        withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { summonSource = "out:demo" }
                    }
                }
                #endif
            }
            .alert("Couldn’t route", isPresented: Binding(get: { routeError != nil }, set: { if !$0 { routeError = nil } })) {
                Button("OK", role: .cancel) { routeError = nil }
            } message: { Text(routeError ?? "") }
            .alert("Pair your Mac", isPresented: $connecting) {
                TextField("host or host:port (e.g. 192.168.1.13:8000)", text: $connectURL)
                Button("Cancel", role: .cancel) {}
                Button("Save") { savePeer(connectURL) }
            } message: { Text("Your iPad sends through your Mac. The Slack credential stays on the Mac — the iPad never holds it.") }
            .alert("Save as a tool", isPresented: $savingTool) {
                TextField("Tool name (e.g. Risks, Brief)", text: $toolName)
                Button("Cancel", role: .cancel) { routeSourceId = nil }
                Button("Save") { saveTool(); routeSourceId = nil }
            } message: { Text("It becomes a tile on your desk. Drop a meeting or output on it to run this Ask again — no retyping.") }
            .alert("New zone", isPresented: $namingZone) {
                TextField("Name", text: $newZoneName)
                Button("Cancel", role: .cancel) { newZoneName = "" }
                Button("Create") { createZone(newZoneName); newZoneName = "" }
            } message: { Text(path.isEmpty ? "A place on your desk that holds meetings." : "A sub-zone inside \(name(of: pathKey)).") }
            .sheet(isPresented: Binding(get: { openMeeting != nil }, set: { if !$0 { openMeeting = nil } })) {
                if let m = openMeeting { NavigationStack { MeetingDetailView(meeting: m) }.preferredColorScheme(.dark) }
            }
            .sheet(isPresented: $showSettings) { NavigationStack { SettingsView() }.preferredColorScheme(.dark) }
        }
        .preferredColorScheme(.dark)
    }

    @ViewBuilder private func level(_ w: CGFloat, _ h: CGFloat) -> some View {
        let zs = childZones(); let ms = contentMembers()
        ZStack {
            ForEach(Array(zs.enumerated()), id: \.element.path) { i, z in
                DioZoneTray(name: name(of: z.path), tint: DioPal.zoneTints[z.color % DioPal.zoneTints.count],
                            members: membersOf(z.path), subZones: zones.filter { parent(of: $0.path) == z.path }.count,
                            size: CGSize(width: z.w, height: z.h), landed: landed, index: i, dimmed: selected != nil,
                            hot: dragHotZone == z.path, onDive: { dive(into: z.path) },
                            onMove: { tr in moveZone(z.path, tr, w, h) }, onResize: { tr in resizeZone(z.path, tr) })
                    .position(x: w * z.cx, y: h * z.cy)
            }
            if selected == nil && !firstRun && !emptyZone {
                Button { haptic(.light); namingZone = true } label: {
                    HStack(spacing: 6) { Image(systemName: "plus.circle.fill").font(.system(size: 14, weight: .bold)); Text("New Zone").font(.system(size: 12.5, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(DioPal.muted).padding(.horizontal, 12).frame(height: 36)
                        .background(Capsule().strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 5])).foregroundStyle(DioPal.muted.opacity(0.45)))
                }.buttonStyle(.plain).opacity(landed ? 0.9 : 0)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing).padding(.top, h * 0.12).padding(.trailing, 20)
            }

            ForEach(Array(ms.enumerated()), id: \.element.id) { i, p in
                DioHero(prim: p, landed: landed, mode: mode(p.id), index: i, pos: pos(p.id, looseHome(i, ms.count, w, h), w, h),
                        hot: dragHotObjectId == p.id, picked: selectedSet.contains(p.id),
                        onSummon: { summonAt = pos(p.id, looseHome(i, ms.count, w, h), w, h); haptic(.medium)
                                    withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { summonSource = p.id } },
                        onTap: { select(selected == p.id ? nil : p.id) },
                        onDrop: { tr in drop(p, looseHome(i, ms.count, w, h), tr, w, h) },
                        onDragChange: { pt in updateHot(p, pt, w, h) })
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

    private func handle(_ act: PrimitiveAction, on prim: any DeskPrimitive) {
        switch act.role {
        case .openEditor: if let m = meeting(forObj: prim.id) { openMeeting = m }
        case .custom("connect"): connectURL = peerHost.isEmpty ? "" : "\(peerHost):\(peerPort)"; select(nil); connecting = true
        case .route, .send, .custom: break
        }
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
        let n = childZones().count, col = n % 3, row = n / 3
        haptic(.medium)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) {
            zones.append(ZoneRec(path: zpath, color: zones.count, cx: 0.27 + 0.23 * Double(col), cy: 0.2 + 0.18 * Double(row), w: 168, h: 104))
        }
        persistZones()
    }
    private func moveZone(_ path: String, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        guard let idx = zones.firstIndex(where: { $0.path == path }) else { return }
        haptic(.light)
        zones[idx].cx = min(0.92, max(0.08, zones[idx].cx + Double(tr.width / w)))
        zones[idx].cy = min(0.84, max(0.1, zones[idx].cy + Double(tr.height / h)))
        persistZones()
    }
    private func resizeZone(_ path: String, _ tr: CGSize) {
        guard let idx = zones.firstIndex(where: { $0.path == path }) else { return }
        haptic(.light)
        zones[idx].w = min(360, max(120, zones[idx].w + Double(tr.width)))
        zones[idx].h = min(260, max(78, zones[idx].h + Double(tr.height)))
        persistZones()
    }
    private func dockToolPos(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let tile: CGFloat = 60, gap: CGFloat = 26
        let rowW = CGFloat(n) * tile + CGFloat(max(0, n - 1)) * gap
        let startX = (w - rowW) / 2 + tile / 2
        // sit in the panel's lower space, clear of the top header (panel is kDioDockOpenHeight tall)
        return CGPoint(x: startX + CGFloat(i) * (tile + gap), y: h - 78)
    }
    private func updateHot(_ p: any DeskPrimitive, _ pt: CGPoint?, _ w: CGFloat, _ h: CGFloat) {
        guard let pt = pt else { dragHotZone = nil; dragHotObjectId = nil; return }
        if let target = objectHit(pt, contentMembers(), w, h, excluding: p.id), target.prim.accepts.contains(p.kind) {
            dragHotObjectId = target.prim.id; dragHotZone = nil; return         // a desk content target (a KB)
        }
        dragHotObjectId = nil
        dragHotZone = (p.kind == .meeting) ? trayHit(pt, w, h) : nil
    }
    // the long-press menu for a primitive — the discoverable twin of drag-to-route / drag-to-send
    private func menuItems(for p: any DeskPrimitive, at center: CGPoint, _ w: CGFloat, _ h: CGFloat) -> [DioMenuItem] {
        var items: [DioMenuItem] = [DioMenuItem(label: "Open", icon: "arrow.up.left.and.arrow.down.right") { select(p.id) }]
        let ms = members()
        if let core = coreTarget(w, h) {
            items.append(DioMenuItem(label: "Route to AI core", icon: "wand.and.stars") {
                routeFrom = center; routeTo = core.center
                routeSourceId = p.id; haptic(.medium); withAnimation { showRouteSheet = true }
            })
        }
        for c in ms where c.kind == .connector && c.accepts.contains(p.kind) {
            let conn = (c as? ConnectorPrimitive)?.connId ?? "slack"
            items.append(DioMenuItem(label: "Send to \(c.title)", icon: "paperplane") {
                sendSourceId = p.id; sendTargetName = c.title; sendTargetConn = conn; haptic(.medium); withAnimation { showSendCard = true }
            })
        }
        if p.kind == .meeting {
            items.append(DioMenuItem(label: "Open full editor", icon: "rectangle.expand.vertical") { if let m = meeting(forObj: p.id) { openMeeting = m } })
        }
        return items
    }
    // act on one facet: route just this section (the summary, the actions…) through the AI core
    private func routeFacet(_ title: String, _ text: String, _ w: CGFloat, _ h: CGFloat) {
        guard let core = coreTarget(w, h) else {
            select(nil); routeError = "Add an on-device model (or pair an endpoint in Settings) to ask the AI."; return
        }
        bundleText = text; bundleTitle = title; routeSourceId = "__bundle__"
        routeTo = core.center
        routeFrom = CGPoint(x: w * 0.24, y: h * 0.24)
        select(nil)                                  // close the pull-out; the route sheet takes over
        haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { showRouteSheet = true }
    }
    private func routeSourceTitle() -> String {
        routeSourceId == "__bundle__" ? bundleTitle : (members().first { $0.id == routeSourceId }?.title ?? "the desk")
    }
    private func lassoRect() -> CGRect {
        guard let s = lassoStart, let e = lassoEnd else { return .zero }
        return CGRect(x: min(s.x, e.x), y: min(s.y, e.y), width: abs(e.x - s.x), height: abs(e.y - s.y))
    }
    private func primitivesIn(_ rect: CGRect, _ ms: [any DeskPrimitive], _ w: CGFloat, _ h: CGFloat) -> Set<String> {
        var out: Set<String> = []
        for (i, o) in ms.enumerated() where rect.contains(pos(o.id, looseHome(i, ms.count, w, h), w, h)) { out.insert(o.id) }
        return out
    }
    // the AI core's id + its dock position (the cable target for menu/bundle/facet routes)
    private func coreTarget(_ w: CGFloat, _ h: CGFloat) -> (id: String, center: CGPoint)? {
        let tm = toolMembers()
        guard let e = tm.enumerated().first(where: { $0.element.kind == .model }) else { return nil }
        return (e.element.id, dockToolPos(e.offset, tm.count, w, h))
    }
    // MARK: the radial summon — the tools that can take this card, blooming around it
    private func summonTargets(for src: any DeskPrimitive) -> [any DeskPrimitive] {
        toolMembers().filter { t in
            switch t.kind {
            case .model:     return true                          // the AI core takes anything
            case .connector: return true                          // connectors are valid targets (tap guides pairing)
            case .workflow:  return t.accepts.contains(src.kind)
            default:         return false
            }
        }
    }
    private func summonPos(_ i: Int, _ n: Int, _ center: CGPoint, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let r: CGFloat = 134
        let fan = min(CGFloat.pi * 1.25, CGFloat(max(1, n)) * 0.62)     // total spread, centered straight up
        let startA = -CGFloat.pi / 2 - fan / 2
        let a = startA + fan * (CGFloat(i) + 0.5) / CGFloat(max(1, n))
        let x = min(w - 62, max(62, center.x + r * cos(a)))
        let y = min(h - 96, max(100, center.y + r * sin(a)))
        return CGPoint(x: x, y: y)
    }
    private func dismissSummon() { haptic(.light); withAnimation(.spring(response: 0.4, dampingFraction: 0.82)) { summonSource = nil } }

    // recording on the desk (not a separate window): the console shows immediately, the mic starts, and
    // on stop the meeting weaves on-device and a fresh cassette lands on the desk.
    private func startCapture() {
        haptic(.medium)
        withAnimation(.spring(response: 0.45, dampingFraction: 0.82)) { capturing = true }
        Task { await model.startRecording() }
    }
    private func stopCapture() {
        haptic(.medium)
        Task {
            await model.stopRecording()
            model.refresh()
            withAnimation(.spring(response: 0.5, dampingFraction: 0.84)) { capturing = false }
        }
    }

    private func askBundle(_ w: CGFloat, _ h: CGFloat) {
        let cm = contentMembers()
        let picked = cm.enumerated().filter { selectedSet.contains($0.element.id) }
        guard !picked.isEmpty else { return }
        guard let core = coreTarget(w, h) else {
            routeError = "Add an on-device model (or pair an endpoint in Settings) to ask the AI."; return
        }
        bundleText = picked.map { "## \($0.element.title)\n\($0.element.routableText)" }.joined(separator: "\n\n")
        bundleTitle = "\(picked.count) items"
        let centers = picked.map { pos($0.element.id, looseHome($0.offset, cm.count, w, h), w, h) }
        routeFrom = CGPoint(x: centers.map(\.x).reduce(0, +) / CGFloat(centers.count),
                            y: centers.map(\.y).reduce(0, +) / CGFloat(centers.count))
        routeTo = core.center
        routeSourceId = "__bundle__"
        haptic(.medium)
        withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { showRouteSheet = true }
    }

    private func objectHit(_ pt: CGPoint, _ ms: [any DeskPrimitive], _ w: CGFloat, _ h: CGFloat, excluding: String) -> (prim: any DeskPrimitive, center: CGPoint)? {
        for (i, o) in ms.enumerated() where o.id != excluding {
            let c = pos(o.id, looseHome(i, ms.count, w, h), w, h)
            let s = o.base
            let rect = CGRect(x: c.x - s / 2, y: c.y - s / 2, width: s, height: s).insetBy(dx: -8, dy: -8)
            if rect.contains(pt) { return (o, c) }
        }
        return nil
    }
    private func trayHit(_ pt: CGPoint, _ w: CGFloat, _ h: CGFloat) -> String? {
        for z in childZones() {
            let c = CGPoint(x: w * z.cx, y: h * z.cy)
            let rect = CGRect(x: c.x - z.w / 2, y: c.y - z.h / 2, width: z.w, height: z.h).insetBy(dx: -14, dy: -14)
            if rect.contains(pt) { return z.path }
        }
        return nil
    }
    private func drop(_ p: any DeskPrimitive, _ fallback: CGPoint, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        let start = pos(p.id, fallback, w, h)
        let end = CGPoint(x: start.x + tr.width, y: start.y + tr.height)
        defer { dragHotZone = nil; dragHotObjectId = nil }
        // 1) dropped on a desk content target (a KB)?
        if let target = objectHit(end, contentMembers(), w, h, excluding: p.id), target.prim.accepts.contains(p.kind) {
            routeFrom = start; routeTo = target.center            // the cable runs source → target
            beginRoute(sourceId: p.id, target: target.prim); return
        }
        // 2) a meeting filed into a zone?
        if p.kind == .meeting, let z = trayHit(end, w, h) { file(p.id, into: z); return }
        // 3) free-place
        haptic(.light)
        let u = positions[p.id] ?? CGPoint(x: start.x / w, y: start.y / h)
        positions[p.id] = CGPoint(x: min(0.92, max(0.08, u.x + tr.width / w)), y: min(0.82, max(0.2, u.y + tr.height / h)))
        persistPositions()
    }

    // MARK: the intelligence engine — route a primitive through the AI core (or a KB)
    private func beginRoute(sourceId: String, target: any DeskPrimitive) {
        haptic(.medium)
        switch target.kind {
        case .model:                                            // the AI core → ask the LLM
            routeSourceId = sourceId
            withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { showRouteSheet = true }
        case .connector:                                        // a connector → propose→approve→send
            sendSourceId = sourceId; sendTargetName = target.title
            sendTargetConn = (target as? ConnectorPrimitive)?.connId ?? "slack"
            withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { showSendCard = true }
        case .workflow:                                         // a saved tool → run its prompt, no sheet
            guard let wf = target as? WorkflowPrimitive else { break }
            routeSourceId = sourceId
            runRoute(lens: wf.rec.name, prompt: wf.rec.prompt)
        default:
            #if canImport(UIKit)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            #endif
        }
    }
    // act on a single action row: turn it into tracked work (a connector) or keep it as a card
    private func beginActOnItem(from prim: any DeskPrimitive, task: String, text: String) {
        haptic(.light)
        actItem = (title: task, text: text, source: prim.title)
        withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { showActSheet = true }
    }
    private func actConnectors() -> [(connId: String, name: String, symbol: String, tint: Color)] {
        [("slack", "Slack", "number", DioPal.violet),
         ("github", "GitHub issue", "exclamationmark.bubble.fill", DioPal.mint),
         ("webhook", "Webhook", "bolt.horizontal.fill", DioPal.cobalt)]
    }
    private func actSend(connId: String, name: String) {
        guard let item = actItem else { return }
        withAnimation { showActSheet = false }
        sendTargetConn = connId; sendTargetName = name
        sendOverride = (title: item.title, text: item.text); sendSourceId = nil
        haptic(.medium)
        withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { showSendCard = true }
    }
    private func actFile() {
        guard let item = actItem else { return }
        withAnimation { showActSheet = false }
        let rec = OutputRecord(id: UUID().uuidString, title: String(item.title.prefix(48)), body: item.text,
                               source: item.source, lens: "Action", path: pathKey)
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(focusSpring) { outputs.append(rec) }
        persistOutputs(); actItem = nil
        toast("Kept on your desk")
    }
    private func sendNow(title: String, text: String) {
        guard let link = hostLink else {
            withAnimation { showSendCard = false }; sendOverride = nil; routeError = "Pair your Mac first — tap the \(sendTargetName) tile."; return
        }
        sending = true
        let target = sendTargetName
        Task { @MainActor in
            if await link.reachable() == false {
                sending = false; withAnimation { showSendCard = false }; sendOverride = nil
                routeError = "Your Mac isn’t reachable. Wake it and make sure it’s on the same network."
                return
            }
            do {
                // propose → approve → execute, all on the host (the credential never leaves the Mac)
                let proposal = try await link.propose(target: sendTargetConn, title: title, text: text)
                let decision = try await link.decide(target: sendTargetConn, id: proposal.id, approved: true)
                sending = false; withAnimation { showSendCard = false }; sendSourceId = nil; sendOverride = nil
                if decision.status == "executed" {
                    #if canImport(UIKit)
                    UINotificationFeedbackGenerator().notificationOccurred(.success)
                    #endif
                    toast("Sent to \(target) via your Mac")
                } else {
                    routeError = decision.error ?? "\(target) send didn’t complete (status: \(decision.status))."
                }
            } catch let DeskHostLink.HostError.message(m) {
                sending = false; withAnimation { showSendCard = false }; sendOverride = nil; routeError = m
            } catch {
                sending = false; withAnimation { showSendCard = false }; sendOverride = nil; routeError = "Couldn’t reach your Mac."
            }
        }
    }
    private func savePeer(_ raw: String) {
        let s = raw.trimmingCharacters(in: .whitespaces)
        guard !s.isEmpty else { return }
        if let colon = s.lastIndex(of: ":"), let p = Int(s[s.index(after: colon)...]), p > 0 {
            peerHost = String(s[..<colon]); peerPort = String(p)
        } else { peerHost = s }
    }
    private func toast(_ s: String) {
        withAnimation { sentToast = s }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.9) { withAnimation { if sentToast == s { sentToast = nil } } }
    }
    private func runRoute(lens: String, prompt: String) {
        withAnimation { showRouteSheet = false }
        let material: String, srcTitle: String
        if routeSourceId == "__bundle__" {
            material = String(bundleText.prefix(6000)); srcTitle = bundleTitle
        } else {
            guard let src = members().first(where: { $0.id == routeSourceId }) else { return }
            material = String(src.routableText.prefix(6000)); srcTitle = src.title
        }
        routeLensRun = lens
        let full = prompt + "\n\nMaterial:\n" + material
        let zpath = pathKey
        haptic(.heavy)
        withAnimation { routing = true }
        Task { @MainActor in
            let result = await callLLM(full)
            withAnimation { routing = false }
            switch result {
            case .success(let raw):
                let clean = raw.trimmingCharacters(in: .whitespacesAndNewlines)
                #if canImport(UIKit)
                UINotificationFeedbackGenerator().notificationOccurred(.success)
                #endif
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                    printed = OutputRecord(id: UUID().uuidString, title: lens, body: clean.isEmpty ? "(the model returned nothing)" : clean,
                                           source: srcTitle, lens: lens, path: zpath)
                }
                selectedSet = []
            case .failure(let e):
                routeError = friendly(e)
            }
        }
    }
    @MainActor private func callLLM(_ prompt: String) async -> Result<String, Error> {
        do {
            let cfg = InferenceConfigStore.shared
            let localPath = ModelFiles.installed().first { $0.url.lastPathComponent.lowercased().contains("mmproj") == false }?.url.path
            let provider = try cfg.makeProvider(localModelPath: localPath, context: 8192)
            let text = try await provider.complete(prompt: prompt)
            return .success(text)
        } catch { return .failure(error) }
    }
    private func friendly(_ e: Error) -> String {
        let cfg = InferenceConfigStore.shared
        if cfg.isLocal { return "No on-device model is loaded. Add one in Models, or point at an endpoint in Settings → where intelligence runs." }
        return "Couldn’t reach the endpoint. Check Settings → where intelligence runs (URL / model)."
    }
    private func keepPrinted() {
        guard let rec = printed else { return }
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(focusSpring) { outputs.append(rec); printed = nil }
        routeSourceId = nil; persistOutputs()
    }
    private func binPrinted() { haptic(.light); withAnimation { printed = nil }; routeSourceId = nil }
    private func file(_ id: String, into zpath: String) {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(focusSpring) { filed[id] = zpath; positions[id] = nil }
        persistFiled(); persistPositions()
    }

    private func persistPositions() { posCSV = positions.map { "\($0.key)=\($0.value.x),\($0.value.y)" }.joined(separator: ";") }
    private func persistZones() { zonesCSV = zones.map { "\($0.path)|\($0.color)|\($0.cx)|\($0.cy)|\($0.w)|\($0.h)" }.joined(separator: ";") }
    private func persistFiled() { dfiledCSV = filed.map { "\($0.key)=\($0.value)" }.joined(separator: ";") }
    private func persistOutputs() {
        if let data = try? JSONEncoder().encode(outputs), let s = String(data: data, encoding: .utf8) { outputsJSON = s }
    }
    private func persistWorkflows() {
        if let data = try? JSONEncoder().encode(workflows), let s = String(data: data, encoding: .utf8) { workflowsJSON = s }
    }
    private func saveTool() {
        let nm = toolName.trimmingCharacters(in: .whitespaces)
        guard !nm.isEmpty, !pendingToolPrompt.isEmpty else { return }
        haptic(.medium)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) {
            workflows.append(WorkflowRecord(id: UUID().uuidString, name: nm, prompt: pendingToolPrompt))
        }
        persistWorkflows()
    }
    private func load() {
        var pd: [String: CGPoint] = [:]
        for row in posCSV.split(separator: ";") {
            let kv = row.split(separator: "="); guard kv.count == 2 else { continue }
            let xy = kv[1].split(separator: ","); guard xy.count == 2, let x = Double(xy[0]), let y = Double(xy[1]) else { continue }
            pd[String(kv[0])] = CGPoint(x: x, y: y)
        }
        positions = pd
        zones = zonesCSV.split(separator: ";").enumerated().compactMap { idx, row in
            let f = row.split(separator: "|"); guard f.count >= 2, let ci = Int(f[1]) else { return nil }
            if f.count >= 6, let cx = Double(f[2]), let cy = Double(f[3]), let zw = Double(f[4]), let zh = Double(f[5]) {
                return ZoneRec(path: String(f[0]), color: ci, cx: cx, cy: cy, w: zw, h: zh)
            }
            // backward-compat: an old "path|color" zone gets a default frame
            let col = idx % 3, r = idx / 3
            return ZoneRec(path: String(f[0]), color: ci, cx: 0.27 + 0.23 * Double(col), cy: 0.2 + 0.18 * Double(r), w: 168, h: 104)
        }
        var fd: [String: String] = [:]
        for row in dfiledCSV.split(separator: ";") {
            let kv = row.split(separator: "=", maxSplits: 1); guard kv.count == 2 else { continue }
            fd[String(kv[0])] = String(kv[1])
        }
        filed = fd
        if let data = outputsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([OutputRecord].self, from: data) { outputs = arr }
        if let data = workflowsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([WorkflowRecord].self, from: data) { workflows = arr }
    }
}
