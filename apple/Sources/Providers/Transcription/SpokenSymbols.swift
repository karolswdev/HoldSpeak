import Foundation

/// HSM-18-04 — the spoken-symbol dictionary, a faithful port of `holdspeak/text_processor.py`
/// (Phase 59). Turns spoken punctuation/format commands into symbols ("new line" -> a newline,
/// "open paren" -> "(", "hello period" -> "hello.") on DICTATION output. It is applied on the
/// dictation path only, NEVER to verbatim meeting transcripts (where "the period of the project"
/// must stay words).
///
/// Built-in tables plus the user's symbols are merged into ONE combined longest-first pass with
/// user-wins precedence: a user entry with the same spoken phrase as a built-in replaces it (the
/// phrase is dropped from every table first, then inserted into its attach mode's table). With no
/// user entries the output is byte-identical to the built-ins. Pure + testable.
public struct SpokenSymbols: Sendable {
    /// A user-defined symbol. `attach` is "left" | "right" | "both" | "none" (default), matching
    /// the hub's spoken-symbol dictionary shape. Codable so the editor persists the
    /// list (HSM-18-04); the shape matches the hub's `spoken_symbols` entries.
    public struct UserSymbol: Sendable, Equatable, Codable {
        public let spoken: String
        public let symbol: String
        public let attach: String
        public init(spoken: String, symbol: String, attach: String = "none") {
            self.spoken = spoken
            self.symbol = symbol
            self.attach = attach
        }
    }

    /// The persisted user dictionary (HSM-18-04): plain JSON in UserDefaults under
    /// `userSymbolsKey`, loaded at the dictation fill site so every speak-to-fill
    /// pass honors the user's entries. Empty/absent = built-ins only, byte-identical.
    public static let userSymbolsKey = "hs.dictate.usersymbols"

    public static func loadUserSymbols(defaults: UserDefaults = .standard) -> [UserSymbol] {
        guard let data = defaults.data(forKey: userSymbolsKey) else { return [] }
        return (try? JSONDecoder().decode([UserSymbol].self, from: data)) ?? []
    }

    public static func saveUserSymbols(_ symbols: [UserSymbol], defaults: UserDefaults = .standard) {
        defaults.set((try? JSONEncoder().encode(symbols)) ?? Data("[]".utf8), forKey: userSymbolsKey)
    }

    /// The configured processor: built-ins + the persisted user dictionary.
    public static func configured(defaults: UserDefaults = .standard) -> SpokenSymbols {
        SpokenSymbols(userSymbols: loadUserSymbols(defaults: defaults))
    }

    /// Removes the space BEFORE (attaches to the previous word): "hello period" -> "hello."
    public static let attachLeft: [String: String] = [
        "period": ".", "full stop": ".", "comma": ",", "question mark": "?",
        "exclamation mark": "!", "exclamation point": "!", "colon": ":", "semicolon": ";",
        "close quote": "\"", "end quote": "\"", "unquote": "\"",
        "close paren": ")", "close parenthesis": ")",
    ]
    /// Removes the space AFTER (attaches to the next word): "open quote hello" -> "\"hello"
    public static let attachRight: [String: String] = [
        "open quote": "\"", "open paren": "(", "open parenthesis": "(",
    ]
    /// Removes the space on BOTH sides: "self dash aware" -> "self-aware"
    public static let attachBoth: [String: String] = ["dash": "-", "hyphen": "-"]
    /// Newline commands (surrounding spaces removed).
    public static let newlines: [String: String] = [
        "new line": "\n", "newline": "\n", "new paragraph": "\n\n",
    ]

    private let left: [String: String]
    private let right: [String: String]
    private let both: [String: String]
    private let news: [String: String]
    private let plain: [String: String]

    public init(userSymbols: [UserSymbol] = []) {
        var l = Self.attachLeft, r = Self.attachRight, b = Self.attachBoth, n = Self.newlines
        var p: [String: String] = [:]
        for entry in userSymbols {
            let spoken = entry.spoken.trimmingCharacters(in: .whitespaces).lowercased()
            let symbol = entry.symbol
            guard !spoken.isEmpty, !symbol.isEmpty else { continue }
            // user wins: drop the phrase from every table before inserting
            l[spoken] = nil; r[spoken] = nil; b[spoken] = nil; n[spoken] = nil; p[spoken] = nil
            switch entry.attach.lowercased() {
            case "left": l[spoken] = symbol
            case "right": r[spoken] = symbol
            case "both": b[spoken] = symbol
            default: p[spoken] = symbol
            }
        }
        left = l; right = r; both = b; news = n; plain = p
    }

    /// Apply all spoken-symbol substitutions. One combined pass, longest command first across
    /// every table (so a short built-in "colon" never eats the inside of a longer phrase).
    public func process(_ text: String) -> String {
        guard !text.isEmpty else { return text }
        var entries: [(cmd: String, rep: String, mode: String)] = []
        for (c, r) in plain { entries.append((c, r, "plain")) }
        for (c, r) in left { entries.append((c, r, "left")) }
        for (c, r) in right { entries.append((c, r, "right")) }
        for (c, r) in both { entries.append((c, r, "both")) }
        for (c, r) in news { entries.append((c, r, "newline")) }
        entries.sort { $0.cmd.count > $1.cmd.count }

        var out = text
        for e in entries {
            let escaped = NSRegularExpression.escapedPattern(for: e.cmd)
            let pattern: String
            switch e.mode {
            case "left": pattern = "\\s*\\b\(escaped)\\b"        // remove space before
            case "right": pattern = "\\b\(escaped)\\b\\s*"       // remove space after
            case "plain": pattern = "\\b\(escaped)\\b"           // spacing preserved
            default: pattern = "\\s*\\b\(escaped)\\b\\s*"        // both / newline
            }
            guard let re = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]) else { continue }
            // the replacement is LITERAL text, never a regex template ($ / backslash must not be special)
            let template = NSRegularExpression.escapedTemplate(for: e.rep)
            let range = NSRange(out.startIndex..., in: out)
            out = re.stringByReplacingMatches(in: out, options: [], range: range, withTemplate: template)
        }
        return out
    }
}
