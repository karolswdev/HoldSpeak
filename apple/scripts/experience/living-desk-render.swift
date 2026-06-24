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
    NSColor(calibratedWhite: 0.135, alpha: 1).setFill()
    NSBezierPath(roundedRect: NSRect(origin: .zero, size: size), xRadius: 16, yRadius: 16).fill()
    tint.setFill(); NSBezierPath(roundedRect: NSRect(x: 10, y: 15, width: 5, height: 48), xRadius: 2.5, yRadius: 2.5).fill()
    NSColor(calibratedWhite: 0.88, alpha: 1).setFill(); NSBezierPath(roundedRect: NSRect(x: 26, y: 44, width: 150, height: 14), xRadius: 4, yRadius: 4).fill()
    NSColor(calibratedWhite: 0.42, alpha: 1).setFill(); NSBezierPath(roundedRect: NSRect(x: 26, y: 24, width: 112, height: 10), xRadius: 3, yRadius: 3).fill()
    img.unlockFocus(); return img
}

func card(_ tint: NSColor, _ x: Float, _ z: Float, rot: Float = 0) -> SCNNode {
    let w: CGFloat = 8.8, h: CGFloat = 2.8, r: CGFloat = 0.6, thick: CGFloat = 0.22
    let g = SCNShape(path: NSBezierPath(roundedRect: NSRect(x: -w/2, y: -h/2, width: w, height: h), xRadius: r, yRadius: r), extrusionDepth: thick)
    let front = SCNMaterial(); front.diffuse.contents = cardImage(tint); front.roughness.contents = 0.5
    let edge = SCNMaterial(); edge.diffuse.contents = NSColor(calibratedWhite: 0.1, alpha: 1)
    g.materials = [front, edge, edge]
    let n = SCNNode(geometry: g); n.castsShadow = true
    n.eulerAngles = SCNVector3(-Float.pi / 2, rot, 0); n.position = SCNVector3(x, 0.22, z)
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

    // Camera — fixed ~82deg.
    let camNode = SCNNode()
    let cam = SCNCamera(); cam.fieldOfView = 40; cam.zNear = 0.1; cam.zFar = 500
    camNode.camera = cam; camNode.position = SCNVector3(0, 32, 12)
    camNode.eulerAngles = SCNVector3(-80.0 * .pi / 180.0, 0, 0)
    scene.rootNode.addChildNode(camNode)

    // Desk — light marble (blinn, even + predictable).
    let desk = SCNBox(width: 70, height: 1, length: 52, chamferRadius: 0.5)
    let dm = SCNMaterial(); dm.lightingModel = .blinn
    dm.diffuse.contents = NSColor(calibratedRed: 0.85, green: 0.83, blue: 0.79, alpha: 1)
    dm.specular.contents = NSColor(calibratedWhite: 0.5, alpha: 1); dm.shininess = 0.3
    desk.materials = [dm]
    let dnode = SCNNode(geometry: desk); dnode.position = SCNVector3(0, -0.5, 0); scene.rootNode.addChildNode(dnode)

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
        ("lightdesk", 16,   -13, -7, 0.6),
        ("plant",      3.2,  13, -7, 0),
        ("books",      5,   -13,  4, 0.3),
        ("mug",       24,    12,  4, 0),
        ("keyboard",   0.03,  0, -6, 3.14),
    ]
    for (n, s, x, z, ry) in props {
        if let p = loadProp(n, scale: s, x, z, rotY: ry) { scene.rootNode.addChildNode(p) }
    }

    // Meeting cards — in the front-center work area.
    let tints = [NSColor(calibratedRed: 0.36, green: 0.55, blue: 0.94, alpha: 1),
                 NSColor(calibratedRed: 1.0, green: 0.42, blue: 0.21, alpha: 1),
                 NSColor(calibratedRed: 0.24, green: 0.81, blue: 0.56, alpha: 1),
                 NSColor(calibratedRed: 0.95, green: 0.64, blue: 0.24, alpha: 1)]
    let spots: [(Float, Float, Float)] = [(-13, -4, -0.08), (-2, -3, 0.06), (9, -4, -0.1),
                                          (-9, 4, 0.04), (3, 5, -0.05), (14, 3, 0.1)]
    for (i, sp) in spots.enumerated() { scene.rootNode.addChildNode(card(tints[i % 4], sp.0, sp.1, rot: sp.2)) }
    // a small stack
    scene.rootNode.addChildNode(card(tints[2], 13, 8, rot: 0.1))
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
