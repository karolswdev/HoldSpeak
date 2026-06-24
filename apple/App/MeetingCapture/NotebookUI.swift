import SwiftUI
import Foundation
import PencilKit

// HSM-14-19 "The Desk" decomposition: the PencilKit notebook UI (HSM-8-02, the magic pencil) — the
// canvas, pages, note cards, and the notebook view-model wiring — lifted verbatim out of
// MeetingCaptureApp.swift. The Notebook/NotebookStore seam lives in RuntimeCore; this is its UI.

/// A standalone notebook for screenshot-verification of the rich surface (tool picker +
/// pages), over an in-memory store.
struct DemoNotebookView: View {
    @StateObject private var notes = NotebookModel(store: InMemoryNotebookStore(), meetingID: "demo")
    var body: some View {
        ZStack {
            Color(.sRGB, red: 0x0E/255, green: 0x0F/255, blue: 0x13/255, opacity: 1).ignoresSafeArea()
            VStack(alignment: .leading, spacing: 14) {
                Text("NOTEBOOK").font(.caption.weight(.bold)).tracking(2)
                    .foregroundStyle(Color(.sRGB, red: 0x5B/255, green: 0x8D/255, blue: 0xEF/255, opacity: 1))
                Text("Handwritten notes").font(.largeTitle.bold()).foregroundStyle(.white)
                NotebookView(model: notes, editable: true)
            }
            .padding(20).frame(maxWidth: 760).frame(maxWidth: .infinity)
        }
    }
}

// MARK: - PencilKit canvas (the magic pencil)

/// A PencilKit canvas with the system tool picker (pen / highlighter / eraser). Strokes
/// flow back through `drawing`; stroke capture stays on PencilKit's own path so it never
/// fights transcription for the main thread.
struct PencilCanvas: UIViewRepresentable {
    @Binding var drawing: PKDrawing
    var editable: Bool

    func makeUIView(context: Context) -> PKCanvasView {
        let cv = PKCanvasView()
        cv.drawing = drawing
        cv.backgroundColor = .clear
        cv.isOpaque = false
        cv.drawingPolicy = .anyInput               // finger OR pencil (the sim has no pencil)
        cv.delegate = context.coordinator
        if editable {
            let picker = context.coordinator.toolPicker
            picker.setVisible(true, forFirstResponder: cv)
            picker.addObserver(cv)
            DispatchQueue.main.async { cv.becomeFirstResponder() }
        } else {
            cv.isUserInteractionEnabled = false
        }
        return cv
    }

    func updateUIView(_ cv: PKCanvasView, context: Context) {
        if cv.drawing != drawing { cv.drawing = drawing }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, PKCanvasViewDelegate {
        let parent: PencilCanvas
        let toolPicker = PKToolPicker()
        init(_ parent: PencilCanvas) { self.parent = parent }
        func canvasViewDrawingDidChange(_ cv: PKCanvasView) { parent.drawing = cv.drawing }
    }
}

/// HSM-14 — a snippet pulled from the transcript onto the note canvas. The user grabs a moment
/// (a live bubble or a tacked note) and drops it here as a movable card to ink around.
struct NoteCard: Identifiable, Codable, Equatable {
    var id = UUID()
    var text: String
    var x: Double
    var y: Double
}

@MainActor
final class NotebookModel: ObservableObject {
    @Published var pages: [PKDrawing]
    @Published var current = 0
    @Published var cards: [NoteCard] = []          // transcript snippets pulled onto the canvas
    private let notebook: Notebook
    private let cardsURL: URL

    init(store: NotebookStore, meetingID: String) {
        notebook = Notebook(store: store, meetingID: meetingID)
        let loaded = notebook.reload().compactMap { try? PKDrawing(data: $0) }
        pages = loaded.isEmpty ? [PKDrawing()] : loaded
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        cardsURL = docs.appendingPathComponent("notecards-\(meetingID).json")
        cards = (try? JSONDecoder().decode([NoteCard].self, from: Data(contentsOf: cardsURL))) ?? []
    }

    func page(_ i: Int) -> Binding<PKDrawing> {
        Binding(get: { self.pages[i] }, set: { self.pages[i] = $0; self.save() })
    }
    func addPage() { pages.append(PKDrawing()); current = pages.count - 1; save() }
    func save() { try? notebook.save(pages: pages.map { $0.dataRepresentation() }) }
    var hasInk: Bool { pages.contains { !$0.strokes.isEmpty } }

    // HSM-14 — transcript → note canvas.
    func addCard(_ text: String, at p: CGPoint) {
        cards.append(NoteCard(text: text, x: Double(p.x), y: Double(p.y))); saveCards()
    }
    func moveCard(_ id: UUID, to p: CGPoint) {
        guard let i = cards.firstIndex(where: { $0.id == id }) else { return }
        cards[i].x = Double(p.x); cards[i].y = Double(p.y); saveCards()
    }
    func removeCard(_ id: UUID) { cards.removeAll { $0.id == id }; saveCards() }
    private func saveCards() { try? JSONEncoder().encode(cards).write(to: cardsURL, options: .atomic) }
}

// MARK: - Notebook surface

struct NotebookView: View {
    @ObservedObject var model: NotebookModel
    var editable: Bool
    var onPromote: ((NoteCard, ArtifactType) -> Void)? = nil

    var body: some View {
        VStack(spacing: 10) {
            HStack(spacing: 10) {
                Text("Page \(model.current + 1) of \(model.pages.count)")
                    .font(.caption.weight(.medium)).foregroundStyle(SigN.muted)
                Spacer()
                if editable {
                    Button { if model.current > 0 { model.current -= 1 } } label: {
                        Image(systemName: "chevron.left").foregroundStyle(model.current > 0 ? SigN.accent : SigN.faint)
                    }.disabled(model.current == 0)
                    Button { if model.current < model.pages.count - 1 { model.current += 1 } } label: {
                        Image(systemName: "chevron.right").foregroundStyle(model.current < model.pages.count - 1 ? SigN.accent : SigN.faint)
                    }.disabled(model.current == model.pages.count - 1)
                    Button { model.addPage() } label: {
                        HStack(spacing: 4) { Image(systemName: "plus"); Text("Page") }
                            .font(.caption.weight(.semibold)).foregroundStyle(SigN.accent)
                    }
                }
            }
            ZStack(alignment: .topLeading) {
                PencilCanvas(drawing: editable ? model.page(model.current) : .constant(model.pages[model.current]),
                             editable: editable)
                // HSM-14 — transcript snippets pulled onto the canvas float ABOVE the ink, so you
                // can drag them around and ink in the gaps. Always rendered (so they reliably
                // reappear when a saved meeting is reopened).
                ForEach(model.cards) { card in
                    NoteCardView(card: card, editable: editable,
                                 onMove: { model.moveCard(card.id, to: $0) },
                                 onRemove: { withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { model.removeCard(card.id) } },
                                 onPromote: onPromote.map { op in { type in op(card, type) } })
                }
            }
            .frame(maxWidth: .infinity, minHeight: 360)
            .background(SigN.s1, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(SigN.line, lineWidth: 1))
            .coordinateSpace(name: "notecanvas")
        }
    }
}

/// A transcript snippet living on the note canvas: a quoted, tinted card you drag to place and
/// ink around. Tap its corner to remove. Lands with a spring when it arrives from the transcript.
struct NoteCardView: View {
    let card: NoteCard
    let editable: Bool
    let onMove: (CGPoint) -> Void
    let onRemove: () -> Void
    var onPromote: ((ArtifactType) -> Void)? = nil
    @State private var landed = false
    @State private var lifting = false
    @State private var promoted = false

    private let promoteTypes: [ArtifactType] = [.decisions, .actionItems, .riskRegister, .requirements, .adr]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 7) {
                Image(systemName: "quote.opening").font(.system(size: 11, weight: .bold)).foregroundStyle(SigN.accent)
                Text(card.text)
                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(SigN.muted)
                    .lineLimit(5).fixedSize(horizontal: false, vertical: true)
            }
            // The card OFFERS something: turn this moment into a real intelligence artifact.
            if let onPromote, editable {
                Button {
                    guard !promoted else { return }
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { promoted = true }
                    tactile(.medium); onPromote(guessArtifactType(card.text))
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: promoted ? "checkmark.circle.fill" : "sparkles")
                        Text(promoted ? "In review" : "Promote to artifact")
                    }
                    .font(.system(size: 10, weight: .heavy))
                    .foregroundStyle(promoted ? SigN.accent : .black)
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(promoted ? SigN.accent.opacity(0.16) : SigN.accent, in: Capsule())
                }
                .buttonStyle(.plain)
                .contextMenu {
                    ForEach(promoteTypes, id: \.self) { t in
                        Button { withAnimation { promoted = true }; tactile(.medium); onPromote(t) } label: {
                            Label("Promote as \(artifactTypeLabel(t))", systemImage: artifactGlyph(t))
                        }
                    }
                }
            }
        }
        .padding(.horizontal, 11).padding(.vertical, 9)
        .frame(width: 196, alignment: .leading)
        .background(SigN.s1, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous).stroke(SigN.accent.opacity(lifting ? 0.85 : 0.4), lineWidth: lifting ? 1.6 : 1))
        .shadow(color: .black.opacity(lifting ? 0.5 : 0.28), radius: lifting ? 14 : 7, y: lifting ? 8 : 4)
        .overlay(alignment: .topTrailing) {
            if editable {
                Button(action: onRemove) {
                    Image(systemName: "xmark.circle.fill").font(.system(size: 16))
                        .foregroundStyle(SigN.faint).background(Circle().fill(SigN.s1))
                }
                .buttonStyle(.plain).offset(x: 6, y: -6)
            }
        }
        .scaleEffect(landed ? (lifting ? 1.04 : 1) : 1.3)
        .position(x: card.x, y: card.y)
        .gesture(editable ?
            DragGesture(coordinateSpace: .named("notecanvas"))
                .onChanged { v in if !lifting { withAnimation(.spring(response: 0.2, dampingFraction: 0.7)) { lifting = true } }; onMove(v.location) }
                .onEnded { _ in withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { lifting = false } }
            : nil)
        .onAppear { withAnimation(.spring(response: 0.34, dampingFraction: 0.6)) { landed = true } }
        .transition(.scale.combined(with: .opacity))
    }
}

/// A tiny palette mirror so the notebook views compile alongside the (fileprivate) one.
