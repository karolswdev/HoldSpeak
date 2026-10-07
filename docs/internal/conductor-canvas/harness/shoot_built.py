"""Conductor F1: the BUILT faces on the real glass, beside their ratified boards.

The canvas method (board.py's runner and fences, unchanged: TARGETS44 at 393, overlap,
contrast, clip, one front window, no modal, no scratch path) against the PRODUCT as built:
CANVAS_MODE=today (no seat, no shim), a real hub on an isolated HOME (removed at the end).
The seed is the canvas's (seed_db.py) plus one git clone registered as the Project's
repository (POST /api/delivery/sources), so the launch sheet's WHERE is real.

Boards: K1a, K1b (first run, the hub's real PATH: claude, codex, tmux), K1c (a second hub
whose PATH holds none of them), K2a-K2e, K3a, K3b. Launch is never pressed: no agent starts.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/conductor-canvas/harness/shoot_built.py
ONLY_WIDTH=393 limits the run. Shots and facts: .tmp/evidence-shots/conductor-f1/. Exit 2 on a
failed fence.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402
import rig  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
OUT = REPO / ".tmp/evidence-shots/conductor-f1"
CANVAS = REPO / "docs/internal/conductor-canvas/shots"
RUNBOOK = "Write the rollback runbook"
ISSUE418 = "PAY-418 Reconciliation job slow on month-end data"
ROOM = "surface-project-memory"
BARE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
TOOLS = ("claude", "codex", "tmux")

OWN44 = r"""() => [...document.querySelectorAll(
  '[data-testid=firstrun-agents] button, [data-testid=hand-sheet] button, [data-testid=hand-sheet] input:not(.surface-choice-card-radio), '
  + '.desk-hand-footer button, [data-testid=hand-row-verb], [role=menu] [role^=menuitem]')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || t.getAttribute('placeholder') || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


ISSUE_SEED = r"""
import json
from datetime import date, timedelta
from holdspeak.db import get_database
db = get_database()
with db._connection() as conn:
    db.automations.create_watch_in_transaction(
        conn, watch_id="w-ledger-jira", connector_id="jira", query_kind="issues",
        name="Ledger issues", query_json=json.dumps({"jql": "project = PAY"}), enabled=True,
        project_id="p-ledger", subject_kind="issue")
day = lambda n: (date.today() - timedelta(days=n)).isoformat()
db.automations.record_refresh("w-ledger-jira", {"schema": 1, "entities": {
    "PAY-418": {"key": "PAY-418", "summary": "Reconciliation job slow on month-end data", "due_at": day(2),
                "url": "https://acme.atlassian.net/browse/PAY-418"},
    "PAY-421": {"key": "PAY-421", "summary": "Add the ledger freeze flag", "due_at": day(1),
                "url": "https://acme.atlassian.net/browse/PAY-421"},
}}, [])
print("issues: 2")
"""


class BuiltStack(rig.Stack):
    """rig.Stack in `today` mode (the product as built). `bare` hides claude, codex and tmux
    from the hub's PATH (K1c). After boot: one git clone, registered as the Project's repository."""

    bare = False
    launch = False          # the receipt boards: tmux and claude doubles first on the hub's PATH
    tmux_state: Path | None = None

    def __init__(self, mode: str = "today", shims: str = "k"):
        super().__init__("today", shims)

    def __enter__(self):
        saved = os.environ.get("PATH", "")
        if self.bare:
            # The hub inherits os.environ; vite needs node, so only tools are hidden: a PATH
            # of the system folders plus node's own folder (no claude, codex, tmux there).
            node = subprocess.run(["which", "node"], capture_output=True, text=True).stdout.strip()
            node_dir = str(Path(node).parent)
            if any((Path(node_dir) / t).exists() for t in TOOLS):
                shim = Path(f"/tmp/f1-node-{os.getpid()}")
                shim.mkdir(exist_ok=True)
                for name in ("node", "npm", "npx"):
                    target = Path(node_dir) / name
                    if target.exists() and not (shim / name).exists():
                        (shim / name).symlink_to(target)
                node_dir = str(shim)
            os.environ["PATH"] = f"{node_dir}:{BARE_PATH}"
        saved_env = {k: os.environ.get(k) for k in ("F1_TMUX_STATE", "F1_HOLDSPEAK")}
        if self.launch:
            state = Path(f"/tmp/f1-tmux-{os.getpid()}-{os.urandom(3).hex()}")
            (state / "bin").mkdir(parents=True)
            double = Path(__file__).resolve().parent / "tmux_double.py"
            for name, twin in (("tmux", ""), ("claude", "F1_TWIN=claude ")):
                exe = state / "bin" / name
                exe.write_text(f"#!/bin/bash\n{twin}exec {rig.PY} {double} \"$@\"\n")
                exe.chmod(0o755)
            BuiltStack.tmux_state = state
            os.environ["PATH"] = f"{state / 'bin'}:{saved}"
            os.environ["F1_TMUX_STATE"] = str(state)
            os.environ["F1_HOLDSPEAK"] = str(Path(rig.PY).parent / "holdspeak")
        try:
            super().__enter__()
        finally:
            os.environ["PATH"] = saved
            for key, value in saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        clone = Path(self.home) / "dev" / "payments-ledger"
        clone.mkdir(parents=True)
        git = ["git", "-C", str(clone), "-c", "user.name=canvas", "-c", "user.email=canvas@example.invalid"]
        subprocess.run(["git", "init", "-q", "-b", "main", str(clone)], check=True)
        (clone / "README.md").write_text("# payments-ledger\n")
        subprocess.run([*git, "add", "."], check=True)
        subprocess.run([*git, "commit", "-qm", "init"], check=True)
        status, body = rig.hub_api(self.hub, "POST", "/api/delivery/sources",
                                   {"path": str(clone), "label": "Payments ledger cutover"})
        self.seed["repository"] = {"status": status, "ok": isinstance(body, dict) and body.get("success")}
        # The canvas's issue rows (#418, #421; its stand-in S4) through a REAL producer: the
        # Room's OPEN HERE reads issue rows only from a Jira `issues` Watch snapshot
        # (ProjectService._read_room_needs_you; a GitHub issues Watch yields no row on main).
        # Since R4 each row names its Watch and entity, so Hand to agent takes it.
        seeded = subprocess.run(
            [rig.PY, "-c", ISSUE_SEED], cwd=REPO, capture_output=True, text=True, timeout=120,
            env={**os.environ, "HOME": self.home, "PYTHONPATH": str(REPO)},
        )
        self.seed["issues"] = seeded.stdout.strip() or seeded.stderr[-400:]
        return self


rig.Stack = BuiltStack


def first_run(r: board.Runner) -> None:
    r.scope44 = OWN44
    if BuiltStack.launch:
        return
    card = "[data-testid=firstrun-agents]"
    r.page.locator(card).scroll_into_view_if_needed()
    r.settle(800)
    if BuiltStack.bare:
        r.shoot_bare("K1c-agents-not-installed", None,
                     whole=[card + " [aria-label^='Copy install: Claude']", card + " [data-testid=firstrun-agents-check]"],
                     checks={"no agent found": "NO AGENT FOUND" in r.ev(f"() => document.querySelector('{card}').innerText")})
        return
    r.shoot_bare("K1a-agents-found", None,
                 whole=[card + " [aria-label^='Install hooks']", card + " [data-agent=claude]", card + " [data-agent=tmux]"],
                 checks={"two agent rows and a tmux row": r.ev(f"() => document.querySelectorAll('{card} [data-testid=firstrun-agent-row]').length") == 3})
    r.tap(r.page.locator(card + " [aria-label^='Install hooks']"), 2500)
    r.page.locator(card).scroll_into_view_if_needed()
    r.settle(600)
    r.shoot_bare("K1b-agents-done-receipt", None, whole=[card + " [data-testid=firstrun-agents-receipt]"],
                 checks={"the card folded to its receipt (no rows)": r.ev(f"() => !document.querySelector('{card} [data-testid=firstrun-agent-row]')")})


def close_sheet(r: board.Runner) -> None:
    r.ev("() => import('/src/desk/agentHand.ts').then((m) => m.useAgentHand.getState().close())")
    r.settle(400)


def boards(r: board.Runner) -> None:
    ev, settle, page, phone = r.ev, r.settle, r.page, r.phone
    r.scope44 = OWN44
    if BuiltStack.bare:
        return
    if BuiltStack.launch:
        receipts(r)
        return

    # ── K2a the Object menu (the Floor list, the decision selected) ──
    ev("() => window.__cOpen.floorList()")
    settle(1500)
    ev("() => window.__cOpen.select('decision:d-freeze')")
    settle(600)
    if phone:
        r.tap(page.locator(".desk-verbbar [data-menu-id=go] button"), 700)
        r.open_sub("Object")
        row = page.locator("[role=menu] [role=menuitem]:has-text('Hand to agent')").first
        row.scroll_into_view_if_needed()
        settle(300)
    else:
        page.locator(".desk-verbbar [data-menu-id=object] button").first.click()
        settle(700)
    f = r.shoot_bare("K2a-object-menu", None)
    if f is not None and not any("Hand to agent" in x for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"K2a-{r.width}: no Hand to agent row in the Object menu ({f['menus'][:1]})")
    r.escape()

    # ── K2b the object context menu (1440; at 393 a press opens the object: K2a is the phone path) ──
    if phone:
        r.facts[f"K2b-context-menu-{r.width}"] = {"not_drawn": "393: a row press opens the object; the object menu is Go > Object (K2a-393)"}
    else:
        name = page.locator(".desk-list-name-cell:has-text('Freeze the old ledger on Nov 5')").first
        name.scroll_into_view_if_needed()
        b = name.bounding_box()
        page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, button="right")
        settle(600)
        f = r.shoot_bare("K2b-context-menu", None)
        if f is not None and not any("Hand to agent" in x for m in f["menus"] for x in m["rows"]):
            r.fails.append(f"K2b-{r.width}: no Hand to agent row in the context menu")
        r.escape()

    # ── K2c the ⌘K deck ──
    ev("() => window.__cOpen.palette('1')")
    settle(700)
    page.keyboard.type("hand", delay=40)
    settle(900)
    deck = ev("() => document.body.innerText")
    r.shoot_bare("K2c-command-deck", None, inherit=["Freeze the old ledger on Nov 5"], inherit_overlap=["39 ITEMS", "39 SHOWN", "40 ITEMS", "40 SHOWN"],
                 checks={"the deck lists Hand to agent": "Hand to agent" in deck})
    ev("() => window.__cOpen.palette('0')")
    settle(400)
    page.keyboard.press("Escape")
    ev("() => window.__cOpen.chair()")
    settle(1500)
    r.close_all()

    # ── K2d the Door row verb (Needs you: the action item) ──
    show = page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if show.count():
        r.tap(show, 900)
    row = page.locator(f"[data-testid=arrival-needs-you-row]:has-text('{RUNBOOK}')").first
    row.scroll_into_view_if_needed()
    settle(500)
    r.shoot("K2d-door-row-verb", "Needs you", whole=[f"[aria-label='Hand to agent: {RUNBOOK}']"])

    # ── K3a the launch sheet (from the Door row), Claude Code ──
    r.tap(row.locator("[data-testid=hand-row-verb]"), 2500)
    footer = "() => (document.querySelector('.desk-hand-footer') || {}).innerText || ''"
    r.shoot("K3a-launch-sheet-claude", "Hand to agent",
            whole=["[data-testid=hand-launch]", ".desk-hand-footer .gadget-chip-egress", "[data-testid=hand-control]"],
            checks={"the egress chip names Anthropic": "API.ANTHROPIC.COM" in ev(footer),
                    "the brief composed (sources listed)": ev("() => document.querySelectorAll('[data-testid=hand-sheet] li.surface-ledger-row').length") > 0,
                    "WHERE names the repository": "PAYMENTS-LEDGER" in ev("() => (document.querySelector('[data-testid=hand-where]') || {}).innerText || ''").upper()},
            extra={"sheet": ev("() => (document.querySelector('[data-testid=hand-sheet]') || {}).innerText || ''")[:1200]})
    close_sheet(r)
    r.close_all()

    # ── K2e the Room row verb, then K3b: the sheet from the Room, Codex picked ──
    ev("() => window.__cOpen.room('p-ledger')")
    settle(3500)
    ev("(w) => window.__cOpen.focus(w)", ROOM)
    settle(500)
    rrow = page.locator(f"[id='{ROOM}'] [data-testid=needs-you-row]:has-text('{RUNBOOK}')").first
    rrow.scroll_into_view_if_needed()
    settle(400)
    rows = ev(f"() => [...document.querySelectorAll(\"[id='{ROOM}'] [data-testid=needs-you-row]\")].map((c) => c.innerText.replace(/\\s+/g, ' ').trim())")
    issue_rows = [x for x in rows if "PAY-418" in x or "PAY-421" in x]
    # Conductor R4: an issue row wears Hand to agent, as ratified (K2e).
    r.shoot("K2e-room-row-verb", "Payments ledger cutover",
            whole=[f"[id='{ROOM}'] [aria-label='Hand to agent: {RUNBOOK}']", f"[id='{ROOM}'] [aria-label='Hand to agent: {ISSUE418}']"],
            checks={"the two issue rows are in OPEN HERE (real producer)": len(issue_rows) == 2,
                    "each issue row has Hand to agent (R4: agent.hand takes an issue)": len(issue_rows) == 2 and all("Hand to agent" in x for x in issue_rows),
                    "the runbook row has Hand to agent": any(RUNBOOK in x and "Hand to agent" in x for x in rows)},
            extra={"open_here": rows})
    # K3b as ratified: the sheet for the issue, from its Room row, Codex picked.
    irow = page.locator(f"[id='{ROOM}'] [data-testid=needs-you-row]:has-text('PAY-418')").first
    irow.scroll_into_view_if_needed()
    settle(300)
    r.tap(irow.locator("[data-testid=hand-row-verb]"), 2500)
    r.tap(page.locator("[data-testid=hand-sheet] label.surface-choice-card:has-text('Codex')").first, 2000)
    r.shoot("K3b-launch-sheet-codex", "Hand to agent", whole=["[data-testid=hand-launch]", ".desk-hand-footer .gadget-chip-egress"],
            checks={"the egress chip follows the pick": "API.OPENAI.COM" in ev(footer),
                    "the sheet carries the issue (R4)": "PAY-418" in ev("() => (document.querySelector('[data-testid=hand-sheet]') || {}).innerText || ''")},
            extra={"sheet": ev("() => (document.querySelector('[data-testid=hand-sheet]') || {}).innerText || ''")[:1200]})
    close_sheet(r)


RECEIPT_LINE = r"""() => { const e = document.querySelector('[data-testid=hand-launch-receipt]'); if (!e) return null;
  const r = e.getBoundingClientRect(), f = e.closest('.desk-window-shell').getBoundingClientRect();
  return { text: e.textContent, clipped: e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1,
           inside: r.left >= f.left - 1 && r.right <= f.right + 1 && r.bottom <= Math.min(f.bottom, innerHeight) + 1 }; }"""


def receipts(r: board.Runner) -> None:
    """After Launch, on the real hub with tmux and claude doubles at the process boundary:
    PENDING (the agent has not registered), DELIVERING (the brief is being typed),
    NOT SENT (the typing failed: the brief is kept), then Send again -> SENT."""
    ev, settle, page = r.ev, r.settle, r.page
    state = BuiltStack.tmux_state
    ev("() => window.__cOpen.chair()")
    settle(1500)
    show = page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if show.count():
        r.tap(show, 900)
    row = page.locator(f"[data-testid=arrival-needs-you-row]:has-text('{RUNBOOK}')").first
    row.scroll_into_view_if_needed()
    r.tap(row.locator("[data-testid=hand-row-verb]"), 2500)
    r.tap(page.locator("[data-testid=hand-launch]"), 400)

    def wait_receipt(word: str, timeout: float = 60) -> dict:
        end = time.time() + timeout
        while time.time() < end:
            line = ev(RECEIPT_LINE)
            if line and word in line["text"]:
                return line
            settle(500)
        r.fails.append(f"receipt-{r.width}: never read {word!r} (last: {ev(RECEIPT_LINE)})")
        return ev(RECEIPT_LINE) or {}

    def shoot(name: str, word: str) -> None:
        line = wait_receipt(word)
        settle(400)
        r.shoot(name, "Hand to agent", whole=["[data-testid=hand-launch-receipt]", ".desk-hand-footer .gadget-chip-egress"],
                checks={f"the receipt reads {word}": word in str(line.get("text")),
                        "the receipt is whole (not clipped, inside the window)": not line.get("clipped") and line.get("inside")},
                extra={"receipt": line})

    shoot("K3r-receipt-pending", "BRIEF PENDING")
    (state / "hold").touch()
    (state / "register").touch()
    shoot("K3r-receipt-delivering", "BRIEF DELIVERING")
    (state / "fail").touch()
    (state / "hold").unlink()
    shoot("K3r-receipt-failed", "BRIEF NOT SENT")
    (state / "fail").unlink()
    r.tap(page.locator("[data-testid=hand-send-again]"), 600)
    shoot("K3r-receipt-sent", "BRIEF SENT")
    r.facts[f"_tmux_argv_{r.width}"] = (state / "argv.log").read_text().splitlines()[-40:] if (state / "argv.log").exists() else []


PAIRS = ["K1a-agents-found", "K1b-agents-done-receipt", "K1c-agents-not-installed", "K2a-object-menu", "K2b-context-menu",
         "K2c-command-deck", "K2d-door-row-verb", "K2e-room-row-verb", "K3a-launch-sheet-claude", "K3b-launch-sheet-codex"]


def pair_page() -> None:
    """One HTML page: each ratified board beside its built shot (both widths)."""
    rows = []
    for name in PAIRS:
        for w in (1440, 393):
            built, ratified = OUT / f"{name}-{w}.png", CANVAS / f"{name}-{w}.png"
            if not built.exists() and not ratified.exists():
                continue
            rows.append(
                f"<h2>{name} · {w}</h2><div class=p><figure><figcaption>RATIFIED</figcaption><img src='{ratified.resolve().as_uri()}'></figure>"
                f"<figure><figcaption>BUILT</figcaption><img src='{built.resolve().as_uri() if built.exists() else ''}'></figure></div>")
    (OUT / "pairs.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Conductor F1: board beside build</title>"
        "<style>body{background:#111;color:#ddd;font:13px monospace}.p{display:flex;gap:12px}figure{margin:0;flex:1}img{width:100%}</style>"
        + "".join(rows))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    widths = [w for w in board.B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts: dict = {}
    fails: list[str] = []
    legs = [(False, False), (True, False), (False, True)]
    if os.environ.get("ONLY_RECEIPTS"):
        legs = [(False, True)]
    for bare, launch in legs:
        BuiltStack.bare, BuiltStack.launch = bare, launch
        for width, height in widths:
            r = board.Runner(OUT, "K", width, height, "k", None)
            r.first_run = first_run
            if bare or launch:
                os.environ["NO_WARMUP"] = "1"
            r.run(boards)
            os.environ.pop("NO_WARMUP", None)
            fails += r.fails
            facts.update(r.facts)
    facts["_fails"] = fails
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    pair_page()
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
