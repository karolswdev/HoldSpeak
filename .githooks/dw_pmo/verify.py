"""Range verification: re-derive gate rules from pushed history.

Implements the remote verification contract
(docs/remote-verification.md, WLA-8-01): everything the local gate
derives from HEAD-vs-index, this module re-derives from
first-parent-tree-vs-commit-tree over a commit range — same status
vocabulary, same filename grammars, same rule ids. Contract-fact
rules are attested-only (the contract never leaves the committing
clone) and are deliberately absent here; two trailer rules
(`trailer-missing`, `trailer-format`) exist only remotely because
locally the hooks stamp trailers by construction.

Scoping (the policy lives in the contract, not in per-sha
exceptions): only commits whose first-parent diff touches a
`pm/roadmap/` tree are examined, and only from the epoch onward —
auto-detected as the first commit in the walked range carrying a
`PMO-Contract-Digest:` trailer, pinnable via --epoch or
PMO_VERIFY_EPOCH. Merge commits get trailer checks only; their
constituent commits are walked individually. Shallow clones fail
loudly (exit 2): a truncated history must never verify silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import DONE_STATUSES, STORY_ID_RE
from .contract import story_id_from_blob
from .gitio import config_value, run_git, status_of

_ROADMAP_SEG_RE = re.compile(r"(?:^|/)pm/roadmap/")
_STORY_PATH_RE = re.compile(
    r"^(?P<phase_dir>(?:.*/)?pm/roadmap/[^/]+/phase-[^/]+)/story-(?P<num>\d+)-.*\.md$"
)
_EVIDENCE_PATH_RE = re.compile(
    r"^(?P<phase_dir>(?:.*/)?pm/roadmap/[^/]+/phase-[^/]+)/evidence-story-(?P<num>\d+)\.md$"
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"
_VALUE_SEP = "\x02"


@dataclass
class Violation:
    sha: str
    rule: str
    message: str


@dataclass
class CommitFacts:
    sha: str
    parents: list[str]
    story_trailer: list[str]
    digest_trailer: list[str]
    bundle_trailer: list[str]


@dataclass
class VerifyResult:
    ok: bool
    verified: int = 0
    pre_epoch_skipped: int = 0
    out_of_scope: int = 0
    epoch: str | None = None
    violations: list[Violation] = field(default_factory=list)
    commits: list[tuple[str, bool, list[Violation]]] = field(default_factory=list)
    error: str | None = None  # usage/git error → exit 2


def _is_shallow(root: Path) -> bool:
    out = run_git(root, "rev-parse", "--is-shallow-repository")
    return (out or "").strip() == "true"


def _resolve(root: Path, rev: str) -> str | None:
    out = run_git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    return out.strip() if out else None


def _default_branch_base(root: Path) -> str | None:
    """Merge-base of the default branch and HEAD, or None."""
    ref = (run_git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD") or "").strip()
    candidates = [ref] if ref else []
    candidates += ["refs/heads/main", "refs/heads/master"]
    head = _resolve(root, "HEAD")
    for cand in candidates:
        sha = _resolve(root, cand)
        if sha is None:
            continue
        if sha == head:
            return None  # on the default branch itself: nothing to add
        out = run_git(root, "merge-base", sha, "HEAD")
        if out:
            return out.strip()
    return None


def _walk(root: Path, range_spec: str) -> list[CommitFacts] | None:
    """Commits in the range, oldest first, with parents and trailers.

    One git invocation for the whole range. Fields are \\x1f-separated,
    records \\x1e-separated, and multiple values of one trailer key are
    \\x02-separated, so the three separators never collide.
    """
    fmt = (
        f"%H{_FIELD_SEP}%P{_FIELD_SEP}"
        f"%(trailers:key=PMO-Story,valueonly,separator=%x02)"
        f"{_FIELD_SEP}%(trailers:key=PMO-Contract-Digest,valueonly,separator=%x02)"
        f"{_FIELD_SEP}%(trailers:key=PMO-Bundle,valueonly,separator=%x02)"
        f"{_RECORD_SEP}"
    )
    out = run_git(root, "log", "--topo-order", "--reverse", f"--format={fmt}", range_spec)
    if out is None:
        return None
    commits: list[CommitFacts] = []
    for record in out.split(_RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(_FIELD_SEP)
        if len(parts) != 5:
            continue
        sha, parents_raw, story_raw, digest_raw, bundle_raw = parts
        commits.append(
            CommitFacts(
                sha=sha.strip(),
                parents=[p for p in parents_raw.strip().split() if p],
                story_trailer=_split_ids(_values(story_raw)),
                digest_trailer=_values(digest_raw),
                bundle_trailer=_values(bundle_raw),
            )
        )
    return commits


def _values(raw: str) -> list[str]:
    return [v.strip() for v in raw.split(_VALUE_SEP) if v.strip()]


def _split_ids(values: list[str]) -> list[str]:
    ids: list[str] = []
    for value in values:
        ids.extend(s.strip() for s in value.split(",") if s.strip())
    return ids


def _changed(root: Path, sha: str, parents: list[str]) -> list[tuple[str, str, str | None]]:
    """(status, path, old_path) from the first-parent diff."""
    if parents:
        out = run_git(root, "diff-tree", "-r", "-z", "-M", "--no-commit-id",
                      "--name-status", parents[0], sha)
    else:
        out = run_git(root, "diff-tree", "--root", "-r", "-z", "-M",
                      "--no-commit-id", "--name-status", sha)
    if out is None:
        return []
    tokens = out.split("\0")
    entries: list[tuple[str, str, str | None]] = []
    i = 0
    while i < len(tokens):
        status = tokens[i]
        if not status:
            i += 1
            continue
        kind = status[0]
        if kind in {"R", "C"}:
            old_path = tokens[i + 1] if i + 1 < len(tokens) else ""
            new_path = tokens[i + 2] if i + 2 < len(tokens) else ""
            if new_path:
                entries.append((kind, new_path, old_path))
            i += 3
        else:
            path = tokens[i + 1] if i + 1 < len(tokens) else ""
            if path:
                entries.append((kind, path, None))
            i += 2
    return entries


def _blob(root: Path, sha: str, path: str) -> str | None:
    return run_git(root, "show", f"{sha}:{path}")


def _story_status_in_tree(
    root: Path, sha: str, phase_dir: str, num: int
) -> tuple[str | None, str | None]:
    """Find the story file for (phase_dir, num) in the commit's tree."""
    out = run_git(root, "ls-tree", "-r", "--name-only", "-z", sha, "--", phase_dir)
    if out is None:
        return None, None
    for path in out.split("\0"):
        m = _STORY_PATH_RE.match(path)
        if m and m.group("phase_dir") == phase_dir and int(m.group("num")) == num:
            return path, status_of(_blob(root, sha, path))
    return None, None


def _check_commit(root: Path, commit: CommitFacts) -> tuple[bool, list[Violation]]:
    """(in_scope, violations) for one post-epoch commit."""
    sha = commit.sha
    short = sha[:7]

    # Merge commits are out of scope: their constituent commits are
    # walked individually, and synthetic merges (GitHub's PR merge
    # ref, merge-button commits) carry no trailers by construction.
    # Evil merges that smuggle roadmap content into the merge commit
    # itself are a documented limitation of v1.
    if len(commit.parents) > 1:
        return False, []

    entries = _changed(root, sha, commit.parents)
    touches_roadmap = any(
        _ROADMAP_SEG_RE.search(p) or (old and _ROADMAP_SEG_RE.search(old))
        for _s, p, old in entries
    )
    if not touches_roadmap:
        return False, []

    violations: list[Violation] = []

    def bad(rule: str, message: str) -> None:
        violations.append(Violation(short, rule, message))

    # Trailer presence and format (remote-only rules).
    if not commit.digest_trailer:
        bad("trailer-missing", "in-scope commit carries no PMO-Contract-Digest trailer")
    for digest in commit.digest_trailer:
        if not _DIGEST_RE.match(digest):
            bad("trailer-format", f"malformed PMO-Contract-Digest value {digest!r}")
    for sid in commit.story_trailer:
        if not STORY_ID_RE.match(sid):
            bad("trailer-format", f"malformed PMO-Story id {sid!r}")

    # Story flips: not-done in first parent → done-synonym in commit.
    story_entries: list[tuple[str, str, str | None, str, int]] = []
    evidence_entries: list[tuple[str, str, str, int]] = []
    for status, path, old_path in entries:
        m = _STORY_PATH_RE.match(path)
        if m:
            story_entries.append((status, path, old_path, m.group("phase_dir"), int(m.group("num"))))
        m = _EVIDENCE_PATH_RE.match(path)
        if m:
            evidence_entries.append((status, path, m.group("phase_dir"), int(m.group("num"))))
        if status == "R" and old_path:
            m_old = _EVIDENCE_PATH_RE.match(old_path)
            if m_old:
                evidence_entries.append(("D", old_path, m_old.group("phase_dir"), int(m_old.group("num"))))

    flipped: list[tuple[str, str, int, str | None]] = []  # path, phase_dir, num, story_id
    parent = commit.parents[0] if commit.parents else None
    for status, path, old_path, phase_dir, num in story_entries:
        if status == "D":
            continue
        blob = _blob(root, sha, path)
        new_status = status_of(blob)
        if new_status not in DONE_STATUSES:
            continue
        head_source = old_path if (status == "R" and old_path) else path
        old_status = status_of(_blob(root, parent, head_source)) if parent else None
        if old_status not in DONE_STATUSES:
            flipped.append((path, phase_dir, num, story_id_from_blob(blob)))

    flipped_keys = {(phase_dir, num) for _p, phase_dir, num, _sid in flipped}

    # atomicity: >1 flip requires a visible PMO-Bundle rationale.
    if len(flipped) > 1 and not commit.bundle_trailer:
        bad(
            "atomicity",
            f"{len(flipped)} stories flipped to done in one commit with no PMO-Bundle trailer",
        )

    # contract-story-mismatch: flipped ⊆ declared (PMO-Story trailer).
    if flipped and not commit.story_trailer:
        bad("trailer-missing", "story flip carries no PMO-Story trailer")
    else:
        for _path, _pd, _num, sid in flipped:
            if sid and sid not in commit.story_trailer:
                bad("contract-story-mismatch", f"flipped story {sid} not declared in PMO-Story trailer")

    # evidence-missing: every flip ships its evidence in the same commit.
    evidence_present = {(pd, num) for status, _p, pd, num in evidence_entries if status != "D"}
    for path, phase_dir, num, _sid in flipped:
        if (phase_dir, num) not in evidence_present:
            bad(
                "evidence-missing",
                f"story {path} flipped to done but evidence-story-{num:02d}.md is not in this commit",
            )

    # Reverse pairing.
    for status, path, phase_dir, num in evidence_entries:
        if status == "D":
            story_path, story_status = _story_status_in_tree(root, sha, phase_dir, num)
            if story_path is not None and story_status in DONE_STATUSES:
                bad(
                    "evidence-deletion-orphans-story",
                    f"evidence {path} deleted while story {story_path} remains done",
                )
            continue
        if status == "A":
            if (phase_dir, num) not in flipped_keys:
                bad(
                    "orphan-evidence",
                    f"evidence {path} added but no story-{num} in this phase flipped to done",
                )
            continue
        if (phase_dir, num) in flipped_keys:
            continue
        story_path, story_status = _story_status_in_tree(root, sha, phase_dir, num)
        if story_path is None or story_status not in DONE_STATUSES:
            bad(
                "orphan-evidence",
                f"evidence {path} changed but its story is not done in this commit's tree",
            )

    return True, violations


def run_verify(
    root: Path,
    range_spec: str | None = None,
    all_history: bool = False,
    epoch: str | None = None,
) -> VerifyResult:
    result = VerifyResult(ok=True)

    if range_spec and all_history:
        result.ok = False
        result.error = "pass either an explicit <base>..<head> range or --all, not both"
        return result

    if _is_shallow(root):
        result.ok = False
        result.error = (
            "shallow repository — history is truncated and first-parent diffs "
            "cannot be trusted; fetch full history (fetch-depth: 0) and retry"
        )
        return result

    if _resolve(root, "HEAD") is None:
        result.ok = False
        result.error = "no HEAD commit (not a git repository, or empty)"
        return result

    if range_spec is None:
        if all_history:
            range_spec = "HEAD"
        else:
            base = _default_branch_base(root)
            if base is None:
                result.verified = 0
                return result  # on the default branch: nothing branch-local to verify
            range_spec = f"{base}..HEAD"

    commits = _walk(root, range_spec)
    if commits is None:
        result.ok = False
        result.error = f"git could not walk range {range_spec!r}"
        return result

    epoch = epoch or config_value(root, "PMO_VERIFY_EPOCH")
    epoch_sha: str | None = None
    if epoch:
        epoch_sha = _resolve(root, epoch)
        if epoch_sha is None:
            result.ok = False
            result.error = f"cannot resolve epoch {epoch!r}"
            return result

    past_epoch = False
    for commit in commits:
        if not past_epoch:
            if epoch_sha is not None:
                past_epoch = commit.sha == epoch_sha or commit.sha.startswith(epoch_sha)
            else:
                past_epoch = bool(commit.digest_trailer)
            if past_epoch:
                result.epoch = commit.sha[:7]
        if not past_epoch:
            result.pre_epoch_skipped += 1
            continue
        in_scope, violations = _check_commit(root, commit)
        if not in_scope:
            result.out_of_scope += 1
            continue
        result.verified += 1
        result.commits.append((commit.sha[:7], in_scope, violations))
        result.violations.extend(violations)

    if result.violations:
        result.ok = False
    return result


def render_verify(result: VerifyResult) -> str:
    if result.error:
        return f"dw verify: error: {result.error}\n"
    lines = [f"ERROR {v.sha}: {v.rule}: {v.message}" for v in result.violations]
    if result.ok:
        lines.append(
            f"dw verify: ok ({result.verified} commits verified, "
            f"{result.pre_epoch_skipped} pre-epoch skipped)"
        )
    else:
        lines.append(
            f"dw verify: {len(result.violations)} violation(s) across "
            f"{result.verified} verified commit(s)"
        )
    return "\n".join(lines) + "\n"


def render_verify_porcelain(result: VerifyResult) -> str:
    lines = [
        f"verify={'pass' if result.ok else 'fail'}",
        f"verified={result.verified}",
        f"pre_epoch_skipped={result.pre_epoch_skipped}",
        f"out_of_scope={result.out_of_scope}",
        f"epoch={result.epoch or 'none'}",
    ]
    if result.error:
        lines.append(f"error={result.error}")
    for sha, _in_scope, violations in result.commits:
        lines.append(f"commit={sha}")
        lines.append(f"verdict={'pass' if not violations else 'fail'}")
        for v in violations:
            lines.append(f"rule={v.rule}")
            lines.append(f"message={v.message}")
    return "\n".join(lines) + "\n"
