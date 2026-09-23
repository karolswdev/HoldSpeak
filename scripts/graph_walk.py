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

VARIABLES: an `api` step may carry `capture_as` (and `capture_path`, a dotted
or JSON-pointer path into its response; the default is `id`). The captured
value fills `{name}` in every later step's `path`, `body`, `selector`, `name`,
`value`, `url` and `key`, and in the case's own `expected.observe_at` and
predicate fields. An unresolved `{name}` at fire time is BLOCKED, naming it —
it is never sent literally. The captured values travel in the observation.
The TRIGGER may capture too (J4's import mints `{meeting_id}`): `expected` is
resolved AFTER the trigger fires; before it, a read field naming a value only
the trigger binds is not read. A name nothing binds blocks before the trigger;
one still unbound after it blocks, naming it.

TRIGGER RESPONSE: an api/fixture trigger's own response is recorded. A `ui`
trigger records the network response its click fired: the first response to
the step's (or case's) `trigger_route: {method, path}`, else the first
same-origin non-GET response after the click, with the rule that chose it
(`trigger_response_capture`). `trigger:<path>` identity and `protocol_status`
read it. `identity_display_path` names the response field the face shows,
when that is not the identity itself.

A step is `{"kind": <one of STEP_KINDS>, ...}`:

  api       {method, path, body?, expect_status?}   HTTP against the hub
  ui        {action: goto|click|click_role|fill|press|wait_for, ...}
  fixture   {path, route:{method,path}, field?, expect_status?} the WAV at the documented
            input boundary — never a microphone
  cli       {action: "restart_hub", adapter}
            The rig owns the hub process, so it stops it (SIGTERM, then
            SIGKILL at the bound), starts it again on the SAME port, HOME,
            flags and database, re-verifies the resolved db path, reloads the
            page for a face case, and records both pids and the downtime.
            Every other cli command is recorded `blocked` with its name.
  clock     {adapter, clock, how, max_wait_s?, poll_s?}
            ONE mechanism is implemented: `adapter: "scheduler-wait"` waits
            (slow polls, ≤ the case's completion_bound_s) for the REAL
            scheduler to change `expected.observe_at`. No clock is moved.
            Every other clock mechanism is recorded `blocked` with its name.
  check     {predicate, observe_at}                 the same evaluator a verdict
            uses, at the point it stands in `setup` (or in `preconditions`).
            A check that does not hold is `blocked: precondition not met`,
            with the predicate and the location named.
  boundary  {label, substitute: "engine_reply", reply, api?}
            A substitution must be PERFORMED, never merely labelled:
            `engine_reply` installs a recorded provider reply at the product's
            own seam INSIDE the hub process, and the step blocks if the hub
            was not booted with it. The observation is labelled
            `engine_mode: replayed`.

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
  unchanged {identity}           an idempotent/read contract: the same result
                                 AND a replay identity produced by THIS
                                 operation. `identity` is
                                 {"from":"trigger","path":…,"display":…?} —
                                 the value the operation's own response
                                 returned, and with `display` it must BE the
                                 one on the face — or
                                 {"from":"selector","selector":…,"attr":…},
                                 which the rig blanks before the trigger so
                                 the operation must write it again. An
                                 unexplained zero diff is UNRESOLVED, not pass.
  protocol_rows {collection, match, min_new, max_new?}
                                 for `observe_at: "protocol: GET /path"` — a
                                 named NEW row must appear in that route's
                                 collection. `field__prefix` matches a prefix.
                                 `max_new` bounds them from above, so
                                 `min_new: 0, max_new: 0` is an ASSERTED
                                 absence ("no sweep ran"): the verdict is
                                 earned by the named bound on a named row
                                 shape, never by an unexplained zero diff.
  protocol_rows_gone {collection, match, min_gone, identity?}
                                 a NAMED row present before and absent after,
                                 by identity — never merely "fewer rows".
  protocol_status {method, path, status, body_contains?}
                                 the TRIGGER's own response status (a 4xx
                                 refusal is a promised result). The call is
                                 never re-fired; the body sha256 is recorded,
                                 and `body_contains` proves the refusal NAMES
                                 what is missing rather than merely failing.
  protocol_field {path, value | absent}
                                 one field of the observe_at payload, at a
                                 dotted or JSON-pointer path. `null` is a
                                 value; `absent: true` is a separate claim.
  input_value {selector, contains | equals}
                                 a form control's `.value` (a draft lives
                                 there, not in the DOM text).
  text_nonempty                 rendered material exists at the named face
  hit_target {min_width, min_height}
                                 the named control is visible, in the viewport,
                                 and owns nine interior hit-test points

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

THE RIG'S HUB
-------------
It takes the product's own database owner lock and runs the product's own
intel drainer (which refuses to start without that lock). It does NOT build
the microphone recorder or the global hotkey listener, so `POST /api/meeting/start`
refuses by name. `provenance.product_wiring` says what the hub HAS and LACKS,
so no observation is read as if it came from the whole product.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

RIG_VERSION = "1.2.0"

# PHILO-3-02's real engine is supplied by the LAN endpoint configured through
# the normal Concierge field.  The URL and model are provenance inputs for a
# run; they are never secrets and are safe to retain in an observation.
ENGINE_URL_ENV = "PHILO3_ENGINE_URL"
ENGINE_URL_DEFAULT = "http://192.168.1.43:8080"
ENGINE_MODEL_ENV = "PHILO3_ENGINE_MODEL"
ENGINE_MODEL_DEFAULT = "Qwen3.6-35B"

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
        "engine_identity": None,
        "boundary_substitutions": [],
        "restarts": [],
        "rig_version": RIG_VERSION,
        "brief_sha256": _sha256(BRIEF) if BRIEF.exists() else None,
    }


def _engine_identity() -> dict[str, Any]:
    """Read the configured OpenAI-compatible endpoint's model identity.

    The response is deliberately reduced to model ids and owners.  Provider
    credentials, if any, never enter the run record.
    """
    base = os.environ.get(ENGINE_URL_ENV, ENGINE_URL_DEFAULT).rstrip("/")
    models_url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
    expected = os.environ.get(ENGINE_MODEL_ENV, ENGINE_MODEL_DEFAULT)
    result: dict[str, Any] = {
        "endpoint": base,
        "models_url": models_url,
        "expected_model_prefix": expected,
    }
    request = urllib.request.Request(models_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode()
            payload = json.loads(raw)
            rows = payload.get("data", []) if isinstance(payload, dict) else []
            if not rows and isinstance(payload, dict):
                rows = payload.get("models", [])
            result["status"] = response.status
            result["models"] = [
                {"id": row.get("id"), "owned_by": row.get("owned_by")}
                for row in rows if isinstance(row, dict)
            ]
            result["expected_model_seen"] = any(
                str(row.get("id") or "").startswith(expected)
                for row in result["models"]
            )
    except Exception as exc:  # noqa: BLE001 — provenance survives a bad endpoint
        result["status"] = None
        result["models"] = []
        result["expected_model_seen"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"[:400]
    return result


# ───────────────────────────────────────────────────── the observation ──

_SNAPSHOT_JS = r"""([selector, pending, valueSelector]) => {
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
  const hitTest = (node) => {
    if (!node) return null;
    const r = node.getBoundingClientRect();
    const insetX = Math.min(2, Math.max(0, r.width / 4));
    const insetY = Math.min(2, Math.max(0, r.height / 4));
    const xs = [r.left + insetX, r.left + r.width / 2, r.right - insetX];
    const ys = [r.top + insetY, r.top + r.height / 2, r.bottom - insetY];
    const samples = [];
    for (const x of xs) for (const y of ys) {
      const owner = document.elementFromPoint(x, y);
      samples.push({
        x: Math.round(x), y: Math.round(y),
        owned: !!owner && (owner === node || node.contains(owner)),
        owner: owner ? path(owner) : null,
      });
    }
    return {
      viewport: {width: window.innerWidth, height: window.innerHeight},
      rect: box(node),
      in_viewport: r.top >= 0 && r.left >= 0 && r.bottom <= window.innerHeight
        && r.right <= window.innerWidth,
      samples,
      all_owned: samples.every((sample) => sample.owned),
    };
  };
  const el = selector ? document.querySelector(selector) : null;
  const attrs = {};
  if (el) for (const a of el.attributes) attrs[a.name] = a.value;
  // Form controls carry their state in `.value`, not in the DOM text, so a
  // snapshot without it cannot see a draft come back after a reload.
  const isField = (node) => node && /^(INPUT|TEXTAREA|SELECT)$/.test(node.tagName);
  const values = [...(el || document).querySelectorAll("input, textarea, select")]
    .slice(0, 20).map((node) => ({selector: path(node), value: node.value}));
  if (isField(el)) values.unshift({selector: path(el), value: el.value});
  const field = valueSelector ? document.querySelector(valueSelector) : null;
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
    hit_test: hitTest(el),
    values,
    field_value: valueSelector
      ? {selector: valueSelector, present: !!field,
         value: field ? (isField(field) ? field.value : null) : null}
      : null,
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
        [None if target else expected.get("observe_at"),
         expected.get("pending_marker"),
         predicate.get("selector") if isinstance(predicate, dict) else None],
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
            # the whole payload, for a `protocol_field` predicate to read
            "payload": payload,
        }
        # the diff reads the digest, never the whole payload
        raw["protocol_digest"] = {"status": status,
                                  "row_count": raw["protocol"]["row_count"],
                                  "payload_sha256": raw["protocol"]["payload_sha256"]}
    body = raw.pop("body_text", "") or ""
    raw["document_text_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    raw["document_text_len"] = len(body)
    raw["_body_text"] = body  # stripped before the record is written
    identity = identity_spec(predicate)
    raw["replay_identity"] = _read_identity(page, identity) if identity else None
    display = (identity or {}).get("display")
    if display:
        raw["identity_display"] = _read_identity(
            page, {"from": "selector", "selector": display,
                   "attr": (identity or {}).get("display_attr")})
        raw["identity_display"]["spec"] = predicate.get("identity_display")
    reads = expected.get("reads") or []
    if reads and hub is not None:
        collected = []
        for read in reads:
            status, payload = hub.api(read["method"], read["path"])
            collected.append({
                "method": read["method"], "path": read["path"], "status": status,
                "payload": payload,
                "body_sha256": hashlib.sha256(
                    json.dumps(payload, sort_keys=True, default=str).encode()
                ).hexdigest(),
            })
        raw["api_reads"] = collected
    raw["at_utc"] = datetime.now(timezone.utc).isoformat()
    return raw


def identity_spec(predicate: Any) -> dict[str, Any] | None:
    """The replay identity, normalised to one of two shapes.

    `{"from": "trigger", "path": …, "display": …?}` — the value the operation's
    own response returned (and, with `display`, the value shown at that
    selector: J10's contract is that the returned id IS the displayed one).

    `{"from": "selector", "selector": …, "attr": …}` — an attribute the rig
    blanks before the trigger, so the operation must write it again.

    The legacy string forms `"#sel@attr"` and `"trigger:<path>"` are read into
    the same shapes; `trigger:` was being handed to `querySelector` as if it
    were CSS (Astra's round two).
    """
    if not isinstance(predicate, dict):
        return None
    raw = predicate.get("identity") or predicate.get("replay_identity")
    if not raw:
        return None
    if isinstance(raw, dict):
        spec = dict(raw)
        spec.setdefault("from", "selector" if spec.get("selector") else "trigger")
    elif str(raw).startswith("trigger:"):
        spec = {"from": "trigger", "path": str(raw).split(":", 1)[1]}
    else:
        selector, _, attr = str(raw).partition("@")
        spec = {"from": "selector", "selector": selector, "attr": attr or None}
    shown = predicate.get("identity_display")
    if shown:
        selector, _, attr = str(shown).partition("@")
        spec["display"] = selector
        spec["display_attr"] = attr or None
        # the response field whose value the face shows; the identity itself
        # by default (a face may show the brief's words, not its id)
        spec["display_path"] = predicate.get("identity_display_path")
    return spec


def _shown_as_token(shown: Any, value: Any) -> bool:
    """`value` is displayed at `shown` as a whole token: `brief-7` is not
    shown by `brief-77` (a longer, different id beside it)."""
    text, want = str(shown), str(value)
    if text.strip() == want.strip():
        return True
    return re.search(rf"(?<![\w-]){re.escape(want)}(?![\w-])", text) is not None


def _read_identity(page: Any, spec: dict[str, Any]) -> dict[str, Any] | None:
    """Read a SELECTOR identity off the page. A trigger identity is not here:
    it lives in the operation's response and is read by the evaluator."""
    if spec.get("from") != "selector":
        return {"from": spec.get("from"), "path": spec.get("path"), "value": None,
                "read_from": "the trigger's response, not the page"}
    value = page.evaluate(
        """([selector, attr]) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            return attr ? el.getAttribute(attr) : (el.innerText || "").trim();
        }""",
        [spec.get("selector"), spec.get("attr")],
    )
    return {"from": "selector", "selector": spec.get("selector"),
            "attr": spec.get("attr"), "value": value}


_DIFF_KEYS = (
    "target_present", "text", "attrs", "rect", "visible", "focus", "focus_label",
    "url", "windows", "document_text_sha256", "document_text_len",
    "replay_identity", "api_reads", "protocol_digest", "values", "field_value",
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
    if predicate is None:
        return False, ("BLOCKED: no structured predicate. The case's `expected` "
                       "carries only `words`, so no verdict is earned.")
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

    if kind == "protocol_status":
        # The TRIGGER's own response. A refusal is a promised result: the rig
        # reads the status the route really answered, never re-fires the call.
        answer = after.get("trigger_response") or {}
        if not answer:
            return False, ("no trigger response was recorded; `protocol_status` "
                           "reads the status of the trigger's own call")
        want = int(predicate["status"])
        got = answer.get("status")
        where = f"{answer.get('method')} {answer.get('path')}"
        for field in ("method", "path"):
            if predicate.get(field) and predicate[field] != answer.get(field):
                return False, (f"the trigger was {where}, not "
                               f"{predicate.get('method')} {predicate.get('path')}")
        reading = (f"{where} answered {got}, wanted {want} "
                   f"(body sha256 {str(answer.get('body_sha256'))[:12]})")
        if got != want:
            return False, reading
        if "body_contains" in predicate:
            # A refusal must be INTELLIGIBLE: the status alone does not say
            # what is missing. The recorded body is read; the call is not
            # fired a second time.
            body = json.dumps(answer.get("body"), default=str)
            want_text = predicate["body_contains"]
            if want_text not in body:
                return False, (
                    f"{reading}; {want_text!r} NOT in the response body")
        body_fields = predicate.get("body_fields") or {}
        for field, wanted in body_fields.items():
            found, value = _json_path(answer.get("body"), field)
            if isinstance(wanted, dict) and wanted.get("nonempty"):
                holds = found and value not in (None, "", [], {})
            else:
                holds = found and value == wanted
            if not holds:
                return False, (
                    f"{reading}; body field {field!r} = {value!r}, "
                    f"wanted {wanted!r}")
        if "body_contains" in predicate or body_fields:
            return True, (
                f"{reading}; response body contains the declared admission "
                "facts")
        return True, reading

    if kind == "protocol_rows_gone":
        # A NAMED disappearance, by row identity — never "fewer rows".
        identity = predicate.get("identity", "id")
        was = {_row_identity(row, identity) for row in match_rows(before, predicate)}
        now = {_row_identity(row, identity) for row in match_rows(after, predicate)}
        gone = was - now
        need = int(predicate.get("min_gone", 1))
        return len(gone) >= need, (
            f"rows matching {predicate.get('match')!r}: before={sorted(was)} "
            f"after={sorted(now)}; gone={sorted(gone)} (needed {need})")

    if kind == "protocol_field":
        payload = (after.get("protocol") or {}).get("payload")
        if payload is None and not (after.get("protocol") or {}):
            return False, ("no protocol payload was recorded; `protocol_field` "
                           "needs `observe_at: \"protocol: GET /path\"`")
        found, value = _json_path(payload, predicate["path"])
        if predicate.get("absent"):
            return (not found), (f"{predicate['path']} "
                                 f"{'is absent' if not found else f'is present ({value!r})'}")
        if not found:
            return False, f"{predicate['path']} is absent; wanted {predicate.get('value')!r}"
        if predicate.get("nonempty"):
            present = value not in (None, "", [], {})
            if not present:
                return False, f"{predicate['path']} is empty"
        if "value" in predicate:
            equal = value == predicate["value"]
            if not equal:
                return False, (
                    f"{predicate['path']} = {value!r}, "
                    f"wanted {predicate['value']!r}"
                )
        if predicate.get("restart_required"):
            restart = after.get("restart") or {}
            required = ("summary_retained", "receipt_retained",
                        "meeting_identity_retained")
            missing = [name for name in required if restart.get(name) is not True]
            if missing:
                return False, f"restart retention flags missing or false: {missing}"
        if predicate.get("nonempty"):
            return True, f"{predicate['path']} is non-empty"
        if "value" in predicate:
            return True, f"{predicate['path']} equals the declared value"
        if predicate.get("positive"):
            positive = isinstance(value, (int, float)) and value > 0
            return positive, (
                f"{predicate['path']} is {value!r}; wanted a positive number"
            )
        return value == predicate.get("value"), (
            f"{predicate['path']} = {value!r}, wanted {predicate.get('value')!r}")

    if kind == "input_value":
        field = after.get("field_value") or {}
        if not field.get("present"):
            return False, (f"no form control at {predicate.get('selector')!r} "
                           "(its value cannot be read)")
        value = field.get("value") or ""
        if "equals" in predicate:
            return value == predicate["equals"], (
                f"value is {value!r}, wanted {predicate['equals']!r}")
        want = predicate.get("contains", "")
        return want in value, (
            f"{want!r} {'in' if want in value else 'NOT in'} the field value {value!r}")

    if kind == "hit_target":
        hit = after.get("hit_test") or {}
        if not after.get("target_present") or not after.get("visible"):
            return False, "the named control is absent or hidden"
        if not hit.get("in_viewport"):
            return False, f"the control is outside the viewport: {hit.get('viewport')}"
        if not hit.get("all_owned"):
            covered = [sample for sample in hit.get("samples", [])
                       if not sample.get("owned")]
            return False, f"a covering element owns hit points: {covered[:3]}"
        rect = hit.get("rect") or {}
        min_width = float(predicate.get("min_width", 0))
        height_by_viewport = predicate.get("min_height_by_viewport") or {}
        viewport_width = str((hit.get("viewport") or {}).get("width"))
        min_height = float(height_by_viewport.get(
            viewport_width, predicate.get("min_height", 0)))
        if float(rect.get("w", 0)) < min_width or float(rect.get("h", 0)) < min_height:
            return False, (
                f"control rect {rect!r} is smaller than "
                f"{min_width:g}x{min_height:g}px")
        return True, (
            f"control owns all 9 hit points in viewport "
            f"{hit.get('viewport')} with rect {rect}")

    if kind == "protocol_rows":
        gained_before = match_rows(before, predicate)
        gained_after = match_rows(after, predicate)
        need = int(predicate.get("min_new", 1))
        ceiling = predicate.get("max_new")
        minted = len(gained_after) - len(gained_before)
        reading = (f"rows matching {predicate.get('match')!r} at "
                   f"{(after.get('protocol') or {}).get('path')}: "
                   f"before={len(gained_before)} after={len(gained_after)} "
                   f"(new={minted}; wanted >= {need}"
                   f"{f' and <= {ceiling}' if ceiling is not None else ''})")
        if (after.get("protocol") or {}).get("status", 0) >= 400:
            return False, f"the route answered {(after['protocol'])['status']}; " + reading
        if need == 0 and ceiling is None:
            return False, (
                "UNRESOLVED: `min_new: 0` with no `max_new` asserts nothing. An "
                "absence must be NAMED with a bound (brief §3). " + reading)
        if ceiling is not None and minted > int(ceiling):
            return False, reading
        return minted >= need, reading

    if kind == "text_contains":
        want = predicate["value"]
        return (want in text), f"{want!r} {'in' if want in text else 'NOT in'} observe_at text"
    if kind == "text_nonempty":
        present = bool(after.get("target_present")) and bool(text.strip())
        return present, (
            f"observe_at text is {'present' if present else 'absent or empty'}"
        )
    if kind == "text_equals":
        want = predicate["value"]
        return (text.strip() == want), f"observe_at text is {text.strip()!r}, wanted {want!r}"
    if kind == "text_absent":
        # Absence INSIDE an existing scope is a result. A missing scope is not
        # an absence — it is a rig that looked nowhere (Astra's counsel).
        if not after.get("target_present"):
            return False, (f"BLOCKED: observe_at not present "
                           f"({after.get('observe_at')!r}); an absence inside a "
                           "scope that does not exist proves nothing")
        want = predicate["value"]
        return (want not in text), f"{want!r} {'absent' if want not in text else 'PRESENT'} at observe_at"
    if kind == "attr_equals":
        if not after.get("target_present"):
            return False, (f"BLOCKED: observe_at not present "
                           f"({after.get('observe_at')!r}); no element carries "
                           f"{predicate.get('attr')!r}")
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
        spec = identity_spec(predicate)
        if not spec:
            return False, (
                "UNRESOLVED: a zero diff with no recorded replay identity. "
                "An unexplained zero diff cannot pass (brief §3).")

        if spec.get("from") == "trigger":
            answer = after.get("trigger_response") or {}
            if not answer:
                return False, ("BLOCKED: the identity comes from the trigger's "
                               "response, and no response was recorded")
            found, returned = _json_path(answer.get("body"), spec.get("path", "id"))
            if not found or returned is None:
                return False, (f"the operation's response carries no "
                               f"{spec.get('path')!r} to identify the replay")
            shown = (after.get("identity_display") or {}).get("value")
            if spec.get("display"):
                if shown is None:
                    return False, (f"BLOCKED: nothing at {spec['display']!r} "
                                   "displays the returned identity")
                expect_shown = returned
                if spec.get("display_path"):
                    got, expect_shown = _json_path(answer.get("body"),
                                                   spec["display_path"])
                    if not got or expect_shown in (None, ""):
                        return False, (f"the operation's response carries no "
                                       f"{spec['display_path']!r} to compare "
                                       "against the face")
                if not _shown_as_token(shown, expect_shown):
                    return False, (f"the operation returned {returned!r} "
                                   f"({spec.get('display_path') or spec.get('path')}"
                                   f"={expect_shown!r}) but the face shows "
                                   f"{shown!r} at {spec['display']!r} — a stale "
                                   "face beside a new result")
                return True, (f"unchanged result; the returned identity {returned!r} "
                              f"({spec.get('display_path') or spec.get('path')}="
                              f"{expect_shown!r}) IS the one displayed at "
                              f"{spec['display']!r} (response chosen by "
                              f"{answer.get('chosen_by') or 'the api trigger'})")
            return True, (f"unchanged result; the operation's own response "
                          f"returned the identity {returned!r}")

        identity_before = (before.get("replay_identity") or {}).get("value")
        identity_after = (after.get("replay_identity") or {}).get("value")
        if identity_after is None:
            return False, (f"the replay identity at {spec.get('selector')!r} was "
                           "not readable after the operation")
        if identity_before != identity_after:
            return False, f"replay identity moved: {identity_before!r} -> {identity_after!r}"
        return True, f"unchanged result with the same replay identity {identity_after!r}"
    return False, f"unknown predicate kind {kind!r}"


def _row_identity(row: dict[str, Any], field: str) -> str:
    """A row's stable name. Without the field, its whole content names it."""
    if isinstance(row, dict) and row.get(field) is not None:
        return str(row[field])
    return "sha:" + hashlib.sha256(
        json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _json_path(payload: Any, path: str) -> tuple[bool, Any]:
    """`counts.needs_attention` or `/counts/needs_attention` — (found, value).

    A list index is a number. `found` is False only when the path does not
    resolve, so a field that really holds `null` is found with value None.
    """
    parts = [p for p in (path.lstrip("/").split("/") if path.startswith("/")
                         else path.split(".")) if p != ""]
    node = payload
    for part in parts:
        if isinstance(node, dict):
            if part not in node:
                return False, None
            node = node[part]
        elif isinstance(node, list) and part.lstrip("-").isdigit():
            index = int(part)
            if not -len(node) <= index < len(node):
                return False, None
            node = node[index]
        else:
            return False, None
    return True, node


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
            # a dotted or JSON-pointer key reaches a NESTED field
            # (`effective.status`); `__prefix` still applies to it
            path = key[: -len("__prefix")] if key.endswith("__prefix") else key
            seen, value = _json_path(row, path)
            if key.endswith("__prefix"):
                ok = ok and seen and str(value or "").startswith(str(want))
            else:
                ok = ok and seen and value == want
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

    def __init__(self, home: Path, token: str = TOKEN, *, scheduler: bool = False,
                 engine_replay: Path | None = None) -> None:
        self.home = guard_home(home)
        self.token = token
        self.scheduler = scheduler
        self.engine_replay_path = engine_replay
        self.engine_replay: str | None = None
        self.wiring: dict[str, Any] = {}
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
            elif line.startswith("ENGINE_REPLAY "):
                self.engine_replay = line.split(" ", 1)[1].strip()
            elif line.startswith("WIRING "):
                self.wiring = json.loads(line.split(" ", 1)[1])

    def restart(self) -> dict[str, Any]:
        """Stop this hub and start it again on the same port, HOME and flags."""
        return _restart_process(self)

    def start(self, timeout: float = 180.0) -> "Hub":
        # a restart re-reads them from the new process; never trust the old
        self.lines = []
        self.db_path = None
        self.engine_replay = None
        self.wiring = {}
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["PYTHONUNBUFFERED"] = "1"
        env.pop("HOLDSPEAK_DB_PATH", None)
        command = [sys.executable, str(Path(__file__).resolve()), "serve",
                   "--port", str(self.port), "--token", self.token]
        if self.scheduler:
            command.append("--scheduler")
        if self.engine_replay_path:
            command += ["--engine-replay", str(self.engine_replay_path)]
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

    def upload(self, method: str, path: str, wav: Path, field: str,
               form: dict[str, Any] | None = None) -> tuple[int, Any]:
        """The fixture WAV at the documented input boundary. Never a microphone."""
        return _multipart_upload(f"{self.url}{path}", method, wav, field,
                                 {"X-HoldSpeak-Token": self.token}, form=form)

    def stop(self) -> None:
        _terminate(self.proc)


def _multipart_upload(url: str, method: str, wav: Path, field: str,
                      headers: dict[str, str],
                      form: dict[str, Any] | None = None) -> tuple[int, Any]:
    """One multipart/form-data upload of `wav` as `field` (the import route
    takes an UploadFile, holdspeak/web/routes/meeting_import.py:52-55)."""
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in (form or {}).items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{wav.name}"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode()
    payload = b"".join(parts) + head + wav.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        url, data=payload, method=method,
        headers={**headers,
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


def _wait_field(value: Any, wanted: Any) -> bool:
    """Match a declared completion field without inventing transcript data."""
    if isinstance(wanted, dict):
        if wanted.get("nonempty"):
            return value not in (None, "", [], {})
        if wanted.get("positive"):
            return isinstance(value, (int, float)) and value > 0
        if "min_items" in wanted:
            return isinstance(value, (list, tuple, dict)) and len(value) >= int(wanted["min_items"])
    return value == wanted


def wait_for_fixture_completion(
    hub: Hub, wait_for: dict[str, Any], variables: dict[str, str],
) -> dict[str, Any]:
    """Poll the product's read route after a 202 import response.

    The 202 is retained as the input-boundary response.  This second read is
    the real worker completion, including the product's ASR output and timing;
    a timeout remains a blocked observation.
    """
    wait_for = substitute(wait_for, variables)
    method = wait_for.get("method", "GET")
    path = wait_for["path"]
    fields = wait_for.get("fields") or {}
    timeout_s = float(wait_for.get("timeout_s", 300))
    poll_s = float(wait_for.get("poll_s", 0.5))
    started = time.monotonic()
    polls = 0
    last_status: int | None = None
    last_payload: Any = None
    last_matches: dict[str, bool] = {}
    while time.monotonic() - started < timeout_s:
        last_status, last_payload = hub.api(method, path)
        last_matches = {}
        payload_is_object = isinstance(last_payload, dict)
        if payload_is_object:
            last_matches = {
                name: (found and _wait_field(value, wanted))
                for name, wanted in fields.items()
                for found, value in [_json_path(last_payload, name)]
            }
        if (last_status is not None and 200 <= last_status < 300
                and payload_is_object and set(last_matches) == set(fields)
                and all(last_matches.values())):
            return {
                "method": method,
                "path": path,
                "fields": fields,
                "status": last_status,
                "matched": True,
                "polls": polls + 1,
                "elapsed_s": round(time.monotonic() - started, 3),
                "payload": last_payload,
                "field_matches": last_matches,
            }
        polls += 1
        time.sleep(poll_s)
    return {
        "method": method,
        "path": path,
        "fields": fields,
        "status": last_status,
        "matched": False,
        "polls": polls,
        "elapsed_s": round(time.monotonic() - started, 3),
        "payload": last_payload,
        "field_matches": last_matches,
        "timeout_s": timeout_s,
    }


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


class _ReplayIntel:
    """A RECORDED provider reply, installed at the product's provider seam.

    It is not a model and it is not a stub of the pipeline: everything
    downstream — the queue, the services, persistence, the face — stays the
    product. Only the provider call is replayed, and every observation made
    with it is labelled `engine_mode: replayed` (brief §7).
    """

    def __init__(self, reply: dict[str, Any]) -> None:
        self.reply = reply
        self.active_provider = reply.get("provider", "replay")
        self.active_model = reply.get("model", "recorded-reply")
        self.calls: list[str] = []

    def _result(self) -> Any:
        from holdspeak.intel.models import ActionItem, IntelResult

        return IntelResult(
            topics=list(self.reply.get("topics", [])),
            action_items=[ActionItem(**item)
                          for item in self.reply.get("action_items", [])],
            summary=self.reply.get("summary", ""),
            raw_response=json.dumps(self.reply),
            error=self.reply.get("error"),
        )

    def analyze(self, transcript: str, *, stream: bool = False) -> Any:
        self.calls.append("analyze")
        if stream:
            return iter([self.reply.get("summary", ""), self._result()])
        return self._result()

    def generate_title(self, transcript: str, max_words: int = 8) -> str:
        self.calls.append("generate_title")
        return self.reply.get("title", "Recorded reply")

    def generate_bookmark_label_with_context(
        self, local_context: str = "", meeting_summary: str = "",
        max_words: int = 5,
    ) -> str:
        self.calls.append("generate_bookmark_label_with_context")
        return self.reply.get("bookmark_label", "Recorded")

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str = "",
                   **_kwargs: Any) -> str:
        self.calls.append("run_prompt")
        return self.reply.get("raw_text", json.dumps(self.reply))

    def run_prompt_messages(self, *, messages: Any, **_kwargs: Any) -> str:
        self.calls.append("run_prompt_messages")
        return self.reply.get("raw_text", json.dumps(self.reply))

    def run_prompt_stream(self, **_kwargs: Any) -> Any:
        self.calls.append("run_prompt_stream")
        return iter(())


def _install_engine_replay(path: Path) -> str:
    """Install the recorded reply at the product's own provider seam.

    The seam is `holdspeak.intel.providers._configured_engine`
    (holdspeak/intel/providers.py:213), reached by the one production caller
    `configured_meeting_intel` (:276). There is no product-supported replay
    provider kind (`VALID_INTEL_PROVIDERS` is local|cloud|auto,
    holdspeak/intel/models.py:34), so this is the same module attribute the
    glass rigs monkeypatch — assigned here inside the hub's OWN process,
    because a parent-process patch could never reach it.
    """
    import holdspeak.intel.engine as engine_module
    import holdspeak.intel.providers as providers_module

    reply = json.loads(path.read_text())
    engine = _ReplayIntel(reply)
    engine_module.MeetingIntel = lambda **_: engine
    providers_module._configured_engine = lambda: engine
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _serve(port: int, token: str, host: str = "127.0.0.1",
           scheduler: bool = False, engine_replay: str | None = None) -> None:
    """The rig's hub subprocess: a real MeetingWebServer on a fresh HOME.

    It takes the product's OWN database owner lock and runs the product's own
    intel drainer, because the drainer refuses to start without ownership
    (`owns_database`, holdspeak/intel_queue_conductor.py:72, :129). It does NOT
    construct `AudioRecorder` or `HotkeyListener` (holdspeak/web_runtime.py:507)
    — the microphone and native keystrokes are forbidden to this rig — so
    `on_start` (start a live recording) refuses by name instead.
    """
    guard_home(os.environ.get("HOME", "/nonexistent"))
    from holdspeak.db import get_database
    from holdspeak.runtime_lock import claim_database, refusal_message
    from holdspeak.services.errors import ValidationError
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    database = get_database()
    print(f"DB_PATH {database.db_path}", flush=True)

    has: list[str] = ["MeetingWebServer routes"]
    lacks: list[str] = [
        "AudioRecorder (the microphone is forbidden to this rig)",
        "HotkeyListener (no native keystrokes)",
        "voice_session / device registry",
        "transcriber warm-up",
        "the deferred plugin-queue thread",
        "the Cadence Engine tick",
    ]

    if engine_replay:
        digest = _install_engine_replay(Path(engine_replay))
        has.append("a RECORDED provider reply at the real provider seam")
        print(f"ENGINE_REPLAY {digest}", flush=True)

    lock = claim_database(Path(str(database.db_path)))
    if lock.held:
        has.append("the database owner lock")
    else:
        print("OWNER_LOCK_REFUSED "
              + refusal_message(Path(str(database.db_path)), lock.owner()),
              flush=True)
        lacks.append("the database owner lock (another process holds it)")

    def _no_microphone(**_kwargs: Any) -> Any:
        raise ValidationError(
            "microphone forbidden: this rig never opens the owner's microphone "
            "(brief §7). Use the fixture WAV at the documented input boundary.")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_start=_no_microphone,
            on_stop=lambda: None,
            on_meeting_stop=lambda: None,
            get_state=lambda: {"active": False, "id": "", "status": "idle",
                               "activity": {"state": "idle", "source": "rig"}},
        ),
        host=host, port=port, auth_token=token,
    )
    url = server.start()

    drainer = None
    if lock.held:
        from holdspeak.intel_queue_conductor import start_intel_queue_conductor

        drainer = start_intel_queue_conductor(broadcast=server.broadcast)
    if drainer is not None:
        has.append("the intelligence queue drainer")
    else:
        lacks.append("the intelligence queue drainer (it refused to start)")

    if scheduler:
        _start_real_heartbeat_conductor()
        has.append("the heartbeat conductor loop")
    else:
        lacks.append("the heartbeat conductor loop (not requested by the case)")

    print("WIRING " + json.dumps({"has": has, "lacks": lacks}), flush=True)
    print(f"HUB_READY {url}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:  # pragma: no cover — operator interrupt
        pass
    finally:
        from holdspeak.runtime_lock import release_database

        release_database()


# ──────────────────────────────────────────── the calibration page host ──


def _fresh_calibration_state() -> dict[str, Any]:
    """The stand-in protocol surface: the shape the real routes answer in.

    `projections` + `counts` mirror `GET /api/desk/projections`
    (holdspeak/db/projections.py:140); `person_sections_state` mirrors
    `GET /api/brief/latest`.
    """
    return {
        "projections": [
            {"id": "cal:r1", "title": "SWEEP", "subject_ref": "service:HeartbeatService",
             "projection_kind": "receipt", "attention_state": "resolved"},
            {"id": "cal:r2", "title": "BINDING", "subject_ref": "profile:cal-p1",
             "projection_kind": "attention", "attention_state": "unseen"},
        ],
        "counts": {"needs_attention": 0, "unseen": 1, "acknowledged": 0, "receipts": 1},
        "person_sections_state": "unavailable",
        "nothing_here": None,
    }


# The fixture state lives in a FILE so a restart of the fixture server can be
# a real restart (a new process) with the value surviving it — the stand-in for
# a hub restart against the same database.
_CAL_STATE_ENV = "GRAPH_WALK_CAL_STATE"


def _cal_state_path() -> Path:
    return Path(os.environ[_CAL_STATE_ENV])


def _read_cal_state() -> dict[str, Any]:
    return json.loads(_cal_state_path().read_text())


def _write_cal_state(state: dict[str, Any]) -> None:
    _cal_state_path().write_text(json.dumps(state))


class _CalibrationHandler(BaseHTTPRequestHandler):
    """The static page, plus the small protocol surface the cases drive."""

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        try:
            return json.loads(self.rfile.read(length).decode())
        except Exception:  # noqa: BLE001
            return None

    def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's name
        if self.path.startswith("/echo"):
            self._json(200, {"ok": True})
            return
        if self.path.startswith("/state"):
            self._json(200, {**_read_cal_state(), "served_by_pid": os.getpid()})
            return
        if self.path.split("?")[0] == "/api/meetings":
            # the shape of GET /api/meetings: newest first
            self._json(200, {"meetings": _read_cal_state().get("meetings", [])})
            return
        body = CALIBRATION_PAGE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith("/refuse"):
            # An intelligible refusal, by name — the shape a 4xx case promises.
            self._json(422, {"error": "no engine is assigned for "
                                      "meeting.deferred_analysis"})
            return
        if self.path.split("?")[0] == "/api/meetings/import":
            # a SYNTHETIC import boundary with the real route's answer:
            # 202 {"meeting_id", "status": "importing"}
            # (holdspeak/services/meeting_service.py:226). It counts uploads, so
            # a fence can prove the trigger really fired.
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            multipart = ("multipart/form-data" in (self.headers.get("Content-Type") or "")
                         and b'name="file"' in raw)
            state = _read_cal_state()
            state["upload_calls"] = int(state.get("upload_calls", 0)) + 1
            if not multipart:
                _write_cal_state(state)
                self._json(422, {"error": "file: field required (multipart)"})
                return
            meeting_id = f"cal-m-{state['upload_calls']}"
            state.setdefault("meetings", []).insert(
                0, {"id": meeting_id, "status": "importing", "bytes": len(raw)})
            _write_cal_state(state)
            self._json(202, {"meeting_id": meeting_id, "status": "importing"})
            return
        if self.path.split("?")[0] == "/brief/generate":
            # the same-day idempotent producer: the SAME brief every time
            state = _read_cal_state()
            state["generate_calls"] = int(state.get("generate_calls", 0)) + 1
            _write_cal_state(state)
            self._json(200, {"id": "brief-7", "headline": "Nothing material changed."})
            return
        if self.path.split("?")[0] == "/brief/generate-fresh":
            # a producer that mints a NEW brief the page never shows
            state = _read_cal_state()
            state["generate_calls"] = int(state.get("generate_calls", 0)) + 1
            _write_cal_state(state)
            self._json(200, {"id": "brief-8", "headline": "Something else."})
            return
        if self.path.startswith("/state/note"):
            state = _read_cal_state()
            state["note"] = (self._body() or {}).get("note")
            _write_cal_state(state)
            self._json(200, {"note": state["note"]})
            return
        self._json(404, {"error": "no such route"})

    def do_DELETE(self) -> None:  # noqa: N802
        prefix = "/state/rows/"
        if self.path.startswith(prefix):
            row_id = self.path[len(prefix):]
            state = _read_cal_state()
            kept = [r for r in state["projections"] if r["id"] != row_id]
            removed = len(state["projections"]) - len(kept)
            state["projections"] = kept
            _write_cal_state(state)
            self._json(200 if removed else 404, {"removed": removed})
            return
        self._json(404, {"error": "no such route"})

    def log_message(self, *_args: Any) -> None:  # quiet
        return


def _serve_calibration(port: int, state: str) -> None:
    """(internal) the fixture server, in its own process so it can restart."""
    os.environ[_CAL_STATE_ENV] = state
    server = ThreadingHTTPServer(("127.0.0.1", port), _CalibrationHandler)
    print(f"CAL_READY {port}", flush=True)
    server.serve_forever()


class CalibrationServer:
    """The fixture server, hub-shaped: the calibration cases run through the
    SAME code path (`.api`, `.restart`) that a real hub run uses.

    Its state file stands in for the hub's database: a restart is a new
    process, and the value written before it must still be there after it.
    """

    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path).resolve()
        self.port = _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen[str] | None = None

    @property
    def db_path(self) -> str:
        return str(self.state_path)

    def start(self, timeout: float = 30.0) -> "CalibrationServer":
        self.proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "serve-calibration",
             "--port", str(self.port), "--state", str(self.state_path)],
            cwd=str(REPO), text=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("the calibration server died on boot")
            try:
                if self.api("GET", "/state")[0] == 200:
                    return self
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.2)
        raise RuntimeError("the calibration server never became ready")

    def api(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode()
            try:
                return exc.code, json.loads(raw)
            except Exception:  # noqa: BLE001
                return exc.code, raw[:600]

    def upload(self, method: str, path: str, wav: Path, field: str) -> tuple[int, Any]:
        """The same multipart upload a real hub receives."""
        return _multipart_upload(f"{self.base}{path}", method, wav, field, {})

    def restart(self) -> dict[str, Any]:
        return _restart_process(self)

    def stop(self) -> None:
        _terminate(self.proc)
        self.proc = None


def _terminate(proc: subprocess.Popen[str] | None, bound: float = 15.0) -> None:
    """SIGTERM, wait to the bound, then SIGKILL. Never leaves a process behind."""
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=bound)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=bound)


def _restart_process(owner: Any) -> dict[str, Any]:
    """Stop the owned process cleanly and start it again the same way.

    Same port, same HOME, same flags, same database. The record names both
    pids and the downtime, so an observation cannot claim a restart that did
    not happen.
    """
    before_db = owner.db_path
    stopped_pid = owner.proc.pid if owner.proc else None
    started_at = time.monotonic()
    owner.stop()
    owner.start()
    record = {
        "stopped_pid": stopped_pid,
        "started_pid": owner.proc.pid if owner.proc else None,
        "downtime_s": round(time.monotonic() - started_at, 2),
        "same_db_path": owner.db_path == before_db,
        "db_path": owner.db_path,
        "port": owner.port,
    }
    if not record["same_db_path"]:
        raise Blocked(
            f"the restarted process opened {owner.db_path}, not {before_db}; "
            "a restart case must read the SAME database")
    if record["started_pid"] == record["stopped_pid"]:
        raise Blocked("the process kept its pid; nothing was restarted")
    return record


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

#: The NEGATIVE CONTROLS. Each one PASSED before the fixes Astra's counsel
#: named, and each must now come out as stated here. They are run by the unit
#: fence, not by `calibrate`, so the six stay the six.
CALIBRATION_NEGATIVE_CASES: list[dict[str, Any]] = [
    {
        # (1) a Refresh whose handler was removed. The replay identity is on
        # the page already; before the fix the rig read it and called it a pass.
        "id": "NEG-1-refresh-without-handler",
        "job": "a dead Refresh must not pass on an identity it never wrote",
        "edge_ids": ["neg:1"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#o-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#o-out",
                     "predicate": {"kind": "unchanged",
                                   "replay_identity": "#o-out@data-replay-id"}},
        "completion_bound_s": 2, "late_grace_s": 0.5, "viewports": [1440],
    },
    {
        # (2) the result is real, but it arrives at ~4s under a 1s bound.
        "id": "NEG-2-result-after-the-bound",
        "job": "a result after the completion bound is never a pass",
        "edge_ids": ["neg:2"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#p-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#p-out",
                     "predicate": {"kind": "text_contains", "value": "ready"}},
        "completion_bound_s": 1, "late_grace_s": 8, "viewports": [1440],
    },
    {
        # (3a) an absence inside a scope that does not exist
        "id": "NEG-3a-absent-without-a-scope",
        "job": "an absence proves nothing when the scope is missing",
        "edge_ids": ["neg:3a"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#a-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#no-such-element",
                     "predicate": {"kind": "text_absent", "value": "an error"}},
        "completion_bound_s": 2, "late_grace_s": 0.5, "viewports": [1440],
    },
    {
        # (3b) an attribute on an element that does not exist
        "id": "NEG-3b-attr-without-a-scope",
        "job": "an attribute check on a missing element is blocked, not a pass",
        "edge_ids": ["neg:3b"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#a-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#no-such-element",
                     "predicate": {"kind": "attr_equals", "attr": "aria-busy",
                                   "value": "false"}},
        "completion_bound_s": 2, "late_grace_s": 0.5, "viewports": [1440],
    },
    {
        # (5) the starting state was never reached
        "id": "NEG-5-precondition-not-met",
        "job": "a case whose starting state is absent is blocked, not failed",
        "edge_ids": ["neg:5"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": [
            "the calibration page is loaded",
            {"kind": "check", "observe_at": "#q-out",
             "predicate": {"kind": "text_contains", "value": "ready to go"}},
        ],
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#q-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#q-out",
                     "predicate": {"kind": "text_contains", "value": "went"}},
        "completion_bound_s": 2, "viewports": [1440],
    },
    {
        # (7) an atlas case that states only `words`
        "id": "NEG-7-words-only",
        "job": "a words-only case earns no verdict",
        "edge_ids": ["neg:7"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#a-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#a-out",
                     "words": "the desk says it was saved"},
        "completion_bound_s": 2, "viewports": [1440],
    },
    {
        # a check step INSIDE setup, evaluated where it appears
        "id": "NEG-8-check-in-setup-fails",
        "job": "a setup check that does not hold blocks the case where it stands",
        "edge_ids": ["neg:8"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [
            {"kind": "ui", "action": "click", "selector": "#q-btn",
             "adapter": "ui-pointer"},
            {"kind": "check", "observe_at": "#q-out",
             "predicate": {"kind": "text_contains", "value": "never written"}},
        ],
        "trigger": {"kind": "ui", "action": "click", "selector": "#a-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#q-out",
                     "predicate": {"kind": "text_contains", "value": "went"}},
        "completion_bound_s": 2, "viewports": [1440],
    },
    {
        # a placeholder nothing ever captured
        "id": "NEG-9-unresolved-placeholder",
        "job": "an unfilled {name} is never sent literally",
        "edge_ids": ["neg:9"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the calibration protocol surface is up",
        "setup": [],
        "trigger": {"kind": "api", "method": "DELETE",
                    "path": "/state/rows/{never_captured}", "adapter": "http-route"},
        "expected": {"observe_at": "protocol: GET /state",
                     "predicate": {"kind": "protocol_rows_gone",
                                   "collection": "projections",
                                   "match": {"id": "cal:r1"}, "min_gone": 1}},
        "completion_bound_s": 10, "viewports": [],
    },
]

# Astra round three, finding 3: "a different ID beside unchanged old
# content" must FAIL. The click POSTs; the producer returns brief-8; the face
# still shows brief-7 beside the old words.
CALIBRATION_NEGATIVE_CASES.append({
    "id": "NEG-10-stale-id-beside-old-content",
    "job": "a clicked verb's returned id must be the one displayed",
    "edge_ids": ["neg:10"], "state_id": "cal:page",
    "applicability": "applicable",
    "preconditions": "the calibration page is loaded",
    "setup": [],
    "trigger": {"kind": "ui", "action": "click", "selector": "#s-stale",
                "adapter": "ui-pointer"},
    "expected": {"observe_at": "#s-content",
                 "predicate": {"kind": "unchanged", "replay_identity": "trigger:id",
                               "identity_display": "#s-id"}},
    "completion_bound_s": 3, "viewports": [1440],
})

# Astra round three, finding 2: a placeholder that NOTHING binds (the import
# trigger here declares no `capture_as`) blocks BEFORE the trigger fires, so
# the synthetic import boundary counts zero uploads.
CALIBRATION_NEGATIVE_CASES.append({
    "id": "NEG-11-unbindable-placeholder-never-fires",
    "job": "an `expected` naming a value nothing captures never fires the trigger",
    "edge_ids": ["neg:11"], "state_id": "cal:protocol",
    "applicability": "applicable",
    "preconditions": "the calibration protocol surface is up",
    "setup": [],
    "trigger": {"kind": "fixture", "path": "tests/fixtures/core_path_smoke_16k.wav",
                "route": {"method": "POST", "path": "/api/meetings/import"},
                "field": "file", "adapter": "http-route"},
    "expected": {"observe_at": "protocol: GET /api/meetings",
                 "predicate": {"kind": "protocol_field", "path": "/meetings/0/id",
                               "value": "{meeting_id}"}},
    "completion_bound_s": 10, "viewports": [],
})

#: What each negative control MUST come out as. A `pass` here is a false pass.
CALIBRATION_NEGATIVE_EXPECTED: dict[str, str] = {
    "NEG-10-stale-id-beside-old-content": "fail",
    "NEG-11-unbindable-placeholder-never-fires": "blocked",
    "NEG-1-refresh-without-handler": "fail",
    "NEG-2-result-after-the-bound": "fail",
    "NEG-3a-absent-without-a-scope": "blocked",
    "NEG-3b-attr-without-a-scope": "blocked",
    "NEG-5-precondition-not-met": "blocked",
    "NEG-7-words-only": "blocked",
    "NEG-8-check-in-setup-fails": "blocked",
    "NEG-9-unresolved-placeholder": "blocked",
}


# NOT part of the six either. One case per predicate kind added for the nine
# `words`-only atlas cases, each driven through the same engine, and none
# decidable by the mere presence of a diff.
CALIBRATION_PREDICATE_CASES: list[dict[str, Any]] = [
    {
        # serves case.j6.route_intelligence_run.refusal
        "id": "CAL-h-refusal-status",
        "job": "a route refuses by name; the refusal IS the promised result",
        "edge_ids": ["cal:h"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the calibration protocol surface is up",
        "setup": [],
        "trigger": {"kind": "api", "method": "POST", "path": "/refuse",
                    "body": {}, "adapter": "http-route"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_status", "method": "POST",
                          "path": "/refuse", "status": 422},
        },
        "completion_bound_s": 10, "viewports": [],
    },
    {
        # serves case.j3.profile_unbind.binding_absent and
        # case.beyond.sweep_held_remote.receipt_resolved
        "id": "CAL-i-row-gone",
        "job": "a NAMED row disappears (never merely 'fewer rows')",
        "edge_ids": ["cal:i"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the row cal:r2 is present",
        "setup": [],
        "trigger": {"kind": "api", "method": "DELETE", "path": "/state/rows/cal:r2",
                    "adapter": "http-route"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_rows_gone", "collection": "projections",
                          "match": {"subject_ref": "profile:cal-p1"},
                          "identity": "id", "min_gone": 1},
        },
        "completion_bound_s": 10, "viewports": [],
    },
    {
        # serves case.beyond.projections_list.counts, the two brief shelf cases
        # and case.j10.brief_people.unavailable
        "id": "CAL-j-protocol-field",
        "job": "a read whose own response is the result: a named field, at a "
               "nested path. The zero diff is EXPLAINED — the trigger is a read.",
        "edge_ids": ["cal:j"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the calibration protocol surface is up",
        "setup": [],
        "trigger": {"kind": "api", "method": "GET", "path": "/state",
                    "adapter": "http-route"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_field", "path": "counts.unseen",
                          "value": 1},
        },
        "completion_bound_s": 10, "viewports": [],
    },
    {
        # serves case.beyond.first_words_reload.retained_draft
        "id": "CAL-k-retained-draft",
        "job": "typed words come back in the field after a reload",
        "edge_ids": ["cal:k"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded; text typed and not kept",
        "setup": [{"kind": "ui", "action": "fill", "selector": "#k-draft",
                   "value": "one sentence", "adapter": "ui-keyboard",
                   "why": "typing is SETUP; the reload is the trigger"}],
        "trigger": {"kind": "ui", "action": "reload", "adapter": "ui-navigation"},
        "expected": {
            "observe_at": "#case-k",
            "predicate": {"kind": "input_value", "selector": "#k-draft",
                          "contains": "one sentence"},
        },
        "completion_bound_s": 15, "viewports": [1440],
    },
    {
        # serves case.j6.route_intelligence_run.refusal — the NAMING half
        "id": "CAL-m-refusal-names-what-is-missing",
        "job": "the refusal names what is missing, not merely a failing status",
        "edge_ids": ["cal:m"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the calibration protocol surface is up",
        "setup": [],
        "trigger": {"kind": "api", "method": "POST", "path": "/refuse",
                    "body": {}, "adapter": "http-route"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_status", "method": "POST",
                          "path": "/refuse", "status": 422,
                          "body_contains": "meeting.deferred_analysis"},
        },
        "completion_bound_s": 10, "viewports": [],
    },
    {
        # serves case.beyond.sweep_held_remote.receipt_resolved — the
        # "no local sweep runs" half: an ASSERTED absence, by named bound
        "id": "CAL-n-no-new-rows",
        "job": "nothing of that named shape appeared — an asserted absence",
        "edge_ids": ["cal:n"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the calibration protocol surface is up",
        "setup": [],
        "trigger": {"kind": "api", "method": "GET", "path": "/state",
                    "adapter": "http-route",
                    "why": "a read mints nothing; the bound, not the zero diff, "
                           "earns the verdict"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_rows", "collection": "projections",
                          "match": {"subject_ref": "service:HeartbeatService",
                                    "outcome": "held_remote_runs_on"},
                          "min_new": 0, "max_new": 0},
        },
        "completion_bound_s": 10, "viewports": [],
    },
    {
        # serves case.j7.hub_restart.intel_retained
        "id": "CAL-l-restart-retained",
        "job": "what was written before the restart is still there after it",
        "edge_ids": ["cal:l"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "a value written through the route before the restart",
        "setup": [{"kind": "api", "method": "POST", "path": "/state/note",
                   "body": {"note": "the summary"}, "expect_status": 200,
                   "adapter": "http-route"}],
        "trigger": {"kind": "cli", "action": "restart_hub", "adapter": "process"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_field", "path": "note",
                          "value": "the summary"},
        },
        "completion_bound_s": 60, "viewports": [],
    },
    {
        # a value captured from one response and used in a LATER step's path
        # and in the predicate's own match (e.g. /api/meetings/{meeting_id})
        "id": "CAL-r-captured-variable",
        "job": "an id read from one response drives the next step and the predicate",
        "edge_ids": ["cal:r"], "state_id": "cal:protocol",
        "applicability": "applicable",
        "preconditions": "the calibration protocol surface is up",
        "setup": [{"kind": "api", "method": "GET", "path": "/state",
                   "capture_as": "row_id", "capture_path": "projections.0.id",
                   "adapter": "http-route"}],
        "trigger": {"kind": "api", "method": "DELETE",
                    "path": "/state/rows/{row_id}", "adapter": "http-route"},
        "expected": {
            "observe_at": "protocol: GET /state",
            "predicate": {"kind": "protocol_rows_gone", "collection": "projections",
                          "match": {"id": "{row_id}"}, "min_gone": 1},
        },
        "completion_bound_s": 10, "viewports": [],
    },
]

# Astra round three, finding 3: a CLICKED verb's identity is its own network
# response. (s) has no declared route, so the rig takes the first same-origin
# non-GET response after the click (the GET before it is skipped); (t) names
# its route and reads the status of the click's own POST.
CALIBRATION_PREDICATE_CASES.extend([
    {
        "id": "CAL-s-clicked-identity",
        "job": "a clicked verb returns the same brief, and the face shows that brief",
        "edge_ids": ["cal:s"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#s-good",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#s-content",
                     "predicate": {"kind": "unchanged",
                                   "replay_identity": "trigger:id",
                                   "identity_display": "#s-id"}},
        "completion_bound_s": 3, "viewports": [1440],
    },
    {
        "id": "CAL-t-clicked-status",
        "job": "the status of the POST a click fired, by its declared route",
        "edge_ids": ["cal:t"], "state_id": "cal:page",
        "applicability": "applicable",
        "preconditions": "the calibration page is loaded",
        "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#s-good",
                    "adapter": "ui-pointer",
                    "trigger_route": {"method": "POST", "path": "/brief/generate"}},
        "expected": {"observe_at": "#s-content",
                     "predicate": {"kind": "protocol_status", "method": "POST",
                                   "path": "/brief/generate", "status": 200,
                                   "body_contains": "brief-7"}},
        "completion_bound_s": 5, "viewports": [1440],
    },
])

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


#: The rig's CLOSED step vocabulary, beside `UI_ACTIONS`, so the atlas fence
#: can import both and refuse a case the rig could never drive.
STEP_KINDS = frozenset({"api", "ui", "fixture", "clock", "boundary", "cli", "check"})

#: `{name}` — a value captured by an earlier step. Only an identifier matches,
#: so JSON braces in a body are never mistaken for a placeholder.
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

#: The fields of `expected` the rig actually READS. `words` is prose for the
#: council and may carry `{attempt_id}` as English, not as a placeholder.
_EXPECTED_READ_FIELDS = ("observe_at", "predicate", "reads", "pending_marker")

#: The step fields a captured value may travel into.
_SUBSTITUTED_FIELDS = ("path", "selector", "name", "value", "url", "key", "body",
                       "observe_at")


def substitute(value: Any, variables: dict[str, str]) -> Any:
    """Fill `{name}` from the captured variables, anywhere in a structure."""
    if isinstance(value, str):
        return _PLACEHOLDER.sub(
            lambda m: str(variables[m.group(1)]) if m.group(1) in variables
            else m.group(0), value)
    if isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, variables) for v in value]
    return value


def unresolved(value: Any) -> list[str]:
    """Every `{name}` still unfilled. A step with one is never fired."""
    if isinstance(value, str):
        return _PLACEHOLDER.findall(value)
    if isinstance(value, dict):
        return [n for v in value.values() for n in unresolved(v)]
    if isinstance(value, list):
        return [n for v in value for n in unresolved(v)]
    return []


#: The rig's CLOSED ui vocabulary. A step naming anything else is blocked
#: before it fires, so a typo cannot silently become a no-op that "passed".
UI_ACTIONS = frozenset({
    "goto", "reload", "click", "click_role", "fill", "press", "wait_for",
})


def _ui_step(page: Any, step: dict[str, Any], hub: Any = None) -> dict[str, Any]:
    action = step.get("action")
    if action not in UI_ACTIONS:
        raise Blocked(
            f"ui action {action!r} is not in the rig's vocabulary "
            f"{sorted(UI_ACTIONS)}; nothing was fired")
    optional = bool(step.get("optional"))
    record = {"kind": "ui", "action": action, "adapter": step.get("adapter", "ui-pointer")}
    timeout = float(step.get("timeout_s", 10)) * 1000
    try:
        if action == "goto":
            url = step["url"]
            if not str(url).startswith("http"):
                # relative: resolved by the context's base_url, and the hub's
                # token is carried so a bare "/" is not an unauthenticated load
                token = step.get("token") or getattr(hub, "token", None)
                if token and "token=" not in str(url):
                    url = f"{url}{'&' if '?' in str(url) else '?'}token={token}"
            page.goto(url)
            record["url"] = url
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
        record["done"] = True
    except Blocked:
        raise
    except Exception as exc:  # noqa: BLE001
        record["done"] = False
        record["error"] = repr(exc)[:400]
        if not optional:
            # name the TARGET plainly: a reader (and a fence) should not have
            # to unescape a repr to learn which selector was unreachable
            target = step.get("selector") or step.get("name") or step.get("url")
            raise Blocked(
                f"ui step {action} on {target!r} failed: {type(exc).__name__}: "
                f"{str(exc)[:200]}") from exc
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
    entry = snapshot(page, case, hub)
    baseline = (entry.get("protocol") or {}).get("payload_sha256") or entry.get("text")
    predicate = (case.get("expected") or {}).get("predicate") or {}
    state_at_entry = False
    if predicate.get("kind") == "protocol_field":
        state_at_entry, _reading = check_predicate(predicate, entry, entry)
    started = time.monotonic()
    polls = 0
    changed = False
    while not state_at_entry and time.monotonic() - started < max_wait:
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
        "state_satisfied_at_entry": state_at_entry,
        "machine_clock_moved": False,
    })
    return {"kind": "clock", "adapter": step.get("adapter"),
            "clock": step.get("clock"), "waited_s": waited, "polls": polls,
            "state_satisfied_at_entry": state_at_entry,
            "conductor_ticks_waited": ticks, "observe_at_changed": changed,
            "done": True}


def _restart_detail(snap: dict[str, Any]) -> dict[str, Any]:
    """Retain the useful meeting material around a real hub restart."""
    payload = (snap.get("protocol") or {}).get("payload") or {}
    intel = payload.get("intel") if isinstance(payload, dict) else None
    return {
        "meeting_id": payload.get("id") if isinstance(payload, dict) else None,
        "summary": intel.get("summary") if isinstance(intel, dict) else None,
        "run_receipt": payload.get("run_receipt") if isinstance(payload, dict) else None,
        "transcription_status": payload.get("transcription_status") if isinstance(payload, dict) else None,
        "payload": payload,
    }


def run_step(step: dict[str, Any], page: Any, hub: Hub | None,
             provenance: dict[str, Any], case: dict[str, Any] | None = None,
             *, allow_error: bool = False,
             variables: dict[str, str] | None = None) -> dict[str, Any]:
    """One setup step or the trigger, by kind. Records the adapter it drove."""
    kind = step.get("kind")
    if kind not in STEP_KINDS:
        raise Blocked(f"step kind {kind!r} is not in the rig's vocabulary "
                      f"{sorted(STEP_KINDS)}; nothing was fired")
    variables = variables if variables is not None else {}
    step = substitute(step, variables)
    missing = unresolved({f: step.get(f) for f in _SUBSTITUTED_FIELDS})
    if missing:
        raise Blocked(
            f"unresolved placeholder(s) {sorted(set(missing))} in the {kind} "
            "step; nothing was sent. A `{name}` is filled by an earlier step's "
            "`capture_as`, never sent literally.")

    if kind == "check":
        # The same evaluator a verdict uses, at the point it stands. It is
        # given a bounded wait: a face that is still loading has not yet
        # refused the precondition.
        probe_case = {"expected": {"observe_at": step.get("observe_at"),
                                   "predicate": step.get("predicate")}}
        deadline = time.monotonic() + float(step.get("timeout_s", 5))
        waited = 0.0
        while True:
            snap = snapshot(page, probe_case, hub)
            ok, why = check_predicate(step.get("predicate"), snap, snap)
            if ok or time.monotonic() >= deadline:
                break
            if page is not None:
                page.wait_for_timeout(300)
            waited = round(time.monotonic() - (deadline - float(step.get("timeout_s", 5))), 2)
        record = {"kind": "check", "observe_at": step.get("observe_at"),
                  "predicate": step.get("predicate"),
                  "adapter": step.get("adapter", "observation"),
                  "waited_s": waited, "holds": ok, "reading": why}
        if not ok:
            raise Blocked(
                f"precondition not met: {step.get('predicate')} at "
                f"{step.get('observe_at')!r} — {why}")
        return record

    if kind == "ui":
        return _ui_step(page, step, hub)
    if kind == "api":
        if hub is None:
            raise Blocked("an api step needs a hub; this pass has none")
        status, payload = hub.api(step["method"], step["path"], step.get("body"))
        record = {"kind": "api", "method": step["method"], "path": step["path"],
                  "adapter": step.get("adapter", "http-route"), "status": status,
                  "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600],
                  "response_sha256": hashlib.sha256(
                      json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()}
        want = step.get("expect_status")
        if want is not None and status != want:
            raise Blocked(f"{step['method']} {step['path']} answered {status}, wanted {want}: {record['response']}"[:500])
        # A SETUP step that errors means the preconditions were never reached,
        # so the case is blocked. A TRIGGER's error status is the observation
        # itself (an intelligible refusal is a promised result), so it is
        # recorded and the predicate decides.
        if want is None and status >= 400 and not allow_error:
            raise Blocked(f"{step['method']} {step['path']} answered {status}: {record['response']}"[:500])
        name = step.get("capture_as")
        if name:
            where = step.get("capture_path", "id")
            found, value = _json_path(payload, where)
            if not found or value is None:
                raise Blocked(
                    f"capture_as {name!r}: no value at {where!r} in the response "
                    f"of {step['method']} {step['path']}")
            variables[name] = str(value)
            record["captured"] = {"name": name, "path": where, "value": str(value)}
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
            route["method"], route["path"], wav, step.get("field", "file"),
            form=step.get("form"))
        record = {"kind": "fixture", "path": step["path"], "route": route,
                  "adapter": step.get("adapter", "http-route"), "status": status,
                  "response": payload if isinstance(payload, (dict, list)) else str(payload)[:600]}
        want_status = step.get("expect_status")
        if want_status is not None and status != want_status:
            raise Blocked(
                f"{route['method']} {route['path']} answered {status}, "
                f"wanted {want_status}: {record['response']}"[:500])
        if status >= 400:
            raise Blocked(f"the input boundary answered {status}: {record['response']}"[:500])
        name = step.get("capture_as")
        if name:
            # the import route answers 202 {"meeting_id": …, "status": "importing"}
            # (holdspeak/services/meeting_service.py:226), so an import case
            # declares `capture_path: "meeting_id"`.
            where = step.get("capture_path", "id")
            found, value = _json_path(payload, where)
            if not found or value is None:
                raise Blocked(
                    f"capture_as {name!r}: no value at {where!r} in the response "
                    f"of the input boundary {route['method']} {route['path']} "
                    f"(it answered {record['response']})"[:500])
            variables[name] = str(value)
            record["captured"] = {"name": name, "path": where, "value": str(value)}
        if step.get("wait_for"):
            record["completion_wait"] = wait_for_fixture_completion(
                hub, step["wait_for"], variables)
        return record
    if kind == "cli":
        action = step.get("action")
        if action != "restart_hub":
            raise Blocked(
                f"cli command {(step.get('command') or action)!r} is not "
                "implemented in this rig; the case is blocked, not claimed. The "
                "one implemented command is action 'restart_hub'.")
        if hub is None or not hasattr(hub, "restart"):
            raise Blocked("a restart_hub step needs the rig's own hub process")
        resolved_case = substitute(case or {}, variables)
        before_restart = snapshot(page, resolved_case, hub) if page is not None else None
        record = {"kind": "cli", "action": "restart_hub",
                  "adapter": step.get("adapter", "process"), **hub.restart()}
        after_restart = snapshot(page, resolved_case, hub) if page is not None else None
        record["hub_identity"] = {
            "url": hub.url,
            "port": hub.port,
            "db_path": hub.db_path,
            "stopped_pid": record.get("stopped_pid"),
            "started_pid": record.get("started_pid"),
        }
        if before_restart is not None and after_restart is not None:
            record["meeting_before"] = _restart_detail(before_restart)
            record["meeting_after"] = _restart_detail(after_restart)
            record["summary_retained"] = (
                record["meeting_before"].get("summary") ==
                record["meeting_after"].get("summary")
                and record["meeting_after"].get("summary") not in (None, "")
            )
            record["receipt_retained"] = (
                record["meeting_before"].get("run_receipt") ==
                record["meeting_after"].get("run_receipt")
                and record["meeting_after"].get("run_receipt") not in (None, {})
            )
            record["meeting_identity_retained"] = (
                record["meeting_before"].get("meeting_id") ==
                record["meeting_after"].get("meeting_id")
            )
            name = step.get("capture_as")
            if name:
                summary = record["meeting_before"].get("summary")
                if summary in (None, ""):
                    raise Blocked(
                        "restart capture_as requested a pre-restart summary, "
                        "but the meeting detail had no summary")
                variables[name] = str(summary)
                record["captured"] = {
                    "name": name,
                    "path": "intel.summary",
                    "value": str(summary),
                }
        provenance["restarts"].append(record)
        # A face case must look at the hub again: the page was talking to a
        # process that no longer exists.
        observe_at = ((case or {}).get("expected") or {}).get("observe_at")
        if page is not None and protocol_target(observe_at) is None:
            page.reload(wait_until=step.get("wait_until", "load"))
            record["page_reloaded"] = True
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
        # Astra's counsel: a boundary that only WROTE ITS LABEL down proved
        # nothing. It must perform the substitution it names, or block.
        label = step.get("label", "unlabelled")
        substitution = step.get("substitute")
        record: dict[str, Any] = {
            "kind": "boundary", "label": label, "substitute": substitution,
            "adapter": step.get("adapter", "labelled-substitution")}
        if substitution != "engine_reply":
            raise Blocked(
                f"boundary substitution {substitution!r} (label {label!r}) is not "
                "implemented; a label alone substitutes nothing. The one "
                "implemented substitution is 'engine_reply'.")
        if hub is None or getattr(hub, "engine_replay", None) is None:
            raise Blocked(
                "the recorded provider reply is NOT installed in the hub "
                "process. Declare `reply` on the boundary step so the hub is "
                "booted with it (the seam is a module attribute inside the "
                "hub's own process; a parent-process patch cannot reach it).")
        declared = step.get("reply")
        if declared:
            digest = _sha256(_repo_path(declared))
            if digest != hub.engine_replay:
                raise Blocked(
                    f"the hub installed reply {hub.engine_replay[:12]}, not the "
                    f"case's {digest[:12]}")
            provenance["fixture_hashes"][declared] = digest
        record["installed_sha256"] = hub.engine_replay
        record["seam"] = ("holdspeak.intel.providers._configured_engine + "
                          "holdspeak.intel.engine.MeetingIntel")
        provenance["boundary_substitutions"].append(
            {"label": label, "substitute": substitution,
             "installed_sha256": hub.engine_replay})
        provenance["engine_mode"] = "replayed"
        inner = step.get("api")
        if inner:
            record["inner"] = run_step({"kind": "api", **inner}, page, hub, provenance, case)
        return record
    raise Blocked(f"step kind {kind!r} has no runner in this rig")  # pragma: no cover


def case_predicate(case: dict[str, Any]) -> Any:
    """The case's expected-result predicate, or None for a `words`-only case.

    Never a KeyError: an atlas case that states only `words` is a fact about
    the atlas, and the rig records it as blocked.
    """
    return (case.get("expected") or {}).get("predicate")


def check_preconditions(case: dict[str, Any], page: Any, hub: Any,
                        recorder: Any = None,
                        variables: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Evaluate the case's preconditions after setup, before the before-capture.

    A precondition may be an executable step (any step kind, plus
    `{"kind": "check", "predicate": …, "observe_at": …}`) or prose. Prose is
    RECORDED and ignored — and says so. An executable check that does not hold
    blocks the case: its starting state was never reached.
    """
    declared = case.get("preconditions")
    if declared is None:
        return []
    entries = declared if isinstance(declared, list) else [declared]
    records: list[dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, str):
            records.append({"kind": "prose", "text": entry, "checked": False,
                            "note": "prose precondition: recorded, not checked "
                                    "by the rig"})
            continue
        if not isinstance(entry, dict):
            records.append({"kind": "unreadable", "value": str(entry)[:200],
                            "checked": False})
            continue
        try:
            records.append({"checked": True, **run_step(
                entry, page, hub,
                {"fixture_hashes": {}, "boundary_substitutions": [], "restarts": []},
                case, variables=variables)})
        except Blocked as blocked:
            # recorded BEFORE the refusal: a blocked case keeps the evidence of
            # why its starting state was never reached
            records.append({"checked": True, "kind": entry.get("kind"),
                            "observe_at": entry.get("observe_at"),
                            "predicate": entry.get("predicate"),
                            "holds": False, "reading": str(blocked)})
            if recorder is not None:
                recorder.set(preconditions=records)
            raise
    return records


def arm_replay_identity(page: Any, predicate: Any, before: dict[str, Any]) -> dict[str, Any] | None:
    """Make a replay identity provable: clear it, so the operation must rewrite it.

    Astra's counsel: an `unchanged` contract passed on an identity that was
    already on the page — a Refresh with its handler removed looked identical
    to a working one. The identity must be produced by THIS operation, so it
    comes either from the trigger's own response (`trigger:<path>`) or from an
    ATTRIBUTE the rig blanks here and the operation must write again.
    """
    if not isinstance(predicate, dict) or predicate.get("kind") != "unchanged":
        return None
    spec = identity_spec(predicate)
    if not spec or spec.get("from") != "selector":
        return None  # a trigger identity needs no probe: the response is fresh
    selector, attr = spec.get("selector"), spec.get("attr")
    if not attr:
        raise Blocked(
            f"replay identity {spec!r} names no attribute. An identity the "
            "operation must REWRITE is an attribute (`#sel@data-rev`) or the "
            "trigger's own response (`trigger:<path>`); page text alone cannot "
            "prove which operation wrote it.")
    cleared = page.evaluate(
        """([selector, attr]) => {
            const el = document.querySelector(selector);
            if (!el) return false;
            el.removeAttribute(attr);
            return true;
        }""",
        [selector, attr],
    )
    return {
        "spec": spec,
        "value_before": (before.get("replay_identity") or {}).get("value"),
        "cleared": bool(cleared),
        "why": "cleared before the trigger: the operation must write it again, "
               "so an identity left over from before cannot pass",
    }


def case_applicable(case: dict[str, Any]) -> tuple[bool, str]:
    """`applicability` is a word in W2's atlas and an object in the sample.

    Both are read; neither is guessed at.
    """
    value = case.get("applicability")
    if isinstance(value, str):
        word = value.strip().lower()
        # the atlas carries the WHY beside the word; it travels verbatim
        return (word in ("applicable", "yes", "true"),
                str(case.get("reason") or value))
    if isinstance(value, dict):
        return (value.get("applicable") is not False,
                str(value.get("reason", "no reason recorded")))
    return True, "no applicability recorded"


def _repo_path(declared: str) -> Path:
    """A path in a case: absolute as given, otherwise relative to the repo."""
    candidate = Path(declared)
    return candidate if candidate.is_absolute() else REPO / declared


def case_engine_replay(case: dict[str, Any]) -> str | None:
    """The recorded provider reply a boundary step declares, if any."""
    for step in case_steps(case):
        if step.get("kind") == "boundary" and step.get("substitute") == "engine_reply":
            return step.get("reply")
    return None


def case_steps(case: dict[str, Any]) -> list[dict[str, Any]]:
    steps = [s for s in (case.get("setup") or []) if isinstance(s, dict)]
    steps += [s for s in (case.get("preconditions") or [])
              if isinstance(s, dict)] if isinstance(case.get("preconditions"), list) else []
    if isinstance(case.get("trigger"), dict):
        steps.append(case["trigger"])
    return steps


def case_needs_scheduler(case: dict[str, Any]) -> bool:
    """True when a step drives the real conductor loop (`scheduler-wait`)."""
    return any(
        step.get("kind") == "clock"
        and str(step.get("adapter") or "").startswith("scheduler-wait")
        for step in case_steps(case)
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


def _blank_unresolved(value: Any) -> Any:
    """Every string still carrying a `{name}` becomes None (a `reads` entry
    with an unresolved path is dropped). Used for the reads BEFORE a trigger
    that will bind the name: nothing is ever sent with a literal `{name}`."""
    if isinstance(value, str):
        return None if unresolved(value) else value
    if isinstance(value, dict):
        return {k: _blank_unresolved(v) for k, v in value.items()}
    if isinstance(value, list):
        kept = [_blank_unresolved(v) for v in value]
        return [v for v in kept
                if not (isinstance(v, dict) and "path" in v and v["path"] is None)]
    return value


def _url_path(url: str) -> str:
    return urllib.parse.urlsplit(url).path or "/"


def _url_origin(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


class _UiResponseCapture:
    """The network response a clicked verb fired (Astra round three, finding 3).

    Armed before the click. A candidate is a response to a request issued
    AFTER arming. The chosen one is, in order of preference:

    * the first response matching the step's (or the case's) declared
      `trigger_route: {method, path}` — the path compared without its query,
      `{name}` filled from the captured variables;
    * otherwise the first SAME-ORIGIN, NON-GET response after the click.

    It is recorded with method, path, status, body_sha256 and body, and the
    rule that chose it, so `trigger:<path>` identity and `protocol_status`
    work for a clicked verb exactly as for an api trigger.
    """

    def __init__(self, page: Any, step: dict[str, Any], case: dict[str, Any],
                 variables: dict[str, str]) -> None:
        self.page = page
        route = step.get("trigger_route") or case.get("trigger_route")
        self.route = substitute(route, variables) if isinstance(route, dict) else None
        self.origin = _url_origin(page.url or "")
        self.requests: list[Any] = []
        self.responses: list[Any] = []
        self._chosen: dict[str, Any] | None = None
        self._closed = False
        self._on_request = lambda request: self.requests.append(request)
        self._on_response = lambda response: self.responses.append(response)
        page.on("request", self._on_request)
        page.on("response", self._on_response)

    def rule(self) -> str:
        if self.route:
            return (f"the declared trigger_route "
                    f"{str(self.route.get('method', '')).upper()} {self.route.get('path')}")
        return f"the first same-origin ({self.origin}) non-GET response after the click"

    def _issued_after_arming(self, response: Any) -> bool:
        request = response.request
        return any(request is seen for seen in self.requests)

    def _matches(self, response: Any) -> bool:
        request = response.request
        method = str(request.method).upper()
        if self.route:
            want_method = str(self.route.get("method") or method).upper()
            return (method == want_method
                    and _url_path(response.url) == self.route.get("path"))
        return (method != "GET" and _url_origin(response.url) == self.origin)

    def chosen(self) -> dict[str, Any] | None:
        if self._chosen is not None:
            return self._chosen
        for response in list(self.responses):
            if not self._issued_after_arming(response) or not self._matches(response):
                continue
            body: Any = None
            body_error = None
            try:
                raw = response.body()
                try:
                    body = json.loads(raw.decode())
                except Exception:  # noqa: BLE001
                    body = raw.decode(errors="replace")[:2000]
            except Exception as exc:  # noqa: BLE001
                body_error = repr(exc)[:300]
            self._chosen = {
                "method": str(response.request.method).upper(),
                "path": _url_path(response.url),
                "status": response.status,
                "body_sha256": hashlib.sha256(
                    json.dumps(body, sort_keys=True, default=str).encode()).hexdigest(),
                "body": body,
                "source": "ui-network",
                "chosen_by": self.rule(),
            }
            if body_error:
                self._chosen["body_error"] = body_error
            return self._chosen
        return None

    def record(self) -> dict[str, Any]:
        seen = [
            {"method": str(r.request.method).upper(), "path": _url_path(r.url),
             "status": r.status, "same_origin": _url_origin(r.url) == self.origin,
             "after_arming": self._issued_after_arming(r)}
            for r in list(self.responses)[:40]
        ]
        chosen = self.chosen()
        return {
            "rule": self.rule(),
            "chosen": ({k: v for k, v in chosen.items() if k != "body"}
                       if chosen else None),
            "why": (f"chosen by {self.rule()}" if chosen else
                    f"NO response matched {self.rule()}; the click fired none"),
            "seen": seen,
        }

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for event, handler in (("request", self._on_request),
                               ("response", self._on_response)):
            try:
                self.page.remove_listener(event, handler)
            except Exception:  # noqa: BLE001
                pass


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
    #: Values captured by setup steps (`capture_as`), filled into every later
    #: step and into the case's own `expected`. An unresolved one is blocked.
    variables: dict[str, str] = {}
    steps: list[dict[str, Any]] = []
    for step in case.get("setup", []):
        try:
            step_record = run_step(step, page, hub, provenance, case,
                                   variables=variables)
            steps.append(step_record)
            recorder.set(setup=steps, provenance=provenance,
                         variables=dict(variables))
            wait = step_record.get("completion_wait")
            if wait and not wait.get("matched"):
                raise Blocked(
                    f"fixture completion did not reach its declared fields in "
                    f"{wait.get('elapsed_s')}s: {wait.get('field_matches')}"
                )
        except Blocked as exc:
            recorder.set(setup=steps, setup_error={
                "step": step, "error": str(exc)[:800]},
                variables=dict(variables))
            raise

    # Placeholders in `expected` are resolved AFTER the trigger (Astra round
    # three, finding 2): a trigger that mints `{meeting_id}` (J4's import,
    # `capture_as`) must be FIRED before its own `expected` can name the id.
    # A placeholder that neither setup nor the trigger can bind blocks here,
    # before anything is fired.
    trigger = case_trigger(case)
    minted = {trigger.get("capture_as")} - {None, ""}
    pre_expected = substitute(case.get("expected") or {}, variables)
    outstanding = set(unresolved({field: pre_expected.get(field)
                                  for field in _EXPECTED_READ_FIELDS}))
    unbindable = outstanding - minted
    if unbindable:
        raise Blocked(
            f"unresolved placeholder(s) {sorted(unbindable)} in the case's "
            "`expected`: no setup step and not the trigger captures them "
            "(`capture_as`), so the trigger was NOT fired")
    # Before the trigger, a read field that names a value the trigger will
    # mint cannot be read yet: it is blanked (never sent with a literal
    # `{name}`), and the record says so.
    pre_case = {**case, "expected": _blank_unresolved(pre_expected)}
    if outstanding:
        recorder.set(pending_placeholders=sorted(outstanding))
        recorder.note(
            f"placeholder(s) {sorted(outstanding)} are bound by the trigger's own "
            "`capture_as`; `expected` is resolved after it fires (fields naming "
            "them are not read before the trigger)")
    pre_predicate = case_predicate(pre_case)

    # Preconditions, AFTER setup and BEFORE the before-capture: a case whose
    # starting state was never reached is blocked, not failed.
    settle(page)
    checks = check_preconditions(pre_case, page, hub, recorder, variables)
    recorder.set(preconditions=checks)

    settle(page)
    before = snapshot(page, pre_case, hub)
    page.screenshot(path=str(shots / "before.png"))
    recorder.set(before=_clean(before))

    # A replay identity must be produced by THIS operation. The rig records it
    # and then clears it, so an identity that merely SAT on the page before the
    # trigger cannot be mistaken for one the operation wrote (Astra's counsel).
    probe = arm_replay_identity(page, pre_predicate, before)
    if probe:
        recorder.set(replay_identity_probe=probe)

    # A clicked verb's own network response (Astra round three, finding 3):
    # the listener is armed BEFORE the click, so only requests the click (or
    # what follows it) issued are candidates.
    ui_capture = (_UiResponseCapture(page, trigger, case, variables)
                  if trigger.get("kind") == "ui" and page is not None else None)
    fired_at = time.monotonic()
    try:
        trigger_record = run_step(trigger, page, hub, provenance, pre_case,
                                  allow_error=True, variables=variables)
        wait = trigger_record.get("completion_wait")
        if wait and not wait.get("matched"):
            recorder.set(trigger=trigger_record, provenance=provenance,
                         variables=dict(variables))
            raise Blocked(
                f"fixture completion did not reach its declared fields in "
                f"{wait.get('elapsed_s')}s: {wait.get('field_matches')}"
            )
    except Blocked as exc:
        recorder.set(trigger_error={"step": trigger, "error": str(exc)[:800]})
        if ui_capture is not None:
            ui_capture.close()
        raise
    except Exception as exc:
        recorder.set(trigger_error={"step": trigger,
                                    "error": f"{type(exc).__name__}: {exc}"[:800]})
        if ui_capture is not None:
            ui_capture.close()
        raise
    recorder.set(trigger=trigger_record, provenance=provenance,
                 variables=dict(variables))

    # From here the case reads with EVERY captured value filled in, including
    # the ones the trigger just bound. One still unfilled blocks, naming it.
    case = {**case, "expected": substitute(case.get("expected") or {}, variables)}
    predicate = case_predicate(case)
    still = unresolved({field: case["expected"].get(field)
                        for field in _EXPECTED_READ_FIELDS})
    if still:
        if ui_capture is not None:
            ui_capture.close()
        raise Blocked(
            f"unresolved placeholder(s) {sorted(set(still))} in the case's "
            "`expected` AFTER the trigger fired; the trigger did not bind them, "
            "so no observation location or predicate can be read")

    # The trigger's OWN response travels with every observation taken after it
    # (and with none taken before it): a `protocol_status` predicate reads the
    # status the route really answered instead of firing the call a second time.
    trigger_response = None
    if "status" in trigger_record:
        # a fixture trigger's `path` is the WAV; its route is where it went
        route = trigger_record.get("route") or {}
        trigger_response = {
            "method": route.get("method") or trigger_record.get("method"),
            "path": route.get("path") or trigger_record.get("path"),
            "status": trigger_record.get("status"),
            "body_sha256": trigger_record.get("response_sha256") or hashlib.sha256(
                json.dumps(trigger_record.get("response"), sort_keys=True,
                           default=str).encode()).hexdigest(),
            "body": trigger_record.get("response"),
        }

    def observe() -> dict[str, Any]:
        snap = snapshot(page, case, hub)
        answer = trigger_response
        if answer is None and ui_capture is not None:
            answer = ui_capture.chosen()
            recorder.record["trigger_response_capture"] = ui_capture.record()
        if answer is not None:
            snap["trigger_response"] = answer
        if trigger.get("kind") == "cli" and trigger.get("action") == "restart_hub":
            snap["restart"] = trigger_record
        return snap

    # The moment the promised result FIRST existed. The bound is measured
    # against this, never against the last poll: an `unchanged` contract holds
    # for the whole bound on purpose, and that is not lateness.
    first_satisfied_at: float | None = None

    def stamp(ok: bool) -> None:
        nonlocal first_satisfied_at
        if ok and first_satisfied_at is None:
            first_satisfied_at = round(time.monotonic() - fired_at, 3)

    # initial feedback: what the face said within ~1s of the trigger.
    page.wait_for_timeout(900)
    initial = observe()
    initial_ok, initial_why = check_predicate(predicate, before, initial)
    stamp(initial_ok)
    recorder.set(initial_feedback={
        **_clean(initial),
        "predicate_satisfied": initial_ok,
        "reading": initial_why,
        "elapsed_s": round(time.monotonic() - fired_at, 3),
    })

    # terminal outcome: poll to the bound. An `unchanged` contract is never
    # settled early — it must hold for the whole bound.
    bound = float(case.get("completion_bound_s", 20))
    hold = isinstance(predicate, dict) and predicate.get("kind") == "unchanged"
    after = initial
    satisfied, why = initial_ok, initial_why
    while time.monotonic() - fired_at < bound:
        if satisfied and not hold:
            break
        page.wait_for_timeout(400)
        after = observe()
        satisfied, why = check_predicate(predicate, before, after)
        stamp(satisfied)

    settle(page)
    after = observe()
    satisfied, why = check_predicate(predicate, before, after)
    stamp(satisfied)
    elapsed = round(time.monotonic() - fired_at, 3)

    # A result that arrives after the bound is NOT a pass: the case named the
    # time the owner would wait, and the rig honours it (Astra's counsel).
    late = bool(satisfied and (first_satisfied_at or elapsed) > bound)
    if late:
        satisfied = False
        why = (f"the result was there at {first_satisfied_at}s, AFTER the bound "
               f"of {bound}s")

    # Distinguish "slow" from "dead": when the bound passed with no result, keep
    # looking for a short grace and record a late arrival as `incomplete`.
    late_result_s = None
    if not satisfied and predicate is not None:
        grace_deadline = time.monotonic() + float(case.get("late_grace_s", 2.0))
        while time.monotonic() < grace_deadline:
            page.wait_for_timeout(400)
            late_snap = observe()
            late_ok, late_why = check_predicate(predicate, before, late_snap)
            if late_ok:
                after = late_snap
                late = True
                late_result_s = round(time.monotonic() - fired_at, 3)
                why = (f"the result arrived at {late_result_s}s, AFTER the bound "
                       f"of {bound}s ({late_why})")
                break

    pending = bool(after.get("pending_marker_present"))
    terminal = {
        # `settled` = the face stopped moving; `incomplete` = it is still
        # working, or it finished too late. Neither is a verdict.
        "state": "settled" if satisfied else (
            "incomplete" if (pending or late) else "settled"),
        "predicate_satisfied": satisfied,
        "reading": why,
        "pending_marker": (case.get("expected") or {}).get("pending_marker"),
        "pending_marker_present": after.get("pending_marker_present"),
        "elapsed_s": elapsed,
        "first_satisfied_at_s": first_satisfied_at,
        "completion_bound_s": bound,
        "late_result_s": late_result_s,
        "within_bound": bool(satisfied),
    }
    state = terminal["state"]
    page.screenshot(path=str(shots / "after.png"))
    if ui_capture is not None:
        recorder.set(trigger_response_capture=ui_capture.record())
        ui_capture.close()

    # A reading the evaluator itself could not make is BLOCKED, never a fail:
    # a missing scope or a missing predicate is a rig/atlas fact, not a defect.
    undecidable = why.startswith(("BLOCKED:", "UNDECIDABLE:"))
    decidable = isinstance(predicate, dict) and not undecidable
    verdict = "pass" if satisfied else ("fail" if decidable else "blocked")
    recorded_diff = diff(_clean(before), _clean(after))
    recorder.set(
        after=_clean(after),
        terminal_outcome=terminal,
        diff=recorded_diff,
        verdict=verdict,
        shots=[str(shots / "before.png"), str(shots / "after.png")],
    )
    framing = capture_framed_view(page, case, hub, shots)
    if framing is not None:
        recorder.set(framing=framing)
        if framing.get("done"):
            recorder.set(shots=[str(shots / "before.png"), str(shots / "after.png"),
                                framing["shot"]])
        recorder.note("framing is a separate scroll after the raw observation; "
                      "it does not change the verdict or completion time")
    recorder.note(f"predicate: {why}")
    if late:
        recorder.note("the completion bound was exceeded; `within_bound` is "
                      "false, so this can never be a pass (brief §3).")
    if not decidable:
        recorder.note("BLOCKED, not failed: the rig gathered the whole run "
                      "(setup, before, trigger, wait, after) but no verdict is "
                      "earned from it.")
    if not satisfied and decidable and not recorded_diff:
        recorder.note("UNRESOLVED: the promised result is absent and nothing moved "
                      "at all. A zero diff is never a pass (brief §3).")
    if not satisfied and decidable and recorded_diff:
        recorder.note("a nonzero diff with the wrong result is a finding, not a pass "
                      f"(changed: {sorted(recorded_diff)}).")
    elsewhere = found_elsewhere(predicate, after)
    if elsewhere:
        recorder.note(elsewhere)
    if state == "incomplete" and pending:
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


def capture_framed_view(page: Any, case: dict[str, Any], hub: Hub | None,
                        shots: Path) -> dict[str, Any] | None:
    """Optional glass framing AFTER the raw verdict, never a completion predicate."""
    selector = (case.get("expected") or {}).get("frame_selector")
    if not selector:
        return None
    record: dict[str, Any] = {"selector": selector,
                              "action": "scroll_into_view_center", "done": False}
    try:
        page.locator(selector).first.evaluate(
            "el => el.scrollIntoView({block: 'center', inline: 'nearest'})", timeout=5000)
        _settle_fn()(page)
        record["snapshot"] = _clean(snapshot(page, case, hub))
        page.screenshot(path=str(shots / "framed.png"))
        record.update(done=True, shot=str(shots / "framed.png"))
    except Exception as exc:  # raw verdict and shots remain intact
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


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
        # a stable shape: a blocked case says plainly that the trigger never
        # fired, instead of leaving the reader to infer it from a missing key
        "setup": [],
        "preconditions": [],
        "variables": {},
        "trigger": None,
        "diff": {},
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
    state_path = out / "calibration-state.json"
    state_path.write_text(json.dumps(_fresh_calibration_state()))
    fixture = CalibrationServer(state_path).start()
    base = fixture.base + "/"
    profile = Path(tempfile.mkdtemp(prefix="graph-walk-calib-profile-"))
    records: list[dict[str, Any]] = []
    try:
        with sync_playwright() as play:
            context = play.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                viewport={"width": viewport, "height": 900},
                # a case's `goto "/"` resolves against the server under test
                base_url=fixture.base,
                args=["--use-fake-device-for-media-stream",
                      "--use-fake-ui-for-media-stream"],
            )
            try:
                for case in (cases or CALIBRATION_CASES):
                    run_id = new_run_id(case["id"], brain, viewport)
                    shots = _run_dir(out, run_id)
                    provenance = base_provenance(engine_mode="none")
                    provenance["hub"] = {
                        "kind": "calibration fixture server (its own process)",
                        "port": fixture.port,
                        "pid": fixture.proc.pid if fixture.proc else None}
                    provenance["db_path"] = fixture.db_path
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
                        exercise(page, case, recorder=recorder, hub=fixture,
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
        fixture.stop()
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

    replay = case_engine_replay(case)
    if replay and engine != "replayed":
        recorder.set(verdict="blocked", complete=True)
        recorder.note(
            f"the case declares a provider replay at {replay!r}, but this run "
            f"was requested with --engine {engine!r}; replay is installed only "
            "for an explicit replayed run")
        return recorder.record
    if engine == "replayed" and not replay:
        recorder.set(verdict="blocked", complete=True)
        recorder.note(
            "--engine replayed was requested but the case declares no "
            "engine_reply boundary")
        return recorder.record

    if build:
        _ensure_build()

    home = Path(tempfile.mkdtemp(prefix="graph-walk-home-"))
    profile = Path(tempfile.mkdtemp(prefix="graph-walk-profile-"))
    hub: Hub | None = None
    try:
        scheduler = case_needs_scheduler(case)
        hub = Hub(home, token=token, scheduler=scheduler,
                  engine_replay=_repo_path(replay) if replay else None).start()
        provenance["hub"] = {"url": hub.url, "port": hub.port,
                             "pid": hub.proc.pid if hub.proc else None,
                             "home": str(home),
                             # brief §7: keep unrelated scheduler activity
                             # identifiable. It is OFF unless a case asks.
                             "scheduler_thread": scheduler}
        provenance["clock"]["scheduler_thread"] = scheduler
        provenance["db_path"] = hub.db_path
        provenance["frontend_build"] = _frontend_build()
        # brief §7: say what product wiring this hub HAS and LACKS, so no
        # observation is read as if it came from the whole product.
        provenance["product_wiring"] = hub.wiring
        provenance["engine_replay_sha256"] = hub.engine_replay
        if engine == "real":
            provenance["engine_identity"] = _engine_identity()
        recorder.set(provenance=provenance)

        with sync_playwright() as play:
            context = play.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                viewport={"width": viewport,
                          "height": 900 if viewport >= 1000 else 852},
                device_scale_factor=2,
                # An atlas case says `goto "/"`. Without a base url Chromium
                # answers "Cannot navigate to invalid URL"; with it the case
                # reads the same on any port. An http(s) url stays absolute.
                base_url=hub.url,
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
                blocked_shot = shots / "blocked.png"
                try:
                    page.screenshot(path=str(blocked_shot))
                except Exception as shot_error:  # noqa: BLE001 — retain the block
                    recorder.note(f"blocked screenshot unavailable: {shot_error}")
                else:
                    recorder.set(shots=[str(blocked_shot)])
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
    p_serve.add_argument("--engine-replay", default=None,
                         help="a recorded provider reply to install at the seam")

    p_cal_serve = sub.add_parser("serve-calibration",
                                 help="(internal) the calibration fixture server")
    p_cal_serve.add_argument("--port", type=int, required=True)
    p_cal_serve.add_argument("--state", required=True)

    args = parser.parse_args(argv)

    if args.mode == "serve-calibration":
        _serve_calibration(args.port, args.state)
        return 0

    if args.mode == "serve":
        _serve(args.port or _free_port(), args.token,
               scheduler=bool(getattr(args, "scheduler", False)),
               engine_replay=getattr(args, "engine_replay", None))
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
