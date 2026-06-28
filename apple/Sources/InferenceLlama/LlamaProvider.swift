import Foundation
import LLM
import Providers

public enum LlamaProviderError: Error, Equatable {
    case modelLoadFailed(path: String)
}

/// HSM-5-02 — the on-device (charter Mode A) `ILLMProvider`, backed by llama.cpp
/// through LLM.swift (the HSM-5-01 engine pick). Loads a GGUF by path and returns a
/// completion with **no network** — the fully-local path.
///
/// The native engine lives only in this target; the domain (Contracts/RuntimeCore)
/// depends on the `ILLMProvider` seam, never on llama.cpp — so Mode A is swappable
/// for Mode B/C (`OpenAIEndpointProvider`) without touching the core.
///
/// A `final class` with `@unchecked Sendable`: the underlying `LLM` is a
/// non-Sendable reference type, so it can't live behind an `actor` (calling its
/// nonisolated async methods would risk a data race). Generation is serial — the
/// artifact engine drives it one call at a time, and `LLM` itself guards
/// reentrancy — so single-owner sequential use is safe.
public final class LlamaProvider: ILLMProvider, @unchecked Sendable {
    private let llm: LLM

    /// - Parameters:
    ///   - modelPath: absolute path to a local `.gguf`.
    ///   - template: the model's chat template (default ChatML — Qwen/Llama-3 style).
    ///   - maxTokenCount: context budget (clamped to the model's trained context).
    public init(modelPath: String,
                template: Template = .chatML(),
                maxTokenCount: Int32 = 2048) throws {
        guard let llm = LLM(from: URL(fileURLWithPath: modelPath),
                            template: template,
                            maxTokenCount: maxTokenCount) else {
            throw LlamaProviderError.modelLoadFailed(path: modelPath)
        }
        self.llm = llm
    }

    /// Build a provider that picks the model's chat template from its filename — so a
    /// downloaded/imported Gemma, Llama-3, Mistral or Qwen is prompted in its OWN format
    /// instead of a one-size-fits-all ChatML (wrong markers = degraded output). Prefer this
    /// over the raw init at every call site that loads a user-chosen model.
    public static func make(modelPath: String, maxTokenCount: Int32 = 2048) throws -> LlamaProvider {
        try LlamaProvider(modelPath: modelPath,
                          template: autoTemplate(for: modelPath),
                          maxTokenCount: maxTokenCount)
    }

    /// Map a GGUF filename to its chat template. Families are detected by the conventional
    /// tokens model authors keep in their filenames; unknown ⇒ ChatML (the safe, common default).
    public static func autoTemplate(for modelPath: String) -> Template {
        let n = (modelPath as NSString).lastPathComponent.lowercased()
        if n.contains("gemma")                                           { return .gemma }
        if n.contains("qwen")                                            { return .chatML() }   // Qwen = ChatML
        if n.contains("mistral") || n.contains("mixtral") || n.contains("nemo") { return .mistral }
        if n.contains("phi-3") || n.contains("phi3") || n.contains("phi-4") || n.contains("phi4") { return phi }
        if n.contains("llama-3") || n.contains("llama3") || n.contains("meta-llama-3") { return llama3 }
        return .chatML()
    }

    /// Llama-3/3.1/3.2 header format (the bundled `.llama()` preset is Llama-**2** `[INST]`,
    /// which is wrong for the Llama-3 line). BOS is added by the tokenizer, so no prefix here.
    static let llama3 = Template(
        system: ("<|start_header_id|>system<|end_header_id|>\n\n", "<|eot_id|>"),
        user:   ("<|start_header_id|>user<|end_header_id|>\n\n", "<|eot_id|>"),
        bot:    ("<|start_header_id|>assistant<|end_header_id|>\n\n", "<|eot_id|>"),
        stopSequence: "<|eot_id|>",
        systemPrompt: nil
    )

    /// Phi-3/Phi-4 turn format.
    static let phi = Template(
        system: ("<|system|>\n", "<|end|>\n"),
        user:   ("<|user|>\n", "<|end|>\n"),
        bot:    ("<|assistant|>\n", "<|end|>\n"),
        stopSequence: "<|end|>",
        systemPrompt: nil
    )

    public func complete(prompt: String) async throws -> String {
        // One-shot completion. NOTE: LLM.swift accumulates KV context across
        // `getCompletion` calls (it's built for chat) and never clears it, so a single
        // instance must NOT be reused for independent completions — the 2nd+ call starves
        // for context (`noJSON`), and clearing it mid-flight races the decoder (crash).
        // The caller therefore uses a FRESH provider per inference; see the on-device
        // generation loop. Apply the chat template, then generate (`getCompletion`
        // expects already-templated input — it does not re-run preprocess).
        let templated = llm.preprocess(prompt, [], .none)
        return await llm.getCompletion(from: templated)
    }
}
