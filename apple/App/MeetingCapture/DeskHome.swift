import SwiftUI

// HSM-14-19 — THE DESK, for real. The app's home reimagined as the gamified physics workspace, bound
// to REAL data: your actual meetings (CaptureModel.meetings, from the on-device store) are bespoke
// cassette objects you fling with momentum and tap to open the real detail; the recorder is the hero
// puck that starts a real recording; the loaded model is a cartridge. No mock data — this is the shell.
// Gate to the classic list with HS_CLASSIC_HOME=1.

struct DeskHome: View {
    @StateObject private var model = CaptureModel()
    @State private var openMeetingID: String?
    @State private var capturing = false
    @State private var showModels = false

    var body: some View {
        NavigationStack {
            GeometryReader { geo in
                let w = geo.size.width, h = geo.size.height
                ZStack {
                    DeskBackground()

                    // Real meetings, scattered as cassette tapes.
                    ForEach(Array(model.meetings.prefix(9).enumerated()), id: \.element.id) { i, m in
                        DeskDrag(start: Self.meetingPos(i, geo.size), angle: Self.angle(i), bounds: geo.size,
                                 onTap: { tactile(); openMeetingID = m.id }) {
                            MeetingTape(meeting: m, sprite: i % 2 == 0 ? "cassette" : "cassette2")
                        }
                    }

                    // The loaded model — a cartridge.
                    if let mdl = ModelFiles.installed().first {
                        DeskDrag(start: CGPoint(x: w * 0.80, y: h * 0.66), angle: -6, bounds: geo.size,
                                 onTap: { tactile(); showModels = true }) {
                            ModelCartridgeObj(name: mdl.name)
                        }
                    }

                    // The recorder — the hero. Tap to start a real recording.
                    DeskRecorder().position(x: w * 0.5, y: h * 0.82)
                        .onTapGesture { tactile(.medium); capturing = true }

                    if model.meetings.isEmpty { DeskEmptyHint().position(x: w * 0.5, y: h * 0.42) }

                    VStack { DeskTopBar(count: model.meetings.count, onModels: { tactile(); showModels = true }); Spacer() }
                }
            }
            .navigationDestination(item: $openMeetingID) { id in
                if let m = model.meetings.first(where: { $0.id == id }) { MeetingDetailView(meeting: m) }
            }
            .navigationDestination(isPresented: $capturing) { CaptureView(model: model, done: { capturing = false; model.refresh() }) }
            .navigationDestination(isPresented: $showModels) { ModelsView() }
            .toolbar(.hidden, for: .navigationBar)
        }
        .tint(Sig.accent)
        .onAppear { model.refresh() }
    }

    // Deterministic scatter in the upper desk (loose 2-column drift).
    static func meetingPos(_ i: Int, _ s: CGSize) -> CGPoint {
        let col = i % 2, row = i / 2
        let xs: [CGFloat] = [0.30, 0.66]
        let jx = CGFloat((i * 37) % 11 - 5) / 100
        return CGPoint(x: s.width * (xs[col] + jx), y: s.height * (0.20 + CGFloat(row) * 0.155))
    }
    static func angle(_ i: Int) -> Double { [-6, 5, -4, 7, -3, 6, -5, 4, -2][i % 9] }
}

// MARK: - Real meeting as a cassette tape

struct MeetingTape: View {
    let meeting: Meeting
    let sprite: String
    private var speakers: Int { Set(meeting.segments.map(\.speaker)).count }
    private var title: String {
        if let t = meeting.title, !t.isEmpty { return t }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"; return f.string(from: meeting.startedAt)
    }
    var body: some View {
        VStack(spacing: 7) {
            DeskSprite(name: sprite, size: 138).shadow(color: .black.opacity(0.45), radius: 12, y: 9)
            VStack(spacing: 2) {
                Text(title).font(.system(size: 13, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                HStack(spacing: 6) {
                    Text(clockString(meeting.duration ?? 0)).font(.system(size: 10.5, weight: .bold)).foregroundStyle(Sig.muted)
                    if speakers > 0 {
                        Text("·").foregroundStyle(Sig.faint)
                        Image(systemName: "person.2.fill").font(.system(size: 8, weight: .bold)).foregroundStyle(Sig.faint)
                        Text("\(speakers)").font(.system(size: 10.5, weight: .bold)).foregroundStyle(Sig.muted)
                    }
                }
            }
            .padding(.horizontal, 11).padding(.vertical, 6)
            .background(Capsule().fill(Sig.s1.opacity(0.82)).overlay(Capsule().strokeBorder(Sig.local.opacity(0.25), lineWidth: 1)))
        }.frame(width: 150)
    }
}

struct ModelCartridgeObj: View {
    let name: String
    var body: some View {
        VStack(spacing: 7) {
            DeskSprite(name: "cartridge", size: 104).shadow(color: .black.opacity(0.45), radius: 12, y: 9)
            VStack(spacing: 2) {
                Text(name.replacingOccurrences(of: ".gguf", with: "")).font(.system(size: 12, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1).frame(maxWidth: 130)
                HStack(spacing: 4) {
                    Circle().fill(Sig.ok).frame(width: 5, height: 5)
                    Text("loaded · on device").font(.system(size: 9.5, weight: .bold)).foregroundStyle(Sig.muted)
                }
            }
            .padding(.horizontal, 10).padding(.vertical, 5)
            .background(Capsule().fill(Sig.s1.opacity(0.82)).overlay(Capsule().strokeBorder(Sig.local.opacity(0.3), lineWidth: 1)))
        }
    }
}

struct DeskRecorder: View {
    @State private var pulse = false
    var body: some View {
        ZStack {
            ForEach(0..<3) { i in
                Circle().stroke(Sig.accent.opacity(0.3 - Double(i) * 0.09), lineWidth: 2)
                    .frame(width: 112 + CGFloat(i) * 28, height: 112 + CGFloat(i) * 28)
                    .scaleEffect(pulse ? 1.06 : 1).opacity(pulse ? 0.7 : 1)
            }
            RadialGradient(colors: [Sig.accent.opacity(0.22), .clear], center: .center, startRadius: 6, endRadius: 90).frame(width: 190, height: 190)
            VStack(spacing: 8) {
                DeskSprite(name: "mic", size: 128).shadow(color: Sig.accent.opacity(0.55), radius: 20, y: 10)
                Text("HOLD TO RECORD").font(.system(size: 10, weight: .black)).tracking(1.5).foregroundStyle(.white.opacity(0.95))
                    .padding(.horizontal, 11).padding(.vertical, 5).background(Capsule().fill(.black.opacity(0.45)))
            }
        }
        .onAppear { withAnimation(.easeInOut(duration: 1.4).repeatForever(autoreverses: true)) { pulse = true } }
    }
}

struct DeskTopBar: View {
    let count: Int
    let onModels: () -> Void
    var body: some View {
        HStack(spacing: 10) {
            HStack(spacing: 7) {
                Circle().fill(Sig.ok).frame(width: 7, height: 7).shadow(color: Sig.ok, radius: 5)
                Text("YOUR DESK").font(.system(size: 13, weight: .black)).tracking(2).foregroundStyle(Sig.muted)
                if count > 0 { Text("· \(count)").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.faint) }
            }
            .padding(.horizontal, 13).padding(.vertical, 8)
            .background(Capsule().fill(Sig.s1.opacity(0.7)).overlay(Capsule().strokeBorder(Sig.line, lineWidth: 1)))
            Spacer()
            Button(action: onModels) {
                HStack(spacing: 5) {
                    Image(systemName: "cpu.fill").font(.system(size: 11, weight: .bold))
                    Text("on device").font(.system(size: 12, weight: .bold))
                }.foregroundStyle(Sig.local)
                .padding(.horizontal, 11).padding(.vertical, 8)
                .background(Capsule().fill(Sig.local.opacity(0.12)).overlay(Capsule().strokeBorder(Sig.local.opacity(0.25), lineWidth: 1)))
            }.buttonStyle(PressableCard())
        }
        .padding(.horizontal, 16).padding(.top, 10)
    }
}

struct DeskBackground: View {
    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            RadialGradient(colors: [Sig.accent.opacity(0.14), .clear], center: .init(x: 0.4, y: 0.78), startRadius: 8, endRadius: 420).ignoresSafeArea()
            RadialGradient(colors: [Sig.local.opacity(0.12), .clear], center: .init(x: 0.85, y: 0.16), startRadius: 8, endRadius: 380).ignoresSafeArea()
            DeskDots().opacity(0.4).ignoresSafeArea()
            RadialGradient(colors: [.clear, .black.opacity(0.42)], center: .center, startRadius: 300, endRadius: 760).ignoresSafeArea()
        }
    }
}
struct DeskDots: View {
    var body: some View {
        GeometryReader { g in
            Path { p in let step: CGFloat = 36; var y: CGFloat = 0
                while y < g.size.height { var x: CGFloat = 0
                    while x < g.size.width { p.addEllipse(in: CGRect(x: x, y: y, width: 2, height: 2)); x += step }; y += step }
            }.fill(Color.white.opacity(0.05))
        }
    }
}

struct DeskEmptyHint: View {
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: "arrow.down").font(.system(size: 22, weight: .bold)).foregroundStyle(Sig.faint)
            Text("Your desk is empty.").font(.system(size: 17, weight: .heavy)).foregroundStyle(Sig.text)
            Text("Tap the mic to record your first meeting —\nit'll land here as a tape you can open.")
                .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.muted).multilineTextAlignment(.center)
        }.frame(width: 280)
    }
}

// MARK: - Drag + tap physics wrapper (tap = a drag that barely moved)

struct DeskDrag<Content: View>: View {
    let start: CGPoint; var angle: Double; let bounds: CGSize; var onTap: () -> Void = {}
    @ViewBuilder var content: () -> Content
    @State private var pos: CGPoint; @State private var drag: CGSize = .zero; @State private var lifted = false
    init(start: CGPoint, angle: Double = 0, bounds: CGSize, onTap: @escaping () -> Void = {}, @ViewBuilder content: @escaping () -> Content) {
        self.start = start; self.angle = angle; self.bounds = bounds; self.onTap = onTap; self.content = content
        _pos = State(initialValue: start)
    }
    var body: some View {
        content()
            .rotationEffect(.degrees(lifted ? angle * 0.3 : angle)).scaleEffect(lifted ? 1.06 : 1)
            .shadow(color: .black.opacity(lifted ? 0.45 : 0), radius: lifted ? 26 : 0, y: lifted ? 20 : 0)
            .position(x: pos.x + drag.width, y: pos.y + drag.height)
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { v in
                    let moved = abs(v.translation.width) + abs(v.translation.height)
                    if moved > 5 { if !lifted { withAnimation(.easeOut(duration: 0.16)) { lifted = true }; tactile() }; drag = v.translation }
                }
                .onEnded { v in
                    let moved = abs(v.translation.width) + abs(v.translation.height)
                    if moved < 6 { onTap(); drag = .zero; lifted = false; return }
                    var nx = pos.x + v.predictedEndTranslation.width, ny = pos.y + v.predictedEndTranslation.height
                    nx = min(max(nx, bounds.width * 0.12), bounds.width * 0.88); ny = min(max(ny, bounds.height * 0.12), bounds.height * 0.86)
                    drag = .zero
                    withAnimation(.spring(response: 0.5, dampingFraction: 0.72)) { pos = CGPoint(x: nx, y: ny); lifted = false }
                    tactile()
                })
    }
}
