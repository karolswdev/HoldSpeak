import SwiftUI
import SpriteKit
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-19 — the DeskOS canvas as a REAL physics world (SpriteKit). Cards are physics bodies: you
// fling them and they FLY, BOUNCE off the walls and each other, spin to an angle, and settle. Pinch to
// zoom out and see the whole desk; drag the empty desk to pan. Tap a card to open the real meeting.
// (Lasso-select -> bundle -> categorize layer on top of this foundation next.) SwiftUI can't do
// collisions/bounce — this is why the canvas is SpriteKit, surfaced through SpriteView/UIViewRepresentable.

struct DeskCardData: Equatable {
    let id: String
    let title: String
    let sub: String
    let sprite: String
    let tintHex: UInt
}

// MARK: - The scene

final class DeskScene: SKScene {
    var onTap: (String) -> Void = { _ in }
    private var nodes: [String: SKNode] = [:]
    private var dragging: SKNode?
    private var dragOffset: CGPoint = .zero
    private var lastPoint: CGPoint = .zero
    private var lastTime: TimeInterval = 0
    private var velocity: CGVector = .zero
    private var downPoint: CGPoint = .zero
    private var panning = false
    let cam = SKCameraNode()
    private let cardSize = CGSize(width: 234, height: 76)

    override func didMove(to view: SKView) {
        backgroundColor = .clear
        scaleMode = .resizeFill
        physicsWorld.gravity = .zero
        physicsWorld.speed = 1
        rebuildWalls()
        camera = cam
        if cam.parent == nil { addChild(cam) }
    }
    override func didChangeSize(_ oldSize: CGSize) { rebuildWalls() }

    private func rebuildWalls() {
        let inset = frame.insetBy(dx: 4, dy: 4)
        physicsBody = SKPhysicsBody(edgeLoopFrom: inset)
        physicsBody?.friction = 0.1
        physicsBody?.restitution = 0.5
    }

    /// Diff the card set against the scene: add new nodes (dropped in with a little scatter), remove gone.
    func sync(_ cards: [DeskCardData], size: CGSize) {
        let ids = Set(cards.map(\.id))
        for (id, n) in nodes where !ids.contains(id) { n.removeFromParent(); nodes[id] = nil }
        for (i, c) in cards.enumerated() where nodes[c.id] == nil {
            let n = makeCard(c)
            // Lay them in a loose readable grid first; physics takes over the moment you touch one.
            let cols = max(1, Int((size.width - 40) / (cardSize.width + 22)))
            let col = i % cols, row = i / cols
            let x = 40 + CGFloat(col) * (cardSize.width + 22) + cardSize.width / 2
            let y = size.height - 120 - CGFloat(row) * (cardSize.height + 20)
            n.position = CGPoint(x: x, y: y)
            addChild(n); nodes[c.id] = n
        }
    }

    func tidy(_ cards: [DeskCardData], size: CGSize) {
        let cols = max(1, Int((size.width - 40) / (cardSize.width + 22)))
        for (i, c) in cards.enumerated() {
            guard let n = nodes[c.id] else { continue }
            let col = i % cols, row = i / cols
            let x = 40 + CGFloat(col) * (cardSize.width + 22) + cardSize.width / 2
            let y = size.height - 120 - CGFloat(row) * (cardSize.height + 20)
            n.physicsBody?.velocity = .zero; n.physicsBody?.angularVelocity = 0
            n.run(.group([.move(to: CGPoint(x: x, y: y), duration: 0.45), .rotate(toAngle: 0, duration: 0.45, shortestUnitArc: true)]))
        }
    }

    func resetZoom() { cam.run(.group([.scale(to: 1, duration: 0.3), .move(to: CGPoint(x: frame.midX, y: frame.midY), duration: 0.3)])) }
    func zoom(by factor: CGFloat) { cam.setScale(min(max(cam.xScale / factor, 0.5), 2.6)) }

    // MARK: card node (SpriteKit-composed: rounded card + pixel marker + labels)
    private func makeCard(_ c: DeskCardData) -> SKNode {
        let container = SKNode()
        let tint = UIColor(red: CGFloat((c.tintHex >> 16) & 0xFF)/255, green: CGFloat((c.tintHex >> 8) & 0xFF)/255, blue: CGFloat(c.tintHex & 0xFF)/255, alpha: 1)
        let card = SKShapeNode(rectOf: cardSize, cornerRadius: 16)
        card.fillColor = UIColor(red: 0x1C/255, green: 0x1F/255, blue: 0x27/255, alpha: 1)
        card.strokeColor = UIColor.white.withAlphaComponent(0.10); card.lineWidth = 1
        container.addChild(card)
        // accent edge
        let edge = SKShapeNode(rectOf: CGSize(width: 4, height: cardSize.height - 26), cornerRadius: 2)
        edge.fillColor = tint; edge.strokeColor = .clear; edge.position = CGPoint(x: -cardSize.width/2 + 12, y: 0)
        container.addChild(edge)
        // pixel-art marker (loaded from the bundle)
        let tex = SKTexture(imageNamed: c.sprite); tex.filteringMode = .nearest
        let marker = SKSpriteNode(texture: tex); marker.size = CGSize(width: 46, height: 46)
        marker.position = CGPoint(x: -cardSize.width/2 + 44, y: 0); container.addChild(marker)
        // title + sub
        let title = SKLabelNode(text: c.title)
        title.fontName = "HelveticaNeue-Bold"; title.fontSize = 15; title.fontColor = UIColor(white: 0.96, alpha: 1)
        title.horizontalAlignmentMode = .left; title.verticalAlignmentMode = .center
        title.position = CGPoint(x: -cardSize.width/2 + 76, y: 9)
        title.preferredMaxLayoutWidth = cardSize.width - 96; container.addChild(title)
        let sub = SKLabelNode(text: c.sub)
        sub.fontName = "HelveticaNeue-Medium"; sub.fontSize = 11; sub.fontColor = UIColor(white: 0.62, alpha: 1)
        sub.horizontalAlignmentMode = .left; sub.verticalAlignmentMode = .center
        sub.position = CGPoint(x: -cardSize.width/2 + 76, y: -11); container.addChild(sub)

        let body = SKPhysicsBody(rectangleOf: cardSize)
        body.restitution = 0.45; body.friction = 0.3; body.linearDamping = 1.8; body.angularDamping = 2.0
        body.mass = 0.5; body.allowsRotation = true
        container.physicsBody = body
        container.name = c.id
        return container
    }

    private func topCard(at p: CGPoint) -> SKNode? {
        for n in nodes.values where n.contains(p) { return n }
        // contains() uses parent coords; fall back to a small search
        return nodes.values.first { abs($0.position.x - p.x) < cardSize.width/2 + 4 && abs($0.position.y - p.y) < cardSize.height/2 + 4 }
    }

    // MARK: touches
    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self)
        downPoint = p; lastPoint = p; lastTime = t.timestamp; velocity = .zero
        if let n = topCard(at: p) {
            dragging = n; dragOffset = CGPoint(x: p.x - n.position.x, y: p.y - n.position.y)
            n.physicsBody?.isDynamic = false   // hold it while dragging
            n.run(.scale(to: 1.06, duration: 0.1))
        } else { panning = true }
    }
    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self)
        let dt = max(0.001, t.timestamp - lastTime)
        velocity = CGVector(dx: (p.x - lastPoint.x)/CGFloat(dt), dy: (p.y - lastPoint.y)/CGFloat(dt))
        if let n = dragging {
            n.position = CGPoint(x: p.x - dragOffset.x, y: p.y - dragOffset.y)
        } else if panning {
            cam.position = CGPoint(x: cam.position.x - (p.x - lastPoint.x) * cam.xScale,
                                   y: cam.position.y - (p.y - lastPoint.y) * cam.xScale)
        }
        lastPoint = p; lastTime = t.timestamp
    }
    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let t = touches.first else { return }
        let p = t.location(in: self)
        let moved = hypot(p.x - downPoint.x, p.y - downPoint.y)
        if let n = dragging {
            n.run(.scale(to: 1, duration: 0.12))
            n.physicsBody?.isDynamic = true
            if moved < 10, let id = n.name { onTap(id) }                 // tap
            else { n.physicsBody?.velocity = velocity                     // FLING -> fly + bounce
                   n.physicsBody?.angularVelocity = CGFloat.random(in: -2...2) }
        }
        dragging = nil; panning = false
    }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        dragging?.physicsBody?.isDynamic = true; dragging = nil; panning = false
    }
}

// MARK: - SwiftUI bridge

struct DeskPhysicsCanvas: UIViewRepresentable {
    let cards: [DeskCardData]
    var tidyToken: Int
    var zoomToken: Int
    let onTap: (String) -> Void

    func makeCoordinator() -> Coord { Coord() }
    final class Coord { var scene: DeskScene?; var lastTidy = 0; var lastZoom = 0; var lastIDs: [String] = [] }

    func makeUIView(context: Context) -> SKView {
        let v = SKView()
        v.allowsTransparency = true
        v.backgroundColor = .clear
        let scene = DeskScene(size: CGSize(width: 400, height: 700))
        scene.onTap = onTap
        v.presentScene(scene)
        context.coordinator.scene = scene
        let pinch = UIPinchGestureRecognizer(target: context.coordinator, action: #selector(Coord.pinch(_:)))
        context.coordinator.scene = scene
        v.addGestureRecognizer(pinch)
        return v
    }
    func updateUIView(_ v: SKView, context: Context) {
        guard let scene = context.coordinator.scene else { return }
        scene.onTap = onTap
        let size = v.bounds.size
        if size.width > 1 { scene.size = size }
        let ids = cards.map(\.id)
        if ids != context.coordinator.lastIDs { scene.sync(cards, size: size); context.coordinator.lastIDs = ids }
        if tidyToken != context.coordinator.lastTidy { scene.tidy(cards, size: size); context.coordinator.lastTidy = tidyToken }
        if zoomToken != context.coordinator.lastZoom { scene.resetZoom(); context.coordinator.lastZoom = zoomToken }
    }
}

extension DeskPhysicsCanvas.Coord {
    @objc func pinch(_ g: UIPinchGestureRecognizer) {
        guard let s = scene else { return }
        if g.state == .changed { s.zoom(by: g.scale); g.scale = 1 }
    }
}
