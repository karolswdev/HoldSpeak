"""HS-174-11 walk runner: Reach -- the remote transport, credentials,
Rhythm host, the Door's third connector, and the shade receipts.

Shoots six faces (Settings System, shade receipts, Rhythm, and the Door)
at 1440x900 and 393x852.  ONE reversible write behind a fail-closed
guard -- the credential probe (story 03).

THE LIVE LAWS (Article IV -- one guarded write):
1. READ-ONLY by default.  The ONLY permitted write is issuing one probe
   credential named ``walk-174-probe`` with palette PROJECT and TTL 12 H
   via POST /api/settings/remote/credentials, ONLY when the remote
   listener is already ON and ONLY if no credential of that name exists.
   The probe is revoked (DELETE) before the walk ends.  Both receipts
   are recorded.
2. The walk NEVER turns Streamable HTTP on, never changes ``Runs on``,
   never runs the steward, never connects Confluence, never presses
   Run now, never Publishes.
3. If the listener is OFF (the expected default), the walk records
   ``REMOTE OFF`` and skips the credential probe -- zero writes.
4. NO HARDCODED TOKENS.
5. FACE-DRIVEN.
6. STANDALONE.  Not collected by pytest.

Usage:
  python tests/e2e/live174_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

# -- pytest collection guard --
collect_ignore_glob = ["live174_walk.py"]


# ---------------------------------------------------------------------------
# Write guard (fail-closed: one named credential probe is the ONLY write)
# ---------------------------------------------------------------------------

PROBE_NAME = "walk-174-probe"
PROBE_PALETTE = "PROJECT"
PROBE_TTL = 43_200.0  # 12 H


def _write_allowed(
    operation: str | None,
    context: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Decide whether a write operation is allowed in this walk.

    Returns (allowed: bool, reason: str).

    Decision table:
        _write_allowed("issue_credential", {"remote_on": True,  "probe_exists": False})
            -> (True,  "credential probe: remote ON, no existing probe")
        _write_allowed("issue_credential", {"remote_on": True,  "probe_exists": True})
            -> (False, "credential probe: probe already exists")
        _write_allowed("issue_credential", {"remote_on": False, "probe_exists": False})
            -> (False, "credential probe: remote OFF")
        _write_allowed("issue_credential", {"remote_on": False, "probe_exists": True})
            -> (False, "credential probe: remote OFF")
        _write_allowed("revoke_credential", {"issued_by_walk": True})
            -> (True,  "revoking walk-issued probe")
        _write_allowed("revoke_credential", {"issued_by_walk": False})
            -> (False, "will not revoke a credential the walk did not issue")
        _write_allowed("revoke_credential", {})
            -> (False, "will not revoke a credential the walk did not issue")
        _write_allowed("enable_remote")     -> (False, "never turns remote on")
        _write_allowed("disable_remote")    -> (False, "never turns remote off")
        _write_allowed("change_runs_on")    -> (False, "never changes Runs on")
        _write_allowed("run_steward")       -> (False, "never runs the steward")
        _write_allowed("connect_confluence")-> (False, "never connects Confluence")
        _write_allowed("run_now")           -> (False, "never presses Run now")
        _write_allowed("publish")           -> (False, "never publishes")
        _write_allowed("unknown")           -> (False, "unknown operation denied by default")
        _write_allowed("")                  -> (False, "empty operation denied")
        _write_allowed(None)                -> (False, "null operation denied")
    """
    if not operation:
        return False, "empty operation denied" if operation == "" else "null operation denied"

    ctx = context or {}

    if operation == "issue_credential":
        remote_on = ctx.get("remote_on", False)
        probe_exists = ctx.get("probe_exists", False)
        if not remote_on:
            return False, "credential probe: remote OFF"
        if probe_exists:
            return False, "credential probe: probe already exists"
        return True, "credential probe: remote ON, no existing probe"

    if operation == "revoke_credential":
        if ctx.get("issued_by_walk", False):
            return True, "revoking walk-issued probe"
        return False, "will not revoke a credential the walk did not issue"

    _DENIALS: dict[str, str] = {
        "enable_remote": "never turns remote on",
        "disable_remote": "never turns remote off",
        "change_runs_on": "never changes Runs on",
        "run_steward": "never runs the steward",
        "connect_confluence": "never connects Confluence",
        "run_now": "never presses Run now",
        "publish": "never publishes",
    }
    reason = _DENIALS.get(operation, "unknown operation denied by default")
    return False, reason


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-174-reach/assets/story-11-shots"

VIEWPORTS = [
    {"width": 1440, "height": 900, "suffix": "1440"},
    {"width": 393, "height": 852, "suffix": "393"},
]


# -- Data model --

@dataclass
class FaceFact:
    face: str
    field: str
    expected: str
    observed: str
    verdict: str
    why: str


@dataclass
class WalkReport:
    generated_at: str = ""
    hub_host: str = ""
    viewports: list[dict] = field(default_factory=list)
    shots: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)
    write_receipts: list[dict] = field(default_factory=list)


# -- Helpers --

def _settle(page: Any) -> None:
    page.evaluate("""() => {
        const anims = document.getAnimations();
        if (anims.length === 0) return;
        return Promise.race([
            Promise.all(anims.map(a => a.finished.catch(() => null))),
            new Promise(r => setTimeout(r, 2000)),
        ]);
    }""")
    page.wait_for_timeout(200)


def _shoot(page: Any, out_dir: Path, name: str, w: int,
           window: bool = False) -> Path:
    _settle(page)
    fname = f"{name}-{w}.png"
    path = out_dir / fname
    path.parent.mkdir(parents=True, exist_ok=True)
    if window:
        win_el = page.locator('.desk-surface-window').last
        if win_el.count() > 0 and win_el.is_visible():
            win_el.screenshot(path=str(path))
        else:
            page.screenshot(path=str(path), full_page=False)
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.exists() and path.stat().st_size > 1_000, f"Shot {fname} missing or too small"
    return path


def _check_overflow(page: Any, w: int, face_name: str) -> str | None:
    result = page.evaluate("""() => {
        const sw = document.documentElement.scrollWidth;
        const cw = document.documentElement.clientWidth;
        return { scrollWidth: sw, clientWidth: cw };
    }""")
    if result["scrollWidth"] > result["clientWidth"]:
        return (f"OVERFLOW on {face_name} at {w}: "
                f"scrollWidth={result['scrollWidth']} > clientWidth={result['clientWidth']}")
    return None


_FETCH_JS = """async ([method, path, body, token]) => {
  const response = await fetch(path, {
    method,
    headers: {
      authorization: `Bearer ${token}`,
      ...(body ? {"content-type": "application/json"} : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("json")
    ? await response.json()
    : await response.text();
  return {status: response.status, payload};
}"""


def _api(page: Any, method: str, path: str,
         body: dict[str, Any] | None, token: str) -> dict[str, Any]:
    return page.evaluate(_FETCH_JS, [method, path, body, token])


def _fact(face: str, fld: str, expected: str, observed: str) -> FaceFact:
    if not observed or observed == "---":
        return FaceFact(face=face, field=fld, expected=expected,
                        observed=observed, verdict="DATA", why="no data observed")
    exp_l = expected.lower().strip()
    obs_l = observed.lower().strip()
    if exp_l == obs_l:
        v, w = "MATCH", "exact"
    elif exp_l in obs_l or obs_l in exp_l:
        v, w = "MATCH", "substring"
    else:
        v, w = "DATA", f"board={expected}, real={observed}"
    return FaceFact(face=face, field=fld, expected=expected,
                    observed=observed, verdict=v, why=w)


def _open_surface(page: Any, token: str, action: str, scope: str | None = None) -> None:
    payload: dict[str, str] = {"key": action}
    if scope:
        payload["scope"] = scope
    page.evaluate(f"""() => {{
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({json.dumps(payload)})
        );
    }}""")
    page.reload(wait_until="load")
    page.wait_for_timeout(500)
    try:
        chair = page.locator(".chair")
        if chair.count() > 0:
            chair.wait_for(timeout=2000)
            if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                btn = page.get_by_role("button", name="Continue later", exact=True)
                if btn.count() > 0:
                    btn.click()
    except Exception:
        pass
    page.wait_for_timeout(1500)
    _settle(page)


def _close_surface(page: Any) -> None:
    close_btn = page.locator('.desk-surface-window .desk-light-close').last
    if close_btn.count() > 0 and close_btn.is_visible():
        close_btn.click()
        page.wait_for_timeout(500)
        _settle(page)


# ---------------------------------------------------------------------------
# Step 1: read remote and hub settings via the API
# ---------------------------------------------------------------------------

def _step_remote_api(page: Any, token: str, report: WalkReport) -> dict:
    """Read GET /api/settings/remote and GET /api/settings/hub.

    Returns a dict with:
      remote_on        -- bool: is Streamable HTTP enabled?
      bind_host        -- the bind address (or None)
      credentials      -- list of credential dicts
      active_count     -- int: active (non-expired) credential count
      total_count      -- int: total credential count
      probe_exists     -- bool: does a credential named PROBE_NAME exist?
    """
    face = "remote-api"
    out: dict[str, Any] = {}

    # GET /api/settings/remote
    remote = _api(page, "GET", "/api/settings/remote", None, token)
    if remote["status"] >= 300:
        report.errors.append(f"GET /api/settings/remote returned {remote['status']}")
        out["remote_on"] = False
        return out

    rp = remote["payload"]
    remote_on = bool(rp.get("enabled", False))
    bind_host = rp.get("bind_host")
    credentials = rp.get("credentials", [])
    active_count = rp.get("active_count", 0)
    total_count = rp.get("total_count", 0)

    out["remote_on"] = remote_on
    out["bind_host"] = bind_host
    out["credentials"] = credentials
    out["active_count"] = active_count
    out["total_count"] = total_count

    # Check whether the probe already exists.
    probe_exists = any(
        c.get("identity") == PROBE_NAME for c in credentials
    )
    out["probe_exists"] = probe_exists

    report.facts.append(asdict(FaceFact(
        face=face, field="remote_enabled",
        expected="(OFF is the expected default)",
        observed="ON" if remote_on else "OFF",
        verdict="DATA", why="Streamable HTTP transport state",
    )))
    if bind_host:
        report.facts.append(asdict(FaceFact(
            face=face, field="bind_host",
            expected="(tailnet address)",
            observed=str(bind_host)[:30],
            verdict="DATA", why="remote bind address",
        )))
    report.facts.append(asdict(FaceFact(
        face=face, field="active_count",
        expected="(varies)",
        observed=str(active_count),
        verdict="DATA", why="active credential count",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="total_count",
        expected="(varies)",
        observed=str(total_count),
        verdict="DATA", why="total credential count",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="probe_exists",
        expected="false",
        observed=str(probe_exists),
        verdict="MATCH" if not probe_exists else "DATA",
        why="walk-174-probe credential pre-existing check",
    )))

    # GET /api/settings/hub (the seven module rows)
    hub = _api(page, "GET", "/api/settings/hub", None, token)
    if hub["status"] == 200:
        hp = hub["payload"]
        system = hp.get("system", {}) if isinstance(hp, dict) else {}
        report.facts.append(asdict(FaceFact(
            face=face, field="hub_host",
            expected="(THIS DEVICE or hostname)",
            observed=str(system.get("host", "---"))[:30],
            verdict="DATA", why="hub host identity",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="hub_mesh",
            expected="(bool)",
            observed="MESH ON" if system.get("mesh") else "MESH OFF",
            verdict="DATA", why="mesh state from hub",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="hub_api_status",
            expected="200", observed=str(hub["status"]),
            verdict="DATA", why=f"GET /api/settings/hub returned HTTP {hub['status']}",
        )))

    return out


# ---------------------------------------------------------------------------
# Step 2: open Settings -> System, shoot the remote transport face
# ---------------------------------------------------------------------------

def _step_settings_system(page: Any, out_dir: Path, w: int, token: str,
                          report: WalkReport, remote_state: dict) -> None:
    """Open Settings -> System at the given width, shoot walk-remote-{w}.png.

    Records the hub row's REMOTE cell, the Streamable HTTP row state,
    the credentials ledger (counts only), whether ``Issue credential``
    is absent when OFF.
    """
    face = "settings-system"
    remote_on = remote_state.get("remote_on", False)

    # Open Settings, then navigate to the System module.
    _open_surface(page, token, "open-settings", "system")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-remote", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the System module face.
    # TODO selectors: the face lanes are building now. Named for D2
    # elements; the real data-testid values will be filled when the
    # Settings System module remote section lands.
    #
    # Expected selectors (from D2(a)):
    #   [data-testid="system-remote-toggle"]   -- CycleGadget OFF/ON
    #   [data-testid="system-remote-address"]   -- muted token with bind address
    #   [data-testid="system-remote-cred-count"] -- N CREDENTIALS token
    #   [data-testid="system-credential-row"]   -- each credential row
    #   [data-testid="system-issue-credential"] -- Issue credential button
    #   [data-testid="system-revoke-credential"] -- Revoke button per row
    system_data = page.evaluate("""([remoteOn]) => {
        const body = document.querySelector('.desk-surface-body') ||
                     document.querySelector('[data-testid="room-body"]') ||
                     document.body;
        const bodyText = body.textContent || '';

        /* Hub row REMOTE cell: look for REMOTE OFF or REMOTE ON tokens */
        const hubRow = body.querySelector('.surface-token[data-chip]');
        const allTokens = body.querySelectorAll('.surface-token[data-chip]');
        let remoteCell = '---';
        for (const tok of allTokens) {
            const t = tok.textContent.trim();
            if (/^REMOTE\\s+(ON|OFF)$/i.test(t)) {
                remoteCell = t;
                break;
            }
        }

        /* Streamable HTTP row: TODO selector [data-testid="system-remote-toggle"] */
        const toggleEl = body.querySelector('[data-testid="system-remote-toggle"]');
        const toggleState = toggleEl
            ? toggleEl.textContent.trim()
            : (bodyText.includes('Streamable HTTP')
                ? (bodyText.includes('ON') ? 'ON (inferred)' : 'OFF (inferred)')
                : '--- (face not landed)');

        /* Credentials count: TODO selector [data-testid="system-remote-cred-count"] */
        let credCountToken = '---';
        for (const tok of allTokens) {
            const t = tok.textContent.trim();
            if (/\\d+\\s+CREDENTIALS/i.test(t)) {
                credCountToken = t;
                break;
            }
        }
        let activeCountToken = '---';
        for (const tok of allTokens) {
            const t = tok.textContent.trim();
            if (/\\d+\\s+ACTIVE/i.test(t)) {
                activeCountToken = t;
                break;
            }
        }

        /* Issue credential button: TODO selector [data-testid="system-issue-credential"] */
        const issueBtn = body.querySelector('[data-testid="system-issue-credential"]');
        const issueBtnByText = !issueBtn
            ? (() => {
                const btns = body.querySelectorAll('button');
                for (const b of btns) {
                    if (/issue credential/i.test(b.textContent)) return b;
                }
                return null;
            })()
            : null;
        const issuePresent = Boolean(issueBtn || issueBtnByText);

        /* Credential rows: TODO selector [data-testid="system-credential-row"] */
        const credRows = body.querySelectorAll('[data-testid="system-credential-row"]');
        const credRowCount = credRows.length;

        /* Defect scans */
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(CREDENTIAL|ACTIVE|REMOTE)/g;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const hasLocal = bodyText.includes('LOCAL');

        const clippedTexts = [];
        const primEls = body.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"]'
        );
        for (const el of primEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            remoteCell, toggleState, credCountToken, activeCountToken,
            issuePresent, credRowCount,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""", [remote_on])

    # Record facts.
    report.facts.append(asdict(FaceFact(
        face=face, field="hub_row_remote_cell",
        expected="REMOTE OFF" if not remote_on else "REMOTE ON",
        observed=system_data.get("remoteCell", "---"),
        verdict="DATA", why="REMOTE cell on the hub row",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="streamable_http_state",
        expected="OFF" if not remote_on else "ON",
        observed=system_data.get("toggleState", "---"),
        verdict="DATA", why="Streamable HTTP toggle row",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="credential_count_token",
        expected="(absent at zero, N CREDENTIALS when >0)",
        observed=system_data.get("credCountToken", "---"),
        verdict="DATA", why="credentials count token",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="active_count_token",
        expected="(absent at zero, N ACTIVE when >0)",
        observed=system_data.get("activeCountToken", "---"),
        verdict="DATA", why="active credentials count",
    )))

    # Issue credential absent when OFF.
    if not remote_on:
        report.facts.append(asdict(FaceFact(
            face=face, field="issue_credential_absent_when_off",
            expected="true (absent when OFF)",
            observed=str(not system_data.get("issuePresent", False)),
            verdict=(
                "MATCH"
                if not system_data.get("issuePresent", False)
                else "DATA"
            ),
            why="Issue credential button should be absent when remote is OFF",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="issue_credential_present_when_on",
            expected="true",
            observed=str(system_data.get("issuePresent", False)),
            verdict=(
                "MATCH"
                if system_data.get("issuePresent", False)
                else "DATA"
            ),
            why="Issue credential button should be present when remote is ON",
        )))

    # Defects.
    for z in system_data.get("zeroCounters", []):
        report.defects.append(
            f"SETTINGS SYSTEM: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if system_data.get("hasLocal"):
        report.defects.append(
            "SETTINGS SYSTEM: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if system_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"SETTINGS SYSTEM: {system_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in system_data.get("clippedTexts", []):
        report.defects.append(f"SETTINGS SYSTEM: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 3: credential probe (guarded write)
# ---------------------------------------------------------------------------

def _step_credential_probe(page: Any, token: str, report: WalkReport,
                           remote_state: dict) -> None:
    """If remote is ON and no probe exists: issue, verify, revoke.

    This is the walk's ONLY write, fail-closed behind _write_allowed.
    If remote is OFF, records REMOTE OFF and skips (zero writes).
    """
    face = "credential-probe"
    remote_on = remote_state.get("remote_on", False)
    probe_exists = remote_state.get("probe_exists", False)

    # Check the guard.
    allowed, reason = _write_allowed(
        "issue_credential",
        {"remote_on": remote_on, "probe_exists": probe_exists},
    )

    if not allowed:
        report.facts.append(asdict(FaceFact(
            face=face, field="probe_skipped",
            expected="(skip when remote OFF or probe exists)",
            observed=reason,
            verdict="DATA", why="write guard denied the credential probe",
        )))
        if not remote_on:
            report.facts.append(asdict(FaceFact(
                face=face, field="remote_state",
                expected="OFF (expected default)",
                observed="REMOTE OFF",
                verdict="MATCH", why="remote listener is OFF; zero writes is the expected outcome",
            )))
        return

    # Issue the probe credential.
    issue_result = _api(page, "POST", "/api/settings/remote/credentials", {
        "identity": PROBE_NAME,
        "palette": PROBE_PALETTE,
        "ttl_seconds": PROBE_TTL,
    }, token)

    if issue_result["status"] >= 300:
        report.errors.append(
            f"POST /api/settings/remote/credentials returned "
            f"{issue_result['status']}: {issue_result.get('payload', '')}"
        )
        return

    issued = issue_result["payload"]
    cred_id = issued.get("id", "")
    cred_identity = issued.get("identity", "")
    # The token is shown once; we record that it was returned but NEVER
    # write the plaintext to any file (the report records a boolean).
    token_returned = bool(issued.get("token"))

    report.write_receipts.append({
        "operation": "issue_credential",
        "identity": cred_identity,
        "id": cred_id[:12],
        "palette": issued.get("palette"),
        "token_returned": token_returned,
        "status": issue_result["status"],
    })
    report.facts.append(asdict(FaceFact(
        face=face, field="probe_issued",
        expected="true",
        observed=f"id={cred_id[:12]}, identity={cred_identity}, token_returned={token_returned}",
        verdict="MATCH" if token_returned and cred_identity == PROBE_NAME else "DATA",
        why="credential probe issued",
    )))

    # Verify active_count moved by one.
    verify = _api(page, "GET", "/api/settings/remote", None, token)
    if verify["status"] == 200:
        new_active = verify["payload"].get("active_count", 0)
        old_active = remote_state.get("active_count", 0)
        report.facts.append(asdict(FaceFact(
            face=face, field="active_count_after_issue",
            expected=str(old_active + 1),
            observed=str(new_active),
            verdict="MATCH" if new_active == old_active + 1 else "DATA",
            why="active credential count should increase by one",
        )))

    # Revoke the probe.
    revoke_allowed, revoke_reason = _write_allowed(
        "revoke_credential", {"issued_by_walk": True},
    )
    if not revoke_allowed:
        report.errors.append(f"write guard refused revoke: {revoke_reason}")
        return

    if cred_id:
        revoke_result = _api(
            page, "DELETE",
            f"/api/settings/remote/credentials/{cred_id}",
            None, token,
        )
        report.write_receipts.append({
            "operation": "revoke_credential",
            "id": cred_id[:12],
            "status": revoke_result["status"],
            "success": revoke_result["status"] == 200,
        })
        report.facts.append(asdict(FaceFact(
            face=face, field="probe_revoked",
            expected="true (HTTP 200)",
            observed=f"status={revoke_result['status']}",
            verdict="MATCH" if revoke_result["status"] == 200 else "DATA",
            why="credential probe revoked",
        )))

        # Verify active_count returned to baseline.
        verify2 = _api(page, "GET", "/api/settings/remote", None, token)
        if verify2["status"] == 200:
            final_active = verify2["payload"].get("active_count", 0)
            old_active = remote_state.get("active_count", 0)
            report.facts.append(asdict(FaceFact(
                face=face, field="active_count_after_revoke",
                expected=str(old_active),
                observed=str(final_active),
                verdict="MATCH" if final_active == old_active else "DATA",
                why="active count should return to baseline after revoke",
            )))
    else:
        report.errors.append("credential probe: no id returned; cannot revoke")


# ---------------------------------------------------------------------------
# Step 4: open the shade, shoot receipts
# ---------------------------------------------------------------------------

def _step_shade_receipts(page: Any, out_dir: Path, w: int, token: str,
                         report: WalkReport) -> None:
    """Open the shade, shoot walk-shade-receipts-{w}.png.

    Records whether any FINISHED row carries ``REMOTE . <ip>`` (expected
    none) and that no chip carries a time inside.
    """
    face = "shade-receipts"

    # Click the bell / shade toggle to open the shade.
    bell = page.locator('.desk-bell, [data-testid="desk-bell"]')
    if bell.count() > 0 and bell.is_visible():
        bell.click()
        page.wait_for_timeout(1500)
        _settle(page)
    else:
        # Try the shade class directly.
        page.evaluate("""() => {
            const btn = document.querySelector('.desk-shade-toggle') ||
                        document.querySelector('[aria-label="Missed"]');
            if (btn && btn.click) btn.click();
        }""")
        page.wait_for_timeout(1500)
        _settle(page)

    shot = _shoot(page, out_dir, "walk-shade-receipts", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the shade's Finished rows.
    shade_data = page.evaluate("""() => {
        const shade = document.querySelector('.desk-shade') ||
                      document.querySelector('[role="group"][aria-label="Missed"]');
        if (!shade) return {
            finishedRows: 0, remoteChips: [],
            chipWithTime: false, warningRemoteChip: false,
            tokenStringVisible: false,
        };

        const shadeText = shade.textContent || '';

        /* Finished section: rows after the h4 "Finished" */
        const finishedSection = shade.querySelector('[aria-label="Finished"]') ||
            shade.querySelector('section:last-of-type');
        let finishedRows = 0;
        let remoteChips = [];

        if (finishedSection) {
            const items = finishedSection.querySelectorAll('.desk-shade-item');
            finishedRows = items.length;

            for (const item of items) {
                const text = item.textContent || '';
                /* Look for REMOTE . <ip> pattern */
                const remoteMatch = text.match(/REMOTE\\s*[.\\xb7]\\s*(\\d+\\.\\d+\\.\\d+\\.\\d+)/);
                if (remoteMatch) {
                    remoteChips.push(remoteMatch[0]);
                }
            }
        }

        /* Check if any chip carries a time inside (HH:MM pattern in a chip) */
        const chips = shade.querySelectorAll('.surface-token[data-chip], .gadget-chip-egress');
        let chipWithTime = false;
        for (const chip of chips) {
            const ct = chip.textContent.trim();
            if (/\\d{1,2}:\\d{2}/.test(ct)) {
                chipWithTime = true;
                break;
            }
        }

        /* Check for REMOTE chip in warning tone */
        let warningRemoteChip = false;
        for (const chip of chips) {
            const ct = chip.textContent.trim();
            if (/REMOTE/i.test(ct)) {
                const isWarning = chip.classList.contains('state--warning') ||
                    chip.dataset.tone === 'warning' ||
                    chip.closest('[data-tone="warning"]');
                if (isWarning) warningRemoteChip = true;
            }
        }

        /* Check for a token string visible (a raw credential token leaked) */
        const tokenStringVisible = /[a-f0-9]{32,}/i.test(shadeText);

        return {
            finishedRows, remoteChips,
            chipWithTime, warningRemoteChip, tokenStringVisible,
        };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="finished_rows",
        expected="(varies)",
        observed=str(shade_data.get("finishedRows", 0)),
        verdict="DATA", why="Finished rows in the shade",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="remote_chips_in_finished",
        expected="(none expected -- no overnight run yet)",
        observed=json.dumps(shade_data.get("remoteChips", [])),
        verdict="DATA",
        why="REMOTE . <ip> badges in Finished rows",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="chip_with_time_inside",
        expected="false (no chip should carry a time inside)",
        observed=str(shade_data.get("chipWithTime", False)),
        verdict="MATCH" if not shade_data.get("chipWithTime") else "DATA",
        why="defect check: chip carrying a time",
    )))

    # Defects.
    if shade_data.get("chipWithTime"):
        report.defects.append(
            "SHADE: a chip carries a time inside (the time belongs "
            "outside the chip, in the row)"
        )
    if shade_data.get("warningRemoteChip"):
        report.defects.append(
            "SHADE: REMOTE chip rendered in warning tone "
            "(counsel C6 ruling: accent outline, never warning)"
        )
    if shade_data.get("tokenStringVisible"):
        report.defects.append(
            "SHADE: a raw token string (>=32 hex chars) visible "
            "after reload -- credential leak"
        )

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    # Close the shade.
    page.evaluate("""() => {
        const shade = document.querySelector('.desk-shade');
        if (shade) {
            const close = shade.querySelector('button');
            if (close) close.click();
        }
    }""")
    page.wait_for_timeout(500)
    _settle(page)


# ---------------------------------------------------------------------------
# Step 5: open Rhythm, shoot the Runs on row
# ---------------------------------------------------------------------------

def _step_rhythm(page: Any, out_dir: Path, w: int, token: str,
                 report: WalkReport) -> None:
    """Open Rhythm, shoot walk-rhythm-{w}.png.

    Records the ``Runs on`` value (expected THIS DEVICE), that ``Run now``
    appears once on the page, the caption absent when local.
    """
    face = "rhythm"

    _open_surface(page, token, "configure-cadence")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-rhythm", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read Rhythm face data.
    # TODO selectors: the Runs on row is a D2(d) element being built now.
    # Expected selectors:
    #   [data-testid="rhythm-runs-on"]      -- the Runs on row
    #   [data-testid="rhythm-runs-on-host"] -- the CycleGadget host picker
    #   [data-testid="rhythm-awake-caption"] -- WHILE THIS MAC IS AWAKE caption
    rhythm_data = page.evaluate("""() => {
        const body = document.querySelector('.desk-surface-body') ||
                     document.querySelector('[data-testid="room-body"]') ||
                     document.body;
        const bodyText = body.textContent || '';

        /* Runs on row: TODO [data-testid="rhythm-runs-on"] */
        const runsOnRow = body.querySelector('[data-testid="rhythm-runs-on"]');
        let runsOnValue = '---';
        if (runsOnRow) {
            const cycle = runsOnRow.querySelector('.cycle-gadget');
            runsOnValue = cycle ? cycle.textContent.trim() : runsOnRow.textContent.trim();
        } else {
            /* Fallback: look for "Runs on" text then the adjacent token */
            const match = bodyText.match(/Runs on[\\s\\S]{0,60}?(THIS DEVICE|\\d+\\.\\d+\\.\\d+\\.\\d+)/);
            if (match) runsOnValue = match[1];
            else runsOnValue = '--- (face not landed)';
        }

        /* Run now: count occurrences (expected exactly 1 on the sweep row) */
        const runNowBtns = body.querySelectorAll('[data-testid="rhythm-run-now"]');
        let runNowCount = runNowBtns.length;
        if (runNowCount === 0) {
            /* Fallback: text search */
            const btns = body.querySelectorAll('button');
            for (const b of btns) {
                if (/^Run now$/i.test(b.textContent.trim())) runNowCount++;
            }
        }

        /* WHILE THIS MAC IS AWAKE caption: present only when remote host selected */
        const awakeCaption = body.querySelector('[data-testid="rhythm-awake-caption"]');
        let awakeCaptionPresent = Boolean(awakeCaption);
        if (!awakeCaptionPresent) {
            awakeCaptionPresent = /WHILE THIS MAC IS AWAKE/i.test(bodyText);
        }

        /* Defect scans */
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(SWEEP|ROOM|WATCH|BRIEF)/g;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const hasLocal = bodyText.includes('LOCAL');

        return {
            runsOnValue, runNowCount, awakeCaptionPresent,
            zeroCounters, rawBtnCount, hasLocal,
        };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="runs_on_value",
        expected="THIS DEVICE",
        observed=rhythm_data.get("runsOnValue", "---"),
        verdict=(
            "MATCH"
            if rhythm_data.get("runsOnValue", "").strip().upper() == "THIS DEVICE"
            else "DATA"
        ),
        why="Runs on host (expected THIS DEVICE on the owner's desk)",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="run_now_count",
        expected="1 (once, on the sweep row)",
        observed=str(rhythm_data.get("runNowCount", 0)),
        verdict=(
            "MATCH"
            if rhythm_data.get("runNowCount", 0) == 1
            else "DATA"
        ),
        why="Run now verb count (counsel C3: one verb, once)",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="awake_caption_present",
        expected="false (caption absent when local)",
        observed=str(rhythm_data.get("awakeCaptionPresent", False)),
        verdict=(
            "MATCH"
            if not rhythm_data.get("awakeCaptionPresent")
            else "DATA"
        ),
        why="WHILE THIS MAC IS AWAKE caption (absent when Runs on = THIS DEVICE)",
    )))

    # Defects.
    if rhythm_data.get("runNowCount", 0) > 1:
        report.defects.append(
            f"RHYTHM: Run now appears {rhythm_data['runNowCount']} times "
            f"(counsel C3: one verb, once)"
        )
    for z in rhythm_data.get("zeroCounters", []):
        report.defects.append(
            f"RHYTHM: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if rhythm_data.get("hasLocal"):
        report.defects.append(
            "RHYTHM: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if rhythm_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"RHYTHM: {rhythm_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 6: open the Door (New Project), read-only, then Cancel
# ---------------------------------------------------------------------------

def _step_door(page: Any, out_dir: Path, w: int, token: str,
               report: WalkReport) -> None:
    """Open the Door (New Project) read-only, shoot walk-door-{w}.png.

    Records whether the Confluence row exists and its state (NOT INSTALLED /
    SIGN IN / SIGNED IN AS), that its defaults read RECENT BLOGS / PAGES BY ID,
    then Cancel without creating.
    """
    face = "door"

    _open_surface(page, token, "new-project")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-door", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the Door face data.
    # Selectors from DoorCore.tsx (existing):
    #   [data-testid="door-root"]           -- the door container
    #   [data-testid="door-row-github"]     -- GitHub source row
    #   [data-testid="door-row-jira"]       -- Jira source row
    #   [data-testid="door-row-confluence"] -- Confluence source row (new in 174)
    #   [data-testid="door-cancel"]         -- Cancel button
    #   [data-testid="door-create"]         -- Create button
    door_data = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="door-root"]') ||
                     document.querySelector('.desk-surface-body') ||
                     document.body;
        const bodyText = body.textContent || '';

        /* Confluence row: [data-testid="door-row-confluence"] */
        const confRow = body.querySelector('[data-testid="door-row-confluence"]');
        let confState = 'NOT FOUND';
        let confDefaults = [];

        if (confRow) {
            const confText = confRow.textContent || '';
            /* Connection state: look for StateChip text */
            if (/SIGNED IN AS/i.test(confText)) {
                const match = confText.match(/SIGNED IN AS\\s+(\\S+)/i);
                confState = match ? 'SIGNED IN AS ' + match[1].slice(0, 12) : 'SIGNED IN';
            } else if (/SIGN IN/i.test(confText)) {
                confState = 'SIGN IN';
            } else if (/NOT INSTALLED/i.test(confText)) {
                confState = 'NOT INSTALLED';
            } else {
                confState = confText.slice(0, 60);
            }

            /* Default watch toggles: look for RECENT BLOGS and PAGES BY ID */
            if (/RECENT BLOGS/i.test(confText)) confDefaults.push('RECENT BLOGS');
            if (/PAGES BY ID/i.test(confText)) confDefaults.push('PAGES BY ID');
        } else {
            /* Fallback: look for Confluence text in the body */
            if (/Confluence/i.test(bodyText)) {
                confState = 'PRESENT (no testid)';
                if (/RECENT BLOGS/i.test(bodyText)) confDefaults.push('RECENT BLOGS');
                if (/PAGES BY ID/i.test(bodyText)) confDefaults.push('PAGES BY ID');
            } else {
                confState = 'NOT FOUND (face not landed)';
            }
        }

        /* GitHub and Jira rows for reference */
        const ghRow = body.querySelector('[data-testid="door-row-github"]');
        const jiraRow = body.querySelector('[data-testid="door-row-jira"]');
        const ghPresent = Boolean(ghRow);
        const jiraPresent = Boolean(jiraRow);

        /* Defect scans */
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(SOURCE|WATCH|REPO)/g;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const hasLocal = bodyText.includes('LOCAL');

        const clippedTexts = [];
        const primEls = body.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"], .door-source-primary'
        );
        for (const el of primEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            confState, confDefaults,
            ghPresent, jiraPresent,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="confluence_row_state",
        expected="(NOT INSTALLED / SIGN IN / SIGNED IN AS)",
        observed=door_data.get("confState", "---"),
        verdict="DATA", why="Confluence source row connection state",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="confluence_defaults",
        expected="['RECENT BLOGS', 'PAGES BY ID']",
        observed=json.dumps(door_data.get("confDefaults", [])),
        verdict=(
            "MATCH"
            if door_data.get("confDefaults") == ["RECENT BLOGS", "PAGES BY ID"]
            else "DATA"
        ),
        why="Confluence default watch labels",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="github_row_present",
        expected="true",
        observed=str(door_data.get("ghPresent", False)),
        verdict="MATCH" if door_data.get("ghPresent") else "DATA",
        why="GitHub source row present",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="jira_row_present",
        expected="true",
        observed=str(door_data.get("jiraPresent", False)),
        verdict="MATCH" if door_data.get("jiraPresent") else "DATA",
        why="Jira source row present",
    )))

    # Defects.
    for z in door_data.get("zeroCounters", []):
        report.defects.append(
            f"DOOR: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if door_data.get("hasLocal"):
        report.defects.append(
            "DOOR: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if door_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"DOOR: {door_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in door_data.get("clippedTexts", []):
        report.defects.append(f"DOOR: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    # Cancel without creating.
    cancel_btn = page.locator('[data-testid="door-cancel"]')
    if cancel_btn.count() > 0 and cancel_btn.is_visible():
        cancel_btn.click()
        page.wait_for_timeout(500)
        _settle(page)
    else:
        _close_surface(page)


# ---------------------------------------------------------------------------
# Step 7: cross-step defect detection
# ---------------------------------------------------------------------------

def _detect_defects(report: WalkReport) -> None:
    """Cross-step defect detection applied after all steps complete."""
    seen: set[tuple[str, str]] = set()
    for fact in report.facts:
        key = (fact["face"], fact["field"])
        if key in seen:
            continue
        seen.add(key)
        obs = fact["observed"]

        # D1: zero counter (UX-CANON A.8).
        if re.search(
            r'\b0\s+(CREDENTIAL|ACTIVE|REMOTE|SWEEP|ROOM|WATCH|'
            r'SOURCE|BRIEF|NEED|THINGS)',
            obs,
        ):
            report.defects.append(
                f"ZERO COUNTER on {fact['face']}/{fact['field']}: "
                f'"{obs}" -- UX-CANON A.8 forbids counters of zero'
            )

        # D2: raw <button>.
        if "rawBtnCount" in fact["field"] and obs not in ("0", "---"):
            pass  # already handled per-step

        # D3: LOCAL instead of THIS DEVICE.
        if fact["field"] == "runs_on_value" and obs.strip().upper() == "LOCAL":
            report.defects.append(
                "RHYTHM: Runs on says LOCAL (should be THIS DEVICE)"
            )

        # D4: a chip with a time inside.
        if fact["field"] == "chip_with_time_inside" and obs.lower() == "true":
            pass  # already handled in step 4

        # D5: a REMOTE chip in the warning tone.
        # already handled in step 4

        # D6: a token string visible after reload.
        # already handled in step 4

        # D7: two Run now verbs.
        if fact["field"] == "run_now_count":
            try:
                count = int(obs)
                if count > 1:
                    pass  # already handled in step 5
            except ValueError:
                pass

    report.defects = list(dict.fromkeys(report.defects))


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _write_facts_json(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n")
    return path


def _write_facts_md(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# HS-174-11 walk facts",
        "",
        f"Generated: {report.generated_at}",
        f"Hub: {report.hub_host}",
        "",
    ]
    faces: dict[str, list[dict]] = {}
    for fact in report.facts:
        face_name = fact["face"]
        if face_name not in faces:
            faces[face_name] = []
        faces[face_name].append(fact)

    for face_name, facts in faces.items():
        lines.append(f"## {face_name}")
        lines.append("")
        lines.append("| Field | Expected | Observed | Verdict | Why |")
        lines.append("|-------|----------|----------|---------|-----|")
        for f in facts:
            exp = f["expected"].replace("|", "\\|")
            obs = f["observed"].replace("|", "\\|")
            why = f["why"].replace("|", "\\|")
            lines.append(
                f"| {f['field']} | {exp} | {obs} | {f['verdict']} | {why} |"
            )
        lines.append("")

    if report.shots:
        lines.append("## Shots")
        lines.append("")
        for s in report.shots:
            lines.append(
                f"- {s['face']} @ {s['width']}: `{Path(s['path']).name}`"
            )
        lines.append("")

    if report.write_receipts:
        lines.append("## Write receipts")
        lines.append("")
        for wr in report.write_receipts:
            lines.append(f"- {wr.get('operation')}: {json.dumps(wr)}")
        lines.append("")

    if report.errors:
        lines.append("## Errors")
        lines.append("")
        for e in report.errors:
            lines.append(f"- {e}")
        lines.append("")

    if report.surprises:
        lines.append("## Surprises")
        lines.append("")
        for s in report.surprises:
            lines.append(f"- {s}")
        lines.append("")

    if report.defects:
        lines.append("## Defects")
        lines.append("")
        for i, d in enumerate(report.defects, 1):
            lines.append(f"{i}. {d}")
        lines.append("")
    else:
        lines.append("## Defects")
        lines.append("")
        lines.append("None.")
        lines.append("")

    path.write_text("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="HS-174-11 walk runner")
    parser.add_argument("--hub", required=True, help="Hub URL with token")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Output directory for shots and facts")
    args = parser.parse_args()

    parsed = urlparse(args.hub)
    qs = parse_qs(parsed.query)
    tok = qs.get("token", [""])[0]
    if not tok:
        print("ERROR: --hub URL must include ?token=...")
        return 1
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = WalkReport(
        generated_at=datetime.now().isoformat(),
        hub_host=parsed.netloc,
        viewports=[{"width": v["width"], "height": v["height"]}
                   for v in VIEWPORTS],
    )
    errors_fatal: list[str] = []

    # Print the write guard's decision table.
    print("=== WRITE GUARD DECISION TABLE ===")
    for op, ctx in [
        ("issue_credential", {"remote_on": True, "probe_exists": False}),
        ("issue_credential", {"remote_on": True, "probe_exists": True}),
        ("issue_credential", {"remote_on": False, "probe_exists": False}),
        ("revoke_credential", {"issued_by_walk": True}),
        ("revoke_credential", {"issued_by_walk": False}),
        ("enable_remote", {}),
        ("disable_remote", {}),
        ("change_runs_on", {}),
        ("run_steward", {}),
        ("connect_confluence", {}),
        ("run_now", {}),
        ("publish", {}),
        ("unknown", {}),
    ]:
        allowed, reason = _write_allowed(op, ctx)
        ctx_str = json.dumps(ctx) if ctx else ""
        print(f"  {op:25s} {ctx_str:45s} -> allowed={allowed}, reason={reason}")
    print()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # API-only steps (no viewport needed).
        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={tok}", wait_until="load")
        page0.wait_for_timeout(2000)

        print("  [1/7] Remote settings (API)...")
        try:
            remote_state = _step_remote_api(page0, tok, report)
            print(
                f"        done. remote={'ON' if remote_state.get('remote_on') else 'OFF'}, "
                f"active={remote_state.get('active_count', '?')}, "
                f"total={remote_state.get('total_count', '?')}"
            )
        except Exception as exc:
            remote_state = {"remote_on": False}
            print(f"        FAILED: {exc}")
            report.errors.append(f"remote-api: {exc}")

        print("  [3/7] Credential probe (guarded write)...")
        try:
            _step_credential_probe(page0, tok, report, remote_state)
            print(
                f"        done. receipts={len(report.write_receipts)}"
            )
        except Exception as exc:
            print(f"        FAILED: {exc}")
            report.errors.append(f"credential-probe: {exc}")

        page0.close()

        # Viewport loop.
        for vp in VIEWPORTS:
            w = vp["width"]
            h = vp["height"]
            print(f"\n=== Viewport {w}x{h} ===")

            page = browser.new_page(viewport={"width": w, "height": h})
            page.emulate_media(reduced_motion="reduce")
            page_errors: list[str] = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto(f"{base_url}/?token={tok}", wait_until="load")
            if "React Web build is missing" in page.content():
                raise RuntimeError(
                    "HUB SERVES NO BUNDLE: the web build is missing; "
                    "every face step would be hollow"
                )
            page.wait_for_timeout(2000)
            try:
                chair = page.locator(".chair")
                if chair.count() > 0:
                    chair.wait_for(timeout=3000)
                    if chair.evaluate(
                        "el => el.classList.contains('chair-first-value')"
                    ):
                        btn = page.get_by_role(
                            "button", name="Continue later", exact=True,
                        )
                        if btn.count() > 0:
                            btn.click()
                            page.wait_for_timeout(500)
            except Exception:
                pass
            _settle(page)

            # Step 2: Settings -> System.
            print(f"  [2/7] Settings System @ {w}...")
            try:
                _step_settings_system(
                    page, out_dir, w, tok, report, remote_state,
                )
                print("        done.")
            except Exception as exc:
                msg = f"settings-system@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Step 4: Shade receipts.
            print(f"  [4/7] Shade receipts @ {w}...")
            try:
                _step_shade_receipts(page, out_dir, w, tok, report)
                print("        done.")
            except Exception as exc:
                msg = f"shade-receipts@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 5: Rhythm.
            print(f"  [5/7] Rhythm @ {w}...")
            try:
                _step_rhythm(page, out_dir, w, tok, report)
                print("        done.")
            except Exception as exc:
                msg = f"rhythm@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 6: Door.
            print(f"  [6/7] Door @ {w}...")
            try:
                _step_door(page, out_dir, w, tok, report)
                print("        done.")
            except Exception as exc:
                msg = f"door@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            critical = [e for e in page_errors if "ResizeObserver" not in e]
            if critical:
                report.errors.extend([f"JS@{w}: {e}" for e in critical])

            page.close()

        browser.close()

    _detect_defects(report)

    json_path = _write_facts_json(report, out_dir)
    md_path = _write_facts_md(report, out_dir)

    print(f"\n=== WALK 174 COMPLETE ===")
    print(f"  Facts JSON: {json_path}")
    print(f"  Facts MD:   {md_path}")
    print(f"  Shots:      {len(report.shots)}")
    print(f"  Errors:     {len(report.errors)}")
    print(f"  Surprises:  {len(report.surprises)}")
    print(f"  Defects:    {len(report.defects)}")
    print(f"  Writes:     {len(report.write_receipts)}")
    if report.defects:
        for d in report.defects:
            print(f"    - {d}")
    if report.write_receipts:
        print("  Write receipts:")
        for wr in report.write_receipts:
            print(f"    - {wr['operation']}: status={wr.get('status')}")

    if errors_fatal:
        print("\nFATAL ERRORS:")
        for e in errors_fatal:
            print(f"  - {e}")
        return 1

    bounces = [f for f in report.facts if f["verdict"] == "BOUNCE"]
    if bounces:
        print(f"\nBOUNCE verdicts ({len(bounces)}):")
        for b in bounces:
            print(f"  - {b['face']}/{b['field']}: {b['why']}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
