import Foundation
import Providers

/// HSM-14-08 — the Pencil as a diagram language. Strokes, NOT pixels: PencilKit gives us
/// vector geometry, so we recognize shapes deterministically, build a graph, and emit Mermaid
/// — reserving any VLM/LLM for ambiguity only. This file is the pure, host-tested engine:
/// `ShapeRecognizer` (a stroke → a shape or a connector), `DiagramBuilder` (shapes + connectors
/// → a graph), `MermaidGenerator` (graph → `flowchart`). No CoreGraphics, no model, no device.

public struct StrokePoint: Equatable, Sendable {
    public let x: Double, y: Double
    public init(_ x: Double, _ y: Double) { self.x = x; self.y = y }
}

public struct Bounds: Equatable, Sendable {
    public let minX, minY, maxX, maxY: Double
    public var w: Double { maxX - minX }
    public var h: Double { maxY - minY }
    public var cx: Double { (minX + maxX) / 2 }
    public var cy: Double { (minY + maxY) / 2 }
    public var center: StrokePoint { StrokePoint(cx, cy) }
}

public enum ShapeKind: String, Sendable, Equatable { case rectangle, diamond, ellipse }

public enum RecognizedStroke: Equatable, Sendable {
    case shape(ShapeKind, Bounds)
    case connector(from: StrokePoint, to: StrokePoint)
}

// MARK: - Stroke → shape / connector

public enum ShapeRecognizer {

    /// Classify one stroke (a polyline) into a closed shape (rectangle / diamond / ellipse) or
    /// an open connector (an arrow/line, carrying its start + end). Geometry only.
    public static func classify(_ points: [StrokePoint]) -> RecognizedStroke {
        guard let first = points.first, let last = points.last, points.count >= 2 else {
            let p = points.first ?? StrokePoint(0, 0)
            return .connector(from: p, to: p)
        }
        let b = bounds(points)
        let diag = max((b.w * b.w + b.h * b.h).squareRoot(), 1)
        // Closed if the ends meet relative to the size → a node; else a connector.
        guard dist(first, last) < 0.28 * diag else { return .connector(from: first, to: last) }
        let simplified = simplify(points, epsilon: 0.06 * diag)
        return .shape(classifyClosed(simplified, bounds: b), b)
    }

    static func bounds(_ pts: [StrokePoint]) -> Bounds {
        var minX = pts[0].x, minY = pts[0].y, maxX = pts[0].x, maxY = pts[0].y
        for p in pts { minX = min(minX, p.x); minY = min(minY, p.y); maxX = max(maxX, p.x); maxY = max(maxY, p.y) }
        return Bounds(minX: minX, minY: minY, maxX: maxX, maxY: maxY)
    }
    static func dist(_ a: StrokePoint, _ b: StrokePoint) -> Double {
        ((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)).squareRoot()
    }

    /// A closed simplified polygon → its kind. Count the SHARP corners (~>63° turns): ~4 sharp
    /// corners at the bounding-box corners → rectangle; at the edge midpoints → diamond; few
    /// sharp corners (gradual all the way round) → ellipse.
    static func classifyClosed(_ raw: [StrokePoint], bounds b: Bounds) -> ShapeKind {
        var v = raw
        if v.count > 1, v.first == v.last { v.removeLast() }   // drop the closing duplicate
        let n = v.count
        guard n >= 3 else { return .rectangle }
        let thresh = 0.25 * max(b.w, b.h, 1)
        let corners = [StrokePoint(b.minX, b.minY), StrokePoint(b.maxX, b.minY),
                       StrokePoint(b.maxX, b.maxY), StrokePoint(b.minX, b.maxY)]
        let mids = [StrokePoint(b.cx, b.minY), StrokePoint(b.maxX, b.cy),
                    StrokePoint(b.cx, b.maxY), StrokePoint(b.minX, b.cy)]
        var sharp = 0, cornerVotes = 0, midVotes = 0
        for i in 0..<n {
            let a = v[(i - 1 + n) % n], c = v[i], d = v[(i + 1) % n]
            guard turnAngle(a, c, d) > 1.1 else { continue }   // ~63°+
            sharp += 1
            let dc = corners.map { dist($0, c) }.min() ?? .infinity
            let dm = mids.map { dist($0, c) }.min() ?? .infinity
            if dc <= thresh && dc <= dm { cornerVotes += 1 }
            else if dm <= thresh { midVotes += 1 }
        }
        guard (3...6).contains(sharp) else { return .ellipse }   // round → ellipse
        return midVotes > cornerVotes ? .diamond : .rectangle
    }

    /// Direction change (radians) at the middle point — 0 straight, ~π/2 a square corner.
    static func turnAngle(_ a: StrokePoint, _ c: StrokePoint, _ d: StrokePoint) -> Double {
        let d1 = atan2(c.y - a.y, c.x - a.x), d2 = atan2(d.y - c.y, d.x - c.x)
        var t = abs(d2 - d1)
        if t > .pi { t = 2 * .pi - t }
        return t
    }

    /// Ramer–Douglas–Peucker polyline simplification — keeps the corners, drops the noise.
    static func simplify(_ pts: [StrokePoint], epsilon: Double) -> [StrokePoint] {
        guard pts.count > 2 else { return pts }
        var dmax = 0.0, index = 0
        for i in 1..<(pts.count - 1) {
            let d = perpendicular(pts[i], pts.first!, pts.last!)
            if d > dmax { dmax = d; index = i }
        }
        if dmax > epsilon {
            let left = simplify(Array(pts[0...index]), epsilon: epsilon)
            let right = simplify(Array(pts[index...]), epsilon: epsilon)
            return left.dropLast() + right
        }
        return [pts.first!, pts.last!]
    }
    static func perpendicular(_ p: StrokePoint, _ a: StrokePoint, _ b: StrokePoint) -> Double {
        let dx = b.x - a.x, dy = b.y - a.y
        let len = (dx * dx + dy * dy).squareRoot()
        guard len > 0 else { return dist(p, a) }
        return abs(dy * p.x - dx * p.y + b.x * a.y - b.y * a.x) / len
    }
}

// MARK: - Graph

public struct DiagramNode: Equatable, Sendable {
    public let id: String; public let kind: ShapeKind; public let text: String; public let bounds: Bounds
    public init(id: String, kind: ShapeKind, text: String, bounds: Bounds) {
        self.id = id; self.kind = kind; self.text = text; self.bounds = bounds
    }
}
public struct DiagramEdge: Equatable, Sendable {
    public let from: String; public let to: String; public let label: String?
    public init(from: String, to: String, label: String? = nil) { self.from = from; self.to = to; self.label = label }
}
public struct DiagramGraph: Equatable, Sendable {
    public let nodes: [DiagramNode]; public let edges: [DiagramEdge]
    public init(nodes: [DiagramNode], edges: [DiagramEdge]) { self.nodes = nodes; self.edges = edges }
}

public enum DiagramBuilder {
    public struct NodeInput { public let kind: ShapeKind; public let text: String; public let bounds: Bounds
        public init(kind: ShapeKind, text: String, bounds: Bounds) { self.kind = kind; self.text = text; self.bounds = bounds } }
    public struct ConnectorInput { public let from: StrokePoint; public let to: StrokePoint; public let label: String?
        public init(from: StrokePoint, to: StrokePoint, label: String? = nil) { self.from = from; self.to = to; self.label = label } }

    /// Build a graph: each node gets a stable id; each connector becomes an edge from the node
    /// nearest its start to the node nearest its end (skipping self-loops / no-node cases).
    public static func build(nodes: [NodeInput], connectors: [ConnectorInput]) -> DiagramGraph {
        let built = nodes.enumerated().map { i, n in DiagramNode(id: "n\(i + 1)", kind: n.kind, text: n.text, bounds: n.bounds) }
        var edges: [DiagramEdge] = []
        for c in connectors {
            guard let a = nearest(to: c.from, in: built), let b = nearest(to: c.to, in: built), a.id != b.id else { continue }
            edges.append(DiagramEdge(from: a.id, to: b.id, label: c.label))
        }
        return DiagramGraph(nodes: built, edges: edges)
    }
    static func nearest(to p: StrokePoint, in nodes: [DiagramNode]) -> DiagramNode? {
        nodes.min { ShapeRecognizer.dist($0.bounds.center, p) < ShapeRecognizer.dist($1.bounds.center, p) }
    }
}

// MARK: - Mermaid

public enum MermaidGenerator {
    /// Render a graph as a Mermaid `flowchart`. Rectangle → `id["t"]`, diamond → `id{"t"}`,
    /// ellipse → `id(("t"))`. Edges → `a --> b` (with `|label|` when present).
    public static func flowchart(_ g: DiagramGraph, direction: String = "TD") -> String {
        var lines = ["flowchart \(direction)"]
        for n in g.nodes {
            let t = escape(n.text.isEmpty ? n.id : n.text)
            switch n.kind {
            case .rectangle: lines.append("    \(n.id)[\"\(t)\"]")
            case .diamond:   lines.append("    \(n.id){\"\(t)\"}")
            case .ellipse:   lines.append("    \(n.id)((\"\(t)\"))")
            }
        }
        for e in g.edges {
            if let l = e.label, !l.isEmpty { lines.append("    \(e.from) -->|\(escape(l))| \(e.to)") }
            else { lines.append("    \(e.from) --> \(e.to)") }
        }
        return lines.joined(separator: "\n")
    }
    static func escape(_ s: String) -> String {
        s.replacingOccurrences(of: "\"", with: "'").replacingOccurrences(of: "\n", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

// MARK: - VLM ambiguity resolution (HSM-14-09)

/// The geometry is the primary path (fast, deterministic, offline). When it's UNCERTAIN about
/// a shape, fall back to a local vision model (Gemma 3 via the `IVisionProvider` seam) — the
/// owner's Option-2 hybrid: the VLM only resolves ambiguity, it never drives the graph.
public enum SketchVision {
    /// Ask the VLM what a hand-drawn shape is, mapping its words to a `ShapeKind`. Returns nil
    /// if the model errors or its answer is unrecognizable (caller keeps the geometry guess).
    public static func resolveShape(image: Data, using vlm: IVisionProvider) async -> ShapeKind? {
        let prompt = "This is a single hand-drawn flowchart shape. Reply with ONE word only: rectangle, diamond, or ellipse."
        guard let answer = try? await vlm.describe(image: image, prompt: prompt) else { return nil }
        return parse(answer)
    }

    /// Map a free-text VLM answer to a `ShapeKind` (diamond = decision; ellipse = circle/oval).
    public static func parse(_ answer: String) -> ShapeKind? {
        let s = answer.lowercased()
        if s.contains("diamond") || s.contains("rhombus") || s.contains("decision") { return .diamond }
        if s.contains("ellipse") || s.contains("circle") || s.contains("oval") || s.contains("round") { return .ellipse }
        if s.contains("rectangle") || s.contains("rect") || s.contains("box") || s.contains("square") { return .rectangle }
        return nil
    }
}
