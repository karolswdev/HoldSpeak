import SwiftUI
import SpriteKit
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-19 — the DeskOS canvas as a real physics world (SpriteKit), done right. Cards are PREMIUM —
// the real SwiftUI card rendered to a texture, not crude shapes. They have WEIGHT: fling one and it
// slides and SETTLES (high friction + damping, gentle bounce) — a desk, not an air-hockey table.
// LONG-PRESS a card to cycle its shape (full -> half -> header, saved); tap to open; drag to fling.
// Pinch to zoom out, drag empty space to pan.

enum CardMode: String, CaseIterable {
    case full, half, header
    var next: CardMode { switch self { case .full: return .half; case .half: return .header; case .header: return .full } }
    var size: CGSize { switch self { case .full: return CGSize(width: 246, height: 78)
                                       case .half: return CGSize(width: 210, height: 56)
                                       case .header: return CGSize(width: 168, height: 40) } }
}

struct DeskCardData: Equatable {
    let id: String; let title: String; let sub: String; let sprite: String; let tintHex: UInt; var mode: CardMode
    var styleRaw: Int = 0     // CardStyle index (paper/ink palette), customizable per card
    var zone: String = ""     // the default-desk zone this card lives in (Today / This Week / ...)
}

// A real PAPER card — card-stock texture, ink type, a glyph stamp, a ruled line, an accent spine and a
// strip of tape. A physical thing you'd keep on a desk, not a flat UI chip. Rendered to a texture for
// both the SpriteKit and SceneKit desks. `style` picks the paper/ink palette (customizable per card).
struct DeskCardFace: View {
    let data: DeskCardData
    var body: some View {
        let m = data.mode
        let st = CardStyle.of(data.styleRaw)
        let tint = Color(hex: data.tintHex)
        let corner: CGFloat = m == .header ? 11 : 15
        let chip: CGFloat = m == .full ? 27 : (m == .half ? 22 : 18)
        let seed = abs(data.id.hashValue)
        let stickerRot = Double(seed % 17) - 8                          // rugged: each sticker sits at its own angle
        ZStack(alignment: .topLeading) {
            // card stock
            CardPaper(paper: st.paper)
            // a strip of tape (full cards only) — the creative, physical detail
            if m == .full {
                RoundedRectangle(cornerRadius: 2).fill(Color.white.opacity(0.28))
                    .frame(width: 46, height: 13).rotationEffect(.degrees(-4)).blendMode(.softLight)
                    .position(x: m.size.width * 0.5, y: 6)
            }
            HStack(spacing: m == .header ? 8 : 11) {
                // a small, rugged die-cut STICKER of the pixel-art asset, slapped on at an angle
                ZStack {
                    RoundedRectangle(cornerRadius: chip * 0.22, style: .continuous).fill(.white)
                        .shadow(color: .black.opacity(0.22), radius: 1.5, y: 1)
                    DeskSprite(name: data.sprite, size: chip - 6)
                }.frame(width: chip, height: chip)
                    .overlay(RoundedRectangle(cornerRadius: chip * 0.22, style: .continuous).strokeBorder(tint.opacity(0.5), lineWidth: 1.2))
                    .rotationEffect(.degrees(stickerRot))
                VStack(alignment: .leading, spacing: 3) {
                    Text(data.title).font(.system(size: m == .header ? 13 : 15, weight: .heavy, design: .rounded))
                        .foregroundStyle(st.ink).lineLimit(1)
                    if m != .header {
                        Rectangle().fill(st.ink.opacity(0.14)).frame(height: 1)        // ruled index line
                        Text(data.sub).font(.system(size: 11, weight: .semibold, design: .rounded))
                            .foregroundStyle(st.inkSoft).lineLimit(1)
                    }
                }
                Spacer(minLength: 0)
            }
            .padding(.horizontal, m == .header ? 11 : 14).padding(.vertical, m == .header ? 7 : 10)
            .padding(.leading, 4)
        }
        .frame(width: m.size.width, height: m.size.height, alignment: .leading)
        .overlay(alignment: .leading) {                                                  // accent spine
            UnevenRoundedRectangle(topLeadingRadius: corner, bottomLeadingRadius: corner).fill(tint).frame(width: 6)
        }
        .clipShape(RoundedRectangle(cornerRadius: corner, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: corner, style: .continuous).strokeBorder(st.ink.opacity(0.16), lineWidth: 1))
    }
}

// The paper surface: the generated card-stock texture, gently shifted toward the style's paper colour
// (colorMultiply keeps it LIGHT — paper, not wood), plus a soft edge vignette.
struct CardPaper: View {
    let paper: Color
    var body: some View {
        Group {
            if let ui = UIImage(named: "paper") {
                Image(uiImage: ui).resizable().interpolation(.medium).colorMultiply(paper)
            } else { paper }
        }
        .overlay(RadialGradient(colors: [.clear, .black.opacity(0.05)], center: .init(x: 0.5, y: 0.4), startRadius: 50, endRadius: 190))
    }
}

// Per-card customizable paper/ink palette.
struct CardStyle {
    let paper: Color, ink: Color, inkSoft: Color
    static let all: [CardStyle] = [
        CardStyle(paper: Color(hex: 0xEDE6D6), ink: Color(hex: 0x2A2218), inkSoft: Color(hex: 0x6E5F4C)), // cream
        CardStyle(paper: Color(hex: 0xD8C7A8), ink: Color(hex: 0x3A2C18), inkSoft: Color(hex: 0x6B543A)), // kraft
        CardStyle(paper: Color(hex: 0xCBD8E6), ink: Color(hex: 0x1C2A38), inkSoft: Color(hex: 0x47586A)), // blueprint
        CardStyle(paper: Color(hex: 0xF6E59B), ink: Color(hex: 0x4A3D12), inkSoft: Color(hex: 0x7A6A2A)), // sticky note
    ]
    static func of(_ raw: Int) -> CardStyle { all[max(0, min(all.count - 1, raw))] }
    static var count: Int { all.count }
}

@MainActor final class DeskScene: SKScene {
    var onTap: (String) -> Void = { _ in }
    var onCycle: (String) -> Void = { _ in }
    var onSelect: (Set<String>) -> Void = { _ in }
    var lassoMode = false
    private(set) var selected: Set<String> = []
    private var nodes: [String: SKNode] = [:]
    private var dragging: SKNode?
    private var dragOffset: CGPoint = .zero
    private var lastPoint: CGPoint = .zero
    private var lastTime: TimeInterval = 0
    private var velocity: CGVector = .zero
    private var downPoint: CGPoint = .zero
    private var panning = false
    private var lassoing = false
    private var lassoPts: [CGPoint] = []
    private let lassoNode = SKShapeNode()
    private let accentUI = UIColor(red: 1.0, green: 0x6B/255.0, blue: 0x35/255.0, alpha: 1.0)
    private var lp: DispatchWorkItem?
    let cam = SKCameraNode()

    override func didMove(to view: SKView) {
        backgroundColor = .clear; scaleMode = .resizeFill
        physicsWorld.gravity = .zero
        rebuildWalls()
        camera = cam; if cam.parent == nil { addChild(cam) }
        lassoNode.strokeColor = accentUI; lassoNode.lineWidth = 2.5; lassoNode.glowWidth = 2
        lassoNode.fillColor = accentUI.withAlphaComponent(0.08); lassoNode.lineCap = .round
        lassoNode.zPosition = 60; lassoNode.lineJoin = .round
        if lassoNode.parent == nil { addChild(lassoNode) }
    }
    override func didChangeSize(_ oldSize: CGSize) { rebuildWalls() }
    private func rebuildWalls() {
        physicsBody = SKPhysicsBody(edgeLoopFrom: frame.insetBy(dx: 4, dy: 4))
        physicsBody?.friction = 0.6; physicsBody?.restitution = 0.12
    }

    @MainActor private func texture(_ c: DeskCardData) -> SKTexture? {
        let r = ImageRenderer(content: DeskCardFace(data: c)); r.scale = 3
        guard let img = r.uiImage else { return nil }
        let tex = SKTexture(image: img); return tex
    }

    private func makeCard(_ c: DeskCardData) -> SKNode {
        let size = c.mode.size
        let n: SKNode
        if let tex = texture(c) {
            let s = SKSpriteNode(texture: tex); s.size = size; n = s
        } else { n = SKShapeNode(rectOf: size, cornerRadius: 16) }
        let body = SKPhysicsBody(rectangleOf: size)
        body.restitution = 0.12; body.friction = 0.55; body.linearDamping = 4.6; body.angularDamping = 5.0
        body.mass = 1.0; body.allowsRotation = true
        n.physicsBody = body; n.name = c.id
        n.userData = ["w": size.width, "h": size.height, "sig": "\(c.mode.rawValue):\(c.styleRaw)"]
        return n
    }

    // Output cards encode their parent meeting in the id ("open:<mid>", "out:<kind>:<mid>...") so a
    // spilled child can be born AT its parent and spray outward — the meeting opening into its parts.
    private func parentMeetingId(_ id: String) -> String? {
        if id.hasPrefix("open:") { return String(id.dropFirst(5)) }
        if id.hasPrefix("out:") { let p = id.split(separator: ":"); return p.count >= 3 ? String(p[2]) : nil }
        return nil
    }
    func sync(_ cards: [DeskCardData], size: CGSize) {
        let ids = Set(cards.map(\.id))
        for (id, n) in nodes where !ids.contains(id) { n.removeFromParent(); nodes[id] = nil }
        let fw = CardMode.full.size, cols = max(1, Int((size.width - 40) / (fw.width + 22)))
        var burst: [String: Int] = [:]
        for (i, c) in cards.enumerated() {
            if let n = nodes[c.id] {
                if (n.userData?["sig"] as? String) != "\(c.mode.rawValue):\(c.styleRaw)" {
                    let p = n.position, r = n.zRotation, v = n.physicsBody?.velocity ?? .zero
                    n.removeFromParent()
                    let nn = makeCard(c); nn.position = p; nn.zRotation = r; nn.physicsBody?.velocity = v
                    addChild(nn); nodes[c.id] = nn
                }
            } else {
                let n = makeCard(c)
                if let pid = parentMeetingId(c.id), let pnode = nodes[pid] {
                    let k = burst[pid] ?? 0; burst[pid] = k + 1
                    let a = CGFloat(k) * 2.399, rad: CGFloat = 150 + CGFloat(k % 4) * 30
                    n.position = pnode.position; n.setScale(0.25); n.zRotation = 0
                    n.run(.group([.move(to: CGPoint(x: pnode.position.x + cos(a) * rad, y: pnode.position.y + sin(a) * rad), duration: 0.42),
                                  .scale(to: 1, duration: 0.42),
                                  .rotate(toAngle: CGFloat.random(in: -0.12...0.12), duration: 0.42, shortestUnitArc: true)]))
                } else {
                    let col = i % cols, row = i / cols
                    n.position = CGPoint(x: 40 + CGFloat(col) * (fw.width + 22) + fw.width / 2, y: size.height - 120 - CGFloat(row) * (fw.height + 20))
                }
                addChild(n); nodes[c.id] = n
            }
        }
    }
    func tidy(_ cards: [DeskCardData], size: CGSize) {
        let fw = CardMode.full.size, cols = max(1, Int((size.width - 40) / (fw.width + 22)))
        for (i, c) in cards.enumerated() {
            guard let n = nodes[c.id] else { continue }
            let col = i % cols, row = i / cols
            n.physicsBody?.velocity = .zero; n.physicsBody?.angularVelocity = 0
            n.run(.group([.move(to: CGPoint(x: 40 + CGFloat(col) * (fw.width + 22) + fw.width / 2, y: size.height - 120 - CGFloat(row) * (fw.height + 20)), duration: 0.4),
                          .rotate(toAngle: 0, duration: 0.4, shortestUnitArc: true)]))
        }
    }
    func resetZoom() { cam.run(.group([.scale(to: 1, duration: 0.3), .move(to: CGPoint(x: frame.midX, y: frame.midY), duration: 0.3)])) }
    func zoom(by f: CGFloat) { cam.setScale(min(max(cam.xScale / f, 0.45), 2.8)) }

    private func topCard(at p: CGPoint) -> SKNode? {
        nodes.values.first { n in
            let w = (n.userData?["w"] as? CGFloat ?? 246), h = (n.userData?["h"] as? CGFloat ?? 78)
            let l = n.convert(p, from: self); return abs(l.x) < w/2 + 4 && abs(l.y) < h/2 + 4
        }
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self); downPoint = p; lastPoint = p; lastTime = t.timestamp; velocity = .zero
        if let n = topCard(at: p), let id = n.name {
            dragging = n; dragOffset = CGPoint(x: p.x - n.position.x, y: p.y - n.position.y)
            n.physicsBody?.isDynamic = false; n.run(.scale(to: 1.05, duration: 0.1))
            let item = DispatchWorkItem { [weak self, weak n] in        // long-press -> cycle shape
                guard let self, let n, self.dragging === n else { return }
                n.physicsBody?.isDynamic = true; n.run(.scale(to: 1, duration: 0.1)); self.dragging = nil
                self.onCycle(id)
            }
            lp = item; DispatchQueue.main.asyncAfter(deadline: .now() + 0.42, execute: item)
        } else if lassoMode { lassoing = true; lassoPts = [p]; updateLasso() }
        else { panning = true }
    }
    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self); let dt = max(0.001, t.timestamp - lastTime)
        if lassoing { lassoPts.append(p); updateLasso(); lastPoint = p; lastTime = t.timestamp; return }
        if hypot(p.x - downPoint.x, p.y - downPoint.y) > 8 { lp?.cancel() }   // a drag, not a long-press
        velocity = CGVector(dx: (p.x - lastPoint.x)/CGFloat(dt), dy: (p.y - lastPoint.y)/CGFloat(dt))
        if let n = dragging { n.position = CGPoint(x: p.x - dragOffset.x, y: p.y - dragOffset.y) }
        else if panning { cam.position = CGPoint(x: cam.position.x - (p.x - lastPoint.x) * cam.xScale, y: cam.position.y - (p.y - lastPoint.y) * cam.xScale) }
        lastPoint = p; lastTime = t.timestamp
    }
    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        lp?.cancel()
        if lassoing { finishLasso(); lassoing = false; dragging = nil; panning = false; return }
        guard let t = touches.first else { panning = false; return }
        let p = t.location(in: self); let moved = hypot(p.x - downPoint.x, p.y - downPoint.y)
        if let n = dragging {
            n.run(.scale(to: 1, duration: 0.12)); n.physicsBody?.isDynamic = true
            if moved < 10, let id = n.name { onTap(id) }
            else {                                      // controlled toss (scaled so a flick doesn't rocket)
                n.physicsBody?.velocity = CGVector(dx: velocity.dx * 0.5, dy: velocity.dy * 0.5)
                n.physicsBody?.angularVelocity = CGFloat.random(in: -1.2...1.2)
            }
        }
        dragging = nil; panning = false
    }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { lp?.cancel(); lassoing = false; lassoNode.path = nil; dragging?.physicsBody?.isDynamic = true; dragging = nil; panning = false }

    // MARK: - Lasso multi-select
    private func updateLasso() {
        let path = CGMutablePath()
        if let f = lassoPts.first { path.move(to: f); for q in lassoPts.dropFirst() { path.addLine(to: q) }; path.closeSubpath() }
        lassoNode.path = path
    }
    private func finishLasso() {
        lassoNode.path = nil
        guard lassoPts.count > 2 else { lassoPts = []; selected = []; applySelection(); onSelect(selected); return }
        let poly = lassoPts
        selected = Set(nodes.compactMap { (id, n) in pointInPoly(n.position, poly) ? id : nil })
        lassoPts = []; applySelection(); onSelect(selected)
    }
    private func pointInPoly(_ pt: CGPoint, _ poly: [CGPoint]) -> Bool {
        var inside = false; var j = poly.count - 1
        for i in 0..<poly.count {
            let a = poly[i], b = poly[j]
            if (a.y > pt.y) != (b.y > pt.y), pt.x < (b.x - a.x) * (pt.y - a.y) / (b.y - a.y) + a.x { inside.toggle() }
            j = i
        }
        return inside
    }
    func applySelection() {
        for (id, n) in nodes {
            let ring = n.childNode(withName: "sel")
            if selected.contains(id) {
                if ring == nil {
                    let w = (n.userData?["w"] as? CGFloat ?? 246), h = (n.userData?["h"] as? CGFloat ?? 78)
                    let r = SKShapeNode(rectOf: CGSize(width: w + 12, height: h + 12), cornerRadius: 22)
                    r.name = "sel"; r.strokeColor = accentUI; r.lineWidth = 3; r.glowWidth = 5
                    r.fillColor = accentUI.withAlphaComponent(0.10); r.zPosition = -1
                    n.addChild(r)
                }
            } else { ring?.removeFromParent() }
        }
    }
    func clearSelection() { selected = []; applySelection(); onSelect(selected) }
    func gather() {                                  // pull the selected cards into a tight bundle in view
        guard !selected.isEmpty else { return }
        let sel = nodes.filter { selected.contains($0.key) }.map(\.value)
        let cx = sel.map { $0.position.x }.reduce(0, +) / CGFloat(sel.count)
        let cy = sel.map { $0.position.y }.reduce(0, +) / CGFloat(sel.count)
        for (i, n) in sel.enumerated() {
            n.physicsBody?.velocity = .zero; n.physicsBody?.angularVelocity = 0
            let a = CGFloat(i) * 2.399, rad = CGFloat(i) * 9
            n.run(.group([.move(to: CGPoint(x: cx + cos(a) * rad, y: cy + sin(a) * rad), duration: 0.32),
                          .rotate(toAngle: CGFloat.random(in: -0.05...0.05), duration: 0.32, shortestUnitArc: true)]))
        }
    }
}

struct DeskPhysicsCanvas: UIViewRepresentable {
    let cards: [DeskCardData]
    var tidyToken: Int
    var zoomToken: Int
    var lassoMode: Bool
    var clearToken: Int
    var gatherToken: Int
    let onTap: (String) -> Void
    let onCycle: (String) -> Void
    let onSelect: (Set<String>) -> Void

    func makeCoordinator() -> Coord { Coord() }
    final class Coord { var scene: DeskScene?; var lastTidy = 0; var lastZoom = 0; var lastClear = 0; var lastGather = 0; var last: [DeskCardData] = [] }

    func makeUIView(context: Context) -> SKView {
        let v = SKView(); v.allowsTransparency = true; v.backgroundColor = .clear
        let scene = DeskScene(size: CGSize(width: 400, height: 700)); v.presentScene(scene); context.coordinator.scene = scene
        v.addGestureRecognizer(UIPinchGestureRecognizer(target: context.coordinator, action: #selector(Coord.pinch(_:))))
        return v
    }
    func updateUIView(_ v: SKView, context: Context) {
        guard let scene = context.coordinator.scene else { return }
        scene.onTap = onTap; scene.onCycle = onCycle; scene.onSelect = onSelect; scene.lassoMode = lassoMode
        let size = v.bounds.size; if size.width > 1 { scene.size = size }
        if cards != context.coordinator.last { scene.sync(cards, size: size); scene.applySelection(); context.coordinator.last = cards }
        if tidyToken != context.coordinator.lastTidy { scene.tidy(cards, size: size); context.coordinator.lastTidy = tidyToken }
        if zoomToken != context.coordinator.lastZoom { scene.resetZoom(); context.coordinator.lastZoom = zoomToken }
        if clearToken != context.coordinator.lastClear { scene.clearSelection(); context.coordinator.lastClear = clearToken }
        if gatherToken != context.coordinator.lastGather { scene.gather(); context.coordinator.lastGather = gatherToken }
    }
}
extension DeskPhysicsCanvas.Coord {
    @MainActor @objc func pinch(_ g: UIPinchGestureRecognizer) { if g.state == .changed, let s = scene { s.zoom(by: g.scale); g.scale = 1 } }
}
