// HSM-14-22 — offscreen SceneKit render of the Living Desk, so the fixed-angle 3D substrate can be
// SEEN + iterated on macOS before it touches the iPad (the Simulator build is blocked). Renders a
// perspective desk: lit material surface, cards laid flat, one lifted (picked), a small stack.
// Build: swiftc -O living-desk-render.swift -o /tmp/ldr -framework SceneKit -framework AppKit -framework Metal
// Run:   /tmp/ldr /tmp/living-desk.png

import Foundation
import SceneKit
import AppKit

func cardImage(_ tint: NSColor, title: String) -> NSImage {
    let size = NSSize(width: 246, height: 78)
    let img = NSImage(size: size)
    img.lockFocus()
    let bg = NSBezierPath(roundedRect: NSRect(origin: .zero, size: size), xRadius: 16, yRadius: 16)
    NSColor(calibratedWhite: 0.135, alpha: 1).setFill(); bg.fill()
    tint.setFill(); NSBezierPath(roundedRect: NSRect(x: 10, y: 15, width: 5, height: 48), xRadius: 2.5, yRadius: 2.5).fill()
    NSColor(calibratedWhite: 0.88, alpha: 1).setFill(); NSBezierPath(roundedRect: NSRect(x: 26, y: 44, width: 150, height: 14), xRadius: 4, yRadius: 4).fill()
    NSColor(calibratedWhite: 0.42, alpha: 1).setFill(); NSBezierPath(roundedRect: NSRect(x: 26, y: 24, width: 112, height: 10), xRadius: 3, yRadius: 3).fill()
    img.unlockFocus()
    return img
}

func card(_ tint: NSColor, _ x: Float, _ z: Float, y: Float = 0.30, rot: Float = 0) -> SCNNode {
    // An extruded rounded-rect so the card SILHOUETTE follows the face model (not a plain box).
    let w: CGFloat = 8.8, h: CGFloat = 2.8, r: CGFloat = 0.6, thick: CGFloat = 0.22
    let path = NSBezierPath(roundedRect: NSRect(x: -w/2, y: -h/2, width: w, height: h), xRadius: r, yRadius: r)
    let g = SCNShape(path: path, extrusionDepth: thick)
    let front = SCNMaterial(); front.diffuse.contents = cardImage(tint, title: ""); front.roughness.contents = 0.5
    let edge = SCNMaterial(); edge.diffuse.contents = NSColor(calibratedWhite: 0.10, alpha: 1); edge.roughness.contents = 0.7
    g.materials = [front, edge, edge]                 // SCNShape: [front, back, sides]
    let n = SCNNode(geometry: g)
    // Lay flat, face up: rotate -90deg about X, then spin so the title reads toward the viewer.
    n.eulerAngles = SCNVector3(-Float.pi / 2, Float.pi + rot, 0)
    n.position = SCNVector3(x, y, z)
    return n
}

func buildScene() -> SCNScene {
    let scene = SCNScene()
    scene.background.contents = NSColor(calibratedWhite: 0.045, alpha: 1)
    // Image-based fill so PBR materials read light + even (an ambient light alone leaves PBR dark).
    scene.lightingEnvironment.contents = NSColor(calibratedRed: 0.74, green: 0.75, blue: 0.78, alpha: 1)
    scene.lightingEnvironment.intensity = 1.5

    // Camera — fixed ~82deg looking down at the desk (90 = top-down; 82 = tilted 8deg toward the viewer).
    let camNode = SCNNode()
    let cam = SCNCamera(); cam.fieldOfView = 38; cam.zNear = 0.1; cam.zFar = 400
    camNode.camera = cam
    camNode.position = SCNVector3(0, 32, 11)
    camNode.eulerAngles = SCNVector3(-82.0 * .pi / 180.0, 0, 0)
    scene.rootNode.addChildNode(camNode)

    // Desk — polished MARBLE (the "Marble & Lamp" environment): light, warm, low-roughness so the lamp
    // pools a visible warm highlight and cards cast readable soft shadows.
    let desk = SCNBox(width: 66, height: 1, length: 48, chamferRadius: 0.5)
    let dm = SCNMaterial()
    dm.lightingModel = .blinn
    dm.diffuse.contents = NSColor(calibratedRed: 0.88, green: 0.86, blue: 0.82, alpha: 1)
    dm.specular.contents = NSColor(calibratedWhite: 0.55, alpha: 1); dm.shininess = 0.25
    desk.materials = [dm]
    let deskNode = SCNNode(geometry: desk); deskNode.position = SCNVector3(0, -0.5, 0)
    scene.rootNode.addChildNode(deskNode)

    // Leather mousepad — a soft dark mat the cards sit on (the owner's exemplar detail).
    let pad = SCNBox(width: 30, height: 0.3, length: 18, chamferRadius: 1.4)
    let pm = SCNMaterial()
    pm.diffuse.contents = NSColor(calibratedRed: 0.18, green: 0.14, blue: 0.12, alpha: 1)
    pm.roughness.contents = 0.92
    pad.materials = [pm]
    let padNode = SCNNode(geometry: pad); padNode.position = SCNVector3(-2, 0.12, 0.5)
    scene.rootNode.addChildNode(padNode)

    // The lamp is a REAL 3D MODEL (poly.pizza CC0 "Light Desk" by Quaternius) standing on the marble,
    // and the light emanates from its head — not a faked gradient.
    if let lampModel = try? SCNScene(url: URL(fileURLWithPath: "assets/models/lightdesk.obj"), options: nil) {
        let lm = SCNNode()
        for c in lampModel.rootNode.childNodes { lm.addChildNode(c) }
        let mat = SCNMaterial(); mat.lightingModel = .blinn
        mat.diffuse.contents = NSColor(calibratedWhite: 0.16, alpha: 1)
        mat.specular.contents = NSColor(calibratedWhite: 0.55, alpha: 1); mat.shininess = 0.4
        lm.enumerateHierarchy { n, _ in n.geometry?.materials = [mat] }
        lm.scale = SCNVector3(17, 17, 17)
        lm.position = SCNVector3(-13, 0, -3)
        lm.eulerAngles = SCNVector3(0, 0.7, 0)
        scene.rootNode.addChildNode(lm)
    }

    // The desk-lamp's throw — a warm spot originating at the lamp head, casting real soft shadows.
    let lampNode = SCNNode()
    let lamp = SCNLight(); lamp.type = .spot
    lamp.color = NSColor(calibratedRed: 1.0, green: 0.88, blue: 0.72, alpha: 1)
    lamp.intensity = 1900
    lamp.spotInnerAngle = 30; lamp.spotOuterAngle = 80
    lamp.attenuationStartDistance = 6; lamp.attenuationEndDistance = 60
    lamp.castsShadow = true; lamp.shadowMode = .forward; lamp.shadowSampleCount = 32
    lamp.shadowRadius = 8; lamp.shadowColor = NSColor(calibratedWhite: 0, alpha: 0.34)
    lampNode.light = lamp; lampNode.position = SCNVector3(-11, 8.5, -2)
    lampNode.look(at: SCNVector3(-3, 0, 2))
    scene.rootNode.addChildNode(lampNode)

    // A strong near-top-down key so the whole marble reads evenly bright (predictable, device-like).
    let keyNode = SCNNode(); let key = SCNLight()
    key.type = .directional; key.intensity = 750; key.color = NSColor(calibratedWhite: 1.0, alpha: 1)
    keyNode.eulerAngles = SCNVector3(-1.32, 0.25, 0); scene.rootNode.addChildNode(keyNode)

    // A soft cool fill from the right so the dark side of objects keeps shape.
    let fillNode = SCNNode(); let fill = SCNLight()
    fill.type = .directional; fill.intensity = 300; fill.color = NSColor(calibratedRed: 0.74, green: 0.80, blue: 0.95, alpha: 1)
    fillNode.eulerAngles = SCNVector3(-0.9, 0.7, 0); scene.rootNode.addChildNode(fillNode)

    let ambNode = SCNNode(); let amb = SCNLight()
    amb.type = .ambient; amb.intensity = 750; amb.color = NSColor(calibratedRed: 0.62, green: 0.62, blue: 0.62, alpha: 1)
    ambNode.light = amb; scene.rootNode.addChildNode(ambNode)

    // Cards laid flat in a loose grid + one lifted + a small stack.
    let tints = [NSColor(calibratedRed: 0.36, green: 0.55, blue: 0.94, alpha: 1),
                 NSColor(calibratedRed: 1.0, green: 0.42, blue: 0.21, alpha: 1),
                 NSColor(calibratedRed: 0.24, green: 0.81, blue: 0.56, alpha: 1),
                 NSColor(calibratedRed: 0.95, green: 0.64, blue: 0.24, alpha: 1)]
    var i = 0
    for row in 0..<3 { for col in 0..<4 {
        let x = Float(col) * 11.5 - 17.0, z = Float(row) * 9.5 - 9.0
        let jitterX = Float((i * 37 % 7)) * 0.1 - 0.3
        let rot = Float((i * 53 % 9)) * 0.03 - 0.12
        scene.rootNode.addChildNode(card(tints[i % 4], x + jitterX, z, rot: rot)); i += 1
    }}
    // A lifted (picked-up) card — raised in Y with a larger gap to the desk -> bigger shadow.
    scene.rootNode.addChildNode(card(tints[1], -17.0, 9.0, y: 4.0, rot: -0.16))
    // A small stack.
    scene.rootNode.addChildNode(card(tints[0], 7.0, 0.0, y: 0.55, rot: 0.10))
    scene.rootNode.addChildNode(card(tints[2], 7.5, 0.4, y: 0.95, rot: -0.06))

    return scene
}

guard let device = MTLCreateSystemDefaultDevice() else {
    FileHandle.standardError.write("no metal device\n".data(using: .utf8)!); exit(1)
}
let renderer = SCNRenderer(device: device, options: nil)
let scene = buildScene()
renderer.scene = scene
renderer.pointOfView = scene.rootNode.childNodes.first { $0.camera != nil }
let image = renderer.snapshot(atTime: 0, with: CGSize(width: 1500, height: 1050), antialiasingMode: .multisampling4X)
let outPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "/tmp/living-desk.png"
if let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
   let png = rep.representation(using: .png, properties: [:]) {
    try? png.write(to: URL(fileURLWithPath: outPath)); print("wrote \(outPath)")
} else { FileHandle.standardError.write("encode failed\n".data(using: .utf8)!); exit(1) }
