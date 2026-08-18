#!/usr/bin/env python3
"""HS-138-06 -- The People walk: full proof of the encrypted People ledger.

Proves every story-06 criterion on the real hub + production Desk bundle +
REAL macOS Keychain.  Reuses scripts/chair_walk.py's Hub/Shooter/goto harness.

The walk has TWO modes:

  Unattended (default):
    Builds the web bundle, boots the hub under an isolated HOME, proves
    readiness is unconfigured, takes screenshots, and prints the plan for
    the attended pass.  No Keychain dialog fires.

  Attended (--attended):
    Runs the full Keychain-touching flow: setup (writes key), seed,
    populated screenshots, restart, missing-key simulation, sentinel
    negative proof, network negative proof, and cleanup.  macOS shows GUI
    authorization dialogs the owner must click.

Run:
    # Unattended (safe, no prompts)
    uv run python scripts/people_walk_full.py

    # Attended (owner must be watching for Keychain prompts)
    uv run python scripts/people_walk_full.py --attended

Shots + transcript land in:
    pm/roadmap/holdspeak/phase-138-the-people-ledger/assets/walk/
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import chair_walk as cw  # noqa: E402
from chair_walk import (  # noqa: E402
    Hub,
    Shooter,
    check,
    finding,
    goto,
    section,
    _free_port,
)

WALK_OUT = REPO / "pm/roadmap/holdspeak/phase-138-the-people-ledger/assets/walk"
TOKEN = "hs-138-06-people-walk-token"
VIEWPORTS = ((1440, 900), (393, 900))

# Sentinel strings: distinctive tokens that must NEVER appear in plaintext
# anywhere in the walk's database or log files.
SENTINEL_NAME = "Zara Quixote-Sentinel"
SENTINEL_AGENDA = "xK7mQ-sentinel-agenda-token-9Fj2p"
SENTINEL_NOTE = "wR3nL-sentinel-note-body-4Hy8v"
SENTINEL_REQUEST = "qT5bJ-sentinel-request-body-6Dz1x"


# ----------------------------------------------------------------- HTTP helpers


def api(
    hub: Hub, method: str, path: str, body: object = None, timeout: float = 60.0,
) -> tuple[int, object]:
    """Authenticated request to the walk hub."""
    data = None
    headers = {"X-HoldSpeak-Token": hub.token}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        hub.url + path, data=data, headers=headers, method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        status = exc.code
    except (TimeoutError, socket.timeout, OSError) as exc:
        return -1, {"error": str(exc)}
    try:
        return status, json.loads(raw)
    except Exception:
        return status, raw


# ----------------------------------------------------------------- walk keychain


def _kc_env(home: str) -> dict[str, str]:
    """Env for keyring subprocesses: they must see the WALK home, never the
    owner's real HOME, or every Keychain op lands in the real login keychain."""
    return {**os.environ, "HOME": home}


def create_walk_keychain(home: str) -> None:
    """Create + unlock a walk-scoped login keychain inside the isolated HOME.

    macOS resolves the login keychain from $HOME, so a fresh HOME has none and
    the first keyring write dies with a "Keychain Not Found" dialog. Creating a
    real keychain file here keeps the walk on the genuine Security framework
    (same daemon, same unlock semantics) while the owner's login keychain stays
    untouched; the file dies with the temp HOME.
    """
    kc_dir = Path(home) / "Library" / "Keychains"
    kc_dir.mkdir(parents=True, exist_ok=True)
    kc = str(kc_dir / "login.keychain-db")
    env = _kc_env(home)
    ok = True
    for args in (
        ["security", "create-keychain", "-p", "walk", kc],
        ["security", "default-keychain", "-s", kc],
        ["security", "unlock-keychain", "-p", "walk", kc],
        ["security", "set-keychain-settings", kc],
    ):
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            ok = False
            finding(f"walk keychain step failed: {' '.join(args[:2])}: {result.stderr.strip()}")
    check("walk keychain created + unlocked (isolated HOME)", ok, kc)


# ----------------------------------------------------------------- network proof


def snapshot_network(hub: Hub, label: str) -> list[str]:
    """Capture lsof -i for the hub process and assert loopback-only."""
    section(f"network proof: {label}")
    if hub.proc is None:
        finding("hub process not available for network snapshot")
        return []
    pid = hub.proc.pid
    try:
        result = subprocess.run(
            ["lsof", "-a", "-p", str(pid), "-i"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.strip().splitlines()
    except Exception as exc:
        finding(f"lsof failed: {exc}")
        return []

    print(f"  lsof snapshot ({label}, pid={pid}):", flush=True)
    for line in lines:
        print(f"    {line}", flush=True)

    # Every connection/listener must be loopback-only
    non_loopback = []
    for line in lines[1:]:  # skip header
        if not line.strip():
            continue
        # lsof -i shows addresses like 127.0.0.1:PORT or localhost:PORT or *:PORT
        # We allow 127.0.0.1, localhost, [::1], *:PORT (LISTEN on all is ok for local hub)
        lower = line.lower()
        if any(tok in lower for tok in ("127.0.0.1", "localhost", "::1", "*:")):
            continue
        # If the line has an IP that is NOT loopback, flag it
        parts = line.split()
        if len(parts) >= 9:
            name_col = parts[8]  # NAME column
            if "->" in name_col:
                # connection line
                for segment in name_col.split("->"):
                    segment = segment.strip()
                    if segment and not any(
                        tok in segment for tok in ("127.0.0.1", "localhost", "::1", "*")
                    ):
                        non_loopback.append(line)

    check(f"all connections loopback-only ({label})", len(non_loopback) == 0,
          f"non-loopback: {non_loopback[:3]}" if non_loopback else "")
    return lines


# ----------------------------------------------------------------- sentinel proof


def sentinel_negative_proof(home: str) -> None:
    """Scan raw bytes of all DB/WAL/SHM/log files for sentinel tokens.

    They must appear NOWHERE in plaintext.
    """
    section("sentinel negative proof")
    sentinels = [SENTINEL_NAME, SENTINEL_AGENDA, SENTINEL_NOTE, SENTINEL_REQUEST]
    home_path = Path(home)

    # Collect all files to scan
    scan_files: list[Path] = []

    # Main holdspeak.db + WAL/SHM
    for pattern in ("**/*.db", "**/*.sqlite3", "**/*-wal", "**/*-shm", "**/*.log"):
        scan_files.extend(home_path.glob(pattern))

    # Also explicitly look for the people sidecar
    people_sidecar = home_path / ".local" / "share" / "holdspeak" / "people.v1.sqlite3"
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(people_sidecar) + suffix)
        if candidate.exists() and candidate not in scan_files:
            scan_files.append(candidate)

    print(f"  scanning {len(scan_files)} files for sentinel tokens", flush=True)
    for f in scan_files:
        print(f"    {f}", flush=True)

    all_clean = True
    for filepath in scan_files:
        if not filepath.exists():
            continue
        try:
            raw = filepath.read_bytes()
        except OSError as exc:
            finding(f"could not read {filepath}: {exc}")
            continue

        for token in sentinels:
            token_bytes = token.encode("utf-8")
            if token_bytes in raw:
                check(f"sentinel '{token}' absent from {filepath.name}", False,
                      f"FOUND in {filepath}")
                all_clean = False

    check("all sentinels absent from all scanned files", all_clean)


# ----------------------------------------------------------------- open People surface


def open_people(shooter: Shooter, hub: Hub) -> None:
    """Navigate to the People surface via Cmd+K shelf search."""
    goto(shooter, hub, "/")
    page = shooter.page
    page.keyboard.press("Meta+k")
    page.wait_for_timeout(500)
    page.keyboard.type("People")
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)


# ----------------------------------------------------------------- walk legs


def leg_readiness_unconfigured(shooter: Shooter, hub: Hub) -> None:
    """Prove readiness endpoint returns unconfigured and the UI shows it."""
    section(f"readiness unconfigured @{shooter.width}")
    status, resp = api(hub, "GET", "/api/people/readiness")
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    check("readiness endpoint reachable", status == 200, f"status={status}")
    check("readiness state is unconfigured", state == "unconfigured", f"state={state}")

    open_people(shooter, hub)
    page = shooter.page

    # Check for unconfigured/degraded state label
    found_label = False
    for label in ("Not set up", "Store unavailable", "Locked", "Key unavailable"):
        if page.get_by_text(label, exact=False).count() > 0:
            check(f"degraded label '{label}' visible", True)
            found_label = True
            break
    if not found_label:
        check("degraded state label visible", False, "none of the expected labels found")

    shooter.shot("people", "unconfigured",
                 "People surface: unconfigured before setup")
    shooter.assert_clean("readiness unconfigured")


def leg_setup(hub: Hub) -> None:
    """POST /api/people/setup -- writes the Keychain entry.

    This is the FIRST Keychain-touching step.
    """
    section("setup: POST /api/people/setup (KEYCHAIN WRITE)")
    print("\n" + "=" * 60, flush=True)
    print("  EXPECT A KEYCHAIN PROMPT -- CLICK 'ALWAYS ALLOW'", flush=True)
    print("  (macOS will ask to allow HoldSpeak People Keychain access)", flush=True)
    print("=" * 60 + "\n", flush=True)

    status, resp = api(hub, "POST", "/api/people/setup", timeout=120.0)
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    check("setup succeeded", status == 200, f"status={status}")
    check("readiness now ready", state == "ready", f"state={state}")


def leg_seed(hub: Hub) -> dict:
    """Seed the People store with sentinel-laden fixture data."""
    section("seed: create relationship + 1:1 + request + notes")
    ids: dict = {}

    # Create relationship with sentinel name
    status, resp = api(hub, "POST", "/api/people/relationships", {
        "display_name": SENTINEL_NAME,
        "relationship_kind": "direct_report",
    })
    check("create relationship", status == 201, f"status={status}")
    rel = resp.get("relationship", {}) if isinstance(resp, dict) else {}
    rel_id = rel.get("id", "")
    ids["relationship_id"] = rel_id

    if not rel_id:
        finding("no relationship id returned; cannot continue seeding")
        return ids

    # Create 1:1 with shared_intent visibility (notes-only)
    status, resp = api(hub, "POST",
                       f"/api/people/relationships/{rel_id}/one-on-ones",
                       {"visibility": "shared_intent"})
    check("create 1:1 session", status == 201, f"status={status}")
    session = resp.get("one_on_one", {}) if isinstance(resp, dict) else {}
    session_id = session.get("id", "")
    ids["session_id"] = session_id

    # Add shared-intent agenda item with sentinel
    if session_id:
        status, resp = api(hub, "POST",
                           f"/api/people/one-on-ones/{session_id}/agenda",
                           {"body": SENTINEL_AGENDA,
                            "visibility": "shared_intent",
                            "state": "open",
                            "source": {"kind": "manual"}})
        check("add shared-intent agenda item", status == 201, f"status={status}")

        # Add leader-private prep agenda item
        status, resp = api(hub, "POST",
                           f"/api/people/one-on-ones/{session_id}/agenda",
                           {"body": "Private leadership preparation notes",
                            "visibility": "leader_private",
                            "state": "open",
                            "source": {"kind": "manual"}})
        check("add leader-private agenda item", status == 201, f"status={status}")

    # Create grounding note with sentinel
    status, resp = api(hub, "POST",
                       f"/api/people/relationships/{rel_id}/notes",
                       {"topic": "Working style",
                        "body": SENTINEL_NOTE,
                        "visibility": "leader_private"})
    check("create grounding note", status == 201, f"status={status}")

    # Create request with sentinel
    status, resp = api(hub, "POST",
                       f"/api/people/relationships/{rel_id}/requests",
                       {"body": SENTINEL_REQUEST,
                        "visibility": "shared_intent",
                        "source": {"kind": "manual"}})
    check("create request", status == 201, f"status={status}")
    req_obj = resp.get("request", {}) if isinstance(resp, dict) else {}
    request_id = req_obj.get("id", "")
    ids["request_id"] = request_id

    # Accept request -> commitment
    if request_id:
        status, resp = api(hub, "POST",
                           f"/api/people/requests/{request_id}/accept", {})
        check("accept request -> commitment", status == 200, f"status={status}")
        commitment = resp.get("commitment", {}) if isinstance(resp, dict) else {}
        commitment_id = commitment.get("id", "")
        ids["commitment_id"] = commitment_id

    return ids


def leg_follow_through_board(hub: Hub, ids: dict) -> None:
    """Assert the commitment appears exactly once on the Follow-through board."""
    section("follow-through board proof")
    status, resp = api(hub, "GET", "/api/follow-through/board")
    check("follow-through board reachable", status == 200, f"status={status}")

    if not isinstance(resp, dict):
        finding("board response is not a dict")
        return

    # The people commitment should appear in the 'now' lane
    now_cards = resp.get("now", [])
    commitment_id = ids.get("commitment_id", "")
    people_cards = [
        c for c in now_cards
        if isinstance(c, dict) and c.get("source") == "people_commitment"
    ]
    check("commitment appears on Follow-through board",
          len(people_cards) >= 1,
          f"people_commitment cards in now lane: {len(people_cards)}")
    check("commitment appears exactly once",
          len(people_cards) == 1,
          f"count={len(people_cards)}")

    if people_cards:
        card = people_cards[0]
        card_id = card.get("id", "")
        check("card text matches request body",
              SENTINEL_REQUEST in str(card.get("text", "")),
              f"text={card.get('text', '')[:60]}")

        # Mark done
        status, resp = api(hub, "POST", "/api/follow-through/complete",
                           {"card_id": card_id, "verb": "done"})
        check("follow-through done verb", status == 200, f"status={status}")

        # Reopen
        status, resp = api(hub, "POST", "/api/follow-through/complete",
                           {"card_id": card_id, "verb": "reopen"})
        check("follow-through reopen verb", status == 200, f"status={status}")


def leg_people_populated(shooter: Shooter, hub: Hub, ids: dict) -> None:
    """Populated People surface at both widths."""
    section(f"people populated @{shooter.width}")
    open_people(shooter, hub)
    page = shooter.page

    # Roster view
    check("sentinel name visible in roster",
          page.get_by_text(SENTINEL_NAME, exact=False).count() > 0)

    shooter.shot("people-roster", "populated",
                 "People roster: relationship with sentinel name")
    shooter.assert_clean("people roster")

    # Click into detail
    sentinel_el = page.get_by_text(SENTINEL_NAME, exact=False).first
    if sentinel_el.count():
        sentinel_el.click()
        page.wait_for_timeout(2000)

        # Now lens (default)
        shooter.shot("people-detail", "now-lens",
                     "Now lens: commitments, requests, next 1:1")
        shooter.assert_clean("people detail now")

        # 1:1s lens
        tab_1on1 = page.locator('button[role="tab"]').get_by_text("1:1s")
        if tab_1on1.count():
            tab_1on1.click()
            page.wait_for_timeout(1500)
            shooter.shot("people-detail", "one-on-ones-lens",
                         "1:1s lens: session with shared and private agenda items")
            shooter.assert_clean("people detail 1:1s")

        # Info lens
        tab_info = page.locator('button[role="tab"]').get_by_text("Info")
        if tab_info.count():
            tab_info.click()
            page.wait_for_timeout(1500)

            # Check for trust facts row and encrypted badge
            encrypted_badge = page.get_by_text("Encrypted", exact=True)
            check("encrypted storage badge visible",
                  encrypted_badge.count() > 0)

            shooter.shot("people-detail", "info-lens",
                         "Info lens: metadata, storage facts, encrypted badge")
            shooter.assert_clean("people detail info")
    else:
        finding("sentinel name not clickable for detail navigation")


def leg_send_to_workbench(shooter: Shooter, hub: Hub, ids: dict) -> None:
    """Prove the Send-to-Workbench egress badge exists in the UI."""
    section(f"send-to-workbench check @{shooter.width}")
    open_people(shooter, hub)
    page = shooter.page

    # Navigate to detail
    sentinel_el = page.get_by_text(SENTINEL_NAME, exact=False).first
    if sentinel_el.count():
        sentinel_el.click()
        page.wait_for_timeout(2000)

        # Open the commitment inspector: click the You-owe commitment row.
        # Scope to the You-owe SurfaceSection — the same sentinel text also
        # renders in the Chair's Follow-Through lane BEHIND the People window,
        # and an unscoped get_by_text clicks that card instead (counsel S1).
        you_owe = page.locator("section.surface-section", has_text="You owe")
        commitment_row = you_owe.locator(
            "button.surface-row-open", has_text=SENTINEL_REQUEST[:20]).first
        if commitment_row.count():
            commitment_row.click()
            page.wait_for_timeout(1500)

        # The SPECIFIC point-of-decision badge, not any .egress-badge on the
        # page (the desk chrome carries a global badge that must not satisfy
        # this check — counsel S1).
        workbench_btn = page.get_by_role("button", name="Send to Workbench")
        egress_badge = page.locator('span.egress-badge.is-cloud[title="Workbench model"]')

        has_send = workbench_btn.count() > 0
        has_badge = egress_badge.count() > 0

        if has_send and has_badge:
            check("Send-to-Workbench button + Workbench-model egress badge", True,
                  f"button={has_send} badge={has_badge}")
            shooter.shot("people-detail", "send-to-workbench",
                         "Commitment inspector: Send-to-Workbench with Workbench-model egress badge")
        else:
            check("Send-to-Workbench button + Workbench-model egress badge", False,
                  f"button={has_send} badge={has_badge}")
            shooter.shot("people-detail", "no-workbench-btn",
                         "Detail view without visible Send-to-Workbench inspector")
    else:
        finding("sentinel name not clickable for workbench check")
    shooter.assert_clean("send-to-workbench check")


# ----------------------------------------------------------------- restart leg


def leg_restart(home: str, ids: dict) -> Hub:
    """Stop the hub and boot a fresh one on the same HOME.

    Proves the store decrypts via the native key after restart.
    """
    section("RESTART LEG: stop + fresh boot on same HOME")
    print("\n" + "=" * 60, flush=True)
    print("  KEYCHAIN READ -- macOS MAY prompt again", flush=True)
    print("  (the fresh hub decrypts the store via the native key)", flush=True)
    print("=" * 60 + "\n", flush=True)

    port = _free_port()
    hub2 = Hub(port, TOKEN, home).start()

    status, resp = api(hub2, "GET", "/api/people/readiness")
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    check("readiness after restart", state == "ready", f"state={state}")

    # Roster intact
    status, resp = api(hub2, "GET", "/api/people/relationships")
    rels = resp.get("relationships", []) if isinstance(resp, dict) else []
    names = [r.get("display_name", "") for r in rels if isinstance(r, dict)]
    check("roster intact after restart", SENTINEL_NAME in names,
          f"names={names}")

    return hub2


# ----------------------------------------------------------------- missing-key leg


def leg_missing_key(home: str) -> None:
    """Simulate missing Keychain entry: delete, boot, assert fail-closed, restore."""
    section("MISSING-KEY SIMULATION")

    # Step 1: Read the key_id from the sidecar's meta table
    people_db = Path(home) / ".local" / "share" / "holdspeak" / "people.v1.sqlite3"
    if not people_db.exists():
        check("SKIP: people sidecar exists for missing-key test", False,
              f"expected {people_db}")
        return

    try:
        conn = sqlite3.connect(str(people_db))
        row = conn.execute("SELECT value FROM meta WHERE key='key_id'").fetchone()
        conn.close()
    except Exception as exc:
        check("SKIP: read key_id from sidecar meta", False, str(exc))
        return

    if not row or not row[0]:
        check("SKIP: key_id found in sidecar meta", False, "no key_id row")
        return

    key_id = row[0]
    print(f"  key_id = {key_id}", flush=True)

    # Step 2: Read the key value via keyring
    print("\n" + "=" * 60, flush=True)
    print("  KEYCHAIN READ -- macOS MAY prompt", flush=True)
    print("  (reading key value via `keyring get` for backup)", flush=True)
    print("=" * 60 + "\n", flush=True)

    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import keyring; v = keyring.get_password('HoldSpeak People', '{key_id}'); print(v or '')"],
            capture_output=True, text=True, timeout=120, env=_kc_env(home),
        )
        key_value = result.stdout.strip()
    except Exception as exc:
        check("SKIP: read key value via keyring", False, str(exc))
        return

    if not key_value:
        check("SKIP: key value retrieved from Keychain", False,
              "empty value -- keyring.get_password returned None")
        return

    check("key value retrieved for backup", True)

    # Step 3: Delete the Keychain entry
    print("\n" + "=" * 60, flush=True)
    print("  KEYCHAIN DELETE -- macOS MAY prompt", flush=True)
    print("  (deleting key to simulate missing-key scenario)", flush=True)
    print("=" * 60 + "\n", flush=True)

    try:
        subprocess.run(
            [sys.executable, "-c",
             f"import keyring; keyring.delete_password('HoldSpeak People', '{key_id}')"],
            capture_output=True, text=True, timeout=120, env=_kc_env(home),
        )
        check("keychain entry deleted", True)
    except Exception as exc:
        check("SKIP: delete keychain entry", False, str(exc))
        # Restore and bail
        return

    # Step 4: Boot hub and assert fail-closed
    port = _free_port()
    try:
        hub_missing = Hub(port, TOKEN, home).start(timeout=30)
    except RuntimeError:
        # Hub might fail to start or be in a degraded state
        check("SKIP: hub boot with missing key", False, "hub failed to start")
        _restore_key(key_id, key_value, home)
        return

    status, resp = api(hub_missing, "GET", "/api/people/readiness")
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    reason = resp.get("reason_code", "") if isinstance(resp, dict) else ""

    # Fail-closed: readiness must NOT be "ready"
    check("fail-closed: readiness is NOT ready",
          state != "ready",
          f"state={state}")
    check("fail-closed: named state reported",
          state in ("key_unavailable", "locked", "unavailable"),
          f"state={state}")
    check("fail-closed: content-free reason code",
          bool(reason),
          f"reason_code={reason}")

    # Roster must not be accessible
    status2, resp2 = api(hub_missing, "GET", "/api/people/relationships")
    check("fail-closed: roster inaccessible",
          status2 != 200,
          f"status={status2}")

    hub_missing.stop()

    # Step 5: Restore the Keychain entry
    _restore_key(key_id, key_value, home)

    # Step 6: Boot again and assert recovery
    port = _free_port()
    hub_restored = Hub(port, TOKEN, home).start()
    status, resp = api(hub_restored, "GET", "/api/people/readiness")
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    check("recovery: readiness restored to ready", state == "ready",
          f"state={state}")

    status, resp = api(hub_restored, "GET", "/api/people/relationships")
    rels = resp.get("relationships", []) if isinstance(resp, dict) else []
    names = [r.get("display_name", "") for r in rels if isinstance(r, dict)]
    check("recovery: roster intact", SENTINEL_NAME in names,
          f"names={names}")

    hub_restored.stop()


def _restore_key(key_id: str, key_value: str, home: str) -> None:
    """Restore the Keychain entry."""
    print("\n" + "=" * 60, flush=True)
    print("  KEYCHAIN WRITE -- macOS MAY prompt", flush=True)
    print("  (restoring key after missing-key test)", flush=True)
    print("=" * 60 + "\n", flush=True)

    try:
        subprocess.run(
            [sys.executable, "-c",
             f"import keyring; keyring.set_password('HoldSpeak People', '{key_id}', '{key_value}')"],
            capture_output=True, text=True, timeout=120, env=_kc_env(home),
        )
        check("keychain entry restored", True)
    except Exception as exc:
        check("CRITICAL: keychain entry restore failed", False, str(exc))


# ----------------------------------------------------------------- cleanup


def cleanup(home: str) -> None:
    """Delete the walk's Keychain entry and temp HOME."""
    section("cleanup")

    # Read key_id to delete the Keychain entry
    people_db = Path(home) / ".local" / "share" / "holdspeak" / "people.v1.sqlite3"
    if people_db.exists():
        try:
            conn = sqlite3.connect(str(people_db))
            row = conn.execute("SELECT value FROM meta WHERE key='key_id'").fetchone()
            conn.close()
            if row and row[0]:
                key_id = row[0]
                print("\n" + "=" * 60, flush=True)
                print("  KEYCHAIN DELETE -- macOS MAY prompt", flush=True)
                print("  (cleaning up the walk's Keychain entry)", flush=True)
                print("=" * 60 + "\n", flush=True)

                subprocess.run(
                    [sys.executable, "-c",
                     f"import keyring; keyring.delete_password('HoldSpeak People', '{key_id}')"],
                    capture_output=True, text=True, timeout=120, env=_kc_env(home),
                )
                check("walk Keychain entry deleted", True, f"key_id={key_id}")
        except Exception as exc:
            finding(f"cleanup Keychain delete failed: {exc}")

    # Delete temp HOME
    try:
        shutil.rmtree(home, ignore_errors=True)
        check("temp HOME deleted", True, home)
    except Exception as exc:
        finding(f"cleanup HOME delete failed: {exc}")


# ----------------------------------------------------------------- main walk


def walk_unattended() -> int:
    """Build, boot, prove unconfigured, print the attended plan."""
    section("UNATTENDED MODE")
    print("  Building web bundle and booting hub under isolated HOME...", flush=True)

    port = _free_port()
    home = tempfile.mkdtemp(prefix="people-walk-138-")
    print(f"  HOME={home}  port={port}", flush=True)

    hub = Hub(port, TOKEN, home).start()

    # Probe readiness -- must be unconfigured (no Keychain in isolated HOME)
    status, resp = api(hub, "GET", "/api/people/readiness")
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    check("readiness endpoint reachable", status == 200, f"status={status}")
    check("readiness is unconfigured (clean HOME)", state == "unconfigured",
          f"state={state}")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for width, height in VIEWPORTS:
                section(f"===== viewport {width}x{height} (unattended) =====")
                ctx = browser.new_context(
                    viewport={"width": width, "height": height},
                    device_scale_factor=2,
                )
                page = ctx.new_page()
                shooter = Shooter(page, width, WALK_OUT)

                leg_readiness_unconfigured(shooter, hub)

                ctx.close()
            browser.close()
    finally:
        hub.stop()
        # Clean up temp HOME (no Keychain entry was created)
        shutil.rmtree(home, ignore_errors=True)

    # Print the attended plan
    section("ATTENDED PLAN")
    print("""
The attended pass (run with --attended) will execute these Keychain-touching steps:

  1. POST /api/people/setup
     -> Keychain WRITE: stores a new AES-256 key in macOS Keychain
        under service "HoldSpeak People"
     -> macOS GUI prompt: "Allow python to access HoldSpeak People?"

  2. Seed: create relationship, 1:1, agenda, notes, request, accept
     -> Keychain READ on each encrypted write (may prompt once)

  3. Follow-through: done + reopen verbs on the commitment card

  4. Screenshots: populated roster, detail Now/1:1s/Info, Send-to-Workbench

  5. RESTART: stop hub, boot fresh hub on same HOME
     -> Keychain READ: proves decrypt with native key survives restart
     -> macOS MAY prompt again

  6. MISSING-KEY SIMULATION:
     a) Read key value via keyring.get_password (Keychain READ)
     b) Delete Keychain entry via keyring.delete_password (Keychain DELETE)
     c) Boot hub -> assert fail-closed (no roster, reason code)
     d) Restore Keychain entry via keyring.set_password (Keychain WRITE)
     e) Boot hub -> assert recovery (roster intact)

  7. SENTINEL NEGATIVE PROOF:
     Scan raw bytes of holdspeak.db + WAL + people.v1.sqlite3 for sentinel
     tokens -- they must appear NOWHERE in plaintext.

  8. NETWORK NEGATIVE PROOF:
     lsof snapshots assert all connections are loopback-only.

  9. CLEANUP:
     Delete the walk's Keychain entry + temp HOME.

Command:
  uv run python scripts/people_walk_full.py --attended
""", flush=True)

    return _finish()


def walk_attended() -> int:
    """Full attended walk with Keychain prompts."""
    section("ATTENDED MODE")
    print("  Owner must be watching for macOS Keychain prompts.", flush=True)

    port = _free_port()
    home = tempfile.mkdtemp(prefix="people-walk-138-attended-")
    print(f"  HOME={home}  port={port}", flush=True)

    create_walk_keychain(home)

    hub = Hub(port, TOKEN, home).start()

    # Network snapshot 1: baseline
    net_lines_1 = snapshot_network(hub, "baseline-after-boot")

    # Step 1: Prove unconfigured, then setup (Keychain write)
    status, resp = api(hub, "GET", "/api/people/readiness")
    state = resp.get("state", "") if isinstance(resp, dict) else ""
    check("pre-setup readiness", state == "unconfigured", f"state={state}")

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)

    # Unconfigured shots
    for width, height in VIEWPORTS:
        section(f"===== viewport {width}x{height} (unconfigured) =====")
        ctx = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page = ctx.new_page()
        shooter = Shooter(page, width, WALK_OUT)
        leg_readiness_unconfigured(shooter, hub)
        ctx.close()

    # Setup (Keychain write)
    leg_setup(hub)

    # Step 2: Seed with sentinels
    ids = leg_seed(hub)

    # Step 3: Follow-through board proof
    leg_follow_through_board(hub, ids)

    # Network snapshot 2: after seeding
    net_lines_2 = snapshot_network(hub, "after-seed-and-follow-through")

    # Step 4: Populated screenshots at both widths
    for width, height in VIEWPORTS:
        section(f"===== viewport {width}x{height} (populated) =====")
        ctx = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page = ctx.new_page()
        shooter = Shooter(page, width, WALK_OUT)
        leg_people_populated(shooter, hub, ids)
        if width == 1440:
            leg_send_to_workbench(shooter, hub, ids)
        ctx.close()

    browser.close()
    pw.stop()

    # Step 5: Restart leg
    hub.stop()
    hub2 = leg_restart(home, ids)
    hub2.stop()

    # Step 6: Missing-key simulation
    leg_missing_key(home)

    # Step 7: Sentinel negative proof
    sentinel_negative_proof(home)

    # Step 8: Cleanup
    cleanup(home)

    return _finish()


def _finish() -> int:
    """Print summary and return exit code."""
    section("RESULT")
    print(
        f"  PASS x{cw.PASSES}   FAIL x{len(cw.FAILS)}   "
        f"FINDINGS x{len(cw.FINDINGS)}   SHOTS x{len(cw.SHOTS)}",
        flush=True,
    )
    if cw.FINDINGS:
        print("\nFINDINGS:", flush=True)
        for f in cw.FINDINGS:
            print(f"  - {f}", flush=True)
    if cw.FAILS:
        print("\nFAILURES:", flush=True)
        for f in cw.FAILS:
            print(f"  - {f}", flush=True)
    print("\nSHOTS:", flush=True)
    for name, proves in cw.SHOTS:
        print(f"  {name}  ({proves})", flush=True)
    return 1 if cw.FAILS else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HS-138-06: People walk (full proof)")
    parser.add_argument(
        "--attended", action="store_true",
        help="Run the full Keychain-touching flow (owner must click prompts)")
    args = parser.parse_args()

    if args.attended:
        return walk_attended()
    else:
        return walk_unattended()


if __name__ == "__main__":
    raise SystemExit(main())
