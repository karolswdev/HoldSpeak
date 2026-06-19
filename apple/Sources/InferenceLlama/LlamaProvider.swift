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

    public func complete(prompt: String) async throws -> String {
        // Apply the chat template, then generate. `getCompletion` expects an
        // already-templated input (it does not re-run preprocess).
        let templated = llm.preprocess(prompt, [], .none)
        return await llm.getCompletion(from: templated)
    }
}
