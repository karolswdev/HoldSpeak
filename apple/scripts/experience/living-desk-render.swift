// HSM-14-22 — offscreen SceneKit render of the Living Desk, populated. A lit material desk with REAL
// poly.pizza CC0 props (lamp, plant, laptop, keyboard, mug, books, pencil) arranged around the work
// area, a directional shadow light so everything casts shadows, and rounded-rect meeting cards in front.
// Build: swiftc -O living-desk-render.swift -o /tmp/ldr -framework SceneKit -framework AppKit -framework Metal
// Run:   /tmp/ldr /tmp/living-desk.png   (props loaded from /tmp/propobj/<name>/<name>.obj)

import Foundation
import SceneKit
import AppKit

func cardImage(_ tint: NSColor) -> NSImage {
    let size = NSSize(width: 246, height: 78); let img = NSImage(size: size); img.lockFocus()
    let rect = NSRect(origin: .zero, size: size)
    let clip = NSBezierPath(roundedRect: rect, xRadius: 15, yRadius: 15); clip.addClip()
    if let paper = NSImage(contentsOfFile: "../../App/paper.png") { paper.draw(in: rect) }
    else { NSColor(calibratedRed: 0.93, green: 0.90, blue: 0.84, alpha: 1).setFill(); NSBezierPath(rect: rect).fill() }
    tint.withAlphaComponent(0.10).setFill(); NSBezierPath(rect: rect).fill()
    tint.setFill(); NSBezierPath(rect: NSRect(x: 0, y: 0, width: 6, height: 78)).fill()        // accent spine
    // die-cut sticker (white tile, tilted, colored outline)
    let ctx = NSGraphicsContext.current!.cgContext
    ctx.saveGState(); ctx.translateBy(x: 40, y: 39); ctx.rotate(by: -0.12)
    let sq = NSRect(x: -17, y: -17, width: 34, height: 34)
    ctx.setShadow(offset: CGSize(width: 1.5, height: -1.5), blur: 3, color: NSColor(white: 0, alpha: 0.3).cgColor)
    NSColor.white.setFill(); NSBezierPath(roundedRect: sq, xRadius: 8, yRadius: 8).fill()
    ctx.setShadow(offset: .zero, blur: 0, color: nil)
    tint.setStroke(); let sp = NSBezierPath(roundedRect: sq, xRadius: 8, yRadius: 8); sp.lineWidth = 2; sp.stroke()
    ctx.restoreGState()
    let ink = NSColor(calibratedRed: 0.16, green: 0.13, blue: 0.09, alpha: 1)
    ink.setFill(); NSBezierPath(roundedRect: NSRect(x: 66, y: 46, width: 136, height: 11), xRadius: 3, yRadius: 3).fill()
    ink.withAlphaComponent(0.14).setFill(); NSBezierPath(rect: NSRect(x: 66, y: 40, width: 150, height: 1)).fill()
    ink.withAlphaComponent(0.5).setFill(); NSBezierPath(roundedRect: NSRect(x: 66, y: 24, width: 98, height: 8), xRadius: 2, yRadius: 2).fill()
    ink.withAlphaComponent(0.16).setStroke(); let b = NSBezierPath(roundedRect: rect.insetBy(dx: 0.5, dy: 0.5), xRadius: 15, yRadius: 15); b.lineWidth = 1; b.stroke()
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

func card(_ tint: NSColor, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let w: CGFloat = 8.8, h: CGFloat = 2.8, r: CGFloat = 0.6, thick: CGFloat = 0.22
    let g = SCNShape(path: NSBezierPath(roundedRect: NSRect(x: -w/2, y: -h/2, width: w, height: h), xRadius: r, yRadius: r), extrusionDepth: thick)
    let front = SCNMaterial(); front.diffuse.contents = cardImage(tint); front.roughness.contents = 0.5
    let edge = SCNMaterial(); edge.diffuse.contents = NSColor(calibratedWhite: 0.1, alpha: 1)
    g.materials = [front, edge, edge]
    let n = SCNNode(geometry: g); n.castsShadow = true
    n.eulerAngles = SCNVector3(-Float.pi / 2, rot, 0); n.position = SCNVector3(x, 0.62, z)  // rest on the mat, above zone decals
    return n
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
    // A drawn ZONE — "Project Atlas" — with three meeting cards filed INSIDE it (the point of the leap:
    // a place that holds things), plus a couple of loose cards outside to read the contrast.
    let accent = NSColor(calibratedRed: 0.95, green: 0.43, blue: 0.30, alpha: 1)
    scene.rootNode.addChildNode(zone("Project Atlas", count: 3, accent, cx: -6, cz: 4, hw: 12, hl: 9))
    let inside: [(Float, Float, Float)] = [(-12, 0, -0.06), (-1, -1, 0.05), (-9, 7, 0.12)]
    for (i, sp) in inside.enumerated() { scene.rootNode.addChildNode(card(tints[i % 4], sp.0, sp.1, rot: sp.2)) }
    // loose cards, not yet filed into any place
    scene.rootNode.addChildNode(card(tints[1], 14, 0, rot: -0.1))
    scene.rootNode.addChildNode(card(tints[3], 16, 9, rot: 0.08))
    return scene
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
