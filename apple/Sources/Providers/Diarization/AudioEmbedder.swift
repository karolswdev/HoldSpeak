import Foundation
import Contracts

/// HSM-14-17 — the Core ML half of on-device diarization: a thin wrapper over the bundled
/// `AudioEmbed.mlmodelc`. The model (de-risked at cosine 0.99993 vs resemblyzer's `VoiceEncoder`)
/// bakes the librosa-matched mel front-end in, so it maps **one ~1.6s raw 16 kHz audio partial**
/// (`audio`, float32, shape `(1, 25440)`, in [-1, 1]) → a **256-dim L2-normalised speaker
/// embedding** (output feature `var_90`, shape `(1, 256)`). Swift does ZERO DSP — feed audio,
/// get an embedding. Compatible with the desktop's encoder, so cross-device identity stays open.
///
/// `import CoreML` is iOS/macOS only; the whole type is `#if canImport(CoreML)`-gated so the
/// pure RuntimeCore matcher still builds where Core ML is absent.

/// The number of samples in one partial the model expects (~1.59s at 16 kHz).
public let audioEmbedPartialSamples = 25_440

#if canImport(CoreML)
import CoreML

/// Loads the bundled model and embeds 1.6s audio partials. Inference is synchronous CPU/ANE work;
/// call it off the main thread (the `SpeakerDiarizer` runs it on a background task).
public final class AudioEmbedder: @unchecked Sendable {
    public static let outputFeatureName = "var_90"
    public static let inputFeatureName = "audio"

    private let model: MLModel

    /// Load `AudioEmbed.mlmodelc` from a bundle (the app's `Bundle.main` by default). Throws if the
    /// compiled model is missing from the bundle — surfaced so diarization degrades gracefully
    /// (segments keep their default speaker) rather than crashing capture.
    public init(bundle: Bundle = .main) throws {
        guard let url = bundle.url(forResource: "AudioEmbed", withExtension: "mlmodelc") else {
            throw AudioEmbedderError.modelMissing
        }
        let config = MLModelConfiguration()
        self.model = try MLModel(contentsOf: url, configuration: config)
    }

    /// Load from an explicit COMPILED model URL (an `AudioEmbed.mlmodelc`), rather than scanning a
    /// bundle. For a sideloaded / downloaded model (HSM-5-03 — the weights need not be app-bundled)
    /// and for the host diarization proof, which compiles the `.mlpackage` then loads it here. The
    /// `Bundle.main` path stays the app default.
    public init(compiledModelURL url: URL) throws {
        self.model = try MLModel(contentsOf: url, configuration: MLModelConfiguration())
    }

    /// Embed ONE 25 440-sample partial (float32 in [-1, 1]) → a 256-dim L2-normalised embedding.
    /// Pads/truncates defensively to the model's input length.
    public func embed(partial: [Float]) throws -> [Float] {
        let arr = try MLMultiArray(shape: [1, NSNumber(value: audioEmbedPartialSamples)], dataType: .float32)
        let ptr = arr.dataPointer.bindMemory(to: Float.self, capacity: audioEmbedPartialSamples)
        let n = Swift.min(partial.count, audioEmbedPartialSamples)
        partial.withUnsafeBufferPointer { src in
            ptr.update(from: src.baseAddress!, count: n)
        }
        if n < audioEmbedPartialSamples {
            for i in n..<audioEmbedPartialSamples { ptr[i] = 0 }
        }
        let input = try MLDictionaryFeatureProvider(dictionary: [Self.inputFeatureName: arr])
        let out = try model.prediction(from: input)
        guard let emb = out.featureValue(for: Self.outputFeatureName)?.multiArrayValue else {
            throw AudioEmbedderError.noOutput
        }
        let count = emb.count
        var result = [Float](repeating: 0, count: count)
        let outPtr = emb.dataPointer.bindMemory(to: Float.self, capacity: count)
        for i in 0..<count { result[i] = outPtr[i] }
        return result
    }
}

public enum AudioEmbedderError: Error, Sendable {
    case modelMissing
    case noOutput
}
#endif
