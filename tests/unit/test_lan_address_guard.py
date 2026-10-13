"""PHILO-17 (the test diet, push 2): no private LAN address ships in web text.

The owner's own LAN engine address (``192.168.1.43``) leaked into a field
placeholder once. A private address in shipped text tells every other user
about one machine on one network, and it reads as a real endpoint. This
guard reads every source file under ``web/src`` that ships (tests, test
wires, parked files and comments do not) and fails on any literal private
IPv4 address: ``10.0.0.0/8``, ``172.16.0.0/12``, ``192.168.0.0/16``.

An example address in a face uses a name (``server.local``), never a number.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "web" / "src"
SHIPPED = {".ts", ".tsx", ".css", ".json", ".html", ".md"}

_OCTET = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
PRIVATE = re.compile(
    r"(?<![\d.])(?:10\.{o}\.{o}\.{o}|192\.168\.{o}\.{o}|172\.(?:1[6-9]|2\d|3[01])\.{o}\.{o})(?![\d.]*\d)".format(o=_OCTET)
)
# A block comment, or a line comment that does not follow a colon (a URL's
# `//` keeps its line). Comments do not ship (the build strips them).
COMMENTS = re.compile(r"/\*.*?\*/|(?<![:\"'`\w])//[^\n]*", re.DOTALL)


def _shipped(path: Path) -> bool:
    rel = path.relative_to(WEB_SRC)
    parts = rel.parts
    if parts[0] in {"_parked", "test"} or "__tests__" in parts or "_parked" in parts:
        return False
    name = path.name
    return path.suffix in SHIPPED and not re.search(r"\.(test|spec)\.[jt]sx?$", name)


def private_hits(text: str, suffix: str) -> list[tuple[int, str]]:
    """(line, address) for each private address outside a comment."""
    if suffix in {".ts", ".tsx", ".css"}:
        # Keep the line numbers: a comment becomes the same count of newlines.
        text = COMMENTS.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return [(text.count("\n", 0, m.start()) + 1, m.group(0)) for m in PRIVATE.finditer(text)]


def test_no_private_lan_address_in_shipped_web_text() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{line}: {address}"
        for path in sorted(WEB_SRC.rglob("*"))
        if path.is_file() and _shipped(path)
        for line, address in private_hits(path.read_text(encoding="utf-8"), path.suffix)
    ]
    assert not offenders, (
        "a private LAN address ships in web text; use a name (server.local), "
        "never a real address:\n" + "\n".join(offenders)
    )


def test_the_reader_sees_an_address_and_skips_comments() -> None:
    """The guard can fail: a literal in code is seen, in all three ranges;
    the same literal in a comment, a public address, or a longer number is not."""
    code = 'const a = "http://192.168.1.43:8080/v1";\nconst b = `10.0.0.7`;\nconst c = "172.20.1.1";\n'
    assert [a for _, a in private_hits(code, ".tsx")] == ["192.168.1.43", "10.0.0.7", "172.20.1.1"]
    assert private_hits(code, ".tsx")[1][0] == 2
    commented = "// 10.0.0.0/8\n/* 192.168.1.43 */\nconst u = 'http://x.local'; // 172.16.0.1\n"
    assert private_hits(commented, ".ts") == []
    assert private_hits('const p = "172.32.0.1 8.8.8.8 110.0.0.1 10.0.0.1.5";', ".ts") == []
    assert private_hits('{"caller": "192.168.0.9"}', ".json") == [(1, "192.168.0.9")]
