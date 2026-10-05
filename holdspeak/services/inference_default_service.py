"""Batteries-included default for AI work (owner ruling 2026-10-05).

"Strong defaults, batteries included":

* When a usable engine runs on THIS machine, HoldSpeak makes it the
  "Default for AI work" (the ``global`` assignment) by itself, with a
  receipt (``inference.default_assigned``) and the LOCAL lamp.
* A network (LAN, mesh) or cloud engine is never assigned by itself.  It is
  stored as a proposal; the owner's "Use it" press assigns it.
* An assignment the owner made is never changed.  The rule acts only when
  the ``global`` head has never existed: a default the owner cleared stays
  cleared.

Detection here reads loopback ports only (``scan_loopback_engines``):
Ollama 11434, LM Studio 1234, llama.cpp 8080 and 8000 on 127.0.0.1.  A
non-loopback host is refused before any socket is opened, and the scan
opener ignores HTTP proxy settings, so a scan request never leaves the
machine.

Ranking (``rank_key``), among candidates that answered their health probe:

1. A model whose size is known ranks before a model whose size is unknown.
2. The larger parameter count first.  The count is read from Ollama's own
   ``details.parameter_size``, else from the model name (``qwen3:8b``,
   ``Qwen3.5-27B-Instruct``); a mixture ``8x7b`` counts 56.
3. A model from the signed catalogue before an unsigned one.
4. An engine already in the Model Library, then Ollama, LM Studio,
   llama.cpp 8080, llama.cpp 8000.
5. The model name.

The winner is assigned only after its readiness probe says ``ready``; the
next candidate is tried when it does not.
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
from urllib.request import ProxyHandler, Request, build_opener

from ..inference_locality import LAMP_RANK, assignment_lamp, deployment_lamp
from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .errors import NotFound, ServiceError, ValidationError

log = get_logger("inference.default")

#: The principal of the product's own default write.
DEFAULT_PRINCIPAL = Principal(PrincipalKind.OWNER, "batteries-default")
#: The kernel operation that records the product's own default write.
ASSIGNED_OPERATION = "inference.default_assigned"
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


_NO_PROXY_OPENER = build_opener(ProxyHandler({}))


def _loopback_get(url: str, *, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    """GET one loopback URL.  Proxies are ignored; a non-loopback URL is refused."""
    require_loopback(urlparse(url).hostname or "")
    request = Request(url, headers=headers, method="GET")
    with _NO_PROXY_OPENER.open(request, timeout=timeout) as response:  # noqa: S310 - loopback only
        return int(getattr(response, "status", 200) or 200), response.read()


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
    ) -> None:
        self._db = db
        self._assignments = assignment_service
        self._library = model_library_service
        self._meaning = meaning_search
        self._home = home_provider
        self._scan = scan or scan_loopback_engines
        self._detect_http_get = detect_http_get
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

    def _global_ever_existed(self) -> bool:
        with self._db._connection() as conn:
            return conn.execute(
                "SELECT 1 FROM inference_assignment_heads WHERE assignment_key='global'"
            ).fetchone() is not None

    def ensure(self, *, reason: str = "boot") -> dict[str, Any]:
        """Assign the local default once, or record proposals.  Never overwrites."""
        with self._lock:
            result: dict[str, Any] = {"reason": reason, "assigned": None, "proposals": 0}
            try:
                result["memory_embed"] = self._ensure_meaning_search()
            except Exception as exc:
                log.warning("meaning search adopt failed: %s", exc)
                result["memory_embed"] = "failed"
            if self._global_ever_existed():
                # The owner's default (or one already made, then maybe cleared
                # by him) is never changed here.
                result["status"] = "kept"
                return result
            candidates = self._local_candidates()
            for candidate in sorted(candidates, key=rank_key):
                assigned = self._try_assign(candidate)
                if assigned is not None:
                    result.update(status="assigned", assigned=assigned)
                    return result
            result["proposals"] = self._record_proposals()
            result["status"] = "proposed" if result["proposals"] else "needs_setup"
            return result

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
        """Model Library profiles that run on this machine and are ready now."""
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
                observation = conn.execute(
                    "SELECT state FROM model_profile_readiness_observations WHERE observation_id=?",
                    (binding["readiness_observation_id"],),
                ).fetchone()
                if observation is None or str(observation["state"]) != "ready":
                    continue
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

    def _ready(self, profile_id: str, revision: int) -> bool:
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT o.state FROM model_profile_binding_heads h
                     JOIN model_profile_binding_revisions b
                       ON b.binding_id=h.binding_id AND b.revision=h.revision
                     JOIN model_profile_readiness_observations o
                       ON o.observation_id=b.readiness_observation_id
                    WHERE h.profile_id=? AND b.profile_revision=? AND b.enabled=1""",
                (profile_id, revision),
            ).fetchone()
        return row is not None and str(row["state"]) == "ready"

    def _try_assign(self, candidate: dict[str, Any]) -> Optional[dict[str, Any]]:
        try:
            if candidate["source"] == "loopback":
                reference = self._register_loopback(candidate)
                if reference is None:
                    return None
            else:
                reference = (candidate["profile_id"], int(candidate["profile_revision"]))
            profile_id, revision = reference
            if not self._ready(profile_id, revision):
                log.info("default candidate %s is not ready; trying the next", candidate["id"])
                return None
            result = self._assignments.set_assignment(DEFAULT_PRINCIPAL, {
                "command_id": f"batteries-default-{uuid.uuid4().hex}",
                # 0: only when no default ever existed.  A head the owner made
                # in the meantime makes this a revision conflict, never a write.
                "expected_revision": 0,
                "scope": {"kind": "global"},
                "entries": [{"profile_id": profile_id, "profile_revision": revision}],
            })
        except (ServiceError, ValidationError) as exc:
            log.info("default candidate %s refused: %s", candidate.get("id"), getattr(exc, "code", exc))
            return None
        assignment_id = str(result.get("id") or "")
        assignment_revision = int(result.get("revision") or 1)
        with self._db._connection() as conn:
            lamp = assignment_lamp(conn, assignment_id, assignment_revision)
        if lamp != "local":  # pragma: no cover - candidates are local by construction
            log.error("batteries default %s is not local (%s)", candidate["id"], lamp)
        label = str(candidate.get("label") or f"{candidate['model']} on {candidate['engine']}")
        receipt_id = self._write_receipt(
            assignment_id=assignment_id,
            assignment_revision=assignment_revision,
            label=label,
            profile_id=profile_id,
            lamp=lamp,
        )
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

    def _ensure_meaning_search(self) -> str:
        """Use the on-device embedding model for ``memory.embed`` when present.

        Only a file already on this device (hash checked) is used: nothing is
        downloaded here.  Only when ``memory.embed`` never had a head: a
        Turn off by the owner stays off.
        """
        meaning = self._meaning
        if meaning is None:
            return "no_service"
        with self._db._connection() as conn:
            if conn.execute(
                "SELECT 1 FROM inference_assignment_heads WHERE assignment_key='capability:memory.embed'"
            ).fetchone() is not None:
                return "kept"
        import importlib.util

        if importlib.util.find_spec("llama_cpp") is None:
            return "runtime_missing"
        from ..memory.local_model import EMBED_MODEL, find_on_device

        path = find_on_device(EMBED_MODEL, self._home())
        if path is None:
            return "model_missing"
        # The adopt step of Turn on, without its download branch: this call
        # can never send a request off the machine.
        with meaning._lock:
            meaning._activate_safely(DEFAULT_PRINCIPAL, path)
        return "adopted"

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
                made = conn.execute(
                    """SELECT r.receipt_id FROM kernel_operations o
                         JOIN kernel_receipts r ON r.operation_id=o.operation_id
                        WHERE o.name=? AND r.result_ref=?""",
                    (ASSIGNED_OPERATION,
                     f"inference_assignment:{global_row['assignment_id']}@{global_row['revision']}"),
                ).fetchone()
                default = {
                    "status": "assigned",
                    "lamp": lamp,
                    "made_by": "holdspeak" if made is not None else "owner",
                    "receipt_id": str(made["receipt_id"]) if made is not None else None,
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
                    # A network or cloud default does not carry memory off the machine.
                    row.update(state="needs_setup", reason="default_not_local")
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
