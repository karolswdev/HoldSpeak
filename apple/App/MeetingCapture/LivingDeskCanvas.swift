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
    var fence: Int = 0          // 0 off, 1 crayon, 2 pencil, 3 mud — draw a fence on the desk

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
        pan.maximumNumberOfTouches = 1                                  // one finger drags a card
        let camPan = UIPanGestureRecognizer(target: context.coordinator, action: #selector(Coord.onCamPan(_:)))
        camPan.minimumNumberOfTouches = 2                               // two fingers pan the desk
        let pinch = UIPinchGestureRecognizer(target: context.coordinator, action: #selector(Coord.onPinch(_:)))
        for g in [tap, lp, pan, camPan, pinch] as [UIGestureRecognizer] { v.addGestureRecognizer(g) }
        return v
    }

    func updateUIView(_ v: SCNView, context: Context) {
        context.coordinator.onTap = onTap; context.coordinator.onCycle = onCycle
        context.coordinator.fence = fence
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
        var fence = 0                       // active fence tool (0 off)
        private var fenceLast: SCNVector3?  // last committed point while drawing a fence
        private var activeSeg: SCNNode?     // the segment currently growing on dwell
        private var activeA = SCNVector3Zero
        private var activeB = SCNVector3Zero
        private var activeH: CGFloat = 1.1
        private var growTimer: Timer?
        // Haptics — the feel layer.
        private let hLight = UIImpactFeedbackGenerator(style: .light)
        private let hMed = UIImpactFeedbackGenerator(style: .medium)
        private var lastTick: CFTimeInterval = 0
        private var lastFling: CFTimeInterval = -10

        init(onTap: @escaping (String) -> Void, onCycle: @escaping (String) -> Void) {
            self.onTap = onTap; self.onCycle = onCycle
            super.init(); hLight.prepare(); hMed.prepare()
        }

        // MARK: scene

        func buildScene() -> SCNScene {
            let scene = SCNScene()
            scene.physicsWorld.gravity = SCNVector3(0, -9.8, 0)
            scene.physicsWorld.contactDelegate = self           // landing/collision haptics
            scene.background.contents = UIColor(white: 0.05, alpha: 1)
            scene.lightingEnvironment.contents = UIColor(white: 0.72, alpha: 1)
            scene.lightingEnvironment.intensity = 1.25

            // Camera — pulled BACK to frame the whole workspace, with atmosphere (AO + depth of field + bloom).
            let cam = SCNCamera(); cam.fieldOfView = 38; cam.zNear = 0.2; cam.zFar = 600
            cam.screenSpaceAmbientOcclusionIntensity = 1.4; cam.screenSpaceAmbientOcclusionRadius = 3.5
            cam.wantsDepthOfField = true; cam.focusDistance = 46; cam.fStop = 0.5; cam.focalLength = 30
            cam.bloomIntensity = 0.4; cam.bloomThreshold = 0.9; cam.bloomBlurRadius = 10
            cameraNode.camera = cam
            cameraNode.position = SCNVector3(0, 44, 34)
            cameraNode.eulerAngles = SCNVector3(-60.0 * .pi / 180.0, 0, 0)
            scene.rootNode.addChildNode(cameraNode)

            // Desk — large marble surface so cards have room and don't run off the edge.
            let deskW: CGFloat = 96, deskL: CGFloat = 70
            let desk = SCNBox(width: deskW, height: 1, length: deskL, chamferRadius: 0.5)
            let dm = SCNMaterial(); dm.lightingModel = .blinn
            dm.diffuse.contents = UIColor(red: 0.85, green: 0.83, blue: 0.79, alpha: 1)
            dm.specular.contents = UIColor(white: 0.5, alpha: 1); dm.shininess = 0.3
            desk.materials = [dm]
            let dnode = SCNNode(geometry: desk); dnode.position = SCNVector3(0, -0.5, 0)
            dnode.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
            dnode.physicsBody?.friction = 0.85; dnode.physicsBody?.restitution = 0.04
            scene.rootNode.addChildNode(dnode); deskNode = dnode

            // Invisible perimeter walls — nothing falls off the desk into the void.
            let hw = Float(deskW) / 2 - 1, hl = Float(deskL) / 2 - 1
            for (px, pz, w, l) in [(0, hl, Float(deskW), 1), (0, -hl, Float(deskW), 1), (hw, 0, 1, Float(deskL)), (-hw, 0, 1, Float(deskL))] as [(Float, Float, Float, Float)] {
                let wall = SCNNode(geometry: SCNBox(width: CGFloat(w), height: 10, length: CGFloat(l), chamferRadius: 0))
                wall.geometry?.firstMaterial?.transparency = 0
                wall.position = SCNVector3(px, 4, pz)
                wall.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
                wall.physicsBody?.restitution = 0.1; wall.physicsBody?.friction = 0.6
                scene.rootNode.addChildNode(wall)
            }

            // Leather desk mat — a real surface (physics) so cards rest ON it, not fall through + hide under.
            let pad = SCNBox(width: 36, height: 0.5, length: 22, chamferRadius: 1.6)
            let pmat = SCNMaterial(); pmat.lightingModel = .blinn
            pmat.diffuse.contents = UIColor(red: 0.16, green: 0.13, blue: 0.12, alpha: 1)
            pmat.specular.contents = UIColor(white: 0.16, alpha: 1)
            pad.materials = [pmat]
            let padNode = SCNNode(geometry: pad); padNode.position = SCNVector3(0, 0.25, 3)
            padNode.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
            padNode.physicsBody?.friction = 0.9; padNode.physicsBody?.restitution = 0.02
            scene.rootNode.addChildNode(padNode)

            // Key light — the main shadow caster. On a real SCNView a directional shadow needs an
            // explicit ortho extent + auto z-range, or no shadow renders (the device bug).
            let key = SCNNode(); let kl = SCNLight(); kl.type = .directional; kl.intensity = 680
            kl.color = UIColor.white
            kl.castsShadow = true; kl.shadowMode = .forward; kl.shadowSampleCount = 24; kl.shadowRadius = 5
            kl.shadowColor = UIColor(white: 0, alpha: 0.4)
            key.position = SCNVector3(8, 44, 22); key.eulerAngles = SCNVector3(-1.05, 0.35, 0)
            scene.rootNode.addChildNode(key)

            // Warm lamp pool (no shadow; the key owns shadows).
            let spot = SCNNode(); let sl = SCNLight(); sl.type = .spot
            sl.color = UIColor(red: 1.0, green: 0.86, blue: 0.66, alpha: 1); sl.intensity = 1700
            sl.spotInnerAngle = 26; sl.spotOuterAngle = 66; sl.attenuationEndDistance = 70
            spot.light = sl; spot.position = SCNVector3(-17, 13, -7); spot.look(at: SCNVector3(-6, 0, 2))
            scene.rootNode.addChildNode(spot)

            let amb = SCNNode(); let al = SCNLight(); al.type = .ambient
            al.intensity = 260; al.color = UIColor(white: 0.5, alpha: 1)
            amb.light = al; scene.rootNode.addChildNode(amb)

            // Real poly.pizza props (bundled .scn + palette texture), arranged around the work area.
            let props: [(String, Float, Float, Float, Float)] = [
                ("lightdesk", 17,   -22, -10, 0.5),
                ("plant",      4.0,  22, -10, 0),
                ("books",      5.5, -20,  6, 0.3),
                ("mug",       26,    18,  7, 0),
                ("keyboard",   0.035, 0, -6, 3.14),
            ]
            for (n, s, x, z, ry) in props { if let p = loadProp(n, scale: s, x, z, rotY: ry) { scene.rootNode.addChildNode(p) } }
            return scene
        }

        private func loadProp(_ name: String, scale s: Float, _ x: Float, _ z: Float, rotY: Float) -> SCNNode? {
            guard let url = Bundle.main.url(forResource: name, withExtension: "scn"),
                  let sc = try? SCNScene(url: url, options: nil) else { return nil }
            let group = SCNNode(); for c in sc.rootNode.childNodes { group.addChildNode(c) }
            if let tex = UIImage(named: "\(name)_tex") {
                group.enumerateHierarchy { n, _ in n.geometry?.materials.forEach { $0.diffuse.contents = tex } }
            }
            var mn = SCNVector3Zero
            group.enumerateHierarchy { n, _ in if let g = n.geometry { mn = g.boundingBox.min } }
            let holder = SCNNode(); holder.addChildNode(group)
            group.scale = SCNVector3(s, s, s); group.eulerAngles = SCNVector3(0, rotY, 0)
            holder.position = SCNVector3(x, -Float(mn.y) * s + 0.02, z)
            holder.enumerateHierarchy { n, _ in n.castsShadow = true }
            return holder
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
            visual.castsShadow = true

            let container = SCNNode(); container.name = c.id; container.addChildNode(visual)
            let body = SCNPhysicsBody(type: .dynamic,
                shape: SCNPhysicsShape(geometry: SCNBox(width: w, height: thick, length: h, chamferRadius: 0), options: nil))
            body.friction = 0.82; body.restitution = 0.05; body.mass = 0.6
            body.angularDamping = 0.85; body.damping = 0.72        // settle, don't slide forever
            body.contactTestBitMask = 1                            // fire landing/collision contacts
            container.physicsBody = body
            return container
        }

        func sync(_ cards: [DeskCardData]) {
            guard let root = view?.scene?.rootNode else { return }
            let ids = Set(cards.map(\.id))
            for (id, n) in nodes where !ids.contains(id) { n.removeFromParentNode(); nodes[id] = nil; modeOf[id] = nil }
            for (i, c) in cards.enumerated() {
                let sig = "\(c.mode.rawValue):\(c.styleRaw)"
                if let n = nodes[c.id] {
                    if modeOf[c.id] != sig {                         // mode OR style changed -> rebuild the textured node
                        let p = n.presentation.position
                        n.removeFromParentNode()
                        let nn = makeCard(c); nn.position = p; root.addChildNode(nn); nodes[c.id] = nn; modeOf[c.id] = sig
                    }
                } else {
                    let n = makeCard(c)
                    let col = i % 4, row = (i / 4) % 4                  // wrap within the mat — never spawn off-desk
                    n.position = SCNVector3(Float(col) * 8 - 12, 0.9 + Float(i / 16) * 0.6, Float(row) * 4.5 - 5)
                    root.addChildNode(n); nodes[c.id] = n; modeOf[c.id] = sig
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
        // Reliable finger-follow: cast the screen ray and intersect the horizontal plane at height y.
        // (hitTest-on-desk fails once a lifted card occludes the surface, which wedged the drag.)
        private func planePoint(at p: CGPoint, y: Float) -> SCNVector3? {
            guard let v = view else { return nil }
            let near = v.unprojectPoint(SCNVector3(Float(p.x), Float(p.y), 0))
            let far = v.unprojectPoint(SCNVector3(Float(p.x), Float(p.y), 1))
            let dy = far.y - near.y
            if abs(dy) < 1e-4 { return nil }
            let t = (y - near.y) / dy
            return SCNVector3(near.x + (far.x - near.x) * t, y, near.z + (far.z - near.z) * t)
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
            if fence != 0 { drawFence(g, p); return }       // the fence tool draws instead of moving a card
            switch g.state {
            case .began:
                guard let n = cardNode(at: p) else { return }
                picked = n
                hLight.impactOccurred(intensity: 0.7)           // lift
                n.physicsBody?.isAffectedByGravity = false      // hold it up, move it kinematically
                n.physicsBody?.velocity = SCNVector3Zero
                n.physicsBody?.angularVelocity = SCNVector4Zero
                let cur = n.presentation.position
                n.position = SCNVector3(cur.x, liftY, cur.z)
            case .changed:
                guard let n = picked else { return }
                n.physicsBody?.velocity = SCNVector3Zero
                if let wp = planePoint(at: p, y: liftY) { n.position = SCNVector3(wp.x, liftY, wp.z) }
            case .ended, .cancelled, .failed:
                guard let n = picked else { return }
                n.physicsBody?.isAffectedByGravity = true       // release -> it falls + stacks from the lifted height
                // Dynamic throw: convert the finger velocity to a world-plane velocity so the card flings + slides.
                let sv = g.velocity(in: view)
                let loc = g.location(in: view)
                if abs(sv.x) + abs(sv.y) > 80,
                   let p0 = planePoint(at: loc, y: liftY),
                   let p1 = planePoint(at: CGPoint(x: loc.x + sv.x * 0.1, y: loc.y + sv.y * 0.1), y: liftY) {
                    let vx = (p1.x - p0.x) / 0.1 * 0.55, vz = (p1.z - p0.z) / 0.1 * 0.55
                    n.physicsBody?.velocity = SCNVector3(vx, -1, vz)
                    n.physicsBody?.angularVelocity = SCNVector4(0, 1, 0, Float.random(in: -1.5...1.5))
                    hMed.impactOccurred(intensity: 0.9)         // fling
                } else {
                    n.physicsBody?.velocity = SCNVector3Zero
                    hLight.impactOccurred(intensity: 0.5)       // set down
                }
                lastFling = CACurrentMediaTime()
                picked = nil
            default: break
            }
        }

        private var camStart: SCNVector3?
        @objc func onCamPan(_ g: UIPanGestureRecognizer) {        // two fingers pan the desk
            let t = g.translation(in: view)
            if g.state == .began { camStart = cameraNode.position }
            guard let s = camStart else { return }
            let f: Float = 0.07
            cameraNode.position = SCNVector3(s.x - Float(t.x) * f, s.y, s.z - Float(t.y) * f)
            if g.state == .ended || g.state == .cancelled { camStart = nil }
        }
        // MARK: fence drawing — drag on the desk to lay a wall (crayon/pencil/mud); DWELL in one place and
        // the active segment keeps STACKING TALLER (build tall walls by holding). A real physics barrier
        // that casts shadows. A core gesture primitive (HSM-14-22 barriers).
        private func drawFence(_ g: UIPanGestureRecognizer, _ p: CGPoint) {
            switch g.state {
            case .began:
                guard let p0 = planePoint(at: p, y: 0.3) else { return }
                fenceLast = p0; activeA = p0; activeB = p0; activeH = baseWallH()
                placeActive()
                startGrow()
            case .changed:
                guard let last = fenceLast, let cur = planePoint(at: p, y: 0.3) else { return }
                if hypotf(cur.x - last.x, cur.z - last.z) > 1.3 {
                    activeA = last; activeB = cur; activeH = baseWallH(); placeActive()   // new segment, base height
                    fenceLast = cur; hLight.impactOccurred(intensity: 0.4)
                }
            case .ended, .cancelled, .failed:
                fenceLast = nil; activeSeg = nil; growTimer?.invalidate(); growTimer = nil
            default: break
            }
        }
        private func baseWallH() -> CGFloat { fence == 3 ? 1.9 : (fence == 2 ? 1.4 : 1.1) }
        private func startGrow() {
            growTimer?.invalidate()
            growTimer = Timer.scheduledTimer(withTimeInterval: 0.07, repeats: true) { [weak self] _ in
                Task { @MainActor in self?.growTick() }
            }
        }
        private func growTick() {                                  // dwell -> the active segment grows taller
            guard activeSeg != nil, activeH < 11 else { return }
            activeH += 0.35; placeActive(); hLight.impactOccurred(intensity: 0.25)
        }
        private func placeActive() {                               // (re)build the active wall at its current height
            let a = activeA, b = activeB
            let len = CGFloat(hypotf(b.x - a.x, b.z - a.z))
            let (color, thick): (UIColor, CGFloat)
            switch fence {
            case 1: color = UIColor(red: 0.95, green: 0.35, blue: 0.30, alpha: 1); thick = 0.55   // crayon
            case 2: color = UIColor(red: 0.78, green: 0.70, blue: 0.45, alpha: 1); thick = 0.45   // pencil
            default: color = UIColor(red: 0.40, green: 0.29, blue: 0.20, alpha: 1); thick = 1.1   // mud
            }
            let box = SCNBox(width: len + thick, height: activeH, length: thick, chamferRadius: thick * 0.4)
            let m = SCNMaterial(); m.lightingModel = .blinn; m.diffuse.contents = color; m.roughness.contents = fence == 3 ? 0.95 : 0.6
            box.materials = [m]
            let node = SCNNode(geometry: box)
            node.position = SCNVector3((a.x + b.x) / 2, Float(activeH) / 2 + 0.5, (a.z + b.z) / 2)
            node.eulerAngles = SCNVector3(0, -atan2f(b.z - a.z, b.x - a.x), 0)
            node.castsShadow = true
            node.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
            node.physicsBody?.friction = 0.7; node.physicsBody?.restitution = 0.1
            activeSeg?.removeFromParentNode()
            view?.scene?.rootNode.addChildNode(node); activeSeg = node
        }

        @objc func onPinch(_ g: UIPinchGestureRecognizer) {      // pinch to zoom (FOV)
            guard g.state == .changed, let cam = cameraNode.camera else { return }
            cam.fieldOfView = max(20, min(58, cam.fieldOfView / Double(g.scale)))
            g.scale = 1
        }

        // A landing "clack" — only in the ~1.6s after a drop/fling, so idle resting cards don't buzz.
        @MainActor private func contactTick() {
            let t = CACurrentMediaTime()
            guard t - lastFling < 1.6, t - lastTick > 0.07 else { return }
            lastTick = t
            hLight.impactOccurred(intensity: 0.6)
        }
    }
}

extension LivingDeskCanvas.Coord: SCNPhysicsContactDelegate {
    nonisolated func physicsWorld(_ world: SCNPhysicsWorld, didBegin contact: SCNPhysicsContact) {
        DispatchQueue.main.async { [weak self] in self?.contactTick() }
    }
}
