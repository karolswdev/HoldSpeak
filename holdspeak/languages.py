"""HS-59-01: the Whisper language registry, vendored.

A frozen copy of the language codes Whisper's tokenizer accepts, so the
config/settings boundary can validate a `model.language` value without
importing a transcription backend (mlx-whisper / faster-whisper are heavy,
optional, and must never load at config time).

``"auto"`` is HoldSpeak's sentinel for Whisper's own per-utterance language
detection, which is today's behavior and the default; it normalizes to
``None`` so the backends receive no language at all (byte-identical calls).
"""

from __future__ import annotations

from typing import Optional

__all__ = ["WHISPER_LANGUAGES", "normalize_language", "language_choices"]

#: code -> English name, as Whisper's tokenizer declares them.
WHISPER_LANGUAGES: dict[str, str] = {
    "en": "English", "zh": "Chinese", "de": "German", "es": "Spanish",
    "ru": "Russian", "ko": "Korean", "fr": "French", "ja": "Japanese",
    "pt": "Portuguese", "tr": "Turkish", "pl": "Polish", "ca": "Catalan",
    "nl": "Dutch", "ar": "Arabic", "sv": "Swedish", "it": "Italian",
    "id": "Indonesian", "hi": "Hindi", "fi": "Finnish", "vi": "Vietnamese",
    "he": "Hebrew", "uk": "Ukrainian", "el": "Greek", "ms": "Malay",
    "cs": "Czech", "ro": "Romanian", "da": "Danish", "hu": "Hungarian",
    "ta": "Tamil", "no": "Norwegian", "th": "Thai", "ur": "Urdu",
    "hr": "Croatian", "bg": "Bulgarian", "lt": "Lithuanian", "la": "Latin",
    "mi": "Maori", "ml": "Malayalam", "cy": "Welsh", "sk": "Slovak",
    "te": "Telugu", "fa": "Persian", "lv": "Latvian", "bn": "Bengali",
    "sr": "Serbian", "az": "Azerbaijani", "sl": "Slovenian", "kn": "Kannada",
    "et": "Estonian", "mk": "Macedonian", "br": "Breton", "eu": "Basque",
    "is": "Icelandic", "hy": "Armenian", "ne": "Nepali", "mn": "Mongolian",
    "bs": "Bosnian", "kk": "Kazakh", "sq": "Albanian", "sw": "Swahili",
    "gl": "Galician", "mr": "Marathi", "pa": "Punjabi", "si": "Sinhala",
    "km": "Khmer", "sn": "Shona", "yo": "Yoruba", "so": "Somali",
    "af": "Afrikaans", "oc": "Occitan", "ka": "Georgian", "be": "Belarusian",
    "tg": "Tajik", "sd": "Sindhi", "gu": "Gujarati", "am": "Amharic",
    "yi": "Yiddish", "lo": "Lao", "uz": "Uzbek", "fo": "Faroese",
    "ht": "Haitian Creole", "ps": "Pashto", "tk": "Turkmen",
    "nn": "Nynorsk", "mt": "Maltese", "sa": "Sanskrit",
    "lb": "Luxembourgish", "my": "Myanmar", "bo": "Tibetan",
    "tl": "Tagalog", "mg": "Malagasy", "as": "Assamese", "tt": "Tatar",
    "haw": "Hawaiian", "ln": "Lingala", "ha": "Hausa", "ba": "Bashkir",
    "jw": "Javanese", "su": "Sundanese", "yue": "Cantonese",
}

#: name (lowercase) -> code, so "polish" validates as well as "pl".
_NAME_TO_CODE = {name.lower(): code for code, name in WHISPER_LANGUAGES.items()}


def normalize_language(value: Optional[str]) -> Optional[str]:
    """Normalize a configured language to a Whisper code, or None for auto.

    Accepts ``None``, ``""``, ``"auto"`` (auto-detect, the default), a code
    (``"pl"``), or an English language name (``"Polish"``). Raises
    ``ValueError`` with an actionable message for anything else, so the
    settings write fails honestly instead of surprising a dictation later.
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("", "auto"):
        return None
    if text in WHISPER_LANGUAGES:
        return text
    if text in _NAME_TO_CODE:
        return _NAME_TO_CODE[text]
    raise ValueError(
        f"Unknown language: {value!r}. Use 'auto', a Whisper language code "
        "(e.g. 'pl', 'de'), or a language name (e.g. 'Polish')."
    )


def language_choices() -> list[dict[str, str]]:
    """The settings UI's option list: auto first, then names A-Z."""
    options = [{"code": "auto", "name": "Auto-detect"}]
    options.extend(
        {"code": code, "name": name}
        for code, name in sorted(WHISPER_LANGUAGES.items(), key=lambda kv: kv[1])
    )
    return options
