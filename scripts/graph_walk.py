#!/usr/bin/env python3
"""THE GRAPH WALK — the one versioned rig of the Philo graph audit (brief §7).

Both brains drive every live case through this one entry point, so that two
independent passes can be compared. It decides nothing by the presence of a
diff: a case declares its expected result as a predicate over a SCOPED
observation, the rig records the diff beside the verdict as evidence, and the
predicate alone decides (brief §3, the outcome law; Astra's finding 1).

Two subcommands:

    # the six calibration cases of brief §7, against a local static page
    uv run python scripts/graph_walk.py calibrate --out .tmp/graph-walk

    # one real case from an atlas, against a real hub in a fresh HOME
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \\
      uv run python scripts/graph_walk.py run \\
        --atlas tests/fixtures/graph_walk_sample_atlas.json \\
        --case J9-sweep-receipt-open --brain muaddib --viewport 1440 \\
        --out .tmp/graph-walk

`serve` is the rig's own hub subprocess; it is not a walk.

CONTRACTS
---------
CASE (brief §8 / the phase contract), as this rig consumes it::

    {"id", "job", "edge_ids": [...], "state_id", "applicability",
     "preconditions", "setup": [step...], "trigger": step,
     "expected": {"predicate": {...}, "observe_at": "<css>",
                  "pending_marker": "<css>"?, "reads": [{method, path}]?},
     "completion_bound_s", "viewports": [1440, 393]}

`trigger` is this rig's one addition to the field list carried in the story
brief: §7 requires the trigger to be fired through its real entry point and
the field list does not name it. A step marked `"is_trigger": true` inside
`setup` is accepted instead, so an atlas written either way runs. REPORTED as
a contract gap to reconcile with the atlas author.

A step is `{"kind": "api"|"ui"|"fixture"|"clock"|"boundary", ...}`:

  api       {method, path, body?, expect_status?}   HTTP against the hub
  ui        {action: goto|click|click_role|fill|press|wait_for, ...}
  fixture   {path, route:{method,path}, field?}     the WAV at the documented
            input boundary — never a microphone
  clock     {adapter, clock, how, max_wait_s?, poll_s?}
            ONE mechanism is implemented: `adapter: "scheduler-wait"` waits
            (slow polls, ≤ the case's completion_bound_s) for the REAL
            scheduler to change `expected.observe_at`. No clock is moved.
            Every other clock mechanism is recorded `blocked` with its name.
  boundary  {label, api?}                           a labelled substitution,
            recorded in the observation's provenance

Every step carries an `adapter` string naming the real entry point it drives
(`ui-pointer`, `http-route`, `scheduler-entry`, …); it is recorded, never
inferred. A timer edge is driven by its scheduler entry, never by a
substitute button.

OBSERVATION: one JSON per run, in its own directory, never overwritten.
Partial records survive a stopped run: the file is flushed at every stage.

PREDICATES (`expected.predicate.kind`):

  text_contains / text_equals / text_absent {value}
  attr_equals {attr, value}
  window_titled {value}          a window with that title, absent before
  presentation_change {fields}   focus | geometry | windows — a valid
                                 presentation change, promised by the contract
  unchanged {replay_identity}    an idempotent/read contract: the same result
                                 AND the same recorded replay identity. An
                                 unexplained zero diff is UNRESOLVED, not pass.
  protocol_rows {collection, match, min_new}
                                 for `observe_at: "protocol: GET /path"` — a
                                 named NEW row must appear in that route's
                                 collection. `field__prefix` matches a prefix.

A predicate written in PROSE is not read: the run is recorded in full and the
verdict is `blocked`, naming the structure the rig needs.

LAWS OBEYED
-----------
* never the owner's HOME, data, keychain or microphone: the hub runs in a
  fresh mkdtemp HOME and the resolved db path is VERIFIED under it before any
  action; a runtime path under the real user's ~/.local or ~/.holdspeak is
  refused outright.
* run-specific output directory; no tracked shot is ever touched.
* one case per invocation, one hub at a time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

RIG_VERSION = "1.0.0"

REPO = Path(__file__).resolve().parents[1]
CALIBRATION_PAGE = REPO / "tests/fixtures/graph_walk_calibration.html"
BRIEF = REPO / "docs/internal/philo/briefs/graph-audit-brief.md"
BUILT_INDEX = REPO / "holdspeak/static/_built/index.html"
TOKEN = "graph-walk-token"

VERDICTS = ("pass", "fail", "blocked", "not_run", "not_applicable")

# The real user's home, read from the passwd database so that it is the owner's
# home even when HOME points at a temporary directory. Nothing this rig runs
# may resolve under these.
_REAL_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)
FORBIDDEN_ROOTS = (
    _REAL_HOME / ".local",
    _REAL_HOME / ".holdspeak",
    Path("/Users/karol/.local"),
    Path("/Users/karol/.holdspeak"),
)


class Refused(RuntimeError):
    """The rig refuses to act (a path guard, never a product finding)."""


class Blocked(RuntimeError):
    """The case cannot be exercised; it is recorded `blocked` with the reason."""


# ────────────────────────────────────────────────────────── the guards ──


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def guard_path(path: str | Path, what: str) -> Path:
    """Refuse any runtime path under the real user's data or config roots."""
    resolved = Path(path).expanduser().resolve()
    for root in FORBIDDEN_ROOTS:
        if resolved == root or _under(resolved, root):
            raise Refused(
                f"refusing to run: {what} resolves to {resolved}, under the "
                f"owner's {root}. Run with HOME=$(mktemp -d)."
            )
    return resolved


def guard_home(home: str | Path) -> Path:
    """The run's HOME, guarded. Also refuses the real user's home itself."""
    resolved = Path(home).expanduser().resolve()
    if resolved == _REAL_HOME:
        raise Refused(
            f"refusing to run: HOME is the owner's own home ({resolved}). "
            "Run with HOME=$(mktemp -d)."
        )
    return guard_path(resolved, "HOME")


# ─────────────────────────────────────────────────────────── provenance ──


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), *args],
            capture_output=True, text=True, timeout=30,
        )
        return out.stdout.strip()
    except Exception as exc:  # noqa: BLE001 — provenance never kills a run
        return f"<unavailable: {exc!r}>"


def _frontend_build() -> dict[str, Any]:
    """The built bundle's identity, as the hub serves it."""
    if not BUILT_INDEX.exists():
        return {"built": False, "reason": f"{BUILT_INDEX} does not exist"}
    text = BUILT_INDEX.read_text()
    assets = sorted(
        part.split('"')[0]
        for part in text.split('src="/_built/assets/')[1:]
    )
    return {
        "built": True,
        "index_sha256": _sha256(BUILT_INDEX),
        "assets": assets,
    }


def base_provenance(*, engine_mode: str) -> dict[str, Any]:
    assert engine_mode in ("real", "replayed", "none"), engine_mode
    return {
        "revision": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain")),
        "frontend_build": None,
        "hub": None,
        "db_path": None,
        "fixture_hashes": {},
        "clock": {
            "tz": os.environ.get("TZ"),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "mechanism": "none — the real clock; no case may claim an advance",
        },
        "engine_mode": engine_mode,
        "boundary_substitutions": [],
        "rig_version": RIG_VERSION,
        "brief_sha256": _sha256(BRIEF) if BRIEF.exists() else None,
    }


# ───────────────────────────────────────────────────── the observation ──

_SNAPSHOT_JS = r"""([selector, pending]) => {
  const path = (el) => {
    if (!el || el === document.body) return el ? "body" : null;
    const bits = [];
    let node = el;
    while (node && node.nodeType === 1 && bits.length < 6) {
      let bit = node.tagName.toLowerCase();
      if (node.id) { bits.unshift(bit + "#" + node.id); break; }
      if (node.className && typeof node.className === "string") {
        bit += "." + node.className.trim().split(/\s+/).slice(0, 2).join(".");
      }
      bits.unshift(bit);
      node = node.parentElement;
    }
    return bits.join(" > ");
  };
  const box = (el) => {
    const r = el.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)};
  };
  const el = selector ? document.querySelector(selector) : null;
  const attrs = {};
  if (el) for (const a of el.attributes) attrs[a.name] = a.value;
  const windows = [...document.querySelectorAll(".desk-window")].map((w) => ({
    title: ((w.querySelector(".desk-window-title") || {}).textContent || "").trim(),
    rect: box(w),
    visible: !!(w.offsetWidth || w.offsetHeight || w.getClientRects().length),
  }));
  const active = document.activeElement;
  return {
    observe_at: selector,
    target_present: !!el,
    text: el ? (el.innerText || el.textContent || "").trim() : null,
    attrs: el ? attrs : null,
    rect: el ? box(el) : null,
    visible: el ? !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length) : null,
    focus: path(active),
    focus_label: active ? (active.getAttribute("aria-label") ||
      (active.innerText || "").trim().slice(0, 60)) : null,
    url: location.href,
    windows,
    pending_marker_present: pending ? !!document.querySelector(pending) : null,
    body_text: (document.body.innerText || "").slice(0, 40000),
  };
}"""


PROTOCOL_PREFIX = "protocol:"


def protocol_target(observe_at: Any) -> tuple[str, str] | None:
    """`protocol: GET /api/desk/projections` -> ("GET", "/api/desk/projections").

    A protocol-only case has no invented viewport requirement (brief §4); its
    observation location is a route, not a selector.
    """
    if not isinstance(observe_at, str):
        return None
    text = observe_at.strip()
    if not text.startswith(PROTOCOL_PREFIX):
        return None
    rest = text[len(PROTOCOL_PREFIX):].strip()
    parts = rest.split()
    if len(parts) >= 2:
        return parts[0].upper(), parts[1]
    return "GET", rest


def _collection_of(payload: Any, predicate: Any) -> str | None:
    if isinstance(predicate, dict) and predicate.get("collection"):
        return predicate["collection"]
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, list):
                return key
    return None


def snapshot(page: Any, case: dict[str, Any], hub: Any | None = None) -> dict[str, Any]:
    """The SCOPED observation: the intended object, plus the presentation state.

    Background activity cannot make a dead action pass, because the predicate
    only ever reads `observe_at`, the window set, focus and the URL. The
    document text is kept as a digest — evidence that something moved, never
    a criterion.
    """
    expected = case.get("expected", {})
    predicate = expected.get("predicate")
    target = protocol_target(expected.get("observe_at"))
    raw = page.evaluate(
        _SNAPSHOT_JS,
        [None if target else expected.get("observe_at"), expected.get("pending_marker")],
    )
    raw["observe_at"] = expected.get("observe_at")
    if target is not None:
        method, path = target
        status, payload = (hub.api(method, path) if hub is not None else (0, None))
        collection = _collection_of(payload, predicate)
        rows = payload.get(collection) if (collection and isinstance(payload, dict)) else []
        raw["protocol"] = {
            "method": method, "path": path, "status": status,
            "collection": collection,
            "row_count": len(rows) if isinstance(rows, list) else None,
            "payload_sha256": hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
            "rows": rows[:50] if isinstance(rows, list) else rows,
        }
        # the diff reads the digest, never the whole payload
        raw["protocol_digest"] = {"status": status,
                                  "row_count": raw["protocol"]["row_count"],
                                  "payload_sha256": raw["protocol"]["payload_sha256"]}
    body = raw.pop("body_text", "") or ""
    raw["document_text_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    raw["document_text_len"] = len(body)
    raw["_body_text"] = body  # stripped before the record is written
    identity = predicate.get("replay_identity") if isinstance(predicate, dict) else None
    raw["replay_identity"] = _read_identity(page, identity) if identity else None
    reads = expected.get("reads") or []
    if reads and hub is not None:
        collected = []
        for read in reads:
            status, payload = hub.api(read["method"], read["path"])
            collected.append({
                "method": read["method"], "path": read["path"], "status": status,
                "body_sha256": hashlib.sha256(
                    json.dumps(payload, sort_keys=True, default=str).encode()
                ).hexdigest(),
            })
        raw["api_reads"] = collected
    raw["at_utc"] = datetime.now(timezone.utc).isoformat()
    return raw


def _read_identity(page: Any, spec: str) -> dict[str, Any]:
    """`#sel@attr` — the replay identity an idempotent contract must repeat."""
    selector, _, attr = spec.partition("@")
    value = page.evaluate(
        """([selector, attr]) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            return attr ? el.getAttribute(attr) : (el.innerText || "").trim();
        }""",
        [selector, attr],
    )
    return {"spec": spec, "value": value}


_DIFF_KEYS = (
    "target_present", "text", "attrs", "rect", "visible", "focus", "focus_label",
    "url", "windows", "document_text_sha256", "document_text_len",
    "replay_identity", "api_reads", "protocol_digest",
)


def diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """The recorded diff. EVIDENCE TO INSPECT — never a success criterion."""
    changed: dict[str, Any] = {}
    for key in _DIFF_KEYS:
        if before.get(key) != after.get(key):
            changed[key] = {"before": before.get(key), "after": after.get(key)}
    return changed


def _clean(snap: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in snap.items() if not k.startswith("_")}


# ────────────────────────────────────────────────────── the predicates ──


def check_predicate(
    predicate: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[bool, str]:
    """The ONE decision: the expected result against the observed one."""
    if not isinstance(predicate, dict):
        # A prose expected result cannot be machine-checked, and the rig will
        # not read prose and call the answer a verdict. The case is recorded
        # `blocked` with the evidence it did gather.
        return False, (
            "UNDECIDABLE: the case states its expected result in prose "
            f"({str(predicate)[:160]!r}). The rig needs a structured predicate "
            "(e.g. {\"kind\": \"protocol_rows\", \"collection\": …, \"match\": …}).")
    kind = predicate.get("kind")
    text = after.get("text") or ""

    if kind == "protocol_rows":
        gained_before = match_rows(before, predicate)
        gained_after = match_rows(after, predicate)
        need = int(predicate.get("min_new", 1))
        new = len(gained_after) - len(gained_before)
        reading = (f"rows matching {predicate.get('match')!r} at "
                   f"{(after.get('protocol') or {}).get('path')}: "
                   f"before={len(gained_before)} after={len(gained_after)} "
                   f"(needed {need} new)")
        if (after.get("protocol") or {}).get("status", 0) >= 400:
            return False, f"the route answered {(after['protocol'])['status']}; " + reading
        return new >= need, reading

    if kind == "text_contains":
        want = predicate["value"]
        return (want in text), f"{want!r} {'in' if want in text else 'NOT in'} observe_at text"
    if kind == "text_equals":
        want = predicate["value"]
        return (text.strip() == want), f"observe_at text is {text.strip()!r}, wanted {want!r}"
    if kind == "text_absent":
        want = predicate["value"]
        return (want not in text), f"{want!r} {'absent' if want not in text else 'PRESENT'} at observe_at"
    if kind == "attr_equals":
        attrs = after.get("attrs") or {}
        got = attrs.get(predicate["attr"])
        return (got == predicate["value"]), f"{predicate['attr']}={got!r}, wanted {predicate['value']!r}"
    if kind == "window_titled":
        want = predicate["value"]
        titles_after = [w["title"] for w in after.get("windows", []) if w.get("visible")]
        titles_before = [w["title"] for w in before.get("windows", []) if w.get("visible")]
        opened = any(want in t for t in titles_after)
        was_open = any(want in t for t in titles_before)
        if was_open and predicate.get("must_be_new", True):
            return False, f"a window titled {want!r} was ALREADY open before the trigger"
        return opened, f"windows after: {titles_after!r}"
    if kind == "presentation_change":
        fields = predicate.get("fields") or ["focus"]
        moved, still = [], []
        for field in fields:
            if field == "focus":
                (moved if before.get("focus") != after.get("focus") else still).append("focus")
            elif field == "geometry":
                geo_b = [w["rect"] for w in before.get("windows", [])]
                geo_a = [w["rect"] for w in after.get("windows", [])]
                (moved if geo_b != geo_a else still).append("geometry")
            elif field == "windows":
                set_b = [w["title"] for w in before.get("windows", [])]
                set_a = [w["title"] for w in after.get("windows", [])]
                (moved if set_b != set_a else still).append("windows")
            else:
                return False, f"unknown presentation field {field!r}"
        if predicate.get("text_must_hold", True) and before.get("text") != after.get("text"):
            return False, "the contract promised presentation only; observe_at text changed"
        return (not still), f"changed: {moved!r}; unchanged: {still!r}"
    if kind == "unchanged":
        same = (before.get("text") == after.get("text")
                and (before.get("attrs") or {}) == (after.get("attrs") or {}))
        if not same:
            return False, "the contract promised an unchanged result; it changed"
        identity_before = (before.get("replay_identity") or {}).get("value")
        identity_after = (after.get("replay_identity") or {}).get("value")
        if not predicate.get("replay_identity"):
            return False, (
                "UNRESOLVED: a zero diff with no recorded replay identity. "
                "An unexplained zero diff cannot pass (brief §3)."
            )
        if identity_after is None:
            return False, f"the replay identity {predicate['replay_identity']!r} was not readable"
        if identity_before != identity_after:
            return False, f"replay identity moved: {identity_before!r} -> {identity_after!r}"
        return True, f"unchanged result with the same replay identity {identity_after!r}"
    return False, f"unknown predicate kind {kind!r}"


def match_rows(snap: dict[str, Any], predicate: dict[str, Any]) -> list[dict[str, Any]]:
    """The rows a `protocol_rows` predicate promises. `field__prefix` matches a
    prefix; every other key is exact."""
    rows = (snap.get("protocol") or {}).get("rows") or []
    match = predicate.get("match") or {}
    found = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ok = True
        for key, want in match.items():
            if key.endswith("__prefix"):
                ok = ok and str(row.get(key[: -len("__prefix")], "")).startswith(str(want))
            else:
                ok = ok and row.get(key) == want
        if ok:
            found.append(row)
    return found


def found_elsewhere(predicate: dict[str, Any], after: dict[str, Any]) -> str | None:
    """A wrong-target result: the promised text exists, but not where promised."""
    if not isinstance(predicate, dict):
        return None
    want = predicate.get("value")
    if predicate.get("kind") not in ("text_contains", "text_equals") or not want:
        return None
    if want in (after.get("text") or ""):
        return None
    if want in (after.get("_body_text") or ""):
        return (f"WRONG TARGET: {want!r} is on the page but NOT at "
                f"{after.get('observe_at')!r}")
    return None


# ────────────────────────────────────────────────────────────── the hub ──


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class Hub:
    """A real hub in its own process, with its own fresh isolated HOME."""

    def __init__(self, home: Path, token: str = TOKEN, *, scheduler: bool = False) -> None:
        self.home = guard_home(home)
        self.token = token
        self.scheduler = scheduler
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen[str] | None = None
        self.db_path: str | None = None
        self.lines: list[str] = []

    def _drain(self) -> None:
        assert self.proc is not None and self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.append(line.rstrip())
            if line.startswith("DB_PATH "):
                self.db_path = line.split(" ", 1)[1].strip()

    def start(self, timeout: float = 180.0) -> "Hub":
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["PYTHONUNBUFFERED"] = "1"
        env.pop("HOLDSPEAK_DB_PATH", None)
        command = [sys.executable, str(Path(__file__).resolve()), "serve",
                   "--port", str(self.port), "--token", self.token]
        if self.scheduler:
            command.append("--scheduler")
        self.proc = subprocess.Popen(
            command,
            cwd=str(REPO), env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        threading.Thread(target=self._drain, daemon=True).start()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("hub died on boot:\n" + "\n".join(self.lines[-40:]))
            if any(line.startswith("HUB_READY") for line in self.lines) and self.healthy():
                self._verify_paths()
                return self
            time.sleep(0.5)
        self.stop()
        raise RuntimeError(f"hub never became healthy at {self.url}")

    def _verify_paths(self) -> None:
        """§7: verify the resolved runtime paths BEFORE exercising anything."""
        if not self.db_path:
            raise Refused("the hub never reported its database path; refusing to act")
        resolved = guard_path(self.db_path, "the hub database")
        if not _under(resolved, self.home):
            raise Refused(
                f"refusing to act: the hub database {resolved} is not under the "
                f"run's HOME {self.home}"
            )

    def healthy(self) -> bool:
        try:
            status, _ = self.api("GET", "/health")
        except Exception:  # noqa: BLE001
            return False
        return status == 200

    def api(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.url}{path}", data=data, method=method,
            headers={"X-HoldSpeak-Token": self.token,
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except Exception:  # noqa: BLE001
                    return resp.status, raw[:2000]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()[:2000]

    def upload(self, method: str, path: str, wav: Path, field: str) -> tuple[int, Any]:
        """The fixture WAV at the documented input boundary. Never a microphone."""
        boundary = uuid.uuid4().hex
        head = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field}"; filename="{wav.name}"\r\n'
            "Content-Type: audio/wav\r\n\r\n"
        ).encode()
        payload = head + wav.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{self.url}{path}", data=payload, method=method,
            headers={"X-HoldSpeak-Token": self.token,
                     "Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except Exception:  # noqa: BLE001
                    return resp.status, raw[:2000]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()[:2000]

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=15)


def _start_real_heartbeat_conductor() -> None:
    """Start the product's OWN heartbeat conductor loop in this hub.

    `HeartbeatMixin._heartbeat_loop` (holdspeak/runtime/heartbeat.py:77) is the
    real timer: the same 60s tick, the same due test, the same
    `HeartbeatService.run_sweep(principal)` with `owner_hand` unset. In the
    product it is started by `WebRuntime.run` via `_start_scheduled_work`
    (holdspeak/runtime/ownership.py:150).

    The rig starts that loop and NOT the rest of `WebRuntime.run`, because
    that constructor opens an `AudioRecorder` on the microphone and installs a
    global `HotkeyListener` (holdspeak/web_runtime.py:507-517) — both forbidden
    to this rig (brief §7). The loop itself is the product's, not a substitute;
    the substitution is recorded in the observation.
    """
    from holdspeak.runtime.heartbeat import HeartbeatMixin

    class _Conductor(HeartbeatMixin):
        def __init__(self) -> None:
            self.runtime_stop_event = threading.Event()

    _Conductor()._start_heartbeat_thread()
    print("SCHEDULER heartbeat conductor thread started "
          "(HeartbeatMixin._heartbeat_loop, TICK_SECONDS=60)", flush=True)


def _serve(port: int, token: str, host: str = "127.0.0.1",
           scheduler: bool = False) -> None:
    """The rig's hub subprocess: a real MeetingWebServer on a fresh HOME."""
    guard_home(os.environ.get("HOME", "/nonexistent"))
    from holdspeak.db import get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    database = get_database()
    print(f"DB_PATH {database.db_path}", flush=True)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {"active": False, "id": "", "status": "idle"},
        ),
        host=host, port=port, auth_token=token,
    )
    url = server.start()
    if scheduler:
        _start_real_heartbeat_conductor()
    print(f"HUB_READY {url}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:  # pragma: no cover — operator interrupt
        pass


# ──────────────────────────────────────────── the calibration page host ──


class _CalibrationHandler(BaseHTTPRequestHandler):
    """The static page, plus the one route case (b)'s request answers."""

    def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's name
        if self.path.startswith("/echo"):
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = CALIBRATION_PAGE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: Any) -> None:  # quiet
        return


# ─────────────────────────────────────────────── the calibration cases ──
#
# brief §7: "Calibrate the rig against a dead action, a request with no
# promised result, a wrong-target result, valid focus/geometry changes, an
# unchanged-result contract and an operation that never completes. None may be
# classified solely by the presence of a diff."
#
# They are written in the SAME case contract and run through the SAME engine
# as a real case, or they would calibrate nothing.

CALIBRATION_BOUND = 2.0

CALIBRATION_CASES: list[dict[str, Any]] = [
    {
        "id": "CAL-a-dead-action",
        "job": "a dead button that does nothing",
        "edge_ids": ["cal:a"], "state_id": "cal:page",
        "applicability": {"applicable": True},
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#a-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#a-out",
                     "predicate": {"kind": "text_contains", "value": "saved"}},
        "completion_bound_s": CALIBRATION_BOUND, "viewports": [1440],
    },
    {
        "id": "CAL-b-request-without-result",
        "job": "a request the route answers; the promised text never appears",
        "edge_ids": ["cal:b"], "state_id": "cal:page",
        "applicability": {"applicable": True},
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#b-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#b-out",
                     "predicate": {"kind": "text_contains", "value": "Saved to the desk"}},
        "completion_bound_s": CALIBRATION_BOUND, "viewports": [1440],
    },
    {
        "id": "CAL-c-wrong-target",
        "job": "the result lands in the wrong target",
        "edge_ids": ["cal:c"], "state_id": "cal:page",
        "applicability": {"applicable": True},
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#c-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#c-out",
                     "predicate": {"kind": "text_contains", "value": "saved"}},
        "completion_bound_s": CALIBRATION_BOUND, "viewports": [1440],
    },
    {
        "id": "CAL-d-presentation-only",
        "job": "focus and geometry move, under a contract that promises exactly that",
        "edge_ids": ["cal:d"], "state_id": "cal:page",
        "applicability": {"applicable": True},
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#d-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#d-out",
                     "predicate": {"kind": "presentation_change",
                                   "fields": ["focus", "geometry"]}},
        "completion_bound_s": CALIBRATION_BOUND, "viewports": [1440],
    },
    {
        "id": "CAL-e-idempotent-refresh",
        "job": "an idempotent refresh: the same result and the same replay identity",
        "edge_ids": ["cal:e"], "state_id": "cal:page",
        "applicability": {"applicable": True},
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#e-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#e-out",
                     "predicate": {"kind": "unchanged",
                                   "replay_identity": "#e-out@data-replay-id"}},
        "completion_bound_s": CALIBRATION_BOUND, "viewports": [1440],
    },
    {
        "id": "CAL-f-never-completes",
        "job": "an operation that never completes within its bound",
        "edge_ids": ["cal:f"], "state_id": "cal:page",
        "applicability": {"applicable": True},
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#f-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#f-out",
                     "pending_marker": "#f-out[aria-busy='true']",
                     "predicate": {"kind": "text_contains", "value": "ready"}},
        "completion_bound_s": CALIBRATION_BOUND, "viewports": [1440],
    },
]

# NOT one of the six. It calibrates the `scheduler-wait` clock adapter against
# a stand-in scheduler in the same static page: setup arms the timer (as the
# real case lowers `sweep_every_minutes` to its floor), and then nothing is
# pressed — the timer alone must produce the promised result.
CALIBRATION_SCHEDULER_CASE: dict[str, Any] = {
    "id": "CAL-g-scheduler-wait",
    "job": "a timer edge: the result arrives from the scheduler, not from a button",
    "edge_ids": ["cal:g"], "state_id": "cal:page",
    "applicability": "applicable",
    "preconditions": "the calibration page is loaded and the stand-in timer is armed",
    "setup": [{"kind": "ui", "action": "click", "selector": "#g-arm",
               "adapter": "ui-pointer",
               "why": "arming the timer is SETUP; it is not the trigger"}],
    "trigger": {"kind": "clock", "clock": "cal.stand_in_timer",
                "how": "no clock is moved: the run waits for the page's own timer",
                "adapter": "scheduler-wait", "max_wait_s": 20, "poll_s": 1},
    "expected": {"observe_at": "#g-out",
                 "predicate": {"kind": "text_contains", "value": "tick"}},
    "completion_bound_s": 25, "viewports": [1440],
}

# What the rig MUST say about each calibration case, and why. A mismatch is a
# broken rig: `calibrate` exits nonzero and no live pass may be run with it.
CALIBRATION_EXPECTED: dict[str, tuple[str, str]] = {
    "CAL-a-dead-action": ("fail", "settled"),
    "CAL-b-request-without-result": ("fail", "settled"),
    "CAL-c-wrong-target": ("fail", "settled"),
    "CAL-d-presentation-only": ("pass", "settled"),
    "CAL-e-idempotent-refresh": ("pass", "settled"),
    "CAL-f-never-completes": ("fail", "incomplete"),
}


# ───────────────────────────────────────────────────────── the steps ──


def _ui_step(page: Any, step: dict[str, Any]) -> dict[str, Any]:
    action = step["action"]
    optional = bool(step.get("optional"))
    record = {"kind": "ui", "action": action, "adapter": step.get("adapter", "ui-pointer")}
    timeout = float(step.get("timeout_s", 10)) * 1000
    try:
        if action == "goto":
            page.goto(step["url"])
        elif action == "reload":
            page.reload(wait_until=step.get("wait_until", "load"))
        elif action == "click":
            page.locator(step["selector"]).first.click(timeout=timeout)
            record["selector"] = step["selector"]
        elif action == "click_role":
            page.get_by_role(
                step.get("role", "button"), name=step["name"],
                exact=bool(step.get("exact", True)),
            ).first.click(timeout=timeout)
            record["name"] = step["name"]
        elif action == "fill":
            page.locator(step["selector"]).first.fill(step["value"], timeout=timeout)
        elif action == "press":
            page.keyboard.press(step["key"])
            record["key"] = step["key"]
        elif action == "wait_for":
            page.locator(step["selector"]).first.wait_for(
                state=step.get("state", "visible"), timeout=timeout)
            record["selector"] = step["selector"]
        else:
            raise Blocked(f"unknown ui action {action!r}")
        record["done"] = True
    except Blocked:
        raise
    except Exception as exc:  # noqa: BLE001
        record["done"] = False
        record["error"] = repr(exc)[:400]
        if not optional:
            raise Blocked(f"ui step {action} failed: {exc!r}"[:400]) from exc
    return record


# The conductor's own tick, mirrored from holdspeak/runtime/heartbeat.py:86.
TICK_SECONDS = 60


def _observe_digest(page: Any, case: dict[str, Any], hub: Hub | None) -> Any:
    """What the scheduler wait watches: the observation location itself."""
    snap = snapshot(page, case, hub)
    protocol = snap.get("protocol") or {}
    return protocol.get("payload_sha256") or snap.get("text")


def scheduler_wait(step: dict[str, Any], case: dict[str, Any] | None, page: Any,
                   hub: Hub | None, provenance: dict[str, Any]) -> dict[str, Any]:
    """The ONE clock mechanism this rig implements: wait for the real timer.

    No clock is moved. The case's setup lowers the interval to its floor
    (`sweep_every_minutes: 1`, holdspeak/services/heartbeat_service.py:176-178)
    and this waits, with slow polls, for the real conductor loop
    (holdspeak/runtime/heartbeat.py:86-126) to reach the producer. The
    out-of-band `POST /api/settings/heartbeat/run-now` is a DIFFERENT edge
    (`owner_hand=True`, holdspeak/web/routes/system/settings.py:337) and is
    never used as the timer's substitute.

    A wait that sees nothing is NOT a block: the predicate still decides.
    """
    if case is None:
        raise Blocked("a scheduler-wait needs its case (it watches observe_at)")
    observe_at = (case.get("expected") or {}).get("observe_at")
    if protocol_target(observe_at) is not None and hub is None:
        raise Blocked("a protocol scheduler-wait needs a hub to read the route")
    bound = float(case.get("completion_bound_s", 180))
    max_wait = min(float(step.get("max_wait_s", 2 * TICK_SECONDS + 15)), bound)
    poll_s = float(step.get("poll_s", 5))
    baseline = _observe_digest(page, case, hub)
    started = time.monotonic()
    polls = 0
    changed = False
    while time.monotonic() - started < max_wait:
        time.sleep(poll_s)
        polls += 1
        if _observe_digest(page, case, hub) != baseline:
            changed = True
            break
    waited = round(time.monotonic() - started, 1)
    ticks = int(waited // TICK_SECONDS) + (1 if waited % TICK_SECONDS else 0)
    provenance["clock"].update({
        "mechanism": step.get("how") or "scheduler-wait",
        "clock": step.get("clock"),
        "adapter": step.get("adapter"),
        "tick_seconds": TICK_SECONDS,
        "max_wait_s": max_wait,
        "waited_s": waited,
        "polls": polls,
        "conductor_ticks_waited": ticks,
        "observe_at_changed": changed,
        "machine_clock_moved": False,
    })
    return {"kind": "clock", "adapter": step.get("adapter"),
            "clock": step.get("clock"), "waited_s": waited, "polls": polls,
            "conductor_ticks_waited": ticks, "observe_at_changed": changed,
            "done": True}


def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
             provenance: dict[str, Any], case: dict[str, Any] | None = None) -> dict[str, Any]:
    """One setup step or the trigger, by kind. Records the adapter it drove."""
    kind = step["kind"]
    if kind == "ui":
        return _ui_step(page, step)
    if kind == "api":
        if hub is None:
            raise Blocked("an api step needs a hub; this pass has none")
        status, payload = hub.api(step["method"], step["path"], step.get("body"))
        record = {"kind": "api", "method": step["method"], "path": step["path"],
                  "adapter": step.get("adapter", "http-route"), "status": status,
                  "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
        want = step.get("expect_status")
        if want is not None and status != want:
            raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
        if want is None and status >= 400:
            raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
        return record
    if kind == "fixture":
        if hub is None:
            raise Blocked("a fixture step needs a hub; this pass has none")
        wav = REPO / step["path"]
        if not wav.exists():
            raise Blocked(f"fixture {wav} does not exist")
        provenance["fixture_hashes"][step["path"]] = _sha256(wav)
        route = step.get("route")
        if not route:
            raise Blocked(
                f"no documented input boundary declared for {step['path']}; "
                "the rig never opens a microphone")
        status, payload = hub.upload(
            route["method"], route["path"], wav, step.get("field", "file"))
        record = {"kind": "fixture", "path": step["path"], "route": route,
                  "adapter": step.get("adapter", "http-route"), "status": status,
                  "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
        if status >= 400:
            raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
        return record
    if kind == "clock":
        if str(step.get("adapter") or "").startswith("scheduler-wait"):
            return scheduler_wait(step, case, page, hub, provenance)
        named = step.get("mechanism") or step.get("clock") or step.get("adapter")
        raise Blocked(
            f"clock mechanism {named!r} is not implemented in this rig; the case "
            "is blocked, not claimed (brief §7: record tooling debt rather than "
            "claiming the state). The one implemented mechanism is "
            "adapter 'scheduler-wait'.")
    if kind == "boundary":
        label = step.get("label", "unlabelled")
        provenance["boundary_substitutions"].append(label)
        record: dict[str, Any] = {"kind": "boundary", "label": label,
                                  "adapter": step.get("adapter", "labelled-substitution")}
        inner = step.get("api")
        if inner:
            record["inner"] = run_step({"kind": "api", **inner}, page, hub, provenance, case)
        return record
    raise Blocked(f"unknown setup kind {kind!r}")


def case_applicable(case: dict[str, Any]) -> tuple[bool, str]:
    """`applicability` is a word in W2's atlas and an object in the sample.

    Both are read; neither is guessed at.
    """
    value = case.get("applicability")
    if isinstance(value, str):
        word = value.strip().lower()
        return word in ("applicable", "yes", "true"), value
    if isinstance(value, dict):
        return (value.get("applicable") is not False,
                str(value.get("reason", "no reason recorded")))
    return True, "no applicability recorded"


def case_needs_scheduler(case: dict[str, Any]) -> bool:
    """True when a step drives the real conductor loop (`scheduler-wait`)."""
    steps = list(case.get("setup") or [])
    if case.get("trigger"):
        steps.append(case["trigger"])
    return any(
        step.get("kind") == "clock"
        and str(step.get("adapter") or "").startswith("scheduler-wait")
        for step in steps
    )


def case_trigger(case: dict[str, Any]) -> dict[str, Any]:
    """The case's trigger: the top-level field, or a setup step marked as one."""
    if case.get("trigger"):
        return case["trigger"]
    for step in case.get("setup", []):
        if step.get("is_trigger"):
            return step
    raise Blocked(
        f"case {case['id']} declares no trigger (neither a `trigger` field nor a "
        "setup step with `is_trigger: true`)")


# ─────────────────────────────────────────────────── the observation run ──


def new_run_id(case_id: str, brain: str, viewport: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{case_id}-{brain}-{viewport}"


def _run_dir(out: Path, run_id: str) -> Path:
    """A run-specific directory that NEVER overwrites an existing one."""
    candidate = out / run_id
    suffix = 2
    while candidate.exists():
        candidate = out / f"{run_id}-{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


class Recorder:
    """The observation on disk. Flushed at every stage: a stopped run keeps
    everything it had proved up to that point (brief §7)."""

    def __init__(self, path: Path, record: dict[str, Any]) -> None:
        self.path = path
        self.record = record
        self.flush()

    def set(self, **fields: Any) -> None:
        self.record.update(fields)
        self.flush()

    def note(self, text: str) -> None:
        self.record.setdefault("notes", []).append(text)
        self.flush()

    def flush(self) -> None:
        self.path.write_text(json.dumps(self.record, indent=2, default=str))


def exercise(
    page: Any,
    case: dict[str, Any],
    *,
    recorder: Recorder,
    hub: Hub | None,
    provenance: dict[str, Any],
    shots: Path,
) -> dict[str, Any]:
    """Setup, before, trigger, initial feedback, terminal outcome, after, verdict.

    The verdict is the predicate's answer. The diff is recorded beside it.
    """
    settle = _settle_fn()
    steps: list[dict[str, Any]] = []
    for step in case.get("setup", []):
        steps.append(run_step(step, page, hub, provenance, case))
        recorder.set(setup=steps, provenance=provenance)

    settle(page)
    before = snapshot(page, case, hub)
    page.screenshot(path=str(shots / "before.png"))
    recorder.set(before=_clean(before))

    trigger = case_trigger(case)
    fired_at = time.monotonic()
    trigger_record = run_step(trigger, page, hub, provenance, case)
    recorder.set(trigger=trigger_record, provenance=provenance)

    # initial feedback: what the face said within ~1s of the trigger.
    page.wait_for_timeout(900)
    initial = snapshot(page, case, hub)
    initial_ok, initial_why = check_predicate(case["expected"]["predicate"], before, initial)
    recorder.set(initial_feedback={
        **_clean(initial),
        "predicate_satisfied": initial_ok,
        "reading": initial_why,
        "elapsed_s": round(time.monotonic() - fired_at, 3),
    })

    # terminal outcome: poll to the bound. An `unchanged` contract is never
    # settled early — it must hold for the whole bound.
    bound = float(case.get("completion_bound_s", 20))
    predicate = case["expected"]["predicate"]
    hold = isinstance(predicate, dict) and predicate.get("kind") == "unchanged"
    after = initial
    satisfied, why = initial_ok, initial_why
    while time.monotonic() - fired_at < bound:
        if satisfied and not hold:
            break
        page.wait_for_timeout(400)
        after = snapshot(page, case, hub)
        satisfied, why = check_predicate(case["expected"]["predicate"], before, after)

    settle(page)
    after = snapshot(page, case, hub)
    satisfied, why = check_predicate(case["expected"]["predicate"], before, after)
    elapsed = round(time.monotonic() - fired_at, 3)
    pending = bool(after.get("pending_marker_present"))
    terminal = {
        # `settled` = the face stopped moving; `incomplete` = it is still
        # saying it is working. Neither is a verdict.
        "state": "settled" if satisfied else ("incomplete" if pending else "settled"),
        "predicate_satisfied": satisfied,
        "reading": why,
        "pending_marker": case["expected"].get("pending_marker"),
        "pending_marker_present": after.get("pending_marker_present"),
        "elapsed_s": elapsed,
        "completion_bound_s": bound,
        "within_bound": bool(satisfied and elapsed <= bound + 2),
    }
    state = terminal["state"]
    page.screenshot(path=str(shots / "after.png"))

    decidable = isinstance(case["expected"]["predicate"], dict)
    verdict = "pass" if satisfied else ("fail" if decidable else "blocked")
    recorded_diff = diff(_clean(before), _clean(after))
    recorder.set(
        after=_clean(after),
        terminal_outcome=terminal,
        diff=recorded_diff,
        verdict=verdict,
        shots=[str(shots / "before.png"), str(shots / "after.png")],
    )
    recorder.note(f"predicate: {why}")
    if not decidable:
        recorder.note("BLOCKED, not failed: the rig gathered the whole run "
                      "(setup, before, trigger, wait, after) but the case's "
                      "expected result is prose, so no verdict is earned.")
    if not satisfied and decidable and not recorded_diff:
        recorder.note("UNRESOLVED: the promised result is absent and nothing moved "
                      "at all. A zero diff is never a pass (brief §3).")
    if not satisfied and decidable and recorded_diff:
        recorder.note("a nonzero diff with the wrong result is a finding, not a pass "
                      f"(changed: {sorted(recorded_diff)}).")
    elsewhere = found_elsewhere(case["expected"]["predicate"], after)
    if elsewhere:
        recorder.note(elsewhere)
    if state == "incomplete":
        recorder.note("the operation never completed within its bound; the pending "
                      "marker was still present.")
    return recorder.record


def _settle_fn():
    """Reuse the glass rigs' animation settle; degrade honestly if unavailable."""
    try:
        sys.path.insert(0, str(REPO))
        from tests.e2e.glass_infra import _settle  # noqa: PLC0415
        return _settle
    except Exception:  # noqa: BLE001 — pragma: no cover
        return lambda page: page.wait_for_timeout(200)


def observation_skeleton(
    case: dict[str, Any], *, brain: str, viewport: int, run_id: str,
    provenance: dict[str, Any], atlas: str,
) -> dict[str, Any]:
    return {
        "id": f"obs-{run_id}",
        "run_id": run_id,
        "case_id": case["id"],
        "brain": brain,
        "pass": "live",
        "viewport": viewport,
        "atlas": atlas,
        "job": case.get("job"),
        "edge_ids": case.get("edge_ids", []),
        "state_id": case.get("state_id"),
        "provenance": provenance,
        "before": None,
        "after": None,
        "initial_feedback": None,
        "terminal_outcome": None,
        "verdict": "not_run",
        "notes": [],
        "complete": False,
    }


# ───────────────────────────────────────────────────────── calibrate ──


def calibrate(out: Path, *, brain: str = "muaddib", viewport: int = 1440,
              cases: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """The six §7 calibration cases against the local static page. No hub.

    `cases` overrides the six (the scheduler-wait adapter is calibrated the
    same way, through the same engine).
    """
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    out.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _CalibrationHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}/"
    profile = Path(tempfile.mkdtemp(prefix="graph-walk-calib-profile-"))
    records: list[dict[str, Any]] = []
    try:
        with sync_playwright() as play:
            context = play.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                viewport={"width": viewport, "height": 900},
                args=["--use-fake-device-for-media-stream",
                      "--use-fake-ui-for-media-stream"],
            )
            try:
                for case in (cases or CALIBRATION_CASES):
                    run_id = new_run_id(case["id"], brain, viewport)
                    shots = _run_dir(out, run_id)
                    provenance = base_provenance(engine_mode="none")
                    provenance["hub"] = {"kind": "calibration static page",
                                         "port": port, "pid": os.getpid()}
                    provenance["frontend_build"] = {
                        "kind": "calibration page (not the product bundle)",
                        "sha256": _sha256(CALIBRATION_PAGE)}
                    provenance["fixture_hashes"] = {
                        "tests/fixtures/graph_walk_calibration.html":
                            _sha256(CALIBRATION_PAGE)}
                    recorder = Recorder(
                        shots / "observation.json",
                        observation_skeleton(case, brain=brain, viewport=viewport,
                                             run_id=run_id, provenance=provenance,
                                             atlas="builtin:calibration"),
                    )
                    page = context.new_page()
                    try:
                        page.goto(base)
                        exercise(page, case, recorder=recorder, hub=None,
                                 provenance=provenance, shots=shots)
                    except Blocked as exc:
                        recorder.set(verdict="blocked")
                        recorder.note(f"BLOCKED: {exc}")
                    finally:
                        page.close()
                        recorder.set(complete=True)
                        records.append(recorder.record)
            finally:
                context.close()
    finally:
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    return records


def calibration_table(records: list[dict[str, Any]]) -> tuple[str, bool]:
    lines = [f"{'case':32} {'verdict':9} {'terminal':11} {'expected':9} {'ok'}"]
    ok = True
    for record in records:
        want_verdict, want_state = CALIBRATION_EXPECTED[record["case_id"]]
        state = (record.get("terminal_outcome") or {}).get("state", "-")
        good = record["verdict"] == want_verdict and state == want_state
        ok = ok and good
        lines.append(
            f"{record['case_id']:32} {record['verdict']:9} {state:11} "
            f"{want_verdict:9} {'OK' if good else 'MISMATCH'}")
    return "\n".join(lines), ok


# ────────────────────────────────────────────────────────────── run ──


def load_atlas(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def find_case(atlas: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in atlas.get("cases", []):
        if case["id"] == case_id:
            return case
    raise SystemExit(f"no case {case_id!r} in the atlas "
                     f"(have: {[c['id'] for c in atlas.get('cases', [])]})")


def run_case(
    atlas_path: Path, case_id: str, *, brain: str, viewport: int,
    out: Path, engine: str = "none", token: str = TOKEN,
    build: bool = True,
) -> dict[str, Any]:
    """ONE case, ONE hub, ONE observation directory (brief §7)."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    atlas = load_atlas(atlas_path)
    case = find_case(atlas, case_id)
    run_id = new_run_id(case_id, brain, viewport)
    out.mkdir(parents=True, exist_ok=True)
    shots = _run_dir(out, run_id)

    provenance = base_provenance(engine_mode=engine)
    provenance["atlas"] = {"path": str(atlas_path),
                           "sha256": _sha256(Path(atlas_path)),
                           "version": atlas.get("atlas_version")}
    recorder = Recorder(
        shots / "observation.json",
        observation_skeleton(case, brain=brain, viewport=viewport, run_id=run_id,
                             provenance=provenance, atlas=str(atlas_path)),
    )

    applicable, why_not = case_applicable(case)
    if not applicable:
        recorder.set(verdict="not_applicable", complete=True)
        recorder.note(f"NOT APPLICABLE: {why_not}")
        return recorder.record
    if viewport not in (case.get("viewports") or [viewport]):
        recorder.set(verdict="not_applicable", complete=True)
        recorder.note(f"the case declares viewports {case.get('viewports')}; "
                      f"{viewport} is not one of them")
        return recorder.record

    if build:
        _ensure_build()

    home = Path(tempfile.mkdtemp(prefix="graph-walk-home-"))
    profile = Path(tempfile.mkdtemp(prefix="graph-walk-profile-"))
    hub: Hub | None = None
    try:
        scheduler = case_needs_scheduler(case)
        hub = Hub(home, token=token, scheduler=scheduler).start()
        provenance["hub"] = {"url": hub.url, "port": hub.port,
                             "pid": hub.proc.pid if hub.proc else None,
                             "home": str(home),
                             # brief §7: keep unrelated scheduler activity
                             # identifiable. It is OFF unless a case asks.
                             "scheduler_thread": scheduler}
        provenance["clock"]["scheduler_thread"] = scheduler
        provenance["db_path"] = hub.db_path
        provenance["frontend_build"] = _frontend_build()
        recorder.set(provenance=provenance)

        with sync_playwright() as play:
            context = play.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                viewport={"width": viewport,
                          "height": 900 if viewport >= 1000 else 852},
                device_scale_factor=2,
                args=["--use-fake-device-for-media-stream",
                      "--use-fake-ui-for-media-stream"],
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(repr(e)[:300]))
            try:
                page.goto(f"{hub.url}/?token={token}")
                exercise(page, case, recorder=recorder, hub=hub,
                         provenance=provenance, shots=shots)
            except Blocked as exc:
                recorder.set(verdict="blocked")
                recorder.note(f"BLOCKED: {exc}")
            finally:
                recorder.set(console_errors=errors[:20])
                context.close()
    finally:
        if hub is not None:
            recorder.set(hub_log=hub.lines[-40:])
            hub.stop()
        shutil.rmtree(profile, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)
        recorder.set(complete=True)
    return recorder.record


def _ensure_build() -> None:
    sys.path.insert(0, str(REPO))
    from tests.e2e.glass_infra import _ensure_build as build  # noqa: PLC0415
    build()


# ───────────────────────────────────────────────────────────── the CLI ──


def report(record: dict[str, Any]) -> str:
    """The §9 shape, for one observation."""
    prov = record.get("provenance", {})
    lines = [
        "PASS: live",
        f"BRAIN: {record['brain']}",
        f"SOURCE: {prov.get('revision')} dirty={prov.get('dirty')}",
        f"CONTRACT: rig={prov.get('rig_version')} brief={str(prov.get('brief_sha256'))[:12]} "
        f"atlas={record.get('atlas')}",
        f"RUNTIME: build={(prov.get('frontend_build') or {}).get('assets') or (prov.get('frontend_build') or {}).get('kind')} "
        f"hub={(prov.get('hub') or {}).get('url') or (prov.get('hub') or {}).get('kind')} "
        f"db={prov.get('db_path')} engine={prov.get('engine_mode')}",
        f"JOB: {record.get('job')}",
        f"VERDICT: {record['verdict']} "
        f"terminal={(record.get('terminal_outcome') or {}).get('state')}",
        f"EVIDENCE: {record.get('shots') or []}",
    ]
    for note in record.get("notes", []):
        lines.append(f"NOTE: {note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="the graph audit's one live rig")
    parser.add_argument("--version", action="version", version=RIG_VERSION)
    sub = parser.add_subparsers(dest="mode", required=True)

    p_cal = sub.add_parser("calibrate", help="the six §7 calibration cases")
    p_cal.add_argument("--out", default=".tmp/graph-walk/calibration")
    p_cal.add_argument("--brain", default="muaddib", choices=("muaddib", "astra"))

    p_run = sub.add_parser("run", help="ONE atlas case against a real hub")
    p_run.add_argument("--atlas", required=True)
    p_run.add_argument("--case", required=True)
    p_run.add_argument("--brain", required=True, choices=("muaddib", "astra"))
    p_run.add_argument("--viewport", required=True, type=int, choices=(1440, 393))
    p_run.add_argument("--engine", default="none", choices=("real", "replayed", "none"))
    p_run.add_argument("--out", default=".tmp/graph-walk/live")
    p_run.add_argument("--no-build", action="store_true")

    p_serve = sub.add_parser("serve", help="(internal) the rig's hub subprocess")
    p_serve.add_argument("--port", type=int, default=0)
    p_serve.add_argument("--token", default=TOKEN)
    p_serve.add_argument("--scheduler", action="store_true",
                         help="also start the real heartbeat conductor loop")

    args = parser.parse_args(argv)

    if args.mode == "serve":
        _serve(args.port or _free_port(), args.token,
               scheduler=bool(getattr(args, "scheduler", False)))
        return 0

    if args.mode == "calibrate":
        records = calibrate(Path(args.out), brain=args.brain)
        table, ok = calibration_table(records)
        print(table)
        print(f"\nRIG {RIG_VERSION} calibration: {'OK' if ok else 'MISMATCH'}")
        return 0 if ok else 1

    record = run_case(
        Path(args.atlas), args.case, brain=args.brain, viewport=args.viewport,
        out=Path(args.out), engine=args.engine, build=not args.no_build,
    )
    print(report(record))
    return 0 if record["verdict"] in ("pass", "not_applicable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
