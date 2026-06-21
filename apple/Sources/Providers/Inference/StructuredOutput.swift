import Foundation
import Contracts

/// Turns raw LLM text into a validated Phase-0 contract value. HSM-5-04 — the
/// bridge between "a model produced text" and "intelligence is contract-shaped".
/// On-device models drift from a requested shape (prose, code fences), so this
/// extracts the JSON, decodes it through the contract `Codable` (which enforces
/// the schema: enums, required fields), and offers a bounded repair-retry.
///
/// HSM-11-06 hardens the salvage: balanced extraction (not first-`{`-to-last-`}`),
/// truncation recovery, conservative repair of common 4B drift, and array unwrap —
/// so a well-fed model's occasional formatting drift no longer costs an artifact.
///
/// Constrained decoding (grammar) where an engine supports it is an engine-specific
/// optimization layered on top later; this validate-and-repair path is the
/// engine-agnostic floor.
public enum StructuredOutputError: Error, Equatable {
    case noJSON
    case exhausted
}

public enum StructuredOutput {

    /// Pull a JSON object/array out of possibly-fenced or prose-wrapped model text,
    /// then conservatively repair common on-device-model drift. Returns `nil` only when
    /// there is no JSON structure at all (so the repair-retry loop can re-prompt).
    public static func extractJSON(from raw: String) -> String? {
        let unfenced = stripFences(raw)
        guard let block = firstBalancedJSON(in: unfenced) else { return nil }
        return repair(block)
    }

    /// Extract + decode a contract value from raw model text. On a decode failure where
    /// the model wrapped the object in a one-element array, decode the inner object.
    public static func decode<T: Decodable>(
        _ type: T.Type, from raw: String,
        using decoder: JSONDecoder = HoldSpeakContracts.decoder()
    ) throws -> T {
        guard let json = extractJSON(from: raw) else { throw StructuredOutputError.noJSON }
        do {
            return try decoder.decode(type, from: Data(json.utf8))
        } catch {
            // Array unwrap: `[{…}]` → decode the inner object rather than failing.
            if let inner = firstObjectInsideArray(json) {
                return try decoder.decode(type, from: Data(inner.utf8))
            }
            throw error
        }
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
                : prompt + "\n\nReturn ONLY one valid JSON object matching the schema — no prose, no code fences, no trailing commas."
            let raw = try await provider.complete(prompt: p)
            do { return try decode(type, from: raw, using: decoder) }
            catch { lastError = error }
        }
        throw lastError
    }

    // MARK: - Extraction internals (HSM-11-06)

    /// Drop Markdown code fences, returning the first fenced body that contains a brace/
    /// bracket (dropping a leading `json` language-tag line). Falls back to the raw text.
    static func stripFences(_ s: String) -> String {
        guard s.contains("```") else { return s }
        let parts = s.components(separatedBy: "```")
        // Odd indices are the fenced bodies (between pairs of fences).
        for i in stride(from: 1, to: parts.count, by: 2) {
            var block = parts[i]
            if let nl = block.firstIndex(of: "\n") {
                let firstLine = block[block.startIndex..<nl].trimmingCharacters(in: .whitespaces)
                // A short tag line with no structure (e.g. "json") → drop it.
                if !firstLine.contains("{") && !firstLine.contains("[") && firstLine.count <= 12 {
                    block = String(block[block.index(after: nl)...])
                }
            }
            if block.contains("{") || block.contains("[") { return block }
        }
        return s
    }

    /// The FIRST complete, brace-balanced `{…}`/`[…]`, respecting strings + escapes — so
    /// trailing prose, a second object, or a `}`/`]` inside a string value don't break it.
    /// If the structure opens but is never closed (truncation), close the open string +
    /// the open brackets so a truncated-but-mostly-there value still decodes.
    static func firstBalancedJSON(in s: String) -> String? {
        let chars = Array(s)
        guard let start = chars.firstIndex(where: { $0 == "{" || $0 == "[" }) else { return nil }
        var stack: [Character] = []
        var inString = false
        var escaped = false
        var i = start
        while i < chars.count {
            let c = chars[i]
            if inString {
                if escaped { escaped = false }
                else if c == "\\" { escaped = true }
                else if c == "\"" { inString = false }
            } else {
                switch c {
                case "\"": inString = true
                case "{": stack.append("}")
                case "[": stack.append("]")
                case "}", "]":
                    if stack.last == c { stack.removeLast() }
                    if stack.isEmpty { return String(chars[start...i]) }
                default: break
                }
            }
            i += 1
        }
        // Truncated: never fully closed. Salvage — close an open string, then the brackets.
        guard !stack.isEmpty else { return nil }
        var salvage = String(chars[start...])
        if inString { salvage += "\"" }
        salvage += String(stack.reversed())
        return salvage
    }

    /// The first balanced `{…}` object found inside an array block — for unwrapping a
    /// model that returned `[{…}]` when one object was asked for.
    static func firstObjectInsideArray(_ s: String) -> String? {
        let chars = Array(s)
        guard chars.first == "[" else { return nil }
        guard let objStart = chars.firstIndex(of: "{") else { return nil }
        return firstBalancedJSON(in: String(chars[objStart...]))
    }

    // MARK: - Conservative repair (HSM-11-06)

    /// Smart quotes → straight, value-position Python literals → JSON, string-aware
    /// trailing-comma removal. None of these touch string *contents* by structure.
    static func repair(_ s: String) -> String {
        var t = s
        for (curly, straight) in [("\u{201C}", "\""), ("\u{201D}", "\""), ("\u{2018}", "'"), ("\u{2019}", "'")] {
            t = t.replacingOccurrences(of: curly, with: straight)
        }
        t = replaceValueLiteral(t, "True", "true")
        t = replaceValueLiteral(t, "False", "false")
        t = replaceValueLiteral(t, "None", "null")
        return removeTrailingCommas(t)
    }

    /// Replace a bare word in VALUE position only (preceded by `:`/`,`/`[` and optional
    /// whitespace, word-bounded) — so `"True"` in a string or `Truesy` text is untouched.
    private static func replaceValueLiteral(_ s: String, _ word: String, _ repl: String) -> String {
        guard let re = try? NSRegularExpression(pattern: "([\\:\\[,]\\s*)\(word)\\b") else { return s }
        let range = NSRange(s.startIndex..., in: s)
        return re.stringByReplacingMatches(in: s, range: range, withTemplate: "$1\(repl)")
    }

    /// Remove a comma that (outside any string) is followed only by whitespace then a
    /// closing `}`/`]`. String-aware, so a comma inside body text is never touched.
    private static func removeTrailingCommas(_ s: String) -> String {
        let chars = Array(s)
        var out: [Character] = []
        out.reserveCapacity(chars.count)
        var inString = false
        var escaped = false
        var i = 0
        while i < chars.count {
            let c = chars[i]
            if inString {
                out.append(c)
                if escaped { escaped = false }
                else if c == "\\" { escaped = true }
                else if c == "\"" { inString = false }
            } else if c == "\"" {
                inString = true; out.append(c)
            } else if c == "," {
                // Look ahead past whitespace for a closer.
                var j = i + 1
                while j < chars.count, chars[j] == " " || chars[j] == "\n" || chars[j] == "\t" || chars[j] == "\r" { j += 1 }
                if j < chars.count, chars[j] == "}" || chars[j] == "]" {
                    // Drop this comma (keep the whitespace + closer as-is).
                } else {
                    out.append(c)
                }
            } else {
                out.append(c)
            }
            i += 1
        }
        return String(out)
    }
}
