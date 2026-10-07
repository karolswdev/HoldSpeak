"""The rules a held Bash call is read against (Conductor K5).

docs/internal/CONDUCTOR.md, "The Control-mode mapping" (owner ruling
2026-10-06). The tool gate decides a held call of a HoldSpeak-launched agent
by the current Control mode:

- **Secure**: every call waits for the owner.
- **Normal**: a short list of read and test commands passes
  (``git status|diff|log|show``, the read forms of ``git branch``, ``ls``,
  ``cat``, ``rg``, ``grep``, ``pytest``, ``uv run pytest``, ``npm test``,
  ``npx vitest run`` and a few more); the rest waits.
- **YOLO**: a call passes when its working folder and every path it names
  are in the agent's own worktree; the rest waits.

This module reads ONE command. It runs in the agent-side hook
(:func:`holdspeak.coder_gate.run_hook`), so the full command never leaves the
agent process: the hub receives the verdict (:class:`BashCall`), never the
command. The reading is conservative. A construct it does not read (command
substitution, a variable, a subshell, an unquoted here-document, ``bash -c``,
``eval``, inline code) makes the call ``unparsed``, and an unparsed call waits
in every mode. The verdict is mode-independent; the hub's policy
(``operation_policy.resolve_policy``, family ``tool_gate``) applies the mode.
"""
from __future__ import annotations

import os
import re
import shlex
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

INSIDE = "inside"
OUTSIDE = "outside"
UNPARSED = "unparsed"
SCOPES = frozenset({INSIDE, OUTSIDE, UNPARSED})

#: Paths outside the worktree that a call may still name (no effect).
_HARMLESS_PATHS = frozenset({"/dev/null", "/dev/stdout", "/dev/stderr"})

_SEPARATORS = frozenset({";", "&&", "||", "|", "&", "|&"})
_WRITE_REDIRECTS = frozenset({">", ">>", "&>", "&>>", ">|", "<>"})
_READ_REDIRECTS = frozenset({"<"})
_FD_DUPS = frozenset({">&", "<&"})

_SHELLS = frozenset({"sh", "bash", "zsh", "dash", "ksh", "fish", "csh", "tcsh"})
_INLINE_CODE = {
    "python": ("-c",), "python3": ("-c",), "node": ("-e", "--eval", "-p", "--print"),
    "perl": ("-e", "-E"), "ruby": ("-e",), "php": ("-r",), "deno": ("eval",),
}
#: Commands that run another command HoldSpeak cannot read here.
_INDIRECT = frozenset({
    "eval", "exec", "sudo", "su", "doas", "xargs", "env", "nohup", "command",
    "builtin", "time", "nice", "timeout", "watch", "parallel", "ssh", "script",
})

#: Normal mode: read commands (no write effect by themselves).
_READ_COMMANDS = frozenset({
    "ls", "cat", "head", "tail", "wc", "rg", "grep", "pwd", "tree", "stat",
    "file", "diff", "echo", "true", "which",
})
_GIT_READ = frozenset({"status", "diff", "log", "show", "rev-parse", "ls-files", "blame"})
_GIT_BRANCH_READ_FLAGS = frozenset({
    "-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "-l", "--list",
    "--show-current", "--merged", "--no-merged", "--contains", "--no-color", "--color",
})
_FIND_ACTIONS = frozenset({
    "-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0",
    "-fprintf", "-fls",
})
#: What a command word runs (Astra round 2 on #904): a bash builtin (a bare
#: name bash runs itself, whatever the PATH holds), a SYSTEM program (a bare
#: name the PATH resolves outside the worktree), or anything else: a path the
#: call names, a bare name the PATH resolves into the worktree (shadowed), or
#: no program at all. Only a builtin or a system program earns read authority
#: or the cd/git/find readings; anything else is a plain worktree program.
BUILTIN, SYSTEM, OTHER = "builtin", "system", "other"
_BUILTINS = frozenset({"cd", "pushd", "popd", "echo", "pwd", "true", "false", "printf", "test", "[", ":"})
#: Builtins that change how later words resolve (PATH, aliases, builtins).
_SHELL_STATE = frozenset({
    "export", "unset", "alias", "unalias", "hash", "enable", "set", "shopt",
    "declare", "typeset", "readonly", "local", "trap", "source", ".",
})

#: find actions that run another command.
_FIND_RUNS = frozenset({"-exec", "-execdir", "-ok", "-okdir"})
_UV_VALUE_FLAGS = frozenset({
    "--extra", "--with", "--group", "--project", "--python", "-p", "--package",
    "--env-file", "--directory", "--only-group", "--with-requirements",
})

#: YOLO: git verbs that change state shared with the main clone (refs,
#: config, other worktrees), so they are not "inside the own worktree".
_GIT_SHARED_WRITE = {
    "branch": frozenset({"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy", "-f", "--force"}),
    "tag": frozenset({"-d", "--delete", "-f", "--force"}),
}
_GIT_SHARED_ALWAYS = frozenset({"update-ref", "reflog", "gc", "prune", "filter-branch", "replace"})
_GIT_REMOTE_READ = frozenset({"", "-v", "--verbose", "show", "get-url"})
_GIT_CONFIG_READ = frozenset({"--get", "--get-all", "--get-regexp", "--list", "-l"})
_GIT_PUSH_FLAGS = frozenset({"-u", "--set-upstream", "-q", "--quiet", "-v", "--verbose", "--porcelain", "--no-verify"})

_ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_REMOTE = re.compile(r"^[^/\s]+@[^/\s]+:")
_DIGITS = re.compile(r"^[0-9]+$")
#: The commit-message form Claude Code writes: "$(cat <<'EOF' ... EOF)". A
#: quoted delimiter means no expansion inside, so the body is plain text.
_HEREDOC_OPEN = re.compile(
    r"\$\(\s*cat\s+<<(?P<dash>-?)\s*(['\"])(?P<tag>[A-Za-z_][A-Za-z0-9_]*)\2[ \t]*\n"
)
_HEREDOC_CLOSE = re.compile(r"\s*\)")


@dataclass(frozen=True)
class BashCall:
    """The mode-independent verdict on one call. ``scope`` is ``inside``
    (the working folder and every named path are in ``root``), ``outside``
    or ``unparsed``; ``rule`` names what decided it. ``read_rule`` names the
    Normal-mode read/test rule the whole call matches (empty when none).
    ``push_branch`` is the one branch a ``git push`` names; the hub compares
    it with the launch's own branch."""

    scope: str
    rule: str
    read_rule: str = ""
    push_branch: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class _Unparsed(Exception):
    def __init__(self, rule: str) -> None:
        super().__init__(rule)
        self.rule = rule


class _Outside(Exception):
    def __init__(self, rule: str) -> None:
        super().__init__(rule)
        self.rule = rule


def classify_tool_call(
    tool: str, tool_input: Optional[Mapping[str, Any]], *, cwd: str, root: Optional[str],
) -> BashCall:
    """The verdict for one held tool call. Only Bash is read; any other tool
    is ``unparsed`` (it waits). ``root`` is the armed worktree the call's
    working folder is in (``None``: in no armed path)."""
    if tool != "Bash":
        return BashCall(UNPARSED, "tool_not_bash")
    command = (tool_input or {}).get("command")
    if not isinstance(command, str):
        return BashCall(UNPARSED, "no_command")
    if not root:
        return BashCall(OUTSIDE, "cwd_outside_armed_path")
    return classify_bash(command, cwd=cwd, root=root)


def classify_bash(command: str, *, cwd: str, root: str) -> BashCall:
    """Read one Bash command against the worktree ``root``."""
    try:
        real_root = os.path.realpath(root)
        real_cwd = os.path.realpath(cwd or root)
        if not _inside(real_cwd, real_root):
            return BashCall(OUTSIDE, "cwd_outside_worktree")
        # Read on the ORIGINAL command: no here-document replacement first.
        activate = _venv_activate(command, cwd=real_cwd, root=real_root)
        if activate is not None:
            return activate
        reader = _Reader(real_root, real_cwd)
        segments = _segments(_tokens(command, cat_is_system=reader.identity("cat") == SYSTEM))
        return reader.read(segments)
    except _Unparsed as exc:
        return BashCall(UNPARSED, exc.rule)
    except _Outside as exc:
        return BashCall(OUTSIDE, exc.rule)
    except ValueError:  # shlex: an unclosed quote
        return BashCall(UNPARSED, "unbalanced_quotes")


#: Conductor R5 (Astra round 1 on #915): the whole command is one plain
#: ``source <path>`` or ``. <path>``. The target is plain characters only: no
#: quote, ``$``, backquote, backslash, glob (``[ * ? {``), ``~`` or newline, so
#: bash reads exactly the text checked here. It must hold a slash, or bash
#: would look for it on the PATH first.
_ACTIVATE = re.compile(r"\A[ \t]*(?:source|\.)[ \t]+(?P<target>[A-Za-z0-9._/+@,=-]+)[ \t]*;?[ \t]*\Z")


def _venv_activate(command: str, *, cwd: str, root: str) -> Optional[BashCall]:
    """``source <path>`` or ``. <path>`` alone, where the plain <path> holds a
    slash and resolves (symlinks followed) inside the worktree to a file named
    ``activate`` in a ``bin/`` folder of a Python venv (``pyvenv.cfg`` two
    levels up). Such a call is ``inside`` with no read rule, so YOLO passes it
    and Normal and Secure hold it. Anything else is left to the reader, which
    keeps ``source`` and ``.`` unparsed."""
    match = _ACTIVATE.match(command)
    if match is None:
        return None
    target = match.group("target")
    if "/" not in target or target.startswith("-"):
        return None
    real = os.path.realpath(os.path.join(cwd, target))
    if not _inside(real, root) or not os.path.isfile(real):
        return None
    bin_dir = os.path.dirname(real)
    venv = os.path.dirname(bin_dir)
    if os.path.basename(real) != "activate" or os.path.basename(bin_dir) != "bin":
        return None
    if not _inside(venv, root) or not os.path.isfile(os.path.join(venv, "pyvenv.cfg")):
        return None
    return BashCall(INSIDE, "venv_activate")


# ── lexing ─────────────────────────────────────────────────────────────


def _prepare(command: str, *, cat_is_system: bool = True) -> str:
    """Replace quoted here-document bodies with plain text, refuse every
    construct that expands at run time, and turn unquoted newlines into
    ``;`` (each line is its own command)."""
    text = _quoted_heredocs(command, cat_is_system=cat_is_system)
    out: list[str] = []
    quote = ""
    index = 0
    while index < len(text):
        char = text[index]
        if quote == "'":
            if char == "'":
                quote = ""
            out.append(char)
        elif char == "\\" and index + 1 < len(text):
            nxt = text[index + 1]
            if nxt == "\n":
                out.append(" ")  # a line continuation
            else:
                out.append(char + nxt)
            index += 2
            continue
        elif quote == '"':
            if char == '"':
                quote = ""
            elif char in "$`":
                raise _Unparsed("shell_expansion")
            out.append(char)
        else:
            if char in "'\"":
                quote = char
            elif char in "$`":
                raise _Unparsed("shell_expansion")
            elif char in "(){}":
                raise _Unparsed("subshell_or_group")
            elif char == "\n":
                out.append(" ; ")
                index += 1
                continue
            elif text.startswith("<<", index):
                raise _Unparsed("here_document")
            out.append(char)
        index += 1
    if quote:
        raise _Unparsed("unbalanced_quotes")
    return "".join(out)


def _quoted_heredocs(command: str, *, cat_is_system: bool = True) -> str:
    """Replace each ``$(cat <<'TAG' ... TAG)`` with plain text. The body
    ends at the FIRST line that is exactly ``TAG`` (as bash reads it), and
    the substitution must close right there: anything between that line and
    ``)`` would run, so the call is unparsed."""
    out: list[str] = []
    pos = 0
    while True:
        opened = _HEREDOC_OPEN.search(command, pos)
        if opened is None:
            out.append(command[pos:])
            return "".join(out)
        if not cat_is_system:
            # The substitution runs ``cat``: only the system cat makes it text.
            raise _Unparsed("heredoc_cat_not_system")
        tag, dash = opened.group("tag"), bool(opened.group("dash"))
        index = opened.end()
        while True:
            newline = command.find("\n", index)
            line = command[index: newline if newline >= 0 else len(command)]
            if (line.lstrip("\t") if dash else line) == tag:
                end = newline if newline >= 0 else len(command)
                break
            if newline < 0:
                raise _Unparsed("here_document")
            index = newline + 1
        closed = _HEREDOC_CLOSE.match(command, end)
        if closed is None:
            raise _Unparsed("here_document")
        out.append(command[pos:opened.start()])
        out.append("HEREDOC_TEXT")
        pos = closed.end()


def _tokens(command: str, *, cat_is_system: bool = True) -> list[tuple[str, bool]]:
    """``(token, is_operator)`` pairs. Quoted text is never an operator."""
    lexer = shlex.shlex(_prepare(command, cat_is_system=cat_is_system), posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    result: list[tuple[str, bool]] = []
    for token in lexer:
        is_op = bool(token) and all(ch in ";&|<>" for ch in token)
        result.append((token, is_op))
    return result


def _segments(tokens: list[tuple[str, bool]]) -> list[tuple[str, list[str], list[tuple[str, str]]]]:
    """Simple commands: ``(joined_by, words, redirects)``. ``joined_by`` is
    the operator before the command (``|`` marks a pipe reader)."""
    segments: list[tuple[str, list[str], list[tuple[str, str]]]] = []
    words: list[str] = []
    redirects: list[tuple[str, str]] = []
    joined = ""
    index = 0
    while index < len(tokens):
        token, is_op = tokens[index]
        if not is_op:
            words.append(token)
            index += 1
            continue
        if token in _SEPARATORS:
            if words or redirects:
                segments.append((joined, words, redirects))
            elif token != "&" and segments:
                raise _Unparsed("empty_command")
            words, redirects, joined = [], [], token
            index += 1
            continue
        if token in _WRITE_REDIRECTS or token in _READ_REDIRECTS or token in _FD_DUPS:
            if index + 1 >= len(tokens) or tokens[index + 1][1]:
                raise _Unparsed("redirect_without_target")
            target = tokens[index + 1][0]
            if words and _DIGITS.match(words[-1]):
                words.pop()  # a file descriptor number (2>, 1>>)
            if token in _FD_DUPS:
                if not _DIGITS.match(target) and target != "-":
                    raise _Unparsed("redirect_dup")
            else:
                redirects.append((token, target))
            index += 2
            continue
        raise _Unparsed("operator_unknown")
    if words or redirects:
        segments.append((joined, words, redirects))
    if not segments:
        raise _Unparsed("empty_command")
    return segments


# ── reading ────────────────────────────────────────────────────────────


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


class _Reader:
    def __init__(self, root: str, cwd: str) -> None:
        self.root = root
        self.cwd = cwd
        self.read_rules: list[str] = []
        self.all_read = True
        self.push_branch = ""
        self.rules: list[str] = []

    def read(self, segments: list[tuple[str, list[str], list[tuple[str, str]]]]) -> BashCall:
        for joined, words, redirects in segments:
            self._segment(joined, words, redirects)
        rule = self.rules[-1] if self.push_branch else "in_worktree"
        read_rule = "+".join(dict.fromkeys(self.read_rules)) if self.all_read else ""
        return BashCall(INSIDE, rule, read_rule=read_rule, push_branch=self.push_branch)

    # one simple command -----------------------------------------------------

    def _segment(self, joined: str, words: list[str], redirects: list[tuple[str, str]]) -> None:
        for op, target in redirects:
            self._path(target, cwd=self.cwd, rule="redirect_outside_worktree")
            if op in _WRITE_REDIRECTS and os.path.realpath(
                os.path.join(self.cwd, target)
            ) not in _HARMLESS_PATHS:
                self.all_read = False  # a write is never a Normal read
        words = list(words)
        while words and _ENV_ASSIGN.match(words[0]):
            assignment = words.pop(0)
            if assignment.split("=", 1)[0] == "PATH":
                raise _Unparsed("path_change")  # the program would resolve elsewhere
            value = assignment.split("=", 1)[1]
            if _looks_like_path(value):
                self._path(value, cwd=self.cwd, rule="env_path_outside_worktree")
            self.all_read = False
        if not words:
            return
        name = words[0]
        base = os.path.basename(name)
        if "/" in name:
            self._path(name, cwd=self.cwd, rule="program_outside_worktree")
        if joined in ("|", "|&") and base in _SHELLS:
            raise _Unparsed("pipe_to_shell")
        if base in _SHELLS and any(w == "-c" or (w.startswith("-") and not w.startswith("--") and "c" in w[1:]) for w in words[1:]):
            raise _Unparsed("shell_c")
        if base in _INDIRECT:
            raise _Unparsed(f"indirect_{base}")
        if base in _INLINE_CODE and any(w in _INLINE_CODE[base] for w in words[1:]):
            raise _Unparsed("inline_code")
        if base == "find" and any(w in _FIND_RUNS for w in words[1:]):
            raise _Unparsed("indirect_find_exec")  # it runs a command this reading cannot see
        if name in _SHELL_STATE:
            raise _Unparsed("shell_state_change")
        # Identity first: no special reading and no read authority for a
        # program that is not the builtin or the system program it is named
        # after. A path-invoked ``./cd`` cannot move the shell's cwd.
        identity = self.identity(name)
        if identity == BUILTIN and name in ("cd", "pushd"):
            self._cd(words[1:])
            self.read_rules.append("cd")
            return
        if identity == SYSTEM and name == "git":
            self._git(words[1:])
            return
        self._args(words[1:], cwd=self.cwd)
        read = _read_rule(name, words[1:]) if identity in (BUILTIN, SYSTEM) else ""
        if read:
            self.read_rules.append(read)
        else:
            self.all_read = False

    def identity(self, name: str) -> str:
        """``builtin`` | ``system`` | ``other`` for one command word."""
        if "/" in name or not name:
            return OTHER
        if name in _BUILTINS:
            return BUILTIN
        found = self._which(name)
        if found is None:
            return OTHER
        return OTHER if _inside(found, self.root) else SYSTEM

    def _which(self, name: str) -> Optional[str]:
        """The PATH lookup bash makes, with relative PATH entries (``.``,
        ``""``, ``bin``) read from the call's working folder."""
        for entry in (os.environ.get("PATH") or "").split(os.pathsep):
            folder = entry or "."
            if not os.path.isabs(folder):
                folder = os.path.join(self.cwd, folder)
            candidate = os.path.join(folder, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return os.path.realpath(candidate)
        return None

    def _cd(self, args: list[str]) -> None:
        targets = [a for a in args if not a.startswith("-")]
        if len(targets) != 1 or targets[0] == "-":
            raise _Outside("cd_outside_worktree") if not targets else _Unparsed("cd_form")
        target = targets[0]
        if target.startswith("~"):
            raise _Outside("cd_outside_worktree")
        new = os.path.realpath(os.path.join(self.cwd, target))
        if not _inside(new, self.root):
            raise _Outside("cd_outside_worktree")
        self.cwd = new

    def _git(self, args: list[str]) -> None:
        cwd = self.cwd
        index = 0
        # Global options before the verb.
        while index < len(args) and args[index].startswith("-"):
            option = args[index]
            if option == "-C":
                if index + 1 >= len(args):
                    raise _Unparsed("git_form")
                target = args[index + 1]
                self._path(target, cwd=cwd, rule="git_outside_worktree")
                cwd = os.path.realpath(os.path.join(cwd, target))
                index += 2
                continue
            if option == "-c":
                setting = args[index + 1] if index + 1 < len(args) else ""
                value = setting.split("=", 1)[1] if "=" in setting else ""
                if _looks_like_path(value):
                    self._path(value, cwd=cwd, rule="git_outside_worktree")
                index += 2
                self.all_read = False
                continue
            if "=" in option:
                self._path(option.split("=", 1)[1], cwd=cwd, rule="git_outside_worktree")
            index += 1
        if index >= len(args):
            self.read_rules.append("git")
            return
        verb, rest = args[index], args[index + 1:]
        if verb == "push":
            self._push(rest)
            self.all_read = False
            return
        if verb in _GIT_SHARED_ALWAYS:
            raise _Outside("git_shared_state")
        shared = _GIT_SHARED_WRITE.get(verb)
        if shared and any(flag in shared for flag in rest):
            raise _Outside("git_shared_state")
        if verb == "worktree" and (rest[:1] or [""])[0] != "list":
            raise _Outside("git_shared_state")
        if verb == "remote" and (rest[:1] or [""])[0] not in _GIT_REMOTE_READ:
            raise _Outside("git_shared_state")
        if verb == "config" and not any(flag in _GIT_CONFIG_READ for flag in rest):
            raise _Outside("git_shared_state")
        self._args(rest, cwd=cwd)
        if verb in _GIT_READ and not any(a.startswith("--output") for a in rest):
            self.read_rules.append(f"git-{verb}")
        elif verb == "branch" and all(a in _GIT_BRANCH_READ_FLAGS for a in rest):
            self.read_rules.append("git-branch")
        else:
            self.all_read = False

    def _push(self, args: list[str]) -> None:
        positional = []
        for arg in args:
            if arg.startswith("-"):
                if arg not in _GIT_PUSH_FLAGS:
                    raise _Outside("git_push_unbound")
                continue
            positional.append(arg)
        if len(positional) != 2 or positional[0] != "origin":
            raise _Outside("git_push_unbound")
        spec = positional[1]
        if spec.startswith("+") or spec.startswith(":"):
            raise _Outside("git_push_unbound")
        source, _, dest = spec.partition(":")
        branch = dest or source
        if dest and source not in ("HEAD", dest, f"refs/heads/{dest}"):
            raise _Outside("git_push_unbound")
        branch = branch.removeprefix("refs/heads/")
        if not branch or branch == "HEAD":
            raise _Outside("git_push_unbound")
        if self.push_branch and self.push_branch != branch:
            raise _Outside("git_push_unbound")
        self.push_branch = branch
        self.rules.append("git_push_launch_branch")

    def _args(self, args: list[str], *, cwd: str) -> None:
        for arg in args:
            if arg.startswith("-") and arg != "-":
                value = ""
                if "=" in arg:
                    value = arg.split("=", 1)[1]
                elif not arg.startswith("--") and len(arg) > 2:
                    value = arg[2:]
                if value and _looks_like_path(value):
                    self._path(value, cwd=cwd, rule="path_outside_worktree")
                continue
            self._path(arg, cwd=cwd, rule="path_outside_worktree")

    def _path(self, word: str, *, cwd: str, rule: str) -> None:
        if not word or word == "-":
            return
        if _URL.match(word) or _REMOTE.match(word):
            raise _Outside("network_target")
        if word.startswith("~"):
            raise _Outside(rule)
        real = os.path.realpath(os.path.join(cwd, word))
        if real in _HARMLESS_PATHS or word in _HARMLESS_PATHS:
            return
        if not _inside(real, self.root):
            raise _Outside(rule)


def _looks_like_path(value: str) -> bool:
    return "/" in value or value.startswith("~") or value.startswith("..") or value == "."


def _read_rule(base: str, args: list[str]) -> str:
    """The Normal-mode read/test rule this simple command matches, or ``""``."""
    if base in _READ_COMMANDS:
        return base
    if base == "find":
        return "" if any(a in _FIND_ACTIONS for a in args) else "find"
    if base == "pytest":
        return "pytest"
    if base in ("python", "python3") and args[:2] == ["-m", "pytest"]:
        return "pytest"
    if base == "uv" and args[:1] == ["run"]:
        rest = args[1:]
        index = 0
        while index < len(rest) and rest[index].startswith("-"):
            index += 2 if rest[index] in _UV_VALUE_FLAGS else 1
        tail = rest[index:]
        if tail[:1] == ["pytest"] or tail[:3] in (["python", "-m", "pytest"], ["python3", "-m", "pytest"]):
            return "uv-run-pytest"
        return ""
    if base == "npm" and (args[:1] == ["test"] or args[:2] == ["run", "test"]):
        return "npm-test"
    if base == "npx" and args[:2] == ["vitest", "run"]:
        return "vitest-run"
    return ""


def classification_from_wire(raw: Any) -> Optional[dict[str, str]]:
    """The verdict as the hub accepts it from the hook: known keys, known
    scope, short strings. Anything else is ``None`` (the call waits)."""
    if not isinstance(raw, Mapping):
        return None
    scope = str(raw.get("scope") or "")
    if scope not in SCOPES:
        return None
    clean: dict[str, str] = {"scope": scope}
    for key in ("rule", "read_rule", "push_branch", "root", "proposal_id", "args_sha256"):
        value = raw.get(key)
        if value is None:
            value = ""
        if not isinstance(value, str) or len(value) > 512:
            return None
        clean[key] = value
    return clean


__all__ = [
    "BashCall",
    "INSIDE",
    "OUTSIDE",
    "SCOPES",
    "UNPARSED",
    "classification_from_wire",
    "classify_bash",
    "classify_tool_call",
]
