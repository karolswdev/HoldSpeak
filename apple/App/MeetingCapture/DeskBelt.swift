import SwiftUI

// HSM-26-02 — the delivery belt as a desk primitive (B4). The mission-control
// conveyor (each rails repo → its current phase → the stories riding it) drawn
// on the diorama STRICTLY from the BeltState contract (GET /api/missioncontrol/
// state, HSM-26-01). Read-only, byte-honest: a live rail shows its current
// phase and stories; an unreachable rail shows its honest state, never a
// fake-idle belt. The whole UI (canvas glyph, card, pull-out sections) is
// derived from this one declaration — the primitive never builds views.

struct BeltPrimitive: DeskPrimitive {
    let state: BeltState

    var id: String { "belt:mission-control" }
    var kind: PrimitiveKind { .workflow }            // a global tool on the desk
    var glyph: String { "rectangle.stack.fill" }     // the conveyor, an SF Symbol
    var isSymbol: Bool { true }
    var color: Color { DioPal.cobalt }
    var base: CGFloat { 122 }
    var title: String { "Mission Control" }

    private var liveRepos: [BeltRepo] { state.repos.filter { $0.status == "live" } }

    var subtitle: String {
        let n = liveRepos.count
        return n == 0 ? "no rails reachable" : "\(n) rail\(n == 1 ? "" : "s") · the delivery belt"
    }

    var preview: String? {
        if let p = liveRepos.first?.feed?.projects.first?.currentPhase {
            return "Phase \(p.number) · \(p.storiesDone ?? 0)/\(p.storiesTotal ?? 0)"
        }
        return liveRepos.isEmpty ? "rails unreachable" : "idle"
    }

    var sections: [PrimitiveSection] {
        var out: [PrimitiveSection] = []
        for repo in state.repos {
            guard repo.status == "live" else {
                // An honest lane: a repo that cannot answer says so, never an empty belt.
                out.append(.init(label: repo.name.uppercased(), tint: DioPal.muted,
                                 body: .text("✕ \(repo.status)" + (repo.detail.map { " — \($0)" } ?? ""))))
                continue
            }
            for proj in repo.feed?.projects ?? [] {
                if let phase = proj.currentPhase {
                    let head = "Phase \(phase.number)"
                        + (phase.title.map { " — \($0)" } ?? "")
                        + " · \(phase.storiesDone ?? 0)/\(phase.storiesTotal ?? 0)"
                    out.append(.init(label: proj.slug.uppercased(), tint: DioPal.cobalt, body: .text(head)))
                    let riding = proj.stories.filter { $0.phase == phase.number }
                    if !riding.isEmpty {
                        out.append(.init(label: "STORIES · \(riding.count)", tint: DioPal.accent,
                            body: .actions(riding.map { s in
                                let ev = (s.evidenceExists == true) ? " ·evidence" : ""
                                let next = (s.storyId == proj.nextStory?.storyId) ? " ·next" : ""
                                return ("\(statusMark(s.status)) \(s.storyId)  \(s.title ?? "")",
                                        s.status + ev + next)
                            })))
                    }
                }
                if let n = proj.warnings, n > 0 {
                    out.append(.init(label: "WARNINGS", tint: DioPal.muted, body: .text("⚠ \(n)")))
                }
            }
        }
        if out.isEmpty {
            out.append(.init(label: "BELT", tint: DioPal.muted,
                             body: .text("No rails configured on the paired desktop.")))
        }
        return out
    }

    // A read from the paired Mac's rails — Local + your desktop, never on-device alone.
    var egress: EgressScope { .mixed("your desktop") }

    private func statusMark(_ status: String) -> String {
        switch status {
        case "done", "complete", "closed", "shipped": return "●"
        case "in-progress": return "◐"
        case "blocked": return "⊘"
        case "ready": return "◔"
        default: return "○"
        }
    }
}

#if DEBUG
extension BeltPrimitive {
    /// A sim-seed sample so the belt renders on glass without a live hub
    /// (HS_DESK_BELT). Mirrors the real GET /api/missioncontrol/state shape.
    static func sampleState() -> BeltState {
        BeltState(repos: [
            BeltRepo(name: "holdspeak", path: "/repos/hs", status: "live", feed: BeltFeed(projects: [
                BeltProject(
                    slug: "holdspeak", prefix: "HS",
                    currentPhase: BeltPhase(number: 88, title: "The Rails-Aware Desk",
                                            status: "closed", storiesDone: 5, storiesTotal: 5),
                    nextStory: nil,
                    stories: [
                        BeltStory(storyId: "HS-88-03", title: "The ambient dw observer", status: "done", phase: 88, evidenceExists: true),
                        BeltStory(storyId: "HS-88-04", title: "The cross-machine reach", status: "done", phase: 88, evidenceExists: true),
                        BeltStory(storyId: "HS-88-05", title: "The walk, the docs, the close", status: "done", phase: 88, evidenceExists: true),
                    ],
                    warnings: 0)
            ])),
            BeltRepo(name: "delivery-workbench", path: "/repos/dw", status: "live", feed: BeltFeed(projects: [
                BeltProject(
                    slug: "work-log-automation", prefix: "WLA",
                    currentPhase: BeltPhase(number: 17, title: "Agent Sync",
                                            status: "open", storiesDone: 2, storiesTotal: 5),
                    nextStory: BeltStoryRef(storyId: "WLA-17-03", title: "The synth pack", status: "ready"),
                    stories: [
                        BeltStory(storyId: "WLA-17-01", title: "The persona recipe", status: "done", phase: 17, evidenceExists: true),
                        BeltStory(storyId: "WLA-17-02", title: "Sync the roster", status: "done", phase: 17, evidenceExists: true),
                        BeltStory(storyId: "WLA-17-03", title: "The synth pack", status: "ready", phase: 17, evidenceExists: false),
                        BeltStory(storyId: "WLA-17-04", title: "The audit trail", status: "in-progress", phase: 17, evidenceExists: false),
                    ],
                    warnings: 1)
            ])),
            BeltRepo(name: "aipi-lite", path: "/repos/aipi", status: "unavailable", detail: "no dw CLI"),
        ])
    }
}
#endif
