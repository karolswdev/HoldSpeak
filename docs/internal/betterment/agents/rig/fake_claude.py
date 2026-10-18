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
import subprocess
import sys
import time
import uuid

HOME = os.environ.get("HOME", "/tmp")
LOG = os.path.join(HOME, "fake-agent.log")
SID = str(uuid.uuid4())
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


HOOKS = settings_hooks()
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


def say(text, delay=0.4):
    for line in text.splitlines():
        print(line, flush=True)
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
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧"
    for i, step in enumerate(steps):
        title(f"{spinner[i % len(spinner)]} fake-claude")
        say(f"● {step}")
        say("  ⎿  esc to interrupt", 0.2)
        fire("PostToolUse", tool_name="Bash", tool_input={"command": step.split(':')[0]})
        time.sleep(2)
    title("✳ fake-claude")


say("╭─────────────────────────────────────────╮")
say("│ ✻ FAKE Claude Code (betterment walk rig) │")
say("╰─────────────────────────────────────────╯")
fire("SessionStart", source="startup")
say(f"cwd: {CWD}")
say("> ", 0)

brief = read_block()
log(f"first message ({len(brief)} chars): {brief[:400]!r}")
fire("UserPromptSubmit", prompt=brief)
transcript("user", brief)
work(["Read: the brief and the repo", "Bash: git status", "Bash: rg rollback"])

question = ("I found two places for the rollback flag. Should it live in "
            "config/flags.yaml (shared with staging) or in an env var (per host)? "
            "Answer 1 for config, 2 for env.")
say("")
say(f"● {question}")
transcript("assistant", question)
fire("Stop", last_assistant_message=question, stop_hook_active=False)
time.sleep(4)
fire("Notification", notification_type="idle_prompt", message="Claude is waiting for your input")
say("> ", 0)

answer = read_block()
log(f"ANSWER RECEIVED: {answer!r}")
fire("UserPromptSubmit", prompt=answer)
transcript("user", answer)
say(f"● Got it: {answer[:120]}")
work(["Edit: config/flags.yaml", "Bash: pytest -q tests/test_rollback.py"])

say("")
say("● Bash command")
say("  rm -rf build/ && make release")
say("  Do you want to proceed?")
say("  ❯ 1. Yes")
say("    2. No, and tell Claude what to do differently (esc)")
fire("Notification", notification_type="permission_prompt",
     message="Claude needs your permission to use Bash")
key = read_block(quiet=0.8)
log(f"PERMISSION KEY RECEIVED: {key!r}")
fire("UserPromptSubmit", prompt=f"(permission answer {key!r})")
work(["Bash: make release"])

done = ("Done. The rollback flag now lives in the place you chose, with a test. "
        "Branch is ready for review; I did not open a PR.")
say("")
say(f"● {done}")
transcript("assistant", done)
fire("Stop", last_assistant_message=done, stop_hook_active=False)
say("> ", 0)
rest = read_block()
log(f"after done, got: {rest!r}")
while True:
    time.sleep(60)
