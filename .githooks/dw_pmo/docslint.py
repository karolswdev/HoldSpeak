"""Documentation lint: internal links, anchors, images, runnable snippets.

Docs get the same verification-over-trust treatment as code: every
relative link and image in every Markdown file must resolve, every
``#anchor`` must match a real heading (GitHub slug rules), every image
must carry alt text, and quickstart blocks marked
``<!-- snippet: name [prep=…] [cwd=…] -->`` are extracted and executed
against throwaway fixtures. Findings print as greppable
``ERROR <file>:<line>: <issue>`` lines. Stdlib only.

External URLs are deliberately not checked (liveness polling is flaky
in CI). A line can opt out with ``<!-- docs-lint: ignore -->`` on the
same or the preceding line; a file can opt out with
``<!-- docs-lint: skip-file -->`` near the top.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXCLUDED_DIRS = {".git", ".tmp", "node_modules", "__pycache__", ".worktrees"}

LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^()]*(?:\([^()]*\)[^()]*)*)\)")
REF_DEF_RE = re.compile(r"^\s*\[([^\]]+)\]:\s+(\S+)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SNIPPET_RE = re.compile(r"<!--\s*snippet:\s*([\w-]+)((?:\s+[\w-]+=[^\s>]+)*)\s*-->")
IGNORE_PRAGMA = "docs-lint: ignore"
SKIP_FILE_PRAGMA = "docs-lint: skip-file"


def iter_markdown(root: Path) -> "list[Path]":
    files = []
    for path in sorted(root.rglob("*.md")):
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDED_DIRS:
            continue
        files.append(path)
    return files


def mask_code(text: str) -> str:
    """Blank out fenced blocks, inline code, and HTML comments while
    preserving line structure, so links inside them are not linted."""
    lines = text.split("\n")
    fence = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        opener = re.match(r"(`{3,}|~{3,})", stripped)
        if fence is None and opener:
            fence = opener.group(1)[0] * 3
            lines[i] = ""
        elif fence is not None:
            if opener and opener.group(1).startswith(fence):
                fence = None
            lines[i] = ""
    masked = "\n".join(lines)
    masked = re.sub(r"`+[^`\n]+`+", lambda m: " " * len(m.group(0)), masked)
    masked = re.sub(
        r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), masked, flags=re.S
    )
    return masked


def strip_heading_markup(text: str) -> str:
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    return text


def github_slug(heading: str) -> str:
    slug = strip_heading_markup(heading).strip().lower()
    slug = re.sub(r"[^\w\- ]", "", slug)
    return slug.replace(" ", "-")


def heading_slugs(text: str) -> "set[str]":
    seen: "dict[str, int]" = {}
    slugs = set()
    fence = None
    for line in text.split("\n"):
        stripped = line.lstrip()
        opener = re.match(r"(`{3,}|~{3,})", stripped)
        if fence is None and opener:
            fence = opener.group(1)[0] * 3
            continue
        if fence is not None:
            if opener and opener.group(1).startswith(fence):
                fence = None
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = github_slug(m.group(2))
        n = seen.get(base, 0)
        seen[base] = n + 1
        slugs.add(base if n == 0 else "%s-%d" % (base, n))
    return slugs


def _split_target(target: str) -> "tuple[str, str]":
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    else:
        target = target.split()[0] if target.split() else ""
    path, _, anchor = target.partition("#")
    return path, anchor


class Linter:
    def __init__(self, root: Path):
        self.root = root
        self._slug_cache: "dict[Path, set[str]]" = {}

    def slugs_for(self, path: Path) -> "set[str]":
        if path not in self._slug_cache:
            self._slug_cache[path] = heading_slugs(path.read_text(encoding="utf-8"))
        return self._slug_cache[path]

    def lint_file(self, path: Path) -> "list[str]":
        rel = path.relative_to(self.root)
        text = path.read_text(encoding="utf-8")
        raw_lines = text.split("\n")
        if SKIP_FILE_PRAGMA in "\n".join(raw_lines[:5]):
            return []
        issues = []
        masked = mask_code(text)
        for i, line in enumerate(masked.split("\n")):
            lineno = i + 1
            raw = raw_lines[i]
            prev = raw_lines[i - 1] if i else ""
            if IGNORE_PRAGMA in raw or IGNORE_PRAGMA in prev:
                continue
            matches = list(LINK_RE.finditer(line))
            for m in matches:
                is_image, alt, target = m.group(1), m.group(2), m.group(3)
                for issue in self.check_link(path, is_image == "!", alt, target):
                    issues.append("ERROR %s:%d: %s" % (rel, lineno, issue))
            ref = REF_DEF_RE.match(line)
            if ref and not matches:
                for issue in self.check_link(path, False, ref.group(1), ref.group(2)):
                    issues.append("ERROR %s:%d: %s" % (rel, lineno, issue))
        return issues

    def check_link(self, source: Path, is_image: bool, alt: str, target: str) -> "list[str]":
        issues = []
        path_part, anchor = _split_target(target)
        if is_image and not alt.strip():
            issues.append("image missing alt text: %s" % (target or "(empty)"))
        if not path_part and not anchor:
            issues.append("empty link target")
            return issues
        if SCHEME_RE.match(path_part) or path_part.startswith("//"):
            return issues  # external URL: liveness deliberately unchecked
        if path_part:
            if path_part.startswith("/"):
                resolved = self.root / path_part.lstrip("/")
            else:
                resolved = source.parent / path_part
            try:
                resolved = resolved.resolve()
            except OSError:
                issues.append("unresolvable link target: %s" % target)
                return issues
            if not resolved.exists():
                kind = "missing image" if is_image else "broken link"
                issues.append("%s: %s" % (kind, target))
                return issues
        else:
            resolved = source
        if anchor and resolved.suffix == ".md" and resolved.is_file():
            if anchor.lower() not in self.slugs_for(resolved):
                issues.append("broken anchor: %s" % target)
        return issues


def lint(root: Path) -> "tuple[list[str], int]":
    linter = Linter(root)
    files = iter_markdown(root)
    issues = []
    for path in files:
        issues.extend(linter.lint_file(path))
    return issues, len(files)


# ── runnable snippets ─────────────────────────────────────────────────


def extract_snippets(root: Path) -> "list[dict]":
    """Find ``<!-- snippet: name [k=v …] -->`` markers, each of which
    must be immediately followed (blank lines allowed) by a bash/sh
    fence whose body is the runnable text."""
    snippets = []
    for path in iter_markdown(root):
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = SNIPPET_RE.search(line)
            if not m:
                continue
            name, attr_text = m.group(1), m.group(2)
            attrs = dict(a.split("=", 1) for a in attr_text.split())
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or not re.match(r"```(bash|sh)\b", lines[j].strip()):
                raise SystemExit(
                    "ERROR %s:%d: snippet marker '%s' is not followed by a bash fence"
                    % (path.relative_to(root), i + 1, name)
                )
            body = []
            j += 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1
            snippets.append(
                {
                    "file": str(path.relative_to(root)),
                    "line": i + 1,
                    "name": name,
                    "attrs": attrs,
                    "body": "\n".join(body),
                }
            )
    return snippets


def _sh(args: "list[str]", cwd: Path) -> None:
    subprocess.run(
        args, cwd=str(cwd), check=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )


def _prepare_fixture(root: Path, prep: str, target: Path) -> None:
    """Fixture ladder: repo → installed → intaken → report, plus
    clone (a fresh clone of this repository, for contributor docs).
    Each rung is exactly the documented earlier quickstart steps."""
    if prep == "clone":
        _sh(["git", "clone", "-q", str(root), str(target)], cwd=root)
    else:
        _sh(["git", "init", "-q", str(target)], cwd=root)
    _sh(["git", "-C", str(target), "config", "user.name", "Docs Smoke"], cwd=root)
    _sh(["git", "-C", str(target), "config", "user.email", "docs@smoke.test"], cwd=root)
    if prep in ("repo", "clone"):
        return
    pmo = root / "pmo-roadmap"
    _sh([str(pmo / "install.sh"), str(target), "--skip-bootstrap"], cwd=pmo)
    if prep == "installed":
        return
    _sh(
        [
            str(pmo / "bootstrap" / "session-intake.sh"), str(target),
            "--project-name", "My Project", "--project-slug", "myproject",
            "--project-prefix", "MP", "--no-prompt",
        ],
        cwd=pmo,
    )
    if prep == "intaken":
        return
    if prep != "report":
        raise SystemExit("ERROR unknown snippet prep '%s'" % prep)
    _sh(
        [
            str(pmo / "bootstrap" / "adopt-project.sh"), str(target),
            "--project-name", "My Project", "--project-slug", "myproject",
            "--project-prefix", "MP", "--require-intake",
        ],
        cwd=pmo,
    )
    report = target / "pm" / "roadmap" / "myproject" / "adoption" / "adoption-discovery.md"
    report.write_text(
        "# Adoption Discovery\n\n"
        "- **Roadmap root:** pm/roadmap/myproject/\n\n"
        "## Proposed Phase Index\n\n"
        "| Phase | Title | Goal | Why now |\n|---|---|---|---|\n"
        "| 0 | Stabilize | Land the rails. | Foundation. |\n\n"
        "## Proposed First Stories\n\n"
        "| ID | Title | Acceptance evidence | Notes |\n|---|---|---|---|\n"
        "| MP-0-01 | First story | Captured test run. | - |\n",
        encoding="utf-8",
    )


def run_snippets(root: Path) -> "list[str]":
    issues = []
    snippets = extract_snippets(root)
    for snip in snippets:
        prep = snip["attrs"].get("prep", "repo")
        cwd_kind = snip["attrs"].get("cwd", "root")
        tmp = Path(tempfile.mkdtemp(prefix="dw-docs-smoke."))
        target = tmp / "target-project"
        label = "%s snippet '%s'" % (snip["file"], snip["name"])
        try:
            try:
                _prepare_fixture(root, prep, target)
            except subprocess.CalledProcessError as exc:
                issues.append(
                    "ERROR %s: fixture prep '%s' failed (%s)" % (snip["file"], prep, exc)
                )
                continue
            body = (
                snip["body"]
                .replace("/path/to/delivery-workbench", str(root))
                .replace("/path/to/target-project", str(target))
                .replace("/path/to/project", str(target))
            )
            cwd = {"root": root, "pmo": root / "pmo-roadmap", "target": target}[cwd_kind]
            proc = subprocess.run(
                ["bash", "-e", "-c", body],
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                tail = "\n".join(proc.stdout.strip().split("\n")[-8:])
                issues.append(
                    "ERROR %s: snippet '%s' exited %d\n%s"
                    % (snip["file"], snip["name"], proc.returncode, tail)
                )
            else:
                print("ok: %s ran as printed" % label)
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)
    if not snippets:
        issues.append("ERROR no runnable snippets found: quickstart smoke has no coverage")
    return issues


def main(argv: "list[str]") -> int:
    root = Path(argv[argv.index("--root") + 1]).resolve() if "--root" in argv else Path.cwd()
    if "--snippets" in argv:
        issues = run_snippets(root)
        for issue in issues:
            print(issue)
        if issues:
            return 1
        print("docs-lint snippets: ok")
        return 0
    issues, count = lint(root)
    for issue in issues:
        print(issue)
    if issues:
        return 1
    print("docs-lint: ok (%d markdown files)" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
