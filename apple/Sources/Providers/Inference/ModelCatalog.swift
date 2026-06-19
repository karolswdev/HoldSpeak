import Foundation

/// HSM-5-03 — the pinned model artifacts. Maps each per-device tier
/// (`InferenceModel`) to a concrete GGUF: the Hugging Face repo, the quantization,
/// and the on-disk filename. These pin the HSM-5-01 named models (Llama-3.2-3B /
/// Llama-3.1-8B Q4_K_M); 12B+ is the experimental, plugged-in-only tier.
public struct ModelArtifact: Sendable, Equatable {
    public let tier: InferenceModel
    public let displayName: String
    /// Hugging Face repo ("owner/name") the GGUF is pulled from.
    public let huggingFaceRepo: String
    /// Quantization tag (matches LLM.swift's `Quantization` raw value, e.g. "Q4_K_M").
    public let quantization: String
    /// Stable on-disk filename the store resolves by (the downloader normalizes to this).
    public let fileName: String

    public init(tier: InferenceModel, displayName: String,
                huggingFaceRepo: String, quantization: String, fileName: String) {
        self.tier = tier
        self.displayName = displayName
        self.huggingFaceRepo = huggingFaceRepo
        self.quantization = quantization
        self.fileName = fileName
    }
}

public enum ModelCatalog {
    /// One pinned artifact per tier. Exact repos are the HSM-5-03 "pin the model
    /// artifacts" decision; all Q4_K_M GGUF per the shipping default.
    public static let artifacts: [InferenceModel: ModelArtifact] = [
        .fourB: ModelArtifact(
            tier: .fourB, displayName: "Llama 3.2 3B Instruct (Q4_K_M)",
            huggingFaceRepo: "bartowski/Llama-3.2-3B-Instruct-GGUF",
            quantization: "Q4_K_M", fileName: "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        .eightB: ModelArtifact(
            tier: .eightB, displayName: "Llama 3.1 8B Instruct (Q4_K_M)",
            huggingFaceRepo: "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
            quantization: "Q4_K_M", fileName: "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"),
        .twelveBPlus: ModelArtifact(
            tier: .twelveBPlus, displayName: "Mistral Nemo 12B Instruct (Q4_K_M)",
            huggingFaceRepo: "bartowski/Mistral-Nemo-Instruct-2407-GGUF",
            quantization: "Q4_K_M", fileName: "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf"),
    ]

    public static func artifact(for tier: InferenceModel) -> ModelArtifact {
        artifacts[tier]!   // every tier is catalogued; missing = programmer error
    }

    /// The artifact a device defaults to, per the per-device policy (4B iPhone / 8B iPad).
    public static func defaultArtifact(for device: DeviceClass) -> ModelArtifact {
        artifact(for: InferenceModelPolicy.defaultModel(for: device))
    }
}
