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

// MARK: - canvas object — derived ENTIRELY from a DeskPrimitive (glyph/colour/title/id). Gesture on the stable outer view.
struct DioHero: View {
    let prim: any DeskPrimitive; let landed: Bool; let mode: DioMode; let index: Int; let pos: CGPoint
    var hot: Bool = false                          // a compatible primitive is hovering over me → I'm a route target
    let onTap: () -> Void; let onDrop: (CGSize) -> Void; let onDragChange: (CGPoint?) -> Void
    @State private var drag: CGSize = .zero
    private var modeScale: CGFloat { hot ? 1.12 : (mode == .focus ? 1.34 : (mode == .recede ? 0.6 : 1)) }
    private var dim: Double { mode == .recede ? 0.3 : 1 }
    private let spring = Animation.spring(response: 0.5, dampingFraction: 0.72)
    var body: some View {
        let s = prim.base
        VStack(spacing: 7) {
            DioHeroVisual(glyph: prim.glyph, glow: prim.color, base: s, seed: prim.id, focused: mode == .focus, hot: hot).frame(width: s, height: s)
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
    }
}

struct DioHeroVisual: View {
    let glyph: String; let glow: Color; let base: CGFloat; let seed: String; let focused: Bool
    var hot: Bool = false
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
                DeskSprite(name: glyph, size: s)
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
struct DioZoneTray: View {
    let name: String, tint: Color
    let members: [any DeskPrimitive]; let subZones: Int; let size: CGSize
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
                    ForEach(Array(members.prefix(3).enumerated()), id: \.offset) { _, m in DioTrayMote(glyph: m.glyph) }
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
    let onClose: () -> Void; let onAction: (PrimitiveAction) -> Void
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
                VStack(alignment: .leading, spacing: 16) {
                    ForEach(Array(prim.sections.enumerated()), id: \.offset) { _, sec in
                        DrawerSection(label: sec.label, tint: sec.tint) { sectionBody(sec.body) }
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
    let sourceTitle: String; let onAsk: (String, String) -> Void; let onCancel: () -> Void
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
struct DioRoutingTheater: View {
    let sourceTitle: String; let lens: String; let local: Bool
    var body: some View {
        ZStack {
            Color.black.opacity(0.74).ignoresSafeArea()
            TimelineView(.animation) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                VStack(spacing: 22) {
                    ZStack {
                        ForEach(0..<3) { i in
                            let p = ((t * 0.7 + Double(i) * 0.33).truncatingRemainder(dividingBy: 1))
                            Circle().stroke(DioPal.accent.opacity(0.5 * (1 - p)), lineWidth: 2).frame(width: 90 + CGFloat(p) * 120, height: 90 + CGFloat(p) * 120)
                        }
                        Circle().fill(RadialGradient(colors: [Color(hex: 0xFFB070), DioPal.accent.opacity(0.7), .clear], center: .center, startRadius: 3, endRadius: 55))
                            .frame(width: 96, height: 96).scaleEffect(1 + CGFloat(sin(t * 2.4) * 0.06))
                        DeskSprite(name: "cartridge", size: 60).rotationEffect(.degrees(sin(t * 1.2) * 6))
                    }
                    VStack(spacing: 5) {
                        Text("Routing \(sourceTitle)").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text("\(lens) · \(local ? "on this iPad · no network" : "endpoint")").font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                    }
                }
            }
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
    // routing (the keystone: drag a primitive onto the AI core → LLM → a new primitive)
    @AppStorage("hs.diorama.outputs") private var outputsJSON = ""
    @State private var outputs: [OutputRecord] = []
    @State private var dragHotObjectId: String? = nil          // a compatible route target under a dragged primitive
    @State private var routeSourceId: String? = nil
    @State private var routeLensRun = ""
    @State private var showRouteSheet = false
    @State private var routing = false
    @State private var printed: OutputRecord? = nil
    @State private var routeError: String? = nil
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

    // EVERYTHING is a DeskPrimitive — built here from the live model.
    private func members() -> [any DeskPrimitive] {
        var out: [any DeskPrimitive] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == pathKey { out.append(MeetingPrimitive(meeting: m, index: i)) }
        for rec in outputs where rec.path == pathKey { out.append(OutputPrimitive(rec: rec)) }
        if path.isEmpty {
            for mdl in ModelFiles.installed().prefix(2) {
                out.append(ModelPrimitive(modelId: mdl.id, name: mdl.name.replacingOccurrences(of: ".gguf", with: "")))
            }
            for kb in knowledgeBases.prefix(3) { out.append(KBPrimitive(name: kb, items: kbCount(kb))) }
        }
        return out
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

                if let p = selectedPrim() {
                    DioPullout(prim: p, onClose: { select(nil) }, onAction: { handle($0, on: p) })
                        .frame(width: min(560, w * 0.62))
                        .padding(.vertical, 22).padding(.trailing, 16)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                        .transition(.move(edge: .trailing).combined(with: .opacity)).zIndex(60)
                }

                if !path.isEmpty && selected == nil && !showRouteSheet && !routing && printed == nil {
                    DioBackBar(crumbs: crumbs(), onBack: { climbOut() }, onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.045).zIndex(100)
                }

                // the keystone routing flow: sheet → theater → printed card (keep/bin)
                if showRouteSheet, let src = members().first(where: { $0.id == routeSourceId }) {
                    DioRouteSheet(sourceTitle: src.title,
                                  onAsk: { l, p in runRoute(lens: l, prompt: p) },
                                  onCancel: { withAnimation { showRouteSheet = false }; routeSourceId = nil })
                        .zIndex(120)
                }
                if routing {
                    DioRoutingTheater(sourceTitle: members().first(where: { $0.id == routeSourceId })?.title ?? "the desk",
                                      lens: routeLensRun, local: InferenceConfigStore.shared.isLocal).zIndex(125)
                }
                if let rec = printed {
                    DioPrintedCard(rec: rec, onKeep: { keepPrinted() }, onBin: { binPrinted() }).zIndex(130)
                }
            }
            .ignoresSafeArea()
            .onAppear { landed = true; load(); model.refresh() }
            .alert("Couldn’t route", isPresented: Binding(get: { routeError != nil }, set: { if !$0 { routeError = nil } })) {
                Button("OK", role: .cancel) { routeError = nil }
            } message: { Text(routeError ?? "") }
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

            ForEach(Array(ms.enumerated()), id: \.element.id) { i, p in
                DioHero(prim: p, landed: landed, mode: mode(p.id), index: i, pos: pos(p.id, looseHome(i, ms.count, w, h), w, h),
                        hot: dragHotObjectId == p.id,
                        onTap: { select(selected == p.id ? nil : p.id) },
                        onDrop: { tr in drop(p, looseHome(i, ms.count, w, h), tr, w, h) },
                        onDragChange: { pt in updateHot(p, pt, zs, slotN, w, h) })
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
        case .route, .send, .custom: break   // wired next (the keystone routing gesture)
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
        haptic(.medium)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) { zones.append((zpath, zones.count)) }
        persistZones()
    }
    private func updateHot(_ p: any DeskPrimitive, _ pt: CGPoint?, _ zs: [(path: String, color: Int)], _ slotN: Int, _ w: CGFloat, _ h: CGFloat) {
        guard let pt = pt else { dragHotZone = nil; dragHotObjectId = nil; return }
        if let target = objectHit(pt, members(), w, h, excluding: p.id), target.accepts.contains(p.kind) {
            dragHotObjectId = target.id; dragHotZone = nil; return    // a route target wins
        }
        dragHotObjectId = nil
        dragHotZone = (p.kind == .meeting) ? trayHit(pt, zs, slotN, w, h) : nil
    }
    private func objectHit(_ pt: CGPoint, _ ms: [any DeskPrimitive], _ w: CGFloat, _ h: CGFloat, excluding: String) -> (any DeskPrimitive)? {
        for (i, o) in ms.enumerated() where o.id != excluding {
            let c = pos(o.id, looseHome(i, ms.count, w, h), w, h)
            let s = o.base
            let rect = CGRect(x: c.x - s / 2, y: c.y - s / 2, width: s, height: s).insetBy(dx: -8, dy: -8)
            if rect.contains(pt) { return o }
        }
        return nil
    }
    private func trayHit(_ pt: CGPoint, _ zs: [(path: String, color: Int)], _ slotN: Int, _ w: CGFloat, _ h: CGFloat) -> String? {
        let size = shelfSize(slotN, w)
        for (i, z) in zs.enumerated() {
            let c = shelfPos(i, slotN, w, h)
            let rect = CGRect(x: c.x - size.width / 2, y: c.y - size.height / 2, width: size.width, height: size.height).insetBy(dx: -14, dy: -14)
            if rect.contains(pt) { return z.path }
        }
        return nil
    }
    private func drop(_ p: any DeskPrimitive, _ fallback: CGPoint, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        let start = pos(p.id, fallback, w, h)
        let end = CGPoint(x: start.x + tr.width, y: start.y + tr.height)
        defer { dragHotZone = nil; dragHotObjectId = nil }
        // 1) routed onto a compatible primitive (the AI core / a KB)?
        if let target = objectHit(end, members(), w, h, excluding: p.id), target.accepts.contains(p.kind) {
            beginRoute(sourceId: p.id, target: target); return
        }
        // 2) a meeting filed into a zone?
        let zs = childZones(); let slotN = zs.count + 1
        if p.kind == .meeting, let z = trayHit(end, zs, slotN, w, h) { file(p.id, into: z); return }
        // 3) free-place
        haptic(.light)
        let u = positions[p.id] ?? CGPoint(x: start.x / w, y: start.y / h)
        positions[p.id] = CGPoint(x: min(0.92, max(0.08, u.x + tr.width / w)), y: min(0.82, max(0.2, u.y + tr.height / h)))
        persistPositions()
    }

    // MARK: the intelligence engine — route a primitive through the AI core (or a KB)
    private func beginRoute(sourceId: String, target: any DeskPrimitive) {
        haptic(.medium)
        if target.kind == .model {                              // the AI core → ask the LLM
            routeSourceId = sourceId
            withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { showRouteSheet = true }
        } else {                                                // e.g. a KB → file into it (simple route for now)
            #if canImport(UIKit)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            #endif
        }
    }
    private func runRoute(lens: String, prompt: String) {
        withAnimation { showRouteSheet = false }
        guard let src = members().first(where: { $0.id == routeSourceId }) else { return }
        routeLensRun = lens
        let material = String(src.routableText.prefix(6000))
        let srcTitle = src.title
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
    private func persistZones() { zonesCSV = zones.map { "\($0.path)|\($0.color)" }.joined(separator: ";") }
    private func persistFiled() { dfiledCSV = filed.map { "\($0.key)=\($0.value)" }.joined(separator: ";") }
    private func persistOutputs() {
        if let data = try? JSONEncoder().encode(outputs), let s = String(data: data, encoding: .utf8) { outputsJSON = s }
    }
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
        if let data = outputsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([OutputRecord].self, from: data) { outputs = arr }
    }
}
