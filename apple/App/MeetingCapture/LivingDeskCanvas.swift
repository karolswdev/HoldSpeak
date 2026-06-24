import SwiftUI
import SceneKit
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-22 — The Living Desk on the iPad: a fixed-angle (~82deg) 3D SceneKit room. Real meeting cards
// are extruded rounded-rect nodes lying flat on a lit material surface; pick one up and it RISES, release
// and gravity drops it so it can fall onto and STACK on others. Tap opens, long-press cycles shape.
// Behind HS_LIVING_DESK while the SpriteKit desk (DeskPhysicsCanvas) stays the default. The scene setup
// was proven in apple/scripts/experience/living-desk-render.swift before landing here.

@MainActor
struct LivingDeskCanvas: UIViewRepresentable {
    let cards: [DeskCardData]
    let onTap: (String) -> Void
    let onCycle: (String) -> Void

    func makeCoordinator() -> Coord { Coord(onTap: onTap, onCycle: onCycle) }

    func makeUIView(context: Context) -> SCNView {
        let v = SCNView()
        v.backgroundColor = .clear
        v.antialiasingMode = .multisampling2X
        v.rendersContinuously = true
        v.scene = context.coordinator.buildScene()
        v.pointOfView = context.coordinator.cameraNode
        context.coordinator.view = v
        let tap = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coord.onTapGesture(_:)))
        let lp = UILongPressGestureRecognizer(target: context.coordinator, action: #selector(Coord.onLongPress(_:)))
        lp.minimumPressDuration = 0.42
        let pan = UIPanGestureRecognizer(target: context.coordinator, action: #selector(Coord.onPan(_:)))
        for g in [tap, lp, pan] as [UIGestureRecognizer] { v.addGestureRecognizer(g) }
        return v
    }

    func updateUIView(_ v: SCNView, context: Context) {
        context.coordinator.onTap = onTap; context.coordinator.onCycle = onCycle
        context.coordinator.sync(cards)
    }

    @MainActor final class Coord: NSObject {
        var onTap: (String) -> Void
        var onCycle: (String) -> Void
        weak var view: SCNView?
        let cameraNode = SCNNode()
        private weak var deskNode: SCNNode?
        private var nodes: [String: SCNNode] = [:]
        private var modeOf: [String: String] = [:]
        private var last: [DeskCardData] = []
        private var picked: SCNNode?
        private let liftY: Float = 3.4

        init(onTap: @escaping (String) -> Void, onCycle: @escaping (String) -> Void) {
            self.onTap = onTap; self.onCycle = onCycle
        }

        // MARK: scene

        func buildScene() -> SCNScene {
            let scene = SCNScene()
            scene.physicsWorld.gravity = SCNVector3(0, -9.8, 0)
            scene.background.contents = UIColor(white: 0.05, alpha: 1)
            scene.lightingEnvironment.contents = UIColor(red: 0.74, green: 0.75, blue: 0.78, alpha: 1)
            scene.lightingEnvironment.intensity = 1.4

            let cam = SCNCamera(); cam.fieldOfView = 38; cam.zNear = 0.1; cam.zFar = 400
            cam.wantsHDR = true
            cameraNode.camera = cam
            cameraNode.position = SCNVector3(0, 32, 11)
            cameraNode.eulerAngles = SCNVector3(-82.0 * .pi / 180.0, 0, 0)
            scene.rootNode.addChildNode(cameraNode)

            let desk = SCNBox(width: 66, height: 1, length: 48, chamferRadius: 0.5)
            let dm = SCNMaterial(); dm.lightingModel = .blinn
            dm.diffuse.contents = UIColor(red: 0.12, green: 0.13, blue: 0.16, alpha: 1)   // Midnight Carbon default
            dm.specular.contents = UIColor(white: 0.5, alpha: 1); dm.shininess = 0.3
            desk.materials = [dm]
            let dnode = SCNNode(geometry: desk); dnode.position = SCNVector3(0, -0.5, 0)
            dnode.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
            dnode.physicsBody?.friction = 0.85; dnode.physicsBody?.restitution = 0.04
            scene.rootNode.addChildNode(dnode); deskNode = dnode

            let key = SCNNode(); let kl = SCNLight(); kl.type = .directional
            kl.intensity = 700; kl.color = UIColor.white
            key.eulerAngles = SCNVector3(-1.32, 0.25, 0); scene.rootNode.addChildNode(key)

            let spot = SCNNode(); let sl = SCNLight(); sl.type = .spot
            sl.color = UIColor(red: 1.0, green: 0.88, blue: 0.72, alpha: 1); sl.intensity = 2000
            sl.spotInnerAngle = 30; sl.spotOuterAngle = 80
            sl.castsShadow = true; sl.shadowMode = .deferred; sl.shadowSampleCount = 16
            sl.shadowRadius = 8; sl.shadowColor = UIColor(white: 0, alpha: 0.4)
            spot.light = sl; spot.position = SCNVector3(-13, 26, 6); spot.look(at: SCNVector3(-2, 0, -2))
            scene.rootNode.addChildNode(spot)

            let amb = SCNNode(); let al = SCNLight(); al.type = .ambient
            al.intensity = 380; al.color = UIColor(white: 0.55, alpha: 1)
            amb.light = al; scene.rootNode.addChildNode(amb)
            return scene
        }

        @MainActor private func texture(_ c: DeskCardData) -> UIImage? {
            let r = ImageRenderer(content: DeskCardFace(data: c)); r.scale = 3; return r.uiImage
        }

        private func makeCard(_ c: DeskCardData) -> SCNNode {
            let s = c.mode.size
            let w = CGFloat(s.width) / 28.0, h = CGFloat(s.height) / 28.0, r: CGFloat = 0.55, thick: CGFloat = 0.22
            let path = UIBezierPath(roundedRect: CGRect(x: -w/2, y: -h/2, width: w, height: h), cornerRadius: r)
            let shape = SCNShape(path: path, extrusionDepth: thick)
            let front = SCNMaterial(); front.lightingModel = .blinn
            front.diffuse.contents = texture(c) ?? UIColor.darkGray; front.diffuse.wrapS = .clamp; front.diffuse.wrapT = .clamp
            let edge = SCNMaterial(); edge.diffuse.contents = UIColor(white: 0.1, alpha: 1)
            shape.materials = [front, edge, edge]                 // [front, back, sides]

            let visual = SCNNode(geometry: shape)
            visual.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)   // lay flat, face up

            let container = SCNNode(); container.name = c.id; container.addChildNode(visual)
            let body = SCNPhysicsBody(type: .dynamic,
                shape: SCNPhysicsShape(geometry: SCNBox(width: w, height: thick, length: h, chamferRadius: 0), options: nil))
            body.friction = 0.75; body.restitution = 0.06; body.mass = 0.6
            body.angularDamping = 0.7; body.damping = 0.5
            container.physicsBody = body
            return container
        }

        func sync(_ cards: [DeskCardData]) {
            guard let root = view?.scene?.rootNode else { return }
            let ids = Set(cards.map(\.id))
            for (id, n) in nodes where !ids.contains(id) { n.removeFromParentNode(); nodes[id] = nil; modeOf[id] = nil }
            let cols = 4
            for (i, c) in cards.enumerated() {
                if let n = nodes[c.id] {
                    if modeOf[c.id] != c.mode.rawValue {
                        let p = n.presentation.position
                        n.removeFromParentNode()
                        let nn = makeCard(c); nn.position = p; root.addChildNode(nn); nodes[c.id] = nn; modeOf[c.id] = c.mode.rawValue
                    }
                } else {
                    let n = makeCard(c)
                    let col = i % cols, row = i / cols
                    n.position = SCNVector3(Float(col) * 12 - 18, 0.3, Float(row) * 9 - 9)
                    root.addChildNode(n); nodes[c.id] = n; modeOf[c.id] = c.mode.rawValue
                }
            }
            last = cards
        }

        // MARK: touch

        private func cardNode(at p: CGPoint) -> SCNNode? {
            guard let hits = view?.hitTest(p, options: [.searchMode: SCNHitTestSearchMode.closest.rawValue]) else { return nil }
            for h in hits { var n: SCNNode? = h.node; while let c = n { if c.name != nil { return c }; n = c.parent } }
            return nil
        }
        private func deskPoint(at p: CGPoint) -> SCNVector3? {
            guard let desk = deskNode, let hits = view?.hitTest(p, options: [.searchMode: SCNHitTestSearchMode.all.rawValue]) else { return nil }
            return hits.first(where: { $0.node == desk })?.worldCoordinates
        }

        @objc func onTapGesture(_ g: UITapGestureRecognizer) {
            guard let id = cardNode(at: g.location(in: view))?.name else { return }
            onTap(id)
        }
        @objc func onLongPress(_ g: UILongPressGestureRecognizer) {
            guard g.state == .began, let id = cardNode(at: g.location(in: view))?.name else { return }
            onCycle(id)
        }
        @objc func onPan(_ g: UIPanGestureRecognizer) {
            let p = g.location(in: view)
            switch g.state {
            case .began:
                guard let n = cardNode(at: p) else { return }
                picked = n
                n.physicsBody?.isAffectedByGravity = false      // hold it up, move it kinematically
                n.physicsBody?.velocity = SCNVector3Zero
                n.physicsBody?.angularVelocity = SCNVector4Zero
                let cur = n.presentation.position
                n.runAction(.move(to: SCNVector3(cur.x, liftY, cur.z), duration: 0.12))
            case .changed:
                guard let n = picked else { return }
                n.physicsBody?.velocity = SCNVector3Zero
                if let wp = deskPoint(at: p) { n.position = SCNVector3(wp.x, liftY, wp.z) }
            case .ended, .cancelled:
                guard let n = picked else { return }
                n.physicsBody?.isAffectedByGravity = true       // release -> it falls + stacks from the lifted height
                picked = nil
            default: break
            }
        }
    }
}
