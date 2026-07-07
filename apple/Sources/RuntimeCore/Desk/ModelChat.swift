import Foundation
import Contracts

/// HSM-15-13 — a mesh model manifest becomes a person you can open. The chat IS a
/// recipe chat: one transient persona pinned to the desktop profile that runs the
/// model, through the same `DioRecipeChat`/`callLLMTurn` path — the thread persists
/// under the persona's id, grounding rides free, no parallel chat surface. Pure and
/// host-testable; the caller supplies the resolved profile id.
public enum ModelChat {

    /// The conversation key — also the transient persona's id. Node-scoped so two
    /// nodes serving the same model name keep separate threads.
    public static func threadId(node: String, model: String) -> String {
        "modelchat:\(node):\(model)"
    }

    public static func isModelChat(_ recipeId: String) -> Bool {
        recipeId.hasPrefix("modelchat:")
    }

    /// The label a model chat wears for where it runs ("your desktop" for the hub).
    public static func nodeLabel(_ node: String) -> String {
        node == "desktop" ? "your desktop" : node
    }

    /// The transient persona: named after the model, pinned to the profile that
    /// runs it, no standing context of its own (grounding is the conversation's).
    public static func persona(manifest: ModelManifest, profileId: String) -> RecipeRecord {
        RecipeRecord(id: threadId(node: manifest.node, model: manifest.name),
                     name: manifest.name, avatar: "p5", role: nodeLabel(manifest.node),
                     systemPrompt: "", userTemplate: "{input}", manualContext: "",
                     useZoneContext: false, kb: "", profileId: profileId)
    }
}
