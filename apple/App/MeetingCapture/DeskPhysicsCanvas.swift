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
}

// The premium card, rendered to a SpriteKit texture so the physics node looks like the design.
struct DeskCardFace: View {
    let data: DeskCardData
    var body: some View {
        let m = data.mode
        let tint = Color(hex: data.tintHex)
        let marker: CGFloat = m == .full ? 48 : (m == .half ? 36 : 24)
        HStack(spacing: m == .header ? 9 : 12) {
            ZStack {
                RoundedRectangle(cornerRadius: marker * 0.28, style: .continuous).fill(tint.opacity(0.18))
                DeskSprite(name: data.sprite, size: marker - 4)
            }.frame(width: marker, height: marker)
            VStack(alignment: .leading, spacing: m == .full ? 3 : 1) {
                Text(data.title).font(.system(size: m == .header ? 13 : 15, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                if m == .full { Text(data.sub).font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.muted).lineLimit(1) }
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, m == .header ? 11 : 14).padding(.vertical, m == .header ? 8 : 11)
        .frame(width: m.size.width, height: m.size.height, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: m == .header ? 13 : 18, style: .continuous)
                .fill(LinearGradient(colors: [Sig.s2, Sig.s1], startPoint: .top, endPoint: .bottom))
                .overlay(RoundedRectangle(cornerRadius: m == .header ? 13 : 18, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
                .overlay(alignment: .leading) { RoundedRectangle(cornerRadius: 3).fill(tint).frame(width: 4).padding(.vertical, m == .header ? 9 : 15).padding(.leading, 2) }
        )
    }
}

@MainActor final class DeskScene: SKScene {
    var onTap: (String) -> Void = { _ in }
    var onCycle: (String) -> Void = { _ in }
    private var nodes: [String: SKNode] = [:]
    private var dragging: SKNode?
    private var dragOffset: CGPoint = .zero
    private var lastPoint: CGPoint = .zero
    private var lastTime: TimeInterval = 0
    private var velocity: CGVector = .zero
    private var downPoint: CGPoint = .zero
    private var panning = false
    private var lp: DispatchWorkItem?
    let cam = SKCameraNode()

    override func didMove(to view: SKView) {
        backgroundColor = .clear; scaleMode = .resizeFill
        physicsWorld.gravity = .zero
        rebuildWalls()
        camera = cam; if cam.parent == nil { addChild(cam) }
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
        n.userData = ["w": size.width, "h": size.height, "mode": c.mode.rawValue]
        return n
    }

    func sync(_ cards: [DeskCardData], size: CGSize) {
        let ids = Set(cards.map(\.id))
        for (id, n) in nodes where !ids.contains(id) { n.removeFromParent(); nodes[id] = nil }
        let fw = CardMode.full.size, cols = max(1, Int((size.width - 40) / (fw.width + 22)))
        for (i, c) in cards.enumerated() {
            if let n = nodes[c.id] {
                if (n.userData?["mode"] as? String) != c.mode.rawValue {
                    let p = n.position, r = n.zRotation, v = n.physicsBody?.velocity ?? .zero
                    n.removeFromParent()
                    let nn = makeCard(c); nn.position = p; nn.zRotation = r; nn.physicsBody?.velocity = v
                    addChild(nn); nodes[c.id] = nn
                }
            } else {
                let n = makeCard(c)
                let col = i % cols, row = i / cols
                n.position = CGPoint(x: 40 + CGFloat(col) * (fw.width + 22) + fw.width / 2, y: size.height - 120 - CGFloat(row) * (fw.height + 20))
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
        } else { panning = true }
    }
    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self); let dt = max(0.001, t.timestamp - lastTime)
        if hypot(p.x - downPoint.x, p.y - downPoint.y) > 8 { lp?.cancel() }   // a drag, not a long-press
        velocity = CGVector(dx: (p.x - lastPoint.x)/CGFloat(dt), dy: (p.y - lastPoint.y)/CGFloat(dt))
        if let n = dragging { n.position = CGPoint(x: p.x - dragOffset.x, y: p.y - dragOffset.y) }
        else if panning { cam.position = CGPoint(x: cam.position.x - (p.x - lastPoint.x) * cam.xScale, y: cam.position.y - (p.y - lastPoint.y) * cam.xScale) }
        lastPoint = p; lastTime = t.timestamp
    }
    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        lp?.cancel()
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
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { lp?.cancel(); dragging?.physicsBody?.isDynamic = true; dragging = nil; panning = false }
}

struct DeskPhysicsCanvas: UIViewRepresentable {
    let cards: [DeskCardData]
    var tidyToken: Int
    var zoomToken: Int
    let onTap: (String) -> Void
    let onCycle: (String) -> Void

    func makeCoordinator() -> Coord { Coord() }
    final class Coord { var scene: DeskScene?; var lastTidy = 0; var lastZoom = 0; var last: [DeskCardData] = [] }

    func makeUIView(context: Context) -> SKView {
        let v = SKView(); v.allowsTransparency = true; v.backgroundColor = .clear
        let scene = DeskScene(size: CGSize(width: 400, height: 700)); v.presentScene(scene); context.coordinator.scene = scene
        v.addGestureRecognizer(UIPinchGestureRecognizer(target: context.coordinator, action: #selector(Coord.pinch(_:))))
        return v
    }
    func updateUIView(_ v: SKView, context: Context) {
        guard let scene = context.coordinator.scene else { return }
        scene.onTap = onTap; scene.onCycle = onCycle
        let size = v.bounds.size; if size.width > 1 { scene.size = size }
        if cards != context.coordinator.last { scene.sync(cards, size: size); context.coordinator.last = cards }
        if tidyToken != context.coordinator.lastTidy { scene.tidy(cards, size: size); context.coordinator.lastTidy = tidyToken }
        if zoomToken != context.coordinator.lastZoom { scene.resetZoom(); context.coordinator.lastZoom = zoomToken }
    }
}
extension DeskPhysicsCanvas.Coord {
    @MainActor @objc func pinch(_ g: UIPinchGestureRecognizer) { if g.state == .changed, let s = scene { s.zoom(by: g.scale); g.scale = 1 } }
}
