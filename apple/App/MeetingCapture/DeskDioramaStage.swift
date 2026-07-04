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
    // a richer ring zones can be painted from (the editor also allows a fully custom colour)
    static let zonePalette: [Color] = [accent, cobalt, violet, mint, Color(hex: 0xFF4D6D), Color(hex: 0xFFC857), Color(hex: 0x4DD0E1), Color(hex: 0xB388FF), Color(hex: 0x9CCC65), Color(hex: 0xF06292)]
    static func zoneColor(_ color: Int, _ hex: Int) -> Color { hex != 0 ? Color(hex: UInt(max(0, hex))) : zonePalette[color % zonePalette.count] }
}

enum DioMode { case home, focus, recede }

// THE SYNC STATUS — the framework, FELT on the desk. Driven by the `DeskSyncDriver` outcome
// + whether a Mac is paired. Premium + ambient, in the DioPal language: a quiet pill that
// breathes while syncing, settles to a calm "synced · 2m ago", goes muted when there's no
// peer, and flares honestly on error. NEVER a default spinner.
enum DeskSyncState: Equatable {
    case idle            // never run this session (paired, but no pass yet)
    case unpaired        // no Mac paired → nothing to sync to
    case syncing         // a pass is in flight
    case synced          // last pass reached the hub and applied/pushed cleanly
    case offline         // peer unreachable; the snapshot is queued for later
    case error(String)   // a pass threw (kept honest)

    var glyph: String {
        switch self {
        case .idle:     return "arrow.triangle.2.circlepath"
        case .unpaired: return "wifi.slash"
        case .syncing:  return "arrow.triangle.2.circlepath"
        case .synced:   return "checkmark.circle.fill"
        case .offline:  return "tray.and.arrow.up.fill"   // queued, will flush
        case .error:    return "exclamationmark.triangle.fill"
        }
    }
    var tint: Color {
        switch self {
        case .idle:     return DioPal.muted
        case .unpaired: return DioPal.muted
        case .syncing:  return DioPal.cobalt
        case .synced:   return DioPal.mint
        case .offline:  return DioPal.accent
        case .error:    return Color(hex: 0xFF6B6B)
        }
    }
    var spins: Bool { if case .syncing = self { return true } else { return false } }
}

// A relative "n ago" the status uses for its last-synced caption (calm + human).
private func dioRelativeAgo(_ date: Date, now: Date = Date()) -> String {
    let s = max(0, Int(now.timeIntervalSince(date)))
    if s < 8 { return "just now" }
    if s < 60 { return "\(s)s ago" }
    let m = s / 60
    if m < 60 { return "\(m)m ago" }
    let h = m / 60
    if h < 24 { return "\(h)h ago" }
    return "\(h / 24)d ago"
}

// The desk's sync chip: a tap-to-sync pill that wears the live state. Ambient, breathing,
// honest — and it carries the egress reality (bits port to your paired Mac on your LAN).
struct DioSyncStatus: View {
    let state: DeskSyncState
    let lastSyncedAt: Date?
    let peerLabel: String          // e.g. "192.168.1.13" — shown only when paired
    let onSync: () -> Void
    @State private var pressed = false

    private var caption: String {
        switch state {
        case .idle:     return "Tap to sync"
        case .unpaired: return "No desktop paired"
        case .syncing:  return "Syncing…"
        case .synced:   return lastSyncedAt.map { "Synced · \(dioRelativeAgo($0))" } ?? "Synced"
        case .offline:  return "Offline · queued"
        case .error(let m): return m.isEmpty ? "Sync failed" : m
        }
    }
    private var title: String {
        switch state {
        case .unpaired: return "Sync"
        case .syncing:  return "Sync"
        case .synced:   return "Synced"
        case .offline:  return "Queued"
        case .error:    return "Sync error"
        case .idle:     return "Sync"
        }
    }
    var body: some View {
        let tint = state.tint
        Button(action: onSync) {
            TimelineView(.animation(paused: !state.spins)) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                let breathe = state.spins ? (0.55 + 0.45 * (0.5 + 0.5 * sin(t * 3.0))) : 1.0
                HStack(spacing: 9) {
                    ZStack {
                        Circle().fill(tint.opacity(0.16))
                            .overlay(Circle().strokeBorder(tint.opacity(state.spins ? 0.55 * breathe : 0.4), lineWidth: 1.2))
                            .frame(width: 30, height: 30)
                        if state.spins {
                            Circle().trim(from: 0, to: 0.7)
                                .stroke(tint, style: StrokeStyle(lineWidth: 2.2, lineCap: .round))
                                .frame(width: 30, height: 30)
                                .rotationEffect(.degrees(t * 220))
                        }
                        Image(systemName: state.glyph)
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(tint)
                            .opacity(state.spins ? 0.9 : 1)
                    }
                    VStack(alignment: .leading, spacing: 1) {
                        Text(title).font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text(caption).font(.system(size: 9.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                }
                .padding(.leading, 8).padding(.trailing, 13).frame(height: 46)
                .background(
                    Capsule().fill(.white.opacity(0.07))
                        .overlay(Capsule().strokeBorder(tint.opacity(state.spins ? 0.45 * breathe : 0.22), lineWidth: 1))
                        .shadow(color: tint.opacity(state == .synced || state.spins ? 0.28 : 0), radius: 9, y: 3)
                )
            }
        }
        .buttonStyle(.plain)
        .disabled(state.spins || state == .unpaired)
        .scaleEffect(pressed ? 0.96 : 1)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: pressed)
        .animation(.spring(response: 0.45, dampingFraction: 0.8), value: state)
        .simultaneousGesture(DragGesture(minimumDistance: 0)
            .onChanged { _ in if !pressed { pressed = true } }
            .onEnded { _ in pressed = false })
    }
}

// per-primitive sync cue — what's canonical (synced to your desktop) vs local-only / pending.
enum PrimSyncCue: Equatable {
    case synced          // confirmed canonical on the hub (this session) — calm mint dot
    case pending         // edited locally, not yet pushed/confirmed — amber ring
    case localOnly       // never syncs by design (games) — quiet, honest
    case none            // no peer / not applicable → show nothing
}

// A tiny, hushed corner mark on a card carrying its sync cue. A filled mint check = canonical
// on your desktop; a hollow amber ring = pending; a quiet slashed cloud = local-only (games).
struct SyncCueBadge: View {
    struct Spec { let glyph: String; let tint: Color; let filled: Bool; let breathes: Bool }
    let spec: Spec
    static func spec(_ cue: PrimSyncCue) -> Spec? {
        switch cue {
        case .synced:    return Spec(glyph: "checkmark", tint: DioPal.mint, filled: true, breathes: false)
        case .pending:   return Spec(glyph: "arrow.up", tint: DioPal.accent, filled: false, breathes: true)
        case .localOnly: return Spec(glyph: "iphone", tint: DioPal.muted, filled: false, breathes: false)
        case .none:      return nil
        }
    }
    var body: some View {
        TimelineView(.animation(paused: !spec.breathes)) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let pulse = spec.breathes ? (0.55 + 0.45 * (0.5 + 0.5 * sin(t * 2.4))) : 1.0
            ZStack {
                Circle().fill(spec.filled ? spec.tint : Color(hex: 0x12101A).opacity(0.92))
                    .overlay(Circle().strokeBorder(spec.tint.opacity(spec.filled ? 0 : 0.85 * pulse), lineWidth: 1.4))
                    .frame(width: 17, height: 17)
                    .shadow(color: spec.filled ? spec.tint.opacity(0.45) : .black.opacity(0.4), radius: spec.filled ? 4 : 2)
                Image(systemName: spec.glyph)
                    .font(.system(size: 8.5, weight: .black))
                    .foregroundStyle(spec.filled ? .white : spec.tint.opacity(0.95))
            }
            .opacity(spec.breathes ? pulse : 1)
        }
    }
}

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
                    Text("Nothing filed in \(name) yet").font(.system(size: 20, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("Drag a meeting here to file it.")
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
                    Text("Record your first meeting.").font(.system(size: 13, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
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
// The ZoneRec itself lives in Sources/RuntimeCore/Desk/DeskRecords.swift (HS-72-09), embedding the
// canonical `Directory` contract (identity + nesting); geometry/paint stays local. Only its SwiftUI
// paint resolution lives here.
extension ZoneRec {
    var tint: Color { DioPal.zoneColor(color, hex) }
}

// the resolved look handed to the tray renderer
struct ZoneStyle { let color: Color; let borderW: CGFloat; let borderStyle: Int; let fillStyle: Int; let fillOpacity: Double; let glow: Bool
    init(_ z: ZoneRec) { color = z.tint; borderW = CGFloat(z.borderW); borderStyle = z.borderStyle; fillStyle = z.fillStyle; fillOpacity = z.fillOpacity; glow = z.glow }
}

// MARK: - canvas object — derived ENTIRELY from a DeskPrimitive (glyph/colour/title/id). Gesture on the stable outer view.
struct DioHero: View {
    let prim: any DeskPrimitive; let landed: Bool; let mode: DioMode; let index: Int; let pos: CGPoint
    var hot: Bool = false                          // a compatible primitive is hovering over me → I'm a route target
    var picked: Bool = false                       // selected by the lasso (part of an Ask bundle)
    var arrived: Bool = false                      // just woven off a recording → glaringly highlighted for a beat
    var syncCue: PrimSyncCue = .none               // canonical (synced) vs local-only/pending — read on the card
    var densityScale: CGFloat = 1                    // the desk shrinks its objects as it fills (to a usability floor)
    var onSummon: () -> Void = {}                   // long-press → radial summon (route/send)
    let onTap: () -> Void; let onDrop: (CGSize) -> Void; let onDragChange: (CGPoint?) -> Void
    @State private var drag: CGSize = .zero
    @State private var didSummon = false        // the long-press fired the radial → swallow the trailing tap/drop
    private var modeScale: CGFloat { hot ? 1.12 : (mode == .focus ? 1.34 : (mode == .recede ? 0.6 : 1)) }
    private var dim: Double { mode == .recede ? 0.3 : 1 }
    private let spring = Animation.spring(response: 0.5, dampingFraction: 0.72)
    var body: some View {
        let s = prim.base * densityScale
        VStack(spacing: 7) {
            ZStack {
                // the "glaringly new" beat — a bright halo + pulsing ring + a NEW badge, just after it weaves
                if arrived {
                    TimelineView(.animation) { tl in
                        let r = 0.5 + 0.5 * sin(tl.date.timeIntervalSinceReferenceDate * 3.4)
                        ZStack {
                            Circle().fill(RadialGradient(colors: [DioPal.accent.opacity(0.5), .clear], center: .center, startRadius: 2, endRadius: s * 0.95)).frame(width: s * 2, height: s * 2).blur(radius: 10)
                            Circle().strokeBorder(DioPal.accent.opacity(0.7 + 0.3 * r), lineWidth: 3).frame(width: s * (1.18 + 0.1 * r), height: s * (1.18 + 0.1 * r))
                        }
                    }.allowsHitTesting(false)
                }
                DioHeroVisual(glyph: prim.glyph, glow: prim.color, base: s, seed: prim.id, focused: mode == .focus, hot: hot, symbol: prim.isSymbol, picked: picked).frame(width: s, height: s)
                if arrived && prim.kind == .artifact {
                    ConstellationEcho(tint: prim.color).frame(width: s * 0.9, height: s * 0.9).allowsHitTesting(false)   // riff 4: the deliverable keeps a faint star-map of where it came from
                }
                if arrived {
                    Text("NEW").font(.system(size: 9, weight: .black, design: .rounded)).tracking(1).foregroundStyle(.white)
                        .padding(.horizontal, 8).padding(.vertical, 3)
                        .background(Capsule().fill(DioPal.accent).shadow(color: DioPal.accent.opacity(0.7), radius: 6))
                        .offset(y: -s * 0.62).transition(.scale.combined(with: .opacity))
                }
                // the SUBTLE per-primitive sync cue: a corner mark for what's canonical (synced to
                // your desktop) vs local-only / pending. Hushed by design — and yields to the NEW halo.
                if !arrived && mode != .recede, let badge = SyncCueBadge.spec(syncCue) {
                    SyncCueBadge(spec: badge).offset(x: s * 0.40, y: -s * 0.40)
                        .transition(.scale.combined(with: .opacity))
                }
            }
            Text(prim.title).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.85))
                .lineLimit(1).frame(maxWidth: s + 36)
                .padding(.horizontal, 8).padding(.vertical, 3)
                .background(Capsule().fill(.black.opacity(0.32)))
                .opacity(mode == .recede ? 0.0 : 0.95)
        }
        .scaleEffect(landed ? (drag == .zero ? (arrived ? modeScale * 1.12 : modeScale) : modeScale * 1.08) : 0.15)
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
                    // a long-press already bloomed the radial — don't ALSO select/route on finger-up
                    // (the trap that opened the pull-out behind the summon overlay).
                    if didSummon { didSummon = false; drag = .zero; return }
                    if mode != .recede { if d < 9 { onTap() } else { onDrop(v.translation) } }
                    drag = .zero
                }
        )
        .simultaneousGesture(LongPressGesture(minimumDuration: 0.32).onEnded { _ in if mode != .recede { didSummon = true; onSummon() } })
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

// MARK: - The lane (HSM-20-02) — the desk at compact width as a one-thumb card column.
// The diorama is a place; the lane is the same place shrunk to thumb-reach. Every primitive that
// exists on the wide desk has a row here (nothing is hidden between sizes); `positions[id]` is
// never touched, so rotating back to `.wide` restores the exact hand-arranged desk.

/// A primitive's glyph at a fixed lane size — the same sprite-vs-SF-symbol logic as `DioHeroVisual`,
/// drawn flat (no bob/glow) so a column of them reads calmly.
struct DioLaneGlyph: View {
    let glyph: String; let tint: Color; let symbol: Bool; var size: CGFloat = 44
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.26, style: .continuous)
                .fill(LinearGradient(colors: [tint.opacity(0.20), Color(hex: 0x14121C)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: size * 0.26, style: .continuous).strokeBorder(tint.opacity(0.45), lineWidth: 1))
            if symbol {
                Image(systemName: glyph).font(.system(size: size * 0.42, weight: .bold)).foregroundStyle(.white)
            } else {
                DeskSprite(name: glyph, size: size * 0.92)
            }
        }.frame(width: size, height: size)
    }
}

/// One full-width row in the lane: glyph @44 · title · BADGE · subtitle · chevron. Tapping it does
/// exactly what tapping the canvas primitive does (notes/KBs edit in-world; everything else opens
/// the pull-out, which on the lane rises from the bottom edge).
struct DioLaneRow: View {
    let glyph: String; let tint: Color; let symbol: Bool
    let title: String; let badge: String; let subtitle: String
    var arrived: Bool = false
    let onTap: () -> Void
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 13) {
                DioLaneGlyph(glyph: glyph, tint: tint, symbol: symbol)
                VStack(alignment: .leading, spacing: 3) {
                    Text(title).font(.system(size: 16, weight: .heavy, design: .rounded))
                        .foregroundStyle(DioPal.text).lineLimit(1)
                    HStack(spacing: 6) {
                        Text(badge).font(.system(size: 9.5, weight: .black, design: .rounded)).tracking(0.6)
                            .foregroundStyle(tint).padding(.horizontal, 6).padding(.vertical, 2)
                            .background(Capsule().fill(tint.opacity(0.16)))
                        if !subtitle.isEmpty {
                            Text(subtitle).font(.system(size: 12, weight: .semibold, design: .rounded))
                                .foregroundStyle(DioPal.muted).lineLimit(1)
                        }
                    }
                }
                Spacer(minLength: 6)
                Image(systemName: "chevron.right").font(.system(size: 13, weight: .black)).foregroundStyle(DioPal.muted.opacity(0.7))
            }
            .padding(.horizontal, 14).padding(.vertical, 11)
            .background(RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(.white.opacity(0.05))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .strokeBorder(arrived ? DioPal.accent.opacity(0.8) : .white.opacity(0.09), lineWidth: arrived ? 2 : 1)))
        }.buttonStyle(.plain)
    }
}

/// A zone row in the lane — taps to dive in (the spatial nav, one-thumb). Mirrors `DioZoneTray`.
struct DioLaneZoneRow: View {
    let name: String; let tint: Color; let count: Int; let subZones: Int
    let onDive: () -> Void
    var body: some View {
        Button(action: onDive) {
            HStack(spacing: 13) {
                ZStack {
                    RoundedRectangle(cornerRadius: 12, style: .continuous).fill(tint.opacity(0.16))
                        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(tint.opacity(0.5), lineWidth: 1))
                    Image(systemName: subZones > 0 ? "square.stack.3d.up.fill" : "tray.full.fill")
                        .font(.system(size: 18, weight: .bold)).foregroundStyle(tint)
                }.frame(width: 44, height: 44)
                VStack(alignment: .leading, spacing: 3) {
                    Text(name).font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                    Text("ZONE · \(count) item\(count == 1 ? "" : "s")\(subZones > 0 ? " · +\(subZones)" : "")")
                        .font(.system(size: 10, weight: .black, design: .rounded)).tracking(0.6).foregroundStyle(tint)
                }
                Spacer(minLength: 6)
                Image(systemName: "chevron.right").font(.system(size: 13, weight: .black)).foregroundStyle(DioPal.muted.opacity(0.7))
            }
            .padding(.horizontal, 14).padding(.vertical, 11)
            .background(RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(tint.opacity(0.06))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(tint.opacity(0.22), lineWidth: 1)))
        }.buttonStyle(.plain)
    }
}

/// Compact inline "nothing filed yet" hint for an empty sub-zone on the lane. Sits at the TOP of the
/// column (above the always-present global toolkit rows) so it never lands on a row, and states the
/// truth: your content is empty here, the toolkit is global. (Device punch-list: the centred overlay
/// used to render on top of the connector rows.)
struct DioLaneEmptyHint: View {
    let name: String; let tint: Color; let onNewSubzone: () -> Void
    var body: some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(tint.opacity(0.5), style: StrokeStyle(lineWidth: 1.4, dash: [4, 4]))
                Image(systemName: "tray").font(.system(size: 18, weight: .regular)).foregroundStyle(tint.opacity(0.9))
            }.frame(width: 44, height: 44)
            VStack(alignment: .leading, spacing: 3) {
                Text("Nothing filed in \(name) yet").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                Text("Long-press any item to file it.").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
            }
            Spacer(minLength: 6)
            Button(action: onNewSubzone) {
                HStack(spacing: 5) {
                    Image(systemName: "plus.circle.fill").font(.system(size: 12, weight: .bold))
                    Text("Sub-zone").font(.system(size: 12, weight: .heavy, design: .rounded))
                }
                .foregroundStyle(.white).padding(.horizontal, 11).frame(height: 32)
                .background(Capsule().fill(LinearGradient(colors: [tint.opacity(0.95), tint.opacity(0.7)], startPoint: .top, endPoint: .bottom)))
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 14).padding(.vertical, 11)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous)
            .fill(tint.opacity(0.05))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(tint.opacity(0.20), lineWidth: 1)))
    }
}

/// A sticky kind-filter chip in the lane rail.
struct DioLaneChip: View {
    let label: String; let tint: Color; let active: Bool; let onTap: () -> Void
    var body: some View {
        Button(action: onTap) {
            Text(label).font(.system(size: 12.5, weight: .heavy, design: .rounded))
                .foregroundStyle(active ? .white : DioPal.muted)
                .padding(.horizontal, 13).frame(height: 32)
                .background(Capsule().fill(active ? tint.opacity(0.9) : .white.opacity(0.06))
                    .overlay(Capsule().strokeBorder(active ? .clear : .white.opacity(0.1), lineWidth: 1)))
        }.buttonStyle(.plain)
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
    let name: String; let style: ZoneStyle
    let members: [any DeskPrimitive]; let subZones: Int; let size: CGSize
    let landed: Bool; let index: Int; let dimmed: Bool; let hot: Bool
    let onDive: () -> Void; let onMove: (CGSize) -> Void; let onResize: (CGSize) -> Void; let onEdit: () -> Void
    @State private var drag: CGSize = .zero
    @State private var rsz: CGSize = .zero
    @State private var didEdit = false        // long-press opened the editor → swallow the trailing tap/drop
    private var tint: Color { style.color }
    var body: some View {
        let w = max(120, size.width + rsz.width), h = max(78, size.height + rsz.height)
        let cap = max(1, Int((w - 26) / 40))
        let dashes: [CGFloat]? = style.borderStyle == 1 ? [6, 5] : (style.borderStyle == 2 ? [1.5, 4] : nil)
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
                    Text(hot ? "DROP TO FILE" : "TAP TO DIVE · HOLD TO EDIT").font(.system(size: 9, weight: .heavy, design: .rounded)).tracking(1)
                }.foregroundStyle(tint.opacity(0.9)).lineLimit(1)
            }
            .padding(13).frame(width: w, height: h, alignment: .topLeading)
            .background(zoneBackground(w, h, dashes))
            .contentShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .gesture(DragGesture(minimumDistance: 6)                 // small floor so a long-press-to-edit isn't read as a drag
                .onChanged { drag = $0.translation }                 // track 1:1 — no implicit animation on the offset
                .onEnded { v in
                    let d = hypot(v.translation.width, v.translation.height)
                    // reset the local offset BEFORE committing the new position — otherwise the parent re-lays
                    // the zone at its new spot while this view still carries the drag offset (= a 1-frame JUMP).
                    let wasEdit = didEdit; didEdit = false; drag = .zero
                    if wasEdit { return }
                    if d < 9 { onDive() } else { onMove(v.translation) }
                })
            .simultaneousGesture(LongPressGesture(minimumDuration: 0.45, maximumDistance: 8).onEnded { _ in didEdit = true; haptic(); onEdit() })
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
        .animation(nil, value: drag)                                 // the drag must NOT lerp — it follows the finger
        .animation(.spring(response: 0.6, dampingFraction: 0.7), value: rsz)
        .animation(.spring(response: 0.65, dampingFraction: 0.62).delay(Double(index) * 0.06), value: landed)
        .animation(.spring(response: 0.35, dampingFraction: 0.6), value: hot)
        .allowsHitTesting(!dimmed)
    }
    @ViewBuilder private func zoneBackground(_ w: CGFloat, _ h: CGFloat, _ dashes: [CGFloat]?) -> some View {
        let shape = RoundedRectangle(cornerRadius: 20, style: .continuous)
        let op = hot ? max(style.fillOpacity, 0.2) : style.fillOpacity
        ZStack {
            // base fill by pattern
            switch style.fillStyle {
            case 0: shape.fill(LinearGradient(colors: [tint.opacity(op * 1.5), DioPal.trayBot.opacity(0.9)], startPoint: .top, endPoint: .bottom))
            default:
                shape.fill(DioPal.trayBot.opacity(0.9))
                if style.fillStyle == 1 { shape.fill(tint.opacity(op)) }
                else { ZonePattern(kind: style.fillStyle, color: tint.opacity(min(0.9, op * 2.4))).clipShape(shape) }
            }
            shape.strokeBorder(tint.opacity(hot ? 1 : 0.6), style: StrokeStyle(lineWidth: hot ? style.borderW + 1 : style.borderW, dash: dashes ?? []))
        }
        .shadow(color: (style.glow ? tint : .black).opacity(style.glow ? 0.55 : 0.4), radius: style.glow ? 16 : 12, y: 8)
    }
    private func haptic() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred()
        #endif
    }
}

// hatch / dots / grid fills painted into a zone
struct ZonePattern: View {
    let kind: Int; let color: Color    // 2 hatch · 3 dots · 4 grid
    var body: some View {
        Canvas { ctx, size in
            let step: CGFloat = 12
            if kind == 2 {            // diagonal hatch
                var x: CGFloat = -size.height
                while x < size.width { var p = Path(); p.move(to: CGPoint(x: x, y: size.height)); p.addLine(to: CGPoint(x: x + size.height, y: 0)); ctx.stroke(p, with: .color(color), lineWidth: 1); x += step }
            } else if kind == 3 {     // dots
                var y: CGFloat = step / 2
                while y < size.height { var x: CGFloat = step / 2; while x < size.width { ctx.fill(Path(ellipseIn: CGRect(x: x - 1, y: y - 1, width: 2, height: 2)), with: .color(color)); x += step }; y += step }
            } else {                  // grid
                var x: CGFloat = 0; while x < size.width { var p = Path(); p.move(to: CGPoint(x: x, y: 0)); p.addLine(to: CGPoint(x: x, y: size.height)); ctx.stroke(p, with: .color(color.opacity(0.6)), lineWidth: 0.6); x += step }
                var y: CGFloat = 0; while y < size.height { var p = Path(); p.move(to: CGPoint(x: 0, y: y)); p.addLine(to: CGPoint(x: size.width, y: y)); ctx.stroke(p, with: .color(color.opacity(0.6)), lineWidth: 0.6); y += step }
            }
        }
    }
}

// THE ZONE STYLE EDITOR — paint a place: colour (palette or fully custom), border width + style, fill
// pattern + opacity, glow. Long-press a zone to open it. Live preview swatch on top.
// THE ZONE STUDIO — the zone itself is the hero: it lifts to focus, big and LIVE, and you paint it with a
// real colour spectrum + curated looks. In-world, direct, premium (no detached settings form).
struct ZoneLook { let name: String; let fill: Int; let edge: Int; let bw: Double; let op: Double; let glow: Bool }
struct DioZoneEditor: View {
    @State var zone: ZoneRec
    let name: String
    var maxW: CGFloat = 380   // clamped by the caller's DeskCamera so it fits the lane (HSM-20-02)
    let onSave: (ZoneRec) -> Void; let onDelete: () -> Void; let onCancel: () -> Void
    @State private var hue: Double = 0
    private var tint: Color { zone.tint }
    private static let looks: [ZoneLook] = [
        .init(name: "Glass", fill: 0, edge: 0, bw: 1.5, op: 0.14, glow: false),
        .init(name: "Outline", fill: 0, edge: 0, bw: 3, op: 0.07, glow: false),
        .init(name: "Dashed", fill: 0, edge: 1, bw: 2, op: 0.1, glow: false),
        .init(name: "Hatch", fill: 2, edge: 0, bw: 1.5, op: 0.22, glow: false),
        .init(name: "Dots", fill: 3, edge: 2, bw: 1.5, op: 0.2, glow: false),
        .init(name: "Grid", fill: 4, edge: 0, bw: 1.5, op: 0.18, glow: false),
        .init(name: "Neon", fill: 0, edge: 0, bw: 2.5, op: 0.24, glow: true),
    ]
    var body: some View {
        ZStack {
            Color.black.opacity(0.78).ignoresSafeArea().onTapGesture { onSave(zone) }   // focus: dim the desk
            RadialGradient(colors: [tint.opacity(0.16), .clear], center: .center, startRadius: 4, endRadius: 360)
                .ignoresSafeArea().allowsHitTesting(false)                              // a soft spotlight on the lifted zone
            VStack(spacing: 26) {
                // THE HERO — the actual zone, large + live, lifted into focus, casting its own glow
                heroZone.frame(width: maxW, height: 188)
                    .overlay(alignment: .topLeading) {
                        HStack(spacing: 7) {
                            Image(systemName: "square.dashed").font(.system(size: 12, weight: .bold)).foregroundStyle(tint)
                            Text(name).font(.system(size: 16, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                        }.padding(16)
                    }
                    .scaleEffect(1.0)
                VStack(spacing: 20) {
                    // a real continuous COLOUR SPECTRUM — drag to paint any hue
                    VStack(alignment: .leading, spacing: 8) {
                        Text("COLOUR").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1.6).foregroundStyle(DioPal.muted)
                        GeometryReader { g in
                            ZStack(alignment: .leading) {
                                Capsule().fill(LinearGradient(colors: Self.spectrum, startPoint: .leading, endPoint: .trailing)).frame(height: 22)
                                    .overlay(Capsule().strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
                                Circle().fill(tint).overlay(Circle().strokeBorder(.white, lineWidth: 3)).frame(width: 30, height: 30)
                                    .shadow(color: .black.opacity(0.45), radius: 4, y: 1)
                                    .offset(x: hue * (g.size.width - 30))
                            }
                            .contentShape(Rectangle())
                            .gesture(DragGesture(minimumDistance: 0).onChanged { v in
                                hue = min(1, max(0, v.location.x / max(1, g.size.width - 30)))
                                zone.hex = max(1, zoneHex(Color(hue: hue, saturation: 0.72, brightness: 0.96)))
                            })
                        }.frame(height: 30)
                    }
                    // curated LOOKS — tap to apply a whole style, keeping the colour
                    VStack(alignment: .leading, spacing: 8) {
                        Text("LOOK").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1.6).foregroundStyle(DioPal.muted)
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 13) {
                                ForEach(Array(Self.looks.enumerated()), id: \.offset) { _, lk in
                                    let on = zone.fillStyle == lk.fill && zone.borderStyle == lk.edge && zone.glow == lk.glow && abs(zone.fillOpacity - lk.op) < 0.02
                                    Button { withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) { zone.fillStyle = lk.fill; zone.borderStyle = lk.edge; zone.borderW = lk.bw; zone.fillOpacity = lk.op; zone.glow = lk.glow }; haptic() } label: {
                                        VStack(spacing: 6) {
                                            styleSwatch(lk.fill, lk.edge, lk.bw, lk.glow, 80, 52, sel: on)
                                            Text(lk.name).font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(on ? DioPal.text : DioPal.muted)
                                        }
                                    }.buttonStyle(.plain)
                                }
                            }.padding(.horizontal, 2).padding(.vertical, 4)
                        }
                    }
                    HStack(spacing: 13) {
                        Button { onDelete() } label: {
                            HStack(spacing: 7) { Image(systemName: "trash"); Text("Delete").font(.system(size: 15, weight: .heavy, design: .rounded)) }
                                .foregroundStyle(Color(hex: 0xFF6B6B)).frame(maxWidth: .infinity).frame(height: 54).background(Capsule().fill(.white.opacity(0.06)))
                        }.buttonStyle(.plain)
                        Button { onSave(zone) } label: {
                            HStack(spacing: 8) { Image(systemName: "checkmark"); Text("Done").font(.system(size: 16.5, weight: .heavy, design: .rounded)) }
                                .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 54)
                                .background(Capsule().fill(LinearGradient(colors: [tint, tint.opacity(0.6)], startPoint: .top, endPoint: .bottom)))
                                .shadow(color: tint.opacity(0.45), radius: 10, y: 4)
                        }.buttonStyle(.plain)
                    }
                }
                .frame(width: maxW)
            }
            .padding(.vertical, 8)
        }
        .onAppear { hue = zone.hex != 0 ? hueOf(Color(hex: UInt(max(0, zone.hex)))) : 0 }
    }
    private static let spectrum: [Color] = (0..<8).map { Color(hue: Double($0) / 7, saturation: 0.72, brightness: 0.96) }
    // the hero — the real zone, large + live (mirrors the on-desk DioZoneTray look)
    private var heroZone: some View {
        let dashes: [CGFloat]? = zone.borderStyle == 1 ? [7, 5] : (zone.borderStyle == 2 ? [1.5, 5] : nil)
        let shape = RoundedRectangle(cornerRadius: 20, style: .continuous)
        return ZStack {
            if zone.fillStyle == 0 { shape.fill(LinearGradient(colors: [tint.opacity(zone.fillOpacity * 1.6), DioPal.trayBot.opacity(0.92)], startPoint: .top, endPoint: .bottom)) }
            else { shape.fill(DioPal.trayBot.opacity(0.92)); if zone.fillStyle == 1 { shape.fill(tint.opacity(zone.fillOpacity)) } else { ZonePattern(kind: zone.fillStyle, color: tint.opacity(min(0.9, zone.fillOpacity * 2.4))).clipShape(shape) } }
            shape.strokeBorder(tint.opacity(0.85), style: StrokeStyle(lineWidth: CGFloat(zone.borderW), dash: dashes ?? []))
        }
        .shadow(color: (zone.glow ? tint : .black).opacity(zone.glow ? 0.7 : 0.4), radius: zone.glow ? 22 : 12, y: 8)
    }
    private func styleSwatch(_ fill: Int, _ edge: Int, _ bw: Double, _ glow: Bool, _ w: CGFloat, _ h: CGFloat, sel: Bool) -> some View {
        let dashes: [CGFloat]? = edge == 1 ? [4, 3] : (edge == 2 ? [1, 3] : nil)
        let shape = RoundedRectangle(cornerRadius: 9, style: .continuous)
        return ZStack {
            if fill == 0 { shape.fill(LinearGradient(colors: [tint.opacity(0.5), DioPal.trayBot.opacity(0.9)], startPoint: .top, endPoint: .bottom)) }
            else { shape.fill(DioPal.trayBot.opacity(0.9)); if fill == 1 { shape.fill(tint.opacity(0.4)) } else { ZonePattern(kind: fill, color: tint.opacity(0.7)).clipShape(shape) } }
            shape.strokeBorder(tint.opacity(0.85), style: StrokeStyle(lineWidth: CGFloat(bw), dash: dashes ?? []))
        }
        .frame(width: w, height: h)
        .shadow(color: glow ? tint.opacity(0.6) : .clear, radius: glow ? 8 : 0)
        .overlay(sel ? RoundedRectangle(cornerRadius: 11, style: .continuous).strokeBorder(.white.opacity(0.95), lineWidth: 2).padding(-3) : nil)
    }
    private func hueOf(_ c: Color) -> Double {
        #if canImport(UIKit)
        var h: CGFloat = 0, s: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        UIColor(c).getHue(&h, saturation: &s, brightness: &b, alpha: &a)
        return Double(h)
        #else
        return 0
        #endif
    }
    private func zoneHex(_ c: Color) -> Int {
        #if canImport(UIKit)
        let ui = UIColor(c); var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        ui.getRed(&r, green: &g, blue: &b, alpha: &a)
        return (Int(r * 255) << 16) | (Int(g * 255) << 8) | Int(b * 255)
        #else
        return 0xFFFFFF
        #endif
    }
    private func haptic() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        #endif
    }
}

// THE SPEAK-TO-FILL MIC — the one building block behind "a mic on every input". Bind it to ANY
// String and it dictates into that field: tap → listen (a breathing ring) → tap → transcribe
// (on-device WhisperKit, fully local) → your words land (appended after existing text, or filling
// an empty field). It's a voice product; no field should be voiceless. Reuses VoiceCaptureState.
struct VoiceFillMic: View {
    @Binding var text: String
    var tint: Color = DioPal.mint
    var size: CGFloat = 30
    /// .append (default) adds after what's there; .replace overwrites — used where re-dictating
    /// the whole value is the natural intent (a short name field).
    enum Fill { case append, replace }
    var fill: Fill = .append
    @StateObject private var voice = VoiceCaptureState()
    @State private var pulse = false

    var body: some View {
        Button { tap() } label: {
            ZStack {
                Circle().fill(state == .idle ? Color.white.opacity(0.06) : tint.opacity(0.18))
                    .overlay(Circle().strokeBorder(tint.opacity(state == .idle ? 0.30 : 0.85),
                                                   lineWidth: state == .listening ? 2 : 1))
                if state == .listening {
                    Circle().strokeBorder(Color(hex: 0xFF4D6D).opacity(pulse ? 0.0 : 0.7), lineWidth: 2)
                        .scaleEffect(pulse ? 1.6 : 1.0)
                }
                switch state {
                case .transcribing:
                    ProgressView().controlSize(.mini).tint(tint)
                case .listening:
                    Image(systemName: "waveform").font(.system(size: size * 0.42, weight: .black))
                        .foregroundStyle(Color(hex: 0xFF4D6D))
                default:
                    Image(systemName: "mic.fill").font(.system(size: size * 0.42, weight: .black))
                        .foregroundStyle(tint)
                }
            }
            .frame(width: size, height: size)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(state == .listening ? "Stop dictation" : "Dictate")
        .disabled(state == .transcribing)
        .onAppear { pulse = false }
        .onChange(of: state) { _, s in
            if s == .listening { withAnimation(.easeOut(duration: 0.9).repeatForever(autoreverses: false)) { pulse = true } }
            else { pulse = false }
        }
        .onChange(of: voice.text) { _, said in
            let words = said.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !words.isEmpty else { return }
            let cur = text.trimmingCharacters(in: .whitespacesAndNewlines)
            if fill == .replace || cur.isEmpty { text = words }
            else { text = cur + (cur.hasSuffix("\n") ? "" : " ") + words }
            voice.text = ""   // consume so a future identical dictation still fires onChange
        }
    }

    private enum MicState { case idle, listening, transcribing }
    private var state: MicState {
        if voice.transcribing { return .transcribing }
        if voice.recording { return .listening }
        return .idle
    }
    private func tap() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        #endif
        if voice.recording { Task { await voice.stopAndTranscribe() } }
        else { Task { await voice.start() } }
    }
}

// A small primary "Done" pill — the in-world commit button shared by the inline editors.
struct DioDonePill: View {
    let tint: Color; let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) { Image(systemName: "checkmark").font(.system(size: 13, weight: .black)); Text("Done").font(.system(size: 14, weight: .heavy, design: .rounded)) }
                .foregroundStyle(.white).padding(.horizontal, 16).frame(height: 38)
                .background(Capsule().fill(LinearGradient(colors: [tint, tint.opacity(0.62)], startPoint: .top, endPoint: .bottom)))
                .shadow(color: tint.opacity(0.5), radius: 8, y: 3)
        }.buttonStyle(.plain)
    }
}

// THE IN-WORLD NOTE CARD — note editing happens ON THE DESK, in place, never in a dimmed modal.
// The card you tapped lifts where it sits (its own mint glow), shows a title + body you write or
// SPEAK (a mic on each field), and commits on Done or when you tap the desk. The parent owns the
// live draft (a Binding) so a tap-away commits exactly what's on screen.
struct DioInlineNoteCard: View {
    @Binding var note: NoteRecord
    let onDone: () -> Void; let onDelete: () -> Void
    @FocusState private var bodyFocused: Bool
    @FocusState private var titleFocused: Bool
    private let tint = DioPal.mint
    var body: some View {
        VStack(alignment: .leading, spacing: 11) {
            HStack(spacing: 9) {
                DeskSprite(name: "note", size: 24)
                Text("NOTE").font(.system(size: 10.5, weight: .black, design: .rounded)).tracking(2).foregroundStyle(tint)
                Spacer(minLength: 0)
                DioDonePill(tint: tint, action: onDone)
            }
            HStack(spacing: 8) {
                TextField("Title", text: $note.title)
                    .font(.system(size: 18, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    .textFieldStyle(.plain).focused($titleFocused)
                    .submitLabel(.next).onSubmit { bodyFocused = true }
                VoiceFillMic(text: $note.title, tint: tint, size: 28, fill: .replace)
            }
            Rectangle().fill(.white.opacity(0.08)).frame(height: 1)
            ZStack(alignment: .topLeading) {
                if note.body.isEmpty {
                    Text("Write or speak your note…").font(.system(size: 14.5, weight: .medium, design: .rounded))
                        .foregroundStyle(DioPal.muted.opacity(0.7)).padding(.top, 8).padding(.leading, 5).allowsHitTesting(false)
                }
                TextEditor(text: $note.body)
                    .font(.system(size: 14.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.text)
                    .scrollContentBackground(.hidden).background(.clear).focused($bodyFocused)
                    .frame(minHeight: 96, maxHeight: 168)
            }
            HStack(spacing: 12) {
                Button(action: onDelete) {
                    HStack(spacing: 6) { Image(systemName: "trash").font(.system(size: 12, weight: .bold)); Text("Delete").font(.system(size: 13, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(Color(hex: 0xFF6B6B).opacity(0.9))
                }.buttonStyle(.plain)
                Spacer(minLength: 0)
                HStack(spacing: 5) {
                    Text("dictate").font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                    VoiceFillMic(text: $note.body, tint: tint, size: 30, fill: .append)
                }
            }
        }
        .padding(16).frame(width: 304)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x1A1622), Color(hex: 0x100C18)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(tint.opacity(0.5), lineWidth: 1.5))
        )
        .shadow(color: tint.opacity(0.4), radius: 22, y: 8).shadow(color: .black.opacity(0.5), radius: 14, y: 10)
        .transition(.scale(scale: 0.9).combined(with: .opacity))
        .onAppear { if note.title.isEmpty { titleFocused = true } else { bodyFocused = true } }
    }
}

// THE IN-WORLD KB CARD — rename / delete a knowledge base in place on the desk (violet, matching
// the note card). Name it by typing or by voice; commit on Done or a tap-away.
struct DioInlineKBCard: View {
    @Binding var kb: KBRecord
    let onDone: () -> Void; let onDelete: () -> Void
    @FocusState private var nameFocused: Bool
    private let tint = DioPal.violet
    var body: some View {
        VStack(alignment: .leading, spacing: 11) {
            HStack(spacing: 9) {
                DeskSprite(name: "crystal", size: 26)
                Text("KNOWLEDGE BASE").font(.system(size: 10.5, weight: .black, design: .rounded)).tracking(1.6).foregroundStyle(tint)
                Spacer(minLength: 0)
                Text("\(kb.items) item\(kb.items == 1 ? "" : "s")").font(.system(size: 11.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
            }
            HStack(spacing: 8) {
                TextField("Name", text: $kb.name)
                    .font(.system(size: 18, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    .textFieldStyle(.plain).focused($nameFocused).submitLabel(.done).onSubmit(onDone)
                VoiceFillMic(text: $kb.name, tint: tint, size: 28, fill: .replace)
            }
            HStack(spacing: 12) {
                Button(action: onDelete) {
                    HStack(spacing: 6) { Image(systemName: "trash").font(.system(size: 12, weight: .bold)); Text("Delete").font(.system(size: 13, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(Color(hex: 0xFF6B6B).opacity(0.9))
                }.buttonStyle(.plain)
                Spacer(minLength: 0)
                DioDonePill(tint: tint, action: onDone)
            }
        }
        .padding(16).frame(width: 288)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x1A1622), Color(hex: 0x100C18)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(tint.opacity(0.5), lineWidth: 1.5))
        )
        .shadow(color: tint.opacity(0.4), radius: 22, y: 8).shadow(color: .black.opacity(0.5), radius: 14, y: 10)
        .transition(.scale(scale: 0.9).combined(with: .opacity))
        .onAppear { nameFocused = true }
    }
}

// THE IN-WORLD CONNECT CARD — pair your desktop FROM THE DESK (host · port · token), never a system
// alert and never buried behind a flag. Host + token are required for a LAN bind; a Test button
// proves the Mac answers before you commit. Lifts on the desk like the editor cards (no scrim).
struct DioConnectCard: View {
    @State var name: String
    @State var host: String
    @State var port: String
    @State var token: String
    var maxW: CGFloat = 380   // clamped by the caller's DeskCamera so it fits the lane (HSM-20-02)
    let paired: Bool
    let onConnect: (_ host: String, _ port: String, _ token: String, _ name: String) -> Void
    let onForget: () -> Void
    let onCancel: () -> Void
    let onTest: (_ host: String, _ port: String, _ token: String) async -> Bool
    @State private var testing = false
    @State private var testResult: Bool? = nil
    @FocusState private var hostFocused: Bool
    private let tint = DioPal.cobalt
    private var canConnect: Bool {
        !host.trimmingCharacters(in: .whitespaces).isEmpty && (Int(port.trimmingCharacters(in: .whitespaces)) ?? 0) > 0
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 13) {
            HStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 11, style: .continuous)
                        .fill(LinearGradient(colors: [tint.opacity(0.4), Color(hex: 0x12101A)], startPoint: .top, endPoint: .bottom))
                        .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous).strokeBorder(tint.opacity(0.7), lineWidth: 1.2))
                        .frame(width: 38, height: 38)
                    Image(systemName: "laptopcomputer").font(.system(size: 18, weight: .bold)).foregroundStyle(.white)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text(paired ? "YOUR DESKTOP" : "CONNECT YOUR DESKTOP").font(.system(size: 11, weight: .black, design: .rounded)).tracking(1.4).foregroundStyle(tint)
                    Text("Sync + send run through it").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                }
                Spacer(minLength: 0)
                Button(action: onCancel) { Image(systemName: "xmark").font(.system(size: 14, weight: .black)).foregroundStyle(DioPal.muted).frame(width: 30, height: 30).background(Circle().fill(.white.opacity(0.06))) }.buttonStyle(.plain)
            }
            field(label: "NAME", placeholder: "e.g. Studio desktop", text: $name, mic: true, keyboard: .default)
            field(label: "HOST", placeholder: "192.168.1.13", text: $host, mic: true, keyboard: .URL, focus: $hostFocused, mono: true)
            HStack(alignment: .bottom, spacing: 12) {
                field(label: "PORT", placeholder: "8765", text: $port, mic: false, keyboard: .numberPad, mono: true).frame(width: 96)
                tokenField
            }
            HStack(spacing: 12) {
                if paired {
                    Button(action: onForget) {
                        HStack(spacing: 6) { Image(systemName: "trash").font(.system(size: 12, weight: .bold)); Text("Forget").font(.system(size: 13, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(Color(hex: 0xFF6B6B).opacity(0.9))
                    }.buttonStyle(.plain)
                }
                Button { runTest() } label: {
                    HStack(spacing: 6) {
                        if testing { ProgressView().controlSize(.mini).tint(tint) }
                        else if let r = testResult { Image(systemName: r ? "checkmark.circle.fill" : "xmark.circle.fill").foregroundStyle(r ? DioPal.mint : Color(hex: 0xFF6B6B)) }
                        else { Image(systemName: "dot.radiowaves.left.and.right") }
                        Text(testResult == true ? "Reachable" : testResult == false ? "No answer" : "Test").font(.system(size: 13, weight: .heavy, design: .rounded))
                    }
                    .foregroundStyle(testResult == true ? DioPal.mint : DioPal.text)
                    .padding(.horizontal, 13).frame(height: 38).background(Capsule().fill(.white.opacity(0.06)))
                }.buttonStyle(.plain).disabled(!canConnect || testing)
                Spacer(minLength: 0)
                Button { onConnect(host, port, token, name) } label: {
                    HStack(spacing: 6) { Image(systemName: "link").font(.system(size: 13, weight: .black)); Text(paired ? "Update" : "Connect").font(.system(size: 14, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(.white).padding(.horizontal, 18).frame(height: 38)
                        .background(Capsule().fill(LinearGradient(colors: [tint, tint.opacity(0.62)], startPoint: .top, endPoint: .bottom)))
                        .shadow(color: tint.opacity(0.5), radius: 8, y: 3).opacity(canConnect ? 1 : 0.4)
                }.buttonStyle(.plain).disabled(!canConnect)
            }
        }
        .padding(18).frame(width: maxW)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x1A1622), Color(hex: 0x0E0B16)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(tint.opacity(0.5), lineWidth: 1.5))
        )
        .shadow(color: tint.opacity(0.4), radius: 26, y: 10).shadow(color: .black.opacity(0.55), radius: 16, y: 12)
        .transition(.scale(scale: 0.92).combined(with: .opacity))
    }

    @ViewBuilder
    private func field(label: String, placeholder: String, text: Binding<String>, mic: Bool, keyboard: UIKeyboardType, focus: FocusState<Bool>.Binding? = nil, mono: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(label).font(.system(size: 9.5, weight: .black, design: .rounded)).tracking(1.4).foregroundStyle(DioPal.muted)
            HStack(spacing: 8) {
                Group {
                    if let focus { TextField(placeholder, text: text).focused(focus) }
                    else { TextField(placeholder, text: text) }
                }
                .font(.system(size: 15, weight: .bold, design: mono ? .monospaced : .rounded)).foregroundStyle(DioPal.text)
                .textFieldStyle(.plain).keyboardType(keyboard).autocorrectionDisabled().textInputAutocapitalization(.never)
                if mic { VoiceFillMic(text: text, tint: tint, size: 26, fill: .replace) }
            }
            .padding(.horizontal, 12).frame(height: 42)
            .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(.white.opacity(0.05))
                .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
        }
    }

    private var tokenField: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack(spacing: 6) {
                Text("TOKEN").font(.system(size: 9.5, weight: .black, design: .rounded)).tracking(1.4).foregroundStyle(DioPal.muted)
                Spacer(minLength: 0)
                Button {
                    #if canImport(UIKit)
                    if let s = UIPasteboard.general.string { token = s.trimmingCharacters(in: .whitespacesAndNewlines) }
                    #endif
                } label: { Text("Paste").font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(tint) }.buttonStyle(.plain)
            }
            TextField("from your desktop", text: $token)
                .font(.system(size: 13, weight: .bold, design: .monospaced)).foregroundStyle(DioPal.text)
                .textFieldStyle(.plain).autocorrectionDisabled().textInputAutocapitalization(.never)
                .lineLimit(1).truncationMode(.middle)
                .padding(.horizontal, 12).frame(height: 42)
                .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(.white.opacity(0.05))
                    .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
        }
    }

    private func runTest() {
        testing = true; testResult = nil
        Task {
            let ok = await onTest(host, port, token)
            await MainActor.run { testing = false; testResult = ok }
        }
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

// SPEAKER AVATARS — tiny PixelLab portraits assigned to "Speaker N" by index, bundled as speaker_<i>.png.
// They give diarized speakers a face, and double as the filter values in the transcript.
enum SpeakerAvatars {
    static let count = 16
    static func index(for speaker: String) -> Int {
        let digits = speaker.filter(\.isNumber)
        if let n = Int(digits), n > 0 { return (n - 1) % count }
        return abs(speaker.hashValue) % count
    }
    static func asset(for speaker: String) -> String { "speaker_\(index(for: speaker))" }
    static func tint(for speaker: String) -> Color { DioPal.zoneTints[index(for: speaker) % DioPal.zoneTints.count] }
}
struct SpeakerAvatarView: View {
    let speaker: String; var size: CGFloat = 26
    var body: some View {
        let tint = SpeakerAvatars.tint(for: speaker)
        ZStack {
            Circle().fill(LinearGradient(colors: [tint.opacity(0.55), Color(hex: 0x14121C)], startPoint: .top, endPoint: .bottom))
                .overlay(Circle().strokeBorder(tint.opacity(0.6), lineWidth: 1))
            DeskSprite(name: SpeakerAvatars.asset(for: speaker), size: size * 0.86)
        }
        .frame(width: size, height: size)
    }
}

// THE TRANSCRIPT — speaker-grouped lines with tiny portraits + tap-a-portrait to filter by speaker. Stateful,
// so it's its own view (the pull-out's pure SectionBody renderer can't hold filter state).
struct DioTranscriptSection: View {
    let lines: [(who: String, what: String)]
    @State private var filter: String? = nil
    private var speakers: [String] {
        var seen = Set<String>(); var out: [String] = []
        for l in lines where !seen.contains(l.who) { seen.insert(l.who); out.append(l.who) }
        return out
    }
    private var shown: [(who: String, what: String)] { filter == nil ? lines : lines.filter { $0.who == filter } }
    var body: some View {
        VStack(alignment: .leading, spacing: 11) {
            if speakers.count > 1 {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 7) {
                        chip(nil, "All", lines.count)
                        ForEach(speakers, id: \.self) { s in chip(s, s, lines.filter { $0.who == s }.count) }
                    }.padding(.bottom, 1)
                }
            }
            ForEach(Array(shown.enumerated()), id: \.offset) { _, ln in
                HStack(alignment: .top, spacing: 9) {
                    SpeakerAvatarView(speaker: ln.who, size: 26)
                    VStack(alignment: .leading, spacing: 1) {
                        Text(ln.who).font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(SpeakerAvatars.tint(for: ln.who))
                        Text(ln.what).font(.system(size: 13.5, weight: .regular, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.88)).fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
        }
    }
    private func chip(_ value: String?, _ label: String, _ n: Int) -> some View {
        let on = filter == value
        let tint = value.map { SpeakerAvatars.tint(for: $0) } ?? DioPal.muted
        return Button { withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) { filter = on ? nil : value }; tapHaptic() } label: {
            HStack(spacing: 5) {
                if let v = value { SpeakerAvatarView(speaker: v, size: 18) } else { Image(systemName: "person.2.fill").font(.system(size: 9, weight: .bold)) }
                Text(label).font(.system(size: 11, weight: .heavy, design: .rounded)).lineLimit(1)
                Text("\(n)").font(.system(size: 9, weight: .black, design: .rounded)).opacity(0.7)
            }
            .foregroundStyle(on ? .white : DioPal.text.opacity(0.85))
            .padding(.horizontal, 9).frame(height: 30)
            .background(Capsule().fill(on ? tint.opacity(0.85) : .white.opacity(0.06)).overlay(Capsule().strokeBorder(tint.opacity(on ? 0 : 0.4), lineWidth: 1)))
        }.buttonStyle(.plain)
    }
    private func tapHaptic() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        #endif
    }
}

// THE PULL-OUT — ONE renderer for ANY primitive. Header (glyph/title/egress) + the primitive's `sections`
// (each SectionBody drawn one way, here) + its `actions`. No per-type code — the contract drives it.
struct DioPullout: View {
    let prim: any DeskPrimitive
    let onClose: () -> Void; let onAction: (PrimitiveAction) -> Void; let onRouteSection: (String, String) -> Void
    var onActItem: ((String, String) -> Void)? = nil      // act on a single action row → send/file
    var onOpenDerivative: ((String) -> Void)? = nil       // tap a derivative card → open its own drawer
    var onChangeIcon: (() -> Void)? = nil                 // tap the header sprite → pick a different icon
    private func sectionText(_ body: SectionBody) -> String {
        switch body {
        case .text(let s): return s
        case .actions(let r): return r.map { "- \($0.task)" + ($0.meta.map { " (\($0))" } ?? "") }.joined(separator: "\n")
        case .chips(let c): return c.joined(separator: ", ")
        case .transcript(let l): return l.map { "\($0.who): \($0.what)" }.joined(separator: "\n")
        case .derivatives(let d): return d.map { "\($0.lens): \($0.title)" }.joined(separator: "\n")
        }
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 11) {
                // The header sprite is tappable → change this object's icon (a small pencil hints it).
                Button { onChangeIcon?() } label: {
                    DeskSprite(name: prim.glyph, size: 40)
                        .overlay(alignment: .bottomTrailing) {
                            if onChangeIcon != nil {
                                Image(systemName: "pencil.circle.fill").font(.system(size: 14, weight: .bold))
                                    .foregroundStyle(DioPal.accent).background(Circle().fill(.black.opacity(0.5)))
                                    .offset(x: 3, y: 3)
                            }
                        }
                }.buttonStyle(.plain).disabled(onChangeIcon == nil)
                VStack(alignment: .leading, spacing: 2) {
                    Text(prim.title).font(.system(size: 18, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                    Text(prim.subtitle).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                }
                Spacer(minLength: 0)
                // HSM-21-01: the primitive's REAL posture (was a hard-coded "On device"
                // capsule — a connector wore the local badge while existing to egress).
                EgressBadge(scope: prim.egress)
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
                        let isDerivatives: Bool = { if case .derivatives = sec.body { return true }; return false }()
                        VStack(alignment: .leading, spacing: 8) {
                            DrawerSection(label: sec.label, tint: sec.tint) { sectionBody(sec.body) }
                            if canRoute && !isDerivatives {   // derivatives are already-run outputs; routing the list is meaningless
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
            DioTranscriptSection(lines: lines)
        case .derivatives(let cards):
            VStack(spacing: 9) {
                ForEach(Array(cards.enumerated()), id: \.offset) { _, c in
                    Button { onOpenDerivative?(c.id) } label: {
                        HStack(spacing: 11) {
                            VStack(alignment: .leading, spacing: 3) {
                                HStack(spacing: 6) {
                                    Text(c.lens.uppercased()).font(.system(size: 8.5, weight: .black, design: .rounded)).tracking(0.8)
                                        .foregroundStyle(lensColorStatic(c.lens))
                                        .padding(.horizontal, 6).padding(.vertical, 2)
                                        .background(Capsule().fill(lensColorStatic(c.lens).opacity(0.16)))
                                    Text(c.title).font(.system(size: 13.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text).lineLimit(1)
                                }
                                if !c.snippet.isEmpty {
                                    Text(c.snippet).font(.system(size: 11.5, weight: .medium, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(2).fixedSize(horizontal: false, vertical: true)
                                }
                            }
                            Spacer(minLength: 6)
                            Image(systemName: "chevron.right").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.muted.opacity(0.7))
                        }
                        .padding(.horizontal, 13).padding(.vertical, 11)
                        .background(RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .fill(.white.opacity(0.04))
                            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(.white.opacity(0.10), lineWidth: 1)))
                    }.buttonStyle(.plain)
                }
            }
        }
    }
}

// The lens hue, available to the pull-out renderer (mirrors DeskDioramaStage.lensColor).
private func lensColorStatic(_ lens: String) -> Color {
    switch lens {
    case "Summary": return DioPal.violet
    case "Actions": return DioPal.mint
    case "Decisions": return DioPal.accent
    case "Questions": return DioPal.cobalt
    default: return DioPal.accent
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

// THE CAPTURE LENSES — pre-baked "intelligence markers" you can fire on a window of the LIVE transcript
// while Whisper keeps running. Each runs through the on-device model (or the endpoint) and pops a small card.
struct LiveLens { let name: String; let icon: String; let instruction: String }
enum LiveLenses {
    static let all: [LiveLens] = [
        .init(name: "Summary", icon: "sparkles", instruction: "Summarize the key points from this meeting transcript window in 3–4 tight sentences."),
        .init(name: "Questions", icon: "questionmark.circle.fill", instruction: "List every open question raised in this transcript window, one per line. If there are none, say 'No open questions yet.'"),
        .init(name: "Decisions", icon: "flag.checkered", instruction: "List the decisions made in this transcript window, one per line. If none, say 'No decisions yet.'"),
        .init(name: "Actions", icon: "checkmark.circle.fill", instruction: "Extract the concrete action items from this transcript window as a short list (task — owner when known)."),
    ]
    // THE DEFAULT POST-RECORD PIPELINE — every recording auto-runs these against the meeting (real steps,
    // real x-of-N progress, each spits a deliverable onto the desk). Summary + Actions: the lean, useful pair.
    static let defaultPipeline: [LiveLens] = [all[0], all[3]]
}
// one live-intelligence result floating by the mic
struct LiveIntelCard: Identifiable { let id: String; let lens: String; let minutes: Double; var text: String?; var thinking: Bool }

// what a live marker fires: a quick built-in lens, one of YOUR tailored agents, or a whole crew — all on a window
enum LiveTarget { case lens(LiveLens); case agent(AgentRecord); case chain(ChainRecord) }

// THE MODE PICKER — a hovering popup over the corner mic: are we recording a meeting, or talking to the Mac?
struct DioRecordModePicker: View {
    let anchor: CGPoint
    let onMeeting: () -> Void; let onDesktop: () -> Void; let onClose: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.4).ignoresSafeArea().onTapGesture { onClose() }
            VStack(alignment: .leading, spacing: 11) {
                Text("WHAT ARE WE CAPTURING?").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1.2).foregroundStyle(DioPal.muted)
                choice(icon: "waveform.badge.mic", title: "Start a meeting", sub: "record & weave it on-device", tint: DioPal.accent, action: onMeeting)
                choice(icon: "desktopcomputer", title: "Talk to the desktop", sub: "dictate straight to your desktop", tint: DioPal.cobalt, action: onDesktop)
            }
            .padding(15).frame(width: 296)
            .background(RoundedRectangle(cornerRadius: 24, style: .continuous).fill(Color(hex: 0x15121C))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 1))
                .shadow(color: .black.opacity(0.5), radius: 24, y: 10))
            .position(x: min(anchor.x + 150, 330), y: max(170, anchor.y - 140))
            .transition(.scale(scale: 0.85, anchor: .bottomLeading).combined(with: .opacity))
        }
    }
    private func choice(icon: String, title: String, sub: String, tint: Color, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 13) {
                Image(systemName: icon).font(.system(size: 19, weight: .bold)).foregroundStyle(.white)
                    .frame(width: 46, height: 46).background(RoundedRectangle(cornerRadius: 14).fill(LinearGradient(colors: [tint, tint.opacity(0.5)], startPoint: .top, endPoint: .bottom)))
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.system(size: 15.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(sub).font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.right").font(.system(size: 12, weight: .black)).foregroundStyle(DioPal.muted)
            }.padding(11).frame(maxWidth: .infinity).background(RoundedRectangle(cornerRadius: 16).fill(.white.opacity(0.05)))
        }.buttonStyle(.plain)
    }
}

// THE AMBIENT RECORDER — recording does NOT take over. The corner mic stays put and RADIATES: faint angled
// waveform sprawls, a small live transcript, and the intelligence markers. Fire one → a quick window slider →
// the agent runs on the recent transcript WHILE Whisper keeps going, and a small card floats up by the mic.
// A wrapping flow — chips flow left-to-right and wrap to new rows so NOTHING cuts off (no horizontal scroll).
struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxW = proposal.width ?? .infinity
        var x: CGFloat = 0, y: CGFloat = 0, rowH: CGFloat = 0
        for v in subviews {
            let s = v.sizeThatFits(.unspecified)
            if x > 0, x + s.width > maxW { x = 0; y += rowH + spacing; rowH = 0 }
            x += s.width + spacing; rowH = max(rowH, s.height)
        }
        return CGSize(width: maxW == .infinity ? x : maxW, height: y + rowH)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let maxW = bounds.width
        var x: CGFloat = 0, y: CGFloat = 0, rowH: CGFloat = 0
        for v in subviews {
            let s = v.sizeThatFits(.unspecified)
            if x > 0, x + s.width > maxW { x = 0; y += rowH + spacing; rowH = 0 }
            v.place(at: CGPoint(x: bounds.minX + x, y: bounds.minY + y), proposal: ProposedViewSize(s))
            x += s.width + spacing; rowH = max(rowH, s.height)
        }
    }
}

// THE WEAVE — THE CONSTELLATION. On stop, the record pane becomes a living node field: the meeting's ideas
// scatter as stars, connections fire between them as the model thinks, and each completed step CONDENSES a
// burst of the field into a deliverable (the real card then lands on the desk). Real x-of-N drives it; a
// skip bails to the desk. Reusable for ANY N-step pipeline.
struct DioConstellationWeave: View {
    let stepName: String; let done: Int; let total: Int; let lensNames: [String]
    var words: [String] = []              // riff 1: the meeting's real words become the stars
    var lensColors: [Color] = []          // riff 2: each step tints the firing connections + the born card
    let onSkip: () -> Void
    @State private var pop = 0.0          // one-shot "condense → card" beat, fired when a step completes
    @State private var popColor = DioPal.mint
    private var finished: Bool { done >= total }
    private var progress: Double { total > 0 ? Double(done) / Double(total) : 0 }
    // a stable scatter of nodes (deterministic pseudo-random in a unit rect)
    private static let nodes: [CGPoint] = (0..<30).map { i in
        func rnd(_ s: Double) -> Double { let v = sin(s) * 43758.5453; return v - Foundation.floor(v) }
        return CGPoint(x: 0.06 + 0.88 * rnd(Double(i) * 12.9898), y: 0.10 + 0.80 * rnd(Double(i) * 78.233 + 1))
    }
    // riff 3: a nearest-neighbour tour the "attention" walks edge-to-edge through the graph
    private static let tour: [Int] = {
        var remaining = Array(1..<nodes.count), order = [0], cur = 0
        while !remaining.isEmpty {
            let c = nodes[cur]
            let nxt = remaining.min { hypot(nodes[$0].x - c.x, nodes[$0].y - c.y) < hypot(nodes[$1].x - c.x, nodes[$1].y - c.y) }!
            order.append(nxt); remaining.removeAll { $0 == nxt }; cur = nxt
        }
        return order
    }()
    private func tint(_ i: Int) -> Color { DioPal.zoneTints[i % DioPal.zoneTints.count] }
    private func attnPos(_ t: Double, _ size: CGSize) -> (p: CGPoint, a: CGPoint, b: CGPoint) {
        let hop = 0.55, f = t / hop, idx = Int(f) % Self.tour.count, frac = f - Foundation.floor(f)
        let a = Self.nodes[Self.tour[idx]], b = Self.nodes[Self.tour[(idx + 1) % Self.tour.count]]
        let ap = CGPoint(x: a.x * size.width, y: a.y * size.height), bp = CGPoint(x: b.x * size.width, y: b.y * size.height)
        return (CGPoint(x: ap.x + (bp.x - ap.x) * frac, y: ap.y + (bp.y - ap.y) * frac), ap, bp)
    }
    private var stepColor: Color? { let li = done - 1; return (!finished && li >= 0 && li < lensColors.count) ? lensColors[li] : nil }
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 9) {
                TimelineView(.animation) { tl in
                    let r = 0.5 + 0.5 * sin(tl.date.timeIntervalSinceReferenceDate * 3.2)
                    Image(systemName: finished ? "checkmark.circle.fill" : "brain.head.profile")
                        .font(.system(size: 20, weight: .bold)).foregroundStyle(finished ? DioPal.mint : DioPal.cobalt)
                        .shadow(color: (finished ? DioPal.mint : DioPal.cobalt).opacity(0.5 + 0.4 * r), radius: 8)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text(finished ? "Meeting ready" : "Connecting ideas…").font(.system(size: 14, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text(finished ? "all deliverables on the desk" : "Step \(min(done + 1, total)) of \(total) · \(stepName)")
                        .font(.system(size: 11.5, weight: .heavy, design: .rounded)).foregroundStyle(finished ? DioPal.mint : DioPal.cobalt).lineLimit(1)
                }
                Spacer(minLength: 0)
                if !finished {
                    Button(action: onSkip) { Text("Skip").font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).padding(.horizontal, 9).frame(height: 24).background(Capsule().fill(.white.opacity(0.07))) }.buttonStyle(.plain)
                }
            }
            constellation.frame(width: 300, height: 132)
            // the deliverables condensing out — a chip lights as its step lands
            HStack(spacing: 6) {
                ForEach(Array(lensNames.enumerated()), id: \.offset) { i, name in
                    let stepDone = (done - 1) > i           // step 1 is the weave; lenses are steps 2…N
                    let active = (done - 1) == i && !finished
                    HStack(spacing: 4) {
                        Image(systemName: stepDone ? "checkmark" : (active ? "circle.dotted" : "circle")).font(.system(size: 8, weight: .black))
                        Text(name).font(.system(size: 10, weight: .heavy, design: .rounded))
                    }
                    .foregroundStyle(stepDone ? .white : (active ? DioPal.cobalt : DioPal.muted))
                    .padding(.horizontal, 8).frame(height: 24)
                    .background(Capsule().fill(stepDone ? DioPal.mint.opacity(0.85) : .white.opacity(0.06)).overlay(Capsule().strokeBorder((active ? DioPal.cobalt : .clear).opacity(0.6), lineWidth: 1)))
                    .scaleEffect(active ? 1.0 + 0.03 : 1)
                }
                Spacer(minLength: 0)
                HStack(spacing: 4) { Image(systemName: "lock.fill").font(.system(size: 8, weight: .bold)); Text("on device").font(.system(size: 9, weight: .heavy, design: .rounded)) }.foregroundStyle(DioPal.mint)
            }.frame(width: 300)
        }
        .padding(15)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(.black.opacity(0.6)).overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
        .padding(.leading, 16).padding(.bottom, 36)
        .transition(.opacity)
        .onChange(of: done) { nv in
            popColor = (nv - 2 >= 0 && nv - 2 < lensColors.count) ? lensColors[nv - 2] : DioPal.mint
            pop = 0; withAnimation(.easeOut(duration: 0.9)) { pop = 1 }
        }
    }
    private var constellation: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            Canvas { ctx, size in
                let pts = Self.nodes.map { CGPoint(x: $0.x * size.width, y: $0.y * size.height) }
                let reveal = 0.2 + 0.65 * progress + 0.05 * sin(t)          // more connections as it thinks
                let edgeBase = stepColor                                    // riff 2: active step tints the edges
                // edges between near neighbours, lit progressively, pulsing
                for i in pts.indices {
                    for j in (i + 1)..<pts.count {
                        let dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y
                        guard (dx * dx + dy * dy).squareRoot() < size.width * 0.24 else { continue }
                        guard (sin(Double(i * 31 + j * 17)) * 0.5 + 0.5) < reveal else { continue }
                        let pulse = 0.25 + 0.5 * (0.5 + 0.5 * sin(t * 2 + Double(i + j)))
                        var path = Path(); path.move(to: pts[i]); path.addLine(to: pts[j])
                        ctx.stroke(path, with: .color((edgeBase ?? tint(i)).opacity(0.22 * pulse)), lineWidth: 1)
                    }
                }
                // riff 1: the nodes ARE the meeting's words (twinkling); plain dots fill the rest of the field
                for (i, p) in pts.enumerated() {
                    let tw = 0.4 + 0.6 * (0.5 + 0.5 * sin(t * 1.6 + Double(i)))
                    let c = edgeBase ?? tint(i)
                    if i < words.count {
                        var gc = ctx; gc.opacity = 0.45 + 0.5 * tw
                        gc.draw(Text(words[i]).font(.system(size: 8.5, weight: .heavy, design: .rounded)).foregroundColor(c), at: p, anchor: .center)
                    } else {
                        let r = 1.4 + 1.3 * tw
                        ctx.fill(Path(ellipseIn: CGRect(x: p.x - r, y: p.y - r, width: 2 * r, height: 2 * r)), with: .color(c.opacity(0.4 + 0.5 * tw)))
                    }
                }
                // riff 3: the "attention" TRACES the graph edge to edge, with a fading trail
                if !finished {
                    for k in stride(from: 6, through: 0, by: -1) {
                        let (tp, _, _) = attnPos(t - Double(k) * 0.05, size)
                        let op = (1 - Double(k) / 7) * 0.5
                        ctx.fill(Path(ellipseIn: CGRect(x: tp.x - 2.5, y: tp.y - 2.5, width: 5, height: 5)), with: .color(.white.opacity(op)))
                    }
                    let (ap, ea, eb) = attnPos(t, size)
                    var edge = Path(); edge.move(to: ea); edge.addLine(to: eb)
                    ctx.stroke(edge, with: .color(.white.opacity(0.35)), lineWidth: 1.5)
                    ctx.fill(Path(ellipseIn: CGRect(x: ap.x - 4, y: ap.y - 4, width: 8, height: 8)), with: .color(.white.opacity(0.95)))
                    ctx.fill(Path(ellipseIn: CGRect(x: ap.x - 10, y: ap.y - 10, width: 20, height: 20)), with: .color(.white.opacity(0.12)))
                }
                // riff 2: a step lands → the lit cluster CONDENSES (ring inward) then a deliverable card is born
                // and flies toward the desk (up-right), tinted the just-finished lens colour
                if pop > 0, pop < 1 {
                    let c = CGPoint(x: size.width / 2, y: size.height / 2)
                    if pop < 0.5 {
                        let rr = size.width * 0.45 * (1 - pop / 0.5)
                        ctx.stroke(Path(ellipseIn: CGRect(x: c.x - rr, y: c.y - rr, width: 2 * rr, height: 2 * rr)), with: .color(popColor.opacity(0.85 * (1 - pop / 0.5))), lineWidth: 2.5)
                    } else {
                        let f = (pop - 0.5) / 0.5
                        let p = CGPoint(x: c.x + (size.width * 0.5 - c.x) * f, y: c.y + (-size.height * 0.5 - c.y) * f)
                        let sc = 0.6 + 0.7 * f, cw = 34 * sc, ch = 22 * sc
                        let op = f < 0.6 ? 1.0 : (1 - (f - 0.6) / 0.4)
                        ctx.fill(Path(roundedRect: CGRect(x: p.x - cw / 2, y: p.y - ch / 2, width: cw, height: ch), cornerRadius: 5), with: .color(popColor.opacity(0.9 * op)))
                    }
                }
            }
        }
    }
}

// riff 4 — a faint, brief star-map drifting over a freshly-born deliverable: it remembers the constellation
// it condensed out of. Used by DioHero on arrived artifacts.
struct ConstellationEcho: View {
    let tint: Color
    private static let pts: [CGPoint] = (0..<10).map { i in
        func rnd(_ s: Double) -> Double { let v = sin(s) * 43758.5453; return v - Foundation.floor(v) }
        return CGPoint(x: 0.12 + 0.76 * rnd(Double(i) * 9.17), y: 0.12 + 0.76 * rnd(Double(i) * 4.71 + 2))
    }
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            Canvas { ctx, size in
                let p = Self.pts.map { CGPoint(x: $0.x * size.width, y: $0.y * size.height) }
                for i in p.indices {
                    for j in (i + 1)..<p.count where hypot(p[i].x - p[j].x, p[i].y - p[j].y) < size.width * 0.4 {
                        var path = Path(); path.move(to: p[i]); path.addLine(to: p[j])
                        ctx.stroke(path, with: .color(tint.opacity(0.12)), lineWidth: 0.6)
                    }
                }
                for (i, q) in p.enumerated() {
                    let tw = 0.4 + 0.6 * (0.5 + 0.5 * sin(t * 2 + Double(i)))
                    ctx.fill(Path(ellipseIn: CGRect(x: q.x - 1.3, y: q.y - 1.3, width: 2.6, height: 2.6)), with: .color(.white.opacity(0.25 * tw)))
                }
            }
        }
    }
}

// THE WORD-SPAWN EFFECT LIBRARY — how live speech materializes onto the desk, emerging from the thinking prism.
enum WordSpawn: String, CaseIterable {
    case prism, swarm, shatter, lightWrite
    var label: String { switch self { case .prism: return "Prism"; case .swarm: return "Swarm"; case .shatter: return "Shatter"; case .lightWrite: return "Light" } }
    var icon: String { switch self { case .prism: return "triangle"; case .swarm: return "sparkles"; case .shatter: return "diamond"; case .lightWrite: return "pencil.tip" } }
    var next: WordSpawn { let a = WordSpawn.allCases; return a[(a.firstIndex(of: self)! + 1) % a.count] }
}

// the MEANING-DRIVEN layer — a line's intent picks its colour + a small marker (heuristic, live; no LLM needed)
func transcriptIntent(_ s: String) -> (tint: Color, icon: String?) {
    let l = s.lowercased()
    if s.contains("?") { return (DioPal.cobalt, "questionmark.circle.fill") }
    if l.contains("risk") || l.contains("blocker") || l.contains("concern") || l.contains("worried") { return (Color(hex: 0xFFC857), "exclamationmark.triangle.fill") }
    if l.contains("agreed") || l.contains("decide") || l.contains("decision") || l.contains("let's") || l.contains("we'll") { return (DioPal.accent, "flag.fill") }
    if l.contains("action") || l.contains("owns") || l.contains("todo") || l.contains(" will ") || l.contains("by friday") || l.contains("next step") { return (DioPal.mint, "checkmark.circle.fill") }
    return (DioPal.text.opacity(0.85), nil)
}

// renders one line with the chosen spawn animation, tinted by intent, ghosted while unconfirmed (confidence)
struct SpawnText: View {
    let text: String; let style: WordSpawn; let tint: Color; var ghost: Bool = false
    @State private var shown = false
    private var base: Double { ghost ? 0.5 : 1 }
    private var font: Font { .system(size: 12.5, weight: ghost ? .semibold : .regular, design: .rounded) }
    var body: some View {
        content
            .onAppear {
                shown = false
                let anim: Animation = style == .lightWrite ? .easeInOut(duration: 0.7) : .spring(response: 0.55, dampingFraction: 0.72)
                withAnimation(anim) { shown = true }
            }
    }
    @ViewBuilder private var content: some View {
        switch style {
        case .swarm:
            HStack(spacing: 0) {
                ForEach(Array(text.enumerated()), id: \.offset) { i, ch in
                    Text(String(ch)).font(font).foregroundStyle(tint)
                        .opacity(shown ? base : 0).blur(radius: shown ? 0 : 1.5)
                        .offset(x: shown ? 0 : CGFloat(sin(Double(i) * 12.9) * 40), y: shown ? 0 : CGFloat(cos(Double(i) * 7.7) * 24))
                        .animation(.spring(response: 0.5, dampingFraction: 0.7).delay(Double(i) * 0.012), value: shown)
                }
            }
        case .shatter:
            Text(text).font(font).foregroundStyle(tint)
                .opacity(shown ? base : 0).blur(radius: shown ? 0 : 4)
                .scaleEffect(shown ? 1 : 1.25).rotation3DEffect(.degrees(shown ? 0 : 28), axis: (x: 1, y: 0.4, z: 0))
        case .lightWrite:
            Text(text).font(font).foregroundStyle(tint).opacity(base)
                .mask(GeometryReader { g in Rectangle().frame(width: shown ? g.size.width : 0, alignment: .leading).frame(maxHeight: .infinity, alignment: .leading) })
                .overlay(alignment: .leading) { GeometryReader { g in Circle().fill(.white).frame(width: 4, height: 4).shadow(color: tint, radius: 4).position(x: shown ? g.size.width : 0, y: g.size.height / 2).opacity(shown ? 0 : 1).animation(.easeInOut(duration: 0.7), value: shown) } }
        case .prism:
            Text(text).font(font).foregroundStyle(tint).modifier(MaterializeModifier(p: shown ? 1 : 0))
        }
    }
}

// the materialize transition — a line/word blurs in, rises, and scales up as if condensing out of the prism
struct MaterializeModifier: ViewModifier {
    let p: Double   // 0 = forming, 1 = formed
    func body(content: Content) -> some View {
        content.opacity(p).blur(radius: (1 - p) * 5).scaleEffect(0.82 + 0.18 * p, anchor: .leading).offset(y: (1 - p) * 10)
    }
}
extension AnyTransition {
    static var prismMaterialize: AnyTransition {
        .asymmetric(insertion: .modifier(active: MaterializeModifier(p: 0), identity: MaterializeModifier(p: 1)), removal: .opacity)
    }
}

// THE THINKING PRISM — a small rotating geometric prism with chromatic refraction; live words spawn from it.
struct PrismTriangle: Shape {
    func path(in r: CGRect) -> Path {
        var p = Path(); p.move(to: CGPoint(x: r.midX, y: r.minY)); p.addLine(to: CGPoint(x: r.maxX, y: r.maxY)); p.addLine(to: CGPoint(x: r.minX, y: r.maxY)); p.closeSubpath(); return p
    }
}
struct DioPrism: View {
    var size: CGFloat = 18; var active: Bool = true
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let rot = t * (active ? 55 : 20)
            ZStack {
                Circle().fill(RadialGradient(colors: [DioPal.cobalt.opacity(active ? 0.5 : 0.18), .clear], center: .center, startRadius: 1, endRadius: size * 0.9)).blur(radius: 3)
                ForEach(Array([DioPal.accent, DioPal.mint, DioPal.cobalt].enumerated()), id: \.offset) { i, c in
                    PrismTriangle().stroke(c.opacity(0.85), lineWidth: 1.2)
                        .frame(width: size, height: size)
                        .rotationEffect(.degrees(rot + Double(i) * 3))
                        .offset(x: CGFloat(i - 1) * 0.8, y: CGFloat(i - 1) * 0.4)   // chromatic refraction split
                }
            }
            .frame(width: size * 1.5, height: size * 1.5)
        }
    }
}

struct DioAmbientRecorder: View {
    @ObservedObject var model: CaptureModel
    let isDesktop: Bool
    let orb: CGPoint; let w: CGFloat; let h: CGFloat
    let cards: [LiveIntelCard]
    let agents: [AgentRecord]; let chains: [ChainRecord]
    let onFire: (LiveTarget, Double) -> Void
    let onKeep: (LiveIntelCard) -> Void
    let onDismiss: (String) -> Void
    let onStop: () -> Void
    @State private var pending: LiveTarget? = nil
    @State private var mins: Double = 0.5
    @State private var expanded = false          // the transcript grew in place
    @State private var panelH: CGFloat = 250      // committed transcript-panel height
    @State private var dragH: CGFloat = 0         // live resize delta from the corner grip
    @AppStorage("hs.diorama.spawn") private var spawnRaw = "prism"   // the chosen word-spawn style
    private var spawn: WordSpawn { WordSpawn(rawValue: spawnRaw) ?? .prism }
    private func timeString(_ s: Double) -> String { let i = Int(s); return String(format: "%d:%02d", i / 60, i % 60) }
    private var segments: [String] {
        model.liveTranscript.replacingOccurrences(of: "\n", with: " ").components(separatedBy: CharacterSet(charactersIn: ".?!")).map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
    }
    private var lastLine: String {
        if !model.partial.isEmpty { return model.partial }
        let segs = model.liveTranscript.replacingOccurrences(of: "\n", with: " ").components(separatedBy: CharacterSet(charactersIn: ".?!")).map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        return segs.last ?? "listening…"
    }
    private var hot: Color { model.transcribing ? DioPal.cobalt : Color(hex: 0xFF4D4D) }
    var body: some View {
        ZStack {
            VStack(alignment: .leading, spacing: 9) {
                ForEach(cards) { c in DioLiveIntelCard(card: c, onKeep: { onKeep(c) }, onDismiss: { onDismiss(c.id) }) }
                if !model.transcribing {
                    if expanded { transcriptPanel } else { peekChip }
                    // ASK LIVE — every lens, agent, and crew, wrapped so NONE cut off (no horizontal scroll)
                    Text("ASK LIVE").font(.system(size: 8, weight: .black, design: .rounded)).tracking(1.5).foregroundStyle(DioPal.muted.opacity(0.8))
                    FlowLayout(spacing: 7) {
                        ForEach(LiveLenses.all, id: \.name) { l in
                            Button { pending = .lens(l); mins = 0.5; tap() } label: {
                                HStack(spacing: 5) { Image(systemName: l.icon).font(.system(size: 10, weight: .bold)); Text(l.name).font(.system(size: 11.5, weight: .heavy, design: .rounded)) }
                                    .foregroundStyle(DioPal.text).padding(.horizontal, 11).frame(height: 32)
                                    .background(Capsule().fill(DioPal.violet.opacity(0.22)).overlay(Capsule().strokeBorder(DioPal.violet.opacity(0.5), lineWidth: 1)))
                            }.buttonStyle(.plain)
                        }
                        ForEach(agents) { a in
                            Button { pending = .agent(a); mins = 0.5; tap() } label: {
                                HStack(spacing: 6) { AgentAvatarView(avatarId: a.avatar, size: 24); Text(a.name).font(.system(size: 11.5, weight: .heavy, design: .rounded)) }
                                    .foregroundStyle(DioPal.text).padding(.horizontal, 8).frame(height: 32)
                                    .background(Capsule().fill(AgentAvatars.color(a.avatar).opacity(0.2)).overlay(Capsule().strokeBorder(AgentAvatars.color(a.avatar).opacity(0.5), lineWidth: 1)))
                            }.buttonStyle(.plain)
                        }
                        ForEach(chains.filter { !$0.steps.isEmpty }) { c in
                            Button { pending = .chain(c); mins = 0.5; tap() } label: {
                                HStack(spacing: 5) { Image(systemName: "arrow.triangle.branch").font(.system(size: 10, weight: .bold)); Text(c.name).font(.system(size: 11.5, weight: .heavy, design: .rounded)) }
                                    .foregroundStyle(DioPal.text).padding(.horizontal, 11).frame(height: 32)
                                    .background(Capsule().fill(DioPal.accent.opacity(0.2)).overlay(Capsule().strokeBorder(DioPal.accent.opacity(0.5), lineWidth: 1)))
                            }.buttonStyle(.plain)
                        }
                    }.frame(maxWidth: w * 0.62, alignment: .leading)
                }
                bottomRow
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
            .padding(.leading, 16).padding(.bottom, h * 0.055)
            if let p = pending {
                DioWindowSlider(title: targetTitle(p), icon: targetIcon(p), tint: targetTint(p), minutes: $mins,
                                onGo: { onFire(p, mins); withAnimation { pending = nil } },
                                onCancel: { withAnimation { pending = nil } }).zIndex(20)
            }
        }
        #if targetEnvironment(simulator)
        .onAppear { if ProcessInfo.processInfo.environment["HS_DESK_RECORD"] == "transcript" { expanded = true } }
        #endif
    }
    private func targetTitle(_ t: LiveTarget) -> String { switch t { case .lens(let l): return l.name; case .agent(let a): return a.name; case .chain(let c): return c.name } }
    private func targetIcon(_ t: LiveTarget) -> String { switch t { case .lens(let l): return l.icon; case .agent: return "person.fill"; case .chain: return "arrow.triangle.branch" } }
    private func targetTint(_ t: LiveTarget) -> Color { switch t { case .lens: return DioPal.violet; case .agent(let a): return AgentAvatars.color(a.avatar); case .chain: return DioPal.accent } }
    private var bottomRow: some View {
        HStack(spacing: 11) {
            Button(action: onStop) {
                ZStack {
                    // the mic stays STILL; louder audio just makes its glow + fog more intense (no size jitter).
                    // CONCENTRIC — no offset shadow (that painted a stray circle BELOW the mic).
                    let lvl = CGFloat(min(1, model.level))
                    TimelineView(.animation) { tl in
                        let breathe = 0.85 + 0.15 * abs(sin(tl.date.timeIntervalSinceReferenceDate * 1.7))
                        // MUST be a ZStack — two bare circles in a TimelineView closure stack VERTICALLY
                        // (that was the phantom "circle below the mic" bug). Concentric glow + ring now.
                        ZStack {
                            Circle().stroke(hot.opacity(0.18 + 0.5 * lvl), lineWidth: 2).frame(width: 62, height: 62)
                            Circle().fill(hot).frame(width: 54, height: 54)
                                .shadow(color: hot.opacity((0.3 + 0.5 * lvl) * breathe), radius: 8 + 16 * lvl)
                                .shadow(color: .black.opacity(0.35), radius: 4, y: 2)
                        }
                    }
                    if model.transcribing { ProgressView().tint(.white) } else { RoundedRectangle(cornerRadius: 5, style: .continuous).fill(.white).frame(width: 18, height: 18) }
                }
                .frame(width: 80, height: 80)
            }.buttonStyle(.plain).disabled(model.transcribing)
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Circle().fill(hot).frame(width: 8, height: 8)
                    Text(model.transcribing ? "WEAVING" : (isDesktop ? "DICTATING" : "REC")).font(.system(size: 10, weight: .heavy, design: .rounded)).tracking(2).foregroundStyle(DioPal.text)
                    Text(timeString(model.elapsedSeconds)).font(.system(size: 11, weight: .heavy, design: .rounded).monospacedDigit()).foregroundStyle(DioPal.muted)
                }
                // HSM-21-01: the one grammar — dictation heard on-device, the text lands
                // on the desktop = a mixed posture, never dressed local.
                let scope: EgressScope = isDesktop ? .mixed("your desktop") : .local
                HStack(spacing: 4) { Image(systemName: scope.symbolName).font(.system(size: 8, weight: .bold)); Text(scope.label).font(.system(size: 9, weight: .heavy, design: .rounded)) }
                    .foregroundStyle(scope.leavesDevice ? Color(hex: 0xF5A524) : DioPal.mint)
            }
        }
    }
    // collapsed: a one-line peek; tap to GROW it in place (no separate modal — canon Law 1/2)
    private var peekChip: some View {
        Button { withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { expanded = true } } label: {
            HStack(alignment: .top, spacing: 8) {
                DioPrism(size: 15, active: !model.partial.isEmpty)
                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 5) { Text("HEARING").font(.system(size: 8, weight: .heavy, design: .rounded)).tracking(1.5); Image(systemName: "chevron.up").font(.system(size: 7, weight: .black)) }.foregroundStyle(DioPal.muted)
                    Text(lastLine).font(.system(size: 12, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.9)).lineLimit(2).frame(maxWidth: w * 0.46, alignment: .leading)
                        .id(lastLine).transition(.prismMaterialize)
                }
            }.padding(10).background(RoundedRectangle(cornerRadius: 13).fill(.black.opacity(0.4)).overlay(RoundedRectangle(cornerRadius: 13).strokeBorder(.white.opacity(0.08), lineWidth: 1)))
            .animation(.spring(response: 0.5, dampingFraction: 0.85), value: lastLine)
        }.buttonStyle(.plain)
    }
    // expanded: the transcript grows out of the same frame, resizable by the pulsing corner grip
    private var transcriptPanel: some View {
        let H = min(max(140, panelH - dragH), h * 0.58)
        return VStack(spacing: 0) {
            // TOP GRABBER — drag to size (clear of the collapse button now)
            Capsule().fill(DioPal.muted.opacity(0.5)).frame(width: 42, height: 5)
                .padding(.vertical, 7).frame(maxWidth: .infinity).contentShape(Rectangle())
                .gesture(DragGesture(minimumDistance: 1)
                    .onChanged { dragH = $0.translation.height }
                    .onEnded { v in panelH = min(max(140, panelH - v.translation.height), h * 0.58); dragH = 0 })
            HStack(spacing: 7) {
                DioPrism(size: 16, active: !model.partial.isEmpty)
                Text("LIVE TRANSCRIPT").font(.system(size: 10, weight: .heavy, design: .rounded)).tracking(1).foregroundStyle(DioPal.text)
                Spacer(minLength: 0)
                // spawn-style switcher — cycles the word-spawn effect (persisted)
                Button { spawnRaw = spawn.next.rawValue; tap() } label: {
                    HStack(spacing: 4) { Image(systemName: spawn.icon).font(.system(size: 9, weight: .bold)); Text(spawn.label).font(.system(size: 10, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(DioPal.cobalt).padding(.horizontal, 8).frame(height: 26).background(Capsule().fill(DioPal.cobalt.opacity(0.16)))
                }.buttonStyle(.plain)
                Button { withAnimation(.spring(response: 0.45, dampingFraction: 0.82)) { expanded = false } } label: {
                    HStack(spacing: 4) { Image(systemName: "chevron.down").font(.system(size: 10, weight: .black)); Text("Collapse").font(.system(size: 10.5, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(DioPal.text.opacity(0.9)).padding(.horizontal, 9).frame(height: 26).background(Capsule().fill(.white.opacity(0.1)))
                }.buttonStyle(.plain)
            }.padding(.horizontal, 12).padding(.bottom, 6)
            ScrollViewReader { proxy in
                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 7) {
                        ForEach(Array(segments.enumerated()), id: \.offset) { _, s in
                            let intent = transcriptIntent(s)
                            HStack(alignment: .top, spacing: 6) {
                                if let ic = intent.icon { Image(systemName: ic).font(.system(size: 9, weight: .bold)).foregroundStyle(intent.tint).padding(.top, 2) }
                                SpawnText(text: s + ".", style: spawn, tint: intent.tint).frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                        if !model.partial.isEmpty {
                            HStack(alignment: .top, spacing: 6) {
                                SpawnText(text: model.partial, style: spawn, tint: DioPal.accent, ghost: true).frame(maxWidth: .infinity, alignment: .leading).id("tail")
                            }
                        }
                    }.padding(.horizontal, 12).padding(.bottom, 10).animation(.spring(response: 0.5, dampingFraction: 0.8), value: segments.count)
                }
                .onChange(of: model.liveTranscript) { _ in withAnimation { proxy.scrollTo("tail", anchor: .bottom) } }
            }
        }
        .frame(width: w * 0.6, height: H, alignment: .top)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(.black.opacity(0.58)).overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
    }
    private func tap() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        #endif
    }
}

// the quick window slider — 0:30 → 5:00, fired while the recording keeps rolling
struct DioWindowSlider: View {
    let title: String; let icon: String; let tint: Color; @Binding var minutes: Double
    let onGo: () -> Void; let onCancel: () -> Void
    private func fmt(_ m: Double) -> String { let s = Int(m * 60); return String(format: "%d:%02d", s / 60, s % 60) }
    var body: some View {
        ZStack {
            Color.black.opacity(0.5).ignoresSafeArea().onTapGesture { onCancel() }
            VStack(alignment: .leading, spacing: 13) {
                HStack(spacing: 9) {
                    Image(systemName: icon).font(.system(size: 16, weight: .bold)).foregroundStyle(tint)
                    Text(title).font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                    Spacer(minLength: 0)
                    Button { onCancel() } label: { Image(systemName: "xmark.circle.fill").font(.system(size: 22)).foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
                }
                Text("OVER THE LAST").font(.system(size: 10, weight: .black, design: .rounded)).tracking(1.2).foregroundStyle(DioPal.muted)
                Text(fmt(minutes)).font(.system(size: 36, weight: .black, design: .rounded).monospacedDigit()).foregroundStyle(tint).frame(maxWidth: .infinity, alignment: .center)
                Slider(value: $minutes, in: 0.5...5, step: 0.5).tint(tint)
                HStack { Text("0:30").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted); Spacer(); Text("5:00").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted) }
                Button { onGo() } label: {
                    HStack(spacing: 7) { Image(systemName: "sparkles"); Text("Go").font(.system(size: 16, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(.white).frame(maxWidth: .infinity).frame(height: 50)
                        .background(Capsule().fill(LinearGradient(colors: [tint, tint.opacity(0.6)], startPoint: .top, endPoint: .bottom)))
                }.buttonStyle(.plain)
                Text("Runs now.").font(.system(size: 10.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).frame(maxWidth: .infinity, alignment: .center)
            }
            .padding(20).frame(width: 322)
            .background(RoundedRectangle(cornerRadius: 26, style: .continuous).fill(Color(hex: 0x15121C)).overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 1)))
        }
    }
}

// a live-intelligence result, floating by the mic; keep it to drop a card on the desk
struct DioLiveIntelCard: View {
    let card: LiveIntelCard; let onKeep: () -> Void; let onDismiss: () -> Void
    private func fmt(_ m: Double) -> String { let s = Int(m * 60); return String(format: "%d:%02d", s / 60, s % 60) }
    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack(spacing: 6) {
                Image(systemName: "sparkles").font(.system(size: 9, weight: .bold)).foregroundStyle(DioPal.violet)
                Text(card.lens.uppercased()).font(.system(size: 9, weight: .heavy, design: .rounded)).tracking(1).foregroundStyle(DioPal.violet)
                Text("· last \(fmt(card.minutes))").font(.system(size: 9, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
                Spacer(minLength: 0)
                Button { onDismiss() } label: { Image(systemName: "xmark").font(.system(size: 9, weight: .black)).foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
            }
            if card.thinking {
                TimelineView(.animation) { tl in
                    let t = tl.date.timeIntervalSinceReferenceDate
                    HStack(spacing: 5) { ForEach(0..<3, id: \.self) { i in Circle().fill(DioPal.violet.opacity(0.4 + 0.5 * (0.5 + 0.5 * sin(t * 4 + Double(i) * 0.7)))).frame(width: 6, height: 6) } }
                }
            } else if let txt = card.text {
                Text(txt).font(.system(size: 12, weight: .medium, design: .rounded)).foregroundStyle(txt.hasPrefix("⚠️") ? Color(hex: 0xFFB4A0) : DioPal.text.opacity(0.92)).lineLimit(7)
                if !txt.hasPrefix("⚠️") {
                    Button { onKeep() } label: { HStack(spacing: 4) { Image(systemName: "tray.and.arrow.down.fill").font(.system(size: 9, weight: .bold)); Text("Keep").font(.system(size: 10, weight: .heavy, design: .rounded)) }.foregroundStyle(DioPal.muted) }.buttonStyle(.plain)
                }
            }
        }
        .padding(11).frame(maxWidth: 300, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(Color(hex: 0x171320).opacity(0.97)).overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(DioPal.violet.opacity(0.3), lineWidth: 1)))
        .transition(.move(edge: .leading).combined(with: .opacity))
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
        // The sheet height is geometry-relative, not `UIScreen.main.bounds` (which lies in
        // iPad split-view). The GeometryReader gives us this surface's real height (HSM-20-01).
        GeometryReader { geo in
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
            .frame(maxWidth: .infinity).frame(height: geo.size.height * 0.62)
            .background(UnevenRoundedRectangle(topLeadingRadius: 30, topTrailingRadius: 30, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x191522), Color(hex: 0x0B0910)], startPoint: .top, endPoint: .bottom))
                .overlay(UnevenRoundedRectangle(topLeadingRadius: 30, topTrailingRadius: 30, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)).ignoresSafeArea(edges: .bottom))
        }
        }
    }
}

// A compact, corner-tucked record button — present but not shouting. One tap arms the mic.
struct DioRecordOrb: View {
    let onTap: () -> Void
    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                ForEach(0..<2) { i in
                    let p = (sin(t * 1.3 + Double(i) * 1.6) * 0.5 + 0.5)
                    Circle().stroke(DioPal.accent.opacity(0.28 * (1 - p)), lineWidth: 1.5)
                        .frame(width: 60 + CGFloat(p) * 26, height: 60 + CGFloat(p) * 26)
                }
                // The disc matches the New FAB's 64pt circle so the two bottom controls read as a pair
                // (owner: the Record circle looked optically smaller than New — it was 46 vs 64).
                Circle().fill(RadialGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent, Color(hex: 0xC23C16)],
                                             center: .init(x: 0.4, y: 0.35), startRadius: 1, endRadius: 34))
                    .frame(width: 64, height: 64).shadow(color: DioPal.accent.opacity(0.55), radius: 12, y: 4)
                Image(systemName: "mic.fill").font(.system(size: 24, weight: .bold)).foregroundStyle(.white)
            }
            .scaleEffect(1 + CGFloat(sin(t * 2) * 0.02)).frame(width: 72, height: 72).contentShape(Circle())
        }
        .onTapGesture(perform: onTap)
    }
}

// THE ROUTE SHEET — drop a primitive on the AI core → pick a lens (or write a prompt) → Ask.
// A pending route through an agent/chain whose "where it runs" the user is choosing —
// on this iPad (on-device) or on the paired Mac (the hub's big model). Captured so the
// run target sheet can fire the right path with the card's text intact.
// The RUNS-ON choice the user can remember (Phase-15 fluid compute) — on this iPad or your desktop.
// (Named `DeskRunTarget` to avoid colliding with RuntimeCore's workflow-step `RunTarget`.)
enum DeskRunTarget: String { case device, mac }

struct PendingHubRun: Identifiable, Equatable {
    // HSM-22-04: a workflow joins the runs-on choice — its graph travels, so the
    // hub can finally run it (the linear subset; refusals ride back as a warning).
    enum Kind: Equatable { case agent(AgentRecord); case chain(ChainRecord); case workflow(WorkflowRecord) }
    let id = UUID()
    let kind: Kind
    let input: String
    let inputId: String            // the routed primitive's id — the lineage's "from" card
    let inputTitle: String
    var name: String { switch kind { case .agent(let a): return a.name.isEmpty ? "Agent" : a.name
                                      case .chain(let c): return c.name.isEmpty ? "Crew" : c.name
                                      case .workflow(let w): return w.name.isEmpty ? "Workflow" : w.name } }
    var isChain: Bool { if case .chain = kind { return true }; return false }
    var isWorkflow: Bool { if case .workflow = kind { return true }; return false }
    // The id + kind of what produced the run — carried into the output's provenance.
    var viaId: String { switch kind { case .agent(let a): return a.id; case .chain(let c): return c.id
                                       case .workflow(let w): return w.id } }
    var viaKind: String { isChain ? "chain" : (isWorkflow ? "workflow" : "agent") }
    // The lineage record stamped onto the resulting OutputRecord.
    var provenance: RunProvenance {
        RunProvenance(sourceCardId: inputId, sourceCardTitle: inputTitle,
                      viaId: viaId, viaName: name, viaKind: viaKind)
    }
}

// WHERE IT RUNS — the Mesh RUNS-ON choice for routing a card through an agent/chain:
// on this iPad (private, on-device) or on your desktop (its big model, LAN egress). When no
// Mac is paired, the hub row is disabled with a clear "pair first" cue; on-device stays
// the default. Premium DioPal sheet — never a flat picker.
struct DioRunTargetSheet: View {
    let run: PendingHubRun
    let paired: Bool
    let peerLabel: String          // e.g. "192.168.1.43" — what the hub row names
    var preferred: DeskRunTarget = .device   // the remembered/sensible default — pre-highlighted
    var remembered: Bool = false         // true once the user has made an explicit pick
    let onDevice: () -> Void
    let onHub: () -> Void
    let onCancel: () -> Void
    @State private var shown = false
    var body: some View {
        ZStack {
            Color.black.opacity(0.6).ignoresSafeArea().onTapGesture { onCancel() }
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 9) {
                    Image(systemName: run.isChain ? "arrow.triangle.branch"
                          : (run.isWorkflow ? "point.topleft.down.curvedto.point.bottomright.up" : "person.crop.square.fill"))
                        .font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                        .frame(width: 36, height: 36).background(Circle().fill(DioPal.accent))
                    VStack(alignment: .leading, spacing: 1) {
                        Text("Run \(run.name)").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text("where should it run?").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                    Spacer(minLength: 0)
                }
                // ON DEVICE — the default, private, no network.
                runRow(icon: DeviceLabel.current == "iPhone" ? "iphone" : "ipad", tint: DioPal.mint, name: "On this \(DeviceLabel.current)",
                       sub: "private · no network", egress: .local, enabled: true,
                       isDefault: preferred == .device, action: onDevice)
                // ON YOUR MAC — the hub's big model; LAN egress; disabled when unpaired.
                runRow(icon: "desktopcomputer", tint: Color(hex: 0xF5A524),
                       name: "On your desktop",
                       sub: paired ? "big model · \(peerLabel)" : "pair your desktop to use its big model",
                       egress: .cloud("your desktop"), enabled: paired,
                       isDefault: paired && preferred == .mac, action: onHub)
                Button(action: onCancel) {
                    Text("Cancel").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted)
                        .frame(maxWidth: .infinity).frame(height: 44).background(Capsule().fill(.white.opacity(0.06)))
                }.buttonStyle(.plain)
            }
            .padding(20).frame(maxWidth: 440)
            .background(RoundedRectangle(cornerRadius: 26, style: .continuous)
                .fill(LinearGradient(colors: [Color(hex: 0x171320), Color(hex: 0x0C0A12)], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(.white.opacity(0.08), lineWidth: 1))
                .shadow(color: .black.opacity(0.6), radius: 30, y: 16))
            .padding(.horizontal, 18).scaleEffect(shown ? 1 : 0.9).opacity(shown ? 1 : 0)
        }
        .transition(.opacity)
        .onAppear { withAnimation(.spring(response: 0.5, dampingFraction: 0.74)) { shown = true } }
    }
    @ViewBuilder private func runRow(icon: String, tint: Color, name: String, sub: String,
                                     egress: EgressScope, enabled: Bool, isDefault: Bool = false,
                                     action: @escaping () -> Void) -> some View {
        // The remembered/sensible choice is pre-highlighted (a brighter ring + glow + a small
        // "Default" cue) so the user can fire it without re-deciding — the override is just the
        // other row, one tap away.
        let highlight = enabled && isDefault
        Button(action: { if enabled { action() } }) {
            HStack(spacing: 12) {
                Image(systemName: icon).font(.system(size: 17, weight: .bold)).foregroundStyle(enabled ? tint : DioPal.muted)
                    .frame(width: 30)
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 7) {
                        Text(name).font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundStyle(enabled ? DioPal.text : DioPal.muted)
                        if highlight {
                            HStack(spacing: 3) {
                                Image(systemName: "checkmark.seal.fill").font(.system(size: 8.5, weight: .black))
                                Text(remembered ? "LAST CHOICE" : "DEFAULT").font(.system(size: 8.5, weight: .black, design: .rounded)).tracking(0.4)
                            }
                            .foregroundStyle(tint)
                            .padding(.horizontal, 7).frame(height: 17)
                            .background(Capsule().fill(tint.opacity(0.16)).overlay(Capsule().strokeBorder(tint.opacity(0.45), lineWidth: 0.8)))
                        }
                    }
                    Text(sub).font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                }
                Spacer(minLength: 0)
                if enabled { EgressBadge(scope: egress) }
                else { Image(systemName: "lock.slash").font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.muted) }
            }
            .padding(13).frame(maxWidth: .infinity)
            .background(RoundedRectangle(cornerRadius: 16).fill(enabled ? tint.opacity(highlight ? 0.16 : 0.10) : Color.white.opacity(0.03))
                .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder((enabled ? tint : Color.white).opacity(highlight ? 0.85 : (enabled ? 0.4 : 0.06)), lineWidth: highlight ? 1.6 : 1))
                .shadow(color: highlight ? tint.opacity(0.35) : .clear, radius: highlight ? 12 : 0, y: highlight ? 4 : 0))
        }.buttonStyle(.plain).opacity(enabled ? 1 : 0.7)
    }
}

struct DioRouteSheet: View {
    let sourceTitle: String; let onAsk: (String, String, String) -> Void; let onCancel: () -> Void; let onSaveTool: (String) -> Void
    @State private var lens = RouteLenses.all.first!.name
    @State private var prompt = RouteLenses.all.first!.instruction
    @State private var profileId = InferenceConfigStore.shared.activeProfileId   // which model runs this
    private var resolvedProfile: RuntimeProfile { InferenceConfigStore.shared.resolveProfile(override: profileId) }
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
                    // Honest egress for the CHOSEN profile (was hardcoded "On device").
                    HStack(spacing: 5) {
                        Image(systemName: resolvedProfile.isLocal ? "lock.fill" : "cloud.fill").font(.system(size: 9, weight: .bold))
                        Text(resolvedProfile.isLocal ? "On device" : (resolvedProfile.egressHost ?? "endpoint")).font(.system(size: 10, weight: .heavy, design: .rounded))
                    }.foregroundStyle(resolvedProfile.isLocal ? DioPal.mint : DioPal.accent)
                        .padding(.horizontal, 9).frame(height: 26)
                        .background(Capsule().fill((resolvedProfile.isLocal ? DioPal.mint : DioPal.accent).opacity(0.14)))
                }
                RunsOnPicker(selectedId: $profileId, allowsDefault: true, label: "Runs on")
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
                        .overlay(alignment: .bottomTrailing) { VoiceFillMic(text: $prompt, tint: DioPal.accent, size: 28).padding(8) }
                }
                HStack(spacing: 10) {
                    Button(action: onCancel) { Text("Cancel").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).frame(maxWidth: .infinity).frame(height: 46).background(Capsule().fill(.white.opacity(0.06))) }.buttonStyle(.plain)
                    Button { onAsk(lens, prompt, profileId) } label: {
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
                Text("\(lens) · \(local ? "on this \(DeviceLabel.current) · no network" : "endpoint")").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted)
            }
            .padding(.horizontal, 16).padding(.vertical, 9).background(Capsule().fill(.black.opacity(0.55)))
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom).padding(.bottom, 130)
        }
        .transition(.opacity)
    }
}

// THE PRINTED CARD — the new primitive that just came out of the core. Keep it (lands on the desk) or bin it.
struct DioPrintedCard: View {
    let rec: OutputRecord; let egress: EgressScope; let onKeep: () -> Void; let onBin: () -> Void
    @State private var shown = false
    // honest provenance: a hub run reads "fresh from your desktop", anything else "from the AI core".
    private var freshLine: String {
        if case .cloud(let t) = egress, t == "your desktop" { return "fresh from your desktop" }
        return "fresh from the AI core"
    }
    var body: some View {
        ZStack {
            Color.black.opacity(0.7).ignoresSafeArea().onTapGesture { onBin() }
            VStack(spacing: 0) {
                HStack(spacing: 11) {
                    DeskSprite(name: "note", size: 38)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(rec.title).font(.system(size: 17, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        Text(freshLine).font(.system(size: 11, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).lineLimit(1)
                    }
                    Spacer(minLength: 0)
                    EgressBadge(scope: egress)
                }.padding(.horizontal, 18).padding(.top, 16).padding(.bottom, 8)
                // LINEAGE — where this came from + what produced it ("from Q3 kickoff · via Scout").
                // A crafted chip, not a flat caption: a branch glyph + the source card + the agent/chain.
                if let p = rec.provenance, !p.line.isEmpty {
                    DioLineageRow(provenance: p).padding(.horizontal, 18).padding(.bottom, 8)
                }
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

// THE LINEAGE ROW — the crafted "from <source card> · via <agent/chain>" line on a run result.
// Not a flat caption: a tinted source-card pill, a flowing connector glyph, and a via-pill that
// reads the agent vs crew icon. Reused by the printed card; the Output pull-out carries the same
// text in its subtitle. Honest provenance the user (and the synced Artifact) can trust.
struct DioLineageRow: View {
    let provenance: RunProvenance
    private var viaIsChain: Bool { provenance.viaKind == "chain" }
    var body: some View {
        HStack(spacing: 7) {
            // FROM — the input card.
            HStack(spacing: 5) {
                Image(systemName: "doc.text.fill").font(.system(size: 9, weight: .bold)).foregroundStyle(DioPal.accent.opacity(0.9))
                Text(provenance.sourceCardTitle.isEmpty ? "a card" : provenance.sourceCardTitle)
                    .font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text.opacity(0.92)).lineLimit(1)
            }
            .padding(.horizontal, 9).frame(height: 24)
            .background(Capsule().fill(DioPal.accent.opacity(0.12)).overlay(Capsule().strokeBorder(DioPal.accent.opacity(0.3), lineWidth: 0.8)))
            // the flow connector
            Image(systemName: "arrow.right").font(.system(size: 9, weight: .black)).foregroundStyle(DioPal.muted.opacity(0.8))
            // VIA — the agent/chain that produced it.
            HStack(spacing: 5) {
                Image(systemName: viaIsChain ? "arrow.triangle.branch" : "sparkles")
                    .font(.system(size: 9, weight: .bold)).foregroundStyle(DioPal.mint)
                Text(provenance.viaName.isEmpty ? (viaIsChain ? "a crew" : "an agent") : provenance.viaName)
                    .font(.system(size: 11, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.mint).lineLimit(1)
            }
            .padding(.horizontal, 9).frame(height: 24)
            .background(Capsule().fill(DioPal.mint.opacity(0.12)).overlay(Capsule().strokeBorder(DioPal.mint.opacity(0.32), lineWidth: 0.8)))
            Spacer(minLength: 0)
        }
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
// HSM-21-01: the words + symbol + honest tint split come from the Contracts `EgressScope`
// grammar; only the chrome is this app's.
struct EgressBadge: View {
    let scope: EgressScope
    var body: some View {
        let tint: Color = scope.leavesDevice ? Color(hex: 0xF5A524) : DioPal.mint
        HStack(spacing: 5) {
            Image(systemName: scope.symbolName).font(.system(size: 9, weight: .bold))
            Text(scope.label).font(.system(size: 10, weight: .heavy, design: .rounded))
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
                        Text("Pair your desktop to send").font(.system(size: 10.5, weight: .heavy, design: .rounded))
                    }.foregroundStyle(DioPal.muted).padding(.horizontal, 10).frame(height: 28).background(Capsule().fill(.white.opacity(0.05)))
                }
                Text("SEND TO").font(.system(size: 10.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(1.4)
                VStack(spacing: 8) {
                    ForEach(connectors, id: \.connId) { c in
                        Button { onSend(c.connId, c.name) } label: {
                            actRow(symbol: c.symbol, tint: c.tint, name: "Send to \(c.name)", sub: configured ? "via your desktop" : "needs your desktop", egress: .cloud(c.name))
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
    @ViewBuilder private func actRow(symbol: String, tint: Color, name: String, sub: String, egress: EgressScope) -> some View {
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
// HoldSpeak actuator framework (propose→approve→execute, Phase 37/38/61) via /api/desk/actuators/slack/*.
struct DeskHostLink {
    let host: String; let port: Int
    // The hub's web auth token. A LAN/non-loopback bind REQUIRES it, so every authed request rides
    // `Authorization: Bearer <token>` — without this the companion (Slack/webhook) routes 401.
    var token: String = ""
    enum HostError: Error { case message(String) }
    private var base: URL? { URL(string: "http://\(host):\(port)") }
    private func auth(_ r: inout URLRequest) {
        let t = token.trimmingCharacters(in: .whitespaces)
        if !t.isEmpty { r.setValue("Bearer \(t)", forHTTPHeaderField: "Authorization") }
    }

    func reachable() async -> Bool {
        guard let u = base?.appendingPathComponent("health") else { return false }
        var r = URLRequest(url: u); r.timeoutInterval = 4; auth(&r)
        if let (_, resp) = try? await URLSession.shared.data(for: r), (resp as? HTTPURLResponse)?.statusCode == 200 { return true }
        return false
    }
    /// Which desk connectors the HOST actually has configured (HSM-21-03; booleans only —
    /// GET /api/desk/actuators/status, HS-77-03: the URLs are credentials and never ride).
    /// nil on any failure so the caller keeps its previous knowledge instead of guessing.
    func connectorStatus() async -> [String: Bool]? {
        guard let u = base?.appendingPathComponent("api/desk/actuators/status") else { return nil }
        var r = URLRequest(url: u); r.timeoutInterval = 6; auth(&r)
        guard let (data, resp) = try? await URLSession.shared.data(for: r),
              (resp as? HTTPURLResponse)?.statusCode == 200,
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
        return ["slack": obj["slack_configured"] as? Bool ?? false,
                "webhook": obj["webhook_configured"] as? Bool ?? false,
                "github": obj["github_configured"] as? Bool ?? false]
    }
    /// Propose an arbitrary-text send on the host for a target ("slack"/"webhook") → (proposalId, preview).
    func propose(target: String, title: String, text: String) async throws -> (id: String, preview: String) {
        var body: [String: Any] = ["text": text]
        if !title.isEmpty { body["title"] = title }
        let (data, resp) = try await post("api/desk/actuators/\(target)/propose", body)
        try Self.check(data, resp, "Your desktop refused the send.")
        let p = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["proposal"] as? [String: Any]
        return (p?["id"] as? String ?? "", p?["preview"] as? String ?? text)
    }
    /// Approve (→ execute) or reject the proposal on the host → (status, error?).
    func decide(target: String, id: String, approved: Bool) async throws -> (status: String, error: String?) {
        let (data, resp) = try await post("api/desk/actuators/\(target)/\(id)/decision",
                                          ["decision": approved ? "approved" : "rejected", "decided_by": "ipad-desk"])
        try Self.check(data, resp, "Your desktop refused the decision.")
        let p = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["proposal"] as? [String: Any]
        return (p?["status"] as? String ?? "", p?["error"] as? String)
    }
    private func post(_ path: String, _ body: [String: Any]) async throws -> (Data, URLResponse) {
        guard let u = base?.appendingPathComponent(path) else { throw HostError.message("No desktop paired.") }
        var r = URLRequest(url: u); r.httpMethod = "POST"; r.timeoutInterval = 14
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        auth(&r)
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
    // The ONE width authority (HSM-20-01). Read the size class here; the camera is derived
    // per-frame inside the body's GeometryReader where the live width is known.
    @Environment(\.horizontalSizeClass) private var hSizeClass
    @StateObject private var model = CaptureModel()
    @AppStorage("hs.diorama.pos") private var posCSV = ""
    @AppStorage("hs.diorama.zones") private var zonesCSV = ""
    @AppStorage("hs.diorama.filed") private var dfiledCSV = ""
    @AppStorage("hs.desk.kbs") private var kbsCSV = ""          // LEGACY (classic home) — migrated into kbs on load
    @AppStorage("hs.desk.filed") private var kbFiledCSV = ""
    @AppStorage("hs.diorama.kbs") private var kbsJSON = ""      // the desk's own KB primitives (id/name/path/items)
    @State private var kbs: [KBRecord] = []
    @State private var editingKB: KBRecord? = nil              // the rename editor is open on this KB
    @State private var namingKB = false
    @State private var newKBName = ""
    @State private var landed = false
    @State private var path: [String] = []
    @State private var diveDir = 1
    @State private var flash = 0.0
    @State private var selected: String? = nil
    @State private var capturing = false
    @State private var weaving = false                // the post-stop default pipeline is running
    @State private var weaveStepName = ""             // the REAL current step (weave, then each intelligence lens)
    @State private var weaveDone = 0                  // steps actually completed
    @State private var weaveTotal = 1                 // total steps in this run (1 weave + N deliverables)
    @State private var weaveCancel = false            // user hit "skip to desk"
    @State private var arrivedIds: Set<String> = []   // the freshly-produced meeting + deliverables, glaringly highlighted
    @State private var showRecordPicker = false       // the meeting-vs-desktop hovering choice
    @State private var captureDesktop = false         // this capture is a "talk to the desktop" dictation
    @State private var liveCards: [LiveIntelCard] = [] // live-intelligence results floating by the mic
    @State private var liveTimeline: [(t: Double, len: Int)] = []  // (elapsed, transcript length) samples → time windows
    // the arcade — a pinnable Breakout to play during a boring meeting (DeskArkanoid.swift, follows the component canon)
    @State private var arkadeOpen = false
    @AppStorage("hs.desk.arkanoid.posX") private var arkadeX: Double = 0.5
    @AppStorage("hs.desk.arkanoid.posY") private var arkadeY: Double = 0.46
    // the arcade: games live in the rail's "Play" column; each launches into an ephemeral window
    @State private var openGameId: String? = nil
    @AppStorage("hs.desk.gamewin.posX") private var gameWinX: Double = 0.5
    @AppStorage("hs.desk.gamewin.posY") private var gameWinY: Double = 0.46
    // The in-world note/KB editor is a MOVABLE window on the lane (drag its grab bar, position
    // persists) — the same affordance as a game window, so every primitive you open can be moved.
    @AppStorage("hs.desk.editorwin.posX") private var editorWinX: Double = 0.5
    @AppStorage("hs.desk.editorwin.posY") private var editorWinY: Double = 0.5
    @State private var editorDragStart: CGPoint? = nil
    @AppStorage("hs.diorama.games") private var gamesJSON = ""  // games placed on the desk as primitives
    @State private var placedGames: [GameRecord] = []
    @State private var coders: [CoderSession] = []             // HSM-17 live Claude/Codex sessions on the desk
    @State private var answeringCoder: CoderSession? = nil     // the answer composer is open on this session
    @State private var openCoderSession: CoderSession? = nil   // the live "running coder" feed is open
    @State private var showSettings = false
    @State private var openMeeting: Meeting? = nil
    @State private var positions: [String: CGPoint] = [:]
    @State private var zones: [ZoneRec] = []
    @State private var filed: [String: String] = [:]
    @State private var dragHotZone: String? = nil
    @State private var namingZone = false
    @State private var pendingFileId: String? = nil   // a primitive to file into the zone being created (lane "New zone…")
    @State private var iconPick: IconPickTarget? = nil          // the object whose icon the user is choosing
    private let spriteKinds: Set<PrimitiveKind> = [.meeting, .note, .kb]   // kinds whose icon you can pick
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
    @AppStorage("hs.diorama.notes") private var notesJSON = ""  // first-class notes you write + place
    @State private var notes: [NoteRecord] = []
    @State private var editingNote: NoteRecord? = nil          // the note editor is open on this draft
    @State private var dragHotObjectId: String? = nil          // a compatible route target under a dragged primitive
    @State private var routeSourceId: String? = nil
    @State private var routeLensRun = ""
    @State private var showRouteSheet = false
    @State private var routing = false
    @State private var routeFrom: CGPoint = .zero
    @State private var routeTo: CGPoint = .zero
    @State private var printed: OutputRecord? = nil
    // the egress of the CURRENT printed card — on-device routes are .local; a hub run is
    // .cloud("your desktop"). Drives the printed card's honest egress badge (POSITIONING canon).
    @State private var printedEgress: EgressScope = .local
    @State private var routeError: String? = nil
    // connectors (the integrations half: drop an output on Slack → approve → the MAC sends).
    // Routed through the paired host PC — the iPad holds no credential. Reuses the desk's Mac pairing.
    @AppStorage("hs.peer.host") private var peerHost = ""
    @AppStorage("hs.peer.port") private var peerPort = "8000"
    @AppStorage("hs.peer.token") private var peerToken = ""   // hub web auth token (LAN bind requires it)
    @AppStorage("hs.peer.name") private var peerName = ""     // friendly name for the paired Mac
    // The remembered RUNS-ON choice (Phase-15 fluid compute) — "" = unset (sensible default),
    // "device" = on this iPad, "mac" = on your desktop. The picker still opens; it just pre-honors
    // the last pick so the user isn't re-choosing every run. Falls back to on-device when unpaired.
    @AppStorage("hs.desk.runtarget") private var runTargetPref = ""
    @State private var sendSourceId: String? = nil
    @State private var sendTargetName = ""
    @State private var sendTargetConn = "slack"          // which host connector ("slack" / "webhook")
    // HSM-21-03: the host's REAL per-connector config (GET /api/desk/actuators/status),
    // refreshed on every sync. nil = not read yet (an older hub / no read) → the tile keeps
    // the paired-only behavior rather than guessing in either direction.
    @State private var connConfigured: [String: Bool]? = nil
    @State private var sendOverride: (title: String, text: String)? = nil   // act-on-item: send THIS, not a whole card
    @State private var actItem: (title: String, text: String, source: String)? = nil   // the row being acted on
    @State private var showActSheet = false
    @State private var showSendCard = false
    @State private var sending = false
    @State private var connecting = false
    @State private var railOpen = false   // iPhone (compact): the agent rail collapses behind an edge tab
    @State private var laneFilter = "all" // iPhone (.lane): the active kind-filter chip in the card column
    @State private var sentToast: String? = nil
    @State private var summonSource: String? = nil       // the card being routed (radial summon active)
    @State private var summonAt: CGPoint = .zero          // where the radial centers (the card's position)
    // tailored agents — characters you build (avatar + system prompt + context); ask them or route cards through them
    @AppStorage("hs.diorama.agents") private var agentsJSON = ""
    @State private var agents: [AgentRecord] = []
    @State private var editingAgent: AgentRecord? = nil  // builder open with this draft (new or existing)
    @State private var openAgent: AgentRecord? = nil      // the agent conversation is open
    @AppStorage("hs.diorama.agentchats") private var agentChatsJSON = ""
    @State private var agentChats: [String: [AgentMessage]] = [:]   // per-agent conversation threads
    // agent chains (crews) — Scout → Critic → Editor, run in order
    @AppStorage("hs.diorama.chains") private var chainsJSON = ""
    @State private var chains: [ChainRecord] = []
    // LIVE SYNC (THE PRIMITIVE FRAMEWORK, wave 2) — the desk's primitives port into the
    // paired desktop hub (the canonical store) and flow back. LWW by meta.last_modified;
    // the iPad's `updatedAt` projection is a side map id→instant (layout never syncs).
    @AppStorage("hs.diorama.synctimes") private var syncTimesJSON = ""   // id → last_modified
    @AppStorage("hs.diorama.tombstones") private var tombstonesJSON = "" // "kind:id" → deleted_at
    @State private var syncModified: [String: Date] = [:]
    @State private var syncTombstones: [String: Date] = [:]
    @State private var syncing = false
    @State private var lastSyncSummary: String? = nil
    // the FELT sync status (drives DioSyncStatus): the last pass outcome + when it landed,
    // so the desk shows syncing / synced·"2m ago" / offline / error — never a bare spinner.
    @State private var syncState: DeskSyncState = .idle
    @State private var lastSyncedAt: Date? = nil
    // bare ids confirmed canonical on the hub this session (pushed or applied on a reached pass)
    // → the per-primitive cue can honestly show "synced" vs "pending". Cleared by a fresh edit.
    @State private var syncConfirmed: Set<String> = []
    // ids the LAST pull brought in fresh (a note authored on the web, etc.) → they arrive on
    // the desk with the NEW-arrival treatment (reuses `arrivedIds`), so cross-surface sync is seen.
    @State private var editingChain: ChainRecord? = nil   // chain builder open
    @State private var editingZone: ZoneRec? = nil        // the zone style editor is open
    @State private var runChainSheet: ChainRecord? = nil  // the run/manage sheet
    // RUN ON THE HUB (the Mesh "RUNS ON: your desktop") — routing a card through an agent/chain
    // offers running it on the desktop hub's big model instead of on-device. The choice
    // sheet captures the pending run; the hub run lands a printed card with a cloud egress.
    @State private var pendingHubRun: PendingHubRun? = nil  // the run/where-it-runs picker is open
    @State private var chainRelay: ChainRecord? = nil     // the live relay overlay
    @State private var chainStep = 0
    @State private var chainResults: [String] = []
    private let diveSpring = Animation.spring(response: 0.6, dampingFraction: 0.74)
    private let focusSpring = Animation.spring(response: 0.5, dampingFraction: 0.72)
    private let dockSpring = Animation.spring(response: 0.5, dampingFraction: 0.84)

    private var pathKey: String { path.joined(separator: "/") }
    private var curTint: Color { path.isEmpty ? DioPal.accent : tintFor(pathKey) }
    private func tintFor(_ zpath: String) -> Color {
        if let z = zones.first(where: { $0.path == zpath }) { return z.tint }
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
    private var knowledgeBases: [String] { kbs.map(\.name) }   // the agent builder picks a KB by name

    // MEETING DRAWER (group by lineage) — an output belongs to a meeting if it was routed FROM it
    // (`provenance.sourceCardId == "m:<id>"`) or its `source` is that meeting's title. Such outputs
    // live INSIDE the meeting's drawer, not loose on the desk.
    private func derivativesOf(_ m: Meeting) -> [OutputRecord] {
        let mid = "m:\(m.id)"; let title = MeetingPrimitive(meeting: m, index: 0).title
        return outputs.filter { ($0.provenance?.sourceCardId == mid) || (!$0.source.isEmpty && $0.source == title) }
    }
    // Every output id that sits in some meeting's drawer (so the loose desk/lane lists skip them).
    private var meetingDerivedOutputIds: Set<String> {
        var ids = Set<String>()
        for m in meetings { for d in derivativesOf(m) { ids.insert("out:\(d.id)") } }
        return ids
    }

    // EVERYTHING is a DeskPrimitive — built here from the live model.
    // CONTENT lives on the desk (meetings, generated outputs, knowledge); TOOLS live in the dock.
    private func contentMembers() -> [any DeskPrimitive] {
        var out: [any DeskPrimitive] = []
        let derived = meetingDerivedOutputIds
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == pathKey { out.append(MeetingPrimitive(meeting: m, index: i, derivatives: derivativesOf(m))) }
        for rec in outputs where rec.path == pathKey && !derived.contains("out:\(rec.id)") { out.append(OutputPrimitive(rec: rec)) }
        for rec in notes where rec.path == pathKey { out.append(NotePrimitive(rec: rec)) }
        for rec in kbs where rec.path == pathKey { out.append(KBPrimitive(rec: rec)) }   // KBs live anywhere now
        for rec in placedGames where rec.path == pathKey { out.append(gamePrim(rec)) }   // games placed on the desk
        if path.isEmpty { for s in coders where s.state != .ended { out.append(AgentSessionPrimitive(session: s)) } }  // live coders at the desk root
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
                                      paired: hostLink != nil, configured: connReady("slack"),
                                      detail: peerHost.isEmpty ? "" : peerHost))
        out.append(ConnectorPrimitive(connId: "webhook", name: "Webhook", symbol: "bolt.horizontal.fill", tint: DioPal.cobalt,
                                      paired: hostLink != nil, configured: connReady("webhook"),
                                      detail: peerHost.isEmpty ? "" : peerHost))
        out.append(ConnectorPrimitive(connId: "github", name: "GitHub", symbol: "exclamationmark.bubble.fill", tint: DioPal.mint,
                                      paired: hostLink != nil, configured: connReady("github"),
                                      detail: peerHost.isEmpty ? "" : peerHost))
        for wf in workflows { out.append(WorkflowPrimitive(rec: wf)) }
        return out
    }
    private func agentMembers() -> [any DeskPrimitive] { agents.map { AgentPrimitive(rec: $0) } }
    private func chainMembers() -> [any DeskPrimitive] { chains.filter { !$0.steps.isEmpty }.map { ChainPrimitive(rec: $0) } }
    private func members() -> [any DeskPrimitive] { contentMembers() + toolMembers() + agentMembers() + chainMembers() }
    private var hostLink: DeskHostLink? {
        let h = peerHost.trimmingCharacters(in: .whitespaces)
        guard !h.isEmpty, let p = Int(peerPort.trimmingCharacters(in: .whitespaces)), p > 0 else { return nil }
        return DeskHostLink(host: h, port: p, token: peerToken)
    }
    /// The status the chip shows — reconciles the raw last-pass `syncState` against the live
    /// truth (no peer paired ⇒ unpaired; a pass in flight ⇒ syncing) so the pill never lies.
    private var liveSyncState: DeskSyncState {
        if hostLink == nil { return .unpaired }
        if syncing { return .syncing }
        return syncState
    }
    /// The per-primitive sync cue: canonical (synced this session) vs pending (edited, not yet
    /// confirmed) vs local-only (games, by design). Honest — never claims "synced" without a peer.
    private func syncCue(for prim: any DeskPrimitive) -> PrimSyncCue {
        // games never sync; show the honest local-only mark wherever they sit
        if prim.kind == .game { return .localOnly }
        guard hostLink != nil else { return .none }
        // only the durable, syncable classes carry a canonical/pending cue
        let syncable: Set<PrimitiveKind> = [.note, .agent, .kb, .artifact, .chain, .workflow]
        guard syncable.contains(prim.kind) else { return .none }
        // the bare record id (the side maps are keyed bare; the primitive id is "kind:bare")
        let bare = prim.id.contains(":") ? String(prim.id.split(separator: ":", maxSplits: 1)[1]) : prim.id
        // confirmed canonical on the hub this session?
        if syncConfirmed.contains(bare) { return .synced }
        // edited/created locally with a stamped instant but not yet confirmed pushed
        if syncModified[bare] != nil { return .pending }
        return .pending
    }
    private func membersOf(_ zpath: String) -> [any DeskPrimitive] {
        var out: [any DeskPrimitive] = []
        for (i, m) in meetings.enumerated() where (filed["m:\(m.id)"] ?? "") == zpath { out.append(MeetingPrimitive(meeting: m, index: i)) }
        for rec in outputs where rec.path == zpath { out.append(OutputPrimitive(rec: rec)) }   // filed agent/lens outputs
        for rec in notes where rec.path == zpath { out.append(NotePrimitive(rec: rec)) }       // filed notes
        for rec in kbs where rec.path == zpath { out.append(KBPrimitive(rec: rec)) }           // filed KBs
        for rec in placedGames where rec.path == zpath { out.append(gamePrim(rec)) }           // filed games
        return out
    }
    // build a GamePrimitive from a placement, reading the live best score + display name/title
    private func gamePrim(_ rec: GameRecord) -> GamePrimitive {
        let name = rec.gameId == "arkanoid" ? "Arkanoid" : (MiniGames.game(rec.gameId)?.title ?? rec.gameId.capitalized)
        let best = UserDefaults.standard.integer(forKey: "hs.mg.\(rec.gameId).best")
        return GamePrimitive(gameId: rec.gameId, name: name, best: best, path: rec.path)
    }
    private func meeting(forObj id: String) -> Meeting? {
        guard id.hasPrefix("m:") else { return nil }
        let mid = String(id.dropFirst(2)); return model.meetings.first { $0.id == mid }
    }
    private func selectedPrim() -> (any DeskPrimitive)? {
        if let m = members().first(where: { $0.id == selected }) { return m }
        // a derivative opened from its meeting's drawer is hidden from the loose lists — resolve it directly
        if let id = selected, id.hasPrefix("out:"), let o = outputs.first(where: { "out:\($0.id)" == id }) { return OutputPrimitive(rec: o) }
        return nil
    }
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
    // The count-driven column count: more items → more columns (so the desk SPREADS as it fills,
    // instead of stacking 3-wide forever). Paired with `densityScale` (objects shrink to a floor).
    private func looseCols(_ n: Int) -> Int { n <= 4 ? 2 : (n <= 9 ? 3 : (n <= 16 ? 4 : 5)) }
    // Objects shrink as the scene fills, clamped to a usability floor (~0.62 → still a real tap target +
    // readable glyph). Past the floor, columns keep spreading rather than shrinking into confetti.
    private func densityScale(_ n: Int) -> CGFloat { n <= 6 ? 1.0 : max(0.62, 1.0 - 0.05 * CGFloat(n - 6)) }
    private func looseHome(_ i: Int, _ n: Int, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        let cols = max(1, min(looseCols(n), n)); let r = i / cols, c = i % cols
        let rows = max(1, Int(ceil(Double(n) / Double(cols))))
        // Spread across the usable canvas (clear of the top chrome and the bottom orb dock) and widen
        // the band as rows grow, so a full desk uses the whole surface instead of a cramped middle strip.
        let yTop = 0.30, yBot = rows <= 2 ? 0.58 : 0.80
        let x = cols == 1 ? 0.5 : 0.16 + 0.68 * Double(c) / Double(cols - 1)
        let y = rows == 1 ? 0.52 : yTop + (yBot - yTop) * Double(r) / Double(rows - 1)
        return CGPoint(x: w * x, y: h * y)
    }
    private func pos(_ id: String, _ fallback: CGPoint, _ w: CGFloat, _ h: CGFloat) -> CGPoint {
        if selected == id { return CGPoint(x: w * 0.24, y: h * 0.44) }
        if let u = positions[id] { return CGPoint(x: w * u.x, y: h * u.y) }
        return fallback
    }
    // the record button's tucked-away corner home (bottom-left), shared by the button + the first-boot trail
    // The bottom controls hug the bottom safe edge, not a 0.9·h fraction (which left a big dead band
    // below them — owner: "so much farther than the base bottom line"). `h` is the safe height, so the
    // safe bottom is y == h; sit the orb+label VStack just above it.
    private func orbPos(_ w: CGFloat, _ h: CGFloat) -> CGPoint { CGPoint(x: 58, y: h - 24) }

    private var diveTransition: AnyTransition {
        diveDir >= 0
            ? .asymmetric(insertion: .scale(scale: 0.6).combined(with: .opacity), removal: .scale(scale: 1.6).combined(with: .opacity))
            : .asymmetric(insertion: .scale(scale: 1.6).combined(with: .opacity), removal: .scale(scale: 0.6).combined(with: .opacity))
    }

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            // The desk is full-bleed (.ignoresSafeArea below), so `h` is the SAFE height but every
            // element is laid out from the PHYSICAL top/bottom. These are the real device insets
            // (Dynamic Island / home indicator) — top/bottom chrome must clear them by hand.
            let topInset = geo.safeAreaInsets.top, botInset = geo.safeAreaInsets.bottom
            // The one width authority — size class first, this frame's width second. Every
            // stray `w < 500` / `w >= 500` / `UIScreen.main.bounds` read folds into this.
            let camera = DeskCamera.resolve(sizeClass: hSizeClass, width: w)
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

                // The decorative title is hidden on a phone (compact) — it collided with the corner
                // affordances; the desk needs that scarce top width for the pill + create cluster.
                VStack(spacing: 3) {
                    Text("HoldSpeak").font(.system(size: 25, weight: .black, design: .rounded)).foregroundStyle(DioPal.text)
                    Text("drag a meeting onto a zone · tap to open")
                        .font(.system(size: 12, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                }
                .opacity(landed && selected == nil && path.isEmpty && !firstRun && camera.isWide ? 1 : 0)
                .frame(maxHeight: .infinity, alignment: .top).padding(.top, h * 0.05)

                // THE FIRST BOOT — the cold-start ritual: an empty desk that teaches itself
                if firstRun && landed && selected == nil && summonSource == nil {
                    DioFirstBoot(w: w, h: h)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.035).transition(.opacity).zIndex(5)
                    // the guiding trail — energy flows from the lesson down to the corner record button
                    TimelineView(.animation) { tl in
                        let phase = tl.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: 1) * -10
                        let orb = orbPos(w, h)
                        Path { p in p.move(to: CGPoint(x: w * 0.5, y: h * 0.52)); p.addQuadCurve(to: CGPoint(x: orb.x, y: orb.y - 46), control: CGPoint(x: w * 0.30, y: h * 0.72)) }
                            .stroke(LinearGradient(colors: [DioPal.violet.opacity(0.0), DioPal.violet.opacity(0.55), DioPal.accent.opacity(0.8)], startPoint: .top, endPoint: .bottom),
                                    style: StrokeStyle(lineWidth: 2, lineCap: .round, dash: [2.5, 8], dashPhase: phase))
                    }
                    .allowsHitTesting(false).zIndex(5)
                    Text("Tap to record your first meeting")
                        .font(.system(size: 12.5, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
                        .position(x: min(w - 130, orbPos(w, h).x + 96), y: orbPos(w, h).y - 4).zIndex(6).allowsHitTesting(false)
                }

                // an empty zone you dived into — teach how to fill it (you file from the desk; or nest deeper).
                // DIORAMA ONLY: on the iPad the canvas is genuinely blank, so the centred card fits. On the
                // lane the zone still lists the global toolkit (connectors/models/agents), so a centred card
                // would land ON those rows (text-on-text) and falsely read "empty" — the lane gets a compact
                // inline hint at the top of the column instead (see laneColumn).
                if emptyZone && !camera.isLane && landed && selected == nil {
                    DioZoneEmpty(name: name(of: pathKey), tint: curTint, onNewSubzone: { haptic(.light); namingZone = true })
                        .frame(maxWidth: .infinity, maxHeight: .infinity).zIndex(5).transition(.opacity)
                }

                // The desk reflows by camera: the lit diorama on iPad (.wide/.narrow), the one-thumb
                // card column on iPhone (.lane). `positions[id]` is untouched either way, so rotating
                // back to .wide restores the exact hand-arranged desk (HSM-20-02).
                ForEach([pathKey], id: \.self) { _ in
                    if camera.isLane {
                        // While recording/weaving, the ambient recorder OWNS the lane surface. Hiding the
                        // card column stops the live UI (transcript, ASK LIVE lenses, agent markers, STOP)
                        // from rendering on top of the list and colliding with every row. (Device
                        // punch-list: recording overlapped everything on the phone.) The iPad diorama keeps
                        // the ambient-over-canvas design — its canvas is sparse, not a dense column.
                        if !(capturing || weaving) { laneColumn(w, h, topInset, botInset) }
                    } else { level(w, h) }
                }
                    .transition(diveTransition)

                // On the lane, the in-world note/KB editors live in `level` — which the lane replaces —
                // so render them here as a shared lifted card over a transparent catcher (no scrim).
                if camera.isLane, editingNote != nil || editingKB != nil {
                    Color.clear.contentShape(Rectangle()).ignoresSafeArea()
                        .onTapGesture { commitInlineEdit() }.zIndex(58)
                    let isNote = editingNote != nil
                    let cardW = camera.cardWidth(isNote ? 304 : 288, in: w)
                    let cardH: CGFloat = isNote ? 320 : 170
                    let pin = editorWinPin(w, h, cardW: cardW, cardH: cardH + 30)
                    VStack(spacing: 0) {
                        // grab bar — drag the window anywhere, the spot persists (like a game window)
                        ZStack {
                            Capsule().fill(.white.opacity(0.10)).frame(width: 60, height: 22)
                            Capsule().fill(.white.opacity(0.55)).frame(width: 38, height: 5)
                        }
                            .frame(maxWidth: .infinity).frame(height: 30).contentShape(Rectangle())
                            .gesture(
                                DragGesture(coordinateSpace: .global)
                                    .onChanged { v in
                                        if editorDragStart == nil { editorDragStart = pin }
                                        editorWinX = Double((editorDragStart!.x + v.translation.width) / w)
                                        editorWinY = Double((editorDragStart!.y + v.translation.height) / h)
                                    }
                                    .onEnded { _ in editorDragStart = nil }
                            )
                        if let n = editingNote {
                            DioInlineNoteCard(note: editingNoteBinding(n), onDone: { commitNote() }, onDelete: { deleteNote("note:\(n.id)") }).id(n.id)
                        } else if let k = editingKB {
                            DioInlineKBCard(kb: editingKBBinding(k), onDone: { commitKB() }, onDelete: { deleteKB("kb:\(k.id)") }).id(k.id)
                        }
                    }
                    .frame(width: cardW)
                    .position(pin)
                    .zIndex(60)
                }

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

                // THE LANE CONTROL DOCK — the Record orb (bottom-left) and the New FAB (bottom-right)
                // float over the scrolling card column; mid-scroll, rows used to collide with them. A
                // SOLID bottom base (the desk colour, seamless with the bg) OCCLUDES the column under
                // the controls, with a short gradient lip for softness — so a row scrolling past simply
                // disappears into the desk instead of clashing with the orbs. (Device punch-list: the
                // overlap gripe — a faint fade wasn't enough; the base must actually hide the rows.)
                if camera.isLane && landed && selected == nil && summonSource == nil && !capturing
                    && editingNote == nil && editingKB == nil && !connecting
                    && !showRouteSheet && !routing && printed == nil && !showSendCard && !showActSheet {
                    VStack(spacing: 0) {
                        LinearGradient(colors: [.clear, DioPal.bgBot], startPoint: .top, endPoint: .bottom)
                            .frame(height: 56)
                        DioPal.bgBot.frame(height: 150 + botInset)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
                    .allowsHitTesting(false).ignoresSafeArea().zIndex(71)
                }

                // Qlippy lives on the spacious iPad DIORAMA only. On the phone lane it floated over the
                // scrolling card column and just got in the way (owner: "annoying af too"). It is purely
                // decorative (no tap/gesture), so dropping it on the lane loses nothing.
                if !camera.isLane {
                    DioCompanion(landed: landed, excited: selected != nil)
                        .position(x: w * 0.9, y: h * 0.86)
                }
                if landed && selected == nil && summonSource == nil && !capturing
                    && editingNote == nil && editingKB == nil && !connecting
                    && !showRouteSheet && !routing && printed == nil && !showSendCard && !showActSheet {
                    VStack(spacing: 4) {
                        DioRecordOrb { haptic(.medium); withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) { showRecordPicker = true } }
                        Text("Record").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                    }
                    .position(orbPos(w, h)).transition(.scale.combined(with: .opacity)).zIndex(72)
                }
                // THE LANE FAB — the create cluster lives in `level` (which the lane replaces), so on
                // iPhone the accent FAB carries New Note / New KB / New Zone. A native Menu, not a
                // dimmed sheet (the no-modal law governs primitive editing; a system menu is allowed).
                if camera.isLane && landed && selected == nil && summonSource == nil && !capturing
                    && editingNote == nil && editingKB == nil && !connecting && !showRouteSheet && !routing
                    && printed == nil && !showSendCard && !showActSheet && !firstRun {
                    VStack(spacing: 4) {
                        Menu {
                            Button { createNote() } label: { Label("New Note", systemImage: "square.and.pencil") }
                            Button { createKBInline() } label: { Label("New KB", systemImage: "diamond.fill") }
                            Button { haptic(.light); namingZone = true } label: { Label("New Zone", systemImage: "plus.circle.fill") }
                        } label: {
                            Image(systemName: "plus").font(.system(size: 24, weight: .black)).foregroundStyle(.white)
                                .frame(width: 64, height: 64)
                                .background(Circle().fill(LinearGradient(colors: [Color(hex: 0xFF8A5B), DioPal.accent], startPoint: .top, endPoint: .bottom))
                                    .shadow(color: DioPal.accent.opacity(0.5), radius: 12, y: 4))
                        }.simultaneousGesture(TapGesture().onEnded { haptic(.medium) })
                        Text("New").font(.system(size: 10, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.muted).tracking(0.5)
                    }
                    // mirror the Record orb (bottom-left) on the bottom-right, same baseline
                    .position(x: w - 58, y: orbPos(w, h).y).zIndex(73)
                }
                // a desk-native settings entry (no bouncing to an old screen)
                if landed && selected == nil && summonSource == nil && !capturing && path.isEmpty {
                    Button { haptic(.light); showSettings = true } label: {
                        Image(systemName: "gearshape.fill").font(.system(size: 16, weight: .bold)).foregroundStyle(DioPal.text.opacity(0.85))
                            .frame(width: 42, height: 42).background(Circle().fill(.white.opacity(0.08)).overlay(Circle().strokeBorder(.white.opacity(0.12), lineWidth: 1)))
                    }.buttonStyle(.plain)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading).padding(.top, topInset + 8).padding(.leading, 18).zIndex(70)
                }
                // THE SYNC STATUS — port your primitives to/from the paired Mac (hub), FELT.
                // A premium ambient pill that wears the live state (syncing / synced·"2m ago" /
                // offline·queued / error) instead of a bare spinner. Only when a Mac is paired.
                if landed && selected == nil && summonSource == nil && !capturing && path.isEmpty && connecting == false {
                    Group {
                        if hostLink != nil {
                            // Paired: the live sync pill + a quiet gear to re-open pairing (edit token / forget).
                            HStack(spacing: 8) {
                                DioSyncStatus(state: liveSyncState, lastSyncedAt: lastSyncedAt,
                                              peerLabel: peerName.isEmpty ? peerHost : peerName, onSync: { haptic(.light); syncDesk(reason: "manual") })
                                Button { haptic(.light); withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { connecting = true } } label: {
                                    Image(systemName: "slider.horizontal.3").font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.muted)
                                        .frame(width: 34, height: 34).background(Circle().fill(.white.opacity(0.06)))
                                }.buttonStyle(.plain)
                            }
                        } else {
                            // Unpaired: an inviting "Connect your desktop" pill — the front-door pairing entry
                            // (was unreachable on the desk; pairing lived behind the classic home).
                            Button { haptic(.medium); withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { connecting = true } } label: {
                                HStack(spacing: 8) {
                                    Image(systemName: "laptopcomputer.and.arrow.down").font(.system(size: 13, weight: .bold))
                                    Text("Connect your desktop").font(.system(size: 13, weight: .heavy, design: .rounded))
                                }
                                .foregroundStyle(DioPal.cobalt).padding(.horizontal, 14).frame(height: 38)
                                .background(Capsule().fill(DioPal.cobalt.opacity(0.12)).overlay(Capsule().strokeBorder(DioPal.cobalt.opacity(0.4), lineWidth: 1.2)))
                            }.buttonStyle(.plain)
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                    .padding(.top, topInset + 8).padding(.leading, 18 + 50).zIndex(70)
                    .transition(.scale.combined(with: .opacity))
                }
                // THE RAIL — Agents · Chains · Play. On iPad it sits open at the right; on a phone
                // (compact) it collapses behind a slim edge tab so it never covers the canvas.
                if landed && selected == nil && summonSource == nil && openAgent == nil
                    && editingAgent == nil && editingChain == nil && runChainSheet == nil && chainRelay == nil
                    && openGameId == nil && !arkadeOpen && connecting == false
                    && !showRouteSheet && !routing && printed == nil && !showSendCard && !showActSheet && !firstRun {
                    // NB: the rail (Agents · Chains · Play) stays available DURING a meeting — recording
                    // and playing/answering are not mutually exclusive (owner: the phone can do both).
                    let compact = camera.railCollapses
                    if compact && !railOpen {
                        // the collapsed handle — tap to slide the rail in
                        Button { haptic(.light); withAnimation(.spring(response: 0.42, dampingFraction: 0.82)) { railOpen = true } } label: {
                            VStack(spacing: 5) {
                                Image(systemName: "person.2.fill").font(.system(size: 13, weight: .bold))
                                Image(systemName: "chevron.left").font(.system(size: 10, weight: .black))
                            }
                            .foregroundStyle(DioPal.muted)
                            .padding(.vertical, 13).padding(.horizontal, 7)
                            .background(RoundedRectangle(cornerRadius: 13, style: .continuous).fill(.black.opacity(0.42))
                                .overlay(RoundedRectangle(cornerRadius: 13, style: .continuous).strokeBorder(.white.opacity(0.1), lineWidth: 1)))
                        }.buttonStyle(.plain)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                        .padding(.trailing, 6).zIndex(64).transition(.move(edge: .trailing).combined(with: .opacity))
                    } else {
                        if compact {
                            // tap the canvas to dismiss the rail (transparent, no scrim)
                            Color.clear.contentShape(Rectangle()).ignoresSafeArea()
                                .onTapGesture { withAnimation(.spring(response: 0.42, dampingFraction: 0.82)) { railOpen = false } }.zIndex(63)
                        }
                        DioAgentRail(agents: agents, chains: chains, dimmed: false,
                                     onOpen: { a in railOpen = false; haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { openAgent = a } },
                                     onCreate: { railOpen = false; haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { editingAgent = AgentRecord.blank() } },
                                     onRunChain: { c in railOpen = false; haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { runChainSheet = c } },
                                     onCreateChain: { railOpen = false; haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { editingChain = ChainRecord.blank() } },
                                     onPlay: { id in railOpen = false; haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { if id == "arkanoid" { arkadeOpen = true } else { openGameId = id } } },
                                     onPlace: { id in placeGame(id) })
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing)
                            .padding(.trailing, compact ? 6 : 10).zIndex(64).transition(.move(edge: .trailing).combined(with: .opacity))
                    }
                }

                // the mode picker — hovering over the corner mic
                if showRecordPicker && !capturing {
                    DioRecordModePicker(anchor: orbPos(w, h),
                                        onMeeting: { startCapture(desktop: false) },
                                        onDesktop: { if hostLink == nil { withAnimation { showRecordPicker = false; connecting = true } } else { startCapture(desktop: true) } },
                                        onClose: { withAnimation { showRecordPicker = false } })
                        .zIndex(116)
                }
                // recording is AMBIENT — anchored to the corner mic, it does not take over the desk
                if capturing && !weaving {
                    DioAmbientRecorder(model: model, isDesktop: captureDesktop, orb: orbPos(w, h), w: w, h: h,
                                       cards: liveCards, agents: agents, chains: chains,
                                       onFire: { target, m in fireLive(target, minutes: m) },
                                       onKeep: { c in keepLiveCard(c) },
                                       onDismiss: { id in withAnimation { liveCards.removeAll { $0.id == id } } },
                                       onStop: { stopCapture() })
                        .transition(.opacity).zIndex(110)
                }
                // the record pane metamorphoses into a staged progress bar, then the meeting lands on the desk
                if weaving {
                    DioConstellationWeave(stepName: weaveStepName, done: weaveDone, total: weaveTotal,
                                          lensNames: LiveLenses.defaultPipeline.map(\.name),
                                          words: notableWords(model.liveTranscript),
                                          lensColors: LiveLenses.defaultPipeline.map { lensColor($0.name) },
                                          onSkip: { weaveCancel = true }).zIndex(111)
                }
                // a council mini-game in the shared ephemeral window
                if let gid = openGameId, let g = MiniGames.game(gid) {
                    DioGameWindow(game: g, onClose: { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { openGameId = nil } },
                                  screen: CGSize(width: w, height: h), pinNX: $gameWinX, pinNY: $gameWinY)
                        .id(gid).transition(.scale(scale: 0.9).combined(with: .opacity)).zIndex(112)
                }
                // the arcade window — Arkanoid keeps its own bespoke window (score/lives) above the recorder
                if arkadeOpen {
                    DeskArkanoidWindow(onMinimize: { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { arkadeOpen = false } },
                                       onClose: { withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { arkadeOpen = false } },
                                       screen: CGSize(width: w, height: h),
                                       pinNX: $arkadeX, pinNY: $arkadeY)
                        .transition(.scale(scale: 0.9).combined(with: .opacity)).zIndex(112)
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
                            Text("Add a model in Settings.").font(.system(size: 11.5, weight: .semibold, design: .rounded)).foregroundStyle(DioPal.muted).multilineTextAlignment(.center)
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
                    // THE MIGRATING PULL-OUT (the signature moment, HSM-20-02). The SAME content
                    // (DioPullout is maxWidth/maxHeight .infinity) enters from the RIGHT edge on the
                    // iPad and RISES from the BOTTOM edge on iPhone — only the entry edge + a grab
                    // handle change by camera. On the lane it sits over a transparent catcher, never a
                    // dimming scrim. Animating on `dockSpring` keyed to the camera means that, in iPad
                    // split-view, dragging the divider into compact migrates the pane right→bottom live.
                    let lane = camera.isLane
                    if lane {
                        Color.clear.contentShape(Rectangle()).ignoresSafeArea()
                            .onTapGesture { select(nil) }.zIndex(59)
                    }
                    DioPullout(prim: p, onClose: { select(nil) }, onAction: { handle($0, on: p) },
                               onRouteSection: { t, x in routeFacet(t, x, w, h) },
                               onActItem: { task, text in beginActOnItem(from: p, task: task, text: text) },
                               onOpenDerivative: { id in haptic(.medium); withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { select(id) } },
                               onChangeIcon: spriteKinds.contains(p.kind) ? { haptic(.light); iconPick = IconPickTarget(id: p.id, kind: p.kind, title: p.title) } : nil)
                        .frame(width: lane ? camera.cardWidth(560, in: w, margin: 8) : min(560, w * 0.62),
                               height: lane ? h * 0.74 : nil)
                        .overlay(alignment: .top) {
                            if lane { Capsule().fill(.white.opacity(0.32)).frame(width: 46, height: 5).padding(.top, 9) }
                        }
                        .padding(.top, lane ? 0 : 22).padding(.bottom, lane ? botInset : 22).padding(.trailing, lane ? 0 : 16)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: lane ? .bottom : .trailing)
                        .transition(.move(edge: lane ? .bottom : .trailing).combined(with: .opacity))
                        .animation(dockSpring, value: lane).zIndex(60)
                }

                if !path.isEmpty && selected == nil && !showRouteSheet && !routing && printed == nil && !showSendCard {
                    DioBackBar(crumbs: crumbs(), onBack: { climbOut() }, onJump: { jump(to: $0) })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, topInset + 8).zIndex(100)
                }

                // the keystone routing flow: sheet → theater → printed card (keep/bin)
                if showRouteSheet {
                    DioRouteSheet(sourceTitle: routeSourceTitle(),
                                  onAsk: { l, p, pid in runRoute(lens: l, prompt: p, profileId: pid) },
                                  onCancel: { withAnimation { showRouteSheet = false }; routeSourceId = nil },
                                  onSaveTool: { p in pendingToolPrompt = p; toolName = ""; withAnimation { showRouteSheet = false }; savingTool = true })
                        .zIndex(120)
                }
                if routing {
                    DioRoutingTheater(from: routeFrom, to: routeTo, sourceTitle: routeSourceTitle(),
                                      lens: routeLensRun, local: InferenceConfigStore.shared.isLocal, tint: DioPal.accent).zIndex(125)
                }
                if let rec = printed {
                    DioPrintedCard(rec: rec, egress: printedEgress, onKeep: { keepPrinted() }, onBin: { binPrinted() }).zIndex(130)
                }
                // WHERE IT RUNS — the run-target picker for an agent/chain route (on-device vs your desktop).
                if let run = pendingHubRun {
                    DioRunTargetSheet(run: run, paired: hostLink != nil,
                                      peerLabel: peerHost.isEmpty ? "your desktop" : peerHost,
                                      preferred: preferredRunTarget,
                                      remembered: DeskRunTarget(rawValue: runTargetPref) != nil,
                                      onDevice: { runOnDevice(run) },
                                      onHub: { runOnHub(run) },
                                      onCancel: { withAnimation { pendingHubRun = nil } })
                        .zIndex(132)
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
                // the agent's home — a living multi-turn conversation; harvest replies to the desk
                if let a = openAgent {
                    DioAgentChat(agent: a,
                                 messages: agentChats[a.id] ?? [],
                                 onInfer: { history, q in await agentReply(a, history: history, question: q) },
                                 onChange: { msgs in agentChats[a.id] = msgs; persistAgentChats() },
                                 onSaveCard: { text in saveAgentReply(text, from: a) },
                                 onEdit: { withAnimation { openAgent = nil; editingAgent = a } },
                                 onDelete: { deleteAgent(a.id) },
                                 onClose: { withAnimation { openAgent = nil } })
                        .id(a.id)
                        .zIndex(140).transition(.opacity)
                }
                // the builder — craft / edit an agent (avatar gallery, presets, context)
                if let draft = editingAgent {
                    DioAgentBuilder(draft: draft, knowledgeBases: knowledgeBases,
                                    onSave: { saveAgent($0) },
                                    onCancel: { withAnimation { editingAgent = nil } },
                                    isNew: !agents.contains { $0.id == draft.id },
                                    contextLimit: agentContextLimit(), zoneTokens: zoneGroundingTokens())
                        .id(draft.id)
                        .zIndex(145).transition(.opacity)
                }
                // the chain run/manage sheet
                if let c = runChainSheet {
                    DioChainSheet(chain: c, agents: agents,
                                  onRun: { input in withAnimation { runChainSheet = nil }; runChain(c, input: input, inputTitle: "Crew run") },
                                  onEdit: { withAnimation { runChainSheet = nil; editingChain = c } },
                                  onDelete: { deleteChain(c.id) },
                                  onClose: { withAnimation { runChainSheet = nil } })
                        .id(c.id).zIndex(141).transition(.opacity)
                }
                // the chain builder
                if let draft = editingChain {
                    DioChainBuilder(draft: draft, agents: agents,
                                    onSave: { saveChain($0) },
                                    onCancel: { withAnimation { editingChain = nil } },
                                    isNew: !chains.contains { $0.id == draft.id })
                        .id(draft.id).zIndex(146).transition(.opacity)
                }
                // the live relay (the gamified payoff)
                if let c = chainRelay {
                    DioChainRelay(chain: c, agents: agents, step: chainStep, results: chainResults)
                        .zIndex(128).transition(.opacity)
                }
                // the zone style editor — paint a place (colour, border, fill, glow)
                if let z = editingZone {
                    DioZoneEditor(zone: z, name: name(of: z.path), maxW: camera.cardWidth(380, in: w),
                                  onSave: { saveZone($0) },
                                  onDelete: { deleteZone(z.path) },
                                  onCancel: { withAnimation { editingZone = nil } })
                        .id(z.path).zIndex(147).transition(.opacity)
                }
                // Notes + KBs are edited IN-WORLD on the desk (see `level`), never in a dimmed modal.
                // the live "running coder" feed — replay the session, approve / answer inline (HSM-17-03)
                if let c = openCoderSession {
                    DioCoderSession(session: c, maxW: camera.cardWidth(480, in: w), maxH: min(560, h - h * 0.12),
                                    onAnswer: { withAnimation { openCoderSession = nil; answeringCoder = c } },
                                    onApprove: { approveCoder(c) },
                                    onClose: { withAnimation { openCoderSession = nil } })
                        .id(c.id).zIndex(149).transition(.opacity)
                }
                // the coder answer composer — reply into a live Claude/Codex session (HSM-17-04)
                if let c = answeringCoder {
                    DioCoderAnswer(session: c, maxW: camera.cardWidth(400, in: w),
                                   onSend: { answerCoder(c, $0) },
                                   onCancel: { withAnimation { answeringCoder = nil } })
                        .id(c.id).zIndex(150).transition(.opacity)
                }
                // THE IN-WORLD CONNECT CARD — pair the Mac from the desk. A transparent (no scrim)
                // catcher dismisses it on a tap-away; the card itself carries Connect / Test / Forget.
                if connecting {
                    Color.clear.contentShape(Rectangle()).ignoresSafeArea()
                        .onTapGesture { withAnimation { connecting = false } }.zIndex(151)
                    DioConnectCard(name: peerName, host: peerHost, port: peerPort.isEmpty ? "8765" : peerPort, token: peerToken,
                                   maxW: camera.cardWidth(380, in: w), paired: hostLink != nil,
                                   onConnect: { hh, pp, tt, nn in savePeerFull(host: hh, port: pp, token: tt, name: nn) },
                                   onForget: { forgetPeer() },
                                   onCancel: { withAnimation { connecting = false } },
                                   onTest: { hh, pp, tt in
                                       guard let p = Int(pp.trimmingCharacters(in: .whitespaces)), p > 0 else { return false }
                                       return await DeskHostLink(host: hh.trimmingCharacters(in: .whitespaces), port: p, token: tt).reachable()
                                   })
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                        .padding(.top, h * 0.08).zIndex(152).transition(.scale(scale: 0.92).combined(with: .opacity))
                }
                if let t = sentToast {
                    HStack(spacing: 7) { Image(systemName: "checkmark.circle.fill"); Text(t).font(.system(size: 13, weight: .heavy, design: .rounded)) }
                        .foregroundStyle(.white).padding(.horizontal, 16).frame(height: 40).background(Capsule().fill(DioPal.mint.opacity(0.92)))
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, topInset + 8)
                        .transition(.move(edge: .top).combined(with: .opacity)).zIndex(200)
                }
                if let t = iconPick {
                    DioIconPicker(target: t, current: SpriteStore.chosen(t.id),
                                  onPick: { name in haptic(.medium); SpriteStore.set(t.id, to: name); withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { iconPick = nil } },
                                  onClose: { withAnimation { iconPick = nil } })
                        .transition(.opacity).zIndex(205)
                }
            }
            .ignoresSafeArea()
            .onAppear { landed = true; load(); model.refresh(); syncDesk(reason: "desk load")
                #if targetEnvironment(simulator)
                if let s = ProcessInfo.processInfo.environment["HS_DESK_SETTINGS"], s == "1" || s == "local" {
                    if s == "local" { InferenceConfigStore.shared.mode = .local }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { showSettings = true }
                }
                if let r = ProcessInfo.processInfo.environment["HS_DESK_RECORD"] {
                    model.liveTranscript = "Welcome everyone to the Q3 kickoff. The big bet this quarter is shipping the desk to the web. Karol will own the mesh sync and the approval contract. We agreed to demo the air-gapped proof by Friday"
                    model.partial = "and then we will"
                    captureDesktop = (r == "desktop")
                    agents = [
                        AgentRecord(id: "seed1", name: "Scout", avatar: "p1", role: "digs for the facts", systemPrompt: "You are a researcher.", userTemplate: "{input}", manualContext: "", useZoneContext: false, kb: ""),
                        AgentRecord(id: "seed3", name: "Critic", avatar: "p7", role: "finds the holes", systemPrompt: "You are a critic.", userTemplate: "{input}", manualContext: "", useZoneContext: false, kb: ""),
                    ]
                    chains = [ChainRecord(id: "c1", name: "Refine", steps: ["seed1", "seed3"])]
                    if r == "intel" {
                        liveCards = [LiveIntelCard(id: "lc1", lens: "Summary", minutes: 1.0, text: "The Q3 bet is shipping the desk to the web. Karol owns mesh sync and the approval contract; the air-gapped proof is due Friday.", thinking: false),
                                     LiveIntelCard(id: "lc2", lens: "Questions", minutes: 0.5, text: nil, thinking: true)]
                    }
                    if r == "picker" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { showRecordPicker = true } } }
                    else if r == "weave" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { weaveStepName = "Action items"; weaveDone = 1; weaveTotal = 3; withAnimation { capturing = true; weaving = true } } }
                    else { DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { withAnimation { capturing = true }; model.recording = true; model.level = 0.6 } }
                }
                if let a = ProcessInfo.processInfo.environment["HS_DESK_ARCADE"] {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                        withAnimation {
                            if a == "1" || a == "play" { arkadeOpen = true }
                            else if MiniGames.game(a) != nil { openGameId = a }
                        }
                    }
                }
                if let zenv = ProcessInfo.processInfo.environment["HS_DESK_ZONE"] {
                    zones = [
                        ZoneRec(path: "Atlas", color: 2, cx: 0.28, cy: 0.3, w: 200, h: 120, borderW: 2, borderStyle: 1, fillStyle: 3, fillOpacity: 0.2, glow: true),
                        ZoneRec(path: "Q3", color: 5, cx: 0.66, cy: 0.32, w: 180, h: 120, borderW: 2.5, borderStyle: 2, fillStyle: 2, fillOpacity: 0.22, glow: false),
                    ]
                    if zenv == "1" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { if let z = zones.first { withAnimation { editingZone = z } } } }
                    // `directory` shows the wave-4 DIRECTORY model on the desk: a parent zone, a
                    // nested child (parent_id chain), and a note filed into the parent (membership) —
                    // exactly what now syncs. Geometry/paint stays this device's; identity+nesting+
                    // membership are canonical.
                    if zenv == "directory" {
                        notes = [NoteRecord(id: "nAtlas", title: "Mesh sync owner", body: "Karol owns the mesh-sync approval contract.", path: "Atlas")]
                        outputs = [OutputRecord(id: "oAtlas", title: "Q3 summary", body: "Ship the desk to the web; air-gapped proof due Friday.", source: "Q3 kickoff", lens: "Summary", path: "Atlas")]
                    }
                }
                if ProcessInfo.processInfo.environment["HS_DESK_ARRIVE"] == "1" {
                    let m = Meeting(id: "demoNew", startedAt: Date(), title: "Q3 kickoff", segments: [Segment(text: "Welcome to the kickoff.", speaker: "Speaker 1", startTime: 0, endTime: 2)])
                    model.meetings = [m] + model.meetings
                    outputs = [OutputRecord(id: "delivNew", title: "Summary", body: "Shipping the desk to the web is the Q3 bet; Karol owns mesh sync and the approval contract; air-gapped proof due Friday.", source: "Q3 kickoff", lens: "Summary", path: ""),
                               // A run-born card (HSM-18-07): no meeting anchor, so it
                               // sits loose on the desk instead of a meeting's drawer.
                               OutputRecord(id: "runNew", title: "Scout: the mesh risks", body: "Top risk: the approval contract drifts between surfaces. Lock it with the parity guard before the air-gapped proof.", source: "your ask", lens: "Agent · your desktop", path: "")]
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) { arrivedIds = ["m:demoNew", "out:delivNew", "out:runNew"]; flash = 0.5 }; withAnimation(.easeOut(duration: 0.9)) { flash = 0 } }
                }
                // IN-WORLD editing + pairing demos (layout checks for the device punch-list).
                // HS_DESK_NOTE=1 → a fresh note, edited in place on the desk (no modal).
                // HS_DESK_CONNECT=1 → the in-world Connect card (host · port · token).
                if ProcessInfo.processInfo.environment["HS_DESK_NOTE"] == "1" {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { createNote() }
                }
                if ProcessInfo.processInfo.environment["HS_DESK_CONNECT"] == "1" {
                    peerHost = ""   // force the unpaired front door
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { withAnimation { connecting = true } }
                }
                // HS_DESK_OPEN=1 → seed a deliverable and open it, so the pull-out is shown. On the
                // lane it RISES from the bottom edge with a grab handle; on iPad it enters from the
                // right. For verifying the HSM-20-02 migrating pull-out in the simulator.
                if ProcessInfo.processInfo.environment["HS_DESK_OPEN"] == "1" {
                    outputs = [OutputRecord(id: "demoOpen", title: "Standup notes",
                                            body: "Shipped the egress badge; review the dock by Friday.\n\nOwner: Karol · Due: Fri",
                                            source: "Standup", lens: "Note", path: "")]
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) { select("out:demoOpen") }
                }
                // HS_DESK_OPEN=connector → open a connector's pull-out (HSM-21-01: the header
                // badge must wear the connector's REAL cloud posture, never "On device").
                if ProcessInfo.processInfo.environment["HS_DESK_OPEN"] == "connector" {
                    peerHost = peerHost.isEmpty ? "192.168.1.13" : peerHost
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) { select("conn:slack") }
                }
                // HS_DESK_OPEN=connector-github → the GitHub pull-out, against the LIVE paired
                // hub (HSM-21-03: ready must reflect the host's real companion_github_repo).
                if ProcessInfo.processInfo.environment["HS_DESK_OPEN"] == "connector-github" {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) { select("conn:github") }
                }
                // HSM-22-04 proof affordance — run the first SYNCED graph workflow on the
                // paired hub with a fixed input: the exact runOnHub path the sheet's
                // "your desktop" row fires (after the desk's own sync pass settles).
                if ProcessInfo.processInfo.environment["HS_DESK_WF_HUB_RUN"] == "1" {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.5) {
                        guard let wf = workflows.first(where: { $0.contract.graphJson != nil }) else { return }
                        runOnHub(.init(kind: .workflow(wf),
                                       input: "Standup: we shipped the graph bridge. Risk: the demo endpoint is slow. Decision: keep linear runs on the hub.",
                                       inputId: "demo", inputTitle: "Standup"))
                    }
                }
                // THE SYNC STATUS demo — show the desk wearing each sync state + a pull-arrival.
                // `synced` (calm, with a "just now") · `syncing` (breathing) · `offline` (queued) ·
                // `error` · `pull` (a note authored on the web lands with the NEW-arrival halo).
                if let sv = ProcessInfo.processInfo.environment["HS_DESK_SYNC"] {
                    peerHost = peerHost.isEmpty ? "192.168.1.13" : peerHost
                    notes = [NoteRecord(id: "nSynced", title: "Approval contract owner", body: "Karol owns the mesh-sync approval contract + egress badge copy.", path: ""),
                             NoteRecord(id: "nPending", title: "Air-gapped proof script", body: "Record the LinkedIn proof offline before Friday's demo.", path: "")]
                    agents = [AgentRecord(id: "agSynced", name: "Scout", avatar: "p1", role: "digs for the facts", systemPrompt: "You are a researcher.", userTemplate: "{input}", manualContext: "", useZoneContext: false, kb: "")]
                    kbs = [KBRecord(id: "kSynced", name: "Architecture", path: "", items: 7)]
                    placedGames = [GameRecord(gameId: "merge", path: "")]   // local-only cue
                    syncModified = ["nPending": Date()]                     // pending: edited, not pushed
                    syncConfirmed = ["nSynced", "agSynced", "kSynced"]      // canonical on the hub
                    lastSyncedAt = Date().addingTimeInterval(-135)          // "2m ago"
                    switch sv {
                    case "syncing": syncing = true
                    case "offline": syncState = .offline
                    case "error":   syncState = .error("Couldn’t reach your desktop")
                    case "pull":
                        // a remote-authored note arrives on the next pull → NEW-arrival treatment
                        syncState = .synced
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
                            let remote = NoteRecord(id: "nFromWeb", title: "Authored on the web", body: "This note was written on another surface and synced into your desk.", path: "")
                            withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) {
                                notes.append(remote); syncConfirmed.insert("nFromWeb")
                                arrivedIds.insert("note:nFromWeb"); flash = 0.45
                            }
                            withAnimation(.easeOut(duration: 0.9)) { flash = 0 }
                        }
                    default: syncState = .synced
                    }
                }
                if let pv = ProcessInfo.processInfo.environment["HS_DESK_PARITY"] {
                    notes = [NoteRecord(id: "n1", title: "Follow up with Karol", body: "Confirm the mesh-sync approval contract owner and the air-gapped proof date before Friday's demo.", path: "")]
                    kbs = [KBRecord(id: "k1", name: "Architecture", path: "", items: 7),
                           KBRecord(id: "k2", name: "Onboarding", path: "", items: 3)]
                    outputs = [OutputRecord(id: "o1", title: "Scout · reply", body: "Three facts: mesh sync is riskiest, proof due Friday, egress badge copy needs an owner.", source: "Scout", lens: "Agent", path: "")]
                    placedGames = [GameRecord(gameId: "merge", path: ""), GameRecord(gameId: "reflex", path: "")]
                    UserDefaults.standard.set(4096, forKey: "hs.mg.merge.best")
                    if pv == "note" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { if let n = notes.first { withAnimation { editingNote = n } } } }
                    if pv == "kb" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { if let k = kbs.first { withAnimation { editingKB = k } } } }
                    if pv == "game" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { withAnimation { selected = "game:merge" } } }
                }
                if let cv = ProcessInfo.processInfo.environment["HS_DESK_CODER"] {
                    let claudeEvents: [CoderEvent] = [
                        .init(id: "e0", ts: nil, kind: .userPrompt("Decompose web_runtime into mixins and wire the dictation seam.")),
                        .init(id: "e1", ts: nil, kind: .assistant("I'll map web_runtime first, then carve the mixins one seam at a time so routing stays byte-identical.")),
                        .init(id: "e2", ts: nil, kind: .tool(.read, target: "holdspeak/web_runtime.py", detail: "2,635 lines")),
                        .init(id: "e3", ts: nil, kind: .result(ok: true, summary: "read", added: nil, removed: nil)),
                        .init(id: "e4", ts: nil, kind: .tool(.search, target: "self._", detail: "mixin candidates")),
                        .init(id: "e5", ts: nil, kind: .result(ok: true, summary: "42 matches across 8 concerns", added: nil, removed: nil)),
                        .init(id: "e6", ts: nil, kind: .tool(.edit, target: "holdspeak/runtime/dictation.py", detail: "extract DictationMixin")),
                        .init(id: "e7", ts: nil, kind: .result(ok: true, summary: "edited", added: 118, removed: 6)),
                        .init(id: "e8", ts: nil, kind: .command(cmd: "uv run pytest -q -k runtime", exit: 0, output: "142 passed in 7.81s")),
                        .init(id: "e9", ts: nil, kind: .assistant("Tests green. The next step rewrites history on the shared branch.")),
                        .init(id: "e10", ts: nil, kind: .approval(question: "Push the mixin split to origin/main? This is a force-with-lease on a shared branch.", command: "git push --force-with-lease origin main")),
                    ]
                    let codexEvents: [CoderEvent] = [
                        .init(id: "c0", ts: nil, kind: .userPrompt("Add the coder primitive to the desk.")),
                        .init(id: "c1", ts: nil, kind: .tool(.edit, target: "apple/App/MeetingCapture/DeskCoder.swift", detail: "AgentSessionPrimitive")),
                        .init(id: "c2", ts: nil, kind: .result(ok: true, summary: "edited", added: 64, removed: 2)),
                        .init(id: "c3", ts: nil, kind: .tool(.bash, target: "xcodebuild", detail: "Simulator build")),
                    ]
                    coders = [
                        CoderSession(agent: "claude", sessionId: "s1", project: "holdspeak", model: "claude-opus-4-8", tokensUsed: 48210, state: .waiting, events: claudeEvents),
                        CoderSession(agent: "codex", sessionId: "s2", project: "apple", model: "gpt-5-codex", tokensUsed: 12940, state: .working, events: codexEvents),
                    ]
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                        withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) { arrivedIds = ["coder:claude/s1"]; flash = 0.4 }
                        withAnimation(.easeOut(duration: 0.9)) { flash = 0 }
                        if cv == "session" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { openCoderSession = coders.first } } }
                        if cv == "answer" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { answeringCoder = coders.first } } }
                    }
                }
                if ProcessInfo.processInfo.environment["HS_DESK_TRANSCRIPT"] == "1" {
                    let segs = [
                        Segment(text: "Welcome everyone to the Q3 kickoff. Big bet this quarter is the desk on the web.", speaker: "Speaker 1", startTime: 0, endTime: 5),
                        Segment(text: "I can own the mesh sync and the approval contract.", speaker: "Speaker 2", startTime: 5, endTime: 9),
                        Segment(text: "Great. What's the riskiest part of that?", speaker: "Speaker 1", startTime: 9, endTime: 12),
                        Segment(text: "Honestly the credential boundary. The iPad must never hold the token.", speaker: "Speaker 2", startTime: 12, endTime: 17),
                        Segment(text: "Agreed. Let's demo the air-gapped proof by Friday.", speaker: "Speaker 3", startTime: 17, endTime: 21),
                        Segment(text: "I'll draft the egress badge copy so it stays one line.", speaker: "Speaker 3", startTime: 21, endTime: 25),
                    ]
                    let m = Meeting(id: "demoT", startedAt: Date(), title: "Q3 kickoff", segments: segs)
                    model.meetings = [m] + model.meetings
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { withAnimation { selected = "m:demoT" } }
                }
                if let ag = ProcessInfo.processInfo.environment["HS_DESK_AGENTS"] {
                    agents = [
                        AgentRecord(id: "seed1", name: "Scout", avatar: "p1", role: "digs for the facts", systemPrompt: "You are a sharp researcher. Pull out concrete facts, names and numbers.", userTemplate: "{input}", manualContext: "", useZoneContext: true, kb: ""),
                        AgentRecord(id: "seed2", name: "Sage", avatar: "p3", role: "turns talk into a plan", systemPrompt: "You are a pragmatic planner.", userTemplate: "Make a plan from this:\n{input}", manualContext: "The team is three engineers.", useZoneContext: false, kb: ""),
                        AgentRecord(id: "seed3", name: "Critic", avatar: "p7", role: "finds the holes", systemPrompt: "You are a constructive critic.", userTemplate: "{input}", manualContext: "", useZoneContext: false, kb: ""),
                    ]
                    chains = [ChainRecord(id: "c1", name: "Refine", steps: ["seed1", "seed3", "seed2"])]
                    if ag == "builder" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { editingAgent = AgentRecord.blank() } } }
                    if ag == "chainbuild" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { editingChain = ChainRecord(id: "newc", name: "Refine", steps: ["seed1", "seed3"]) } } }
                    if ag == "chainrun" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { runChainSheet = chains.first } } }
                    // the WHERE-IT-RUNS picker (on-device vs your desktop) — seeded paired so the hub row is live.
                    if ag == "runtarget" || ag == "runtarget-unpaired" {
                        if ag == "runtarget" { peerHost = "192.168.1.43"; peerPort = "8080" }
                        else { peerHost = ""; peerPort = "8000" }   // unpaired → hub row disabled with a cue
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                            withAnimation { pendingHubRun = PendingHubRun(kind: .agent(agents[0]),
                                                                          input: "Welcome to the Q3 kickoff. The big bet is shipping the desk to the web; Karol owns mesh sync.",
                                                                          inputId: "mtg.q3", inputTitle: "Q3 kickoff") }
                        }
                    }
                    // a hub run's RESULT — the printed card with the cloud · your desktop egress badge.
                    if ag == "hubresult" {
                        peerHost = "192.168.1.43"; peerPort = "8080"
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                            printedEgress = .cloud("your desktop")
                            withAnimation { printed = OutputRecord(id: "hubdemo", title: "Scout",
                                body: "Three concrete facts: the mesh-sync approval contract is the riskiest piece, the air-gapped proof is due Friday, and the egress badge copy still has no owner.",
                                source: "Q3 kickoff", lens: "Agent · your desktop", path: "",
                                provenance: RunProvenance(sourceCardId: "mtg.q3", sourceCardTitle: "Q3 kickoff",
                                                          viaId: "seed1", viaName: "Scout", viaKind: "agent")) }
                        }
                    }
                    if ag == "chainrelay" { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { chainStep = 1; chainResults = ["Three key facts: the mesh-sync approval contract is the riskiest piece, the air-gapped proof is due Friday, and the egress badge copy has no owner yet."]; withAnimation { chainRelay = chains.first } } }
                    if ["p0", "o0", "s0"].contains(ag) { DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { var d = AgentRecord.blank(); d.avatar = ag; d.name = "Buddy"; withAnimation { editingAgent = d } } }
                    if ag == "sheet" || ag == "chat" {
                        agentChats["seed1"] = [
                            AgentMessage(id: "m1", role: "you", text: "What should I focus on after today's kickoff?"),
                            AgentMessage(id: "m2", role: "agent", text: "Three things stood out: lock the mesh-sync approval contract (it's the riskiest piece), get the air-gapped proof recorded before Friday, and pin down who owns the egress badge copy. Want me to draft a short plan for the first one?"),
                            AgentMessage(id: "m3", role: "you", text: "Yes, keep it tight."),
                        ]
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { withAnimation { openAgent = agents.first } }
                    }
                }
                if ProcessInfo.processInfo.environment["HS_DESK_SUMMON"] == "1" {
                    outputs = [OutputRecord(id: "demo", title: "Standup notes", body: "Shipped the egress badge; review the dock by Friday.", source: "Standup", lens: "Note", path: "")]
                    if agents.isEmpty {
                        agents = [
                            AgentRecord(id: "seed1", name: "Scout", avatar: "a21", role: "digs for the facts", systemPrompt: "You are a researcher.", userTemplate: "{input}", manualContext: "", useZoneContext: true, kb: ""),
                            AgentRecord(id: "seed3", name: "Critic", avatar: "a22", role: "finds the holes", systemPrompt: "You are a critic.", userTemplate: "{input}", manualContext: "", useZoneContext: false, kb: ""),
                        ]
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
                        summonAt = CGPoint(x: w * 0.5, y: h * 0.5)
                        withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { summonSource = "out:demo" }
                    }
                }
                #endif
            }
            .onChange(of: model.liveTranscript) { newValue in
                if capturing { liveTimeline.append((model.elapsedSeconds, newValue.count)) }   // for "last N minutes" windows
            }
            .alert("Couldn’t route", isPresented: Binding(get: { routeError != nil }, set: { if !$0 { routeError = nil } })) {
                Button("OK", role: .cancel) { routeError = nil }
            } message: { Text(routeError ?? "") }
            // Pairing is IN-WORLD on the desk now (DioConnectCard), not a system alert.
            .alert("Save as a tool", isPresented: $savingTool) {
                TextField("Tool name (e.g. Risks, Brief)", text: $toolName)
                Button("Cancel", role: .cancel) { routeSourceId = nil }
                Button("Save") { saveTool(); routeSourceId = nil }
            } message: { Text("Becomes a reusable tile on your desk.") }
            .alert("New zone", isPresented: $namingZone) {
                TextField("Name", text: $newZoneName)
                Button("Cancel", role: .cancel) { newZoneName = ""; pendingFileId = nil }
                Button("Create") { createZone(newZoneName); newZoneName = "" }
            } message: { Text(path.isEmpty ? "A place on your desk that holds meetings." : "A sub-zone inside \(name(of: pathKey)).") }
            .alert("New knowledge base", isPresented: $namingKB) {
                TextField("Name", text: $newKBName)
                Button("Cancel", role: .cancel) { newKBName = "" }
                Button("Create") { createKB(newKBName); newKBName = "" }
            } message: { Text("A container for notes you can ask over.") }
            .sheet(isPresented: Binding(get: { openMeeting != nil }, set: { if !$0 { openMeeting = nil } })) {
                if let m = openMeeting { NavigationStack { MeetingDetailView(meeting: m) }.preferredColorScheme(.dark) }
            }
            .sheet(isPresented: $showSettings) { NavigationStack { SettingsView() }.preferredColorScheme(.dark) }
        }
        .preferredColorScheme(.dark)
    }

    // MARK: - The lane (HSM-20-02): the desk reflowed to a one-thumb card column on iPhone.

    /// Which filter bucket a primitive kind falls under (the chip rail).
    private func laneBucketKey(_ k: PrimitiveKind) -> String {
        switch k {
        case .meeting, .summary, .actions, .transcript, .topics, .artifact: return "meetings"
        case .note: return "notes"
        case .kb: return "kb"
        case .model, .connector, .workflow: return "tools"
        case .agent, .chain, .coder: return "agents"
        case .game: return "play"
        }
    }
    private func laneBucketLabel(_ key: String) -> String {
        switch key {
        case "meetings": return "Meetings"; case "notes": return "Notes"; case "kb": return "KB"
        case "tools": return "Tools"; case "agents": return "Agents"; case "play": return "Play"
        default: return key.capitalized
        }
    }
    private func laneBucketTint(_ key: String) -> Color {
        switch key {
        case "meetings": return DioPal.accent; case "notes": return DioPal.mint; case "kb": return DioPal.violet
        case "tools": return DioPal.cobalt; case "agents": return DioPal.mint; case "play": return DioPal.cobalt
        default: return DioPal.accent
        }
    }
    /// The chip rail: "All" plus a chip per bucket that has at least one primitive (preserving a
    /// stable order), so the lane never shows an empty filter.
    private func laneBuckets(_ prims: [any DeskPrimitive]) -> [String] {
        let order = ["meetings", "notes", "kb", "agents", "tools", "play"]
        let present = Set(prims.map { laneBucketKey($0.kind) })
        return order.filter { present.contains($0) }
    }

    /// The one-thumb card column — the lane camera's renderer (HSM-20-02). Every primitive the wide
    /// desk shows has a row here; zones are divable rows; the chip rail filters by kind. Tapping a
    /// row is identical to tapping its canvas primitive (notes/KBs edit in-world; everything else
    /// opens the pull-out, which rises from the bottom edge on the lane).
    @ViewBuilder private func laneColumn(_ w: CGFloat, _ h: CGFloat, _ topInset: CGFloat, _ botInset: CGFloat) -> some View {
        let zs = childZones()
        let prims = members()
        let buckets = laneBuckets(prims)
        // "All" is your CONTENT + things you invoke (meetings/notes/KBs/agents/chains/games). Pure
        // infrastructure — models + connectors + workflows (the "tools" bucket) — is not content you
        // browse; it earns a spot only as a drag-target, which the lane has none of. So it lives behind
        // the "Tools" chip, out of the default view (owner: "why even have them there?"). This also keeps
        // a dived zone genuinely calm instead of flooded with the inherited toolkit.
        let shown = laneFilter == "all" ? prims.filter { laneBucketKey($0.kind) != "tools" }
                                        : prims.filter { laneBucketKey($0.kind) == laneFilter }
        VStack(spacing: 0) {
            if buckets.count > 1 {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        DioLaneChip(label: "All", tint: DioPal.accent, active: laneFilter == "all") {
                            haptic(.light); withAnimation(.easeOut(duration: 0.18)) { laneFilter = "all" }
                        }
                        ForEach(buckets, id: \.self) { key in
                            DioLaneChip(label: laneBucketLabel(key), tint: laneBucketTint(key), active: laneFilter == key) {
                                haptic(.light); withAnimation(.easeOut(duration: 0.18)) { laneFilter = key }
                            }
                        }
                    }.padding(.horizontal, 16)
                }.padding(.vertical, 8).zIndex(2)
            }
            ScrollView(showsIndicators: false) {
                VStack(spacing: 10) {
                    // Empty SUB-ZONE on the lane: a compact, inline hint at the top (NOT a centred card
                    // over the rows). The zone still lists the global toolkit below, so this is honest —
                    // your content is empty; the toolkit is always here. (Device punch-list: the false
                    // "empty" overlay that landed on the connector rows.)
                    if !path.isEmpty && contentMembers().isEmpty {
                        DioLaneEmptyHint(name: name(of: pathKey), tint: curTint) { haptic(.light); namingZone = true }
                    }
                    if laneFilter == "all" {
                        ForEach(Array(zs.enumerated()), id: \.element.path) { _, z in
                            DioLaneZoneRow(name: name(of: z.path), tint: ZoneStyle(z).color,
                                           count: membersOf(z.path).count,
                                           subZones: zones.filter { parent(of: $0.path) == z.path }.count) { dive(into: z.path) }
                        }
                    }
                    ForEach(Array(shown.enumerated()), id: \.element.id) { _, p in
                        DioLaneRow(glyph: p.glyph, tint: p.color, symbol: p.isSymbol, title: p.title,
                                   badge: p.kind.badge, subtitle: p.subtitle, arrived: arrivedIds.contains(p.id)) { tapPrimitive(p) }
                            .contextMenu { laneFileMenu(p) }
                    }
                }.padding(.horizontal, 16).padding(.top, 2).padding(.bottom, 200 + botInset)
            }
        }
        .padding(.top, topInset + 54)   // clear the Dynamic Island + the top-left gear/connect/sync chrome
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }

    @ViewBuilder private func level(_ w: CGFloat, _ h: CGFloat) -> some View {
        let zs = childZones(); let ms = contentMembers()
        let dScale = densityScale(ms.count)   // the desk shrinks its objects as it fills (#2)
        ZStack {
            ForEach(Array(zs.enumerated()), id: \.element.path) { i, z in
                DioZoneTray(name: name(of: z.path), style: ZoneStyle(z),
                            members: membersOf(z.path), subZones: zones.filter { parent(of: $0.path) == z.path }.count,
                            size: CGSize(width: z.w, height: z.h), landed: landed, index: i, dimmed: selected != nil,
                            hot: dragHotZone == z.path, onDive: { dive(into: z.path) },
                            onMove: { tr in moveZone(z.path, tr, w, h) }, onResize: { tr in resizeZone(z.path, tr) },
                            onEdit: { editingZone = z })
                    .position(x: w * z.cx, y: h * z.cy)
            }
            // The create cluster is always at hand when nothing is selected or being edited — a notes
            // product should never make you hunt for "New Note". (Was gated off on empty/first-run.)
            if selected == nil && editingNote == nil && editingKB == nil {
                HStack(spacing: 8) {
                    Button { createNote() } label: {
                        HStack(spacing: 6) { Image(systemName: "square.and.pencil").font(.system(size: 13, weight: .bold)); Text("New Note").font(.system(size: 12.5, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(DioPal.mint).padding(.horizontal, 12).frame(height: 36)
                            .background(Capsule().strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 5])).foregroundStyle(DioPal.mint.opacity(0.4)))
                    }.buttonStyle(.plain)
                    Button { createKBInline() } label: {
                        HStack(spacing: 6) { Image(systemName: "diamond.fill").font(.system(size: 12, weight: .bold)); Text("New KB").font(.system(size: 12.5, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(DioPal.violet).padding(.horizontal, 12).frame(height: 36)
                            .background(Capsule().strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 5])).foregroundStyle(DioPal.violet.opacity(0.4)))
                    }.buttonStyle(.plain)
                    Button { haptic(.light); namingZone = true } label: {
                        HStack(spacing: 6) { Image(systemName: "plus.circle.fill").font(.system(size: 14, weight: .bold)); Text("New Zone").font(.system(size: 12.5, weight: .heavy, design: .rounded)) }
                            .foregroundStyle(DioPal.muted).padding(.horizontal, 12).frame(height: 36)
                            .background(Capsule().strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6, 5])).foregroundStyle(DioPal.muted.opacity(0.45)))
                    }.buttonStyle(.plain)
                }.opacity(landed ? 0.9 : 0)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing).padding(.top, h * 0.12).padding(.trailing, 20)
            }

            // A transparent (NOT dimmed) catcher behind the lifted editor card: tapping the desk
            // commits the in-world edit. No scrim — the desk stays fully visible around the card.
            if editingNote != nil || editingKB != nil {
                Color.clear.contentShape(Rectangle()).ignoresSafeArea()
                    .onTapGesture { commitInlineEdit() }.zIndex(40)
            }

            ForEach(Array(ms.enumerated()), id: \.element.id) { i, p in
                let home = looseHome(i, ms.count, w, h)
                if let n = editingNote, "note:\(n.id)" == p.id {
                    DioInlineNoteCard(note: editingNoteBinding(n), onDone: { commitNote() }, onDelete: { deleteNote("note:\(n.id)") })
                        .position(clampInline(pos(p.id, home, w, h), w, h, cardW: 304, cardH: 320))
                        .zIndex(60).id(n.id)
                } else if let k = editingKB, "kb:\(k.id)" == p.id {
                    DioInlineKBCard(kb: editingKBBinding(k), onDone: { commitKB() }, onDelete: { deleteKB("kb:\(k.id)") })
                        .position(clampInline(pos(p.id, home, w, h), w, h, cardW: 288, cardH: 170))
                        .zIndex(60).id(k.id)
                } else {
                    DioHero(prim: p, landed: landed, mode: mode(p.id), index: i, pos: pos(p.id, home, w, h),
                            hot: dragHotObjectId == p.id, picked: selectedSet.contains(p.id), arrived: arrivedIds.contains(p.id),
                            syncCue: syncCue(for: p), densityScale: dScale,
                            onSummon: { summonAt = pos(p.id, home, w, h); haptic(.medium)
                                        withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { summonSource = p.id } },
                            onTap: { tapPrimitive(p) },
                            onDrop: { tr in drop(p, home, tr, w, h) },
                            onDragChange: { pt in updateHot(p, pt, w, h) })
                }
            }

            if selected != nil {
                Color.black.opacity(0.45).ignoresSafeArea().onTapGesture { select(nil) }
                    .zIndex(5).transition(.opacity)
            }
        }
    }

    /// A live binding the inline editor card writes into, so a tap-away commits exactly what's
    /// on screen. Non-nil in the branch where it's used (`fallback` only satisfies the type).
    private func editingNoteBinding(_ fallback: NoteRecord) -> Binding<NoteRecord> {
        Binding(get: { editingNote ?? fallback }, set: { editingNote = $0 })
    }
    private func editingKBBinding(_ fallback: KBRecord) -> Binding<KBRecord> {
        Binding(get: { editingKB ?? fallback }, set: { editingKB = $0 })
    }
    /// Keep a lifted editor card fully on-screen, biased into the top half so the keyboard never
    /// covers what you're writing.
    private func clampInline(_ p: CGPoint, _ w: CGFloat, _ h: CGFloat, cardW: CGFloat, cardH: CGFloat) -> CGPoint {
        let pad: CGFloat = 16
        let x = min(max(p.x, cardW / 2 + pad), w - cardW / 2 - pad)
        let y = min(max(p.y, cardH / 2 + pad), max(cardH / 2 + pad, h * 0.46))
        return CGPoint(x: x, y: y)
    }
    /// The persisted, clamped centre for the movable in-world editor window (note/KB) on the lane.
    private func editorWinPin(_ w: CGFloat, _ h: CGFloat, cardW: CGFloat, cardH: CGFloat) -> CGPoint {
        CGPoint(x: min(max(CGFloat(editorWinX) * w, cardW / 2 + 8), w - cardW / 2 - 8),
                y: min(max(CGFloat(editorWinY) * h, cardH / 2 + 30), h - cardH / 2 - 8))
    }
    /// Tap a desk card: notes + KBs flip to IN-WORLD edit in place; a live coder opens its feed;
    /// everything else opens its pullout (select).
    private func tapPrimitive(_ p: any DeskPrimitive) {
        if let c = p as? AgentSessionPrimitive { haptic(.medium); withAnimation { openCoderSession = c.session } }
        else if let n = notes.first(where: { "note:\($0.id)" == p.id }) { haptic(.medium); select(nil); withAnimation(.spring(response: 0.5, dampingFraction: 0.78)) { editingNote = n } }
        else if let k = kbs.first(where: { "kb:\($0.id)" == p.id }) { haptic(.medium); select(nil); withAnimation(.spring(response: 0.5, dampingFraction: 0.78)) { editingKB = k } }
        else { select(selected == p.id ? nil : p.id) }
    }
    private func commitNote() { if let n = editingNote { saveNote(n) } }
    private func commitKB() { if let k = editingKB { renameKB(k) } else { withAnimation { editingKB = nil } } }
    private func commitInlineEdit() { if editingNote != nil { commitNote() } else if editingKB != nil { commitKB() } }

    private func crumbs() -> [(String, Color)] {
        var out: [(String, Color)] = [("Desk", DioPal.accent)]; var acc: [String] = []
        for comp in path { acc.append(comp); let id = acc.joined(separator: "/"); out.append((comp, tintFor(id))) }
        return out
    }

    private func handle(_ act: PrimitiveAction, on prim: any DeskPrimitive) {
        switch act.role {
        case .openEditor:
            if let m = meeting(forObj: prim.id) { openMeeting = m }
            else if let n = notes.first(where: { "note:\($0.id)" == prim.id }) { select(nil); withAnimation { editingNote = n } }
            else if let k = kbs.first(where: { "kb:\($0.id)" == prim.id }) { select(nil); withAnimation { editingKB = k } }
        case .custom("connect"): select(nil); withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { connecting = true }
        case .custom("delete"):
            if prim.id.hasPrefix("note:") { deleteNote(prim.id) }
            else if prim.id.hasPrefix("out:") { deleteOutput(prim.id) }
            else if prim.id.hasPrefix("kb:") { deleteKB(prim.id) }
            else if prim.id.hasPrefix("game:") { removeGame(prim.id) }
        case .custom("play"):
            guard let g = prim as? GamePrimitive else { break }
            select(nil); haptic(.medium)
            withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { if g.gameId == "arkanoid" { arkadeOpen = true } else { openGameId = g.gameId } }
        case .custom("harvest"):
            guard let g = prim as? GamePrimitive else { break }
            harvestScore(g)
        case .custom("answer"):
            guard let c = prim as? AgentSessionPrimitive else { break }
            select(nil); withAnimation { answeringCoder = c.session }
        case .custom("opensession"):
            guard let c = prim as? AgentSessionPrimitive else { break }
            select(nil); haptic(.medium); withAnimation { openCoderSession = c.session }
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
        persistZones(); stampSync(zpath)   // the directory (identity+nesting) is a synced primitive
        if let pid = pendingFileId { fileAny(pid, into: zpath); pendingFileId = nil }   // lane "New zone…" → file into it
    }
    private func moveZone(_ path: String, _ tr: CGSize, _ w: CGFloat, _ h: CGFloat) {
        guard let idx = zones.firstIndex(where: { $0.path == path }) else { return }
        haptic(.light)
        zones[idx].cx = min(0.95, max(0.05, zones[idx].cx + Double(tr.width / w)))
        zones[idx].cy = min(0.93, max(0.06, zones[idx].cy + Double(tr.height / h)))
        persistZones()
    }
    private func resizeZone(_ path: String, _ tr: CGSize) {
        guard let idx = zones.firstIndex(where: { $0.path == path }) else { return }
        haptic(.light)
        zones[idx].w = min(360, max(120, zones[idx].w + Double(tr.width)))
        zones[idx].h = min(260, max(78, zones[idx].h + Double(tr.height)))
        persistZones()
    }
    private func saveZone(_ z: ZoneRec) {
        guard let idx = zones.firstIndex(where: { $0.path == z.path }) else { return }
        haptic(.medium)
        withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) { zones[idx] = z; editingZone = nil }
        persistZones()
    }
    private func deleteZone(_ path: String) {
        haptic(.medium)
        // the directories about to go (this zone + every sub-zone) → tombstone each so the delete syncs
        let gone = zones.filter { $0.path == path || $0.path.hasPrefix(path + "/") }.map(\.path)
        withAnimation(.spring(response: 0.5, dampingFraction: 0.78)) {
            zones.removeAll { $0.path == path || $0.path.hasPrefix(path + "/") }   // drop the zone + any sub-zones
            filed = filed.filter { $0.value != path && !$0.value.hasPrefix(path + "/") }
            editingZone = nil
        }
        for p in gone { tombstone(p, kind: .directory) }   // propagate the directory delete
        persistZones(); persistFiled()
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
        var out: [any DeskPrimitive] = []
        // the AI core first, then your tailored agents, then saved workflows, then connectors
        out += toolMembers().filter { $0.kind == .model }                        // takes anything
        out += agentMembers().filter { $0.accepts.contains(src.kind) }           // route the card through an agent
        out += chainMembers().filter { $0.accepts.contains(src.kind) }           // …or a whole crew
        out += toolMembers().filter { $0.kind == .workflow && $0.accepts.contains(src.kind) }
        out += toolMembers().filter { $0.kind == .connector }                    // tap guides pairing
        return out
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
    private func startCapture(desktop: Bool) {
        haptic(.medium)
        captureDesktop = desktop
        liveCards = []; liveTimeline = [(0, 0)]
        withAnimation(.spring(response: 0.45, dampingFraction: 0.82)) { showRecordPicker = false; capturing = true }
        Task { await model.startRecording() }
    }
    private func stopCapture() {
        haptic(.medium)
        let before = Set(model.meetings.map(\.id))
        let pipeline = LiveLenses.defaultPipeline
        weaveCancel = false; weaveDone = 0; weaveTotal = 1 + pipeline.count
        weaveStepName = "Hearing every word"
        withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) { weaving = true }
        let zpath = pathKey
        Task { @MainActor in
            // STEP 1 (real): the on-device weave — transcribe + diarize → the cassette.
            await model.stopRecording()
            model.refresh()
            weaveDone = 1
            let newId = model.meetings.first(where: { !before.contains($0.id) })?.id ?? model.meetings.first?.id
            var produced: [String] = []
            if let nid = newId, let m = model.meetings.first(where: { $0.id == nid }) {
                let material = String(MeetingPrimitive(meeting: m, index: 0).routableText.prefix(6000))
                // STEPS 2..N (real): the default pipeline runs against the meeting; each lands a deliverable.
                for lens in pipeline {
                    if weaveCancel { break }
                    weaveStepName = lens.name
                    let result = await callLLM(lens.instruction + "\n\nTranscript:\n" + material)
                    guard case .success(let raw) = result else { break }   // no provider → stop, keep the cassette
                    let clean = raw.trimmingCharacters(in: .whitespacesAndNewlines)
                    if !clean.isEmpty {
                        let rec = OutputRecord(id: UUID().uuidString, title: lens.name, body: clean, source: m.title ?? "Meeting", lens: lens.name, path: zpath)
                        outputs.append(rec); produced.append("out:\(rec.id)")
                    }
                    weaveDone += 1
                }
                persistOutputs()
            }
            weaveDone = weaveTotal; weaveStepName = "Ready"
            #if canImport(UIKit)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            #endif
            try? await Task.sleep(nanoseconds: 450_000_000)   // a beat on "Ready"
            withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) {
                weaving = false; capturing = false
                arrivedIds = Set(produced + (newId.map { ["m:\($0)"] } ?? [])); flash = 0.5
            }
            liveCards = []; liveTimeline = []
            withAnimation(.easeOut(duration: 0.9)) { flash = 0 }
            DispatchQueue.main.asyncAfter(deadline: .now() + 6) { withAnimation { arrivedIds = [] } }
        }
    }

    // the meeting's notable words → the constellation's stars (riff 1)
    private func notableWords(_ text: String) -> [String] {
        var seen = Set<String>(); var out: [String] = []
        for raw in text.split(whereSeparator: { !$0.isLetter }) {
            let w = String(raw); guard w.count >= 5 else { continue }
            let key = w.lowercased(); if seen.contains(key) { continue }
            seen.insert(key); out.append(w); if out.count >= 20 { break }
        }
        return out
    }
    private func lensColor(_ name: String) -> Color {
        switch name {
        case "Summary": return DioPal.violet
        case "Actions": return DioPal.mint
        case "Decisions": return DioPal.accent
        case "Questions": return DioPal.cobalt
        default: return DioPal.cobalt
        }
    }

    // MARK: live intelligence — fire a lens on a window of the LIVE transcript while Whisper keeps running
    private func windowedTranscript(_ minutes: Double) -> String {
        let full = model.liveTranscript
        let cutoff = model.elapsedSeconds - minutes * 60
        let startLen = liveTimeline.last(where: { $0.t <= cutoff })?.len ?? 0
        guard startLen > 0, startLen < full.count else { return full }
        return String(full.dropFirst(startLen))
    }
    // a live marker fired: a quick lens, one of your agents, or a crew — all on a transcript window
    private func fireLive(_ target: LiveTarget, minutes: Double) {
        switch target {
        case .lens(let l):  fireLiveIntel(l, minutes: minutes)
        case .agent(let a): fireLiveAgent(a, minutes: minutes)
        case .chain(let c): fireLiveChain(c, minutes: minutes)
        }
    }
    private func startLiveCard(_ lens: String, _ minutes: Double) -> String {
        haptic(.medium)
        let id = UUID().uuidString
        withAnimation(.spring(response: 0.4, dampingFraction: 0.72)) {
            liveCards.append(LiveIntelCard(id: id, lens: lens, minutes: minutes, text: nil, thinking: true))
        }
        return id
    }
    private func setLiveCard(_ id: String, _ text: String) {
        guard let i = liveCards.firstIndex(where: { $0.id == id }) else { return }
        liveCards[i].text = text.isEmpty ? "Nothing notable yet." : text
        withAnimation { liveCards[i].thinking = false }
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
    }
    private func liveWindowMaterial(_ minutes: Double) -> String {
        let window = windowedTranscript(minutes).trimmingCharacters(in: .whitespacesAndNewlines)
        return window.isEmpty ? "(nothing transcribed in this window yet)" : String(window.suffix(6000))
    }
    private func fireLiveIntel(_ lens: LiveLens, minutes: Double) {
        let id = startLiveCard(lens.name, minutes)
        let prompt = lens.instruction + "\n\nTranscript:\n" + liveWindowMaterial(minutes)
        Task { @MainActor in
            switch await callLLM(prompt) {
            case .success(let raw): setLiveCard(id, raw.trimmingCharacters(in: .whitespacesAndNewlines))
            case .failure(let e): setLiveCard(id, "⚠️ " + friendly(e))
            }
        }
    }
    private func fireLiveAgent(_ a: AgentRecord, minutes: Double) {
        let id = startLiveCard(a.name, minutes)
        let question = "Based on this live meeting transcript window, respond per your role:\n\n" + liveWindowMaterial(minutes)
        Task { @MainActor in setLiveCard(id, await agentReply(a, history: [], question: question)) }
    }
    private func fireLiveChain(_ c: ChainRecord, minutes: Double) {
        let steps = c.steps.compactMap { sid in agents.first { $0.id == sid } }
        guard !steps.isEmpty else { return }
        let id = startLiveCard(c.name, minutes)
        Task { @MainActor in
            var carry = liveWindowMaterial(minutes)
            for ag in steps { let r = await agentReply(ag, history: [], question: carry); carry = r; if r.hasPrefix("⚠️") { break } }
            setLiveCard(id, carry)
        }
    }
    private func keepLiveCard(_ card: LiveIntelCard) {
        guard let text = card.text, !text.hasPrefix("⚠️") else { return }
        haptic(.medium)
        let rec = OutputRecord(id: UUID().uuidString, title: "\(card.lens) · live", body: text, source: "Live capture", lens: card.lens, path: pathKey)
        outputs.append(rec); persistOutputs()
        withAnimation { liveCards.removeAll { $0.id == card.id } }
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
    // What can live inside a zone — declared in ONE place so filing is never re-gated per call site.
    // Tools (model/connector/workflow) stay anchored in the dock (owner: tools are global, not filed).
    private func isFileable(_ k: PrimitiveKind) -> Bool {
        switch k {
        case .meeting, .artifact, .summary, .actions, .transcript, .topics, .note, .kb, .game: return true
        default: return false
        }
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
        // 2) content filed into a zone — ANY fileable primitive, kind-AGNOSTICALLY (was hard-gated to
        // meeting/output, which is the rot that made "an agent-output note can't go in a zone" possible).
        // Outputs persist their zone on their own record; everything else uses the unified `filed` map.
        if let z = trayHit(end, w, h), isFileable(p.kind) {
            fileAny(p.id, into: z); return
        }
        // 3) free-place
        haptic(.light)
        let u = positions[p.id] ?? CGPoint(x: start.x / w, y: start.y / h)
        positions[p.id] = CGPoint(x: min(0.92, max(0.08, u.x + tr.width / w)), y: min(0.82, max(0.2, u.y + tr.height / h)))
        persistPositions()
    }

    /// File any fileable primitive into a zone path ("" = the desk root). Outputs/notes/KBs/games
    /// persist their zone on their own record; everything else rides the unified `filed` map. Both
    /// stamp a synced membership edge. Shared by drag-drop (iPad diorama) and the lane long-press
    /// "File into…" menu (iPhone, which has no drag).
    private func fileAny(_ id: String, into z: String) {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        if let idx = outputs.firstIndex(where: { "out:\($0.id)" == id }) {
            withAnimation(focusSpring) { outputs[idx].path = z; positions[id] = nil }; persistOutputs()
        } else if let idx = notes.firstIndex(where: { "note:\($0.id)" == id }) {
            withAnimation(focusSpring) { notes[idx].path = z; positions[id] = nil }; persistNotes()
        } else if let idx = kbs.firstIndex(where: { "kb:\($0.id)" == id }) {
            withAnimation(focusSpring) { kbs[idx].path = z; positions[id] = nil }; persistKBs()
        } else if let idx = placedGames.firstIndex(where: { "game:\($0.gameId)" == id }) {
            withAnimation(focusSpring) { placedGames[idx].path = z; positions[id] = nil }; persistGames()
        } else {
            file(id, into: z); return   // file() already haptics + stamps the membership edge
        }
        stampSync("mem:\(id)")
    }

    /// Every zone path that exists, for the lane "File into…" picker. Deepest-labelled by its leaf.
    private func allZonePaths() -> [String] { zones.map(\.path).sorted() }

    /// Where a primitive currently lives ("" = the desk root), to check-mark it in the file menu.
    private func currentPath(of p: any DeskPrimitive) -> String {
        if let o = outputs.first(where: { "out:\($0.id)" == p.id }) { return o.path }
        if let n = notes.first(where: { "note:\($0.id)" == p.id }) { return n.path }
        if let k = kbs.first(where: { "kb:\($0.id)" == p.id }) { return k.path }
        if let g = placedGames.first(where: { "game:\($0.gameId)" == p.id }) { return g.path }
        return filed[p.id] ?? ""
    }

    /// The lane long-press menu (iPhone has no drag): Open + "File into…" a zone. The owner's
    /// "how do I even drag a meeting to a zone on iPhone" — you don't; you long-press and pick.
    @ViewBuilder private func laneFileMenu(_ p: any DeskPrimitive) -> some View {
        Button { tapPrimitive(p) } label: { Label("Open", systemImage: "arrow.up.left.and.arrow.down.right") }
        if spriteKinds.contains(p.kind) {
            Button { haptic(.light); iconPick = IconPickTarget(id: p.id, kind: p.kind, title: p.title) } label: { Label("Change icon", systemImage: "wand.and.stars") }
        }
        if isFileable(p.kind) {
            let cur = currentPath(of: p)
            Menu {
                Button { fileAny(p.id, into: "") } label: {
                    Label("Desk (root)", systemImage: cur.isEmpty ? "checkmark" : "tray")
                }
                ForEach(allZonePaths(), id: \.self) { zp in
                    Button { fileAny(p.id, into: zp) } label: {
                        Label(name(of: zp), systemImage: cur == zp ? "checkmark" : "folder")
                    }
                }
                Divider()
                Button { haptic(.light); pendingFileId = p.id; namingZone = true } label: {
                    Label("New zone…", systemImage: "plus.circle")
                }
            } label: { Label("File into…", systemImage: "tray.and.arrow.down") }
        }
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
        case .workflow:                                         // a saved tool / a travelling graph
            guard let wf = target as? WorkflowPrimitive,
                  let src = members().first(where: { $0.id == sourceId }) else { break }
            // HSM-22-04: a workflow with a graph aboard offers WHERE it runs — the
            // hub runs the synced graph. A prompt-only saved Ask keeps the old
            // no-sheet local path (byte-identical).
            if wf.rec.contract.graphJson != nil {
                offerRunTarget(.init(kind: .workflow(wf.rec), input: src.routableText,
                                     inputId: src.id, inputTitle: src.title))
            } else {
                routeSourceId = sourceId
                runRoute(lens: wf.rec.name, prompt: wf.rec.prompt)
            }
        case .agent:                                            // a tailored agent → answer grounded in the card
            guard let ap = target as? AgentPrimitive,
                  let src = members().first(where: { $0.id == sourceId }) else { break }
            // offer WHERE it runs (on-device vs your desktop's big model) — on-device stays default.
            offerRunTarget(.init(kind: .agent(ap.rec), input: src.routableText, inputId: src.id, inputTitle: src.title))
        case .chain:                                            // a crew → run the card through each agent in order
            guard let cp = target as? ChainPrimitive,
                  let src = members().first(where: { $0.id == sourceId }) else { break }
            offerRunTarget(.init(kind: .chain(cp.rec), input: src.routableText, inputId: src.id, inputTitle: src.title))
        case .kb:                                               // a knowledge base → file the card into it
            guard let kp = target as? KBPrimitive, let idx = kbs.firstIndex(where: { $0.id == kp.rec.id }) else { break }
            #if canImport(UIKit)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            #endif
            withAnimation(focusSpring) { kbs[idx].items += 1 }
            persistKBs(); toast("Filed into \(kp.rec.name)")
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
    /// True when a send through this connector can actually complete: paired AND the host
    /// has it configured (HSM-21-03). An unread status (older hub) keeps the paired-only
    /// behavior rather than presenting everything unconfigured.
    private func connReady(_ connId: String) -> Bool {
        guard hostLink != nil else { return false }
        return connConfigured?[connId] ?? true
    }
    private func actConnectors() -> [(connId: String, name: String, symbol: String, tint: Color)] {
        // Only connectors whose send can complete — a GitHub row with no repo on the host
        // was a guaranteed 400 at approve time (HSM-21-03).
        [("slack", "Slack", "number", DioPal.violet),
         ("github", "GitHub issue", "exclamationmark.bubble.fill", DioPal.mint),
         ("webhook", "Webhook", "bolt.horizontal.fill", DioPal.cobalt)]
            .filter { connReady($0.0) }
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
            withAnimation { showSendCard = false }; sendOverride = nil; routeError = "Pair your desktop first — tap the \(sendTargetName) tile."; return
        }
        sending = true
        let target = sendTargetName
        Task { @MainActor in
            if await link.reachable() == false {
                sending = false; withAnimation { showSendCard = false }; sendOverride = nil
                routeError = "Your desktop isn’t reachable. Wake it and make sure it’s on the same network."
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
                    toast("Sent to \(target) via your desktop")
                } else {
                    routeError = decision.error ?? "\(target) send didn’t complete (status: \(decision.status))."
                }
            } catch let DeskHostLink.HostError.message(m) {
                sending = false; withAnimation { showSendCard = false }; sendOverride = nil; routeError = m
            } catch {
                sending = false; withAnimation { showSendCard = false }; sendOverride = nil; routeError = "Couldn’t reach your desktop."
            }
        }
    }
    // Commit the in-world Connect card: host (a bare host, or host:port), port, the auth token and
    // an optional name. Then sync immediately so pairing is felt right away (the chip goes live).
    private func savePeerFull(host: String, port: String, token: String, name: String) {
        var h = host.trimmingCharacters(in: .whitespaces)
        var p = port.trimmingCharacters(in: .whitespaces)
        // tolerate a pasted "host:port" in the host field
        if let colon = h.lastIndex(of: ":"), let pp = Int(h[h.index(after: colon)...]), pp > 0 {
            p = String(pp); h = String(h[..<colon])
        }
        guard !h.isEmpty, (Int(p) ?? 0) > 0 else { return }
        haptic(.medium)
        peerHost = h; peerPort = p
        peerToken = token.trimmingCharacters(in: .whitespaces)
        peerName = name.trimmingCharacters(in: .whitespaces)
        withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { connecting = false }
        syncDesk(reason: "paired")
    }
    private func forgetPeer() {
        haptic(.medium)
        peerHost = ""; peerToken = ""; peerName = ""
        withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { connecting = false }
    }
    private func toast(_ s: String) {
        withAnimation { sentToast = s }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.9) { withAnimation { if sentToast == s { sentToast = nil } } }
    }
    private func runRoute(lens: String, prompt: String, profileId: String? = nil) {
        withAnimation { showRouteSheet = false }
        let material: String, srcTitle: String
        if routeSourceId == "__bundle__" {
            material = String(bundleText.prefix(6000)); srcTitle = bundleTitle
        } else {
            guard let src = members().first(where: { $0.id == routeSourceId }) else { return }
            material = String(src.routableText.prefix(6000)); srcTitle = src.title
        }
        runAssembled(lens: lens, source: srcTitle, fullPrompt: prompt + "\n\nMaterial:\n" + material, profileId: profileId)
    }

    // the shared inference tail: theater → callLLM → printed card (keep/bin). Used by routes and agents.
    // `provenance` is the run lineage (input card + the agent/chain that produced it) for routed runs;
    // nil for direct lens routes (their `source` is the lineage).
    private func runAssembled(lens: String, source: String, fullPrompt: String, provenance: RunProvenance? = nil, profileId: String? = nil) {
        routeLensRun = lens
        let zpath = pathKey
        haptic(.heavy)
        withAnimation { routing = true }
        Task { @MainActor in
            let result = await callLLM(fullPrompt, profileId: profileId)
            withAnimation { routing = false }
            switch result {
            case .success(let raw):
                let clean = raw.trimmingCharacters(in: .whitespacesAndNewlines)
                #if canImport(UIKit)
                UINotificationFeedbackGenerator().notificationOccurred(.success)
                #endif
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                    printed = OutputRecord(id: UUID().uuidString, title: lens, body: clean.isEmpty ? "(the model returned nothing)" : clean,
                                           source: source, lens: lens, path: zpath, provenance: provenance)
                    printedEgress = InferenceConfigStore.shared.isLocal ? .local : .cloud("endpoint")
                }
                selectedSet = []
            case .failure(let e):
                routeError = friendly(e)
            }
        }
    }

    // the agent's role + always-on context (manual notes, zone meetings, KB) — shared by routing and chat.
    private func agentRoleAndContext(_ a: AgentRecord) -> [String] {
        var blocks: [String] = []
        blocks.append("[ROLE]\n" + (a.systemPrompt.isEmpty ? "You are \(a.name), a helpful assistant." : a.systemPrompt))
        var ctx: [String] = []
        if !a.manualContext.isEmpty { ctx.append(a.manualContext) }
        if a.useZoneContext {
            let z = contentMembers().filter { $0.kind == .meeting }
                .map { "## \($0.title)\n\(String($0.routableText.prefix(2000)))" }.joined(separator: "\n\n")
            if !z.isEmpty { ctx.append("Meetings filed here:\n" + z) }
        }
        if !a.kb.isEmpty { ctx.append("Lean on the knowledge base \"\(a.kb)\" when relevant.") }
        if !ctx.isEmpty { blocks.append("[CONTEXT]\n" + ctx.joined(separator: "\n\n")) }
        return blocks
    }

    // For the builder's context gauge: the est. tokens this zone's meetings would add as grounding
    // (mirrors the assembly above — title + first 2000 chars per meeting).
    private func zoneGroundingTokens() -> Int {
        let z = contentMembers().filter { $0.kind == .meeting }
            .map { "## \($0.title)\n\(String($0.routableText.prefix(2000)))" }.joined(separator: "\n\n")
        return z.isEmpty ? 0 : OnDeviceBudget.estimateTokens("Meetings filed here:\n" + z)
    }

    // The chosen runtime's usable context: the on-device budget when local (clamped by RAM), else the
    // ceiling as a reference for an endpoint (whose true window we don't control).
    private func agentContextLimit() -> Int {
        guard InferenceConfigStore.shared.isLocal, let p = MeetingReviewState.localGGUF() else { return 16_384 }
        let modelBytes = ((try? FileManager.default.attributesOfItem(atPath: p))?[.size] as? Int) ?? 0
        let availRaw = Int(os_proc_available_memory())
        let avail = availRaw > 0 ? availRaw : Int(ProcessInfo.processInfo.physicalMemory / 2)
        return OnDeviceBudget.contextTokens(availableBytes: avail, modelBytes: modelBytes, marginBytes: 768 * 1_048_576, ceiling: 16_384)
    }

    // route a card THROUGH an agent (radial): assemble role + context + the card, infer → printed card.
    // `provenance` records the lineage (input card + this agent) onto the resulting output.
    private func runAgent(_ a: AgentRecord, input: String, inputTitle: String, provenance: RunProvenance? = nil) {
        var blocks = agentRoleAndContext(a)
        let template = a.userTemplate.isEmpty ? "{input}" : a.userTemplate
        blocks.append("[TASK]\n" + template.replacingOccurrences(of: "{input}", with: String(input.prefix(6000))))
        routeSourceId = nil
        runAssembled(lens: a.name, source: inputTitle, fullPrompt: blocks.joined(separator: "\n\n"), provenance: provenance, profileId: a.profileId)
    }

    // one conversational turn — role + context + the running transcript + the new message.
    @MainActor private func agentReply(_ a: AgentRecord, history: [AgentMessage], question: String) async -> String {
        var blocks = agentRoleAndContext(a)
        if !history.isEmpty {
            let convo = history.suffix(12).map { ($0.isYou ? "User: " : "\(a.name): ") + $0.text }.joined(separator: "\n")
            blocks.append("[CONVERSATION SO FAR]\n" + convo)
        }
        blocks.append("[USER]\n" + String(question.prefix(6000)) + "\n\nReply as \(a.name).")
        switch await callLLM(blocks.joined(separator: "\n\n"), profileId: a.profileId) {
        case .success(let raw):
            let c = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            return c.isEmpty ? "⚠️ The model returned nothing — try rephrasing." : c
        case .failure(let e): return "⚠️ " + friendly(e)
        }
    }

    // run a chain (crew): thread the input through each agent in order; the relay animates; final → printed card.
    // `provenance` records the lineage (input card + this crew) onto the final output.
    private func runChain(_ c: ChainRecord, input: String, inputTitle: String, provenance: RunProvenance? = nil) {
        let steps = c.steps.compactMap { sid in agents.first { $0.id == sid } }
        guard !steps.isEmpty else { return }
        haptic(.heavy)
        chainResults = []; chainStep = 0
        withAnimation(.spring(response: 0.45, dampingFraction: 0.8)) { chainRelay = c }
        Task { @MainActor in
            var carry = input
            for (i, ag) in steps.enumerated() {
                withAnimation { chainStep = i }
                let out = await agentReply(ag, history: [], question: carry)
                chainResults.append(out)
                carry = out
                if out.hasPrefix("⚠️") { break }              // a step failed → stop, surface what we got
            }
            withAnimation { chainStep = steps.count }
            try? await Task.sleep(nanoseconds: 800_000_000)    // a beat on "Done"
            let zpath = pathKey
            withAnimation { chainRelay = nil }
            #if canImport(UIKit)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            #endif
            withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                printed = OutputRecord(id: UUID().uuidString, title: c.name, body: carry, source: inputTitle, lens: "Chain", path: zpath, provenance: provenance)
                printedEgress = InferenceConfigStore.shared.isLocal ? .local : .cloud("endpoint")
            }
        }
    }
    // MARK: - Run on the hub (the Mesh "RUNS ON: your desktop")

    /// A built `HTTPDesktopClient` for the paired peer, or nil when unpaired/malformed.
    /// Reuses the same host/port the desk already pairs against (`hs.peer.*`); the hub
    /// run is a longer call than a health probe, so it gets a generous timeout.
    private var desktopClient: HTTPDesktopClient? {
        let h = peerHost.trimmingCharacters(in: .whitespaces)
        guard !h.isEmpty, let p = Int(peerPort.trimmingCharacters(in: .whitespaces)), p > 0 else { return nil }
        let peer = DesktopPeer(host: h, port: p)
        guard let cfg = HTTPDesktopClient.Config(peer: peer, timeout: 120) else { return nil }
        return HTTPDesktopClient(config: cfg)
    }

    /// The remembered RUN-ON choice, sanity-clamped to what's actually possible right now:
    /// honors the last pick when valid; otherwise on-device. "On your desktop" is only sensible
    /// when paired — an unpaired desk always defaults to on-device regardless of the stored pref.
    private var preferredRunTarget: DeskRunTarget {
        if hostLink != nil, DeskRunTarget(rawValue: runTargetPref) == .mac { return .mac }
        return .device
    }

    /// Persist the user's RUN-ON pick so the next run pre-selects it (easy override stays — the
    /// picker still opens). We don't persist a forced on-device fallback, only an explicit choice.
    private func rememberRunTarget(_ t: DeskRunTarget) { runTargetPref = t.rawValue }

    /// Open the where-it-runs picker for a routed agent/chain. The picker pre-highlights the
    /// remembered choice (on-device by default / when unpaired); "your desktop" is offered when
    /// paired, disabled (with a cue) when not.
    private func offerRunTarget(_ run: PendingHubRun) {
        haptic(.medium)
        withAnimation(.spring(response: 0.45, dampingFraction: 0.78)) { pendingHubRun = run }
    }

    /// The user picked on-device — fire the existing local run (unchanged behavior).
    private func runOnDevice(_ run: PendingHubRun) {
        rememberRunTarget(.device)
        withAnimation { pendingHubRun = nil }
        switch run.kind {
        case .agent(let a): runAgent(a, input: run.input, inputTitle: run.inputTitle, provenance: run.provenance)
        case .chain(let c): runChain(c, input: run.input, inputTitle: run.inputTitle, provenance: run.provenance)
        case .workflow(let w):
            // On-device keeps the saved-Ask semantics: the prompt (or the input
            // straight through) — the iPad engine does not run synced graphs yet.
            routeSourceId = run.inputId
            runRoute(lens: w.name, prompt: w.prompt)
        }
    }

    /// The user picked "your desktop" — run the agent/chain on the desktop hub's big model
    /// via `HTTPDesktopClient`, land the result as a printed card with a CLOUD egress
    /// badge (it ran on the Mac, not on-device). Errors surface honestly — never silent.
    private func runOnHub(_ run: PendingHubRun) {
        rememberRunTarget(.mac)
        withAnimation { pendingHubRun = nil }
        guard let client = desktopClient else {
            routeError = "Pair your desktop first to run on its big model."
            return
        }
        let input = String(run.input.prefix(8000))
        let title = run.name
        let source = run.inputTitle
        let zpath = pathKey
        routeLensRun = title
        haptic(.heavy)
        withAnimation { routing = true }
        Task { @MainActor in
            do {
                let output: String
                let artifactId: String?
                var warning: String?
                switch run.kind {
                case .agent(let a):
                    let result = try await client.runAgent(id: a.id, input: input)
                    output = result.output; artifactId = result.artifactId
                case .chain(let c):
                    let result = try await client.runChain(id: c.id, input: input)
                    output = result.output; artifactId = result.artifactId
                case .workflow(let w):
                    // HSM-22-04 — the travelling graph runs where it synced to. A
                    // refused graph's honest `warning` rides onto the card, never
                    // dropped (the same truth the web run surface shows).
                    let result = try await client.runWorkflow(id: w.id, input: input)
                    output = result.output ?? ""; artifactId = result.artifactId
                    warning = result.warning
                }
                withAnimation { routing = false }
                var clean = output.trimmingCharacters(in: .whitespacesAndNewlines)
                if let warning, !warning.isEmpty {
                    clean = "⚠ \(warning)\n\n\(clean)"
                }
                #if canImport(UIKit)
                UINotificationFeedbackGenerator().notificationOccurred(.success)
                #endif
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                    // The hub persisted this run as a run-born artifact (v6) —
                    // the card shares its id so Keep reconciles on sync instead
                    // of duplicating.
                    printed = OutputRecord(id: artifactId ?? UUID().uuidString,
                                           title: title,
                                           body: clean.isEmpty ? "(your desktop returned nothing)" : clean,
                                           source: source,
                                           lens: run.isChain ? "Chain · your desktop"
                                               : (run.isWorkflow ? "Workflow · your desktop" : "Agent · your desktop"),
                                           path: zpath,
                                           provenance: run.provenance)
                    printedEgress = .cloud("your desktop")
                }
                selectedSet = []
            } catch {
                withAnimation { routing = false }
                routeError = hubRunError(error)
            }
        }
    }

    /// A human, honest message for a failed hub run — unreachable Mac, a 502 (no model
    /// loaded on the hub), or a bad payload. Never a silent failure.
    private func hubRunError(_ error: Error) -> String {
        if let e = error as? HTTPDesktopClient.DesktopClientError {
            switch e {
            case .http(502), .http(503): return "Your desktop has no model loaded — start the desktop runtime and try again."
            case .http(404): return "That agent, crew, or workflow isn’t on your desktop yet — sync first, then run on the hub."
            case .http(let code): return "Your desktop refused the run (status \(code))."
            case .malformed: return "Your desktop sent back something the desk couldn’t read."
            }
        }
        if error is URLError { return "Your desktop isn’t reachable. Wake it and make sure it’s on the same network." }
        return "Couldn’t run on your desktop."
    }

    private func saveChain(_ rec: ChainRecord) {
        haptic(.medium)
        withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) {
            if let i = chains.firstIndex(where: { $0.id == rec.id }) { chains[i] = rec } else { chains.append(rec) }
            editingChain = nil
        }
        persistChains(); stampSync(rec.id)
    }
    private func deleteChain(_ id: String) {
        haptic(.medium)
        withAnimation(.spring(response: 0.5, dampingFraction: 0.78)) { chains.removeAll { $0.id == id }; runChainSheet = nil }
        persistChains(); tombstone(id, kind: .chain)
    }
    private func persistChains() {
        if let data = try? JSONEncoder().encode(chains), let s = String(data: data, encoding: .utf8) { chainsJSON = s }
    }

    // MARK: - LIVE SYNC plumbing (port primitives ⇄ the desktop hub)

    private func persistSyncMaps() {
        let enc = JSONEncoder(); enc.dateEncodingStrategy = .iso8601
        if let d = try? enc.encode(syncModified), let s = String(data: d, encoding: .utf8) { syncTimesJSON = s }
        if let d = try? enc.encode(syncTombstones), let s = String(data: d, encoding: .utf8) { tombstonesJSON = s }
    }
    private func loadSyncMaps() {
        let dec = JSONDecoder(); dec.dateDecodingStrategy = .iso8601
        if let d = syncTimesJSON.data(using: .utf8), let m = try? dec.decode([String: Date].self, from: d) { syncModified = m }
        if let d = tombstonesJSON.data(using: .utf8), let m = try? dec.decode([String: Date].self, from: d) { syncTombstones = m }
    }
    /// Stamp a primitive id as modified-now (the iPad's `updatedAt` → meta.last_modified).
    private func stampSync(_ id: String) {
        syncModified[id] = Date()
        syncConfirmed.remove(id)        // a fresh local edit is pending again until the next pass confirms it
        persistSyncMaps()
    }
    /// Record a tombstone (a propagated delete) keyed "kind:id"; clears the live instant.
    private func tombstone(_ id: String, kind: SyncKind) {
        syncModified[id] = nil
        syncConfirmed.remove(id)
        syncTombstones["\(kind.rawValue):\(id)"] = Date()
        persistSyncMaps()
    }
    /// The desk's syncable records as a flat snapshot the store reads.
    private func currentDeskRecords() -> DeskRecords {
        DeskRecords(notes: notes, agents: agents, kbs: kbs, outputs: outputs,
                    chains: chains, workflows: workflows,
                    zones: zones, membership: unifiedMembership(),
                    modified: syncModified, tombstones: syncTombstones)
    }
    /// The desk's filing as one synced map: primitiveId → directoryId (a zone path). Unifies the
    /// `filed` map (meetings) with each output/note/kb/game record's `path`. Root ("") edges are
    /// omitted — only a real filing is an edge worth syncing.
    private func unifiedMembership() -> [String: String] {
        var m: [String: String] = [:]
        for (id, z) in filed where !z.isEmpty { m[id] = z }
        for rec in outputs where !rec.path.isEmpty { m["out:\(rec.id)"] = rec.path }
        for rec in notes where !rec.path.isEmpty { m["note:\(rec.id)"] = rec.path }
        for rec in kbs where !rec.path.isEmpty { m["kb:\(rec.id)"] = rec.path }
        for rec in placedGames where !rec.path.isEmpty { m["game:\(rec.gameId)"] = rec.path }
        return m
    }
    /// Reconcile an incoming unified membership map back into the desk's two filing surfaces:
    /// the `filed` map (meetings) and each record's `path` (outputs/notes/kbs/games). A primitive
    /// missing from the map was unfiled (→ root). Geometry/paint never participates here.
    private func applyMembership(_ m: [String: String]) {
        // meetings → the filed map (keep only meeting keys; clear then reapply)
        var f = filed
        for k in f.keys where k.hasPrefix("m:") { f[k] = nil }
        for (id, z) in m where id.hasPrefix("m:") { f[id] = z }
        filed = f
        for i in outputs.indices { outputs[i].path = m["out:\(outputs[i].id)"] ?? "" }
        for i in notes.indices { notes[i].path = m["note:\(notes[i].id)"] ?? "" }
        for i in kbs.indices { kbs[i].path = m["kb:\(kbs[i].id)"] ?? "" }
        for i in placedGames.indices { placedGames[i].path = m["game:\(placedGames[i].gameId)"] ?? "" }
    }
    /// Write a merged record set back into the desk's @AppStorage-backed arrays + persist.
    private func applyDeskRecords(_ r: DeskRecords) {
        notes = r.notes; agents = r.agents; kbs = r.kbs
        outputs = r.outputs; chains = r.chains; workflows = r.workflows
        zones = r.zones
        syncModified = r.modified; syncTombstones = r.tombstones
        // membership reconciles back into the filed map + each record's path (it overwrites the
        // record-path writes above for the filed surfaces — applied last so it wins).
        applyMembership(r.membership)
        persistNotes(); persistAgents(); persistKBs()
        persistOutputs(); persistChains(); persistWorkflows()
        persistZones(); persistFiled(); persistSyncMaps()
    }
    /// Run one real sync pass against the paired hub: push the local snapshot + pull/apply
    /// remote changes (offline-safe; never on the author path). Triggered on desk load,
    /// after authoring a Note/Agent, and from the manual "Sync" affordance.
    private func syncDesk(reason: String) {
        guard !syncing, let link = hostLink,
              let driver = DeskSyncDriver.make(host: link.host, port: link.port, token: peerToken) else { return }
        syncing = true
        // HSM-21-03: refresh which connectors the host REALLY has configured, so a
        // GitHub tile with no repo on the host cannot present ready (nil keeps the
        // last known truth — an unreachable status is not evidence of unconfigured).
        Task { @MainActor in
            if let status = await link.connectorStatus() { connConfigured = status }
        }
        let snapshot = currentDeskRecords()
        // the desk's primitive ids BEFORE the pull → anything new afterward arrived from a peer
        let before = deskPrimitiveIds(snapshot)
        Task { @MainActor in
            let (merged, outcome) = await driver.syncNow(snapshot)
            if outcome.applied > 0 || merged != snapshot { applyDeskRecords(merged) }
            syncing = false

            if outcome.reachedPeer {
                lastSyncedAt = Date()
                syncState = .synced
                // everything we just pushed/round-tripped is now canonical on the hub → mark it
                // confirmed so the per-primitive cue can honestly read "synced".
                syncConfirmed.formUnion(deskPrimitiveIds(merged))
                lastSyncSummary = "Synced · \(outcome.pushed) sent · \(outcome.applied) in"
                // PULL-APPLIED FEEDBACK: a remote primitive (a note authored on the web, an agent
                // from the desktop) lands on the desk with the NEW-arrival treatment — cross-surface
                // sync is visible + delightful, reusing the same `arrivedIds` halo as a fresh weave.
                let after = deskPrimitiveIds(merged)
                let fresh = after.subtracting(before)
                if !fresh.isEmpty {
                    haptic(.medium)
                    withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) { arrivedIds.formUnion(fresh); flash = 0.45 }
                    withAnimation(.easeOut(duration: 0.9)) { flash = 0 }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 6) { withAnimation { arrivedIds.subtract(fresh) } }
                }
            } else if outcome.pendingAfter > 0 {
                syncState = .offline
                lastSyncSummary = "Offline · queued for your desktop"
            } else {
                syncState = .error("Couldn’t reach your desktop")
                lastSyncSummary = nil
            }
            if let s = lastSyncSummary { toast(s) }
        }
    }
    /// The set of card-level primitive ids (the `kind:bare` desk ids) present in a record set —
    /// used to diff before/after a pull so freshly-pulled primitives get the arrival treatment.
    private func deskPrimitiveIds(_ r: DeskRecords) -> Set<String> {
        var ids = Set<String>()
        ids.formUnion(r.notes.map { "note:\($0.id)" })
        ids.formUnion(r.agents.map { "agent:\($0.id)" })
        ids.formUnion(r.kbs.map { "kb:\($0.id)" })
        ids.formUnion(r.outputs.map { "out:\($0.id)" })
        ids.formUnion(r.chains.map { "chain:\($0.id)" })
        ids.formUnion(r.workflows.map { "wf:\($0.id)" })
        return ids
    }

    // harvest a reply onto the desk as a routable output card.
    private func saveAgentReply(_ text: String, from a: AgentRecord) {
        haptic(.medium)
        let rec = OutputRecord(id: UUID().uuidString, title: "\(a.name) · reply", body: text, source: a.name, lens: "Agent", path: pathKey)
        withAnimation(focusSpring) { outputs.append(rec) }
        persistOutputs(); stampSync(rec.id)
        withAnimation { sentToast = "Saved to desk" }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) { withAnimation { sentToast = nil } }
    }
    // `profileId` (an agent's assignment) resolves which runtime executes this — override → agent →
    // active. For an on-device profile, its `modelFile` chooses the GGUF; the key (endpoint) is joined
    // from the Keychain inside makeProvider.
    @MainActor private func callLLM(_ prompt: String, profileId: String? = nil) async -> Result<String, Error> {
        do {
            let cfg = InferenceConfigStore.shared
            let profile = cfg.resolveProfile(agentProfileId: profileId)
            let langModels = ModelFiles.installed().filter { $0.kind == .language }
            let wantFile = profile.modelFile.isEmpty ? cfg.localModelId : profile.modelFile
            let chosen = langModels.first { $0.id == wantFile } ?? langModels.first
            let provider = try cfg.makeProvider(profile: profile, localModelPath: chosen?.url.path, context: 8192)
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
        // The kept run result materializes on the stage with the same arrival
        // beat woven deliverables and synced peers get (HSM-18-07).
        withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) {
            arrivedIds.insert("out:\(rec.id)"); flash = 0.45
        }
        withAnimation(.easeOut(duration: 0.9)) { flash = 0 }
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) {
            withAnimation { arrivedIds.subtract(["out:\(rec.id)"]) }
        }
        routeSourceId = nil; persistOutputs(); stampSync(rec.id)
    }
    private func binPrinted() { haptic(.light); withAnimation { printed = nil }; routeSourceId = nil }
    private func file(_ id: String, into zpath: String) {
        #if canImport(UIKit)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
        withAnimation(focusSpring) { filed[id] = zpath; positions[id] = nil }
        persistFiled(); persistPositions(); stampSync("mem:\(id)")   // a membership edge is synced
    }

    private func persistPositions() { posCSV = positions.map { "\($0.key)=\($0.value.x),\($0.value.y)" }.joined(separator: ";") }
    private func persistZones() {
        zonesCSV = zones.map { z in
            "\(z.path)|\(z.color)|\(z.cx)|\(z.cy)|\(z.w)|\(z.h)|\(z.borderW)|\(z.borderStyle)|\(z.fillStyle)|\(z.fillOpacity)|\(z.glow ? 1 : 0)|\(z.hex)"
        }.joined(separator: ";")
    }
    private func persistFiled() { dfiledCSV = filed.map { "\($0.key)=\($0.value)" }.joined(separator: ";") }
    private func persistOutputs() {
        if let data = try? JSONEncoder().encode(outputs), let s = String(data: data, encoding: .utf8) { outputsJSON = s }
    }
    private func persistNotes() {
        if let data = try? JSONEncoder().encode(notes), let s = String(data: data, encoding: .utf8) { notesJSON = s }
    }
    // create a fresh note at the current level and open the editor on it
    private func createNote() {
        haptic(.medium)
        let rec = NoteRecord(id: UUID().uuidString, title: "", body: "", path: pathKey)
        withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) { notes.append(rec); editingNote = rec }
        persistNotes()
    }
    private func saveNote(_ rec: NoteRecord) {
        haptic(.medium)
        withAnimation(focusSpring) {
            if let i = notes.firstIndex(where: { $0.id == rec.id }) { notes[i] = rec } else { notes.append(rec) }
            editingNote = nil
        }
        persistNotes(); stampSync(rec.id); syncDesk(reason: "note saved")
    }
    private func deleteNote(_ id: String) {
        haptic(.medium)
        let raw = id.hasPrefix("note:") ? String(id.dropFirst(5)) : id
        withAnimation(focusSpring) { notes.removeAll { $0.id == raw }; editingNote = nil; if selected == id { selected = nil } }
        positions[id] = nil; persistNotes(); persistPositions(); tombstone(raw, kind: .note); syncDesk(reason: "note deleted")
    }
    private func deleteOutput(_ id: String) {
        haptic(.medium)
        let raw = id.hasPrefix("out:") ? String(id.dropFirst(4)) : id
        withAnimation(focusSpring) { outputs.removeAll { $0.id == raw }; if selected == id { selected = nil } }
        positions[id] = nil; persistOutputs(); persistPositions(); tombstone(raw, kind: .artifact)
    }
    private func persistKBs() {
        if let data = try? JSONEncoder().encode(kbs), let s = String(data: data, encoding: .utf8) { kbsJSON = s }
    }
    private func createKB(_ raw: String) {
        let nm = raw.trimmingCharacters(in: .whitespaces)
        guard !nm.isEmpty, !kbs.contains(where: { $0.name.caseInsensitiveCompare(nm) == .orderedSame }) else { return }
        haptic(.medium)
        let newKB = KBRecord(id: UUID().uuidString, name: nm, path: pathKey, items: 0)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) { kbs.append(newKB) }
        persistKBs(); stampSync(newKB.id)
    }
    // create a KB at the current level and immediately open the in-world rename card on it (no
    // naming alert) — the same instant-create-then-edit gesture as a Note.
    private func createKBInline() {
        haptic(.medium)
        let rec = KBRecord(id: UUID().uuidString, name: "", path: pathKey, items: 0)
        withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) { kbs.append(rec); editingKB = rec }
        persistKBs()
    }
    private func renameKB(_ rec: KBRecord) {
        guard let i = kbs.firstIndex(where: { $0.id == rec.id }) else { return }
        haptic(.medium)
        withAnimation(focusSpring) { kbs[i] = rec; editingKB = nil }
        persistKBs(); stampSync(rec.id)
    }
    private func deleteKB(_ id: String) {
        haptic(.medium)
        let raw = id.hasPrefix("kb:") ? String(id.dropFirst(3)) : id
        withAnimation(focusSpring) { kbs.removeAll { $0.id == raw }; editingKB = nil; if selected == id { selected = nil } }
        positions[id] = nil; persistKBs(); persistPositions(); tombstone(raw, kind: .kb)
    }
    private func persistGames() {
        if let data = try? JSONEncoder().encode(placedGames), let s = String(data: data, encoding: .utf8) { gamesJSON = s }
    }
    // place a game on the desk as a primitive (idempotent — tapping an already-placed game just plays it)
    private func placeGame(_ gameId: String) {
        if placedGames.contains(where: { $0.gameId == gameId }) {
            select("game:\(gameId)"); return
        }
        haptic(.medium)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) { placedGames.append(GameRecord(gameId: gameId, path: pathKey)) }
        persistGames(); toast("\(gamePrim(GameRecord(gameId: gameId, path: pathKey)).title) on the desk")
    }
    private func removeGame(_ id: String) {
        haptic(.medium)
        let raw = id.hasPrefix("game:") ? String(id.dropFirst(5)) : id
        withAnimation(focusSpring) { placedGames.removeAll { $0.gameId == raw }; if selected == id { selected = nil } }
        positions[id] = nil; persistGames(); persistPositions()
    }
    // HSM-17-04 — send your reply back into the live coding session. This slice does the optimistic desk
    // side (clears the question, returns the coder to working, toasts). The real inject over
    // `/api/dictation/remote` (the proven Phase-13 path) + voice / dropped-context / AI-draft land next.
    private func answerCoder(_ session: CoderSession, _ text: String) {
        let reply = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !reply.isEmpty else { return }
        haptic(.medium)
        // TODO(HSM-17-04): inject via HTTPDesktopClient.sendRemoteDictation(target: session) on real metal.
        resolveCoder(session, with: .userPrompt(reply))
        answeringCoder = nil
        toast("Sent to \(session.display)")
    }
    private func approveCoder(_ session: CoderSession) {
        haptic(.medium)
        // TODO(HSM-17-04): send the approval down /api/dictation/remote (or the approve route) on real metal.
        resolveCoder(session, with: .notification("You approved the request"))
        openCoderSession = nil
        toast("Approved · \(session.display) continues")
    }
    // optimistic desk side: clear the pending ask, append the resolving event, return the coder to working
    private func resolveCoder(_ session: CoderSession, with event: CoderEvent.Kind) {
        withAnimation(focusSpring) {
            if let i = coders.firstIndex(where: { $0.id == session.id }) {
                coders[i].events.append(CoderEvent(id: "ev-\(coders[i].events.count)", ts: nil, kind: event))
                coders[i].state = .working
            }
            arrivedIds.remove(session.id)
        }
    }
    // harvest a game's best score as a routable output card on the desk
    private func harvestScore(_ g: GamePrimitive) {
        haptic(.medium)
        let body = g.best > 0 ? "Best score in \(g.title): \(g.best)." : "Played \(g.title) — no score recorded yet."
        let rec = OutputRecord(id: UUID().uuidString, title: "\(g.title) · score", body: body, source: g.title, lens: "Score", path: pathKey)
        withAnimation(focusSpring) { outputs.append(rec) }
        persistOutputs(); stampSync(rec.id); select(nil); toast("Score harvested")
    }
    private func persistWorkflows() {
        if let data = try? JSONEncoder().encode(workflows), let s = String(data: data, encoding: .utf8) { workflowsJSON = s }
    }
    private func persistAgents() {
        if let data = try? JSONEncoder().encode(agents), let s = String(data: data, encoding: .utf8) { agentsJSON = s }
    }
    private func persistAgentChats() {
        if let data = try? JSONEncoder().encode(agentChats), let s = String(data: data, encoding: .utf8) { agentChatsJSON = s }
    }
    private func saveAgent(_ rec: AgentRecord) {
        haptic(.medium)
        withAnimation(.spring(response: 0.55, dampingFraction: 0.7)) {
            if let i = agents.firstIndex(where: { $0.id == rec.id }) { agents[i] = rec } else { agents.append(rec) }
            editingAgent = nil
        }
        persistAgents(); stampSync(rec.id); syncDesk(reason: "agent saved")
    }
    private func deleteAgent(_ id: String) {
        haptic(.medium)
        withAnimation(.spring(response: 0.5, dampingFraction: 0.78)) {
            agents.removeAll { $0.id == id }; openAgent = nil
        }
        persistAgents(); tombstone(id, kind: .agent); syncDesk(reason: "agent deleted")
    }
    private func saveTool() {
        let nm = toolName.trimmingCharacters(in: .whitespaces)
        guard !nm.isEmpty, !pendingToolPrompt.isEmpty else { return }
        haptic(.medium)
        let wf = WorkflowRecord(id: UUID().uuidString, name: nm, prompt: pendingToolPrompt)
        withAnimation(.spring(response: 0.6, dampingFraction: 0.62)) { workflows.append(wf) }
        persistWorkflows(); stampSync(wf.id)
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
                var z = ZoneRec(path: String(f[0]), color: ci, cx: cx, cy: cy, w: zw, h: zh)
                if f.count >= 12 {   // style fields appended (backward-compatible)
                    z.borderW = Double(f[6]) ?? 1.5; z.borderStyle = Int(f[7]) ?? 0; z.fillStyle = Int(f[8]) ?? 0
                    z.fillOpacity = Double(f[9]) ?? 0.12; z.glow = (f[10] == "1"); z.hex = Int(f[11]) ?? 0
                }
                return z
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
        if let data = notesJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([NoteRecord].self, from: data) { notes = arr }
        if let data = kbsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([KBRecord].self, from: data) { kbs = arr }
        else {   // one-time migration: legacy classic-home KB names (CSV) → desk KB primitives at root
            let legacy = kbsCSV.split(separator: ";").map(String.init).filter { !$0.isEmpty }
            if !legacy.isEmpty { kbs = legacy.map { KBRecord(id: UUID().uuidString, name: $0, path: "", items: 0) }; persistKBs() }
        }
        if let data = gamesJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([GameRecord].self, from: data) { placedGames = arr }
        if let data = workflowsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([WorkflowRecord].self, from: data) { workflows = arr }
        if let data = agentsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([AgentRecord].self, from: data) { agents = arr }
        if let data = agentChatsJSON.data(using: .utf8), let d = try? JSONDecoder().decode([String: [AgentMessage]].self, from: data) { agentChats = d }
        if let data = chainsJSON.data(using: .utf8), let arr = try? JSONDecoder().decode([ChainRecord].self, from: data) { chains = arr }
        loadSyncMaps()
    }
}
