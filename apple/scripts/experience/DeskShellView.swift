import SwiftUI

// HSM-14 — "THE DESK" v8: the full generative playground. Bespoke PixelLab objects everywhere — a
// cassette (meeting) + a cartridge (model) + a crystal (the intelligence lens) wired into the workflow
// → a sticky-note OUTCOME blooms out; a little robot companion reacts; and the input DRAWERS (Models /
// Recordings / Blocks) hold the pieces you pull onto the landscape. Reuses DS / Color(hex:) / haptic() / Sprite.

struct DeskShellView: View {
    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width, h = geo.size.height
            ZStack(alignment: .top) {
                DeskSurface()

                LiveWorkflow().position(x: w * 0.52, y: h * 0.30)
                DeskObject(start: CGPoint(x: w * 0.80, y: h * 0.45), angle: 0, bounds: geo.size) { RobotCompanion() }
                DeskObject(start: CGPoint(x: w * 0.18, y: h * 0.50), angle: 0, bounds: geo.size) { RecorderObject() }

                VStack(spacing: 0) {
                    SlimTopBar().padding(.horizontal, 16).padding(.top, 8)
                    Spacer()
                    DrawerDeck().padding(.horizontal, 12).padding(.bottom, 14)
                }
            }.ignoresSafeArea()
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - Live workflow: cassette + cartridge + crystal → sticky-note outcome

struct LiveWorkflow: View {
    var body: some View {
        ZStack {
            Path { p in
                p.move(to: CGPoint(x: 92, y: 150)); p.addQuadCurve(to: CGPoint(x: 196, y: 162), control: CGPoint(x: 150, y: 142))
                p.move(to: CGPoint(x: 150, y: 280)); p.addQuadCurve(to: CGPoint(x: 250, y: 214), control: CGPoint(x: 190, y: 262))
                p.move(to: CGPoint(x: 404, y: 168)); p.addQuadCurve(to: CGPoint(x: 486, y: 150), control: CGPoint(x: 446, y: 150))
            }.stroke(LinearGradient(colors: [DS.local, DS.accent, DS.ok], startPoint: .leading, endPoint: .trailing),
                     style: StrokeStyle(lineWidth: 2.5, lineCap: .round, dash: [1, 7])).opacity(0.85)

            WorkflowMachine().position(x: 300, y: 162)
            VStack(spacing: 4) { Sprite(name: "cassette", size: 100); portTag("SOURCE", DS.local) }.position(x: 74, y: 148)
            VStack(spacing: 4) { Sprite(name: "cartridge", size: 80); portTag("MODEL", DS.local) }.position(x: 132, y: 296)
            // the OUTCOME — a real sticky note blooming out
            VStack(spacing: 5) {
                Sprite(name: "note", size: 96).shadow(color: DS.ok.opacity(0.4), radius: 16, y: 8)
                HStack(spacing: 5) { Image(systemName: "checkmark.seal.fill").font(.system(size: 11, weight: .bold)).foregroundStyle(DS.ok)
                    Text("3 Decisions").font(.system(size: 12, weight: .heavy)).foregroundStyle(DS.text) }
                    .padding(.horizontal, 9).padding(.vertical, 5).background(Capsule().fill(DS.s1.opacity(0.9)).overlay(Capsule().stroke(DS.ok.opacity(0.4))))
            }.position(x: 540, y: 150)
        }.frame(width: 620, height: 340)
    }
    func portTag(_ t: String, _ c: Color) -> some View {
        Text(t).font(.system(size: 8.5, weight: .black)).tracking(1).foregroundStyle(.white)
            .padding(.horizontal, 7).padding(.vertical, 3).background(Capsule().fill(c.opacity(0.85)))
    }
}

struct WorkflowMachine: View {
    var body: some View {
        ZStack {
            // the crystal is the intelligence LENS at the machine's heart
            Sprite(name: "crystal", size: 84).shadow(color: DS.accent.opacity(0.5), radius: 14)
            RadialGradient(colors: [DS.accent.opacity(0.25), .clear], center: .center, startRadius: 4, endRadius: 70).frame(width: 150, height: 150)
        }
        .frame(width: 150, height: 110).padding(10)
        .background(RoundedRectangle(cornerRadius: 20).fill(LinearGradient(colors: [Color(hex: 0x1A1D26), Color(hex: 0x121419)], startPoint: .top, endPoint: .bottom)).litFace(20))
        .overlay(alignment: .bottom) {
            HStack(spacing: 5) { Circle().fill(DS.ok).frame(width: 5, height: 5).shadow(color: DS.ok, radius: 3)
                Text("LENS · running").font(.system(size: 8.5, weight: .black)).tracking(1.2).foregroundStyle(DS.faint) }.padding(.bottom, 7)
        }
    }
}

struct RobotCompanion: View {
    var body: some View {
        VStack(spacing: 6) {
            Text("found 3 decisions ✦").font(.system(size: 11, weight: .heavy)).foregroundStyle(DS.text)
                .padding(.horizontal, 11).padding(.vertical, 7)
                .background(RoundedRectangle(cornerRadius: 14).fill(DS.s1.opacity(0.92)).litFace(14).overlay(RoundedRectangle(cornerRadius: 14).stroke(DS.accent.opacity(0.3))))
            Sprite(name: "robot", size: 104).shadow(color: .black.opacity(0.45), radius: 12, y: 8)
        }
    }
}

// MARK: - Drawers

struct DrawerDeck: View {
    var body: some View {
        HStack(spacing: 12) {
            Drawer(title: "MODELS", tint: DS.local) {
                HStack(spacing: -10) { Sprite(name: "cartridge", size: 70).rotationEffect(.degrees(-7))
                    Sprite(name: "cartridge", size: 64).rotationEffect(.degrees(6)).opacity(0.92) }
            }
            Drawer(title: "RECORDINGS", tint: DS.warn) {
                HStack(spacing: -16) { Sprite(name: "cassette", size: 76).rotationEffect(.degrees(-6))
                    Sprite(name: "cassette2", size: 70).rotationEffect(.degrees(7))
                    Sprite(name: "cassette", size: 62).rotationEffect(.degrees(-3)).opacity(0.9) }
            }
            Drawer(title: "BLOCKS", tint: DS.accent) {
                HStack(spacing: 4) { Sprite(name: "crystal", size: 64).rotationEffect(.degrees(-5))
                    blockChip("EXTRACT", DS.ok); blockChip("NOTE", DS.local) }
            }
        }.frame(height: 150)
    }
    func blockChip(_ t: String, _ c: Color) -> some View {
        Text(t).font(.system(size: 9, weight: .black)).foregroundStyle(.white)
            .padding(.horizontal, 9).padding(.vertical, 7)
            .background(Capsule().fill(LinearGradient(colors: [c, c.opacity(0.65)], startPoint: .top, endPoint: .bottom)).overlay(Capsule().stroke(.white.opacity(0.25))))
            .shadow(color: c.opacity(0.5), radius: 6, y: 3).rotationEffect(.degrees(Double((t.count % 5)) - 2))
    }
}

struct Drawer<Content: View>: View {
    let title: String; let tint: Color
    @ViewBuilder var content: () -> Content
    var body: some View {
        VStack(spacing: 0) {
            ZStack { content() }.frame(maxWidth: .infinity).frame(height: 104)
                .background(
                    RoundedRectangle(cornerRadius: 18)
                        .fill(LinearGradient(colors: [Color(hex: 0x0A0B0E), Color(hex: 0x14161D)], startPoint: .top, endPoint: .bottom))
                        .overlay(RoundedRectangle(cornerRadius: 18).stroke(LinearGradient(colors: [.black.opacity(0.6), .clear], startPoint: .top, endPoint: .center), lineWidth: 6).blur(radius: 4).mask(RoundedRectangle(cornerRadius: 18)))
                        .overlay(RoundedRectangle(cornerRadius: 18).stroke(DS.line)))
            HStack(spacing: 6) {
                RoundedRectangle(cornerRadius: 2).fill(tint).frame(width: 4, height: 11)
                Text(title).font(.system(size: 10, weight: .black)).tracking(1.5).foregroundStyle(DS.muted)
                Spacer()
                Image(systemName: "hand.draw.fill").font(.system(size: 10, weight: .bold)).foregroundStyle(DS.faint)
            }
            .padding(.horizontal, 12).padding(.vertical, 7)
            .background(RoundedRectangle(cornerRadius: 12).fill(LinearGradient(colors: [Color(hex: 0x20232C), Color(hex: 0x171A21)], startPoint: .top, endPoint: .bottom)).litFace(12)).offset(y: -6)
        }
    }
}

// MARK: - Recorder + physics + surface

struct RecorderObject: View {
    var body: some View {
        ZStack {
            ForEach(0..<3) { i in Circle().stroke(DS.accent.opacity(0.3 - Double(i) * 0.09), lineWidth: 2).frame(width: 110 + CGFloat(i) * 28, height: 110 + CGFloat(i) * 28) }
            RadialGradient(colors: [DS.accent.opacity(0.22), .clear], center: .center, startRadius: 6, endRadius: 88).frame(width: 188, height: 188)
            VStack(spacing: 8) {
                Sprite(name: "mic", size: 126).shadow(color: DS.accent.opacity(0.55), radius: 20, y: 10)
                Text("HOLD TO RECORD").font(.system(size: 10, weight: .black)).tracking(1.5).foregroundStyle(.white.opacity(0.95))
                    .padding(.horizontal, 11).padding(.vertical, 5).background(Capsule().fill(.black.opacity(0.45)).overlay(Capsule().stroke(.white.opacity(0.1))))
            }
        }
    }
}

struct DeskObject<Content: View>: View {
    let start: CGPoint; var angle: Double; let bounds: CGSize
    @ViewBuilder var content: () -> Content
    @State private var pos: CGPoint; @State private var drag: CGSize = .zero; @State private var lifted = false
    init(start: CGPoint, angle: Double = 0, bounds: CGSize, @ViewBuilder content: @escaping () -> Content) {
        self.start = start; self.angle = angle; self.bounds = bounds; self.content = content
        _pos = State(initialValue: start)
    }
    var body: some View {
        content().rotationEffect(.degrees(lifted ? angle * 0.3 : angle)).scaleEffect(lifted ? 1.06 : 1)
            .shadow(color: .black.opacity(lifted ? 0.5 : 0.35), radius: lifted ? 28 : 14, x: 0, y: lifted ? 22 : 10)
            .position(x: pos.x + drag.width, y: pos.y + drag.height)
            .gesture(DragGesture()
                .onChanged { v in if !lifted { withAnimation(.easeOut(duration: 0.18)) { lifted = true }; haptic(0) }; drag = v.translation }
                .onEnded { v in
                    var nx = pos.x + v.predictedEndTranslation.width, ny = pos.y + v.predictedEndTranslation.height
                    nx = min(max(nx, bounds.width * 0.1), bounds.width * 0.9); ny = min(max(ny, bounds.height * 0.1), bounds.height * 0.72)
                    drag = .zero
                    withAnimation(.spring(response: 0.5, dampingFraction: 0.72)) { pos = CGPoint(x: nx, y: ny); lifted = false }; haptic(1)
                })
    }
}

struct DeskSurface: View {
    var body: some View {
        ZStack {
            LinearGradient(colors: [Color(hex: 0x0C0D11), Color(hex: 0x111219)], startPoint: .top, endPoint: .bottom)
            RadialGradient(colors: [DS.accent.opacity(0.14), .clear], center: .init(x: 0.5, y: 0.4), startRadius: 8, endRadius: 470)
            RadialGradient(colors: [DS.local.opacity(0.11), .clear], center: .init(x: 0.85, y: 0.16), startRadius: 8, endRadius: 420)
            DotGrid().opacity(0.4)
            RadialGradient(colors: [.clear, .black.opacity(0.5)], center: .center, startRadius: 330, endRadius: 790)
        }.ignoresSafeArea()
    }
}
struct DotGrid: View {
    var body: some View {
        GeometryReader { g in
            Path { p in let step: CGFloat = 36; var y: CGFloat = 0
                while y < g.size.height { var x: CGFloat = 0
                    while x < g.size.width { p.addEllipse(in: CGRect(x: x, y: y, width: 2, height: 2)); x += step }; y += step }
            }.fill(Color.white.opacity(0.05))
        }
    }
}
extension View {
    func litFace(_ radius: CGFloat) -> some View {
        self.overlay(RoundedRectangle(cornerRadius: radius).stroke(LinearGradient(colors: [.white.opacity(0.2), .white.opacity(0.03), .clear], startPoint: .top, endPoint: .bottom), lineWidth: 1))
    }
}
struct SlimTopBar: View {
    var body: some View {
        HStack(spacing: 12) {
            HStack(spacing: 6) {
                Image(systemName: "house.fill").font(.system(size: 11, weight: .bold)).foregroundStyle(DS.faint)
                Image(systemName: "chevron.right").font(.system(size: 8, weight: .bold)).foregroundStyle(DS.faint)
                Text("GitLab").font(.system(size: 13, weight: .heavy)).foregroundStyle(DS.text)
            }
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").font(.system(size: 12, weight: .bold)).foregroundStyle(DS.faint)
                Text("Find a meeting, open a folder, run a workflow…").font(.system(size: 12, weight: .semibold)).foregroundStyle(DS.faint)
                Spacer()
                Text("⌘K").font(.system(size: 10, weight: .bold)).foregroundStyle(DS.faint).padding(.horizontal, 5).padding(.vertical, 2).background(RoundedRectangle(cornerRadius: 5).fill(DS.s3))
            }.padding(.horizontal, 11).padding(.vertical, 8).background(Capsule().fill(DS.s1.opacity(0.85)).overlay(Capsule().stroke(DS.line)))
            HStack(spacing: 5) { Circle().fill(DS.ok).frame(width: 7, height: 7).shadow(color: DS.ok, radius: 4)
                Text("on device").font(.system(size: 12, weight: .bold)).foregroundStyle(DS.muted) }
                .padding(.horizontal, 10).padding(.vertical, 8).background(Capsule().fill(DS.s1.opacity(0.7)).overlay(Capsule().stroke(DS.line)))
        }
    }
}
