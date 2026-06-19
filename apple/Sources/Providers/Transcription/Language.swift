import Foundation

// HSM-3-03: the Whisper language registry, vendored at PARITY with the desktop
// (holdspeak/languages.py, Phase 59). GENERATED — do not hand-edit; regenerate
// via `uv run python apple/scripts/gen-languages.py`. "auto" is the default and
// normalizes to nil (Whisper's own per-utterance detection).

public enum WhisperLanguageError: Error, Equatable {
    case unknown(String)
}

public enum WhisperLanguage {
    /// 100 codes -> English name, as Whisper's tokenizer declares them.
    public static let names: [String: String] = [
        "en": "English",
        "zh": "Chinese",
        "de": "German",
        "es": "Spanish",
        "ru": "Russian",
        "ko": "Korean",
        "fr": "French",
        "ja": "Japanese",
        "pt": "Portuguese",
        "tr": "Turkish",
        "pl": "Polish",
        "ca": "Catalan",
        "nl": "Dutch",
        "ar": "Arabic",
        "sv": "Swedish",
        "it": "Italian",
        "id": "Indonesian",
        "hi": "Hindi",
        "fi": "Finnish",
        "vi": "Vietnamese",
        "he": "Hebrew",
        "uk": "Ukrainian",
        "el": "Greek",
        "ms": "Malay",
        "cs": "Czech",
        "ro": "Romanian",
        "da": "Danish",
        "hu": "Hungarian",
        "ta": "Tamil",
        "no": "Norwegian",
        "th": "Thai",
        "ur": "Urdu",
        "hr": "Croatian",
        "bg": "Bulgarian",
        "lt": "Lithuanian",
        "la": "Latin",
        "mi": "Maori",
        "ml": "Malayalam",
        "cy": "Welsh",
        "sk": "Slovak",
        "te": "Telugu",
        "fa": "Persian",
        "lv": "Latvian",
        "bn": "Bengali",
        "sr": "Serbian",
        "az": "Azerbaijani",
        "sl": "Slovenian",
        "kn": "Kannada",
        "et": "Estonian",
        "mk": "Macedonian",
        "br": "Breton",
        "eu": "Basque",
        "is": "Icelandic",
        "hy": "Armenian",
        "ne": "Nepali",
        "mn": "Mongolian",
        "bs": "Bosnian",
        "kk": "Kazakh",
        "sq": "Albanian",
        "sw": "Swahili",
        "gl": "Galician",
        "mr": "Marathi",
        "pa": "Punjabi",
        "si": "Sinhala",
        "km": "Khmer",
        "sn": "Shona",
        "yo": "Yoruba",
        "so": "Somali",
        "af": "Afrikaans",
        "oc": "Occitan",
        "ka": "Georgian",
        "be": "Belarusian",
        "tg": "Tajik",
        "sd": "Sindhi",
        "gu": "Gujarati",
        "am": "Amharic",
        "yi": "Yiddish",
        "lo": "Lao",
        "uz": "Uzbek",
        "fo": "Faroese",
        "ht": "Haitian Creole",
        "ps": "Pashto",
        "tk": "Turkmen",
        "nn": "Nynorsk",
        "mt": "Maltese",
        "sa": "Sanskrit",
        "lb": "Luxembourgish",
        "my": "Myanmar",
        "bo": "Tibetan",
        "tl": "Tagalog",
        "mg": "Malagasy",
        "as": "Assamese",
        "tt": "Tatar",
        "haw": "Hawaiian",
        "ln": "Lingala",
        "ha": "Hausa",
        "ba": "Bashkir",
        "jw": "Javanese",
        "su": "Sundanese",
        "yue": "Cantonese",
    ]

    public static var count: Int { names.count }

    private static let nameToCode: [String: String] = {
        var m = [String: String]()
        for (code, name) in names { m[name.lowercased()] = code }
        return m
    }()

    /// Normalize a configured language to a Whisper code, or nil for auto.
    /// Accepts nil / "" / "auto" (-> nil), a code ("pl"), or an English name
    /// ("Polish"). Throws `.unknown` for anything else, so a bad setting fails
    /// honestly instead of surprising a transcription later.
    public static func normalize(_ value: String?) throws -> String? {
        guard let raw = value?.trimmingCharacters(in: .whitespacesAndNewlines),
              !raw.isEmpty, raw.lowercased() != "auto" else { return nil }
        let lower = raw.lowercased()
        if names[lower] != nil { return lower }
        if let code = nameToCode[lower] { return code }
        throw WhisperLanguageError.unknown(raw)
    }

    public static func isValid(_ value: String?) -> Bool {
        (try? normalize(value)) != nil || (value ?? "auto").trimmingCharacters(
            in: .whitespacesAndNewlines).lowercased() == "auto"
            || (value ?? "").isEmpty
    }
}
