import Foundation
import Contracts

/// HSM-14 — The Workbench engine. A **user-defined intelligence workflow**: pick a SOURCE (what the
/// model reads), chain a few STEPS (lenses / extractions / transforms — the "basic set of logic"),
/// and send the result to an OUTPUT. A deliberately *linear pipeline* (not a free node graph) so the
/// builder has crushing usability — every workflow reads top-to-bottom and is impossible to wire
/// wrong. Pure + Codable + host-tested here; the gamified visual canvas binds to this model, and the
/// App runs it through the configured `ILLMProvider` (on-device or LAN endpoint).
public enum WorkflowSource: String, Codable, Sendable, CaseIterable {
    case fullTranscript    // the whole meeting
    case tackedMoments     // only the moments you tacked (HSM-8-03 marks)
    case selection         // a highlighted span

    public var label: String {
        switch self {
        case .fullTranscript: return "Full transcript"
        case .tackedMoments:  return "Tacked moments"
        case .selection:      return "Selected text"
        }
    }
    public var glyph: String {
        switch self {
        case .fullTranscript: return "text.alignleft"
        case .tackedMoments:  return "pin.fill"
        case .selection:      return "selection.pin.in.out"
        }
    }
}

/// What a step reads as its input — the meeting source, or the output of the step above it. The
/// custom `llmCall` block uses this to be wired into the pipeline.
public enum WorkflowInput: String, Codable, Sendable, CaseIterable {
    case meeting        // the workflow's SOURCE (full transcript / tacked moments / selection)
    case previousStep   // the output of the step directly above

    public var label: String { self == .meeting ? "the meeting" : "the previous step" }
}

/// One step in the pipeline. The curated blocks (lens / extract / summarize / rewrite / filter) are
/// first-class, AND there's a fully custom **`llmCall`** — your own prompt over a chosen input — so a
/// workflow isn't limited to the presets. The custom node is what makes this a real builder.
public enum WorkflowStep: Codable, Sendable, Equatable, Identifiable {
    case lens(MIRProfile)                                   // surface through a meeting lens
    case extract(ArtifactType)                             // draft a specific artifact type
    case summarize                                         // condense to a tight summary
    case rewrite(tone: String)                             // restate in a tone
    case keepIf(String)                                    // basic filter: keep items mentioning a keyword
    case llmCall(name: String, prompt: String, input: WorkflowInput)   // CUSTOM: your prompt, your input

    public var id: String { label + "·" + String(describing: self).prefix(40) }

    public var label: String {
        switch self {
        case .lens(let p):    return "Lens · \(p.rawValue.capitalized)"
        case .extract(let t): return "Extract · \(t.rawValue)"
        case .summarize:      return "Summarize"
        case .rewrite(let t): return "Rewrite · \(t)"
        case .keepIf(let k):  return "Keep if · \(k)"
        case .llmCall(let n, _, _): return n.isEmpty ? "LLM call" : n
        }
    }
    public var glyph: String {
        switch self {
        case .lens:      return "camera.filters"
        case .extract:   return "doc.text.magnifyingglass"
        case .summarize: return "text.append"
        case .rewrite:   return "pencil.and.outline"
        case .keepIf:    return "line.3.horizontal.decrease.circle"
        case .llmCall:   return "terminal.fill"
        }
    }
    /// Whether this is the fully custom LLM-call node (the builder treats it specially).
    public var isCustom: Bool { if case .llmCall = self { return true }; return false }
}

/// Where the pipeline's result goes.
public enum WorkflowOutput: String, Codable, Sendable, CaseIterable {
    case artifacts   // reviewable artifact cards (the default)
    case note        // a single note on the meeting
    case slack       // propose → approve → send (reuses the existing connector path)

    public var label: String {
        switch self {
        case .artifacts: return "Artifact cards"
        case .note:      return "A note"
        case .slack:     return "Send to Slack"
        }
    }
    public var glyph: String {
        switch self {
        case .artifacts: return "rectangle.stack.fill"
        case .note:      return "note.text"
        case .slack:     return "paperplane.fill"
        }
    }
    /// Outputs that leave the device (so the UI can show the egress reality).
    public var isEgress: Bool { self == .slack }
}

/// A complete, named, user-defined workflow.
public struct Workflow: Identifiable, Codable, Sendable, Equatable {
    public var id: UUID
    public var name: String
    public var source: WorkflowSource
    public var steps: [WorkflowStep]
    public var output: WorkflowOutput

    public init(id: UUID = UUID(), name: String, source: WorkflowSource,
                steps: [WorkflowStep], output: WorkflowOutput) {
        self.id = id
        self.name = name
        self.source = source
        self.steps = steps
        self.output = output
    }

    /// A workflow runs only if it has at least one step (a source + output alone does nothing).
    public var isRunnable: Bool { !steps.isEmpty }

    /// A human-readable, top-to-bottom plan — the sentence the builder shows so the workflow is
    /// never a mystery: "Full transcript → Lens · Delivery → Summarize → Artifact cards".
    public var plan: String {
        ([source.label] + steps.map(\.label) + [output.label]).joined(separator: "  →  ")
    }

    /// The artifact types this workflow will produce, derived from its extract/lens steps — what a
    /// run will surface (so the canvas can preview it, like the generation theater's constellation).
    public func producedTypes(default base: [ArtifactType]) -> [ArtifactType] {
        var out: [ArtifactType] = []
        for step in steps {
            switch step {
            case .extract(let t): out.append(t)
            case .lens(let p):    out.append(contentsOf: MIRRouter.baseEmphasis[p] ?? [])
            default: break
            }
        }
        var seen = Set<ArtifactType>(), ordered: [ArtifactType] = []
        for t in out where seen.insert(t).inserted { ordered.append(t) }
        return ordered.isEmpty ? base : ordered
    }
}

/// The starter workflows the Workbench ships with — one tap to a useful pipeline, the on-ramp to
/// building your own. (The "absolute crushing usability" entry point: don't start from blank.)
public enum WorkflowPresets {
    public static let all: [Workflow] = [
        Workflow(name: "Decisions & owners", source: .fullTranscript,
                 steps: [.lens(.delivery), .extract(.decisions), .extract(.actionItems)], output: .artifacts),
        Workflow(name: "What I flagged", source: .tackedMoments,
                 steps: [.extract(.actionItems), .extract(.riskRegister)], output: .artifacts),
        Workflow(name: "Exec summary → Slack", source: .fullTranscript,
                 steps: [.summarize, .rewrite(tone: "executive")], output: .slack),
        Workflow(name: "Risks only", source: .fullTranscript,
                 steps: [.lens(.incident), .extract(.riskRegister), .keepIf("risk")], output: .artifacts),
        Workflow(name: "Custom: open questions", source: .fullTranscript,
                 steps: [.llmCall(name: "Open questions",
                                  prompt: "From {input}, list the unresolved questions raised but not answered. One per line, no preamble.",
                                  input: .meeting)],
                 output: .note),
    ]
}
