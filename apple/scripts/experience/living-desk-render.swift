// HSM-14-22 — offscreen SceneKit render of the Living Desk, populated. A lit material desk with REAL
// poly.pizza CC0 props (lamp, plant, laptop, keyboard, mug, books, pencil) arranged around the work
// area, a directional shadow light so everything casts shadows, and rounded-rect meeting cards in front.
// Build: swiftc -O living-desk-render.swift -o /tmp/ldr -framework SceneKit -framework AppKit -framework Metal
// Run:   /tmp/ldr /tmp/living-desk.png   (props loaded from /tmp/propobj/<name>/<name>.obj)

import Foundation
import SceneKit
import AppKit

// A kind of card — drives SIZE, shape, badge, mirroring DeskCardKind so the owner sees the real variety.
struct CardKind { let label: String?; let corner: CGFloat; let pxW: CGFloat; let pxH: CGFloat; let seed: Int }

func cardImage(_ tint: NSColor, _ kind: CardKind, snippet: String) -> NSImage {
    let size = NSSize(width: kind.pxW, height: kind.pxH); let img = NSImage(size: size); img.lockFocus()
    let rect = NSRect(origin: .zero, size: size)
    let clip = NSBezierPath(roundedRect: rect, xRadius: kind.corner, yRadius: kind.corner); clip.addClip()
    if let paper = NSImage(contentsOfFile: "../../App/paper.png") { paper.draw(in: rect) }
    else { NSColor(calibratedRed: 0.93, green: 0.90, blue: 0.84, alpha: 1).setFill(); NSBezierPath(rect: rect).fill() }
    tint.withAlphaComponent(0.10).setFill(); NSBezierPath(rect: rect).fill()
    tint.setFill(); NSBezierPath(rect: NSRect(x: 0, y: 0, width: 6, height: kind.pxH)).fill()    // accent spine
    let ink = NSColor(calibratedRed: 0.16, green: 0.13, blue: 0.09, alpha: 1)
    let ctx = NSGraphicsContext.current!.cgContext
    // LOOSE sticker — varied rotation / scale / shape / nudge with a lifted corner. Not regulated.
    let rot = CGFloat(kind.seed % 31 - 15) * .pi / 180
    let chip = 30 * (0.86 + CGFloat(kind.seed % 8) * 0.045)
    let shape = kind.seed % 3
    let scr: CGFloat = shape == 1 ? chip/2 : (shape == 2 ? chip*0.08 : chip*0.26)
    ctx.saveGState(); ctx.translateBy(x: 26 + CGFloat(kind.seed % 5), y: kind.pxH - 28 + CGFloat(kind.seed % 5)); ctx.rotate(by: rot)
    let sq = NSRect(x: -chip/2, y: -chip/2, width: chip, height: chip)
    ctx.setShadow(offset: CGSize(width: 1.4, height: -1.8), blur: 3, color: NSColor(white: 0, alpha: 0.3).cgColor)
    NSColor.white.setFill(); NSBezierPath(roundedRect: sq, xRadius: scr, yRadius: scr).fill()
    ctx.setShadow(offset: .zero, blur: 0, color: nil)
    tint.withAlphaComponent(0.75).setFill(); NSBezierPath(roundedRect: sq.insetBy(dx: 7, dy: 7), xRadius: scr*0.6, yRadius: scr*0.6).fill()
    tint.setStroke(); let sp = NSBezierPath(roundedRect: sq, xRadius: scr, yRadius: scr); sp.lineWidth = 2; sp.stroke()
    ctx.restoreGState()
    let tx: CGFloat = 52
    ink.setFill(); NSBezierPath(roundedRect: NSRect(x: tx, y: kind.pxH - 24, width: min(kind.pxW - tx - 76, 118), height: 11), xRadius: 3, yRadius: 3).fill()
    ink.withAlphaComponent(0.45).setFill(); NSBezierPath(roundedRect: NSRect(x: tx, y: kind.pxH - 38, width: 78, height: 7), xRadius: 2, yRadius: 2).fill()
    // TYPE badge pill — obvious what it is
    if let label = kind.label {
        let bw = CGFloat(label.count) * 6.6 + 16, bx = kind.pxW - bw - 10, by = kind.pxH - 27
        tint.setFill(); NSBezierPath(roundedRect: NSRect(x: bx, y: by, width: bw, height: 17), xRadius: 8.5, yRadius: 8.5).fill()
        let bp = NSMutableParagraphStyle(); bp.alignment = .center
        (label as NSString).draw(in: NSRect(x: bx, y: by + 3, width: bw, height: 13),
            withAttributes: [.font: NSFont.systemFont(ofSize: 9, weight: .black), .foregroundColor: NSColor.white, .paragraphStyle: bp])
    }
    ink.withAlphaComponent(0.14).setFill(); NSBezierPath(rect: NSRect(x: 14, y: kind.pxH - 48, width: kind.pxW - 28, height: 1)).fill()
    (snippet as NSString).draw(in: NSRect(x: 16, y: 10, width: kind.pxW - 30, height: kind.pxH - 60),
        withAttributes: [.font: NSFont.systemFont(ofSize: 11, weight: .medium), .foregroundColor: ink.withAlphaComponent(0.78)])
    ink.withAlphaComponent(0.16).setStroke(); let b = NSBezierPath(roundedRect: rect.insetBy(dx: 0.5, dy: 0.5), xRadius: kind.corner, yRadius: kind.corner); b.lineWidth = 1; b.stroke()
    img.unlockFocus(); return img
}

// A crayon-scribble fill (mirrors LivingDeskCanvas.crayonFillImage) — a hand-drawn "place" on the desk.
func crayonFill(_ color: NSColor, w: CGFloat, h: CGFloat) -> NSImage {
    let px = NSSize(width: max(64, w * 14), height: max(64, h * 14))
    let img = NSImage(size: px); img.lockFocus()
    let c = NSGraphicsContext.current!.cgContext
    let rect = NSRect(origin: .zero, size: px).insetBy(dx: 6, dy: 6)
    color.withAlphaComponent(0.9).setStroke()
    let bp = NSBezierPath(roundedRect: rect, xRadius: 14, yRadius: 14); bp.lineWidth = 5; bp.lineCapStyle = .round; bp.stroke()
    c.setLineWidth(7); c.setLineCap(.round); color.withAlphaComponent(0.34).setStroke()
    var y = rect.minY + 8; var i = 0
    while y < rect.maxY {
        let jA = CGFloat((i * 37) % 11) - 5, jB = CGFloat((i * 53) % 13) - 6
        c.move(to: CGPoint(x: rect.minX + 6 + jA, y: y))
        c.addCurve(to: CGPoint(x: rect.maxX - 6 + jB, y: y + 3),
                   control1: CGPoint(x: rect.midX, y: y - 7), control2: CGPoint(x: rect.midX, y: y + 9))
        c.strokePath(); y += 12; i += 1
    }
    img.unlockFocus(); return img
}
// A zone placard with a live count (mirrors LivingDeskCanvas.labelImage).
func zoneLabel(_ text: String, _ accent: NSColor) -> NSImage {
    let size = NSSize(width: 380, height: 96); let img = NSImage(size: size); img.lockFocus()
    let rect = NSRect(origin: .zero, size: size)
    NSColor(calibratedWhite: 0.10, alpha: 0.94).setFill(); NSBezierPath(roundedRect: rect, xRadius: 20, yRadius: 20).fill()
    accent.setFill(); NSBezierPath(rect: NSRect(x: 0, y: 0, width: 9, height: size.height)).fill()
    let p = NSMutableParagraphStyle(); p.alignment = .center
    (text as NSString).draw(in: rect.insetBy(dx: 18, dy: 22),
        withAttributes: [.font: NSFont.systemFont(ofSize: 42, weight: .heavy), .foregroundColor: NSColor.white, .paragraphStyle: p])
    img.unlockFocus(); return img
}
// A drawn ZONE — a crayon footprint + a named count placard. The thing that gives a place meaning.
func zone(_ name: String, count: Int, _ accent: NSColor, cx: Float, cz: Float, hw: Float, hl: Float) -> SCNNode {
    let holder = SCNNode(); holder.position = SCNVector3(cx, 0, cz)
    let plane = SCNPlane(width: CGFloat(hw * 2), height: CGFloat(hl * 2))
    let m = SCNMaterial(); m.lightingModel = .constant; m.isDoubleSided = true
    m.diffuse.contents = crayonFill(accent, w: CGFloat(hw * 2), h: CGFloat(hl * 2))
    plane.materials = [m]
    let pnode = SCNNode(geometry: plane); pnode.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)
    pnode.position = SCNVector3(0, 0.53, 0); holder.addChildNode(pnode)   // just above the mat (top 0.5)
    let lplane = SCNPlane(width: 13, height: 3.4)
    let lm = SCNMaterial(); lm.lightingModel = .constant; lm.isDoubleSided = true; lm.diffuse.contents = zoneLabel("\(name)   ·   \(count)", accent)
    lplane.materials = [lm]
    let lnode = SCNNode(geometry: lplane); lnode.eulerAngles = SCNVector3(-Float.pi / 2, 0, 0)
    lnode.position = SCNVector3(0, 0.60, -hl + 2.2); holder.addChildNode(lnode)
    return holder
}

// ─────────────────────────────────────────────────────────────────────────────────────────────────
// HSM-14-22 the OBJECT LANGUAGE: hardware/containers are REAL 3D things, not chips with text on them.
// A meeting is a cassette (a recording), a model a glowing cartridge, a KB a crystal, a notebook a book.
// Only actual documents (summary/transcript/action) stay paper. Composed here first, then ported.
// ─────────────────────────────────────────────────────────────────────────────────────────────────

func objLabel(_ text: String, ink: NSColor, bg: NSColor) -> NSImage {
    let size = NSSize(width: 256, height: 64); let img = NSImage(size: size); img.lockFocus()
    bg.setFill(); NSBezierPath(roundedRect: NSRect(origin: .zero, size: size), xRadius: 8, yRadius: 8).fill()
    let p = NSMutableParagraphStyle(); p.alignment = .left; p.lineBreakMode = .byTruncatingTail
    (text as NSString).draw(in: NSRect(x: 12, y: 16, width: 232, height: 34),
        withAttributes: [.font: NSFont.systemFont(ofSize: 28, weight: .heavy), .foregroundColor: ink, .paragraphStyle: p])
    img.unlockFocus(); return img
}
func pbr(_ c: NSColor, rough: CGFloat, metal: CGFloat, emit: NSColor? = nil) -> SCNMaterial {
    let m = SCNMaterial(); m.lightingModel = .physicallyBased
    m.diffuse.contents = c; m.roughness.contents = rough; m.metalness.contents = metal
    if let e = emit { m.emission.contents = e }
    return m
}
func node(_ g: SCNGeometry, _ mat: SCNMaterial, _ x: Float, _ y: Float, _ z: Float) -> SCNNode {
    g.materials = [mat]; let n = SCNNode(geometry: g); n.position = SCNVector3(x, y, z); return n
}
func place(_ holder: SCNNode, _ x: Float, _ z: Float, _ rot: Float) -> SCNNode {
    holder.position = SCNVector3(x, 0.5, z); holder.eulerAngles = SCNVector3(0, rot, 0)
    holder.enumerateHierarchy { n, _ in n.castsShadow = true }
    return holder
}

// A MEETING — a cassette tape lying on the desk: dark body, a tinted title label, a window, two reels.
func makeCassette(_ tint: NSColor, _ title: String, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let h = SCNNode()
    h.addChildNode(node(SCNBox(width: 9, height: 1.0, length: 5.6, chamferRadius: 0.35), pbr(NSColor(white: 0.13, alpha: 1), rough: 0.5, metal: 0), 0, 0.5, 0))
    let labelBg = tint.blended(withFraction: 0.55, of: .white) ?? tint
    h.addChildNode(node(SCNBox(width: 8.2, height: 0.1, length: 1.9, chamferRadius: 0.08),
        { let m = SCNMaterial(); m.lightingModel = .blinn; m.diffuse.contents = objLabel(title, ink: NSColor(white: 0.12, alpha: 1), bg: labelBg); return m }(), 0, 1.03, -1.45))
    h.addChildNode(node(SCNBox(width: 5.4, height: 0.08, length: 1.8, chamferRadius: 0.15), pbr(NSColor(white: 0.04, alpha: 1), rough: 0.3, metal: 0), 0, 1.02, 1.1))   // window
    for dx in [Float(-1.45), 1.45] {
        h.addChildNode(node(SCNCylinder(radius: 0.8, height: 0.16), pbr(NSColor(white: 0.72, alpha: 1), rough: 0.6, metal: 0), dx, 1.08, 1.1))
        h.addChildNode(node(SCNCylinder(radius: 0.3, height: 0.2), pbr(tint, rough: 0.4, metal: 0.1), dx, 1.1, 1.1))   // hub
    }
    return place(h, x, z, rot)
}

// A MODEL — a glowing cartridge: glossy dark slab, an emissive accent bar (loaded/alive), a name plate,
// gold contact pins. The owner singled models out — this is the premium object.
func makeCartridge(_ tint: NSColor, _ name: String, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let h = SCNNode()
    h.addChildNode(node(SCNBox(width: 7.6, height: 1.5, length: 5.4, chamferRadius: 0.55), pbr(NSColor(white: 0.10, alpha: 1), rough: 0.22, metal: 0.6), 0, 0.75, 0))
    h.addChildNode(node(SCNBox(width: 6.6, height: 0.14, length: 0.72, chamferRadius: 0.06), pbr(tint, rough: 0.3, metal: 0, emit: tint), 0, 1.52, -1.7))   // GLOW bar
    h.addChildNode(node(SCNBox(width: 6.6, height: 0.1, length: 2.7, chamferRadius: 0.1),
        { let m = SCNMaterial(); m.lightingModel = .blinn; m.diffuse.contents = objLabel(name, ink: .white, bg: NSColor(white: 0.17, alpha: 1)); return m }(), 0, 1.52, 0.2))
    h.addChildNode(node(SCNBox(width: 6.0, height: 0.34, length: 0.5, chamferRadius: 0.05), pbr(NSColor(red: 0.85, green: 0.68, blue: 0.25, alpha: 1), rough: 0.3, metal: 0.9), 0, 0.5, 2.6))   // gold pins
    return place(h, x, z, rot)
}

// A KNOWLEDGE BASE — a faceted crystal (a bipyramid gem) with an inner glow.
func makeCrystal(_ tint: NSColor, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let h = SCNNode()
    let m = pbr(tint, rough: 0.05, metal: 0.1, emit: tint.withAlphaComponent(0.35))
    h.addChildNode(node(SCNPyramid(width: 3.0, height: 3.6, length: 3.0), m, 0, 1.4, 0))           // top
    let bn = node(SCNPyramid(width: 3.0, height: 1.4, length: 3.0), m, 0, 1.4, 0); bn.eulerAngles = SCNVector3(Float.pi, 0, 0); h.addChildNode(bn)   // bottom point
    return place(h, x, z, rot)
}

// A NOTEBOOK — a closed book: cream pages between a tinted cover, a darker spine.
func makeBook(_ tint: NSColor, _ title: String, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let h = SCNNode()
    h.addChildNode(node(SCNBox(width: 8.2, height: 1.2, length: 5.8, chamferRadius: 0.18), pbr(tint.blended(withFraction: 0.25, of: .black) ?? tint, rough: 0.55, metal: 0), 0, 0.6, 0))   // cover
    h.addChildNode(node(SCNBox(width: 7.5, height: 1.0, length: 5.1, chamferRadius: 0.05), pbr(NSColor(red: 0.93, green: 0.90, blue: 0.83, alpha: 1), rough: 0.85, metal: 0), 0.2, 0.65, 0))   // pages
    h.addChildNode(node(SCNBox(width: 0.5, height: 1.28, length: 5.8, chamferRadius: 0.08), pbr(tint, rough: 0.5, metal: 0), -3.85, 0.62, 0))   // spine
    return place(h, x, z, rot)
}

func card(_ tint: NSColor, _ kind: CardKind, snippet: String, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let scale: CGFloat = 8.8 / 246                              // px -> world units
    let w = kind.pxW * scale, h = kind.pxH * scale, thick: CGFloat = 0.22
    let r = w * kind.corner / kind.pxW
    let g = SCNShape(path: NSBezierPath(roundedRect: NSRect(x: -w/2, y: -h/2, width: w, height: h), xRadius: r, yRadius: r), extrusionDepth: thick)
    let front = SCNMaterial(); front.diffuse.contents = cardImage(tint, kind, snippet: snippet); front.roughness.contents = 0.5
    let edge = SCNMaterial(); edge.diffuse.contents = NSColor(calibratedWhite: 0.1, alpha: 1)
    g.materials = [front, edge, edge]
    let n = SCNNode(geometry: g); n.castsShadow = true
    n.eulerAngles = SCNVector3(-Float.pi / 2, rot, 0); n.position = SCNVector3(x, 0.62, z)
    return n
}

// Load a real CC0 model (OBJ+MTL+texture), AUTO-FIT it to a target width, sit its base on the mat.
// For a single merged mesh (trimesh force='mesh') the geometry boundingBox is exact, so this is reliable.
func loadFit(_ name: String, _ targetW: CGFloat, _ x: CGFloat, _ z: CGFloat, rotY: CGFloat = 0) -> SCNNode? {
    let url = URL(fileURLWithPath: "/tmp/propobj/\(name)/\(name).obj")
    guard let sc = try? SCNScene(url: url, options: nil) else { return nil }
    let group = SCNNode(); for c in sc.rootNode.childNodes { group.addChildNode(c) }
    // apply the palette texture from the obj dir (material_0.png / Atlas.png) — SCNScene(url:obj) doesn't always
    let texPath = ["material_0.png", "Atlas.png"].map { "/tmp/propobj/\(name)/\($0)" }.first { FileManager.default.fileExists(atPath: $0) }
    if let tp = texPath, let tex = NSImage(contentsOfFile: tp) {
        group.enumerateHierarchy { n, _ in n.geometry?.materials.forEach { $0.diffuse.contents = tex; $0.diffuse.wrapS = .clamp; $0.diffuse.wrapT = .clamp } }
    }
    var mn = SCNVector3(1e9, 1e9, 1e9), mx = SCNVector3(-1e9, -1e9, -1e9)
    group.enumerateHierarchy { n, _ in if let g = n.geometry { let b = g.boundingBox
        mn.x = min(mn.x, b.min.x); mn.y = min(mn.y, b.min.y); mn.z = min(mn.z, b.min.z)
        mx.x = max(mx.x, b.max.x); mx.y = max(mx.y, b.max.y); mx.z = max(mx.z, b.max.z) } }
    let s = targetW / max(0.001, max(mx.x - mn.x, mx.z - mn.z))   // fit by the largest horizontal span
    group.scale = SCNVector3(s, s, s); group.eulerAngles = SCNVector3(0, rotY, 0)
    let holder = SCNNode(); holder.addChildNode(group)
    holder.position = SCNVector3(x, -mn.y * s + 0.5, z)
    holder.enumerateHierarchy { n, _ in n.castsShadow = true }
    return holder
}

// Load a poly.pizza prop (OBJ + MTL + texture), keep its colours, scale to a target height, sit it on
// the desk top, cast shadows.
func loadProp(_ name: String, scale s: Float, _ x: Float, _ z: Float, rotY: Float = 0) -> SCNNode? {
    let url = URL(fileURLWithPath: "/tmp/propobj/\(name)/\(name).obj")
    guard let scene = try? SCNScene(url: url, options: nil) else { return nil }
    let group = SCNNode(); for c in scene.rootNode.childNodes { group.addChildNode(c) }
    var mn = SCNVector3Zero, mx = SCNVector3Zero
    group.enumerateHierarchy { n, _ in if let g = n.geometry { let bb = g.boundingBox; mn = bb.min; mx = bb.max } }
    let holder = SCNNode(); holder.addChildNode(group)
    group.scale = SCNVector3(s, s, s)
    group.eulerAngles = SCNVector3(0, rotY, 0)
    holder.position = SCNVector3(x, -Float(mn.y) * s + 0.02, z)   // sit the base on the desk
    holder.enumerateHierarchy { n, _ in n.castsShadow = true }
    return holder
}

func buildScene() -> SCNScene {
    let scene = SCNScene()
    scene.background.contents = NSColor(calibratedWhite: 0.05, alpha: 1)
    scene.lightingEnvironment.contents = NSColor(calibratedWhite: 0.72, alpha: 1)
    scene.lightingEnvironment.intensity = 1.25

    // Camera — pulled BACK to frame the whole workspace, with atmosphere (AO + depth of field + bloom).
    let camNode = SCNNode()
    let cam = SCNCamera(); cam.fieldOfView = 38; cam.zNear = 0.2; cam.zFar = 600
    cam.screenSpaceAmbientOcclusionIntensity = 1.6; cam.screenSpaceAmbientOcclusionRadius = 3.5
    cam.screenSpaceAmbientOcclusionBias = 0.08
    cam.wantsDepthOfField = true; cam.focusDistance = 46; cam.fStop = 0.4; cam.focalLength = 30
    cam.bloomIntensity = 0.45; cam.bloomThreshold = 0.9; cam.bloomBlurRadius = 10
    camNode.camera = cam; camNode.position = SCNVector3(0, 44, 34)
    camNode.eulerAngles = SCNVector3(-60.0 * .pi / 180.0, 0, 0)
    scene.rootNode.addChildNode(camNode)

    // Desk — light marble (blinn, even + predictable).
    let desk = SCNBox(width: 70, height: 1, length: 52, chamferRadius: 0.5)
    let dm = SCNMaterial(); dm.lightingModel = .blinn
    dm.diffuse.contents = NSColor(calibratedRed: 0.85, green: 0.83, blue: 0.79, alpha: 1)
    dm.specular.contents = NSColor(calibratedWhite: 0.5, alpha: 1); dm.shininess = 0.3
    desk.materials = [dm]
    let dnode = SCNNode(geometry: desk); dnode.position = SCNVector3(0, -0.5, 0); scene.rootNode.addChildNode(dnode)

    // A leather desk mat — the work surface the cards sit on (grounds the scene). Matches the app's mat
    // (centre y=0.25, height 0.5 -> top at 0.5) so zone/card heights tuned here port 1:1.
    let pad = SCNBox(width: 42, height: 0.5, length: 26, chamferRadius: 1.6)
    let pm = SCNMaterial(); pm.lightingModel = .blinn
    pm.diffuse.contents = NSColor(calibratedRed: 0.14, green: 0.12, blue: 0.11, alpha: 1)
    pm.specular.contents = NSColor(calibratedWhite: 0.18, alpha: 1)
    pad.materials = [pm]
    let padNode = SCNNode(geometry: pad); padNode.position = SCNVector3(0, 0.25, 3); scene.rootNode.addChildNode(padNode)

    // Key light — the main shadow caster, covering the whole desk so every object casts a shadow.
    let key = SCNNode(); let kl = SCNLight(); kl.type = .directional; kl.intensity = 680
    kl.color = NSColor(calibratedWhite: 1, alpha: 1)
    kl.castsShadow = true; kl.shadowSampleCount = 16
    kl.shadowRadius = 4; kl.shadowColor = NSColor(calibratedWhite: 0, alpha: 0.4)
    key.position = SCNVector3(10, 40, 20)
    key.eulerAngles = SCNVector3(-1.05, 0.4, 0); scene.rootNode.addChildNode(key)

    // Warm lamp pool (no shadow — the key owns shadows; this is the warm tint).
    let spot = SCNNode(); let sl = SCNLight(); sl.type = .spot
    sl.color = NSColor(calibratedRed: 1.0, green: 0.86, blue: 0.66, alpha: 1); sl.intensity = 1700
    sl.spotInnerAngle = 26; sl.spotOuterAngle = 66; sl.attenuationEndDistance = 70
    spot.light = sl; spot.position = SCNVector3(-17, 13, -7); spot.look(at: SCNVector3(-6, 0, 2))
    scene.rootNode.addChildNode(spot)

    let amb = SCNNode(); let al = SCNLight(); al.type = .ambient; al.intensity = 260
    al.color = NSColor(calibratedWhite: 0.5, alpha: 1); amb.light = al; scene.rootNode.addChildNode(amb)

    // Props — real poly.pizza CC0 models arranged around the work area.
    // Explicit per-prop scales (auto-fit is unreliable — these models have wildly different native sizes).
    let props: [(String, Float, Float, Float, Float)] = [
        ("lightdesk",  17,   -22, -10, 0.5),
        ("plant",       4.0,  22, -10, 0),
        ("books",       5.5, -20,  6, 0.3),
        ("mug",        26,    19,  8, 0),
        ("keyboard",    0.035, 0, -6, 3.14),
    ]
    for (n, s, x, z, ry) in props {
        if let p = loadProp(n, scale: s, x, z, rotY: ry) { scene.rootNode.addChildNode(p) }
    }

    // Meeting cards — in the front-center work area.
    let tints = [NSColor(calibratedRed: 0.36, green: 0.55, blue: 0.94, alpha: 1),
                 NSColor(calibratedRed: 1.0, green: 0.42, blue: 0.21, alpha: 1),
                 NSColor(calibratedRed: 0.24, green: 0.81, blue: 0.56, alpha: 1),
                 NSColor(calibratedRed: 0.95, green: 0.64, blue: 0.24, alpha: 1)]
    // HSM-14-22 card craft (owner feedback): cards now come in DIFFERENT SHAPES + SIZES, are obviously
    // TYPED (a tinted badge), carry a real CONTENT snippet, and the sticker is LOOSE (each a different
    // angle / size / shape / nudge). One of each kind, spread on the desk.
    let green  = NSColor(calibratedRed: 0.24, green: 0.81, blue: 0.56, alpha: 1)
    let purple = NSColor(calibratedRed: 0.61, green: 0.55, blue: 1.00, alpha: 1)
    let orange = NSColor(calibratedRed: 0.95, green: 0.64, blue: 0.24, alpha: 1)
    let blue   = NSColor(calibratedRed: 0.36, green: 0.62, blue: 0.95, alpha: 1)
    let cobalt = NSColor(calibratedRed: 0.36, green: 0.55, blue: 0.94, alpha: 1)
    // The OBJECT LANGUAGE (procedural for now — raw CC0 low-poly came in untextured/rough; curation is a
    // separate art pass): meetings = cassettes, model = a glowing cartridge, KB = a crystal, notebook = a book.
    scene.rootNode.addChildNode(makeCassette(cobalt, "Weekly Sync", -12, -3, rot: -0.06))
    scene.rootNode.addChildNode(makeCassette(orange, "1:1 · Priya",  -12, 6, rot: 0.05))
    scene.rootNode.addChildNode(makeCartridge(green, "Qwen3-4B", 1, -4, rot: 0.04))
    scene.rootNode.addChildNode(makeCrystal(purple, 13, -3, rot: 0.3))
    scene.rootNode.addChildNode(makeBook(blue, "Atlas", 12, 8, rot: -0.12))
    // documents stay paper — what a meeting spills into
    let summary = CardKind(label: "SUMMARY", corner: 15, pxW: 248, pxH: 112, seed: 3)
    let action  = CardKind(label: "ACTION",  corner: 9,  pxW: 196, pxH: 70,  seed: 12)
    scene.rootNode.addChildNode(card(green,  summary, snippet: "Team aligned on shipping the beta Friday; pricing deferred a week pending finance sign-off.", -1, 9, rot: 0.03))
    scene.rootNode.addChildNode(card(orange, action,  snippet: "Send the finance deck to Priya by EOD.", -10, 12, rot: 0.1))
    return scene
}

// "faces" mode — write a flat contact sheet of the card FACES on a light bg, so the badge / snippet /
// loose sticker can be judged at full clarity (the 3D snapshot path renders dark).
if CommandLine.arguments.count > 2, CommandLine.arguments[2] == "faces" {
    let green = NSColor(calibratedRed:0.24,green:0.81,blue:0.56,alpha:1), purple = NSColor(calibratedRed:0.61,green:0.55,blue:1,alpha:1)
    let orange = NSColor(calibratedRed:0.95,green:0.64,blue:0.24,alpha:1), blue = NSColor(calibratedRed:0.36,green:0.62,blue:0.95,alpha:1)
    let cobalt = NSColor(calibratedRed:0.36,green:0.55,blue:0.94,alpha:1)
    let faces: [(NSColor, CardKind, String)] = [
        (green,  CardKind(label:"SUMMARY",    corner:15, pxW:266, pxH:124, seed:3),  "The team aligned on shipping the beta Friday; pricing deferred a week pending finance sign-off."),
        (blue,   CardKind(label:"TOPICS",     corner:15, pxW:232, pxH:98,  seed:5),  "Topics — pricing, beta timeline, export tab, finance sign-off"),
        (purple, CardKind(label:"TRANSCRIPT", corner:9,  pxW:198, pxH:150, seed:7),  "Alex: can we cut scope?  Jordan: only if we drop the export tab.  Alex: fine, ship it Friday."),
        (orange, CardKind(label:"ACTION",     corner:9,  pxW:200, pxH:72,  seed:12), "Send the finance deck to Priya by EOD."),
        (cobalt, CardKind(label:nil,          corner:15, pxW:248, pxH:106, seed:9),  "Weekly sync · 32 min · 3 speakers. Tap to open the full meeting."),
    ]
    let sheet = NSImage(size: NSSize(width: 600, height: 700)); sheet.lockFocus()
    NSColor(calibratedWhite: 0.16, alpha: 1).setFill(); NSBezierPath(rect: NSRect(x:0,y:0,width:600,height:700)).fill()
    var y: CGFloat = 700
    for (tint, kind, snip) in faces {
        let im = cardImage(tint, kind, snippet: snip); y -= kind.pxH + 22
        im.draw(in: NSRect(x: 30, y: y, width: kind.pxW, height: kind.pxH))
    }
    sheet.unlockFocus()
    if let tiff = sheet.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff), let png = rep.representation(using: .png, properties: [:]) {
        try? png.write(to: URL(fileURLWithPath: CommandLine.arguments[1])); print("wrote faces \(CommandLine.arguments[1])")
    }
    exit(0)
}

guard let device = MTLCreateSystemDefaultDevice() else { FileHandle.standardError.write("no metal\n".data(using: .utf8)!); exit(1) }
let renderer = SCNRenderer(device: device, options: nil)
let scene = buildScene(); renderer.scene = scene
renderer.pointOfView = scene.rootNode.childNodes.first { $0.camera != nil }
let image = renderer.snapshot(atTime: 0, with: CGSize(width: 1500, height: 1050), antialiasingMode: .multisampling4X)
let outPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "/tmp/living-desk.png"
if let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff), let png = rep.representation(using: .png, properties: [:]) {
    try? png.write(to: URL(fileURLWithPath: outPath)); print("wrote \(outPath)")
} else { FileHandle.standardError.write("encode failed\n".data(using: .utf8)!); exit(1) }
