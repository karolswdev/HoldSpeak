import SwiftUI
import Foundation
import PencilKit
import Vision
import WebKit
import UIKit

// HSM-14-19 "The Desk" decomposition: the Sketch -> Diagram feature (HSM-14-08/09 — the Pencil as a
// diagram language: geometry + on-device Vision + the LAN vision model, rendered to native Mermaid),
// lifted verbatim out of MeetingCaptureApp.swift. Same module; Sig/tactile/ShapeKind/DiagramGraph resolve.

// MARK: - Sketch → Diagram (HSM-14-08: the Pencil as a diagram language, live)

private func shapeTint(_ k: ShapeKind) -> Color {
    switch k { case .rectangle: return Sig.local; case .diamond: return Sig.accent; case .ellipse: return Sig.ok }
}

/// Recognizes the PencilKit drawing into a graph + Mermaid, live + on-device. Geometry does the
/// shapes/edges (HSM-14-08 engine); on-device Vision reads the handwriting into node labels.
@MainActor final class SketchModel: ObservableObject {
    @Published var drawing = PKDrawing() { didSet { schedule() } }
    @Published var graph = DiagramGraph(nodes: [], edges: [])
    @Published var mermaid = ""
    @Published var vlmBusy = false
    @Published var vlmError = ""
    @Published var usedAI = false
    @Published var diagramType = ""
    private var task: Task<Void, Never>?

    /// HSM-14-09 — hand the whole sketch to the local vision model (Qwythos on .43) when the
    /// geometry isn't enough. It returns Mermaid; we parse + render it natively.
    func recognizeWithAI() {
        guard !drawing.strokes.isEmpty, !vlmBusy else { return }
        let png = Self.renderPNG(drawing)
        vlmBusy = true; vlmError = ""; tactile(.medium)
        Task { [weak self] in
            do {
                let raw = try await SketchVLM.mermaid(from: png)
                let (mm, type) = MermaidParse.parseResponse(raw)
                let g = MermaidParse.graph(mm)
                await MainActor.run {
                    self?.vlmBusy = false; self?.usedAI = true; self?.mermaid = mm; self?.diagramType = type
                    withAnimation(.spring(response: 0.5, dampingFraction: 0.82)) { self?.graph = g }
                }
            } catch {
                await MainActor.run { self?.vlmBusy = false; self?.vlmError = "Couldn't reach the vision model: \(error.localizedDescription)" }
            }
        }
    }
    nonisolated static func renderPNG(_ drawing: PKDrawing) -> Data {
        let b = drawing.bounds.insetBy(dx: -24, dy: -24)
        let rect = (b.isNull || b.isEmpty) ? CGRect(x: 0, y: 0, width: 400, height: 300) : b
        let drawn = drawing.image(from: rect, scale: 2)
        let r = UIGraphicsImageRenderer(size: drawn.size)
        let onWhite = r.image { ctx in
            UIColor.white.setFill(); ctx.fill(CGRect(origin: .zero, size: drawn.size)); drawn.draw(at: .zero)
        }
        return onWhite.pngData() ?? Data()
    }

    func schedule() {
        task?.cancel()
        let d = drawing
        task = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 280_000_000)        // debounce while drawing
            if Task.isCancelled { return }
            let result = await Task.detached { Self.recognize(d) }.value   // Vision off the main actor
            if Task.isCancelled { return }
            withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) { self?.graph = result.0 }
            self?.mermaid = result.1
        }
    }
    func clear() {
        drawing = PKDrawing(); graph = DiagramGraph(nodes: [], edges: []); mermaid = ""
    }

    nonisolated static func recognize(_ drawing: PKDrawing) -> (DiagramGraph, String) {
        var nodes: [DiagramBuilder.NodeInput] = []
        var connectors: [DiagramBuilder.ConnectorInput] = []
        for s in drawing.strokes {
            let pts = s.path.map { StrokePoint(Double($0.location.x), Double($0.location.y)) }
            guard pts.count >= 2 else { continue }
            switch ShapeRecognizer.classify(pts) {
            case .shape(let kind, let b):
                nodes.append(.init(kind: kind, text: ocrText(in: b, drawing: drawing), bounds: b))
            case .connector(let from, let to):
                let len = ((to.x - from.x) * (to.x - from.x) + (to.y - from.y) * (to.y - from.y)).squareRoot()
                if len > 30 { connectors.append(.init(from: from, to: to, label: nil)) }   // skip tiny text strokes
            }
        }
        let g = DiagramBuilder.build(nodes: nodes, connectors: connectors)
        return (g, MermaidGenerator.flowchart(g))
    }

    /// On-device handwriting OCR over a shape's region → its node label.
    nonisolated static func ocrText(in b: Bounds, drawing: PKDrawing) -> String {
        let rect = CGRect(x: b.minX - 6, y: b.minY - 6, width: b.w + 12, height: b.h + 12)
        guard rect.width > 8, rect.height > 8 else { return "" }
        let img = drawing.image(from: rect, scale: 2)
        guard let cg = img.cgImage else { return "" }
        var text = ""
        let req = VNRecognizeTextRequest { request, _ in
            text = (request.results as? [VNRecognizedTextObservation])?
                .compactMap { $0.topCandidates(1).first?.string }.joined(separator: " ") ?? ""
        }
        req.recognitionLevel = .accurate
        req.usesLanguageCorrection = true
        try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
        return text.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

/// Calls a local OpenAI-compatible VISION endpoint (Qwythos + mmproj on .43) to turn a sketch
/// image into Mermaid. Points at the owner's LAN server; swap the URL to retarget.
enum SketchVLM {
    static let endpoint = URL(string: "http://192.168.1.43:8080/v1/chat/completions")!
    static func mermaid(from png: Data) async throws -> String {
        let b64 = png.base64EncodedString()
        let prompt = """
        You are an expert at reading hand-drawn diagrams. Look at this sketch and reproduce it as a Mermaid diagram.

        FIRST decide which Mermaid diagram type best fits what is actually drawn:
        - "flowchart"        — boxes/diamonds joined by arrows (processes, decisions)
        - "sequenceDiagram"  — actors with vertical lifelines and horizontal messages
        - "classDiagram"     — boxes with a title + a list of fields/methods, connected
        - "stateDiagram-v2"  — states with labelled transitions, often a start/end dot
        - "erDiagram"        — entities with attributes and relationship lines
        - "mindmap"          — a central node with radiating branches
        - "gantt" or "timeline" — bars/events along a time axis

        THEN output VALID Mermaid for that type. Read the handwritten labels (fix obvious misspellings),
        keep it minimal and correct. For flowcharts: box A["x"], diamond B{"x"}, circle C(("x")),
        edge A --> B, labelled edge B -->|yes| C.

        Return ONLY JSON: {"diagram_type": "<one of the names above>", "mermaid": "<the full mermaid code, \\n between lines>"}.
        """
        let body: [String: Any] = [
            "messages": [["role": "user", "content": [
                ["type": "text", "text": prompt],
                ["type": "image_url", "image_url": ["url": "data:image/png;base64,\(b64)"]],
            ]]],
            "max_tokens": 900, "temperature": 0.2,
            "response_format": [
                "type": "json_schema",
                "json_schema": [
                    "name": "diagram",
                    "schema": ["type": "object",
                               "properties": ["diagram_type": ["type": "string"],
                                              "mermaid": ["type": "string", "minLength": 1]],
                               "required": ["diagram_type", "mermaid"], "additionalProperties": false],
                ],
            ],
        ]
        var req = URLRequest(url: endpoint, timeoutInterval: 120)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, _) = try await URLSession.shared.data(for: req)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let msg = (json?["choices"] as? [[String: Any]])?.first?["message"] as? [String: Any]
        return (msg?["content"] as? String) ?? ""
    }
}

/// Parse Mermaid flowchart text → a `DiagramGraph` with a simple layered layout, so the VLM's
/// output renders natively. Best-effort: a parse miss just leaves the graph empty (the raw
/// Mermaid is still shown).
enum MermaidParse {
    static func extract(_ raw: String) -> String {
        var s = raw
        if let f = s.range(of: "```") {
            s = String(s[f.upperBound...])
            if let e = s.range(of: "```") { s = String(s[..<e.lowerBound]) }
        }
        if let nl = s.firstIndex(of: "\n"), s[s.startIndex..<nl].lowercased().contains("mermaid") {
            s = String(s[s.index(after: nl)...])
        }
        if let r = s.range(of: "flowchart") { s = String(s[r.lowerBound...]) }
        else if let r = s.range(of: "graph ") { s = String(s[r.lowerBound...]) }
        return s.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// The model returns `{"diagram_type":"…","mermaid":"…"}` (json_schema) or raw/fenced mermaid.
    /// Returns the cleaned mermaid + the diagram type (inferred from the header if absent).
    static func parseResponse(_ content: String) -> (mermaid: String, type: String) {
        if let data = content.data(using: .utf8),
           let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let mm = obj["mermaid"] as? String {
            let m = extract(mm)
            let t = (obj["diagram_type"] as? String).flatMap { $0.isEmpty ? nil : $0 } ?? inferType(m)
            return (m, t)
        }
        let m = extract(content)
        return (m, inferType(m))
    }
    static func inferType(_ mermaid: String) -> String {
        let head = (mermaid.split(separator: "\n").first.map(String.init) ?? "").lowercased()
        let map: [(String, String)] = [
            ("sequencediagram", "sequence"), ("classdiagram", "class"), ("statediagram", "state"),
            ("erdiagram", "ER"), ("mindmap", "mindmap"), ("gantt", "gantt"), ("timeline", "timeline"),
            ("flowchart", "flowchart"), ("graph", "flowchart"),
        ]
        for (k, v) in map where head.contains(k) { return v }
        return "diagram"
    }

    static func graph(_ mermaid: String) -> DiagramGraph {
        var kinds: [String: ShapeKind] = [:]
        var texts: [String: String] = [:]
        var order: [String] = []
        var edges: [(String, String, String?)] = []
        func note(_ id: String, _ kind: ShapeKind?, _ text: String?) {
            if !order.contains(id) { order.append(id) }
            if let k = kind { kinds[id] = k }
            if let t = text, !t.isEmpty { texts[id] = t }
        }
        for raw in mermaid.split(separator: "\n") {
            let line = raw.trimmingCharacters(in: .whitespaces)
            scanDefs(line, note)
            for e in scanEdges(line) { note(e.0, nil, nil); note(e.1, nil, nil); edges.append(e) }
        }
        var depth: [String: Int] = [:]; for id in order { depth[id] = 0 }
        for _ in 0..<max(order.count, 1) {
            for (a, b, _) in edges { let d = (depth[a] ?? 0) + 1; if d > (depth[b] ?? 0) { depth[b] = d } }
        }
        var perRow: [Int: Int] = [:]
        var nodes: [DiagramNode] = []
        for id in order {
            let d = depth[id] ?? 0
            let col = perRow[d, default: 0]; perRow[d] = col + 1
            let x = Double(col) * 175, y = Double(d) * 115
            nodes.append(DiagramNode(id: id, kind: kinds[id] ?? .rectangle, text: texts[id] ?? id,
                                     bounds: Bounds(minX: x, minY: y, maxX: x + 130, maxY: y + 54)))
        }
        return DiagramGraph(nodes: nodes, edges: edges.map { DiagramEdge(from: $0.0, to: $0.1, label: $0.2) })
    }

    private static func scanDefs(_ l: String, _ note: (String, ShapeKind?, String?) -> Void) {
        let pats: [(String, ShapeKind)] = [
            (#"([A-Za-z0-9_]+)\(\(\s*\"?([^\")]*)\"?\s*\)\)"#, .ellipse),
            (#"([A-Za-z0-9_]+)\{\s*\"?([^\"}]*)\"?\s*\}"#, .diamond),
            (#"([A-Za-z0-9_]+)\[\s*\"?([^\"\]]*)\"?\s*\]"#, .rectangle),
        ]
        for (pat, kind) in pats {
            guard let re = try? NSRegularExpression(pattern: pat) else { continue }
            let ns = l as NSString
            re.enumerateMatches(in: l, range: NSRange(location: 0, length: ns.length)) { m, _, _ in
                guard let m = m, m.numberOfRanges >= 3 else { return }
                note(ns.substring(with: m.range(at: 1)), kind,
                     ns.substring(with: m.range(at: 2)).trimmingCharacters(in: .whitespaces))
            }
        }
    }
    private static func scanEdges(_ l: String) -> [(String, String, String?)] {
        let pat = #"([A-Za-z0-9_]+)(?:\[[^\]]*\]|\{[^}]*\}|\(\([^)]*\)\))?\s*[-.=]+>\s*(?:\|([^|]*)\|\s*)?([A-Za-z0-9_]+)"#
        guard let re = try? NSRegularExpression(pattern: pat) else { return [] }
        let ns = l as NSString
        var out: [(String, String, String?)] = []
        re.enumerateMatches(in: l, range: NSRange(location: 0, length: ns.length)) { m, _, _ in
            guard let m = m, m.numberOfRanges >= 4 else { return }
            let a = ns.substring(with: m.range(at: 1))
            let label = m.range(at: 2).location != NSNotFound ? ns.substring(with: m.range(at: 2)).trimmingCharacters(in: .whitespaces) : nil
            out.append((a, ns.substring(with: m.range(at: 3)), label))
        }
        return out
    }
}

/// A REAL Mermaid renderer — a WKWebView running the bundled mermaid.js (offline). Renders any
/// valid Mermaid the geometry engine or the VLM produces, re-rendering on each code change.
struct MermaidWebView: UIViewRepresentable {
    let code: String

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        let wv = WKWebView(frame: .zero, configuration: cfg)
        wv.navigationDelegate = context.coordinator
        wv.isOpaque = false
        wv.backgroundColor = .clear
        wv.scrollView.backgroundColor = .clear
        context.coordinator.wv = wv
        wv.loadHTMLString(Self.html(), baseURL: nil)
        return wv
    }

    func updateUIView(_ wv: WKWebView, context: Context) {
        context.coordinator.latest = code
        if context.coordinator.ready { context.coordinator.render(code) }
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        weak var wv: WKWebView?
        var ready = false
        var latest = ""
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            ready = true
            if !latest.isEmpty { render(latest) }
        }
        func render(_ code: String) {
            let esc = code.replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: "`", with: "\\`").replacingOccurrences(of: "$", with: "\\$")
            wv?.evaluateJavaScript("renderMermaid(`\(esc)`)", completionHandler: nil)
        }
    }

    static func html() -> String {
        let lib = (Bundle.main.url(forResource: "mermaid.min", withExtension: "js")
            .flatMap { try? String(contentsOf: $0, encoding: .utf8) }) ?? ""
        return """
        <!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=3">
        <style>
          html,body{margin:0;background:transparent;}
          #wrap{padding:10px;display:flex;align-items:center;justify-content:center;min-height:100%;}
          .mermaid svg{max-width:100%;height:auto;}
          .err{color:#E5544B;font:12px -apple-system;padding:10px;white-space:pre-wrap;}
        </style>
        <script>\(lib)</script></head>
        <body><div id="wrap"><div class="mermaid" id="m"></div></div>
        <script>
          mermaid.initialize({ startOnLoad:false, theme:'dark', securityLevel:'loose',
            themeVariables:{ background:'transparent', primaryColor:'#1D202A', primaryTextColor:'#F3F4F7',
              lineColor:'#9CA3B2', primaryBorderColor:'#FF6B35' } });
          async function renderMermaid(code){
            const t = (code||'').trim();
            if(!t){ document.getElementById('m').innerHTML=''; return; }
            try{ const { svg } = await mermaid.render('g'+Date.now(), t);
                 document.getElementById('m').innerHTML = svg; }
            catch(e){ document.getElementById('m').innerHTML = '<div class="err">'+String(e&&e.message||e)+'</div>'; }
          }
        </script></body></html>
        """
    }
}

/// Renders a `DiagramGraph` natively (offline, on-brand) — nodes as shapes, edges as arrows,
/// laid out at the sketched positions, scaled to fit.
struct DiagramPreview: View {
    let graph: DiagramGraph

    var body: some View {
        GeometryReader { geo in
            if graph.nodes.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "scribble.variable").font(.system(size: 26)).foregroundStyle(Sig.faint)
                    Text("Draw boxes, diamonds, and arrows.")
                        .font(.system(size: 13)).foregroundStyle(Sig.faint).multilineTextAlignment(.center)
                }.frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Canvas { ctx, size in render(ctx, size) }
            }
        }
    }

    private func render(_ ctx: GraphicsContext, _ size: CGSize) {
        let minX = graph.nodes.map { $0.bounds.minX }.min() ?? 0
        let maxX = graph.nodes.map { $0.bounds.maxX }.max() ?? 1
        let minY = graph.nodes.map { $0.bounds.minY }.min() ?? 0
        let maxY = graph.nodes.map { $0.bounds.maxY }.max() ?? 1
        let gw = max(maxX - minX, 1), gh = max(maxY - minY, 1)
        let pad: CGFloat = 44
        let scale = max(min((size.width - 2 * pad) / gw, (size.height - 2 * pad) / gh), 0.05)
        let offX = (size.width - gw * scale) / 2 - minX * scale
        let offY = (size.height - gh * scale) / 2 - minY * scale
        func pt(_ x: Double, _ y: Double) -> CGPoint { CGPoint(x: x * scale + offX, y: y * scale + offY) }
        func centerOf(_ n: DiagramNode) -> CGPoint { pt(n.bounds.cx, n.bounds.cy) }

        // edges (under nodes)
        for e in graph.edges {
            guard let a = graph.nodes.first(where: { $0.id == e.from }),
                  let b = graph.nodes.first(where: { $0.id == e.to }) else { continue }
            let p1 = centerOf(a), p2 = centerOf(b)
            var line = Path(); line.move(to: p1); line.addLine(to: p2)
            ctx.stroke(line, with: .color(Sig.muted), lineWidth: 2)
            // arrowhead
            let ang = atan2(p2.y - p1.y, p2.x - p1.x)
            let tip = CGPoint(x: p2.x - cos(ang) * 14, y: p2.y - sin(ang) * 14)
            var head = Path()
            head.move(to: tip)
            head.addLine(to: CGPoint(x: tip.x - cos(ang - 0.5) * 12, y: tip.y - sin(ang - 0.5) * 12))
            head.addLine(to: CGPoint(x: tip.x - cos(ang + 0.5) * 12, y: tip.y - sin(ang + 0.5) * 12))
            head.closeSubpath()
            ctx.fill(head, with: .color(Sig.muted))
        }
        // nodes
        for n in graph.nodes {
            let c = centerOf(n)
            let w = max(n.bounds.w * scale, 56), h = max(n.bounds.h * scale, 34)
            let r = CGRect(x: c.x - w / 2, y: c.y - h / 2, width: w, height: h)
            let tint = shapeTint(n.kind)
            let shape: Path
            switch n.kind {
            case .rectangle: shape = Path(roundedRect: r, cornerRadius: 9)
            case .ellipse: shape = Path(ellipseIn: r)
            case .diamond:
                var p = Path()
                p.move(to: CGPoint(x: r.midX, y: r.minY)); p.addLine(to: CGPoint(x: r.maxX, y: r.midY))
                p.addLine(to: CGPoint(x: r.midX, y: r.maxY)); p.addLine(to: CGPoint(x: r.minX, y: r.midY)); p.closeSubpath()
                shape = p
            }
            ctx.fill(shape, with: .color(tint.opacity(0.18)))
            ctx.stroke(shape, with: .color(tint), lineWidth: 2)
            let label = n.text.isEmpty ? "…" : n.text
            ctx.draw(Text(label).font(.system(size: 12, weight: .bold)).foregroundColor(Sig.text), at: c)
        }
    }
}

struct SketchToDiagramView: View {
    @StateObject private var model = SketchModel()
    @Environment(\.dismiss) private var dismiss
    @State private var copied = false

    var body: some View {
        ZStack {
            Sig.bg.ignoresSafeArea()
            VStack(spacing: 12) {
                HStack {
                    Button { dismiss() } label: {
                        HStack(spacing: 6) { Image(systemName: "chevron.left"); Text("Home") }
                            .font(.system(size: 15, weight: .bold)).foregroundStyle(Sig.muted)
                    }
                    Spacer()
                    Text("Sketch → Diagram").font(.system(size: 16, weight: .heavy)).foregroundStyle(Sig.text)
                    Spacer()
                    Button { tactile(); model.clear() } label: {
                        Image(systemName: "trash").font(.system(size: 15, weight: .semibold)).foregroundStyle(Sig.faint)
                    }
                }.padding(.horizontal, 16).padding(.top, 8)

                // Draw
                ZStack(alignment: .topLeading) {
                    PencilCanvas(drawing: $model.drawing, editable: true)
                    if model.drawing.strokes.isEmpty {
                        Text("Draw here ✏️").font(.system(size: 13, weight: .semibold)).foregroundStyle(Sig.faint).padding(14)
                    }
                }
                .background(Sig.s1, in: RoundedRectangle(cornerRadius: 18))
                .overlay(RoundedRectangle(cornerRadius: 18).stroke(Sig.line, lineWidth: 1))
                .frame(maxHeight: .infinity)
                .padding(.horizontal, 14)

                // Recognize-with-AI (the local vision model rescues messy sketches)
                Button { model.recognizeWithAI() } label: {
                    HStack(spacing: 8) {
                        if model.vlmBusy { ProgressView().tint(.black) } else { Image(systemName: "sparkles") }
                        Text(model.vlmBusy ? "Reading your sketch…" : "Recognize with AI")
                    }
                    .font(.system(size: 15, weight: .heavy)).foregroundStyle(.black)
                    .frame(maxWidth: .infinity).frame(height: 50)
                    .background(Sig.accent.opacity(model.drawing.strokes.isEmpty ? 0.3 : 1), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .disabled(model.drawing.strokes.isEmpty || model.vlmBusy)
                .padding(.horizontal, 14)
                if !model.vlmError.isEmpty {
                    Text(model.vlmError).font(.caption).foregroundStyle(Sig.warn).padding(.horizontal, 16)
                }

                // Live diagram
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(model.usedAI ? "AI DIAGRAM" : "LIVE DIAGRAM").font(.system(size: 11, weight: .heavy)).tracking(1.4)
                            .foregroundStyle(model.usedAI ? Sig.accent : Sig.faint)
                        if model.usedAI && !model.diagramType.isEmpty {
                            Text(model.diagramType).font(.system(size: 10, weight: .heavy)).foregroundStyle(Sig.local)
                                .padding(.horizontal, 7).padding(.vertical, 2).background(Sig.local.opacity(0.16), in: Capsule())
                        }
                        Spacer()
                        if !model.usedAI && !model.graph.nodes.isEmpty {
                            Text("\(model.graph.nodes.count) nodes · \(model.graph.edges.count) edges")
                                .font(.system(size: 11, weight: .semibold)).foregroundStyle(Sig.muted)
                        }
                    }
                    Group {
                        if model.mermaid.isEmpty {
                            VStack(spacing: 8) {
                                Image(systemName: "scribble.variable").font(.system(size: 26)).foregroundStyle(Sig.faint)
                                Text("Draw boxes, diamonds, and arrows.")
                                    .font(.system(size: 13)).foregroundStyle(Sig.faint).multilineTextAlignment(.center)
                            }.frame(maxWidth: .infinity, maxHeight: .infinity)
                        } else {
                            MermaidWebView(code: model.mermaid)
                        }
                    }
                    .frame(height: 240)
                    .background(Sig.s1, in: RoundedRectangle(cornerRadius: 16))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(Sig.line, lineWidth: 1))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    if !model.mermaid.isEmpty {
                        HStack {
                            Text(model.mermaid).font(.system(size: 11, design: .monospaced)).foregroundStyle(Sig.muted).lineLimit(3)
                            Spacer(minLength: 8)
                            Button {
                                UIPasteboard.general.string = model.mermaid; tactile(.medium)
                                withAnimation { copied = true }
                                DispatchQueue.main.asyncAfter(deadline: .now() + 1.3) { withAnimation { copied = false } }
                            } label: {
                                Image(systemName: copied ? "checkmark.circle.fill" : "doc.on.doc")
                                    .foregroundStyle(copied ? Sig.ok : Sig.accent)
                            }
                            ShareLink(item: model.mermaid) { Image(systemName: "square.and.arrow.up").foregroundStyle(Sig.accent) }
                        }
                        .padding(10).background(Sig.s2, in: RoundedRectangle(cornerRadius: 12))
                    }
                }
                .padding(.horizontal, 14).padding(.bottom, 10)
            }
        }
        .toolbar(.hidden, for: .navigationBar)
        .preferredColorScheme(.dark)
    }
}

// MARK: - Inference settings store (where intelligence runs) — HSM-14 / HSM-5-06

/// The persisted choice of where a meeting's intelligence runs: fully on this iPad (Mode A,
/// LlamaProvider) or against an OpenAI-compatible endpoint on your LAN (Modes B/C,
/// OpenAIEndpointProvider). One store the Settings UI writes and `generate()` reads, so flipping
/// the target takes effect with no code change. Persisted in UserDefaults; the API key never
/// leaves this store and is attached only at request time.
@MainActor final class InferenceConfigStore: ObservableObject {
    static let shared = InferenceConfigStore()
    @Published var mode: RuntimeMode { didSet { d.set(mode.rawValue, forKey: K.mode) } }
    @Published var endpointURL: String { didSet { d.set(endpointURL, forKey: K.url) } }
    @Published var endpointModel: String { didSet { d.set(endpointModel, forKey: K.model) } }
    @Published var endpointKey: String { didSet { d.set(endpointKey, forKey: K.key) } }
    /// HSM-14-17 — on-device speaker diarization (opt-in). Default ON. When set, capture's `stop()`
    /// labels each transcript segment with who spoke it, fully on-device (no network).
    @Published var diarizationOn: Bool { didSet { d.set(diarizationOn, forKey: K.diarize) } }
    /// Which installed on-device model (its `InstalledModel.id`, i.e. the .gguf filename) runs local
    /// intelligence. Empty = "use the first installed language model" (back-compat default).
    @Published var localModelId: String { didSet { d.set(localModelId, forKey: K.localModel) } }
    /// The WhisperKit transcription model for recording + import (tiny/base/small/large-v3). Read by the
    /// capture transcriber from UserDefaults at transcribe time, so a change applies on the next recording.
    @Published var whisperModel: String { didSet { d.set(whisperModel, forKey: K.whisper) } }
    static let whisperKey = "hs.inf.whisper"        // the UserDefaults key the transcriber reads directly
    /// HSM-18-03 — the spoken language for transcription (dictation, meetings, import). "auto" (the
    /// default) is Whisper's per-utterance detection, byte-identical to before. Read by every
    /// transcriber from UserDefaults at transcribe time (so a change applies on the next recording),
    /// matching the hub's one-knob language model (holdspeak/languages.py, Phase 59).
    @Published var whisperLanguage: String { didSet { d.set(whisperLanguage, forKey: K.whisperLang) } }
    static let whisperLangKey = "hs.inf.whisperlang"  // the UserDefaults key the transcriber reads directly

    private let d = UserDefaults.standard
    private enum K { static let mode = "hs.inf.mode", url = "hs.inf.url", model = "hs.inf.model", key = "hs.inf.key", diarize = "hs.inf.diarize", localModel = "hs.inf.localmodel", whisper = "hs.inf.whisper", whisperLang = "hs.inf.whisperlang" }
    private init() {
        mode = RuntimeMode(rawValue: d.string(forKey: K.mode) ?? "") ?? .local
        endpointURL = d.string(forKey: K.url) ?? ""
        endpointModel = d.string(forKey: K.model) ?? ""
        endpointKey = d.string(forKey: K.key) ?? ""
        diarizationOn = d.object(forKey: K.diarize) as? Bool ?? true
        localModelId = d.string(forKey: K.localModel) ?? ""
        whisperModel = d.string(forKey: K.whisper) ?? "base"
        whisperLanguage = d.string(forKey: K.whisperLang) ?? "auto"
    }

    var isLocal: Bool { mode == .local }

    /// The endpoint config, or nil if the URL is blank/invalid (so generate() can refuse cleanly).
    var endpointConfig: EndpointConfig? {
        let t = endpointURL.trimmingCharacters(in: .whitespaces)
        guard !t.isEmpty, let u = URL(string: t), u.host != nil else { return nil }
        return EndpointConfig(baseURL: u, model: endpointModel.isEmpty ? "local-model" : endpointModel,
                              apiKey: endpointKey.isEmpty ? nil : endpointKey)
    }

    /// A fresh provider for one inference (Llama must be fresh per call; an endpoint client is cheap).
    func makeProvider(localModelPath: String?, context: Int) throws -> ILLMProvider {
        switch mode {
        case .local:
            guard let p = localModelPath else { throw InferenceSettingsError.localEngineUnavailable }
            return try LlamaProvider.make(modelPath: p, maxTokenCount: Int32(context))   // template auto-picked per model family
        case .homelab, .endpoint:
            guard let cfg = endpointConfig else { throw InferenceSettingsError.endpointNotConfigured }
            return OpenAIEndpointProvider(config: cfg)
        }
    }

    /// The egress reality for the badge: local keeps everything on the iPad; an endpoint sends to its host.
    var egressLabel: String { isLocal ? "On-device" : "Sends to \(endpointConfig?.baseURL.host ?? "your endpoint")" }

    private struct ModelsResponse: Decodable { let data: [Entry]; struct Entry: Decodable { let id: String } }

    /// Ask the endpoint what it serves (OpenAI-compatible `GET /v1/models`) so the user PICKS from
    /// the real list instead of typing a name. A successful fetch doubles as the reachability test.
    func fetchModels() async throws -> [String] {
        let base = endpointURL.trimmingCharacters(in: .whitespaces)
        guard !base.isEmpty,
              let u = URL(string: base.hasSuffix("/") ? base + "models" : base + "/models") else { throw URLError(.badURL) }
        var req = URLRequest(url: u); req.timeoutInterval = 12
        if !endpointKey.isEmpty { req.setValue("Bearer \(endpointKey)", forHTTPHeaderField: "Authorization") }
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(ModelsResponse.self, from: data).data.map(\.id)
    }
}
