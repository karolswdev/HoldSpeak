import Foundation
import Contracts

/// Turns raw LLM text into a validated Phase-0 contract value. HSM-5-04 — the
/// bridge between "a model produced text" and "intelligence is contract-shaped".
/// On-device models drift from a requested shape (prose, code fences), so this
/// extracts the JSON, decodes it through the contract `Codable` (which enforces
/// the schema: enums, required fields), and offers a bounded repair-retry.
///
/// Constrained decoding (grammar) where an engine supports it is an engine-specific
/// optimization layered on top later; this validate-and-repair path is the
/// engine-agnostic floor.
public enum StructuredOutputError: Error, Equatable {
    case noJSON
    case exhausted
}

public enum StructuredOutput {

    /// Pull a JSON object/array out of possibly-fenced or prose-wrapped model text.
    public static func extractJSON(from raw: String) -> String? {
        var s = raw
        if s.contains("```") {
            let parts = s.components(separatedBy: "```")
            if parts.count >= 2 {
                var block = parts[1]
                // Drop a leading language-tag line (e.g. "json") if present.
                if let nl = block.firstIndex(of: "\n") {
                    let firstLine = block[block.startIndex..<nl].trimmingCharacters(in: .whitespaces)
                    if !firstLine.contains("{") && !firstLine.contains("[") {
                        block = String(block[block.index(after: nl)...])
                    }
                }
                s = block
            }
        }
        let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
        if let o = t.firstIndex(of: "{"), let c = t.lastIndex(of: "}"), o < c { return String(t[o...c]) }
        if let o = t.firstIndex(of: "["), let c = t.lastIndex(of: "]"), o < c { return String(t[o...c]) }
        return nil
    }

    /// Extract + decode a contract value from raw model text.
    public static func decode<T: Decodable>(
        _ type: T.Type, from raw: String,
        using decoder: JSONDecoder = HoldSpeakContracts.decoder()
    ) throws -> T {
        guard let json = extractJSON(from: raw) else { throw StructuredOutputError.noJSON }
        return try decoder.decode(type, from: Data(json.utf8))
    }

    /// Ask an `ILLMProvider` for structured output, decoding to `T`. On a parse/
    /// validation failure, re-prompt with a repair hint, up to `maxAttempts`.
    public static func generate<T: Decodable>(
        _ type: T.Type, prompt: String, using provider: ILLMProvider,
        maxAttempts: Int = 3,
        decoder: JSONDecoder = HoldSpeakContracts.decoder()
    ) async throws -> T {
        precondition(maxAttempts >= 1)
        var lastError: Error = StructuredOutputError.exhausted
        for attempt in 0..<maxAttempts {
            let p = attempt == 0
                ? prompt
                : prompt + "\n\nReturn ONLY valid JSON matching the schema — no prose, no fences."
            let raw = try await provider.complete(prompt: p)
            do { return try decode(type, from: raw, using: decoder) }
            catch { lastError = error }
        }
        throw lastError
    }
}
