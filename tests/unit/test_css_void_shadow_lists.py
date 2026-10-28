"""Guard: no shadow or filter list holds a token whose value is `none`.

`box-shadow: var(--wb-raised), 0 1px 2px #0003` with `--wb-raised: none`
computes to `none, 0 1px 2px #0003`. That list is invalid, so the browser
draws NO shadow at all (found by delight slice 5, #1560). The same holds for
`text-shadow`, and for a `filter` chain where a token is `none` next to
another filter function.

The scan reads every custom property definition in web/src CSS (each theme
block counts: a token that is `none` in any theme is void there), resolves
token chains, and fails with file:line and the token name.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "web" / "src"

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_DEF = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]*)")
_DECL = re.compile(r"(?<![A-Za-z0-9_-])(box-shadow|text-shadow|filter)\s*:\s*([^;{}]*)", re.I)
_TS_DECL = re.compile(
    r"(?<![A-Za-z0-9_-])(boxShadow|textShadow|filter|box-shadow|text-shadow)[\"']?\s*:\s*[\"'`]([^\"'`]*)[\"'`]"
)


def _css_files() -> list[Path]:
    return sorted(p for p in WEB_SRC.rglob("*.css") if "_parked" not in p.parts)


def _script_files() -> list[Path]:
    out = [p for ext in ("*.ts", "*.tsx") for p in WEB_SRC.rglob(ext)]
    return sorted(p for p in out if "_parked" not in p.parts and "__tests__" not in p.parts)


def _strip_comments(text: str) -> str:
    # Keep newlines so offsets still map to lines.
    return _COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def _definitions(files: list[Path]) -> dict[str, set[str]]:
    defs: dict[str, set[str]] = {}
    for path in files:
        for m in _DEF.finditer(_strip_comments(path.read_text(encoding="utf-8"))):
            value = m.group(2).replace("!important", "").strip()
            defs.setdefault(m.group(1), set()).add(value)
    return defs


def _void_tokens(defs: dict[str, set[str]]) -> set[str]:
    """Tokens that compute to `none` in at least one definition (chains resolved)."""
    void = {name for name, values in defs.items() if "none" in {v.lower() for v in values}}
    changed = True
    while changed:
        changed = False
        for name, values in defs.items():
            if name in void:
                continue
            for value in values:
                m = re.fullmatch(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)", value)
                if m and m.group(1) in void:
                    void.add(name)
                    changed = True
                    break
    return void


def _split_top(value: str, sep: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur).strip())
    return [p for p in parts if p]


def _bare_token(item: str) -> str | None:
    m = re.fullmatch(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,.*)?\)", item.strip(), re.S)
    return m.group(1) if m else None


def scan() -> list[str]:
    files = _css_files()
    void = _void_tokens(_definitions(files))
    hits: list[str] = []
    sources = [(p, _DECL) for p in files] + [(p, _TS_DECL) for p in _script_files()]
    for path, pattern in sources:
        text = path.read_text(encoding="utf-8")
        if pattern is _DECL:
            text = _strip_comments(text)
        for m in pattern.finditer(text):
            prop = m.group(1).lower().replace("boxshadow", "box-shadow").replace("textshadow", "text-shadow")
            value = m.group(2).replace("!important", "").strip()
            line = text.count("\n", 0, m.start()) + 1
            rel = path.relative_to(ROOT)
            if prop == "filter":
                items = _split_top(value, " ")
            else:
                items = _split_top(value, ",")
            if len(items) < 2:
                continue
            for item in items:
                token = _bare_token(item)
                if token and token in void:
                    hits.append(f"{rel}:{line}: {prop} list holds {token} (value none)")
    return hits


def test_no_shadow_list_holds_a_void_token() -> None:
    hits = scan()
    assert not hits, (
        "A shadow/filter list that holds a token whose value is `none` is invalid; "
        "the browser draws no shadow. Drop the token or give it a real value:\n"
        + "\n".join(hits)
    )


def test_scan_catches_the_known_shape(tmp_path: Path) -> None:
    css = ":root{--void:none;--chain:var(--void)}\n.a{box-shadow: var(--chain), 0 1px 2px red}\n"
    defs = {}
    for m in _DEF.finditer(css):
        defs.setdefault(m.group(1), set()).add(m.group(2).strip())
    void = _void_tokens(defs)
    assert void == {"--void", "--chain"}
    items = _split_top("var(--chain), 0 1px 2px red", ",")
    assert _bare_token(items[0]) == "--chain"
