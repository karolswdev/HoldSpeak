"""Verify probes — a recipe that cannot prove its own world fails loudly.

A probe is a list of typed assertions, each read back **through the
product's own routes** (never by poking its DB). A probe result names the
assertion, whether it held, and what the product actually returned — so a
failed recipe says exactly which claim it could not verify.

Assertion forms in YAML (single-key mappings, arg scalar or mapping):

    probe:
      - notes_min_count: 2
      - note_exists: uat-seed-note-decisions
      - kb_exists: uat-seed-kb-project
      - meeting_with_open_actions: {min_actions: 1, timeout: 180}
      - runtime_endpoint_unreachable: true
      - setup_not_ready: true
      - mesh_node_seen: uat-worker
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .product_client import ProductClient


@dataclass
class ProbeResult:
    kind: str
    ok: bool
    detail: str
    arg: Any = None

    def to_dict(self) -> dict:
        return {"kind": self.kind, "ok": self.ok, "detail": self.detail, "arg": self.arg}


@dataclass
class ProbeReport:
    results: list[ProbeResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def failed(self) -> list[ProbeResult]:
        return [r for r in self.results if not r.ok]

    def to_dict(self) -> dict:
        return {"ok": self.ok, "results": [r.to_dict() for r in self.results]}

    def summary(self) -> str:
        if self.ok:
            return f"probe ok ({len(self.results)} assertions)"
        return "; ".join(f"{r.kind}: {r.detail}" for r in self.failed)


class ProbeError(RuntimeError):
    pass


class ProbeEvaluator:
    """Evaluates a probe spec against a booted run."""

    def __init__(self, client: ProductClient, *, home: Path | None = None, run_id: str | None = None):
        self.client = client
        self.home = home
        self.run_id = run_id

    def evaluate(self, spec: list[Any] | None) -> ProbeReport:
        report = ProbeReport()
        for assertion in spec or []:
            kind, arg = _split_assertion(assertion)
            method = getattr(self, f"_check_{kind}", None)
            if method is None:
                report.results.append(
                    ProbeResult(kind, False, f"unknown probe kind {kind!r}", arg)
                )
                continue
            try:
                ok, detail = method(arg)
            except Exception as exc:  # a probe that errors is a probe that failed
                ok, detail = False, f"probe raised: {exc}"
            report.results.append(ProbeResult(kind, ok, detail, arg))
        return report

    # --- desk primitives --------------------------------------------------

    def _notes(self) -> list[dict]:
        return self.client.get_json("/api/notes").get("notes", [])

    def _kbs(self) -> list[dict]:
        return self.client.get_json("/api/kbs").get("kbs", [])

    def _check_notes_empty(self, _arg):
        notes = self._notes()
        return (len(notes) == 0, f"{len(notes)} notes present")

    def _check_notes_min_count(self, arg):
        n = int(arg)
        notes = self._notes()
        return (len(notes) >= n, f"{len(notes)} notes (need ≥{n})")

    def _check_note_exists(self, arg):
        wanted = str(arg)
        ids = {n.get("id") for n in self._notes()}
        return (wanted in ids, f"note {wanted!r} {'present' if wanted in ids else 'absent'}")

    def _check_kbs_empty(self, _arg):
        kbs = self._kbs()
        return (len(kbs) == 0, f"{len(kbs)} KBs present")

    def _check_kbs_min_count(self, arg):
        n = int(arg)
        kbs = self._kbs()
        return (len(kbs) >= n, f"{len(kbs)} KBs (need ≥{n})")

    def _check_kb_exists(self, arg):
        wanted = str(arg)
        ids = {k.get("id") for k in self._kbs()}
        return (wanted in ids, f"KB {wanted!r} {'present' if wanted in ids else 'absent'}")

    # --- other desk primitives (verify seeded state) ----------------------

    def _list_ids(self, path: str, key: str) -> set:
        try:
            return {x.get("id") for x in self.client.get_json(path).get(key, [])}
        except Exception:
            return set()

    def _check_recipe_exists(self, arg):
        wanted = str(arg)
        present = wanted in self._list_ids("/api/recipes", "recipes")
        return (present, f"recipe {wanted!r} {'present' if present else 'absent'}")

    def _check_chain_exists(self, arg):
        wanted = str(arg)
        present = wanted in self._list_ids("/api/chains", "chains")
        return (present, f"chain {wanted!r} {'present' if present else 'absent'}")

    def _check_workflow_exists(self, arg):
        wanted = str(arg)
        present = wanted in self._list_ids("/api/workflows", "workflows")
        return (present, f"workflow {wanted!r} {'present' if present else 'absent'}")

    def _check_directory_exists(self, arg):
        """A desk zone (directory) is present. arg = id, or {id, members: [ids]}."""
        wanted = str(arg if not isinstance(arg, dict) else arg.get("id"))
        try:
            dirs = self.client.get_json("/api/directories").get("directories", [])
        except Exception:
            dirs = []
        match = next((d for d in dirs if d.get("id") == wanted), None)
        if match is None:
            return (False, f"zone {wanted!r} absent")
        if isinstance(arg, dict) and arg.get("members"):
            have = set(match.get("member_ids", []))
            want = set(arg["members"])
            return (want <= have, f"zone {wanted!r} members {sorted(have)} (need {sorted(want)})")
        return (True, f"zone {wanted!r} present")

    # Alias — a "zone" reads more naturally in a recipe than "directory".
    _check_zone_exists = _check_directory_exists

    def _check_profile_exists(self, arg):
        wanted = str(arg)
        present = wanted in self._list_ids("/api/profiles", "profiles")
        return (present, f"profile {wanted!r} {'present' if present else 'absent'}")

    # --- meetings ---------------------------------------------------------

    def _check_meeting_with_open_actions(self, arg):
        if isinstance(arg, dict):
            min_actions = int(arg.get("min_actions", 1))
            timeout = float(arg.get("timeout", 180))
        else:
            min_actions, timeout = 1, 180.0
        deadline = time.monotonic() + timeout
        last = "no meetings"
        while time.monotonic() < deadline:
            meetings = self.client.get_json("/api/meetings", params={"limit": 50}).get(
                "meetings", []
            )
            # Wait out any still-importing meeting before judging.
            importing = [m for m in meetings if m.get("intel_status") == "importing"]
            with_actions = [
                m for m in meetings if int(m.get("action_item_count") or 0) >= min_actions
            ]
            if with_actions:
                m = with_actions[0]
                return (
                    True,
                    f"meeting {m.get('id')} '{m.get('title')}' has "
                    f"{m.get('action_item_count')} open action(s), intel={m.get('intel_status')}",
                )
            if meetings and not importing:
                last = (
                    "meetings present but none with ≥"
                    f"{min_actions} open actions: "
                    + ", ".join(
                        f"{m.get('title')}({m.get('action_item_count')},{m.get('intel_status')})"
                        for m in meetings[:4]
                    )
                )
            elif importing:
                last = f"{len(importing)} meeting(s) still importing…"
            time.sleep(2.0)
        return (False, f"timed out after {timeout:.0f}s: {last}")

    # --- runtime / first-run ---------------------------------------------

    def _check_runtime_endpoint_unreachable(self, _arg):
        t0 = time.monotonic()
        resp = self.client.post_json("/api/setup/runtime-test")
        elapsed = time.monotonic() - t0
        data = resp.json()
        ok = (data.get("ok") is False) and (
            data.get("status") in {"unreachable", "error", "missing_model", "unconfigured"}
        )
        fast = elapsed < 5.0
        return (
            ok and fast,
            f"runtime-test ok={data.get('ok')} status={data.get('status')!r} "
            f"in {elapsed:.1f}s: {data.get('detail','')}",
        )

    def _check_setup_not_ready(self, _arg):
        status = self.client.get_json("/api/setup/status")
        overall = str(status.get("overall", "")).lower()
        ready = overall == "pass"
        return (not ready, f"setup overall={overall!r} (first-run expects not-pass)")

    def _check_setup_reachable(self, _arg):
        resp = self.client.get("/api/setup/status")
        return (resp.status_code == 200, f"/api/setup/status HTTP {resp.status_code}")

    # --- mesh -------------------------------------------------------------

    def _mesh_liveness(self, name: str) -> dict | None:
        """The hub's own liveness view of a meshNode, via /api/profiles.

        The hub stamps a node's last-seen on every relay claim poll (the mesh's
        only heartbeat); ``GET /api/profiles`` reports ``mesh_liveness[node] =
        {live, last_seen_seconds}`` for each meshNode profile. This is the
        product-side read the recipe verifies against."""
        try:
            data = self.client.get_json("/api/profiles")
        except Exception:
            return None
        return (data.get("mesh_liveness") or {}).get(name)

    def _check_mesh_node_live(self, arg):
        name = str(arg if not isinstance(arg, dict) else arg.get("name"))
        timeout = float(arg.get("timeout", 40)) if isinstance(arg, dict) else 40.0
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            live = self._mesh_liveness(name)
            last = live
            if live and live.get("live"):
                return (True, f"node {name!r} live (seen {live.get('last_seen_seconds')}s ago)")
            time.sleep(2.0)
        return (False, f"node {name!r} not live within {timeout:.0f}s (liveness={last})")

    def _check_mesh_node_offline(self, arg):
        name = str(arg if not isinstance(arg, dict) else arg.get("name"))
        timeout = float(arg.get("timeout", 60)) if isinstance(arg, dict) else 60.0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            live = self._mesh_liveness(name)
            if live is None or not live.get("live"):
                return (True, f"node {name!r} reads offline (liveness={live})")
            time.sleep(3.0)
        return (False, f"node {name!r} still reads live within {timeout:.0f}s")

    # --- live steering (via the product's /api/coders routes) -------------

    def _steer_session(self, name: str) -> str:
        from . import steering

        return steering.session_name(self.run_id or "", name)

    def _peek(self, name: str) -> dict:
        from . import steering

        session = self._steer_session(name)
        key = steering.pane_key_for_session(self.client, session)
        if key is None:
            return {"_missing": True}
        try:
            return self.client.get_json(f"/api/coders/{steering.enc(key)}/peek")
        except Exception:
            return {"_missing": True}

    def _check_pane_listed(self, arg):
        from . import steering

        name = str(arg if not isinstance(arg, dict) else arg.get("name"))
        session = self._steer_session(name)
        present = steering.pane_key_for_session(self.client, session) is not None
        return (present, f"pane {session!r} {'listed' if present else 'absent'}")

    def _check_pane_shows(self, arg):
        name = str(arg.get("name"))
        contains = str(arg.get("contains", ""))
        peek = self._peek(name)
        if peek.get("_missing"):
            return (False, f"no pane for {name!r}")
        blob = _json_str(peek)
        ok = peek.get("peek", {}).get("status") == "live" and contains in blob
        return (ok, f"peek live={peek.get('peek',{}).get('status')} contains={contains!r}:{contains in blob}")

    def _check_pane_awaiting_input(self, arg):
        name = str(arg if not isinstance(arg, dict) else arg.get("name"))
        marker = arg.get("marker", "AWAITING-INPUT") if isinstance(arg, dict) else "AWAITING-INPUT"
        peek = self._peek(name)
        if peek.get("_missing"):
            return (False, f"no pane for {name!r}")
        live = peek.get("peek", {}).get("status") == "live"
        shows = str(marker) in _json_str(peek)
        return (live and shows, f"pane live={live} shows-prompt={shows}")

    def _check_grant_live(self, arg):
        from . import steering

        name = str(arg if not isinstance(arg, dict) else arg.get("name"))
        session = self._steer_session(name)
        key = steering.pane_key_for_session(self.client, session)
        try:
            grants = self.client.get_json("/api/coders/steering/grants").get("grants", {})
        except Exception:
            grants = {}
        live = key is not None and key in grants
        return (live, f"grant for {key!r} {'live' if live else 'absent'}")

    def _check_audit_min(self, arg):
        n = int(arg if not isinstance(arg, dict) else arg.get("count", 1))
        try:
            audit = self.client.get_json("/api/coders/steering/audit").get("audit", [])
        except Exception:
            audit = []
        return (len(audit) >= n, f"{len(audit)} audit rows (need ≥{n})")

    def _check_keys_refused_unarmed(self, arg):
        """Sending keys to an UNARMED pane must refuse (the consent gate)."""
        from . import steering

        name = str(arg if not isinstance(arg, dict) else arg.get("name"))
        session = self._steer_session(name)
        key = steering.pane_key_for_session(self.client, session)
        if key is None:
            return (False, f"no pane for {name!r}")
        resp = self.client.post_json(f"/api/coders/{steering.enc(key)}/keys", {"keys": ["a"]})
        refused = resp.status_code != 200
        return (refused, f"unarmed keys refused={refused} (HTTP {resp.status_code})")

    # --- doctor (subprocess, product-routed) ------------------------------

    def _check_doctor_names_dead_endpoint(self, _arg):
        if self.home is None:
            return (False, "no run HOME available for doctor")
        import os

        env = os.environ.copy()
        env["HOME"] = str(self.home)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "holdspeak.main", "doctor"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return (False, "doctor hung (>30s) — the failure the recipe forbids")
        out = (proc.stdout + proc.stderr).lower()
        named = ("127.0.0.1:9" in out) or ("unreachable" in out) or (
            "endpoint" in out and "fail" in out
        )
        return (named, "doctor output names the dead endpoint" if named else
                "doctor did not name the dead endpoint")


def _json_str(obj: Any) -> str:
    import json

    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return str(obj)


def _split_assertion(assertion: Any) -> tuple[str, Any]:
    if isinstance(assertion, str):
        return assertion, True
    if isinstance(assertion, dict):
        if len(assertion) != 1:
            raise ProbeError(f"a probe assertion must be a single-key mapping: {assertion!r}")
        (kind, arg), = assertion.items()
        return str(kind), arg
    raise ProbeError(f"unrecognised probe assertion: {assertion!r}")
