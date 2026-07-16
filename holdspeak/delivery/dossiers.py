"""Evidence dossiers and safe asset access (HS-94-05).

PLATFORM-CONTRACT §5.3 made concrete on the hub side:

- the Delivery Workbench evidence manifest (``dw evidence manifest
  <project> <story> --json``) is the SOLE membership/path authority —
  HoldSpeak never composes a repository path from a client request;
- manifests are cached keyed by ``bundle_id`` with revision awareness:
  a changed index tree is a NEW bundle, and a request addressing a
  superseded bundle is answered from the cache with an honest
  ``bundle_changed`` marker (§13: preserve manifest metadata, request
  a new bundle) — never silently re-pointed at different bytes;
- bytes flow only through ``dw evidence asset`` (the counterpart's
  typed chokepoint), get re-hashed against the manifest's sha256, and
  every refusal stays typed: ``not_in_manifest`` / ``outside_root`` /
  ``symlink`` / ``absent`` / ``oversize`` / ``bundle_changed`` /
  ``hash_mismatch`` / ``unavailable`` / ``incompatible``;
- wire shapes carry asset IDs, roles, media types, sizes, and hashes —
  the manifest's server-side ``path`` field never leaves this module
  (§12.3, §13).

Grounding: :func:`hydrate_dossier_refs` resolves a dossier member ref
(``{source, project, kind, id}``) into the SAME capped
:class:`~holdspeak.grounding.GroundingBlock` the rails picker produces
(``grounding_rails.hydrate_rails_refs``): ``kind="rails:story"`` /
``"rails:evidence"``, text capped at ``GROUNDING_TRANSCRIPT_CAP`` with
the rail-object cut marker. Final wiring into the steer/ask compose
path belongs to HS-94-08; this is the adapter it calls.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from ..grounding import GROUNDING_TRANSCRIPT_CAP, GroundingBlock
from .registry import DeliveryRegistry

DOSSIER_SCHEMA = 1
PHASE_DOSSIER_SCHEMA = 1
EVIDENCE_SCHEMA_PROVEN = 1
DW_TIMEOUT_SECONDS = 30
DEFAULT_MAX_AGE_SECONDS = 15.0
DEFAULT_MAX_ENTRIES = 64

# Manifest member roles whose bodies a story dossier serves inline.
_DOC_ROLES = ("story_markdown", "evidence_markdown")

# dw's typed refusal codes, mapped to the HTTP status this hub answers
# with. `bundle_changed` and `hash_mismatch` are hub-detected (409);
# everything the manifest simply does not authorize is a 404.
REFUSAL_HTTP = {
    "not_found": 404,
    "not_in_manifest": 404,
    "outside_root": 404,
    "symlink": 404,
    "absent": 404,
    "oversize": 413,
    "bundle_changed": 409,
    "hash_mismatch": 409,
    "unavailable": 503,
    "incompatible": 503,
}


class DossierRefusal(Exception):
    """A typed, wire-safe refusal: ``code`` is one of REFUSAL_HTTP's
    keys, ``detail`` is classified (no paths, no argv, no stderr),
    and ``manifest`` optionally carries the cached metadata that must
    stay visible (§13: bundle changed / node offline)."""

    def __init__(
        self,
        code: str,
        detail: str,
        *,
        manifest: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.http_status = REFUSAL_HTTP.get(code, 500)
        self.manifest = manifest


# ── markdown safety ──────────────────────────────────────────────────

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HTML_COMMENT_RE = re.compile(r"<!--.*?(?:-->|$)", re.S)
_HTML_DANGEROUS_BLOCK_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b.*?(?:</\1\s*>|$)",
    re.I | re.S,
)
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9-]*(?:\s[^<>]*)?/?>")


def sanitize_markdown(text: str) -> str:
    """Markdown served as TEXT for the client to render — with raw
    HTML stripped server-side (story acceptance: safe Markdown, inert
    raw HTML). Fenced code blocks are preserved verbatim: captured
    output is data, not markup the client would execute."""
    out: list[str] = []
    buffer: list[str] = []
    in_fence = False

    def _flush() -> None:
        if not buffer:
            return
        chunk = "\n".join(buffer)
        chunk = _HTML_COMMENT_RE.sub("", chunk)
        chunk = _HTML_DANGEROUS_BLOCK_RE.sub("", chunk)
        chunk = _HTML_TAG_RE.sub("", chunk)
        out.extend(chunk.split("\n"))
        buffer.clear()

    for line in text.splitlines():
        if _FENCE_RE.match(line):
            if in_fence:
                out.append(line)
                in_fence = False
            else:
                _flush()
                out.append(line)
                in_fence = True
            continue
        if in_fence:
            out.append(line)
        else:
            buffer.append(line)
    _flush()
    return "\n".join(out)


# ── wire projections ─────────────────────────────────────────────────


def _wire_member(member: dict[str, Any]) -> dict[str, Any]:
    """A manifest member as the wire sees it: identity + typed
    metadata, never the repository-relative path (§13)."""
    return {
        "asset_id": member.get("asset_id"),
        "role": member.get("role"),
        "label": member.get("label"),
        "media_type": member.get("media_type"),
        "bytes": member.get("bytes"),
        "sha256": member.get("sha256"),
    }


def _wire_run(run: dict[str, Any]) -> dict[str, Any]:
    exit_code = run.get("exit_code")
    return {
        "timestamp": run.get("timestamp"),
        "command": run.get("command"),
        "exit_code": exit_code,
        "passed": exit_code == 0,
    }


def _wire_revision(manifest: dict[str, Any]) -> dict[str, Any]:
    revision = manifest.get("source_revision") or {}
    return {
        "head_sha": revision.get("head_sha"),
        "index_tree": revision.get("index_tree"),
    }


# ── the manifest cache ───────────────────────────────────────────────


@dataclass
class ManifestEntry:
    """One cached manifest, immutable for its bundle's lifetime; the
    sanitized doc bodies fill lazily and die with the entry."""

    bundle_id: str
    source_id: str
    project: str
    story_id: str
    manifest: dict[str, Any]
    fetched_at: float
    docs: dict[str, str] = field(default_factory=dict)

    def member(self, asset_id: str) -> Optional[dict[str, Any]]:
        for candidate in self.manifest.get("members") or []:
            if candidate.get("asset_id") == asset_id:
                return candidate
        return None


@dataclass
class ManifestView:
    """A cache answer: the entry plus its honesty markers."""

    entry: ManifestEntry
    bundle_changed: bool = False
    live_bundle_id: Optional[str] = None
    freshness: str = "live"  # live | cached | unavailable
    detail: str = ""


def _default_runner(
    argv: list[str], cwd: Optional[str] = None, *, binary: bool = False
):
    kwargs: dict[str, Any] = {}
    if not binary:
        kwargs["text"] = True
        kwargs["errors"] = "replace"
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=DW_TIMEOUT_SECONDS,
        **kwargs,
    )


class DossierService:
    """The hub-side evidence dossier service: manifest cache, dossier
    read model, and manifest-bound asset access — all through the
    source's own vendored dw, its repo root resolved server-side from
    the Delivery registry (never from a client payload)."""

    def __init__(
        self,
        registry: DeliveryRegistry,
        *,
        runner: Optional[Callable[..., Any]] = None,
        dw_argv_factory: Optional[Callable[[Path], Optional[list[str]]]] = None,
        max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._registry = registry
        self._runner = runner or _default_runner
        self._dw_argv = dw_argv_factory or self._default_dw_argv
        self._max_age = float(max_age_seconds)
        self._max_entries = max(1, int(max_entries))
        self._clock = clock
        self._lock = threading.Lock()
        # bundle_id -> entry, LRU-bounded; story key -> latest bundle_id.
        self._entries: "OrderedDict[str, ManifestEntry]" = OrderedDict()
        self._latest: dict[tuple[str, str, str], str] = {}
        # Every dw spawn, as (verb, source_id) — the laziness/economics
        # proof hook for tests; not a wire surface.
        self.dw_calls: list[tuple[str, str]] = []

    @staticmethod
    def _default_dw_argv(root: Path) -> Optional[list[str]]:
        from ..missioncontrol_bridge import dw_argv_base

        return dw_argv_base(root)

    def source_ids(self) -> list[str]:
        return [source.source_id for source in self._registry.sources()]

    # ── subprocess plumbing (root resolved server-side) ──────────

    def _root_and_argv(self, source_id: str) -> tuple[Path, list[str]]:
        source = self._registry.get(source_id)
        if source is None:
            raise DossierRefusal("not_found", f"unknown source {source_id!r}")
        if not source.primary_path:
            raise DossierRefusal("unavailable", "source has no worktree")
        root = Path(source.primary_path)
        argv = self._dw_argv(root)
        if argv is None:
            raise DossierRefusal("unavailable", "no dw CLI")
        return root, argv

    def _spawn(
        self,
        source_id: str,
        verb: str,
        tail: list[str],
        *,
        binary: bool = False,
    ):
        root, argv = self._root_and_argv(source_id)
        self.dw_calls.append((verb, source_id))
        try:
            return self._runner([*argv, *tail], str(root), binary=binary)
        except subprocess.TimeoutExpired:
            raise DossierRefusal("unavailable", "dw timed out") from None
        except OSError:
            raise DossierRefusal("unavailable", "dw failed to start") from None

    def _run_json(self, source_id: str, verb: str, tail: list[str]) -> Any:
        proc = self._spawn(source_id, verb, tail)
        if proc.returncode != 0:
            stderr = str(proc.stderr or "")
            if "not found" in stderr or "no story or evidence bundle" in stderr:
                raise DossierRefusal("not_found", "story not on the roadmap")
            raise DossierRefusal("unavailable", f"dw exited {proc.returncode}")
        try:
            return json.loads(proc.stdout)
        except (ValueError, TypeError):
            raise DossierRefusal(
                "unavailable", "dw did not return JSON"
            ) from None

    # ── manifests ────────────────────────────────────────────────

    def _fetch_manifest(
        self, source_id: str, project: str, story_id: str
    ) -> ManifestEntry:
        doc = self._run_json(
            source_id,
            "manifest",
            ["evidence", "manifest", project, story_id, "--json"],
        )
        if (
            not isinstance(doc, dict)
            or doc.get("evidence_schema") != EVIDENCE_SCHEMA_PROVEN
        ):
            found = doc.get("evidence_schema") if isinstance(doc, dict) else None
            raise DossierRefusal(
                "incompatible",
                f"evidence_schema {found!r} unsupported "
                f"(proven {EVIDENCE_SCHEMA_PROVEN})",
            )
        return ManifestEntry(
            bundle_id=str(doc.get("bundle_id") or ""),
            source_id=source_id,
            project=str(doc.get("project") or project),
            story_id=str(doc.get("story_id") or story_id),
            manifest=doc,
            fetched_at=self._clock(),
        )

    def _store(self, entry: ManifestEntry) -> None:
        with self._lock:
            self._entries[entry.bundle_id] = entry
            self._entries.move_to_end(entry.bundle_id)
            key = (entry.source_id, entry.project, entry.story_id)
            self._latest[key] = entry.bundle_id
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def manifest_for_story(
        self, source_id: str, project: str, story_id: str
    ) -> ManifestView:
        """The story's live manifest — served from the cache inside
        the bounded-age window (a poll never shells out), refreshed
        past it. A refresh failure with a retained manifest degrades
        to ``freshness: "unavailable"`` instead of vanishing (§13)."""
        key = (source_id, project, story_id)
        with self._lock:
            bundle_id = self._latest.get(key)
            entry = self._entries.get(bundle_id) if bundle_id else None
            if entry is not None:
                self._entries.move_to_end(entry.bundle_id)
                if (self._clock() - entry.fetched_at) < self._max_age:
                    return ManifestView(entry=entry, freshness="cached")
        try:
            fresh = self._fetch_manifest(source_id, project, story_id)
        except DossierRefusal as refusal:
            if entry is not None and refusal.code == "unavailable":
                return ManifestView(
                    entry=entry,
                    freshness="unavailable",
                    detail=refusal.detail,
                )
            raise
        if entry is not None and fresh.bundle_id == entry.bundle_id:
            # Same bundle: keep the entry (and its hydrated docs),
            # just restamp its age.
            entry.fetched_at = fresh.fetched_at
            self._store(entry)
            return ManifestView(entry=entry)
        self._store(fresh)
        return ManifestView(entry=fresh)

    def manifest_for_bundle(self, bundle_id: str) -> ManifestView:
        """Resolve a bundle_id the hub has served before. If the live
        bundle differs, the CACHED manifest still answers — marked
        ``bundle_changed`` with the live bundle named — so metadata
        never vanishes mid-browse (§13)."""
        with self._lock:
            entry = self._entries.get(bundle_id)
        if entry is None:
            raise DossierRefusal(
                "not_found",
                f"bundle {bundle_id!r} is not in the hub cache; "
                "re-fetch the story dossier",
            )
        live = self.manifest_for_story(
            entry.source_id, entry.project, entry.story_id
        )
        if live.entry.bundle_id != bundle_id:
            return ManifestView(
                entry=entry,
                bundle_changed=True,
                live_bundle_id=live.entry.bundle_id,
                freshness="cached",
            )
        return ManifestView(
            entry=entry,
            freshness=live.freshness,
            detail=live.detail,
        )

    # ── assets ───────────────────────────────────────────────────

    def open_asset(
        self, bundle_id: str, asset_id: str
    ) -> tuple[bytes, dict[str, Any]]:
        """One manifest member's bytes, via the counterpart's
        ``dw evidence asset`` chokepoint, re-hashed against the
        manifest. Returns ``(data, wire_member)``; refusals are
        typed."""
        view = self.manifest_for_bundle(bundle_id)
        entry = view.entry
        member = entry.member(asset_id)
        if member is None:
            raise DossierRefusal(
                "not_in_manifest",
                f"{asset_id!r} is not a member of {bundle_id}",
            )
        if view.bundle_changed:
            raise DossierRefusal(
                "bundle_changed",
                "the source moved past this bundle; re-fetch the dossier",
                manifest=self.manifest_wire(view),
            )
        proc = self._spawn(
            entry.source_id,
            "asset",
            ["evidence", "asset", bundle_id, asset_id],
            binary=True,
        )
        if proc.returncode != 0:
            raise self._asset_refusal(proc.stderr, view)
        data: bytes = proc.stdout or b""
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        if digest != member.get("sha256"):
            raise DossierRefusal(
                "hash_mismatch",
                "asset bytes no longer match the manifest hash; "
                "re-fetch the dossier",
                manifest=self.manifest_wire(view),
            )
        return data, _wire_member(member)

    def _asset_refusal(self, stderr: Any, view: ManifestView) -> DossierRefusal:
        text = stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else str(stderr or "")
        if "no story or evidence bundle" in text:
            return DossierRefusal(
                "bundle_changed",
                "the source moved past this bundle; re-fetch the dossier",
                manifest=self.manifest_wire(view),
            )
        for code in ("not_in_manifest", "outside_root", "symlink", "absent", "oversize"):
            if f"({code})" in text:
                return DossierRefusal(code, f"dw refused the asset ({code})")
        return DossierRefusal("unavailable", "dw asset stream failed")

    # ── dossiers ─────────────────────────────────────────────────

    def manifest_wire(self, view: ManifestView) -> dict[str, Any]:
        """The §5.3 manifest as wire metadata: members without paths,
        runs with an explicit passed flag, honesty markers on top."""
        manifest = view.entry.manifest
        return {
            "bundle_id": view.entry.bundle_id,
            "bundle_changed": view.bundle_changed,
            "live_bundle_id": view.live_bundle_id,
            "freshness": view.freshness,
            "detail": view.detail,
            "source_id": view.entry.source_id,
            "project": view.entry.project,
            "story_id": view.entry.story_id,
            "phase": manifest.get("phase"),
            "status": manifest.get("status"),
            "source_revision": _wire_revision(manifest),
            "summary": manifest.get("summary") or {},
            "members": [
                _wire_member(m) for m in manifest.get("members") or []
            ],
            "captured_runs": [
                _wire_run(r) for r in manifest.get("captured_runs") or []
            ],
            "trace": dict(manifest.get("trace") or {}),
        }

    def _doc_body(self, view: ManifestView, member: dict[str, Any]) -> dict[str, Any]:
        """One inline document (story/evidence markdown): sanitized
        text, cached on the entry, honest about unavailability."""
        asset_id = str(member.get("asset_id") or "")
        entry = view.entry
        cached = entry.docs.get(asset_id)
        if cached is not None:
            return {"asset_id": asset_id, "state": "ready", "markdown": cached}
        try:
            data, _ = self.open_asset(entry.bundle_id, asset_id)
        except DossierRefusal as refusal:
            return {
                "asset_id": asset_id,
                "state": refusal.code,
                "markdown": None,
            }
        text = sanitize_markdown(data.decode("utf-8", "replace"))
        entry.docs[asset_id] = text
        return {"asset_id": asset_id, "state": "ready", "markdown": text}

    def story_dossier(
        self,
        source_id: str,
        project: str,
        story_id: str,
        *,
        include_docs: bool = True,
    ) -> dict[str, Any]:
        view = self.manifest_for_story(source_id, project, story_id)
        wire = self.manifest_wire(view)
        wire["dossier_schema"] = DOSSIER_SCHEMA
        if include_docs:
            trace = view.entry.manifest.get("trace") or {}
            story_member = (
                view.entry.member(str(trace.get("story_asset_id")))
                if trace.get("story_asset_id")
                else None
            )
            wire["story"] = (
                self._doc_body(view, story_member) if story_member else None
            )
            wire["evidence"] = [
                self._doc_body(view, member)
                for member in view.entry.manifest.get("members") or []
                if member.get("role") == "evidence_markdown"
            ]
        return wire

    def story_dossier_any(self, project: str, story_id: str) -> dict[str, Any]:
        """Resolve a story dossier across every registered source —
        the no-`?source=` path. A story an offline source may hold is
        `unavailable`, never silently `not found`."""
        saw_unavailable: Optional[DossierRefusal] = None
        for source_id in self.source_ids():
            try:
                return self.story_dossier(source_id, project, story_id)
            except DossierRefusal as refusal:
                if refusal.code != "not_found":
                    saw_unavailable = refusal
        if saw_unavailable is not None:
            raise saw_unavailable
        raise DossierRefusal(
            "not_found", f"story {story_id!r} not found in any source"
        )

    def phase_dossier(
        self, source_id: str, project: str, phase: int
    ) -> dict[str, Any]:
        """The phase's story dossiers grouped, metadata only — no
        story/evidence bodies, no asset reads (§ story: 'without
        eagerly loading assets'). Assets stream later, by asset_id."""
        feed = self._run_json(source_id, "state", ["state", "--json"])
        if not isinstance(feed, dict):
            raise DossierRefusal("unavailable", "dw state was not a document")
        project_doc = next(
            (
                p
                for p in feed.get("projects") or []
                if isinstance(p, dict) and str(p.get("slug")) == project
            ),
            None,
        )
        if project_doc is None:
            raise DossierRefusal(
                "not_found", f"project {project!r} not on the roadmap"
            )
        phase_doc = next(
            (
                p
                for p in project_doc.get("phases") or []
                if isinstance(p, dict) and p.get("number") == phase
            ),
            None,
        )
        if phase_doc is None:
            raise DossierRefusal("not_found", f"phase {phase} not on the roadmap")
        stories = [
            s
            for s in project_doc.get("stories") or []
            if isinstance(s, dict) and s.get("phase") == phase
        ]
        rows: list[dict[str, Any]] = []
        final_summary: Optional[dict[str, Any]] = None
        for story in stories:
            story_id = str(story.get("story_id") or "")
            try:
                dossier = self.story_dossier(
                    source_id, project, story_id, include_docs=False
                )
            except DossierRefusal as refusal:
                rows.append(
                    {
                        "story_id": story_id,
                        "title": story.get("title"),
                        "status": story.get("status"),
                        "state": refusal.code,
                    }
                )
                continue
            dossier["title"] = story.get("title")
            dossier["state"] = "ready"
            rows.append(dossier)
            if final_summary is None:
                summary_id = (dossier.get("trace") or {}).get(
                    "final_summary_asset_id"
                )
                if summary_id:
                    member = next(
                        (
                            m
                            for m in dossier["members"]
                            if m.get("asset_id") == summary_id
                        ),
                        None,
                    )
                    if member is not None:
                        final_summary = {
                            **member,
                            "bundle_id": dossier["bundle_id"],
                        }
        return {
            "phase_dossier_schema": PHASE_DOSSIER_SCHEMA,
            "source_id": source_id,
            "project": project,
            "phase": phase,
            "title": phase_doc.get("title"),
            "status": phase_doc.get("status"),
            "stories_done": phase_doc.get("stories_done"),
            "stories_total": phase_doc.get("stories_total"),
            "stories": rows,
            "final_summary": final_summary,
        }


# ── grounding adapter (HS-94-08 wires the compose path) ─────────────

GROUNDABLE_KINDS = ("story", "evidence")


def hydrate_dossier_refs(
    refs: list[dict[str, Any]], service: DossierService
) -> tuple[list[GroundingBlock], list[str]]:
    """Hydrate dossier member refs into the SAME GroundingBlock shape
    ``grounding_rails.hydrate_rails_refs`` produces, byte-capped with
    the rail-object cut marker. Each ref is
    ``{source, project, kind, id}`` with ``kind`` in
    ``("story", "evidence")`` and ``id`` the story ID; the bytes flow
    through the manifest-bound asset chokepoint, never a raw path.
    Unknown/unreachable refs come back as ``"<kind>:<id>"`` tokens for
    the caller to refuse."""
    blocks: list[GroundingBlock] = []
    unknown: list[str] = []
    for ref in refs:
        if not isinstance(ref, dict):
            unknown.append(str(ref))
            continue
        source_id = str(ref.get("source") or "")
        project = str(ref.get("project") or "")
        kind = str(ref.get("kind") or "")
        rid = str(ref.get("id") or "")
        token = f"{kind}:{rid}"
        if kind not in GROUNDABLE_KINDS or not (source_id and project and rid):
            unknown.append(token)
            continue
        try:
            view = service.manifest_for_story(source_id, project, rid)
            trace = view.entry.manifest.get("trace") or {}
            asset_id = trace.get(
                "story_asset_id" if kind == "story" else "evidence_asset_id"
            )
            if not asset_id:
                unknown.append(token)
                continue
            data, _ = service.open_asset(view.entry.bundle_id, str(asset_id))
        except DossierRefusal:
            unknown.append(token)
            continue
        text = data.decode("utf-8", "replace")
        if len(text) > GROUNDING_TRANSCRIPT_CAP:
            text = (
                text[:GROUNDING_TRANSCRIPT_CAP]
                + f"\n[rail object cut at {GROUNDING_TRANSCRIPT_CAP} chars]"
            )
        source = service._registry.get(source_id)
        label = source.label if source else source_id
        blocks.append(
            GroundingBlock(
                kind=f"rails:{kind}",
                ref=rid,
                title=rid,
                subtitle=f"{label}/{project}",
                text=text,
            )
        )
    return blocks, unknown


__all__ = [
    "DOSSIER_SCHEMA",
    "PHASE_DOSSIER_SCHEMA",
    "REFUSAL_HTTP",
    "GROUNDABLE_KINDS",
    "DossierRefusal",
    "DossierService",
    "ManifestEntry",
    "ManifestView",
    "hydrate_dossier_refs",
    "sanitize_markdown",
]
