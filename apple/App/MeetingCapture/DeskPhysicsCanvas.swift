import SwiftUI
import SpriteKit
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-19 — the DeskOS canvas as a real physics world (SpriteKit): cards fly, bounce off the walls
// and each other, spin, settle. Pinch to zoom, drag empty space to pan, tap a card to open. Each card
// presents at a saved MODE (full / half / header) — tap the corner control to cycle it, and it persists.

enum CardMode: String, CaseIterable {
    case full, half, header
    var next: CardMode { switch self { case .full: return .half; case .half: return .header; case .header: return .full } }
    var size: CGSize { switch self { case .full: return CGSize(width: 234, height: 76)
                                       case .half: return CGSize(width: 196, height: 54)
                                       case .header: return CGSize(width: 158, height: 36) } }
}

struct DeskCardData: Equatable {
    let id: String; let title: String; let sub: String; let sprite: String; let tintHex: UInt; var mode: CardMode
}

final class DeskScene: SKScene {
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
        physicsBody?.friction = 0.1; physicsBody?.restitution = 0.5
    }

    func sync(_ cards: [DeskCardData], size: CGSize) {
        let ids = Set(cards.map(\.id))
        for (id, n) in nodes where !ids.contains(id) { n.removeFromParent(); nodes[id] = nil }
        let cols = max(1, Int((size.width - 40) / (CardMode.full.size.width + 22)))
        for (i, c) in cards.enumerated() {
            if let n = nodes[c.id] {
                if (n.userData?["mode"] as? String) != c.mode.rawValue {   // mode changed -> rebuild in place
                    let p = n.position, r = n.zRotation
                    n.removeFromParent()
                    let nn = makeCard(c); nn.position = p; nn.zRotation = r
                    addChild(nn); nodes[c.id] = nn
                }
            } else {
                let n = makeCard(c)
                let col = i % cols, row = i / cols
                n.position = CGPoint(x: 40 + CGFloat(col) * (CardMode.full.size.width + 22) + CardMode.full.size.width / 2,
                                     y: size.height - 120 - CGFloat(row) * (CardMode.full.size.height + 20))
                addChild(n); nodes[c.id] = n
            }
        }
    }

    func tidy(_ cards: [DeskCardData], size: CGSize) {
        let cols = max(1, Int((size.width - 40) / (CardMode.full.size.width + 22)))
        for (i, c) in cards.enumerated() {
            guard let n = nodes[c.id] else { continue }
            let col = i % cols, row = i / cols
            n.physicsBody?.velocity = .zero; n.physicsBody?.angularVelocity = 0
            n.run(.group([.move(to: CGPoint(x: 40 + CGFloat(col) * (CardMode.full.size.width + 22) + CardMode.full.size.width / 2,
                                            y: size.height - 120 - CGFloat(row) * (CardMode.full.size.height + 20)), duration: 0.45),
                          .rotate(toAngle: 0, duration: 0.45, shortestUnitArc: true)]))
        }
    }
    func resetZoom() { cam.run(.group([.scale(to: 1, duration: 0.3), .move(to: CGPoint(x: frame.midX, y: frame.midY), duration: 0.3)])) }
    func zoom(by f: CGFloat) { cam.setScale(min(max(cam.xScale / f, 0.45), 2.8)) }

    private func symbol(_ name: String, _ pt: CGFloat, _ color: UIColor) -> SKSpriteNode {
        let cfg = UIImage.SymbolConfiguration(pointSize: pt, weight: .bold)
        let img = UIImage(systemName: name, withConfiguration: cfg)?.withTintColor(color, renderingMode: .alwaysOriginal)
        let n = SKSpriteNode(texture: img.map { SKTexture(image: $0) }); n.size = CGSize(width: pt + 4, height: pt + 4); return n
    }

    private func makeCard(_ c: DeskCardData) -> SKNode {
        let size = c.mode.size
        let container = SKNode()
        let tint = UIColor(red: CGFloat((c.tintHex >> 16) & 0xFF)/255, green: CGFloat((c.tintHex >> 8) & 0xFF)/255, blue: CGFloat(c.tintHex & 0xFF)/255, alpha: 1)
        let card = SKShapeNode(rectOf: size, cornerRadius: c.mode == .header ? 12 : 16)
        card.fillColor = UIColor(red: 0x1C/255, green: 0x1F/255, blue: 0x27/255, alpha: 1)
        card.strokeColor = .white.withAlphaComponent(0.10); card.lineWidth = 1; container.addChild(card)
        let edge = SKShapeNode(rectOf: CGSize(width: 4, height: size.height - (c.mode == .header ? 14 : 26)), cornerRadius: 2)
        edge.fillColor = tint; edge.strokeColor = .clear; edge.position = CGPoint(x: -size.width/2 + 11, y: 0); container.addChild(edge)

        let markerSize: CGFloat = c.mode == .full ? 46 : (c.mode == .half ? 34 : 20)
        let tex = SKTexture(imageNamed: c.sprite); tex.filteringMode = .nearest
        let marker = SKSpriteNode(texture: tex); marker.size = CGSize(width: markerSize, height: markerSize)
        marker.position = CGPoint(x: -size.width/2 + (c.mode == .header ? 26 : 44), y: 0); container.addChild(marker)

        let titleX = -size.width/2 + (c.mode == .header ? 44 : 76)
        let title = SKLabelNode(text: c.title)
        title.fontName = "HelveticaNeue-Bold"; title.fontSize = c.mode == .header ? 12 : 15; title.fontColor = UIColor(white: 0.96, alpha: 1)
        title.horizontalAlignmentMode = .left; title.verticalAlignmentMode = .center
        title.position = CGPoint(x: titleX, y: c.mode == .full ? 9 : 0); container.addChild(title)
        if c.mode == .full {
            let sub = SKLabelNode(text: c.sub)
            sub.fontName = "HelveticaNeue-Medium"; sub.fontSize = 11; sub.fontColor = UIColor(white: 0.62, alpha: 1)
            sub.horizontalAlignmentMode = .left; sub.verticalAlignmentMode = .center
            sub.position = CGPoint(x: titleX, y: -11); container.addChild(sub)
        }
        // corner resize control
        let ctrl = SKShapeNode(circleOfRadius: 11)
        ctrl.fillColor = UIColor(white: 1, alpha: 0.08); ctrl.strokeColor = .white.withAlphaComponent(0.12); ctrl.lineWidth = 1
        ctrl.position = CGPoint(x: size.width/2 - 16, y: size.height/2 - (c.mode == .header ? 12 : 16))
        let glyph = symbol(c.mode == .full ? "arrow.down.right.and.arrow.up.left" : "arrow.up.left.and.arrow.down.right", 10, .white.withAlphaComponent(0.85))
        glyph.position = ctrl.position; container.addChild(ctrl); container.addChild(glyph)

        let body = SKPhysicsBody(rectangleOf: size)
        body.restitution = 0.45; body.friction = 0.3; body.linearDamping = 1.8; body.angularDamping = 2.0; body.mass = 0.5; body.allowsRotation = true
        container.physicsBody = body; container.name = c.id
        container.userData = ["w": size.width, "h": size.height, "mode": c.mode.rawValue]
        return container
    }

    private func topCard(at p: CGPoint) -> SKNode? {
        nodes.values.first { n in
            let w = (n.userData?["w"] as? CGFloat ?? 234), h = (n.userData?["h"] as? CGFloat ?? 76)
            let l = n.convert(p, from: self); return abs(l.x) < w/2 + 4 && abs(l.y) < h/2 + 4
        }
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self); downPoint = p; lastPoint = p; lastTime = t.timestamp; velocity = .zero
        if let n = topCard(at: p) { dragging = n; dragOffset = CGPoint(x: p.x - n.position.x, y: p.y - n.position.y)
            n.physicsBody?.isDynamic = false; n.run(.scale(to: 1.06, duration: 0.1)) } else { panning = true }
    }
    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self); let dt = max(0.001, t.timestamp - lastTime)
        velocity = CGVector(dx: (p.x - lastPoint.x)/CGFloat(dt), dy: (p.y - lastPoint.y)/CGFloat(dt))
        if let n = dragging { n.position = CGPoint(x: p.x - dragOffset.x, y: p.y - dragOffset.y) }
        else if panning { cam.position = CGPoint(x: cam.position.x - (p.x - lastPoint.x) * cam.xScale, y: cam.position.y - (p.y - lastPoint.y) * cam.xScale) }
        lastPoint = p; lastTime = t.timestamp
    }
    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self); let moved = hypot(p.x - downPoint.x, p.y - downPoint.y)
        if let n = dragging {
            n.run(.scale(to: 1, duration: 0.12)); n.physicsBody?.isDynamic = true
            if moved < 10, let id = n.name {
                let l = n.convert(p, from: self)
                let w = (n.userData?["w"] as? CGFloat ?? 234), h = (n.userData?["h"] as? CGFloat ?? 76)
                if l.x > w/2 - 30 && l.y > h/2 - 28 { onCycle(id) } else { onTap(id) }   // corner = cycle mode
            } else { n.physicsBody?.velocity = velocity; n.physicsBody?.angularVelocity = CGFloat.random(in: -2...2) }
        }
        dragging = nil; panning = false
    }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { dragging?.physicsBody?.isDynamic = true; dragging = nil; panning = false }
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
        let scene = DeskScene(size: CGSize(width: 400, height: 700))
        v.presentScene(scene); context.coordinator.scene = scene
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
    @objc func pinch(_ g: UIPinchGestureRecognizer) { if g.state == .changed, let s = scene { s.zoom(by: g.scale); g.scale = 1 } }
}
