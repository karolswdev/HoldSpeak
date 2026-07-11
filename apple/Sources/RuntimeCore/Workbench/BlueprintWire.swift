import Foundation
import Contracts

// HSM-22-01 — the graph travels: lower a `Blueprint` to the canonical `graph_json`
// wire. ONE coder produces the wire (the shared `HoldSpeakContracts` encoder:
// snake_case keys, the tagged-union kind shape incl. `{"extract":{"_0":…}}`), and the
// hub's `workflow_graph.linearize()` parses exactly that — pinned by the committed
// golden fixtures (`contracts/fixtures/blueprint-*.json`) that a Swift test
// regenerates and a hub pytest feeds byte-for-byte into the linearizer.

public enum BlueprintWireError: Error, Equatable {
    /// The encoded wire failed to re-parse as JSON (should be impossible; surfaced
    /// rather than swallowed so a coder regression is loud).
    case unparsable
}

public extension Blueprint {
    /// The canonical `graph_json` bytes for this Blueprint (snake_case, stable key
    /// order so the golden fixture is byte-comparable).
    func graphJSONData() throws -> Data {
        let encoder = HoldSpeakContracts.encoder()
        encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
        return try encoder.encode(self)
    }

    /// The wire as a `JSONValue`, ready for `WorkflowDefinition.graphJson`.
    ///
    /// Decoded with a PLAIN `JSONDecoder` on purpose: the wire keys are already
    /// snake_case from the canonical encoder, and `JSONValue` captures keys verbatim —
    /// running the snake_case-converting decoder here would mangle them back.
    func graphJSONValue() throws -> JSONValue {
        let data = try graphJSONData()
        guard let value = try? JSONDecoder().decode(JSONValue.self, from: data) else {
            throw BlueprintWireError.unparsable
        }
        return value
    }

    /// This Blueprint as a syncable `WorkflowDefinition` (the desk's workflow
    /// primitive): `graphJson` carries the graph; `prompt` stays the caller's
    /// prompt-only compatibility text; a host must never lower an unsupported graph to it.
    func workflowDefinition(id: String? = nil, prompt: String? = nil,
                            createdAt: Date = Date(), updatedAt: Date = Date()) throws -> WorkflowDefinition {
        var definition = WorkflowDefinition(id: id ?? self.id.uuidString.lowercased(),
                                            name: name, prompt: prompt,
                                            createdAt: createdAt, updatedAt: updatedAt)
        definition.graphJson = try graphJSONValue()
        return definition
    }
}
