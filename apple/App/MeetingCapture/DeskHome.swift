import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-19 — DeskOS: a world-class organization PANE (a directory tree over your real meetings —
// Smart folders by time, Pinned, the model Library) beside a real PHYSICS CANVAS (SpriteKit) where each
// meeting is a card you fling — it FLIES, BOUNCES off the walls and other cards, spins to an angle, and
// settles. Pinch to zoom out; drag the desk to pan; Tidy snaps them into a clean grid; tap a card to
// open the real meeting. Bound to real data. Classic list behind HS_CLASSIC_HOME=1.

enum DeskFolder: String, Hashable, CaseIterable {
    case all, today, week, pinned, models, knowledge, archive
    var label: String { ["all": "All Meetings", "today": "Today", "week": "This Week", "pinned": "Pinned",
                         "models": "Models", "knowledge": "Knowledge", "archive": "Archive"][rawValue] ?? rawValue }
    var icon: String { ["all": "tray.full.fill", "today": "sun.max.fill", "week": "calendar", "pinned": "pin.fill",
                        "models": "cpu.fill", "knowledge": "sparkles", "archive": "archivebox.fill"][rawValue] ?? "folder" }
}

// HSM-14-20 — the one typed convention. Every card on the desk is a DeskObject of some kind; the kind
// (parsed from the id namespace) decides what a tap does. This retires the scattered hasPrefix() hacks
// into a single dispatch — add a primitive by adding a case, not by sprinkling string checks.
enum DeskObjectKind {
    case meeting, output, notebook, model, knowledgeBase
    static func of(_ id: String) -> DeskObjectKind {
        if id.hasPrefix("model:") { return .model }
        if id.hasPrefix("kb:") { return .knowledgeBase }
        if id.hasPrefix("open:") { return .notebook }
        if id.hasPrefix("out:") { return .output }
        return .meeting
    }
}

struct DeskHome: View {
    @StateObject private var model = CaptureModel()
    @AppStorage("hs.desk.pinned") private var pinnedCSV = ""
    @AppStorage("hs.desk.cardmodes") private var modesCSV = ""    // "id=full;id=header" — persists each card's presentation
    @AppStorage("hs.desk.folders") private var foldersCSV = ""    // user directories: "Project Atlas;Hiring"
    @AppStorage("hs.desk.kbs") private var kbsCSV = ""            // knowledge bases (typed containers): "Onboarding;Architecture"
    @AppStorage("hs.desk.filed") private var filedCSV = ""        // membership: "id=Project Atlas;..." (dirs AND KBs share this map)
    @State private var folder: DeskFolder = .all
    @State private var activeUserFolder: String?                  // non-nil = a user directory is open (overrides the smart folder)
    @State private var tidyToken = 0
    @State private var zoomToken = 0
    @State private var clearToken = 0
    @State private var gatherToken = 0
    @State private var lassoMode = false
    @State private var selectedIDs: Set<String> = []
    @State private var expanded: Set<String> = []                // meetings whose outputs are spilled onto the desk
    @State private var expandedKBs: Set<String> = []             // knowledge bases opened (members spilled)
    @State private var newIsKB = false                           // the New… alert is creating a KB vs a directory
    @State private var spilledCards: [DeskCardData] = []         // the meeting's outputs, living as desk objects
    @State private var outputBodies: [String: OutputDoc] = [:]   // output id -> what opening it shows
    @State private var windows: [DeskWindowItem] = []            // apps open AS windows on the desk, not as pushed screens
    @State private var topZ: Double = 1
    @State private var showNewFolder = false
    @State private var newFolderName = ""
    @State private var fileAfterCreate = false                    // creating a directory to immediately file the current selection
    @AppStorage("hs.desk.living") private var livingDesk = false   // HSM-14-22: the 3D Living Desk (toolbar toggle)

    var body: some View {
        NavigationStack {
            HStack(spacing: 0) {
                DeskSidebar(folder: $folder, activeUserFolder: $activeUserFolder, userFolders: userFolders,
                            count: { count($0) }, userCount: { userFolderCount($0) },
                            onPick: { selectedIDs = []; clearToken += 1 },
                            onNewFolder: { fileAfterCreate = false; newIsKB = false; newFolderName = ""; showNewFolder = true })
                    .frame(width: 236)
                canvas
            }
            .background(Sig.bg.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .alert(newIsKB ? "New Knowledge Base" : "New Directory", isPresented: $showNewFolder) {
                TextField("Name", text: $newFolderName)
                Button("Create") {
                    let n = newFolderName.trimmingCharacters(in: .whitespaces)
                    if newIsKB { createKB(n) } else { createFolder(n) }
                    if fileAfterCreate, !n.isEmpty { fileSelected(to: n) }
                    newFolderName = ""
                }
                Button("Cancel", role: .cancel) { newFolderName = "" }
            } message: { Text(newIsKB ? "A knowledge base classifies what you file into it; open it to spill its contents."
                                       : "Group meetings into a directory you organize yourself.") }
        }
        .tint(Sig.accent)
        .onAppear { model.refresh() }
    }

    private var canvas: some View {
        GeometryReader { geo in
            ZStack(alignment: .topLeading) {
                DeskCanvasBackground()
                if livingDesk {
                    LivingDeskCanvas(cards: cardData, onTap: { handleTap($0) }, onCycle: { id in tactile(); cycleMode(id) })
                } else {
                    DeskPhysicsCanvas(cards: cardData, tidyToken: tidyToken, zoomToken: zoomToken,
                                      lassoMode: lassoMode, clearToken: clearToken, gatherToken: gatherToken,
                                      onTap: { id in handleTap(id) },
                                      onCycle: { id in tactile(); cycleMode(id) },
                                      onSelect: { ids in selectedIDs = ids })
                }
                if cardData.isEmpty { DeskEmptyHint(folder: activeUserFolder == nil ? folder : .all).position(x: geo.size.width / 2, y: geo.size.height * 0.42) }
                if selectedIDs.isEmpty, activeUserFolder == nil, folder != .models, folder != .knowledge {
                    DeskMic().position(x: geo.size.width * 0.5, y: geo.size.height - 92)
                        .onTapGesture { tactile(.medium); open(.capture) }
                }
                if folder == .knowledge, activeUserFolder == nil, selectedIDs.isEmpty {
                    Button { tactile(.medium); fileAfterCreate = false; newIsKB = true; newFolderName = ""; showNewFolder = true } label: {
                        HStack(spacing: 8) { Image(systemName: "plus").font(.system(size: 13, weight: .black)); Text("New Knowledge Base").font(.system(size: 14, weight: .heavy)) }
                            .foregroundStyle(.white).padding(.horizontal, 18).padding(.vertical, 12)
                            .background(Capsule().fill(Sig.accentGradient).shadow(color: Sig.accent.opacity(0.45), radius: 14, y: 5))
                    }.buttonStyle(PressableCard()).position(x: geo.size.width * 0.5, y: geo.size.height - 86)
                }
                if !selectedIDs.isEmpty {
                    VStack { Spacer()
                        DeskSelectionBar(count: selectedIDs.count, directories: userFolders, knowledgeBases: knowledgeBases,
                                         onBundle: { tactile(.medium); gatherToken += 1 },
                                         onFile: { f in tactile(.medium); fileSelected(to: f) },
                                         onNewFolder: { fileAfterCreate = true; newIsKB = false; newFolderName = ""; showNewFolder = true },
                                         onNewKB: { fileAfterCreate = true; newIsKB = true; newFolderName = ""; showNewFolder = true },
                                         onClear: { tactile(); selectedIDs = []; clearToken += 1 })
                        .padding(.horizontal, 18).padding(.bottom, 22)
                    }
                }
                VStack { DeskCanvasBar(folder: folder, userFolder: activeUserFolder, count: cardData.count, lassoMode: lassoMode,
                                       livingDesk: livingDesk, onToggle3D: { tactile(.medium); livingDesk.toggle() },
                                       onLasso: { tactile(); lassoMode.toggle(); if !lassoMode { selectedIDs = []; clearToken += 1 } },
                                       onTidy: { tactile(); tidyToken += 1 }, onZoom: { tactile(); zoomToken += 1 }); Spacer() }

                // The window layer — apps live ON the desk, floating above the cards.
                ForEach(windows) { w in
                    DeskWindowChrome(item: binding(for: w.id), desk: geo.size,
                                     onClose: { close(w.id) }, onFront: { bringToFront(w.id) }) {
                        windowContent(w.kind)
                    }
                    .zIndex(w.z)
                }
            }
        }
        .onChange(of: folder) { _ in collapseAll(); selectedIDs = []; clearToken += 1 }
        .onChange(of: activeUserFolder) { _ in collapseAll(); selectedIDs = []; clearToken += 1 }
    }

    // MARK: spill — a meeting opens into its OUTPUT OBJECTS on the desk (not files in a panel)

    private func handleTap(_ id: String) {
        tactile()
        switch DeskObjectKind.of(id) {
        case .model: open(.models)
        case .notebook: open(.meeting(String(id.dropFirst(5))))                       // the full notebook (generation lives here)
        case .output: if let d = outputBodies[id] { open(.output(id: id, title: d.title, icon: d.icon, body: d.body)) }
        case .knowledgeBase: toggleSpillKB(String(id.dropFirst(3)))                   // a KB opens by spilling its members
        case .meeting: toggleSpill(id)                                                // a meeting opens by spilling its parts
        }
    }
    private func childParent(_ id: String) -> String? {
        if id.hasPrefix("open:") { return String(id.dropFirst(5)) }
        if id.hasPrefix("out:") { let p = id.split(separator: ":"); return p.count >= 3 ? String(p[2]) : nil }
        return nil
    }
    private func collapseAll() { expanded.removeAll(); expandedKBs.removeAll(); spilledCards.removeAll() }
    private func toggleSpill(_ mid: String) {
        if expanded.contains(mid) {
            expanded.remove(mid); spilledCards.removeAll { childParent($0.id) == mid }
        } else {
            expanded.insert(mid)
            let (cards, bodies) = buildOutputs(mid)
            spilledCards.append(contentsOf: cards); outputBodies.merge(bodies) { _, n in n }
        }
    }
    private func artifacts(for id: String) -> [Artifact] {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let s = try? SQLiteStorage(path: docs.appendingPathComponent("meetings.sqlite").path)
        return (try? s?.loadArtifacts(meetingId: id)) ?? []
    }
    private func buildOutputs(_ mid: String) -> ([DeskCardData], [String: OutputDoc]) {
        guard let m = model.meetings.first(where: { $0.id == mid }) else { return ([], [:]) }
        var cards: [DeskCardData] = []; var bodies: [String: OutputDoc] = [:]
        func add(_ id: String, _ title: String, _ sub: String, _ sprite: String, _ tint: UInt, _ icon: String, _ body: String) {
            cards.append(DeskCardData(id: id, title: title, sub: sub, sprite: sprite, tintHex: tint, mode: .full))
            bodies[id] = OutputDoc(title: title, icon: icon, body: body)
        }
        // The notebook itself — the full detail view (generation / review / ink) is never lost; it's an object too.
        cards.append(DeskCardData(id: "open:\(mid)", title: titleFor(m), sub: "open notebook", sprite: "folder", tintHex: 0xFF6B35, mode: .full))
        if let s = m.intel?.summary, !s.isEmpty { add("out:sum:\(mid)", "Summary", "intelligence", "robot", 0x3ECF8E, "sparkles", s) }
        if let t = m.intel?.topics, !t.isEmpty {
            add("out:top:\(mid)", "Topics", "\(t.count) topic\(t.count == 1 ? "" : "s")", "note", 0x5B8DEF, "tag.fill", t.map { "- \($0)" }.joined(separator: "\n"))
        }
        for (i, a) in (m.intel?.actionItems ?? []).enumerated() {
            add("out:act:\(mid):\(i)", a.task, "action" + (a.owner.map { " · \($0)" } ?? ""), "note", 0xF2A33C, "checkmark.circle.fill",
                "\(a.task)\n\n**Owner:** \(a.owner ?? "—")\n**Due:** \(a.due ?? "—")")
        }
        for art in artifacts(for: mid) {
            add("out:art:\(mid):\(art.id)", art.title, artifactTypeLabel(art.artifactType), "note", 0xF2A33C, "doc.text.fill", art.bodyMarkdown)
        }
        if !m.segments.isEmpty {
            let spk = Set(m.segments.map(\.speaker)).count
            add("out:tx:\(mid)", "Transcript", "\(m.segments.count) segs · \(spk) spk", "cassette2", 0x9B8CFF, "text.alignleft",
                m.segments.map { "**\($0.speaker):** \($0.text)" }.joined(separator: "\n\n"))
        }
        return (cards, bodies)
    }

    // MARK: window management

    private func open(_ kind: DeskWindowKind) {
        tactile()
        if let i = windows.firstIndex(where: { $0.kind == kind }) { bringToFront(windows[i].id); return }
        topZ += 1
        let n = windows.count % 5
        windows.append(DeskWindowItem(id: UUID().uuidString, kind: kind,
                                      offset: CGSize(width: CGFloat(n) * 28 - 24, height: CGFloat(n) * 26 - 30), z: topZ))
    }
    private func close(_ id: String) { tactile(); windows.removeAll { $0.id == id } }
    private func closeKind(_ kind: DeskWindowKind) { windows.removeAll { $0.kind == kind } }
    private func bringToFront(_ id: String) {
        guard let i = windows.firstIndex(where: { $0.id == id }) else { return }
        topZ += 1; windows[i].z = topZ
    }
    private func binding(for id: String) -> Binding<DeskWindowItem> {
        Binding(get: { windows.first(where: { $0.id == id }) ?? DeskWindowItem(id: id, kind: .models, offset: .zero, z: 1) },
                set: { nv in if let i = windows.firstIndex(where: { $0.id == id }) { windows[i] = nv } })
    }
    @ViewBuilder private func windowContent(_ kind: DeskWindowKind) -> some View {
        switch kind {
        case .meeting(let id):
            if let m = model.meetings.first(where: { $0.id == id }) { MeetingDetailView(meeting: m) }
            else { ContentUnavailable(text: "Meeting unavailable") }
        case .capture: CaptureView(model: model, done: { closeKind(.capture); model.refresh() })
        case .models: ModelsView()
        case .output(_, let t, let i, let b): OutputWindowView(title: t, icon: i, text: b)
        }
    }

    // MARK: data

    private var cardData: [DeskCardData] {
        if activeUserFolder == nil, folder == .models {
            return ModelFiles.installed().map {
                DeskCardData(id: "model:\($0.id)", title: $0.name.replacingOccurrences(of: ".gguf", with: ""),
                             sub: "loaded · on device", sprite: "cartridge", tintHex: 0x5B8DEF, mode: modeFor("model:\($0.id)"))
            }
        }
        if activeUserFolder == nil, folder == .knowledge {
            let kbCards = knowledgeBases.map { name in
                DeskCardData(id: "kb:\(name)", title: name, sub: "\(kbCount(name)) item\(kbCount(name) == 1 ? "" : "s") · knowledge base",
                             sprite: "crystal", tintHex: 0x9B8CFF, mode: modeFor("kb:\(name)"))
            }
            return kbCards + spilledCards     // tapping a KB spills its members alongside
        }
        let base = filtered.map { m in
            DeskCardData(id: m.id, title: titleFor(m), sub: subFor(m), sprite: spriteFor(m), tintHex: tintHexFor(m), mode: modeFor(m.id))
        }
        return base + spilledCards            // the meeting's spilled output objects live alongside the cards
    }
    private var filtered: [Meeting] {
        if let uf = activeUserFolder { let d = filedDict(); return model.meetings.filter { d[$0.id] == uf } }
        let cal = Calendar.current
        switch folder {
        case .all: return model.meetings
        case .today: return model.meetings.filter { cal.isDateInToday($0.startedAt) }
        case .week: return model.meetings.filter { cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }
        case .pinned: return model.meetings.filter { pinnedSet.contains($0.id) }
        case .archive: return model.meetings.filter { !cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }
        case .models, .knowledge: return []
        }
    }

    // MARK: user directories

    private var userFolders: [String] { foldersCSV.split(separator: ";").map(String.init).filter { !$0.isEmpty } }
    private func filedDict() -> [String: String] {
        var d: [String: String] = [:]
        for pair in filedCSV.split(separator: ";") {
            let kv = pair.split(separator: "=", maxSplits: 1); if kv.count == 2 { d[String(kv[0])] = String(kv[1]) }
        }
        return d
    }
    private func userFolderCount(_ name: String) -> Int { filedDict().values.filter { $0 == name }.count }
    private func createFolder(_ name: String) {
        let n = name.trimmingCharacters(in: .whitespaces)
        guard !n.isEmpty, !userFolders.contains(n) else { return }
        foldersCSV = (userFolders + [n]).joined(separator: ";")
    }
    private func fileSelected(to name: String) {
        var d = filedDict()
        for id in selectedIDs where !id.contains(":") { d[id] = name }   // file real meetings only (outputs/models carry a ":")
        filedCSV = d.map { "\($0.key)=\($0.value)" }.joined(separator: ";")
        selectedIDs = []; clearToken += 1
    }

    // MARK: knowledge bases — a typed container that reuses filing (to classify) + spill (to open)

    private var knowledgeBases: [String] { kbsCSV.split(separator: ";").map(String.init).filter { !$0.isEmpty } }
    private func kbCount(_ name: String) -> Int { filedDict().values.filter { $0 == name }.count }
    private func createKB(_ name: String) {
        let n = name.trimmingCharacters(in: .whitespaces)
        guard !n.isEmpty, !knowledgeBases.contains(n) else { return }
        kbsCSV = (knowledgeBases + [n]).joined(separator: ";")
    }
    /// Open a KB by spilling its classified members onto the desk (tap again to collapse).
    private func toggleSpillKB(_ name: String) {
        if expandedKBs.contains(name) {
            expandedKBs.remove(name)
            let members = Set(filedDict().filter { $0.value == name }.map(\.key))
            spilledCards.removeAll { members.contains($0.id) }
        } else {
            expandedKBs.insert(name)
            let d = filedDict()
            let members = model.meetings.filter { d[$0.id] == name }
            spilledCards.append(contentsOf: members.map { m in
                DeskCardData(id: m.id, title: titleFor(m), sub: subFor(m), sprite: spriteFor(m), tintHex: tintHexFor(m), mode: modeFor(m.id))
            })
        }
    }
    private var allContainers: [String] { knowledgeBases + userFolders }   // both share the filing map
    private func count(_ f: DeskFolder) -> Int {
        if f == .models { return ModelFiles.installed().count }
        if f == .knowledge { return knowledgeBases.count }
        let cal = Calendar.current
        switch f {
        case .all: return model.meetings.count
        case .today: return model.meetings.filter { cal.isDateInToday($0.startedAt) }.count
        case .week: return model.meetings.filter { cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }.count
        case .pinned: return pinnedSet.count
        case .archive: return model.meetings.filter { !cal.isDate($0.startedAt, equalTo: Date(), toGranularity: .weekOfYear) }.count
        case .models, .knowledge: return 0
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
    @Binding var activeUserFolder: String?
    let userFolders: [String]
    let count: (DeskFolder) -> Int
    let userCount: (String) -> Int
    let onPick: () -> Void
    let onNewFolder: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 8) {
                RoundedRectangle(cornerRadius: 8).fill(Sig.accentGradient).frame(width: 26, height: 26)
                    .overlay(Image(systemName: "square.stack.3d.up.fill").font(.system(size: 12, weight: .bold)).foregroundStyle(.white))
                Text("HoldSpeak").font(.system(size: 17, weight: .black)).foregroundStyle(Sig.text)
            }.padding(.bottom, 18).padding(.leading, 4)
            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 2) {
                    section("SMART")
                    ForEach([DeskFolder.all, .today, .week, .pinned], id: \.self) { row($0) }
                    section("LIBRARY").padding(.top, 14)
                    ForEach([DeskFolder.models, .knowledge, .archive], id: \.self) { row($0) }
                    HStack {
                        section("DIRECTORIES")
                        Spacer()
                        Button(action: onNewFolder) { Image(systemName: "plus.circle.fill").font(.system(size: 14, weight: .bold)).foregroundStyle(Sig.accent) }
                            .padding(.trailing, 6)
                    }.padding(.top, 14)
                    if userFolders.isEmpty {
                        Text("Lasso cards on the desk, then\nFile them into a directory.")
                            .font(.system(size: 11, weight: .medium)).foregroundStyle(Sig.faint).padding(.leading, 9).padding(.top, 2)
                    } else {
                        ForEach(userFolders, id: \.self) { userRow($0) }
                    }
                }
            }
            HStack(spacing: 6) {
                Image(systemName: "lock.fill").font(.system(size: 9, weight: .black))
                Text("ON-DEVICE").font(.system(size: 9, weight: .heavy)).tracking(1.2)
            }.foregroundStyle(Sig.local).padding(.leading, 6).padding(.top, 10).padding(.bottom, 6)
        }
        .padding(.horizontal, 12).padding(.vertical, 18)
        .frame(maxHeight: .infinity, alignment: .topLeading)
        .background(Sig.bg.opacity(0.55).overlay(Rectangle().fill(Sig.line).frame(width: 1), alignment: .trailing).ignoresSafeArea())
    }
    private func section(_ t: String) -> some View {
        Text(t).font(.system(size: 10, weight: .black)).tracking(1.5).foregroundStyle(Sig.faint).padding(.leading, 9).padding(.bottom, 5)
    }
    private func row(_ f: DeskFolder) -> some View {
        let sel = folder == f && activeUserFolder == nil
        return Button { tactile(); onPick(); withAnimation(.easeOut(duration: 0.18)) { activeUserFolder = nil; folder = f } } label: {
            rowBody(icon: f.icon, label: f.label, n: count(f), sel: sel)
        }.buttonStyle(PressableCard())
    }
    private func userRow(_ name: String) -> some View {
        let sel = activeUserFolder == name
        return Button { tactile(); onPick(); withAnimation(.easeOut(duration: 0.18)) { activeUserFolder = name } } label: {
            rowBody(icon: sel ? "folder.fill" : "folder", label: name, n: userCount(name), sel: sel)
        }.buttonStyle(PressableCard())
    }
    private func rowBody(icon: String, label: String, n: Int, sel: Bool) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon).font(.system(size: 13, weight: .semibold)).foregroundStyle(sel ? Sig.accent : Sig.muted).frame(width: 20)
            Text(label).font(.system(size: 14, weight: sel ? .heavy : .semibold)).foregroundStyle(sel ? Sig.text : Sig.muted).lineLimit(1)
            Spacer()
            if n > 0 { Text("\(n)").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint) }
        }
        .padding(.horizontal, 9).padding(.vertical, 8)
        .background(RoundedRectangle(cornerRadius: 10).fill(sel ? Sig.accent.opacity(0.15) : .clear)
            .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(sel ? Sig.accent.opacity(0.35) : .clear, lineWidth: 1)))
    }
}

// MARK: - The lasso selection action bar (floats above the desk when cards are selected)

struct DeskSelectionBar: View {
    let count: Int
    let directories: [String]
    let knowledgeBases: [String]
    let onBundle: () -> Void
    let onFile: (String) -> Void
    let onNewFolder: () -> Void
    let onNewKB: () -> Void
    let onClear: () -> Void
    var body: some View {
        HStack(spacing: 10) {
            HStack(spacing: 7) {
                Image(systemName: "lasso").font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.accent)
                Text("\(count) selected").font(.system(size: 14, weight: .heavy)).foregroundStyle(Sig.text)
            }
            Spacer()
            Button(action: onBundle) { plain("Bundle", "circle.grid.3x3.fill") }.buttonStyle(PressableCard())
            Menu {
                if !knowledgeBases.isEmpty {
                    Section("Knowledge bases") { ForEach(knowledgeBases, id: \.self) { k in Button { onFile(k) } label: { Label(k, systemImage: "sparkles") } } }
                }
                if !directories.isEmpty {
                    Section("Directories") { ForEach(directories, id: \.self) { f in Button { onFile(f) } label: { Label(f, systemImage: "folder") } } }
                }
                Divider()
                Button { onNewKB() } label: { Label("New Knowledge Base…", systemImage: "sparkles") }
                Button { onNewFolder() } label: { Label("New Directory…", systemImage: "folder.badge.plus") }
            } label: { filled("File to", "tray.and.arrow.down.fill") }
            Button(action: onClear) {
                Image(systemName: "xmark").font(.system(size: 12, weight: .black)).foregroundStyle(Sig.muted)
                    .frame(width: 32, height: 32).background(Circle().fill(Sig.s3))
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 11)
        .background(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(Sig.s2)
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(Sig.accent.opacity(0.4), lineWidth: 1))
            .shadow(color: .black.opacity(0.45), radius: 18, y: 8))
    }
    private func plain(_ t: String, _ icon: String) -> some View {
        HStack(spacing: 6) { Image(systemName: icon).font(.system(size: 12, weight: .bold)); Text(t).font(.system(size: 13, weight: .heavy)) }
            .foregroundStyle(Sig.text).padding(.horizontal, 12).padding(.vertical, 9).background(Capsule().fill(Sig.s3))
    }
    private func filled(_ t: String, _ icon: String) -> some View {
        HStack(spacing: 6) { Image(systemName: icon).font(.system(size: 12, weight: .bold)); Text(t).font(.system(size: 13, weight: .heavy)) }
            .foregroundStyle(.white).padding(.horizontal, 13).padding(.vertical, 9).background(Capsule().fill(Sig.accentGradient))
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
    let folder: DeskFolder; let userFolder: String?; let count: Int; let lassoMode: Bool
    let livingDesk: Bool; let onToggle3D: () -> Void
    let onLasso: () -> Void; let onTidy: () -> Void; let onZoom: () -> Void
    var body: some View {
        HStack(spacing: 10) {
            HStack(spacing: 7) {
                Image(systemName: userFolder == nil ? folder.icon : "folder.fill").font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.accent)
                Text(userFolder ?? folder.label).font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                if count > 0 { Text("\(count)").font(.system(size: 11, weight: .bold)).foregroundStyle(Sig.faint)
                    .padding(.horizontal, 6).padding(.vertical, 2).background(Capsule().fill(Sig.s3)) }
            }
            Spacer()
            pill("cube.fill", livingDesk ? "3D" : "2D", onToggle3D, on: livingDesk)
            if !livingDesk {
                pill("lasso", "Select", onLasso, on: lassoMode)
                pill("arrow.up.left.and.arrow.down.right", "Fit", onZoom)
                pill("square.grid.2x2.fill", "Tidy", onTidy)
            }
        }.padding(.horizontal, 18).padding(.top, 14)
    }
    private func pill(_ icon: String, _ label: String, _ action: @escaping () -> Void, on: Bool = false) -> some View {
        Button(action: action) {
            HStack(spacing: 5) { Image(systemName: icon).font(.system(size: 11, weight: .bold)); Text(label).font(.system(size: 12, weight: .bold)) }
                .foregroundStyle(on ? .white : Sig.text).padding(.horizontal, 11).padding(.vertical, 7)
                .background(Capsule().fill(on ? AnyShapeStyle(Sig.accentGradient) : AnyShapeStyle(Sig.s3)))
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
            if folder == .knowledge {
                Text("A knowledge base classifies what you file into it.\nMake one, then lasso cards and File them in.")
                    .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.muted).multilineTextAlignment(.center)
            } else if folder != .models {
                Text("Tap the mic to record — it lands here as a card\nyou can fling, arrange, and tidy.")
                    .font(.system(size: 13, weight: .medium)).foregroundStyle(Sig.muted).multilineTextAlignment(.center)
            }
        }.frame(width: 320)
    }
}

struct ContentUnavailable: View {
    let text: String
    var body: some View { Text(text).font(.system(size: 14, weight: .semibold)).foregroundStyle(Sig.muted).frame(maxWidth: .infinity, maxHeight: .infinity) }
}

// A meeting output opened to read in full — the body is rendered (markdown), copyable.
struct OutputWindowView: View {
    let title: String; let icon: String; let text: String
    @State private var copied = false
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 9) {
                Image(systemName: icon).font(.system(size: 13, weight: .bold)).foregroundStyle(Sig.accent)
                Text(title).font(.system(size: 15, weight: .heavy)).foregroundStyle(Sig.text).lineLimit(1)
                Spacer()
                Button {
                    #if canImport(UIKit)
                    UIPasteboard.general.string = text
                    #endif
                    tactile(); withAnimation { copied = true }
                } label: {
                    HStack(spacing: 5) { Image(systemName: copied ? "checkmark" : "doc.on.doc")
                        Text(copied ? "Copied" : "Copy").font(.system(size: 12, weight: .bold)) }
                        .foregroundStyle(copied ? Sig.local : Sig.muted)
                }
            }.padding(.horizontal, 18).padding(.top, 16).padding(.bottom, 10)
            ScrollView {
                Text(LocalizedStringKey(text)).font(.system(size: 14, weight: .regular)).foregroundStyle(Sig.text)
                    .textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 18).padding(.bottom, 22)
            }
        }.frame(maxWidth: .infinity, maxHeight: .infinity).background(Sig.s1)
    }
}

// MARK: - The window layer: apps open ON the desk (draggable / layered / closeable), not as pushed screens

struct OutputDoc { let title: String; let icon: String; let body: String }

enum DeskWindowKind: Equatable {
    case meeting(String), capture, models
    case output(id: String, title: String, icon: String, body: String)   // a meeting output, opened to read in full
    var title: String {
        switch self {
        case .meeting: return "Meeting"; case .capture: return "Record"; case .models: return "Models"
        case .output(_, let t, _, _): return t
        }
    }
    var icon: String {
        switch self {
        case .meeting: return "doc.text.fill"; case .capture: return "mic.fill"; case .models: return "cpu.fill"
        case .output(_, _, let i, _): return i
        }
    }
}

struct DeskWindowItem: Identifiable, Equatable {
    let id: String
    var kind: DeskWindowKind
    var offset: CGSize
    var z: Double
    var maximized: Bool = false
}

struct DeskWindowChrome<Content: View>: View {
    @Binding var item: DeskWindowItem
    let desk: CGSize
    let onClose: () -> Void
    let onFront: () -> Void
    @ViewBuilder var content: () -> Content
    @State private var dragBase: CGSize?

    private var size: CGSize {
        item.maximized ? CGSize(width: max(280, desk.width - 28), height: max(360, desk.height - 28))
                       : CGSize(width: min(desk.width - 48, 480), height: min(desk.height - 96, 660))
    }
    var body: some View {
        let s = size
        VStack(spacing: 0) {
            titleBar
            Rectangle().fill(Sig.line).frame(height: 1)
            NavigationStack { content() }                       // own nav context so the app's internal links/toolbars work
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .tint(Sig.accent)
        }
        .frame(width: s.width, height: s.height)
        .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Sig.s1))
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(Sig.topHairline, lineWidth: 1))
        .shadow(color: .black.opacity(0.5), radius: 30, y: 16)
        .position(x: desk.width / 2 + (item.maximized ? 0 : item.offset.width),
                  y: desk.height / 2 + (item.maximized ? 0 : item.offset.height))
        .onTapGesture { onFront() }
    }
    private var titleBar: some View {
        HStack(spacing: 10) {
            Button(action: onClose) { Circle().fill(Color(hex: 0xFF5F57)).frame(width: 13, height: 13)
                .overlay(Image(systemName: "xmark").font(.system(size: 7, weight: .black)).foregroundStyle(.black.opacity(0.5))) }
            Image(systemName: item.kind.icon).font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.accent)
            Text(item.kind.title).font(.system(size: 14, weight: .heavy)).foregroundStyle(Sig.text)
            Spacer()
            Button { withAnimation(.spring(response: 0.32, dampingFraction: 0.82)) { item.maximized.toggle() } } label: {
                Image(systemName: item.maximized ? "arrow.down.right.and.arrow.up.left" : "arrow.up.left.and.arrow.down.right")
                    .font(.system(size: 12, weight: .bold)).foregroundStyle(Sig.muted)
            }
        }
        .padding(.horizontal, 14).frame(height: 44)
        .background(LinearGradient(colors: [Sig.s2, Sig.s1], startPoint: .top, endPoint: .bottom))
        .contentShape(Rectangle())
        .gesture(
            DragGesture(minimumDistance: 2)
                .onChanged { v in
                    if dragBase == nil { dragBase = item.offset; onFront() }
                    let nx = (dragBase?.width ?? 0) + v.translation.width
                    let ny = (dragBase?.height ?? 0) + v.translation.height
                    item.offset = CGSize(width: min(max(nx, -desk.width / 2), desk.width / 2),
                                         height: min(max(ny, -desk.height / 2 + 30), desk.height / 2))
                    item.maximized = false
                }
                .onEnded { _ in dragBase = nil }
        )
    }
}
