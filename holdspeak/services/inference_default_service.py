"""Batteries-included default for AI work (owner ruling 2026-10-05).

"Strong defaults, batteries included":

* When a usable engine runs on THIS machine, HoldSpeak makes it the
  "Default for AI work" (the ``global`` assignment) by itself, with a
  receipt (``inference.default_assigned``) and the LOCAL lamp.
* A network (LAN, mesh) or cloud engine is never assigned by itself.  It is
  stored as a proposal; the owner's "Use it" press assigns it.
* An assignment the owner made is never changed, and a default he cleared
  stays cleared.  The rule writes when the ``global`` head never existed, or
  re-picks HoldSpeak's OWN default (``made_by='holdspeak_default'`` on the
  revision) when it no longer answers and another local engine does.

Detection here reads loopback ports only (``scan_loopback_engines``):
Ollama 11434, LM Studio 1234, llama.cpp 8080 and 8000 on 127.0.0.1.  A
non-loopback host is refused before any socket is opened, and the scan
request ignores HTTP proxy settings and follows no redirect
(``loopback_http``), so a scan request never leaves the machine.

Ranking (``rank_key``), among candidates that answered their health probe:

1. A model whose size is known ranks before a model whose size is unknown.
2. The larger parameter count first.  The count is read from Ollama's own
   ``details.parameter_size``, else from the model name (``qwen3:8b``,
   ``Qwen3.5-27B-Instruct``); a mixture ``8x7b`` counts 56.
3. A model from the signed catalogue before an unsigned one.
4. An engine already in the Model Library, then Ollama, LM Studio,
   llama.cpp 8080, llama.cpp 8000.
5. The model name.

Every candidate is probed live at assign time (bounded, loopback rules); an
old readiness observation never decides.  The next candidate is tried when
the probe does not say ``ready``.
"""
from __future__ import annotations

import ipaddress
import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence
from urllib.parse import urlparse

from ..inference_locality import (
    AUTO_ASSIGNED_OPERATION as ASSIGNED_OPERATION,
    assignment_lamp,
    deployment_lamp,
    made_by_holdspeak,
)
from ..logging_config import get_logger
from ..loopback_http import loopback_get
from ..principals import Principal, PrincipalKind
from .errors import NotFound, ServiceError, ValidationError

log = get_logger("inference.default")

#: The principal of the product's own default write.
DEFAULT_PRINCIPAL = Principal(PrincipalKind.OWNER, "batteries-default")
#: The kernel operation that records the product's own default write
#: (``ASSIGNED_OPERATION``, imported from inference_locality).
ASSIGN_REASON = "batteries-included default"

#: (port, engine) on this machine, in rank order.
LOOPBACK_ENGINE_PORTS: tuple[tuple[int, str], ...] = (
    (11434, "Ollama"),
    (1234, "LM Studio"),
    (8080, "llama.cpp"),
    (8000, "llama.cpp"),
)
LOOPBACK_HOST = "127.0.0.1"
SCAN_TIMEOUT_SECONDS = 0.5

#: Model names that are not chat models.
_NOT_CHAT = re.compile(
    r"embed|rerank|whisper|(^|[^a-z])bge[-_]|(^|[^a-z])e5[-_]|minilm|clip|tts|moderation",
    re.IGNORECASE,
)
_MIXTURE = re.compile(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*b(?![a-z])", re.IGNORECASE)
_PARAMS = re.compile(r"(\d+(?:\.\d+)?)\s*b(?![a-z])", re.IGNORECASE)
_PARAMS_M = re.compile(r"(\d+(?:\.\d+)?)\s*m(?![a-z])", re.IGNORECASE)
_UNSIGNED_SOURCES = frozenset({
    "uploaded_file", "existing_local_file", "model_library_provider_material", "fixture",
})


class LoopbackOnlyError(ValueError):
    """A scan was asked to reach an address that is not on this machine."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_loopback(host: str) -> str:
    """Return ``host`` when it is a loopback address literal, else refuse.

    Only address literals pass: a name could resolve to any address.
    """
    text = str(host or "").strip().strip("[]")
    try:
        address = ipaddress.ip_address(text)
    except ValueError as exc:
        raise LoopbackOnlyError(f"not a loopback address: {host!r}") from exc
    if not address.is_loopback:
        raise LoopbackOnlyError(f"not a loopback address: {host!r}")
    return text


def _loopback_get(url: str, *, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    """GET one loopback URL: pinned literal, no proxy, no redirect (loopback_http)."""
    require_loopback(urlparse(url).hostname or "")
    return loopback_get(url, headers=headers, timeout=timeout)


def parameter_billions(*texts: Any) -> Optional[float]:
    """The parameter count in billions read from a size word or a model name."""
    for text in texts:
        value = str(text or "").strip()
        if not value:
            continue
        mixture = _MIXTURE.search(value)
        if mixture:
            return float(mixture.group(1)) * float(mixture.group(2))
        found = [float(m.group(1)) for m in _PARAMS.finditer(value)]
        if found:
            return max(found)
        millions = [float(m.group(1)) for m in _PARAMS_M.finditer(value)]
        if millions and re.fullmatch(r"\s*\d+(?:\.\d+)?\s*m\s*", value, re.IGNORECASE):
            return max(millions) / 1000.0
    return None


def is_chat_model(name: str) -> bool:
    return bool(str(name or "").strip()) and not _NOT_CHAT.search(str(name))


def _ollama_sizes(base_root: str, getter: Callable[..., tuple[int, bytes]], timeout: float) -> dict[str, str]:
    try:
        code, raw = getter(f"{base_root}/api/tags", headers={"Accept": "application/json"}, timeout=timeout)
        if not 200 <= int(code) < 300:
            return {}
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return {}
    sizes: dict[str, str] = {}
    for row in (payload.get("models") if isinstance(payload, dict) else None) or []:
        if not isinstance(row, dict):
            continue
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        size = str(details.get("parameter_size") or "")
        for key in (row.get("name"), row.get("model")):
            if key and size:
                sizes[str(key)] = size
    return sizes


def scan_loopback_engines(
    *,
    ports: Sequence[tuple[int, str]] = LOOPBACK_ENGINE_PORTS,
    host: str = LOOPBACK_HOST,
    timeout: float = SCAN_TIMEOUT_SECONDS,
    http_get: Optional[Callable[..., tuple[int, bytes]]] = None,
) -> list[dict[str, Any]]:
    """Every chat model an engine on this machine serves, one row per model.

    The host is checked before any socket is opened.  A port that does not
    answer an OpenAI-compatible ``/v1/models`` is skipped.
    """
    from ..setup_runtime import discover_endpoint_models

    loopback = require_loopback(host)
    url_host = f"[{loopback}]" if ":" in loopback else loopback
    getter = http_get or _loopback_get
    found: list[dict[str, Any]] = []
    for order, (port, engine) in enumerate(ports):
        root = f"http://{url_host}:{int(port)}"
        base = f"{root}/v1"
        try:
            result = discover_endpoint_models(base, timeout_seconds=timeout, http_get=getter)
        except Exception:
            continue
        if not result.get("ok"):
            continue
        models = [m for m in (result.get("models") or []) if is_chat_model(m)]
        if not models:
            continue
        sizes = _ollama_sizes(root, getter, timeout) if engine == "Ollama" else {}
        for model in models:
            found.append({
                "id": f"loopback:{int(port)}:{model}",
                "source": "loopback",
                "engine": engine,
                "port": int(port),
                "base_url": base,
                "model": str(model),
                "params_b": parameter_billions(sizes.get(model), model),
                "signed": False,
                "order": 1 + order,
                "lamp": "local",
            })
    return found


def rank_key(candidate: dict[str, Any]) -> tuple:
    """The sort key for the ranking in the module text (smaller is better)."""
    params = candidate.get("params_b")
    return (
        0 if params is not None else 1,
        -(params or 0.0),
        0 if candidate.get("signed") else 1,
        int(candidate.get("order", 99)),
        str(candidate.get("model") or candidate.get("label") or ""),
    )


def _slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def loopback_profile_id(candidate: dict[str, Any]) -> str:
    slug = _slug(f"{candidate['engine']}-{candidate['port']}-{candidate['model']}")
    return ("local-" + slug)[:96].rstrip("-_") or "local-engine"


class _FirstAssignmentOnly:
    """The assignment writer automatic adoption gets: first assignment only.

    Every write is forced to ``expected_revision`` 0, checked inside the
    write transaction, so a head that exists or ever existed (an owner's
    Turn off leaves a cleared head) is a conflict and never a write.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.refused = False
        self.written = False

    def set_assignment(self, principal: Any, body: Any) -> dict[str, Any]:
        from .errors import ConflictError

        try:
            result = self._inner.set_assignment(
                principal, {**dict(body), "expected_revision": 0}, made_by="holdspeak_default",
            )
        except ConflictError:
            self.refused = True
            raise
        self.written = True
        return result

    def __getattr__(self, name: str) -> Any:
        if name in {"clear_assignment"}:
            raise AttributeError(name)  # automatic code never clears
        return getattr(self._inner, name)


class InferenceDefaultService:
    """Assigns the batteries-included default; stores and reads proposals."""

    def __init__(
        self,
        db: Any,
        *,
        assignment_service: Any,
        model_library_service: Any = None,
        meaning_search: Any = None,
        home_provider: Callable[[], Path] = Path.home,
        scan: Optional[Callable[[], list[dict[str, Any]]]] = None,
        detect_http_get: Optional[Callable[..., tuple[int, bytes]]] = None,
        meaning_factory: Optional[Callable[[Any], Any]] = None,
        find_embed_model: Optional[Callable[..., Optional[Path]]] = None,
    ) -> None:
        self._db = db
        self._assignments = assignment_service
        self._library = model_library_service
        self._meaning = meaning_search
        self._home = home_provider
        self._scan = scan or scan_loopback_engines
        self._detect_http_get = detect_http_get
        self._meaning_factory = meaning_factory
        if find_embed_model is None:
            from ..memory.local_model import find_on_device as find_embed_model
        self._find_embed_model = find_embed_model
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    # ── triggers ─────────────────────────────────────────────────────

    def kick(self, reason: str) -> None:
        """Run ``ensure`` on a daemon thread unless one already runs."""
        thread = self._thread
        if thread is not None and thread.is_alive():
            return

        def _run() -> None:
            try:
                self.ensure(reason=reason)
            except Exception as exc:  # a background default never breaks the hub
                log.warning("batteries default (%s) failed: %s", reason, exc)

        self._thread = threading.Thread(target=_run, name="inference-default", daemon=True)
        self._thread.start()

    def wait(self, timeout: float = 30.0) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    # ── the rule ─────────────────────────────────────────────────────

    def _global_head(self) -> Any:
        """The global head (cleared or not) with who made its revision; None if never."""
        with self._db._connection() as conn:
            return conn.execute(
                """SELECT h.assignment_id,h.revision,h.cleared,r.made_by
                     FROM inference_assignment_heads h
                     JOIN inference_assignment_revisions r
                       ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                    WHERE h.assignment_key='global'"""
            ).fetchone()

    def _head_entry(self, head: Any) -> Optional[tuple[str, int]]:
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT profile_id,profile_revision FROM inference_assignments
                    WHERE assignment_id=? AND assignment_revision=? ORDER BY ordinal LIMIT 1""",
                (str(head["assignment_id"]), int(head["revision"])),
            ).fetchone()
        return None if row is None else (str(row["profile_id"]), int(row["profile_revision"]))

    def ensure(self, *, reason: str = "boot") -> dict[str, Any]:
        """Assign the local default once, or record proposals.  Never overwrites."""
        with self._lock:
            result: dict[str, Any] = {"reason": reason, "assigned": None, "proposals": 0}
            try:
                result["memory_embed"] = self._ensure_meaning_search()
            except Exception as exc:
                log.warning("meaning search adopt failed: %s", exc)
                result["memory_embed"] = "failed"
            head = self._global_head()
            expected = 0
            current_profile = None
            if head is not None:
                if int(head["cleared"]) or str(head["made_by"]) != "holdspeak_default":
                    # The owner's default, or any default he cleared, is
                    # never changed here.
                    result["status"] = "kept"
                    return result
                # HoldSpeak's own default: keep it while it answers; re-pick
                # only when it is no longer ready and another local engine is.
                current_profile = self._head_entry(head)
                if current_profile is not None and self._live_ready(*current_profile):
                    result["status"] = "kept"
                    return result
                expected = int(head["revision"])
            candidates = self._local_candidates()
            for candidate in sorted(candidates, key=rank_key):
                if current_profile is not None and candidate.get("profile_id") == current_profile[0]:
                    continue
                assigned = self._try_assign(candidate, expected_revision=expected)
                if assigned is not None:
                    result.update(
                        status="repicked" if expected else "assigned", assigned=assigned,
                    )
                    return result
            if head is not None:
                result["status"] = "kept"  # nothing better: the default stays as it is
                return result
            result["proposals"] = self._record_proposals()
            result["status"] = "proposed" if result["proposals"] else "needs_setup"
            return result

    def has_global_head(self) -> bool:
        """True once any ``global`` head exists (set, re-picked or cleared)."""
        return self._global_head() is not None

    def rescan(self) -> dict[str, Any]:
        """The light periodic re-scan: an engine started AFTER boot is found.

        Loopback only, the same rules as boot (``scan_loopback_engines``: no
        proxy, no redirect, a non-loopback host refused before any socket).
        It runs only while no ``global`` head ever existed, so it never
        touches a default the owner made or cleared, and it records no
        proposals (proposals read LAN and cloud endpoints; boot and Detect do
        that).  A Model Library profile is probed only when its endpoint is
        one the scan just found answering, so an idle tick opens four
        loopback connections and probes nothing.
        """
        if not self._lock.acquire(blocking=False):
            return {"reason": "rescan", "status": "busy"}
        try:
            if self._global_head() is not None:
                return {"reason": "rescan", "status": "has_default"}
            try:
                scanned = [c for c in self._scan() if c.get("lamp") == "local"]
            except Exception as exc:
                log.info("loopback rescan failed: %s", exc)
                scanned = []
            if not scanned:
                return {"reason": "rescan", "status": "none"}
            answering = {(str(c["base_url"]).rstrip("/"), str(c["model"])) for c in scanned}
            profiles = [
                c for c in self._local_profile_candidates()
                if (str(c.get("endpoint", "")).rstrip("/"), str(c.get("model", ""))) in answering
            ]
            known = {(str(c.get("endpoint", "")).rstrip("/"), str(c.get("model", ""))) for c in profiles}
            fresh = [
                c for c in scanned
                if (str(c["base_url"]).rstrip("/"), str(c["model"])) not in known
            ]
            for candidate in sorted(profiles + fresh, key=rank_key):
                assigned = self._try_assign(candidate, expected_revision=0)
                if assigned is not None:
                    return {"reason": "rescan", "status": "assigned", "assigned": assigned}
            return {"reason": "rescan", "status": "not_ready"}
        finally:
            self._lock.release()

    # ── candidates ───────────────────────────────────────────────────

    def _local_candidates(self) -> list[dict[str, Any]]:
        profiles = self._local_profile_candidates()
        known = {(c.get("endpoint", "").rstrip("/"), c.get("model", "")) for c in profiles}
        try:
            scanned = list(self._scan())
        except Exception as exc:
            log.info("loopback scan failed: %s", exc)
            scanned = []
        fresh = [
            c for c in scanned
            if c.get("lamp") == "local"
            and (str(c["base_url"]).rstrip("/"), str(c["model"])) not in known
        ]
        return profiles + fresh

    def _local_profile_candidates(self) -> list[dict[str, Any]]:
        """Model Library profiles that run on this machine (readiness is probed later)."""
        out: list[dict[str, Any]] = []
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT r.* FROM model_profile_revisions r
                     JOIN model_profile_binding_heads h ON h.profile_id=r.profile_id
                     JOIN model_profile_binding_revisions b
                       ON b.binding_id=h.binding_id AND b.revision=h.revision
                      AND b.profile_revision=r.revision
                     LEFT JOIN model_profile_tombstones t ON t.profile_id=r.profile_id
                    WHERE t.profile_id IS NULL AND b.enabled=1"""
            ).fetchall()
            for row in rows:
                binding = conn.execute(
                    """SELECT b.* FROM model_profile_binding_heads h
                         JOIN model_profile_binding_revisions b
                           ON b.binding_id=h.binding_id AND b.revision=h.revision
                        WHERE h.profile_id=?""",
                    (row["profile_id"],),
                ).fetchone()
                deployment = conn.execute(
                    "SELECT * FROM deployment_revisions WHERE id=?",
                    (binding["deployment_revision_id"],),
                ).fetchone()
                if deployment is None:
                    continue
                if deployment_lamp(deployment["boundary"], deployment["endpoint"]) != "local":
                    continue
                # Readiness is probed live at assign time (_live_ready), never
                # read from an old observation.
                try:
                    claims = set(json.loads(str(row["capability_manifest_json"])).get("claims") or [])
                    modalities = set(json.loads(str(row["supported_modalities_json"])))
                except Exception:
                    continue
                if "embedding" in claims or not ({"language", "text"} & modalities):
                    continue
                model = str(deployment["model"] or "")
                label = str(row["label"] or row["profile_id"])
                if not is_chat_model(model) or not is_chat_model(label):
                    continue
                artifact = conn.execute(
                    "SELECT source_kind FROM inference_model_artifacts WHERE artifact_id=?",
                    (str(deployment["artifact_id"] or ""),),
                ).fetchone()
                signed = artifact is not None and str(artifact["source_kind"]) not in _UNSIGNED_SOURCES
                out.append({
                    "id": f"profile:{row['profile_id']}",
                    "source": "profile",
                    "profile_id": str(row["profile_id"]),
                    "profile_revision": int(row["revision"]),
                    "label": label,
                    "model": model,
                    "endpoint": str(deployment["endpoint"] or ""),
                    "engine": "this machine",
                    "params_b": parameter_billions(model, label, row["model_or_artifact_identity"]),
                    "signed": signed,
                    "order": 0,
                    "lamp": "local",
                })
        return out

    # ── assign ───────────────────────────────────────────────────────

    def _register_loopback(self, candidate: dict[str, Any]) -> Optional[tuple[str, int]]:
        """Put one loopback model in the Model Library; its readiness probe runs there."""
        if self._library is None:
            return None
        profile_id = loopback_profile_id(candidate)
        try:
            current = self._library._profiles.get_profile(DEFAULT_PRINCIPAL, profile_id)
            expected = int(current["revision"])
        except NotFound:
            expected = 0
        label = f"{candidate['model']} on {candidate['engine']}".replace("/", " ")[:200]
        receipt = self._library.define_endpoint(DEFAULT_PRINCIPAL, {
            "request_id": f"batteries-{profile_id}-r{expected}",
            "profile_id": profile_id,
            "expected_profile_revision": expected,
            "label": label,
            "provider_family": "openai_compatible",
            "model": str(candidate["model"]),
            "endpoint": str(candidate["base_url"]),
            "requires_key": False,
        }, None)
        provider = receipt.get("provider") or {}
        return str(provider["profile_id"]), int(provider["profile_revision"])

    def _profile_lamp(self, profile_id: str, revision: int) -> str:
        """The lamp of one profile revision's bound deployment, read before any write."""
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT d.boundary,d.endpoint FROM model_profile_binding_heads h
                     JOIN model_profile_binding_revisions b
                       ON b.binding_id=h.binding_id AND b.revision=h.revision
                     JOIN deployment_revisions d ON d.id=b.deployment_revision_id
                    WHERE h.profile_id=? AND b.profile_revision=?""",
                (profile_id, revision),
            ).fetchone()
        return "unknown" if row is None else deployment_lamp(row["boundary"], row["endpoint"])

    def _live_ready(self, profile_id: str, revision: int) -> bool:
        """Probe the bound deployment NOW (bounded; loopback rules) and read the result.

        An old readiness observation never decides: a dead engine that was
        ready last week is not ready now.
        """
        with self._db._connection() as conn:
            binding = conn.execute(
                """SELECT b.* FROM model_profile_binding_heads h
                     JOIN model_profile_binding_revisions b
                       ON b.binding_id=h.binding_id AND b.revision=h.revision
                    WHERE h.profile_id=? AND b.profile_revision=? AND b.enabled=1""",
                (profile_id, revision),
            ).fetchone()
        if binding is None:
            return False
        try:
            observation = self._profiles().probe_profile(DEFAULT_PRINCIPAL, {
                "profile_id": profile_id,
                "profile_revision": revision,
                "deployment_head_id": str(binding["deployment_head_id"]),
                "expected_deployment_configuration_revision": int(binding["deployment_configuration_revision"]),
                "expected_deployment_revision_id": str(binding["deployment_revision_id"]),
            })
        except (ServiceError, ValidationError) as exc:
            log.info("default candidate %s probe refused: %s", profile_id, getattr(exc, "code", exc))
            return False
        return str(observation.get("state")) == "ready"

    def _profiles(self) -> Any:
        if self._library is not None:
            return self._library._profiles
        from .model_profile_service import ModelProfileService

        return ModelProfileService(self._db)

    def _try_assign(
        self, candidate: dict[str, Any], *, expected_revision: int = 0,
    ) -> Optional[dict[str, Any]]:
        try:
            if candidate["source"] == "loopback":
                reference = self._register_loopback(candidate)
                if reference is None:
                    return None
            else:
                reference = (candidate["profile_id"], int(candidate["profile_revision"]))
            profile_id, revision = reference
            if self._profile_lamp(profile_id, revision) != "local":
                # The product never makes a network or cloud default by
                # itself: memory follows a default it made only when local.
                log.error("default candidate %s is not local; refused", candidate["id"])
                return None
            if not self._live_ready(profile_id, revision):
                log.info("default candidate %s is not ready; trying the next", candidate["id"])
                return None
            result = self._assignments.set_assignment(DEFAULT_PRINCIPAL, {
                "command_id": f"batteries-default-{uuid.uuid4().hex}",
                # 0 when no default ever existed; else the revision of
                # HoldSpeak's own default being re-picked.  A head the owner
                # wrote in the meantime makes this a revision conflict.
                "expected_revision": expected_revision,
                "scope": {"kind": "global"},
                "entries": [{"profile_id": profile_id, "profile_revision": revision}],
            }, made_by="holdspeak_default")
        except (ServiceError, ValidationError) as exc:
            log.info("default candidate %s refused: %s", candidate.get("id"), getattr(exc, "code", exc))
            return None
        assignment_id = str(result.get("id") or "")
        assignment_revision = int(result.get("revision") or 1)
        with self._db._connection() as conn:
            lamp = assignment_lamp(conn, assignment_id, assignment_revision)
        label = str(candidate.get("label") or f"{candidate['model']} on {candidate['engine']}")
        try:
            # Evidence only: who made the revision is already durable on it.
            receipt_id = self._write_receipt(
                assignment_id=assignment_id,
                assignment_revision=assignment_revision,
                label=label,
                profile_id=profile_id,
                lamp=lamp,
            )
        except Exception as exc:
            log.warning("default receipt not written (the revision says who made it): %s", exc)
            receipt_id = ""
        log.info("Default for AI work: %s (lamp %s, receipt %s)", label, lamp, receipt_id)
        return {
            "profile_id": profile_id,
            "profile_revision": revision,
            "label": label,
            "lamp": lamp,
            "assignment_id": assignment_id,
            "assignment_revision": assignment_revision,
            "receipt_id": receipt_id,
            "candidate": candidate["id"],
        }

    def _write_receipt(
        self, *, assignment_id: str, assignment_revision: int, label: str, profile_id: str, lamp: str,
    ) -> str:
        """One kernel operation + receipt; the idempotency key makes it once per hub."""
        import time as _time

        operation_id = f"inference-default-{uuid.uuid4().hex[:12]}"
        receipt_id = f"inference-default-assigned-{uuid.uuid4().hex[:12]}"
        idempotency = f"{ASSIGNED_OPERATION}:global:{assignment_id}@{assignment_revision}"
        now = _time.time()
        outcome = (
            f"Default for AI work: {label}. Boundary {lamp.upper()}. Reason: {ASSIGN_REASON}."
        )
        with self._db._connection() as conn:
            inserted = conn.execute(
                """INSERT OR IGNORE INTO kernel_operations
                   (operation_id, request_id, idempotency_key, name, version,
                    principal_kind, principal_identity, target_ref, placement,
                    envelope_sha256, policy_version, authority_basis,
                    state, revision, native_id, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                (
                    operation_id, idempotency, idempotency, ASSIGNED_OPERATION, 1,
                    "owner", DEFAULT_PRINCIPAL.identity, f"inference.assignment:global:{profile_id}",
                    lamp, "", "", "owner_ruling_2026_10_05_batteries_included",
                    "succeeded", operation_id, now, now,
                ),
            ).rowcount
            if not inserted:
                row = conn.execute(
                    """SELECT r.receipt_id FROM kernel_operations o
                         JOIN kernel_receipts r ON r.operation_id=o.operation_id
                        WHERE o.principal_identity=? AND o.idempotency_key=?""",
                    (DEFAULT_PRINCIPAL.identity, idempotency),
                ).fetchone()
                return str(row["receipt_id"]) if row is not None else ""
            conn.execute(
                """INSERT INTO kernel_receipts
                   (receipt_id, operation_id, state, outcome, result_ref, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (receipt_id, operation_id, "succeeded", outcome,
                 f"inference_assignment:{assignment_id}@{assignment_revision}", now),
            )
        return receipt_id

    # ── proposals (network and cloud engines) ────────────────────────

    def _record_proposals(self) -> int:
        """Store each ready LAN / mesh / cloud engine as a proposal; assign none."""
        from .concierge_service import KIND_CLOUD, KIND_LAN, STATE_READY, detect

        try:
            engines = detect(db=self._db, home=self._home(), http_get=self._detect_http_get)["engines"]
        except Exception as exc:
            log.info("default proposals: detection failed: %s", exc)
            return 0
        count = 0
        now = _now()
        with self._db._connection() as conn:
            for engine in engines:
                kind = engine.get("kind")
                if kind not in {KIND_LAN, KIND_CLOUD} or engine.get("state") != STATE_READY:
                    continue
                base = str(engine.get("baseUrl") or "")
                if kind == KIND_CLOUD:
                    lamp = "cloud"
                elif base:
                    lamp = deployment_lamp("private_network", base)
                else:
                    lamp = "mesh"
                if lamp == "local":
                    continue  # never a proposal: a local engine is assigned, not proposed
                revision = engine.get("profileRevision")
                conn.execute(
                    """INSERT INTO inference_default_proposals
                       (engine_id,lamp,label,host,profile_id,profile_revision,state,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,'open',?,?)
                       ON CONFLICT(engine_id) DO UPDATE SET
                         lamp=excluded.lamp,label=excluded.label,host=excluded.host,
                         profile_id=excluded.profile_id,profile_revision=excluded.profile_revision,
                         updated_at=excluded.updated_at
                       WHERE inference_default_proposals.state='open'""",
                    (
                        str(engine["id"]), lamp, str(engine.get("name") or engine["id"])[:200],
                        str(engine.get("host") or "")[:200], str(engine.get("profileId") or ""),
                        int(revision) if type(revision) is int else 0, now, now,
                    ),
                )
                count += 1
        return count

    def proposals(self) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM inference_default_proposals WHERE state='open' ORDER BY created_at, engine_id"
            ).fetchall()
        return [
            {
                "id": str(row["engine_id"]),
                "label": str(row["label"]),
                "host": str(row["host"]),
                "lamp": str(row["lamp"]),
                "profile_id": str(row["profile_id"]),
                "profile_revision": int(row["profile_revision"]),
                "verb": "Use it",
            }
            for row in rows
        ]

    def use_proposal(self, principal: Principal, proposal_id: str) -> dict[str, Any]:
        """The owner's "Use it" press: assign the proposed engine as the default."""
        self._assignments._require_owner(principal)
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM inference_default_proposals WHERE engine_id=? AND state='open'",
                (str(proposal_id or ""),),
            ).fetchone()
            current = conn.execute(
                "SELECT revision FROM inference_assignment_heads WHERE assignment_key='global'"
            ).fetchone()
        if row is None:
            raise NotFound("default proposal", str(proposal_id))
        if not str(row["profile_id"]) or int(row["profile_revision"]) < 1:
            raise ServiceError(
                "inference_default_proposal_unbound",
                "This engine has no model profile revision.",
                context={"status": 409},
            )
        result = self._assignments.set_assignment(principal, {
            "command_id": f"default-proposal-{uuid.uuid4().hex}",
            "expected_revision": 0 if current is None else int(current["revision"]),
            "scope": {"kind": "global"},
            "entries": [{"profile_id": str(row["profile_id"]), "profile_revision": int(row["profile_revision"])}],
        })
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE inference_default_proposals SET state='used', updated_at=? WHERE engine_id=?",
                (_now(), str(row["engine_id"])),
            )
        return {"proposal": str(row["engine_id"]), "assignment": result}

    # ── memory.embed: the local embedding model when it is here ──────

    def _embed_head_ever_existed(self) -> bool:
        with self._db._connection() as conn:
            return conn.execute(
                "SELECT 1 FROM inference_assignment_heads WHERE assignment_key='capability:memory.embed'"
            ).fetchone() is not None

    def _ensure_meaning_search(self) -> str:
        """Use the on-device embedding model for ``memory.embed`` when present.

        Only a file already on this device (hash checked) is used: nothing is
        downloaded here.  Only when ``memory.embed`` never had a head: the
        owner's Turn off (a cleared head) is final for automatic code.  The
        quick read below skips work; the rule itself is enforced inside the
        assignment write (``_FirstAssignmentOnly``: expected revision 0, so
        any head, cleared or not, is a conflict, never a write).
        """
        if self._meaning is None and self._meaning_factory is None:
            return "no_service"
        if self._embed_head_ever_existed():
            return "kept"
        import importlib.util

        if importlib.util.find_spec("llama_cpp") is None and self._meaning_factory is None:
            return "runtime_missing"
        from ..memory.local_model import EMBED_MODEL

        path = self._find_embed_model(EMBED_MODEL, self._home())
        if path is None:
            return "model_missing"
        guarded = _FirstAssignmentOnly(self._assignments)
        adopter = (
            self._meaning_factory(guarded) if self._meaning_factory is not None
            else self._auto_meaning(guarded)
        )
        adopter._activate_safely(DEFAULT_PRINCIPAL, path)
        return "kept" if guarded.refused else ("adopted" if guarded.written else "failed")

    def _auto_meaning(self, guarded: Any) -> Any:
        """A Meaning search adopter whose only assignment writer is ``guarded``."""
        from .meaning_search_service import MeaningSearchService

        meaning = self._meaning
        return MeaningSearchService(
            self._db,
            assignment_service=guarded,
            profile_service=meaning._profiles,
            broker_provider=meaning._broker_provider,
            model=meaning._model,
            home_provider=meaning._home,
            wake=meaning._wake,
        )

    # ── the honest state read ────────────────────────────────────────

    def state(self, principal: Principal) -> dict[str, Any]:
        """Per capability: assigned / inherited_from_default / proposed / needs_setup."""
        self._assignments._require_owner(principal)
        from ..memory.engine import LOCAL_INHERITING_CAPABILITIES, _assignment_head

        registry = self._assignments._registry
        proposals = self.proposals()
        with self._db._connection() as conn:
            global_row = conn.execute(
                "SELECT h.assignment_id,h.revision,h.cleared FROM inference_assignment_heads h"
                " WHERE h.assignment_key='global'"
            ).fetchone()
            default: dict[str, Any]
            if global_row is not None and not int(global_row["cleared"]):
                lamp = assignment_lamp(conn, str(global_row["assignment_id"]), int(global_row["revision"]))
                # "made by" is durable on the revision (made_by column); the
                # receipt is evidence and may be absent.
                by_holdspeak = made_by_holdspeak(
                    conn, str(global_row["assignment_id"]), int(global_row["revision"]),
                )
                receipt = conn.execute(
                    """SELECT r.receipt_id FROM kernel_operations o
                         JOIN kernel_receipts r ON r.operation_id=o.operation_id
                        WHERE o.name=? AND r.result_ref=?""",
                    (ASSIGNED_OPERATION,
                     f"inference_assignment:{global_row['assignment_id']}@{global_row['revision']}"),
                ).fetchone()
                default = {
                    "status": "assigned",
                    "lamp": lamp,
                    "made_by": "holdspeak" if by_holdspeak else "owner",
                    "receipt_id": str(receipt["receipt_id"]) if receipt is not None else None,
                }
            else:
                default = {
                    "status": "proposed" if proposals else "needs_setup",
                    "lamp": None,
                    "made_by": None,
                    "receipt_id": None,
                    "cleared_by_owner": global_row is not None,
                }
            capabilities: list[dict[str, Any]] = []
            for capability_id in registry.capability_ids:
                definition = registry.require(capability_id)
                if definition.owner_visibility != "owner":
                    continue
                effective = self._assignments._resolve(conn, definition)
                inherited = effective.get("inherited_from")
                lamp = None
                assignment = effective.get("assignment") or {}
                if assignment.get("id"):
                    lamp = assignment_lamp(conn, str(assignment["id"]), int(assignment.get("revision") or 0))
                row: dict[str, Any] = {
                    "id": definition.id,
                    "label": definition.label,
                    "group": definition.group_id,
                    "inherited_from": inherited,
                    "lamp": lamp,
                    "reason": None,
                }
                if effective["status"] == "no_assignment":
                    if definition.id == "memory.embed":
                        row.update(state="needs_setup", reason="embedding_model_needed")
                    else:
                        row.update(state="proposed" if proposals else "needs_setup",
                                   reason="no_default")
                elif effective["status"] != "assigned":
                    row.update(state="needs_setup", reason="model_incompatible")
                elif inherited == "capability":
                    row.update(state="assigned")
                elif definition.id == "memory.embed":
                    # An embedding call never falls through to a chat model.
                    row.update(state="needs_setup", reason="embedding_model_needed",
                               inherited_from=None, lamp=None)
                elif definition.id in LOCAL_INHERITING_CAPABILITIES and _assignment_head(conn, definition.id) is None:
                    # A non-local default the owner did not make never carries
                    # memory off the machine.
                    row.update(state="needs_setup", reason="default_not_local_not_owner")
                else:
                    row.update(state="inherited_from_default")
                capabilities.append(row)
        return {
            "schema": "InferenceDefaultsState@1",
            "default": default,
            "proposals": proposals,
            "capabilities": capabilities,
        }


__all__ = [
    "ASSIGNED_OPERATION",
    "DEFAULT_PRINCIPAL",
    "InferenceDefaultService",
    "LOOPBACK_ENGINE_PORTS",
    "LoopbackOnlyError",
    "is_chat_model",
    "loopback_profile_id",
    "parameter_billions",
    "rank_key",
    "require_loopback",
    "scan_loopback_engines",
]
