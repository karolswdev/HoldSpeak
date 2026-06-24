import SwiftUI

// HSM-14-19 — DeskOS: a world-class organization PANE (a directory tree over your real meetings —
// Smart folders by time, Pinned, the model Library) beside a real PHYSICS CANVAS (SpriteKit) where each
// meeting is a card you fling — it FLIES, BOUNCES off the walls and other cards, spins to an angle, and
// settles. Pinch to zoom out; drag the desk to pan; Tidy snaps them into a clean grid; tap a card to
// open the real meeting. Bound to real data. Classic list behind HS_CLASSIC_HOME=1.

enum DeskFolder: String, Hashable, CaseIterable {
    case all, today, week, pinned, models, archive
    var label: String { ["all": "All Meetings", "today": "Today", "week": "This Week",
                         "pinned": "Pinned", "models": "Models", "archive": "Archive"][rawValue] ?? rawValue }
    var icon: String { ["all": "tray.full.fill", "today": "sun.max.fill", "week": "calendar",
                        "pinned": "pin.fill", "models": "cpu.fill", "archive": "archivebox.fill"][rawValue] ?? "folder" }
}

struct DeskHome: View {
    @StateObject private var model = CaptureModel()
    @AppStorage("hs.desk.pinned") private var pinnedCSV = ""
    @AppStorage("hs.desk.cardmodes") private var modesCSV = ""    // "id=full;id=header" — persists each card's presentation
    @State private var folder: DeskFolder = .all
    @State private var tidyToken = 0
    @State private var zoomToken = 0
    @State private var openMeetingID: String?
    @State private var capturing = false
    @State private var showModels = false

    var body: some View {
        NavigationStack {
            HStack(spacing: 0) {
                DeskSidebar(folder: $folder, count: { count($0) }).frame(width: 236)
                canvas
            }
            .background(Sig.bg.ignoresSafeArea())
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

    private var canvas: some View {
        GeometryReader { geo in
            ZStack(alignment: .topLeading) {
                DeskCanvasBackground()
                DeskPhysicsCanvas(cards: cardData, tidyToken: tidyToken, zoomToken: zoomToken,
                                  onTap: { id in tactile(); if id.hasPrefix("model:") { showModels = true } else { openMeetingID = id } },
                                  onCycle: { id in tactile(); cycleMode(id) })
                if cardData.isEmpty { DeskEmptyHint(folder: folder).position(x: geo.size.width / 2, y: geo.size.height * 0.42) }
                if folder != .models {
                    DeskMic().position(x: geo.size.width * 0.5, y: geo.size.height - 92)
                        .onTapGesture { tactile(.medium); capturing = true }
                }
                VStack { DeskCanvasBar(folder: folder, count: cardData.count,
                                       onTidy: { tactile(); tidyToken += 1 }, onZoom: { tactile(); zoomToken += 1 }); Spacer() }
            }
        }
    }

    // MARK: data

    private var cardData: [DeskCardData] {
        if folder == .models {
            return ModelFiles.installed().map {
                DeskCardData(id: "model:\($0.id)", title: $0.name.replacingOccurrences(of: ".gguf", with: ""),
                             sub: "loaded · on device", sprite: "cartridge", tintHex: 0x5B8DEF, mode: modeFor("model:\($0.id)"))
            }
        }
        return filtered.map { m in
            DeskCardData(id: m.id, title: titleFor(m), sub: subFor(m), sprite: spriteFor(m), tintHex: tintHexFor(m), mode: modeFor(m.id))
        }
    }
    private var filtered: [Meeting] {
        let cal = Calendar.current
        switch folder {
        case .all: return model.meetings
        case .today: return model.meetings.filter { cal.isDateInToday($0.startedAt) }
        case .week: return model.meetings.filter { cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }
        case .pinned: return model.meetings.filter { pinnedSet.contains($0.id) }
        case .archive: return model.meetings.filter { !cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }
        case .models: return []
        }
    }
    private func count(_ f: DeskFolder) -> Int {
        if f == .models { return ModelFiles.installed().count }
        let cal = Calendar.current
        switch f {
        case .all: return model.meetings.count
        case .today: return model.meetings.filter { cal.isDateInToday($0.startedAt) }.count
        case .week: return model.meetings.filter { cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }.count
        case .pinned: return pinnedSet.count
        case .archive: return model.meetings.filter { !cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }.count
        case .models: return 0
        }
    }
    private var pinnedSet: Set<String> { Set(pinnedCSV.split(separator: ",").map(String.init)) }

    // Per-card presentation mode, persisted in "id=full;id=header" form.
    private func modesDict() -> [String: CardMode] {
        var d: [String: CardMode] = [:]
        for pair in modesCSV.split(separator: ";") {
            let kv = pair.split(separator: "=", maxSplits: 1)
            if kv.count == 2, let m = CardMode(rawValue: String(kv[1])) { d[String(kv[0])] = m }
        }
        return d
    }
    private func modeFor(_ id: String) -> CardMode { modesDict()[id] ?? .full }
    private func cycleMode(_ id: String) {
        var d = modesDict(); d[id] = (d[id] ?? .full).next
        modesCSV = d.map { "\($0.key)=\($0.value.rawValue)" }.joined(separator: ";")
    }
    private func spriteFor(_ m: Meeting) -> String { abs(m.id.hashValue) % 2 == 0 ? "cassette" : "cassette2" }
    private func titleFor(_ m: Meeting) -> String {
        if let t = m.title, !t.isEmpty { return t }
        let f = DateFormatter(); f.dateFormat = "MMM d · h:mm a"; return f.string(from: m.startedAt)
    }
    private func subFor(_ m: Meeting) -> String {
        let spk = Set(m.segments.map(\.speaker)).count
        return spk > 0 ? "\(clockString(m.duration ?? 0))  ·  \(spk) speaker\(spk == 1 ? "" : "s")" : clockString(m.duration ?? 0)
    }
    private func tintHexFor(_ m: Meeting) -> UInt { [0x5B8DEF, 0xFF6B35, 0xF2A33C, 0x3ECF8E][abs(m.id.hashValue) % 4] }
}

// MARK: - The left organization pane

struct DeskSidebar: View {
    @Binding var folder: DeskFolder
    let count: (DeskFolder) -> Int
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 8) {
                RoundedRectangle(cornerRadius: 8).fill(Sig.accentGradient).frame(width: 26, height: 26)
                    .overlay(Image(systemName: "square.stack.3d.up.fill").font(.system(size: 12, weight: .bold)).foregroundStyle(.white))
                Text("HoldSpeak").font(.system(size: 17, weight: .black)).foregroundStyle(Sig.text)
            }.padding(.bottom, 18).padding(.leading, 4)
            section("SMART")
            ForEach([DeskFolder.all, .today, .week, .pinned], id: \.self) { row($0) }
            section("LIBRARY").padding(.top, 14)
            ForEach([DeskFolder.models, .archive], id: \.self) { row($0) }
            Spacer()
            HStack(spacing: 6) {
                Image(systemName: "lock.fill").font(.system(size: 9, weight: .black))
                Text("ON-DEVICE").font(.system(size: 9, weight: .heavy)).tracking(1.2)
            }.foregroundStyle(Sig.local).padding(.leading, 6).padding(.bottom, 6)
        }
        .padding(.horizontal, 12).padding(.vertical, 18)
        .frame(maxHeight: .infinity, alignment: .topLeading)
        .background(Sig.bg.opacity(0.55).overlay(Rectangle().fill(Sig.line).frame(width: 1), alignment: .trailing).ignoresSafeArea())
    }
    private func section(_ t: String) -> some View {
        Text(t).font(.system(size: 10, weight: .black)).tracking(1.5).foregroundStyle(Sig.faint).padding(.leading, 9).padding(.bottom, 5)
    }
    private func row(_ f: DeskFolder) -> some View {
        let sel = folder == f
        return Button { tactile(); withAnimation(.easeOut(duration: 0.18)) { folder = f } } label: {
            HStack(spacing: 10) {
                Image(systemName: f.icon).font(.system(size: 13, weight: .semibold)).foregroundStyle(sel ? Sig.accent : Sig.muted).frame(width: 20)
                Text(f.label).font(.system(size: 14, weight: sel ? .heavy : .semibold)).foregroundStyle(sel ? Sig.text : Sig.muted)
                Spacer()
                let c = count(f); if c > 0 { Text("\(c)").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint) }
            }
            .padding(.horizontal, 9).padding(.vertical, 8)
            .background(RoundedRectangle(cornerRadius: 10).fill(sel ? Sig.accent.opacity(0.15) : .clear)
                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(sel ? Sig.accent.opacity(0.35) : .clear, lineWidth: 1)))
        }.buttonStyle(PressableCard())
    }
}

// MARK: - Canvas chrome

struct DeskMic: View {
    @State private var pulse = false
    var body: some View {
        ZStack {
            ForEach(0..<2) { i in
                Circle().stroke(Sig.accent.opacity(0.3 - Double(i) * 0.12), lineWidth: 2)
                    .frame(width: 90 + CGFloat(i) * 24, height: 90 + CGFloat(i) * 24).scaleEffect(pulse ? 1.08 : 1).opacity(pulse ? 0.6 : 1)
            }
            Circle().fill(RadialGradient(colors: [Color(hex: 0xFF8A5B), Sig.accent, Color(hex: 0xC23C16)], center: .init(x: 0.4, y: 0.35), startRadius: 3, endRadius: 50))
                .frame(width: 80, height: 80).overlay(Circle().strokeBorder(.white.opacity(0.25), lineWidth: 1)).shadow(color: Sig.accent.opacity(0.55), radius: 18, y: 6)
            Image(systemName: "mic.fill").font(.system(size: 28, weight: .bold)).foregroundStyle(.white)
        }.onAppear { withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) { pulse = true } }
    }
}

struct DeskCanvasBar: View {
    let folder: DeskFolder; let count: Int; let onTidy: () -> Void; let onZoom: () -> Void
    var body: some View {
        HStack(spacing: 10) {
            HStack(spacing: 7) {
                Image(systemName: folder.icon).font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.accent)
                Text(folder.label).font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.text)
                if count > 0 { Text("\(count)").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint)
                    .padding(.horizontal, 6).padding(.vertical, 2).background(Capsule().fill(Sig.s3)) }
            }
            Spacer()
            pill("arrow.up.left.and.arrow.down.right", "Fit", onZoom)
            pill("square.grid.2x2.fill", "Tidy", onTidy)
        }.padding(.horizontal, 18).padding(.top, 14)
    }
    private func pill(_ icon: String, _ label: String, _ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 5) { Image(systemName: icon).font(.system(size: 11, weight: .bold)); Text(label).font(.system(size: 12, weight: .bold)) }
                .foregroundStyle(Sig.text).padding(.horizontal, 11).padding(.vertical, 7).background(Capsule().fill(Sig.s3))
        }.buttonStyle(PressableCard())
    }
}

struct DeskCanvasBackground: View {
    var body: some View {
        ZStack {
            Sig.bgGradient.ignoresSafeArea()
            RadialGradient(colors: [Sig.accent.opacity(0.10), .clear], center: .init(x: 0.5, y: 0.85), startRadius: 8, endRadius: 420).ignoresSafeArea()
            DeskDots().opacity(0.32).ignoresSafeArea()
        }
    }
}
struct DeskDots: View {
    var body: some View {
        GeometryReader { g in
            Path { p in let step: CGFloat = 38; var y: CGFloat = 0
                while y < g.size.height { var x: CGFloat = 0
                    while x < g.size.width { p.addEllipse(in: CGRect(x: x, y: y, width: 2, height: 2)); x += step }; y += step }
            }.fill(Color.white.opacity(0.045))
        }
    }
}
struct DeskEmptyHint: View {
    let folder: DeskFolder
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: folder.icon).font(.system(size: 28, weight: .bold)).foregroundStyle(Sig.faint)
            Text(folder == .all ? "Your desk is empty." : "Nothing in \(folder.label) yet.").font(.system(size: 18, weight: .heavy)).foregroundStyle(Sig.text)
            if folder != .models {
                Text("Tap the mic to record — it lands here as a card\nyou can fling, arrange, and tidy.")
                    .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.muted).multilineTextAlignment(.center)
            }
        }.frame(width: 320)
    }
}
