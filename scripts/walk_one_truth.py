#!/usr/bin/env python3
"""HS-130-11 — The One Truth walk harness (reusable).

Proves, with assertions rather than inspection, the single claim Phase 130
exists to make: for every run, readiness, badge, doctor, and the receipt name
the SAME deployment and the SAME egress boundary, and every placement control
reports where it was inherited from.

Run with an ISOLATED HOME so it never touches a real hub DB:

    HOME=$(mktemp -d) XDG_DATA_HOME=$HOME/.local/share \
        .venv/bin/python scripts/walk_one_truth.py

Set HS_WALK_LAN=http://192.168.1.43:8080/v1 to include the live-metal
control-vs-treatment leg (a real LAN endpoint must report private_network
end-to-end, never cloud). Exits non-zero on the first failed assertion.
"""
from __future__ import annotations

import os
import sys
import tempfile
import urllib.request
from pathlib import Path

FAILS: list[str] = []
PASSES = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global PASSES
    if cond:
        PASSES += 1
        print(f"  PASS  {label}" + (f" — {detail}" if detail else ""))
    else:
        FAILS.append(label)
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n== {title} ==")


def main() -> int:
    from holdspeak.db.core import Database
    from holdspeak.intel.providers import (
        EGRESS_CLOUD,
        EGRESS_LOCAL,
        EGRESS_MESH,
        EGRESS_PRIVATE_NETWORK,
        egress_boundary,
        endpoint_egress,
        profile_key_env,
        profile_slot_id,
    )
    from holdspeak.inference_targets import resolve_inference_target, resolve_placement

    lan = os.environ.get("HS_WALK_LAN")

    # ---- 1. One egress vocabulary: control (cloud) vs treatment (LAN) ----
    section("HS-130-04 — one egress vocabulary (control vs treatment)")
    check("LAN 192.168.x → private_network (NOT cloud)",
          egress_boundary(cloud=True, base_url="http://192.168.1.43:8080/v1") == EGRESS_PRIVATE_NETWORK,
          egress_boundary(cloud=True, base_url="http://192.168.1.43:8080/v1"))
    check("public host api.openai.com → cloud (control)",
          egress_boundary(cloud=True, base_url="https://api.openai.com/v1") == EGRESS_CLOUD)
    check("loopback 127.0.0.1 → local",
          egress_boundary(cloud=False, base_url="http://127.0.0.1:8080/v1") == EGRESS_LOCAL)
    check("mesh node → mesh (never Local only)",
          egress_boundary(cloud=False, node="walk-edge") == EGRESS_MESH)
    hostless_badge = endpoint_egress(cloud=True, base_url=None)
    check("host-less cloud intent → no fabricated host in the badge (DEFAULT_CLOUD_HOST gone)",
          not hostless_badge.get("host"),
          f"badge={hostless_badge}")

    # ---- 2. Injective secret slots: the exfiltration path is closed ----
    section("HS-130-02 — collision-free secret slots")
    adversarial = ["foo-bar", "foo_bar", "foo.bar", "foo bar"]
    slots = {p: profile_slot_id(p) for p in adversarial}
    check("punctuation siblings → 4 distinct slots",
          len(set(slots.values())) == 4, str(slots))
    check("env names are 4 distinct too",
          len({profile_key_env(p) for p in adversarial}) == 4)

    # ---- 3. Placement provenance: inherit-down with source ----
    section("HS-130-01 — precedence resolver reports its source")
    home = Path(os.environ.get("XDG_DATA_HOME", tempfile.mkdtemp())) / "holdspeak"
    home.mkdir(parents=True, exist_ok=True)
    db = Database(home / "walk.db")
    db.profiles.upsert(profile_id="p-agent", name="Agent default", kind="openAICompatible",
                       base_url="http://192.168.1.50:8000/v1", model="agent-model")
    db.profiles.upsert(profile_id="p-run", name="Run this", kind="openAICompatible",
                       base_url="http://192.168.1.51:8000/v1", model="run-model")
    r_agent = resolve_placement(db, agent="p-agent")
    check("agent-only resolves to agent, source=agent",
          r_agent.effective_target_id == "p-agent" and r_agent.source == "agent",
          f"{r_agent.effective_target_id}/{r_agent.source}")
    r_over = resolve_placement(db, invocation="p-run", agent="p-agent")
    check("invocation overrides agent, source=invocation",
          r_over.effective_target_id == "p-run" and r_over.source == "invocation",
          f"{r_over.effective_target_id}/{r_over.source}")
    r_glob = resolve_placement(db)
    check("all-unset inherits to the named global default (never accidental this_machine)",
          r_glob.source == "global", f"{r_glob.effective_target_id}/{r_glob.source}")

    # ---- 4. One deployment identity: readiness == receipt == badge ----
    section("HS-130-03 — one deployment identity")
    tgt = resolve_inference_target(db, "p-agent")
    receipt = tgt.placement_receipt()
    dep = tgt.deployment
    check("target carries a DeploymentIdentity", dep is not None)
    if dep is not None:
        check("receipt model == deployment.model (no advertised-but-unloaded model)",
              receipt.get("model") == dep.model, f"{receipt.get('model')} == {dep.model}")
        check("deployment boundary == egress_boundary of its endpoint (private_network)",
              dep.boundary == EGRESS_PRIVATE_NETWORK, dep.boundary)

    # ---- 5. Settings version guard: a stale write is rejected ----
    section("HS-130-07 — settings versioned writes")
    from holdspeak.config import Config
    from holdspeak.services.settings_service import settings_revision
    cfg = Config()
    rev1 = settings_revision(cfg)
    cfg.dictation.pipeline.enabled = not cfg.dictation.pipeline.enabled
    rev2 = settings_revision(cfg)
    check("revision changes when the config changes", rev1 != rev2, f"{rev1} -> {rev2}")
    check("revision is stable for identical config", settings_revision(Config()) == rev1)

    # ---- 6. LIVE metal (.43): the real LAN endpoint is private_network end to end ----
    if lan:
        section(f"LIVE METAL — {lan} (control-vs-treatment on real hardware)")
        host = lan.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
        reachable, models = _probe(lan)
        check("real LAN endpoint reachable", reachable, f"{len(models)} model(s): {models[:2]}")
        db.profiles.upsert(profile_id="p-lan43", name="Homelab .43", kind="openAICompatible",
                           base_url=lan, model=(models[0] if models else "qwen"))
        lan_tgt = resolve_inference_target(db, "p-lan43")
        lan_receipt = lan_tgt.placement_receipt()
        b = egress_boundary(cloud=True, base_url=lan)
        check("live .43 classifies private_network (the metal proof)",
              b == EGRESS_PRIVATE_NETWORK, b)
        check("live .43 deployment boundary == private_network",
              lan_tgt.deployment is not None and lan_tgt.deployment.boundary == EGRESS_PRIVATE_NETWORK,
              getattr(lan_tgt.deployment, "boundary", None))
        check("live .43 receipt boundary == private_network (not cloud), no fabricated host",
              lan_receipt.get("boundary") == EGRESS_PRIVATE_NETWORK
              and "openai.com" not in str(lan_receipt),
              f"boundary={lan_receipt.get('boundary')} owner={lan_receipt.get('owner')}")
        _ = host
    else:
        print("\n(skip LIVE metal leg — set HS_WALK_LAN to include it)")

    print(f"\n{'='*56}\n{PASSES} passed, {len(FAILS)} failed")
    if FAILS:
        print("FAILURES:")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print("ALL ONE-TRUTH ASSERTIONS PASS")
    return 0



def _probe(url: str) -> tuple[bool, list[str]]:
    try:
        base = url.rstrip("/")
        req = urllib.request.Request(base + "/models")
        with urllib.request.urlopen(req, timeout=6) as resp:
            import json
            data = json.loads(resp.read().decode("utf-8"))
        rows = data.get("models") or data.get("data") or []
        names = [r.get("name") or r.get("id") or "" for r in rows]
        return True, [n for n in names if n]
    except Exception as exc:  # noqa: BLE001 — the harness reports, never raises
        print(f"    (probe error: {exc})")
        return False, []


if __name__ == "__main__":
    sys.exit(main())
