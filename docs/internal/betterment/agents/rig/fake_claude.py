#!/opt/homebrew/bin/python3 -I
"""A FAKE Claude Code for the betterment walk. Never the real one.

It speaks Claude Code's hook protocol (the --settings file the launch
passes), prints a little work, asks one question, waits for the answer on
stdin, then asks for one permission, then finishes. Nothing leaves the
machine. Every event is logged to $HOME/fake-agent.log.
"""
import json
import os
import select
import shlex
import shutil
import subprocess
import sys
import time
import uuid

HOME = os.environ.get("HOME", "/tmp")
LOG = os.path.join(HOME, "fake-agent.log")
# Betterment AG6: `--resume <id>` continues that session (its transcript
# must exist, as the real CLI's must); an unknown id fails like the real one.
RESUME = sys.argv[sys.argv.index("--resume") + 1] if "--resume" in sys.argv[1:-1] else None
SID = RESUME or str(uuid.uuid4())
CWD = os.getcwd()
TRANSCRIPT = os.path.join(HOME, f"fake-transcript-{SID}.jsonl")


def log(msg):
    with open(LOG, "a") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} [{SID[:8]}] {msg}\n")


def settings_hooks():
    argv = sys.argv[1:]
    if "--settings" in argv:
        path = argv[argv.index("--settings") + 1]
        try:
            return json.load(open(path)).get("hooks", {})
        except Exception as exc:  # noqa: BLE001
            log(f"settings unreadable: {exc}")
    return {}


# Betterment AG7: with its hooks off (FAKE_CLAUDE_HOOKS=off, or the file
# $HOME/fake-claude-hooks-off) the desk knows this agent from its screen
# alone (the herdr rules read the title and the bottom of the pane).
HOOKS_OFF = os.environ.get("FAKE_CLAUDE_HOOKS", "").lower() == "off" or os.path.exists(
    os.path.join(HOME, "fake-claude-hooks-off"))
HOOKS = {} if HOOKS_OFF else settings_hooks()
safe_argv = [a if len(a) < 200 else a[:60] + "…" for a in sys.argv[1:]]
log(f"start argv={safe_argv} cwd={CWD}")
log("env HOLDSPEAK keys: " + ",".join(sorted(k for k in os.environ if k.startswith("HOLDSPEAK"))))


def fire(event, **extra):
    payload = {"session_id": SID, "transcript_path": TRANSCRIPT, "cwd": CWD,
               "hook_event_name": event, **extra}
    entries = HOOKS.get(event, [])
    ran = 0
    for entry in entries:
        matcher = entry.get("matcher")
        tool = extra.get("tool_name")
        if matcher and tool and tool not in matcher.split("|"):
            continue
        if matcher and event == "SessionStart" and extra.get("source") not in matcher.split("|"):
            continue
        for hook in entry.get("hooks", []):
            cmd = hook.get("command")
            if not cmd:
                continue
            try:
                res = subprocess.run(cmd, shell=True, input=json.dumps(payload), text=True,
                                     capture_output=True, timeout=hook.get("timeout", 30))
                ran += 1
                log(f"hook {event} rc={res.returncode} out={res.stdout[:200]!r} err={res.stderr[-300:]!r}")
            except Exception as exc:  # noqa: BLE001
                log(f"hook {event} failed: {exc}")
    log(f"fired {event} ({ran} hooks)")


def title(text):
    sys.stdout.write(f"\033]0;{text}\007")
    sys.stdout.flush()


# The screen is drawn like Claude Code's own: the conversation, then (while
# it works) a spinner line with "esc to interrupt", then the prompt box
# between two rules, or an approval dialog in its place. Each change redraws
# the whole screen, as a full-screen terminal app does.
LINES = []
FOOT = "prompt"     # "prompt" | "working" | "dialog"
DIALOG = []
STARTED = time.time()


def rule():
    width = shutil.get_terminal_size((100, 30)).columns
    return "─" * max(20, width - 1)


def draw():
    height = shutil.get_terminal_size((100, 30)).lines
    foot = []
    if FOOT == "working":
        foot += ["", f"✻ Working… ({int(time.time() - STARTED) % 60 + 1}s · esc to interrupt)"]
    if FOOT == "dialog":
        foot += [rule(), *DIALOG]
    else:
        foot += [rule(), "❯ ", rule(), "  ? for shortcuts"]
    body = LINES[-max(1, height - len(foot) - 1):]
    sys.stdout.write("\033[2J\033[H" + "\n".join(body + foot))
    sys.stdout.flush()


def say(text, delay=0.4):
    for line in text.splitlines():
        LINES.append(line)
        draw()
        time.sleep(delay)


def read_block(quiet=1.5):
    """Read lines until the input is quiet: a pasted brief arrives in parts."""
    lines = []
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], quiet if lines else 3600)
        if not ready:
            break
        line = sys.stdin.readline()
        if line == "":
            break
        lines.append(line.rstrip("\n"))
    return "\n".join(lines).strip()


def transcript(role, text):
    with open(TRANSCRIPT, "a") as fh:
        fh.write(json.dumps({"type": role, "message": {"role": role,
                 "content": [{"type": "text", "text": text}]}}) + "\n")


def work(steps):
    global FOOT
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧"
    FOOT = "working"
    for i, step in enumerate(steps):
        title(f"{spinner[i % len(spinner)]} fake-claude")
        say(f"● {step}")
        say("  ⎿  done", 0.2)
        fire("PostToolUse", tool_name="Bash", tool_input={"command": step.split(':')[0]})
        time.sleep(2)
    FOOT = "prompt"
    title("✳ fake-claude")
    draw()


if RESUME is not None:
    if not os.path.exists(TRANSCRIPT):
        log(f"resume refused: no conversation {RESUME}")
        print(f"No conversation found with session ID: {RESUME}", file=sys.stderr)
        sys.exit(1)
    log(f"resumed {RESUME}")
    say("✻ FAKE Claude Code resumed the conversation")
    fire("SessionStart", source="resume")
    title("✳ fake-claude")
    draw()
    rest = read_block()
    log(f"after resume, got: {rest!r}")
    while True:
        time.sleep(60)

say("╭─────────────────────────────────────────╮")
say("│ ✻ FAKE Claude Code (betterment walk rig) │")
say("╰─────────────────────────────────────────╯")
fire("SessionStart", source="startup")
say(f"cwd: {CWD}")
title("✳ fake-claude")
draw()

brief = read_block()
log(f"first message ({len(brief)} chars): {brief[:400]!r}")
fire("UserPromptSubmit", prompt=brief)
transcript("user", brief)
# Betterment AG10: like a real agent, it reads one desk object through the
# hub's MCP with its launch credential (the meeting its brief names), then
# changes one file in its worktree and commits it.
def mcp_read(text):
    import re
    import urllib.request

    url = os.environ.get("HOLDSPEAK_HUB_URL", "")
    token = os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL", "")
    match = re.search(r"meeting:([A-Za-z0-9_.-]+)", text or "")
    if not (url and token and match):
        log(f"mcp read skipped (url={bool(url)} token={bool(token)} meeting={bool(match)})")
        return
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "meeting.get", "arguments": {"meeting_id": match.group(1)}}}).encode()
    request = urllib.request.Request(url.rstrip("/") + "/api/mcp", data=body, method="POST",
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as answer:
            log(f"mcp meeting.get {match.group(1)}: {answer.read()[:160]!r}")
    except Exception as exc:  # noqa: BLE001
        log(f"mcp meeting.get failed: {exc}")


def edit_and_commit():
    path = os.path.join(CWD, "ROLLBACK.md")
    with open(path, "a") as fh:
        fh.write("The rollback flag lives in config/flags.yaml.\n")
    for argv in (["git", "add", "ROLLBACK.md"],
                 ["git", "-c", "user.name=Fake Claude", "-c", "user.email=fake@example.invalid",
                  "commit", "-q", "-m", "Move the rollback flag into config"]):
        done = subprocess.run(argv, cwd=CWD, capture_output=True, text=True)
        log(f"{' '.join(argv[:2])} rc={done.returncode} {done.stderr[-160:]!r}")


mcp_read(brief)
work(["Read: the brief and the repo", "Bash: git status", "Bash: rg rollback"])
edit_and_commit()

question = ("I found two places for the rollback flag. Should it live in "
            "config/flags.yaml (shared with staging) or in an env var (per host)? "
            "Answer 1 for config, 2 for env.")
say("")
say(f"● {question}")
transcript("assistant", question)
fire("Stop", last_assistant_message=question, stop_hook_active=False)
time.sleep(4)
fire("Notification", notification_type="idle_prompt", message="Claude is waiting for your input")

answer = read_block()
log(f"ANSWER RECEIVED: {answer!r}")
fire("UserPromptSubmit", prompt=answer)
transcript("user", answer)
say(f"● Got it: {answer[:120]}")
work(["Edit: config/flags.yaml", "Bash: pytest -q tests/test_rollback.py"])

DIALOG = [" Bash command", "", "   rm -rf build/ && make release", "   Clean the build and release",
          "", " Do you want to proceed?", " ❯ 1. Yes", "   2. No, and tell Claude what to do differently (esc)",
          "", " Esc to cancel"]
FOOT = "dialog"
draw()
fire("Notification", notification_type="permission_prompt",
     message="Claude needs your permission to use Bash")
key = read_block(quiet=0.8)
log(f"PERMISSION KEY RECEIVED: {key!r}")
FOOT = "prompt"
say("● Bash(rm -rf build/ && make release)")
fire("UserPromptSubmit", prompt=f"(permission answer {key!r})")
work(["Bash: make release"])

done = ("Done. The rollback flag now lives in the place you chose, with a test. "
        "Branch is ready for review; I did not open a PR.")
say("")
say(f"● {done}")
transcript("assistant", done)
fire("Stop", last_assistant_message=done, stop_hook_active=False)
rest = read_block()
log(f"after done, got: {rest!r}")
while True:
    time.sleep(60)
