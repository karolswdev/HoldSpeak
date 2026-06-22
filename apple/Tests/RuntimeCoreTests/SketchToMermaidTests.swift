import XCTest
@testable import RuntimeCore

/// HSM-14-08 — the Pencil-as-diagram-language engine: strokes → shapes → graph → Mermaid,
/// deterministic + pure (no model, no device). Synthetic strokes prove the recognizer, and
/// the owner's login-flow example proves the full pipeline emits the right Mermaid.
final class SketchToMermaidTests: XCTestCase {

    // MARK: synthetic stroke makers

    private func trace(_ corners: [(Double, Double)], step: Double = 0.18) -> [StrokePoint] {
        var p: [StrokePoint] = []
        for i in 0..<(corners.count - 1) {
            let (ax, ay) = corners[i]; let (bx, by) = corners[i + 1]
            var t = 0.0
            while t < 1.0 { p.append(StrokePoint(ax + (bx - ax) * t, ay + (by - ay) * t)); t += step }
        }
        p.append(StrokePoint(corners.last!.0, corners.last!.1))
        return p
    }
    private func rect(_ x: Double, _ y: Double, _ w: Double, _ h: Double) -> [StrokePoint] {
        trace([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)])
    }
    private func diamond(_ cx: Double, _ cy: Double, _ rx: Double, _ ry: Double) -> [StrokePoint] {
        trace([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy), (cx, cy - ry)])
    }
    private func ellipse(_ cx: Double, _ cy: Double, _ rx: Double, _ ry: Double, _ n: Int = 60) -> [StrokePoint] {
        (0...n).map { i in
            let a = 2 * Double.pi * Double(i) / Double(n)
            return StrokePoint(cx + rx * cos(a), cy + ry * sin(a))
        }
    }

    // MARK: recognizer

    func testRectangleRecognized() {
        guard case .shape(let k, _) = ShapeRecognizer.classify(rect(0, 0, 100, 60)) else { return XCTFail("not a shape") }
        XCTAssertEqual(k, .rectangle)
    }
    func testDiamondRecognized() {
        guard case .shape(let k, _) = ShapeRecognizer.classify(diamond(50, 40, 50, 40)) else { return XCTFail("not a shape") }
        XCTAssertEqual(k, .diamond)
    }
    func testEllipseRecognized() {
        guard case .shape(let k, _) = ShapeRecognizer.classify(ellipse(50, 30, 50, 30)) else { return XCTFail("not a shape") }
        XCTAssertEqual(k, .ellipse)
    }
    func testOpenStrokeIsAConnectorCarryingDirection() {
        guard case .connector(let from, let to) = ShapeRecognizer.classify(
            [StrokePoint(0, 0), StrokePoint(50, 40), StrokePoint(100, 80)]) else { return XCTFail("not a connector") }
        XCTAssertEqual(from, StrokePoint(0, 0)); XCTAssertEqual(to, StrokePoint(100, 80))
    }

    // MARK: full pipeline — the owner's login flow

    func testLoginFlowBuildsTheExpectedMermaid() {
        let nodes = [
            DiagramBuilder.NodeInput(kind: .rectangle, text: "Login", bounds: Bounds(minX: 0, minY: 0, maxX: 100, maxY: 40)),
            DiagramBuilder.NodeInput(kind: .diamond, text: "Validate User", bounds: Bounds(minX: 20, minY: 80, maxX: 80, maxY: 140)),
            DiagramBuilder.NodeInput(kind: .rectangle, text: "Home", bounds: Bounds(minX: 0, minY: 200, maxX: 60, maxY: 240)),
            DiagramBuilder.NodeInput(kind: .rectangle, text: "Error", bounds: Bounds(minX: 100, minY: 200, maxX: 160, maxY: 240)),
        ]
        let connectors = [
            DiagramBuilder.ConnectorInput(from: StrokePoint(50, 40), to: StrokePoint(50, 80)),
            DiagramBuilder.ConnectorInput(from: StrokePoint(40, 140), to: StrokePoint(30, 200), label: "yes"),
            DiagramBuilder.ConnectorInput(from: StrokePoint(60, 140), to: StrokePoint(130, 200), label: "no"),
        ]
        let mermaid = MermaidGenerator.flowchart(DiagramBuilder.build(nodes: nodes, connectors: connectors))
        XCTAssertTrue(mermaid.contains("flowchart TD"))
        XCTAssertTrue(mermaid.contains(#"n1["Login"]"#))
        XCTAssertTrue(mermaid.contains(#"n2{"Validate User"}"#))   // decision → diamond
        XCTAssertTrue(mermaid.contains(#"n3["Home"]"#))
        XCTAssertTrue(mermaid.contains("n1 --> n2"))
        XCTAssertTrue(mermaid.contains("n2 -->|yes| n3"))
        XCTAssertTrue(mermaid.contains("n2 -->|no| n4"))
    }

    func testSelfLoopAndNodelessConnectorsAreSkipped() {
        let nodes = [DiagramBuilder.NodeInput(kind: .rectangle, text: "A", bounds: Bounds(minX: 0, minY: 0, maxX: 10, maxY: 10))]
        let g = DiagramBuilder.build(nodes: nodes, connectors: [
            DiagramBuilder.ConnectorInput(from: StrokePoint(1, 1), to: StrokePoint(2, 2)),   // both nearest A → self-loop
        ])
        XCTAssertTrue(g.edges.isEmpty)
    }
}
