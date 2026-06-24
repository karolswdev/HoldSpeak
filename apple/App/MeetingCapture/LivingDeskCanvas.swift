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
    var zones: [DeskZone] = []   // persisted drawn places that hold cards (drop a card inside one to file it)
    var pathDepth: Int = 0       // HSM-14-24: how deep we've dived (0 = root) — drives the dive/ascend settle
    var focusedId: String? = nil // HSM-14-22: the selected object, LIFTED toward the camera (focus-lens mode)
    let onTap: (String) -> Void
    let onCycle: (String) -> Void
    var onZoneCreate: (DeskZone) -> Void = { _ in }       // a drawn+named area becomes a persisted zone
    var onFileToZone: (String, String) -> Void = { _, _ in }  // (cardID, zoneName) — drop filed a card into a zone
    var onDive: (String) -> Void = { _ in }              // double-tap a zone -> dive into it (its full path)
    var onAscend: () -> Void = {}                         // double-tap the empty desk -> climb out one level
    var brush: Int = 0          // 0 off · 1 crayon AREA (filled+named) · 2 crayon wall · 3 pencil wall · 4 mud wall

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
        let dtap = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coord.onDoubleTap(_:)))
        dtap.numberOfTapsRequired = 2                                   // double-tap a zone dives in / empty climbs out
        tap.require(toFail: dtap)                                       // a single tap waits to be sure it isn't a double
        let lp = UILongPressGestureRecognizer(target: context.coordinator, action: #selector(Coord.onLongPress(_:)))
        lp.minimumPressDuration = 0.42
        let pan = UIPanGestureRecognizer(target: context.coordinator, action: #selector(Coord.onPan(_:)))
        pan.maximumNumberOfTouches = 1                                  // one finger drags a card
        let camPan = UIPanGestureRecognizer(target: context.coordinator, action: #selector(Coord.onCamPan(_:)))
        camPan.minimumNumberOfTouches = 2                               // two fingers pan the desk
        let pinch = UIPinchGestureRecognizer(target: context.coordinator, action: #selector(Coord.onPinch(_:)))
        for g in [tap, dtap, lp, pan, camPan, pinch] as [UIGestureRecognizer] { v.addGestureRecognizer(g) }
        return v
    }

    func updateUIView(_ v: SCNView, context: Context) {
        context.coordinator.onTap = onTap; context.coordinator.onCycle = onCycle
        context.coordinator.onZoneCreate = onZoneCreate; context.coordinator.onFileToZone = onFileToZone
        context.coordinator.onDive = onDive; context.coordinator.onAscend = onAscend
        context.coordinator.brush = brush
        context.coordinator.zones = zones
        context.coordinator.pathDepth = pathDepth
        context.coordinator.focusedId = focusedId
        context.coordinator.syncUserZones()
        context.coordinator.sync(cards)
        context.coordinator.syncLevel()        // play the dive/ascend settle if the depth changed
        context.coordinator.syncFocus()        // lift the selected object / drop it back
    }

    @MainActor final class Coord: NSObject {
        var onTap: (String) -> Void
        var onCycle: (String) -> Void
        var onZoneCreate: (DeskZone) -> Void = { _ in }
        var onFileToZone: (String, String) -> Void = { _, _ in }
        var onDive: (String) -> Void = { _ in }
        var onAscend: () -> Void = {}
        var pathDepth = 0
        private var lastDepth = 0
        var focusedId: String? = nil
        private var lastFocused: String?
        // saved desk state per lifted node, so it clips back exactly: (pos, rotation, scale, category, collision)
        private var focusSaved: [String: (SCNVector3, SCNVector4, SCNVector3, Int, Int)] = [:]
        private let homeCam = SCNVector3(0, 44, 34)        // the resting camera (matches buildScene)
        weak var view: SCNView?
        let cameraNode = SCNNode()
        private weak var deskNode: SCNNode?
        private var nodes: [String: SCNNode] = [:]
        private var modeOf: [String: String] = [:]
        private var zoneDecor: [SCNNode] = []        // zone fences + labels for the organized default desk
        private var lastZoneSig = ""
        var zones: [DeskZone] = []                    // the persisted user-drawn zones (drop targets)
        private var userZoneNodes: [String: SCNNode] = [:]
        private var lastUserZoneSig = ""
        private var last: [DeskCardData] = []
        private var picked: SCNNode?
        private let liftY: Float = 3.4
        var brush = 0                       // active brush (0 off)
        private var fenceLast: SCNVector3?  // last committed point while drawing a fence
        private var areaStart: SCNVector3?  // first corner while dragging a crayon area
        private var areaPreview: SCNNode?
        private var activeSeg: SCNNode?     // the segment currently growing on dwell
        private var activeA = SCNVector3Zero
        private var activeB = SCNVector3Zero
        private var activeH: CGFloat = 1.1
        private var growTimer: Timer?
        private var lastMoveTime: CFTimeInterval = 0    // when the finger last moved (dwell detection)
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

        // MARK: the OBJECT LANGUAGE — hardware/containers are REAL 3D things, not paper chips. A meeting is
        // a cassette (a recording), a model a glowing cartridge, a KB a crystal, a notebook a book. Only
        // actual documents (summary/topics/action/transcript/artifact) stay paper. Composed in the offscreen
        // renderer (scripts/experience/living-desk-render.swift) first, then ported here 1:1.

        private func uic(_ hex: UInt) -> UIColor {
            UIColor(red: CGFloat((hex >> 16) & 0xFF) / 255, green: CGFloat((hex >> 8) & 0xFF) / 255, blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
        }
        private func blend(_ a: UIColor, _ b: UIColor, _ t: CGFloat) -> UIColor {
            var ar: CGFloat = 0, ag: CGFloat = 0, ab: CGFloat = 0, aa: CGFloat = 0; a.getRed(&ar, green: &ag, blue: &ab, alpha: &aa)
            var br: CGFloat = 0, bg: CGFloat = 0, bb: CGFloat = 0, ba: CGFloat = 0; b.getRed(&br, green: &bg, blue: &bb, alpha: &ba)
            return UIColor(red: ar + (br - ar) * t, green: ag + (bg - ag) * t, blue: ab + (bb - ab) * t, alpha: 1)
        }
        private func pbr(_ c: UIColor, _ rough: CGFloat, _ metal: CGFloat, emit: UIColor? = nil) -> SCNMaterial {
            let m = SCNMaterial(); m.lightingModel = .physicallyBased
            m.diffuse.contents = c; m.roughness.contents = rough; m.metalness.contents = metal
            if let e = emit { m.emission.contents = e }
            return m
        }
        private func gnode(_ g: SCNGeometry, _ mat: SCNMaterial, _ x: Float, _ y: Float, _ z: Float) -> SCNNode {
            g.materials = [mat]; let n = SCNNode(geometry: g); n.position = SCNVector3(x, y, z); n.castsShadow = true; return n
        }
        private func objLabelImg(_ text: String, ink: UIColor, bg: UIColor) -> UIImage {
            let size = CGSize(width: 256, height: 64)
            return UIGraphicsImageRenderer(size: size).image { _ in
                bg.setFill(); UIBezierPath(roundedRect: CGRect(origin: .zero, size: size), cornerRadius: 8).fill()
                let p = NSMutableParagraphStyle(); p.alignment = .left; p.lineBreakMode = .byTruncatingTail
                (text as NSString).draw(in: CGRect(x: 12, y: 14, width: 232, height: 36),
                    withAttributes: [.font: UIFont.systemFont(ofSize: 28, weight: .heavy), .foregroundColor: ink, .paragraphStyle: p])
            }
        }
        private func blinnLabel(_ img: UIImage) -> SCNMaterial { let m = SCNMaterial(); m.lightingModel = .blinn; m.diffuse.contents = img; return m }

        // Each builder returns a visual node whose geometry sits with its BASE at local y=0, plus its
        // (width, height, length) so makeObject can centre it on the physics box.
        private func cassetteVisual(_ tint: UIColor, _ title: String) -> (SCNNode, (CGFloat, CGFloat, CGFloat)) {
            let h = SCNNode()
            h.addChildNode(gnode(SCNBox(width: 9, height: 1.0, length: 5.6, chamferRadius: 0.35), pbr(UIColor(white: 0.13, alpha: 1), 0.5, 0), 0, 0.5, 0))
            h.addChildNode(gnode(SCNBox(width: 8.2, height: 0.1, length: 1.9, chamferRadius: 0.08), blinnLabel(objLabelImg(title, ink: UIColor(white: 0.12, alpha: 1), bg: blend(tint, .white, 0.55))), 0, 1.03, -1.45))
            h.addChildNode(gnode(SCNBox(width: 5.4, height: 0.08, length: 1.8, chamferRadius: 0.15), pbr(UIColor(white: 0.04, alpha: 1), 0.3, 0), 0, 1.02, 1.1))
            for dx in [Float(-1.45), 1.45] {
                h.addChildNode(gnode(SCNCylinder(radius: 0.8, height: 0.16), pbr(UIColor(white: 0.72, alpha: 1), 0.6, 0), dx, 1.08, 1.1))
                h.addChildNode(gnode(SCNCylinder(radius: 0.3, height: 0.2), pbr(tint, 0.4, 0.1), dx, 1.1, 1.1))
            }
            return (h, (9, 1.2, 5.6))
        }
        private func cartridgeVisual(_ tint: UIColor, _ name: String) -> (SCNNode, (CGFloat, CGFloat, CGFloat)) {
            let h = SCNNode()
            h.addChildNode(gnode(SCNBox(width: 7.6, height: 1.5, length: 5.4, chamferRadius: 0.55), pbr(UIColor(white: 0.10, alpha: 1), 0.22, 0.6), 0, 0.75, 0))
            h.addChildNode(gnode(SCNBox(width: 6.6, height: 0.14, length: 0.72, chamferRadius: 0.06), pbr(tint, 0.3, 0, emit: tint), 0, 1.52, -1.7))   // GLOW
            h.addChildNode(gnode(SCNBox(width: 6.6, height: 0.1, length: 2.7, chamferRadius: 0.1), blinnLabel(objLabelImg(name, ink: .white, bg: UIColor(white: 0.17, alpha: 1))), 0, 1.52, 0.2))
            h.addChildNode(gnode(SCNBox(width: 6.0, height: 0.34, length: 0.5, chamferRadius: 0.05), pbr(UIColor(red: 0.85, green: 0.68, blue: 0.25, alpha: 1), 0.3, 0.9), 0, 0.5, 2.6))   // gold pins
            return (h, (7.6, 1.6, 5.4))
        }
        private func crystalVisual(_ tint: UIColor) -> (SCNNode, (CGFloat, CGFloat, CGFloat)) {
            let h = SCNNode(); let m = pbr(tint, 0.05, 0.1, emit: tint.withAlphaComponent(0.35))
            h.addChildNode(gnode(SCNPyramid(width: 3.0, height: 3.6, length: 3.0), m, 0, 1.4, 0))
            let bn = gnode(SCNPyramid(width: 3.0, height: 1.4, length: 3.0), m, 0, 1.4, 0); bn.eulerAngles = SCNVector3(Float.pi, 0, 0); h.addChildNode(bn)
            return (h, (3.0, 5.0, 3.0))
        }
        private func bookVisual(_ tint: UIColor, _ title: String) -> (SCNNode, (CGFloat, CGFloat, CGFloat)) {
            let h = SCNNode()
            h.addChildNode(gnode(SCNBox(width: 8.2, height: 1.2, length: 5.8, chamferRadius: 0.18), pbr(blend(tint, .black, 0.25), 0.55, 0), 0, 0.6, 0))
            h.addChildNode(gnode(SCNBox(width: 7.5, height: 1.0, length: 5.1, chamferRadius: 0.05), pbr(UIColor(red: 0.93, green: 0.90, blue: 0.83, alpha: 1), 0.85, 0), 0.2, 0.65, 0))
            h.addChildNode(gnode(SCNBox(width: 0.5, height: 1.28, length: 5.8, chamferRadius: 0.08), pbr(tint, 0.5, 0), -3.85, 0.62, 0))
            return (h, (8.2, 1.3, 5.8))
        }

        /// Dispatch: a hardware/container kind becomes a real object; a document stays paper.
        private func makeObject(_ c: DeskCardData) -> SCNNode {
            let tint = uic(c.tintHex)
            let built: (SCNNode, (CGFloat, CGFloat, CGFloat))?
            switch c.kind {
            case .meeting:  built = cassetteVisual(tint, c.title)
            case .model:    built = cartridgeVisual(tint, c.title)
            case .kb:       built = crystalVisual(tint)
            case .notebook: built = bookVisual(tint, c.title)
            default:        built = nil                          // summary/topics/action/transcript/artifact = paper
            }
            guard let (visual, dim) = built else { return paperCardNode(c) }
            let (w, H, l) = dim
            visual.position = SCNVector3(0, Float(-H / 2), 0)     // centre the geometry on the physics box
            let container = SCNNode(); container.name = c.id; container.addChildNode(visual)
            let body = SCNPhysicsBody(type: .dynamic, shape: SCNPhysicsShape(geometry: SCNBox(width: w, height: H, length: l, chamferRadius: 0), options: nil))
            body.friction = 0.82; body.restitution = 0.05; body.mass = 0.7
            body.angularDamping = 0.9; body.damping = 0.74; body.contactTestBitMask = 1
            container.physicsBody = body
            return container
        }

        private func paperCardNode(_ c: DeskCardData) -> SCNNode {
            let s = c.renderSize                                    // per-kind shape + size
            let w = CGFloat(s.width) / 28.0, h = CGFloat(s.height) / 28.0, thick: CGFloat = 0.22
            let r = w * CGFloat(c.corner) / CGFloat(s.width)        // match the face's corner radius
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
            if cards.contains(where: { !$0.zone.isEmpty }) { zonedLayout(cards, root); return }
            if !zoneDecor.isEmpty {                       // left the zoned default view -> drop the fences/labels
                zoneDecor.forEach { $0.removeFromParentNode() }; zoneDecor.removeAll(); lastZoneSig = ""
                for (_, n) in nodes { n.removeFromParentNode() }; nodes.removeAll(); modeOf.removeAll()
            }
            let ids = Set(cards.map(\.id))
            for (id, n) in nodes where !ids.contains(id) { n.removeFromParentNode(); nodes[id] = nil; modeOf[id] = nil }
            for (i, c) in cards.enumerated() {
                let sig = "\(c.mode.rawValue):\(c.styleRaw)"
                if let n = nodes[c.id] {
                    if modeOf[c.id] != sig {                         // mode OR style changed -> rebuild the textured node
                        let p = n.presentation.position
                        n.removeFromParentNode()
                        let nn = makeObject(c); nn.position = p; root.addChildNode(nn); nodes[c.id] = nn; modeOf[c.id] = sig
                    }
                } else {
                    let n = makeObject(c)
                    let col = i % 4, row = (i / 4) % 4                  // wrap within the mat — never spawn off-desk
                    n.position = SCNVector3(Float(col) * 8 - 12, 0.9 + Float(i / 16) * 0.6, Float(row) * 4.5 - 5)
                    root.addChildNode(n); nodes[c.id] = n; modeOf[c.id] = sig
                }
            }
            last = cards
        }

        // MARK: zoned default desk — meetings grouped into fenced, labeled time zones (the powerhouse default)
        private func zonedLayout(_ cards: [DeskCardData], _ root: SCNNode) {
            let sig = cards.map { "\($0.id)|\($0.zone)|\($0.mode.rawValue)|\($0.styleRaw)" }.joined(separator: ";")
            if sig == lastZoneSig { return }
            lastZoneSig = sig
            for (_, n) in nodes { n.removeFromParentNode() }; nodes.removeAll(); modeOf.removeAll()
            zoneDecor.forEach { $0.removeFromParentNode() }; zoneDecor.removeAll()
            let order = ["Today", "This Week", "This Month", "Earlier"]
            let groups = order.compactMap { z -> (String, [DeskCardData])? in
                let cs = cards.filter { $0.zone == z }; return cs.isEmpty ? nil : (z, cs)
            }
            let n = max(1, groups.count)
            let tints: [UInt] = [0x3ECF8E, 0x5B8DEF, 0xF2A33C, 0x9B8CFF]
            for (zi, g) in groups.enumerated() {
                let cx = (Float(zi) - Float(n - 1) / 2) * 25
                layoutZone(g.0, g.1, cx, UInt(tints[zi % 4]), root)
            }
            last = cards
        }
        private func layoutZone(_ label: String, _ cards: [DeskCardData], _ cx: Float, _ tint: UInt, _ root: SCNNode) {
            let zhw: Float = 10, zFront: Float = 13, zBack: Float = -12
            let c = UIColor(red: CGFloat((tint >> 16) & 0xFF) / 255, green: CGFloat((tint >> 8) & 0xFF) / 255, blue: CGFloat(tint & 0xFF) / 255, alpha: 1)
            // a low fence around the zone
            let corners = [SCNVector3(cx - zhw, 0, zBack), SCNVector3(cx + zhw, 0, zBack), SCNVector3(cx + zhw, 0, zFront), SCNVector3(cx - zhw, 0, zFront)]
            for i in 0..<4 {
                let a = corners[i], b = corners[(i + 1) % 4]
                let len = CGFloat(hypotf(b.x - a.x, b.z - a.z))
                let box = SCNBox(width: len + 0.6, height: 0.9, length: 0.6, chamferRadius: 0.25)
                let m = SCNMaterial(); m.lightingModel = .blinn; m.diffuse.contents = c
                box.materials = [m]
                let node = SCNNode(geometry: box)
                node.position = SCNVector3((a.x + b.x) / 2, 0.95, (a.z + b.z) / 2)
                node.eulerAngles = SCNVector3(0, -atan2f(b.z - a.z, b.x - a.x), 0)
                node.castsShadow = true
                node.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
                root.addChildNode(node); zoneDecor.append(node)
            }
            // label placard, flat at the zone's front edge
            let plane = SCNPlane(width: 15, height: 3.8)
            let lm = SCNMaterial(); lm.diffuse.contents = labelImage("\(label)   ·   \(cards.count)", c); lm.isDoubleSided = true; lm.lightingModel = .constant
            plane.materials = [lm]
            let lnode = SCNNode(geometry: plane)
            lnode.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)
            lnode.position = SCNVector3(cx, 0.62, zFront - 1.8)
            root.addChildNode(lnode); zoneDecor.append(lnode)
            // cards in a grid inside the fence
            for (i, cd) in cards.prefix(12).enumerated() {
                let col = i % 2, row = i / 2
                let node = makeObject(cd)
                node.position = SCNVector3(cx - 4.2 + Float(col) * 8.4, 1.0, zFront - 5.5 - Float(row) * 3.6)
                root.addChildNode(node); nodes[cd.id] = node; modeOf[cd.id] = "\(cd.mode.rawValue):\(cd.styleRaw)"
            }
        }
        private func labelImage(_ text: String, _ accent: UIColor) -> UIImage {
            let size = CGSize(width: 380, height: 96)
            return UIGraphicsImageRenderer(size: size).image { _ in
                let rect = CGRect(origin: .zero, size: size)
                UIColor(white: 0.10, alpha: 0.94).setFill(); UIBezierPath(roundedRect: rect, cornerRadius: 20).fill()
                accent.setFill(); UIBezierPath(rect: CGRect(x: 0, y: 0, width: 9, height: size.height)).fill()
                let p = NSMutableParagraphStyle(); p.alignment = .center
                (text as NSString).draw(in: rect.insetBy(dx: 18, dy: 24),
                    withAttributes: [.font: UIFont.systemFont(ofSize: 42, weight: .heavy), .foregroundColor: UIColor.white, .paragraphStyle: p])
            }
        }

        // MARK: user zones — persisted drawn places that HOLD cards (the drop-to-file targets)

        /// Redraw the persistent zones whenever their set or any member count changes. Each zone is a
        /// crayon-filled footprint with a live-count placard; its rect is the drop hit-test region.
        func syncUserZones() {
            guard let root = view?.scene?.rootNode else { return }
            let sig = zones.map { "\($0.name)|\($0.cx)|\($0.cz)|\($0.hw)|\($0.hl)|\($0.count)" }.joined(separator: ";")
            if sig == lastUserZoneSig { return }
            lastUserZoneSig = sig
            userZoneNodes.values.forEach { $0.removeFromParentNode() }; userZoneNodes.removeAll()
            for z in zones {
                let node = buildUserZone(z)
                root.addChildNode(node); userZoneNodes[z.name] = node
            }
        }
        private func buildUserZone(_ z: DeskZone) -> SCNNode {
            let color = areaColors[z.colorIdx % areaColors.count]
            let holder = SCNNode(); holder.name = "zone:\(z.name)"
            holder.position = SCNVector3(z.cx, 0, z.cz)
            let w = CGFloat(z.hw * 2), d = CGFloat(z.hl * 2)
            let plane = SCNPlane(width: max(2, w), height: max(2, d))
            let m = SCNMaterial(); m.lightingModel = .constant; m.isDoubleSided = true
            m.diffuse.contents = crayonFillImage(color, w: max(2, w), h: max(2, d))
            plane.materials = [m]
            let pnode = SCNNode(geometry: plane)
            pnode.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)
            pnode.position = SCNVector3(0, 0.53, 0)        // just above the mat (top 0.5) so the fill is visible
            holder.addChildNode(pnode)
            // a count placard pinned at the zone's front edge
            let lplane = SCNPlane(width: 13, height: 3.4)
            let lm = SCNMaterial(); lm.lightingModel = .constant; lm.isDoubleSided = true
            lm.diffuse.contents = labelImage("\(z.leaf)   ·   \(z.count)   ›", color)   // › hints: tap to enter
            lplane.materials = [lm]
            let lnode = SCNNode(geometry: lplane)
            lnode.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)
            lnode.position = SCNVector3(0, 0.60, -z.hl + 2.2)
            holder.addChildNode(lnode)
            return holder
        }
        /// A quick "it went in" pulse on the zone the card was just filed into.
        private func flashZone(_ name: String) {
            guard let node = userZoneNodes[name] else { return }
            node.runAction(.sequence([.scale(to: 1.06, duration: 0.12), .scale(to: 1.0, duration: 0.20)]))
        }

        // MARK: dive — a boundary is a doorway (HSM-14-24). Double-tap a zone to fall IN; double-tap the
        // empty desk to climb OUT. The dramatic camera move sells the descent; the content swap (driven by
        // the new path's cards/zones flowing down) is masked at the camera's closest point.

        @objc func onDoubleTap(_ g: UITapGestureRecognizer) {
            guard brush == 0 else { return }                    // not while a zone brush is armed
            let p = g.location(in: view)
            if let path = zoneHit(at: p) { diveInto(path); return }   // double-tap a zone also dives (owner's reflex)
            if pathDepth > 0 { hLight.impactOccurred(intensity: 0.7); onAscend() }   // double-tap empty desk -> climb out
        }
        // Find a zone under the point — by node FIRST (search ALL hits so a card resting on top can't block
        // it), then by footprint as a fallback. Returns the zone's full path.
        private func zoneHit(at p: CGPoint) -> String? {
            if let hits = view?.hitTest(p, options: [.searchMode: SCNHitTestSearchMode.all.rawValue]) {
                for h in hits { var n: SCNNode? = h.node
                    while let c = n { if let nm = c.name, nm.hasPrefix("zone:") { return String(nm.dropFirst(5)) }; n = c.parent } }
            }
            if let dp = planePoint(at: p, y: 0.53), let z = zones.first(where: { $0.contains(dp.x, dp.z) }) { return z.name }
            return nil
        }
        private func diveInto(_ path: String) {
            hMed.impactOccurred(intensity: 0.95)
            let center = zones.first { $0.name == path }.map { SCNVector3($0.cx, 0, $0.cz) } ?? SCNVector3Zero
            // Rush toward the zone + zoom in; when we're tight on it, swap to its nested desk.
            SCNTransaction.begin(); SCNTransaction.animationDuration = 0.42
            SCNTransaction.animationTimingFunction = CAMediaTimingFunction(name: .easeIn)
            cameraNode.position = SCNVector3(center.x, 20, center.z + 13)
            cameraNode.camera?.fieldOfView = 22
            SCNTransaction.completionBlock = { [weak self] in self?.onDive(path) }
            SCNTransaction.commit()
        }
        /// Called after the content has swapped: if the depth changed, settle the camera home FROM a
        /// directional offset so a dive feels like landing and a back feels like climbing out.
        func syncLevel() {
            guard pathDepth != lastDepth else { return }
            let deeper = pathDepth > lastDepth
            lastDepth = pathDepth
            SCNTransaction.begin(); SCNTransaction.animationDuration = 0          // snap to the start pose
            if deeper { cameraNode.position = SCNVector3(0, 22, 15); cameraNode.camera?.fieldOfView = 24 }
            else { cameraNode.position = SCNVector3(0, 60, 48); cameraNode.camera?.fieldOfView = 50 }
            SCNTransaction.commit()
            SCNTransaction.begin(); SCNTransaction.animationDuration = 0.55       // ease home
            SCNTransaction.animationTimingFunction = CAMediaTimingFunction(name: .easeOut)
            cameraNode.position = homeCam; cameraNode.camera?.fieldOfView = 38
            SCNTransaction.commit()
            hMed.impactOccurred(intensity: 0.6)
        }

        // MARK: focus lens — lift the selected object toward the camera, make it non-solid (so it doesn't
        // shove the desk), and remember where it was so it clips back on exit. The fog + floating outputs
        // are the SwiftUI overlay above; here we just animate the 3D object.
        func syncFocus() {
            if focusedId == lastFocused { return }
            if let prev = lastFocused, let n = nodes[prev] { dropFromFocus(n, prev) }
            if let cur = focusedId, let n = nodes[cur] { liftToFocus(n, cur) }
            lastFocused = focusedId
        }
        private func liftToFocus(_ n: SCNNode, _ id: String) {
            let pres = n.presentation
            focusSaved[id] = (pres.position, pres.rotation, n.scale,
                              n.physicsBody?.categoryBitMask ?? 1, n.physicsBody?.collisionBitMask ?? -1)
            // non-solid: kinematic + collides with nothing, so the lift can't fling the desk around
            n.physicsBody?.type = .kinematic
            n.physicsBody?.categoryBitMask = 0; n.physicsBody?.collisionBitMask = 0
            n.physicsBody?.velocity = SCNVector3Zero; n.physicsBody?.angularVelocity = SCNVector4Zero
            n.position = pres.position; n.rotation = pres.rotation       // sync model to where physics left it
            hMed.impactOccurred(intensity: 0.95)
            SCNTransaction.begin(); SCNTransaction.animationDuration = 0.5
            SCNTransaction.animationTimingFunction = CAMediaTimingFunction(name: .easeOut)
            n.position = SCNVector3(0, 16, 15)                            // lifted up + toward the camera
            n.eulerAngles = SCNVector3(0, 0, 0)                           // squared up, presented
            n.scale = SCNVector3(1.5, 1.5, 1.5)
            SCNTransaction.commit()
        }
        private func dropFromFocus(_ n: SCNNode, _ id: String) {
            guard let s = focusSaved[id] else { return }
            hLight.impactOccurred(intensity: 0.6)
            SCNTransaction.begin(); SCNTransaction.animationDuration = 0.4
            SCNTransaction.animationTimingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            n.position = s.0; n.rotation = s.1; n.scale = s.2            // clip back to the saved desk spot
            SCNTransaction.completionBlock = { [weak n] in
                guard let n, let b = n.physicsBody else { return }
                b.type = .dynamic; b.categoryBitMask = s.3; b.collisionBitMask = s.4
                b.isAffectedByGravity = true; b.velocity = SCNVector3Zero; b.angularVelocity = SCNVector4Zero
            }
            SCNTransaction.commit()
            focusSaved[id] = nil
        }

        // MARK: touch

        private func cardNode(at p: CGPoint) -> SCNNode? {
            guard let hits = view?.hitTest(p, options: [.searchMode: SCNHitTestSearchMode.closest.rawValue]) else { return nil }
            for h in hits { var n: SCNNode? = h.node
                while let c = n { if let nm = c.name { return nm.hasPrefix("zone:") ? nil : c }; n = c.parent } }   // a zone is not a card
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
            guard brush == 0 else { return }
            let p = g.location(in: view)
            if let id = cardNode(at: p)?.name { onTap(id); return }   // a card -> open it
            if let path = zoneHit(at: p) { diveInto(path) }           // a zone (no card on it) -> dive IN (one tap)
        }
        @objc func onLongPress(_ g: UILongPressGestureRecognizer) {
            guard g.state == .began, let id = cardNode(at: g.location(in: view))?.name else { return }
            onCycle(id)
        }
        @objc func onPan(_ g: UIPanGestureRecognizer) {
            let p = g.location(in: view)
            if brush == 1 { drawArea(g, p); return }         // crayon AREA marker
            if brush >= 2 { drawFence(g, p); return }        // fence wall
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
                let loc = g.location(in: view)
                // Drop-to-tag: if the card was released inside a zone footprint, FILE it into that zone and
                // let it SETTLE there (a deliberate drop shouldn't fling back out on residual finger speed).
                var filed = false
                if g.state == .ended, let id = n.name, !id.contains(":"),
                   let dp = planePoint(at: loc, y: 0.2),
                   let z = zones.first(where: { $0.contains(dp.x, dp.z) }) {
                    onFileToZone(id, z.name)
                    hMed.impactOccurred(intensity: 1.0)
                    flashZone(z.name)
                    filed = true
                }
                // Dynamic throw: convert the finger velocity to a world-plane velocity so the card flings + slides.
                let sv = g.velocity(in: view)
                if !filed, abs(sv.x) + abs(sv.y) > 80,
                   let p0 = planePoint(at: loc, y: liftY),
                   let p1 = planePoint(at: CGPoint(x: loc.x + sv.x * 0.1, y: loc.y + sv.y * 0.1), y: liftY) {
                    let vx = (p1.x - p0.x) / 0.1 * 0.55, vz = (p1.z - p0.z) / 0.1 * 0.55
                    n.physicsBody?.velocity = SCNVector3(vx, -1, vz)
                    n.physicsBody?.angularVelocity = SCNVector4(0, 1, 0, Float.random(in: -1.5...1.5))
                    hMed.impactOccurred(intensity: 0.9)         // fling
                } else {
                    n.physicsBody?.velocity = SCNVector3Zero
                    if !filed { hLight.impactOccurred(intensity: 0.5) }   // plain set down
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
        // MARK: crayon AREA — drag a rectangle on the desk; it fills with a child's-crayon scribble in a
        // colour, and you name it. A flat zone marker (no walls) — the simplest organizing brush.
        private let areaColors: [UIColor] = [UIColor(red: 0.95, green: 0.43, blue: 0.30, alpha: 1), UIColor(red: 0.36, green: 0.62, blue: 0.95, alpha: 1),
                                             UIColor(red: 0.34, green: 0.78, blue: 0.52, alpha: 1), UIColor(red: 0.96, green: 0.78, blue: 0.30, alpha: 1)]
        private var areaColorIdx = 0
        private func drawArea(_ g: UIPanGestureRecognizer, _ p: CGPoint) {
            switch g.state {
            case .began:
                areaStart = planePoint(at: p, y: 0.2)
            case .changed:
                guard let a = areaStart, let b = planePoint(at: p, y: 0.2) else { return }
                areaPreview?.removeFromParentNode()
                areaPreview = areaPlane(a, b, color: areaColors[areaColorIdx], preview: true)
                if let pv = areaPreview { view?.scene?.rootNode.addChildNode(pv) }
            case .ended:
                guard let a = areaStart, let b = planePoint(at: p, y: 0.2) else { return }
                areaPreview?.removeFromParentNode(); areaPreview = nil
                if hypotf(b.x - a.x, b.z - a.z) > 3 {
                    hMed.impactOccurred(intensity: 0.7)
                    // Hand the footprint up to be NAMED + PERSISTED; syncUserZones draws the real zone.
                    promptZoneName(cx: (a.x + b.x) / 2, cz: (a.z + b.z) / 2,
                                   hw: abs(b.x - a.x) / 2, hl: abs(b.z - a.z) / 2, colorIdx: areaColorIdx)
                    areaColorIdx = (areaColorIdx + 1) % areaColors.count
                }
                areaStart = nil
            case .cancelled, .failed:
                areaPreview?.removeFromParentNode(); areaPreview = nil; areaStart = nil
            default: break
            }
        }
        private func areaPlane(_ a: SCNVector3, _ b: SCNVector3, color: UIColor, preview: Bool) -> SCNNode {
            let w = CGFloat(abs(b.x - a.x)), d = CGFloat(abs(b.z - a.z))
            let plane = SCNPlane(width: max(2, w), height: max(2, d))
            let m = SCNMaterial(); m.lightingModel = .constant; m.isDoubleSided = true
            m.diffuse.contents = crayonFillImage(color, w: max(2, w), h: max(2, d)); m.transparency = preview ? 0.5 : 1
            plane.materials = [m]
            let node = SCNNode(geometry: plane)
            node.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)
            node.position = SCNVector3((a.x + b.x) / 2, 0.53, (a.z + b.z) / 2)   // match the committed zone height
            node.name = "area"
            return node
        }
        private func crayonFillImage(_ color: UIColor, w: CGFloat, h: CGFloat) -> UIImage {
            let px = CGSize(width: max(64, w * 14), height: max(64, h * 14))
            return UIGraphicsImageRenderer(size: px).image { ctx in
                let c = ctx.cgContext
                let rect = CGRect(origin: .zero, size: px).insetBy(dx: 6, dy: 6)
                // a wobbly hand-drawn border
                color.withAlphaComponent(0.9).setStroke(); c.setLineWidth(5); c.setLineCap(.round)
                let bp = UIBezierPath(roundedRect: rect, cornerRadius: 14); bp.lineWidth = 5; bp.stroke()
                // scribble fill — many slightly-random crayon strokes, like a kid filling it in
                c.setLineWidth(7); c.setLineCap(.round); color.withAlphaComponent(0.34).setStroke()
                var y = rect.minY + 8; var i = 0
                while y < rect.maxY {
                    let jitterA = CGFloat((i * 37) % 11) - 5, jitterB = CGFloat((i * 53) % 13) - 6
                    c.move(to: CGPoint(x: rect.minX + 6 + jitterA, y: y))
                    c.addCurve(to: CGPoint(x: rect.maxX - 6 + jitterB, y: y + 3),
                               control1: CGPoint(x: rect.midX, y: y - 7), control2: CGPoint(x: rect.midX, y: y + 9))
                    c.strokePath(); y += 12; i += 1
                }
            }
        }
        private func promptZoneName(cx: Float, cz: Float, hw: Float, hl: Float, colorIdx: Int) {
            guard let host = view?.window?.rootViewController else { return }
            let alert = UIAlertController(title: "Name this zone", message: "Drop cards inside it to file them here.", preferredStyle: .alert)
            alert.addTextField { $0.placeholder = "e.g. Project Atlas"; $0.autocapitalizationType = .words }
            alert.addAction(UIAlertAction(title: "Add", style: .default) { [weak self] _ in
                guard let self else { return }
                let name = alert.textFields?.first?.text?.trimmingCharacters(in: .whitespaces) ?? ""
                if !name.isEmpty { self.onZoneCreate(DeskZone(name: name, cx: cx, cz: cz, hw: hw, hl: hl, colorIdx: colorIdx)) }
            })
            alert.addAction(UIAlertAction(title: "Skip", style: .cancel))
            host.present(alert, animated: true)
        }

        // MARK: fence drawing — drag on the desk to lay a wall (crayon/pencil/mud); DWELL in one place and
        // the active segment keeps STACKING TALLER (build tall walls by holding). A real physics barrier
        // that casts shadows. A core gesture primitive (HSM-14-22 barriers).
        private func drawFence(_ g: UIPanGestureRecognizer, _ p: CGPoint) {
            switch g.state {
            case .began:
                guard let p0 = planePoint(at: p, y: 0.3) else { return }
                fenceLast = p0; activeA = p0; activeB = p0; activeH = baseWallH()
                activeSeg = buildWall(activeA, activeB, activeH)     // an initial post
                lastMoveTime = CACurrentMediaTime(); startGrow()
            case .changed:
                guard let last = fenceLast, let cur = planePoint(at: p, y: 0.3) else { return }
                if hypotf(cur.x - last.x, cur.z - last.z) > 1.0 {
                    // COMMIT the current segment (leave it in place) and start a fresh one -> a fluid line.
                    activeA = last; activeB = cur; activeH = baseWallH()
                    activeSeg = buildWall(activeA, activeB, activeH)
                    fenceLast = cur; lastMoveTime = CACurrentMediaTime()
                    hLight.impactOccurred(intensity: 0.35)
                }
            case .ended, .cancelled, .failed:
                fenceLast = nil; activeSeg = nil; growTimer?.invalidate(); growTimer = nil
            default: break
            }
        }
        private func baseWallH() -> CGFloat { brush == 4 ? 1.9 : (brush == 3 ? 1.4 : 1.1) }
        private func startGrow() {
            growTimer?.invalidate()
            growTimer = Timer.scheduledTimer(withTimeInterval: 0.08, repeats: true) { [weak self] _ in
                Task { @MainActor in self?.growTick() }
            }
        }
        private func growTick() {                                   // grow ONLY while dwelling (finger stopped)
            guard let seg = activeSeg, activeH < 11 else { return }
            guard CACurrentMediaTime() - lastMoveTime > 0.13 else { return }   // still drawing -> don't grow
            activeH += 0.35
            seg.removeFromParentNode()                             // replace the active segment in place, taller
            activeSeg = buildWall(activeA, activeB, activeH)
            hLight.impactOccurred(intensity: 0.25)
        }
        @discardableResult private func buildWall(_ a: SCNVector3, _ b: SCNVector3, _ h: CGFloat) -> SCNNode {
            let len = CGFloat(hypotf(b.x - a.x, b.z - a.z))
            let (color, thick): (UIColor, CGFloat)
            switch brush {
            case 2: color = UIColor(red: 0.95, green: 0.35, blue: 0.30, alpha: 1); thick = 0.55   // crayon
            case 3: color = UIColor(red: 0.78, green: 0.70, blue: 0.45, alpha: 1); thick = 0.45   // pencil
            default: color = UIColor(red: 0.40, green: 0.29, blue: 0.20, alpha: 1); thick = 1.1   // mud
            }
            let box = SCNBox(width: len + thick, height: h, length: thick, chamferRadius: thick * 0.4)
            let m = SCNMaterial(); m.lightingModel = .blinn; m.diffuse.contents = color; m.roughness.contents = brush == 4 ? 0.95 : 0.6
            box.materials = [m]
            let node = SCNNode(geometry: box)
            node.position = SCNVector3((a.x + b.x) / 2, Float(h) / 2 + 0.5, (a.z + b.z) / 2)
            node.eulerAngles = SCNVector3(0, -atan2f(b.z - a.z, b.x - a.x), 0)
            node.castsShadow = true
            node.physicsBody = SCNPhysicsBody(type: .static, shape: nil)
            node.physicsBody?.friction = 0.7; node.physicsBody?.restitution = 0.1
            view?.scene?.rootNode.addChildNode(node)
            return node
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
