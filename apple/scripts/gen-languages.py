#!/usr/bin/env python3
"""Generate apple/Sources/Providers/Transcription/Language.swift from the desktop
Whisper language registry (holdspeak/languages.py), so the Swift registry stays at
parity with desktop. Run from the repo root:  uv run python apple/scripts/gen-languages.py
"""
from pathlib import Path
from holdspeak.languages import WHISPER_LANGUAGES

OUT = Path("apple/Sources/Providers/Transcription/Language.swift")

entries = "\n".join(
    f'        {code!r}: {name!r},'.replace("'", '"')
    for code, name in WHISPER_LANGUAGES.items()
)

swift = f'''import Foundation

// HSM-3-03: the Whisper language registry, vendored at PARITY with the desktop
// (holdspeak/languages.py, Phase 59). GENERATED — do not hand-edit; regenerate
// via `uv run python apple/scripts/gen-languages.py`. "auto" is the default and
// normalizes to nil (Whisper's own per-utterance detection).

public enum WhisperLanguageError: Error, Equatable {{
    case unknown(String)
}}

public enum WhisperLanguage {{
    /// {len(WHISPER_LANGUAGES)} codes -> English name, as Whisper's tokenizer declares them.
    public static let names: [String: String] = [
{entries}
    ]

    public static var count: Int {{ names.count }}

    private static let nameToCode: [String: String] = {{
        var m = [String: String]()
        for (code, name) in names {{ m[name.lowercased()] = code }}
        return m
    }}()

    /// Normalize a configured language to a Whisper code, or nil for auto.
    /// Accepts nil / "" / "auto" (-> nil), a code ("pl"), or an English name
    /// ("Polish"). Throws `.unknown` for anything else, so a bad setting fails
    /// honestly instead of surprising a transcription later.
    public static func normalize(_ value: String?) throws -> String? {{
        guard let raw = value?.trimmingCharacters(in: .whitespacesAndNewlines),
              !raw.isEmpty, raw.lowercased() != "auto" else {{ return nil }}
        let lower = raw.lowercased()
        if names[lower] != nil {{ return lower }}
        if let code = nameToCode[lower] {{ return code }}
        throw WhisperLanguageError.unknown(raw)
    }}

    public static func isValid(_ value: String?) -> Bool {{
        (try? normalize(value)) != nil || (value ?? "auto").trimmingCharacters(
            in: .whitespacesAndNewlines).lowercased() == "auto"
            || (value ?? "").isEmpty
    }}
}}
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(swift)
print(f"wrote {OUT} with {len(WHISPER_LANGUAGES)} languages")
