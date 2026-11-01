"""The brief in his terms (owner verdict 2026-10-31, the standing BRIEF RULE).

"I saw this briefing. And to be honest? It didn't even make sense to me. I
didn't get enough context plus I felt like I answered, so why is there
more…?" A brief reads like a note from a chief of staff, in this order, each
one short line:

1. what the program is for (its goal);
2. what this step was doing (its title and the first sentence of its brief);
3. what happened, in plain words (the known failures translated; an unknown
   one is the first sentence of the reason with every path, command,
   ``fatal:``, ``error:`` and hash removed);
4. the question, in one sentence;
5. each choice with its consequence in his terms, with what happens to the
   program after.

The raw reason, the check log, the brief and the Program text are folds,
closed. "What changed" is at most three plain lines. After his press the
page settles to one line (:func:`settle_words`).

One truth: ``BriefingService._compose`` builds the package from these
words, and the page, the Telegram message and the call read the same lines
in the same order. :func:`fence_hits` is the fence every line passes: no
``fatal:``, ``error:``, ``Traceback``, path, shell command or 7+ hex hash.
No model is in this module: every line is a rule.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Optional

# ── the fence ─────────────────────────────────────────────────────────

_FENCE: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fatal:", re.compile(r"fatal:", re.I)),
    ("error:", re.compile(r"error:", re.I)),
    ("Traceback", re.compile(r"Traceback")),
    # A shell command.
    ("command", re.compile(r"\b(?:sh|bash|zsh)\s+-\w|\b(?:git|gh|npm|npx|uv|pytest|python3?|curl)\s+[a-z-]{2,}"
                           r"|&&|\|\||\$\(|`")),
    # A hash: 7 or more hex characters with a digit and a letter.
    ("hash", re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,}\b", re.I)),
)


def _is_path(token: str) -> bool:
    """A slash-joined token with a dot in it, or one that starts with ``/``
    or ``~/`` (``src/a.py``, ``/tmp/x``, ``./run.sh``, a URL)."""
    token = token.strip("()[]{}\"'`,;:").rstrip(".?!…")
    if "/" not in token or token == "/":
        return False
    return token.startswith(("/", "~/")) or "." in token


def fence_hits(text: Any) -> list[str]:
    """The names of what a line may never hold, found in ``text``."""
    words = str(text or "")
    hits = {name for name, pattern in _FENCE if pattern.search(words)}
    if any(_is_path(token) for token in words.split()):
        hits.add("path")
    return sorted(hits)


def clean(text: Any) -> bool:
    return not fence_hits(text)


# ── plain words ───────────────────────────────────────────────────────

_PATHISH = re.compile(r"~?/?(?:[\w.@+-]+/)+[\w.@+-]*|(?<![\w])/[\w.@+-]+")
_HASH = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,}\b", re.I)
_QUOTED = re.compile(r"(['\"`])[^'\"`]*\1")
_MARKDOWN = re.compile(r"[#*_`>]+")


def _squash(text: Any) -> str:
    return " ".join(str(text or "").split()).strip()


def sentence(text: Any) -> str:
    """One sentence: a capital first letter and a full stop."""
    text = _squash(text).rstrip(" ,;:·-")
    if not text:
        return ""
    text = text[:1].upper() + text[1:]
    return text if text[-1] in ".?!…" else text + "."


def first_sentence(text: Any, limit: int = 160) -> str:
    text = _squash(_MARKDOWN.sub(" ", str(text or "")))
    found = re.match(r"(.+?[.?!])(?:\s|$)", text)
    text = found.group(1) if found else text
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return text


def basenames(text: Any) -> str:
    """Paths as their last name: ``holdspeak/db/schema.py`` → ``schema.py``."""
    def last(found: re.Match[str]) -> str:
        parts = [part for part in found.group(0).split("/") if part and part != "~"]
        return parts[-1] if parts else ""

    return _squash(_PATHISH.sub(last, str(text or "")))


def scrub(text: Any) -> str:
    """The first sentence of a raw reason with every path, command,
    ``fatal:``, ``error:``, ``Traceback`` and hash removed ("" when nothing
    plain is left)."""
    words = _squash(text)
    for cut in (r"fatal:", r"error:", r"Traceback"):
        found = re.search(cut, words, re.I)
        if found:
            words = words[: found.start()]
    words = _QUOTED.sub(" ", words)
    words = re.sub(r"\b(?:sh|bash|zsh)\s+-\w.*$", " ", words)
    words = _PATHISH.sub(" ", words)
    words = _HASH.sub(" ", words)
    words = re.sub(r"\(\s*[,;:]*\s*\)", " ", words)
    words = first_sentence(words)
    words = re.sub(r"\s+([,.;:)])", r"\1", _squash(words)).rstrip(" ,;:(.")
    words = re.sub(r"(?:\s+(?:at|with|in|on|from|to|for|of|the|a|an|and|by|into))+$", "", words, flags=re.I)
    out = sentence(words)
    return out if clean(out) else ""


# ── the lines ─────────────────────────────────────────────────────────

def goal_line(program: Mapping[str, Any]) -> str:
    """"Goal: Stop the stalls." (the program's goal; its title when it has none)."""
    goal = first_sentence(basenames(program.get("goal_markdown") or program.get("goal") or ""))
    if goal:
        line = sentence(f"Goal: {goal[:1].upper() + goal[1:]}")
    else:
        line = sentence(f"The program “{_squash(program.get('title'))}”")
    return line if clean(line) else sentence(f"The program “{_squash(program.get('title'))}”")


def doing_line(step: Optional[Mapping[str, Any]]) -> str:
    """"Step 1, “Add one line to the README”: Add the line under the title."
    (the step's title and the first sentence of its brief)."""
    if not step:
        return "The program's own requirements, after its last step."
    title = _squash(step.get("title")) or "a step"
    brief = first_sentence(basenames(step.get("brief_markdown") or ""), 140)
    ordinal = step.get("ordinal")
    where = f"Step {ordinal}" if ordinal else "The step"
    if brief and title.lower().rstrip(".") in brief.lower():
        line = sentence(f"{where}: {brief}")
    elif brief:
        line = sentence(f"{where}, “{title}”: {brief}")
    else:
        line = sentence(f"{where}: {title}")
    return line if clean(line) else sentence(f"{where}: {scrub(title).rstrip('.') or 'a step'}")


def delivery_where(program: Mapping[str, Any]) -> str:
    """``dw app/1`` for a Program's ``delivery_ref`` ``dw:app/1`` (LANG13)."""
    ref = str(program.get("delivery_ref") or "")
    return f"dw {ref[3:]}" if ref.startswith("dw:") else "its record"


def doing_words(kind: str, program: Mapping[str, Any], step: Optional[Mapping[str, Any]]) -> str:
    """What the held thing was doing: the step, or the program's delivery."""
    if kind == "delivery":
        return sentence(f"The program is done. It delivers its record to {delivery_where(program)}")
    return doing_line(step)


_DELIVER_FAILED = re.compile(r"^Deliver “.*” to (.+?): it (.+)$")
_DELIVER_MERGE = re.compile(r"PR #(\d+)")


_NO_REMOTE = re.compile(r"does not appear to be a git repository|No configured push destination|No such remote|"
                        r"no remote|remote .* not found", re.I)
_ACCESS = re.compile(r"Permission denied|access rights|Authentication failed|could not read Username|403", re.I)
_RED_SECTION = re.compile(r"the section (\S+?) is red")


def parked_cause(reason: Any) -> str:
    """The known failure behind a parked step: ``no_remote``, ``push_access``,
    ``push``, ``pr_create``, ``check_red``, ``agent_start``, ``hand``, or
    ``other``."""
    text = str(reason or "")
    if text.startswith("git push failed"):
        if _NO_REMOTE.search(text):
            return "no_remote"
        return "push_access" if _ACCESS.search(text) else "push"
    if text.startswith("gh pr create failed"):
        return "pr_create"
    if text.startswith("The check failed"):
        return "check_red"
    if text.startswith("The agent did not start"):
        return "agent_start"
    if text.startswith("The hand refused"):
        return "hand"
    return "other"


def _and(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


_PR_CAUSE_WORDS = {
    "no_remote": "could not push its branch: this repository has no remote",
    "push_access": "could not push its branch: the remote refused access",
    "push": "could not push its branch to the remote",
    "pr_create": "could not open its PR on GitHub",
}


def pr_failure_words(reason: Any) -> str:
    """"could not push its branch: this repository has no remote" for a
    push or PR failure (the engine's ledger line and his Your turn row read
    these words, never git's stderr); "" for any other reason."""
    return _PR_CAUSE_WORDS.get(parked_cause(reason), "")


def parked_happened(reason: Any) -> str:
    text = str(reason or "")
    cause = parked_cause(text)
    if cause in _PR_CAUSE_WORDS:
        return f"The step {_PR_CAUSE_WORDS[cause]}."
    if cause == "check_red":
        sections = list(dict.fromkeys(_RED_SECTION.findall(text)))
        if sections:
            return sentence(f"The check went red on {_and(sections[:3])}")
        times = re.match(r"The check failed (\d+) times", text)
        return sentence(f"The check went red {times.group(1)} times" if times else "The check went red")
    if cause == "agent_start":
        return "The agent did not start."
    if cause == "hand":
        return "HoldSpeak could not give the step to an agent."
    return scrub(text) or "The step stopped."


def _after_title(text: Any) -> str:
    """The words after the first ": " of an item title ("Step 1 · X: R1 · …")."""
    text = _squash(text)
    return text.split(": ", 1)[1] if ": " in text else text


def happened_line(kind: str, item: Mapping[str, Any], step: Optional[Mapping[str, Any]]) -> str:
    """What happened, in plain words, for one held item."""
    step = step or {}
    facts = step.get("facts") or {}
    if kind == "parked":
        return parked_happened(step.get("parked_reason") or item.get("title"))
    if kind == "core":
        reason = basenames(item.get("reason") or "")
        if reason.lower().startswith("it "):
            line = sentence(f"The step's change {reason[3:]}")
        else:
            line = sentence(f"The step asks you: {reason}")
        return line if clean(line) else (scrub(reason) or "The step asks you a core question.")
    if kind == "commit":
        return "The agent wants to commit its change."
    if kind == "merge":
        review = ", and the review passed" if step.get("review_verdict") == "pass" else ""
        number = step.get("pr_number")
        pr = f"PR #{number}" if number else "Its PR"
        return sentence(f"The step is ready to merge. {pr} is open, the check is green{review}")
    if kind == "finding":
        finding = next((row for row in step.get("findings") or [] if row.get("id") == item.get("finding_id")), {})
        text = first_sentence(basenames(finding.get("text") or _after_title(item.get("title"))), 150)
        must = str(finding.get("level") or item.get("level") or "").upper() in ("MUST", "REQUIRED")
        line = sentence(f"The reviewer found a required fix: {text}" if must else f"The reviewer found: {text}")
        return line if clean(line) else ("The reviewer found a required fix." if must else "The reviewer found one fix.")
    if kind == "delivery":
        title = _squash(item.get("title"))
        failed = _DELIVER_FAILED.match(title)
        if failed:
            line = sentence(f"Could not deliver to {failed.group(1)}: {failed.group(2)}")
            return line if clean(line) else sentence(f"Could not deliver to {failed.group(1)}")
        number = _DELIVER_MERGE.search(title)
        pr = f"PR #{number.group(1)}" if number else "Its PR"
        return sentence(f"The program is done. The delivery {pr} is open and waits for your merge")
    if kind == "limited":
        until = f" until {item['until_words']}" if item.get("until_words") else ""
        return sentence(f"{item.get('agent') or 'The agent'} is at its usage limit{until}")
    if kind == "race":
        from .program_service import agent_label

        return sentence(f"Agents raced on this step. {agent_label(step.get('profile'))} finished and waits for your pick")
    if kind == "add_step":
        index = item.get("proposal")
        rows = facts.get("proposed_steps") or []
        proposal = rows[index] if isinstance(index, int) and 0 <= index < len(rows) else {}
        title = basenames(proposal.get("title") or "")
        line = sentence(f"The agent proposes a new step: {title}" if title else "The agent proposes a new step")
        return line if clean(line) else "The agent proposes a new step."
    if kind == "todo":
        # PG-IMPORT IMP2: "Claude Code asks you to do this · step 3: <the walk>".
        walk = " ".join(sentence(line) for line in item.get("walk") or [])
        what = basenames(_after_title(item.get("title"))).split(" · ", 1)[-1]
        agent = item.get("agent") or "The agent"
        line = sentence(f"{agent} asks you to do this: {what}") + (f" {walk}" if walk else "")
        return line if clean(line) else sentence(f"{agent} asks you to do this")
    if kind == "requirement_word":
        line = sentence(f"A requirement waits for your word: {basenames(_after_title(item.get('title')))}")
        return line if clean(line) else "A requirement waits for your word."
    if kind == "requirement_left":
        line = sentence(basenames(_after_title(item.get("title"))).replace(" · ", ": ", 1))
        return line if clean(line) else "A requirement is still unmet after the rounds."
    if kind in ("requirement_proposed", "step_change", "step_amend"):
        what = {"requirement_proposed": "a requirement", "step_change": "a change to a step",
                "step_amend": "a line for the running step"}[kind]
        title = basenames(item.get("title") or "")
        line = sentence(f"The agent proposes {what}: {title}" if title else f"The agent proposes {what}")
        return line if clean(line) else sentence(f"The agent proposes {what}")
    return scrub(item.get("reason") or item.get("title")) or "An item waits for you."


QUESTIONS = {
    "parked": "Start the step again, or stop it?",
    "core": "Let the step go on with this, or park it?",
    "commit": "Allow the commit, or stop the step?",
    "merge": "Merge the PR, or keep it open?",
    "finding": "Fix it now, make it a task, or go on without it?",
    "race": "Pick this agent's work as the winner?",
    "add_step": "Add this step to the plan?",
    "requirement_word": "Is the requirement met?",
    "todo": "Did you do it?",
    "requirement_left": "Send the step back for one more round?",
    "requirement_proposed": "Add this requirement to the program?",
    "step_change": "Apply this change to the step?",
    "step_amend": "Send this line to the agent?",
    "answer": "Answer the agent in its lane?",
    "close": "Close the program?",
    "ask_review": "Send it for review?",
}


def question_line(kind: str, item: Mapping[str, Any]) -> str:
    if kind == "answer":
        return "What do you answer the agent?"
    if kind == "delivery":
        return ("Try the delivery again, or skip it?" if "retry" in (item.get("choices") or [])
                else "Merge the delivery pull request, or skip the delivery?")
    if kind == "limited":
        nxt = (item.get("next") or {}).get("label") or "the next agent"
        return sentence(f"Continue in {nxt} now, or wait for the reset?")
    return QUESTIONS.get(kind, "What do you want to do?")


def rest_words(blocked: Iterable[Any], others_open: bool) -> str:
    """What happens to the program after a stop: the steps that wait on this
    one, or the rest going on."""
    count = len(list(blocked))
    if count:
        return ("The step that waits on it waits too." if count == 1
                else f"The {count} steps that wait on it wait too.")
    return "The other steps go on." if others_open else "The program has no other step to run."


def consequence(kind: str, choice: str, item: Mapping[str, Any], step: Optional[Mapping[str, Any]],
                rest: str, blocked: int = 0) -> str:
    """Each choice's consequence in his terms, with what happens after."""
    step = step or {}
    if kind == "parked":
        cause = parked_cause(step.get("parked_reason"))
        if choice == "resume":
            tail = {
                "no_remote": " It will fail the same way until the repository has a remote.",
                "push_access": " It will fail the same way until the remote lets HoldSpeak push.",
                "pr_create": " It fails the same way until GitHub lets HoldSpeak open the PR.",
            }.get(cause, "")
            return f"Try the step again.{tail}"
        return f"Stop this step. {rest}"
    if kind == "core":
        return ("The step goes on with this change." if choice == "go_on"
                else f"Stop this step. {rest}")
    if kind == "commit":
        return ("The change is committed and the check runs." if choice == "allow"
                else f"Stop this step. The change stays in its worktree. {rest}")
    if kind == "merge":
        if choice != "merge":
            return "The PR stays open. Nothing merges."
        if blocked:
            return ("HoldSpeak merges the PR. The step that waits on it can start." if blocked == 1
                    else f"HoldSpeak merges the PR. {blocked} steps that wait on it can start.")
        return "HoldSpeak merges the PR."
    if kind == "finding":
        return {"fix_now": "The agent fixes it in this step.",
                "later": "It becomes a task for later. The step goes on.",
                "skip": "The step goes on without the fix."}.get(choice, "")
    if kind == "limited":
        nxt = (item.get("next") or {}).get("label") or "The next agent"
        until = f" until {item['until_words']}" if item.get("until_words") else ""
        return (sentence(f"{nxt} takes the step now, in the same worktree") if choice == "continue"
                else sentence(f"The step waits{until}"))
    if kind == "race":
        return "This agent's work wins. The step goes on."
    if kind == "add_step":
        return "The step is added to the plan." if choice == "add" else "No step is added. The plan stays as it is."
    if kind == "todo":
        agent = item.get("agent") or "The agent"
        return (f"The requirement is met. {agent} is told." if choice == "done"
                else f"The requirement is not met. {agent} is told you cannot do it. The step does not merge.")
    if kind == "requirement_word":
        return "The requirement is met." if choice == "met" else "The requirement is not met. The step does not merge."
    if kind == "requirement_left":
        return "The agent gets one more round on it."
    if kind == "requirement_proposed":
        return "The requirement is added." if choice == "add" else "Nothing is added."
    if kind == "step_change":
        return "The step changes." if choice == "apply" else "The step stays as it is."
    if kind == "step_amend":
        return "The agent gets the line." if choice == "send" else "Nothing is sent."
    if kind == "delivery":
        return {"merge": "Merge the delivery pull request. The program is then delivered.",
                "retry": "Try the delivery again.",
                "skip": "Skip it. The program stays Done, not delivered."}.get(choice, "")
    return ""


#: What his press did, in one short sentence, for the settled page.
_SETTLED = {
    ("parked", "resume"): "The step starts again.", ("parked", "skip"): "The step stays stopped.",
    ("core", "go_on"): "The step goes on.", ("core", "park"): "The step is parked.",
    ("commit", "allow"): "The change is committed.", ("commit", "not_now"): "The step is parked.",
    ("merge", "merge"): "The PR merges.", ("merge", "not_yet"): "The PR stays open.",
    ("finding", "fix_now"): "The agent fixes it.", ("finding", "later"): "It is a task for later.",
    ("finding", "skip"): "The step goes on.", ("limited", "continue"): "Another agent takes the step.",
    ("limited", "wait"): "The step waits for the reset.", ("race", "pick"): "This agent's work wins.",
    ("add_step", "add"): "The step is added.", ("add_step", "skip"): "No step is added.",
    ("requirement_word", "met"): "The requirement is met.",
    ("requirement_word", "unmet"): "The requirement is not met.",
    ("requirement_left", "send_back"): "The agent gets one more round.",
    ("todo", "done"): "Done. The agent is told.", ("todo", "cant"): "Sent. The agent is told you cannot do it.",
    ("requirement_proposed", "add"): "The requirement is added.", ("requirement_proposed", "skip"): "Nothing is added.",
    ("step_change", "apply"): "The step changes.", ("step_change", "skip"): "The step stays as it is.",
    ("step_amend", "send"): "The agent gets the line.", ("step_amend", "skip"): "Nothing is sent.",
    ("delivery", "merge"): "The program is delivered.", ("delivery", "retry"): "The delivery runs again.",
    ("delivery", "skip"): "The program stays Done, not delivered.",
}

_COUNT = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}


def waits_words(others: int) -> str:
    """"Nothing else waits on you." · "One more waits on you." · "Two more wait on you."."""
    if others <= 0:
        return "Nothing else waits on you."
    count = _COUNT.get(others, str(others))
    return f"{count} more waits on you." if others == 1 else f"{count} more wait on you."


def settle_words(kind: str, choice: str, label: str, clock: str, others: int, via_words: str = "") -> str:
    """"Resume · 18:18. The step starts again. Nothing else waits on you."."""
    did = _SETTLED.get((kind, choice), "")
    head = f"{label} · {clock}" + (f" · {via_words}" if via_words else "")
    return " ".join(part for part in (f"{head}.", did, waits_words(others)) if part)


# ── what changed ──────────────────────────────────────────────────────

_DROP = re.compile(r"^(?:Running the check|git push failed|gh pr create failed|Could not push its branch|"
                   r"Could not open its PR|Parked|Resumed)", re.I)


#: The engine's own ledger words, in his terms (PG-WINDOW follow-up: the
#: window quoted "Skipped the step" and "Could not hand the step:
#: worktree_duplicate").
_PLAIN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^Skipped the step", re.I), "You skipped the step."),
    (re.compile(r"^Could not hand the step\b", re.I), "HoldSpeak could not give the step to an agent."),
    (re.compile(r"^Said it is done\b", re.I), "The agent said it is done."),
    (re.compile(r"^Allowed the agent's commit\b", re.I), "You allowed the agent's commit."),
)
_WIRE_WORD = re.compile(r"\b[a-z]+_[a-z0-9_]+\b")


def changed_line(line: Any) -> str:
    """One checkpoint line in plain words, or "" when it says nothing plain
    (a command, a path, a wire code, the failure the brief already names)."""
    text = _squash(line)
    if not text or _DROP.match(text):
        return ""
    for pattern, words in _PLAIN:
        if pattern.match(text):
            return words
    handed = re.match(r"^Handed to (.+?) in \S+$", text)
    if handed and clean(handed.group(1)):
        return sentence(f"Handed to {handed.group(1)}")
    parts = [part.strip() for part in text.split(" · ")]
    if parts[0] == "Checked" and len(parts) >= 2:
        took = next((part for part in parts[2:] if clean(part) and ("min" in part or "minute" in part
                                                                 or re.match(r"\d+ h", part))), "")
        return sentence(f"The check ran {parts[1]}" + (f" in {took}" if took else ""))
    if re.match(r"New commit\b", text):
        return "The agent made a new commit."
    words = sentence(" · ".join(part for part in parts if clean(part)))
    return words if words and clean(words) and not _WIRE_WORD.search(words) else ""


def changed_lines(rows: Iterable[Mapping[str, Any]], limit: int = 3) -> list[str]:
    out: list[str] = []
    for row in rows:
        line = changed_line(row.get("line"))
        if line and line not in out:
            out.append(line)
        if len(out) >= limit:
            break
    return out


# ── where we are ──────────────────────────────────────────────────────

def blocked_steps(steps: list[Mapping[str, Any]], step: Optional[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The steps that wait on this one (``after``, transitively), not yet
    finished, in plan order."""
    if not step:
        return []
    closed = {"merged", "done"}
    waiting: set[int] = {int(step["ordinal"])}
    found: list[Mapping[str, Any]] = []
    grew = True
    while grew:
        grew = False
        for row in steps:
            ordinal = int(row["ordinal"])
            if row.get("race_of") or ordinal in waiting or row.get("state") in closed:
                continue
            if any(int(value) in waiting for value in row.get("after") or []):
                waiting.add(ordinal)
                found.append(row)
                grew = True
    return sorted(found, key=lambda row: int(row["ordinal"]))


def freed_steps(steps: list[Mapping[str, Any]], step: Optional[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The steps that can start once this one is finished: each waits on it
    and on nothing else that is unfinished."""
    if not step:
        return []
    done = {int(row["ordinal"]) for row in steps if row.get("state") in ("merged", "done")}
    here = int(step["ordinal"])
    return [row for row in steps if not row.get("race_of") and row.get("state") in ("planned", "ready")
            and here in {int(value) for value in row.get("after") or []}
            and all(int(value) in done or int(value) == here for value in row.get("after") or [])]


def blocked_words(blocked: list[Mapping[str, Any]]) -> str:
    """"3 steps wait on this: 4 People routes, 5 The fan-out, 6 Docs"."""
    if not blocked:
        return "Nothing else waits on this."
    names = ", ".join(f"{row['ordinal']} {_squash(row.get('title'))}" for row in blocked[:6])
    more = f" and {len(blocked) - 6} more" if len(blocked) > 6 else ""
    head = "1 step waits on this" if len(blocked) == 1 else f"{len(blocked)} steps wait on this"
    line = f"{head}: {names}{more}."
    return line if clean(line) else f"{head}."


def brief_lines(body: Mapping[str, Any]) -> list[str]:
    """The brief's lines in the package's order: the goal, the step, what
    happened, the question, then what this answer blocks (only when a step
    waits on it). Telegram and the call read these; the page draws the same
    fields in the same order."""
    lines = [str(line) for line in body.get("note") or [] if line]
    lines.append(str(body.get("question") or ""))
    if body.get("blocked"):
        lines.append(str(body.get("blocked_words") or ""))
    return [line for line in lines if line]


# ── the Program window (PG-WINDOW, 2026-10-31) ────────────────────────

def item_brief(program: Mapping[str, Any], steps: list[Mapping[str, Any]], item: Mapping[str, Any]) -> dict[str, Any]:
    """One held item's brief for the Program window, in the briefing page's
    words and order: the goal, what the step was doing, what happened, the
    question, what waits on this answer, and each choice's consequence."""
    top = [row for row in steps if not row.get("race_of")]
    step = next((row for row in steps if row.get("id") == item.get("step_id")), None)
    kind = str(item.get("kind") or "")
    blocked = blocked_steps(top, step)
    freed = freed_steps(top, step)
    others_open = any(row.get("state") not in ("merged", "done", "parked") for row in top
                      if step is None or row.get("id") != step.get("id"))
    rest = rest_words(blocked, others_open)
    consequences = {}
    for choice in item.get("choices") or []:
        said = consequence(kind, str(choice), item, step, rest, len(freed))
        if said:
            consequences[str(choice)] = said
    return {
        "goal": goal_line(program), "doing": doing_words(kind, program, step), "happened": happened_line(kind, item, step),
        "question": question_line(kind, item),
        "blocked": [int(row["ordinal"]) for row in blocked], "blocked_words": blocked_words(blocked) if blocked else "",
        "consequences": consequences,
    }


def step_story(checkpoints: Iterable[Mapping[str, Any]], step_id: Any, limit: int = 3) -> list[dict[str, Any]]:
    """What the agent did on one step: at most ``limit`` plain lines from its
    ledger (newest kept), in the order they happened."""
    out: list[dict[str, Any]] = []
    seen: list[str] = []
    for row in checkpoints:
        if row.get("step_id") != step_id or row.get("kind"):
            continue
        line = changed_line(row.get("line"))
        if not line or line in seen:
            continue
        seen.append(line)
        out.append({"at": row.get("at"), "line": line})
        if len(out) >= limit:
            break
    # Newest first from the store; the same second keeps the store's order.
    return sorted(reversed(out), key=lambda row: str(row.get("at") or ""))


# ── the step report (PG-IMPORT IMP1) ─────────────────────────────────

#: The step states that carry a report (Done, Merged, Parked or Skipped,
#: Failed).
REPORT_STATES = frozenset({"merged", "done", "parked", "failed"})
#: The registers, in the order the face reads them.
REPORT_WORDS = {"observed": "Checked:", "claimed": "The agent says:", "not_checked": "Not checked:",
                "files": "Files:"}
#: At most this many file names; the rest is "and N more".
REPORT_FILES = 12
_REPORT_CLAIMS = 4


def _short(commit: Any) -> str:
    return str(commit or "")[:8]


def _engine_rows(checkpoints: Iterable[Mapping[str, Any]], step_id: Any) -> list[Mapping[str, Any]]:
    """The step's engine checkpoints, oldest first."""
    rows = [row for row in checkpoints if row.get("step_id") == step_id and row.get("by") == "engine"]
    return sorted(rows, key=lambda row: (str(row.get("at") or ""), int(row.get("id") or 0)))


def _cite(rows: list[Mapping[str, Any]], test: Any) -> Optional[Mapping[str, Any]]:
    """The first engine checkpoint whose ``seen`` record passes ``test``."""
    for row in rows:
        seen = (row.get("undo") or {}).get("seen")
        if isinstance(seen, Mapping) and test(seen):
            return row
    return None


def _requirement_cite(rows: list[Mapping[str, Any]], requirement_id: str) -> Optional[Mapping[str, Any]]:
    """The newest engine checkpoint that judged this requirement."""
    found = None
    for row in rows:
        if row.get("kind") != "requirement":
            continue
        undo = row.get("undo") or {}
        if undo.get("requirement_id") == requirement_id or requirement_id in (undo.get("requirement_ids") or []):
            found = row
    return found


def _observed(line: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {"line": line, "checkpoint": row.get("id"), "at": row.get("at")}


def step_report(step: Mapping[str, Any], checkpoints: Iterable[Mapping[str, Any]],
                requirements: Iterable[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """BroCrew's report rule, on our engine: "a finished piece of work comes
    back with its outcome, what was checked, what wasn't, and where the
    files are." Four registers, each built from the step's own fields and
    the ledger's ``by``, never from a line's prose:

    - ``observed`` ("Checked:"): what the engine saw (the commit, the
      check, the PR, the merge, each requirement it judged). Each line cites
      the engine checkpoint that saw it (``seen`` on the checkpoint); a fact
      no engine checkpoint saw is left out.
    - ``claimed`` ("The agent says:"): the agent's own report and its own
      checkpoint lines.
    - ``not_checked`` ("Not checked:"): requirements nobody judged, a
      review that did not run, a gate check that was off.
    - ``files`` ("Files:"): the step's diff file names, bounded.

    ``None`` for a step that is not Done, Merged, Parked or Failed."""
    from .program_requirements import KIND_WORDS, STATE_WORDS, label

    state = str(step.get("state") or "")
    if state not in REPORT_STATES:
        return None
    facts = step.get("facts") or {}
    rows = _engine_rows(checkpoints, step.get("id"))
    observed: list[dict[str, Any]] = []
    head = step.get("head_commit")
    base = facts.get("base_commit")
    if head and head != base:
        row = _cite(rows, lambda seen: seen.get("commit") == head)
        if row is not None:
            observed.append(_observed(f"Commit {_short(head)}", row))
    verdict = str(step.get("check_verdict") or "")
    checked = step.get("checked_commit")
    if verdict and verdict != "none":
        row = _cite(rows, lambda seen: seen.get("check") == verdict and seen.get("checked") == checked)
        if row is not None:
            on = f" on {_short(checked)}" if checked else ""
            observed.append(_observed(f"Check {verdict.replace('_', ' ')}{on}", row))
    number = step.get("pr_number")
    if number:
        row = _cite(rows, lambda seen: seen.get("pr") == number)
        if row is not None:
            observed.append(_observed(f"PR #{number} opened", row))
    if state in ("merged", "done"):
        row = _cite(rows, lambda seen: seen.get("state") in ("merged", "done"))
        if row is not None:
            observed.append(_observed(f"PR #{number} merged" if number else "Merged", row))
    owner_id = step.get("race_of") or step.get("id")
    own = sorted((row for row in requirements if row.get("step_id") == owner_id),
                 key=lambda row: int(row.get("ordinal") or 0))
    not_checked: list[dict[str, Any]] = []
    for req in own:
        name = f"{label(req.get('ordinal'))} {_squash(req.get('text'))}"
        kind = str(req.get("kind") or "")
        req_state = str(req.get("state") or "")
        evidence = req.get("evidence") or {}
        if req_state in ("met", "unmet") and evidence.get("by") == "engine":
            row = _requirement_cite(rows, str(req.get("id")))
            if row is not None:
                value = evidence.get("value")
                unit = str((req.get("spec") or {}).get("unit") or "")
                tail = f" · {value}{(' ' + unit) if unit else ''}" if value is not None else ""
                observed.append(_observed(f"{name} · {STATE_WORDS.get(req_state, req_state)}{tail}", row))
        elif req_state == "waived":
            not_checked.append({"line": f"{name}: waived" + (f" · {_squash(req.get('waived_reason'))}"
                                                             if req.get("waived_reason") else "")})
        elif req_state == "not_yet":
            why = {"word": "nobody judged it", "review": "no review ran"}.get(kind, "it did not run")
            not_checked.append({"line": f"{name}: {why}"})
    if not step.get("gate_check"):
        not_checked.append({"line": "The gate check was off"})
    elif verdict == "none":
        not_checked.append({"line": "No check command ran"})
    elif not verdict:
        not_checked.append({"line": "The check did not run"})
    if step.get("gate_review") in ("agent", "person") and not step.get("review_verdict") \
            and not facts.get("person_approved"):
        not_checked.append({"line": "The review did not run"})
    claimed: list[dict[str, Any]] = []
    seen_lines: list[str] = []
    for raw in str(step.get("report") or "").splitlines():
        text = raw.strip()
        if not text or text.startswith(("#", "```", "|")):
            continue  # a heading, a fence or a table row says nothing plain
        words = first_sentence(scrub(text.lstrip("-*+> ").lstrip("0123456789.) ")), 200)
        if len(words.split()) >= 2 and words not in seen_lines:
            seen_lines.append(words)
            claimed.append({"line": words})
        if len(claimed) >= _REPORT_CLAIMS:
            break
    agent_rows = sorted((row for row in checkpoints if row.get("step_id") == step.get("id")
                         and row.get("by") == "agent" and not row.get("kind")),
                        key=lambda row: (str(row.get("at") or ""), int(row.get("id") or 0)))
    for row in agent_rows:
        words = changed_line(row.get("line"))
        if words and words not in seen_lines and len(claimed) < _REPORT_CLAIMS + 2:
            seen_lines.append(words)
            claimed.append({"line": words, "checkpoint": row.get("id"), "at": row.get("at")})
    files = facts.get("files") if isinstance(facts.get("files"), Mapping) else {}
    names = [str(name) for name in (files.get("names") or [])]
    return {
        "observed": observed, "claimed": claimed, "not_checked": not_checked,
        "files": names[:REPORT_FILES], "files_more": max(0, int(files.get("count") or len(names)) - REPORT_FILES),
        "words": dict(REPORT_WORDS),
    }


def window_words(program: Mapping[str, Any], steps: list[Mapping[str, Any]], turn: Iterable[Mapping[str, Any]],
                 checkpoints: Iterable[Mapping[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """The Program window's words: each held item's brief (by item id) and
    each step's story (by step id). ``checkpoints`` newest first, as the
    store lists them."""
    rows = list(checkpoints)
    briefs = {str(item.get("id")): item_brief(program, steps, item) for item in turn}
    stories = {str(row["id"]): step_story(rows, row["id"]) for row in steps}
    return briefs, stories


# ── the Programs list (PG-WINDOW List, 2026-11-01) ────────────────────

_LIST_RUNNING = frozenset({"briefed", "working", "waiting", "limited", "checking", "check_failed", "review",
                           "findings", "pr_open", "merge_ask"})


def _wall(stamp: Any) -> Optional[Any]:
    from datetime import datetime

    try:
        value = datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return None
    return value.astimezone() if value.tzinfo else value


def _skipped(row: Mapping[str, Any]) -> bool:
    """An owner's Skip: the step is finished without a merge."""
    return "skipped" in str(row.get("parked_reason") or "").lower()


def _done_words(steps: list[Mapping[str, Any]], *, history: Optional[Mapping[str, Any]], done_in: str, ended: Any) -> str:
    """"Done, 14 PRs, 28 Oct", "Done, 3 merges, 1 Nov", "Done, 1 skipped, 31 Oct"."""
    if history and history.get("words"):
        words = str(history["words"]).replace(" · ", ", ")
        return f"Done, {words[:1].lower()}{words[1:]}"
    merged = [row for row in steps if row.get("state") in ("merged", "done")]
    prs = sum(1 for row in merged if row.get("pr_number"))
    skipped = sum(1 for row in steps if row.get("state") == "parked" and _skipped(row))
    day = _wall(ended)
    parts = ["Done",
             f"{prs} {'PR' if prs == 1 else 'PRs'}" if prs else
             (f"{len(merged)} {'merge' if len(merged) == 1 else 'merges'}" if merged else ""),
             f"{skipped} skipped" if skipped else "",
             f"{day.day} {day.strftime('%b')}" if day else ""]
    line = ", ".join(part for part in parts if part)
    return line if line != "Done" else (f"Done in {done_in}" if done_in else "Done")


def _finished(steps: list[Mapping[str, Any]]) -> bool:
    return bool(steps) and all(row.get("state") in ("merged", "done") or (row.get("state") == "parked" and _skipped(row))
                               for row in steps)


def list_track(steps: list[Mapping[str, Any]], turn: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """One mark per step for the list's mini track: ``done``, ``here`` (it
    waits on him), ``running``, ``red``, ``parked``, ``planned``."""
    held = {str(item.get("step_id")) for item in turn if item.get("step_id")}
    out = []
    for row in steps:
        state = str(row.get("state") or "")
        if state in ("merged", "done"):
            mark = "done"
        elif str(row.get("id")) in held:
            mark = "here"
        elif state in ("check_failed", "failed"):
            mark = "red"
        elif state == "parked" and row.get("parked_by") == "owner" and _skipped(row):
            mark = "skipped"
        elif state == "parked":
            mark = "parked"
        elif state in _LIST_RUNNING:
            mark = "running"
        else:
            mark = "planned"
        out.append({"ordinal": int(row["ordinal"]), "title": _squash(row.get("title")), "mark": mark})
    return out


def list_line(state: str, steps: list[Mapping[str, Any]], turn: list[Mapping[str, Any]], *,
              history: Optional[Mapping[str, Any]] = None, done_in: str = "", ended: Any = None) -> str:
    """The Programs list's one line for a program, as a chief of staff says
    it: "Step 2 of 3 waits on you since 21:43", "Runs step 4 of 8, Claude
    Code, 11 min", "Done, 14 PRs, 28 Oct", "Drafting, 8 steps"."""
    from .program_service import agent_label, duration_words

    total = len(steps)
    of = f" of {total}" if total else ""
    if state == "waiting" and turn:
        item = turn[0]
        since = _wall(item.get("since"))
        when = f" since {since.strftime('%H:%M')}" if since else ""
        ordinal = int(item.get("ordinal") or 0)
        # PG-IMPORT IMP2: a held step whose lane failed or was cut off says so.
        held = next((row for row in steps if row.get("id") == item.get("step_id")), None) or {}
        ending = (held.get("facts") or {}).get("ending") if held.get("state") in ("parked", "failed") else None
        tail = f" · {ending}" if ending in ("failed", "interrupted") else ""
        return f"Step {ordinal}{of} waits on you{when}{tail}" if ordinal else f"The program waits on you{when}"
    if state == "running":
        live = next((row for row in steps if row.get("state") in _LIST_RUNNING), None)
        if live is None:
            nxt = next((row for row in steps if row.get("state") in ("planned", "ready")), None)
            return f"Runs, step {int(nxt['ordinal'])}{of} is next" if nxt else "Runs"
        started = _wall(live.get("started_at"))
        took = ""
        if started:
            from datetime import datetime

            took = duration_words(int((datetime.now(started.tzinfo) - started).total_seconds()))
        parts = [f"Runs step {int(live['ordinal'])}{of}", agent_label(live.get("profile")), took]
        return ", ".join(part for part in parts if part)
    if state == "drafting":
        return f"Drafting, {total} {'step' if total == 1 else 'steps'}" if total else "Drafting, no steps yet"
    if state == "done":
        return _done_words(steps, history=history, done_in=done_in, ended=ended)
    if state == "parked" and _finished(steps):
        # Done is a fact parking does not erase (owner catch 2026-11-01).
        return f"{_done_words(steps, history=history, done_in=done_in, ended=ended)} · parked"
    if state in ("parked", "failed"):
        stopped = next((row for row in steps if row.get("state") in ("parked", "failed", "check_failed")), None)
        word = "Parked" if state == "parked" else "Failed"
        if not stopped:
            return word
        # PG-IMPORT IMP2: how its lane ended, beside the state.
        ending = (stopped.get("facts") or {}).get("ending")
        return f"{word} at step {int(stopped['ordinal'])}{of}" + (f" · {ending}" if ending in ("failed", "interrupted") else "")
    return ""


__all__ = ["brief_lines", "blocked_steps", "blocked_words", "changed_line", "changed_lines", "clean", "consequence", "doing_line",
           "delivery_where", "doing_words", "fence_hits", "first_sentence", "goal_line", "list_line", "list_track", "happened_line", "item_brief", "step_story", "window_words", "parked_cause", "question_line",
           "rest_words", "scrub", "sentence", "settle_words", "step_report", "waits_words"]
