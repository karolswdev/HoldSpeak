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

#: git verbs this reading knows (Astra round 1 on #914). Any other verb may
#: be an alias (``git -c alias.x=push x``, or one in a config file), so it
#: is held as unparsed. Git never lets an alias shadow a built-in verb.
_GIT_KNOWN_VERBS = frozenset({
    "add", "am", "apply", "archive", "bisect", "blame", "branch", "cat-file", "checkout",
    "cherry-pick", "clean", "clone", "commit", "config", "describe", "diff", "fetch",
    "for-each-ref", "format-patch", "gc", "grep", "help", "init", "log", "ls-files",
    "ls-remote", "ls-tree", "merge", "merge-base", "mv", "name-rev", "notes", "prune",
    "pull", "push", "range-diff", "rebase", "reflog", "remote", "replace", "reset",
    "restore", "rev-list", "rev-parse", "revert", "rm", "shortlog", "show", "show-ref",
    "stash", "status", "submodule", "switch", "tag", "update-ref", "version", "worktree",
    "filter-branch",
})
#: git options before the verb that change nothing this reading relies on.
_GIT_PLAIN_GLOBALS = frozenset({"--no-pager", "-P", "--no-optional-locks"})
#: Programs whose arguments are network destinations (a schemeless
#: ``example.test`` or ``host:22`` too): a call to one is outside.
_NETWORK_CLIENTS = frozenset({
    "curl", "wget", "nc", "ncat", "netcat", "socat", "telnet", "ftp", "sftp", "scp",
    "rsync", "http", "https", "httpie", "xh", "aria2c", "lynx", "links", "w3m", "ssh",
    "mosh", "openssl",
})
#: ``python -m <module>`` forms that open network connections.
_NETWORK_MODULES = ("http", "urllib", "ftplib", "smtplib", "xmlrpc", "socketserver", "telnetlib", "pip")
_HOST_PORT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]*:[0-9]+(/.*)?$")

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


#: Claude Code's file-writing tools (Conductor R1). A launch's per-launch
#: settings put them on the gate: ``acceptEdits`` also accepts edits in
#: Claude's other allowed folders, so the gate keeps them to the worktree.
EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
#: The rule of a file write inside the launch's own worktree.
EDIT_INSIDE_RULE = "edit_in_worktree"


def _real_target(path: str) -> str:
    """The path a write lands on: every symlink resolved, also for a target
    that does not exist yet (its nearest existing folder is resolved and
    the rest of the path joined to it)."""
    absolute = os.path.abspath(path)
    tail: list[str] = []
    probe = absolute
    while not os.path.lexists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        tail.append(os.path.basename(probe))
        probe = parent
    resolved = os.path.realpath(probe)
    for part in reversed(tail):
        if part in ("", ".", ".."):
            raise _Outside("edit_path_not_plain")
        resolved = os.path.join(resolved, part)
    return resolved


def classify_edit(tool_input: Optional[Mapping[str, Any]], *, cwd: str, root: str) -> BashCall:
    """Read one file write against the worktree ``root``: inside only when
    the resolved target is in the resolved worktree."""
    raw = tool_input or {}
    target = raw.get("file_path") or raw.get("notebook_path")
    if not isinstance(target, str) or not target.strip():
        return BashCall(UNPARSED, "no_file_path")
    try:
        real_root = os.path.realpath(root)
        joined = target if os.path.isabs(target) else os.path.join(cwd or root, target)
        real = _real_target(joined)
    except _Outside as exc:
        return BashCall(OUTSIDE, exc.rule)
    except (OSError, ValueError):
        return BashCall(UNPARSED, "edit_path_unreadable")
    if not _inside(real, real_root):
        return BashCall(OUTSIDE, "edit_outside_worktree")
    return BashCall(INSIDE, EDIT_INSIDE_RULE)


def classify_tool_call(
    tool: str, tool_input: Optional[Mapping[str, Any]], *, cwd: str, root: Optional[str],
) -> BashCall:
    """The verdict for one held tool call. Bash and the file-writing tools
    are read; any other tool is ``unparsed`` (it waits). ``root`` is the
    armed worktree the call's working folder is in (``None``: in no armed
    path)."""
    if tool in EDIT_TOOLS:
        if not root:
            return BashCall(OUTSIDE, "cwd_outside_armed_path")
        return classify_edit(tool_input, cwd=cwd, root=root)
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
        segments = _segments(_tokens(
            command, cat_is_system=reader.identity("cat") == SYSTEM, bodies=reader.heredocs,
        ))
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


def _prepare(command: str, *, cat_is_system: bool = True, bodies: Optional[list[str]] = None) -> str:
    """Replace quoted here-document bodies with plain text, refuse every
    construct that expands at run time, and turn unquoted newlines into
    ``;`` (each line is its own command)."""
    text = _quoted_heredocs(command, cat_is_system=cat_is_system, bodies=bodies)
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


def _quoted_heredocs(command: str, *, cat_is_system: bool = True, bodies: Optional[list[str]] = None) -> str:
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
        # The body is plain text; its placeholder keeps it for the readers
        # that look at a message (a closing keyword, R3).
        if bodies is not None:
            bodies.append(command[opened.end():end])
            out.append(f"HEREDOC_TEXT_{len(bodies) - 1}")
        else:
            out.append("HEREDOC_TEXT")
        pos = closed.end()


def _tokens(
    command: str, *, cat_is_system: bool = True, bodies: Optional[list[str]] = None,
) -> list[tuple[str, bool]]:
    """``(token, is_operator)`` pairs. Quoted text is never an operator."""
    lexer = shlex.shlex(
        _prepare(command, cat_is_system=cat_is_system, bodies=bodies), posix=True, punctuation_chars=";&|<>",
    )
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
        self.heredocs: list[str] = []

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
            if assignment.split("=", 1)[0].startswith("GIT_"):
                raise _Unparsed("git_env")  # GIT_CONFIG_*, GIT_DIR ... change what git runs
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
        if base == "gh":
            self._gh(words[1:])
        if base in _NETWORK_CLIENTS:
            raise _Outside("network_client")
        if base.startswith("python") and len(words) > 2 and words[1] == "-m" and (
            words[2].split(".")[0] in _NETWORK_MODULES
        ):
            raise _Outside("network_client")
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
            if option in _GIT_PLAIN_GLOBALS:
                index += 1
                continue
            # -c, --config-env, --git-dir, --exec-path ...: a config override
            # can define an alias or a command; it is held, never read.
            raise _Unparsed("git_global_option")
        if index >= len(args):
            self.read_rules.append("git")
            return
        verb, rest = args[index], args[index + 1:]
        if verb not in _GIT_KNOWN_VERBS:
            raise _Unparsed("git_unknown_verb")
        if verb == "commit":
            self._commit_message(rest, cwd=cwd)
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

    def _gh(self, args: list[str]) -> None:
        """``gh``: its global flags may come first (``-R o/r``, ``--repo``,
        ``--hostname``). Only the forms below run in the agent's own
        right; any other ``gh`` call (``issue close``, ``pr merge``, ``api``
        ...) acts on GitHub for the owner, so it is outside. A PR's title,
        body or body file must not close an issue (``pr_close_keyword``)."""
        positional: list[str] = []
        index = 0
        while index < len(args):
            arg = args[index]
            if arg in _GH_VALUE_FLAGS:
                index += 2
                continue
            if arg.startswith("-"):
                index += 1
                continue
            positional.append(arg)
            index += 1
            if len(positional) == 2:
                break
        form = tuple(positional[:2])
        if form not in _GH_ALLOWED:
            raise _Outside("gh_effect")
        if form in (("pr", "create"), ("pr", "edit")):
            if any(a in ("-T", "--template") or a.startswith("--template=") for a in args):
                raise _Unparsed("message_source_unread")  # the body comes from a template
            self._close_check(args, _GH_MESSAGE_FLAGS, _GH_MESSAGE_FILE_FLAGS, cwd=self.cwd)

    def _commit_message(self, args: list[str], *, cwd: str) -> None:
        """Every message source of ``git commit``: ``-m``/``--message`` and
        ``--trailer`` text, ``-F``/``--file`` read from the worktree. Git
        takes any unambiguous prefix of a long option (``--mess``); an
        ambiguous one, or a message taken from elsewhere (``-C``, ``-c``,
        ``-t``, ``--reuse-message``, ``--fixup`` ...), holds."""
        texts: list[str] = []
        index = 0
        while index < len(args):
            arg = args[index]
            nxt = args[index + 1] if index + 1 < len(args) else None
            if arg == "--":
                break
            if arg.startswith("--"):
                name, eq, value = arg[2:].partition("=")
                option = _git_long_option(name, _GIT_COMMIT_LONG)
                if option is None:
                    raise _Unparsed("git_option_ambiguous")
                if option in _GIT_COMMIT_MESSAGE_ELSEWHERE:
                    raise _Unparsed("message_source_unread")
                if option in _GIT_COMMIT_VALUE_LONG and not eq:
                    if nxt is None:
                        raise _Unparsed("git_form")
                    value = nxt
                    index += 1
                if option in ("message", "trailer"):
                    texts.append(value)
                elif option == "file":
                    texts.append(self._message_file(value, cwd=cwd))
            elif arg.startswith("-") and len(arg) > 1:
                for pos, char in enumerate(arg[1:], start=1):
                    if char in _GIT_COMMIT_MESSAGE_ELSEWHERE_SHORT:
                        raise _Unparsed("message_source_unread")
                    if char in "mF":
                        value = arg[pos + 1:]
                        if not value:
                            if nxt is None:
                                raise _Unparsed("git_form")
                            value = nxt
                            index += 1
                        texts.append(value if char == "m" else self._message_file(value, cwd=cwd))
                        break
                    if char in "Su":
                        break  # an optional value attached to it: the rest of the word
            index += 1
        if any(_closes_issue(self._expand(text)) for text in texts):
            raise _Unparsed("pr_close_keyword")

    def _close_check(
        self, args: list[str], text_flags: frozenset[str], file_flags: frozenset[str], *, cwd: str,
    ) -> None:
        """Hold a message that would close a GitHub issue (a closing keyword
        and an issue reference): GitHub closes it on merge, an external
        effect the owner decides. A message file in the worktree is read; one
        that cannot be read holds."""
        for flag, value in _flag_values(args, text_flags | file_flags):
            if flag in file_flags:
                value = self._message_file(value, cwd=cwd)
            if _closes_issue(self._expand(value)):
                raise _Unparsed("pr_close_keyword")

    def _expand(self, text: str) -> str:
        return _HEREDOC_REF.sub(
            lambda m: self.heredocs[int(m.group(1))] if int(m.group(1)) < len(self.heredocs) else m.group(0),
            text,
        )

    def _message_file(self, value: str, *, cwd: str) -> str:
        if not value or value == "-":
            raise _Unparsed("message_file_unread")
        real = os.path.realpath(os.path.join(cwd, value))
        if not _inside(real, self.root):
            raise _Unparsed("message_file_unread")
        try:
            with open(real, encoding="utf-8", errors="replace") as handle:
                return handle.read(1_000_000)
        except OSError as exc:
            raise _Unparsed("message_file_unread") from exc

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
        if _URL.match(word) or _REMOTE.match(word) or _HOST_PORT.match(word):
            raise _Outside("network_target")
        if word.startswith("~"):
            raise _Outside(rule)
        real = os.path.realpath(os.path.join(cwd, word))
        if real in _HARMLESS_PATHS or word in _HARMLESS_PATHS:
            return
        if not _inside(real, self.root):
            raise _Outside(rule)


#: GitHub's closing keywords followed by an issue reference (``#12``,
#: ``owner/repo#12``, an issue URL). Case does not matter; a colon may follow.
_CLOSE_KEYWORD = re.compile(
    r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*:?\s*"
    r"(?:#\d+|[\w.-]+/[\w.-]+#\d+|https?://\S+/issues/\d+)"
)
_HEREDOC_REF = re.compile(r"HEREDOC_TEXT_(\d+)")
_GH_MESSAGE_FLAGS = frozenset({"--body", "-b", "--title", "-t"})
#: gh flags that take a value (global and the pr forms'), so a value is
#: never read as the subcommand.
_GH_VALUE_FLAGS = frozenset({
    "-R", "--repo", "--hostname", "-b", "--body", "-t", "--title", "-F", "--body-file",
    "-B", "--base", "-H", "--head", "-a", "--assignee", "-l", "--label", "-m", "--milestone",
    "-p", "--project", "-r", "--reviewer", "-T", "--template", "-q", "--jq", "--json",
    "-L", "--limit", "-s", "--state", "-A", "--author", "-S", "--search",
})
#: The gh forms an agent runs in its own right (read, or its own PR).
_GH_ALLOWED = frozenset({
    ("pr", "create"), ("pr", "edit"), ("pr", "view"), ("pr", "list"), ("pr", "status"),
    ("pr", "checks"), ("pr", "diff"), ("issue", "view"), ("issue", "list"),
    ("run", "view"), ("run", "list"), ("run", "watch"), ("repo", "view"), ("auth", "status"),
})
#: git commit's long options (git 2.x ``--git-completion-helper-all``); git
#: accepts any unambiguous prefix of one.
_GIT_COMMIT_LONG = (
    "quiet", "verbose", "file", "author", "date", "message", "reedit-message", "reuse-message",
    "fixup", "squash", "reset-author", "trailer", "signoff", "template", "edit", "cleanup",
    "status", "gpg-sign", "all", "include", "interactive", "patch", "only", "no-verify",
    "dry-run", "short", "branch", "ahead-behind", "porcelain", "long", "null", "amend",
    "no-post-rewrite", "untracked-files", "pathspec-from-file", "pathspec-file-nul",
    "allow-empty", "allow-empty-message", "verify", "post-rewrite",
)
_GIT_COMMIT_VALUE_LONG = frozenset({
    "file", "author", "date", "message", "reedit-message", "reuse-message", "fixup", "squash",
    "trailer", "template", "cleanup", "pathspec-from-file",
})
_GIT_COMMIT_MESSAGE_ELSEWHERE = frozenset({
    "reedit-message", "reuse-message", "fixup", "squash", "template",
})
_GIT_COMMIT_MESSAGE_ELSEWHERE_SHORT = frozenset("Cct")


def _git_long_option(name: str, options: tuple[str, ...]) -> Optional[str]:
    """The long option ``name`` names, as git reads it: an exact name (its
    ``no-`` form too), else the ONE option it is a prefix of; ``None`` when
    none or more than one matches (git refuses an ambiguous prefix)."""
    if not name:
        return None
    names = list(options) + [f"no-{o}" for o in options if not o.startswith("no-")]
    if name in names:
        return name
    matches = [o for o in names if o.startswith(name)]
    return matches[0] if len(matches) == 1 else None


_GH_MESSAGE_FILE_FLAGS = frozenset({"--body-file", "-F"})


def _closes_issue(text: str) -> bool:
    return bool(_CLOSE_KEYWORD.search(text or ""))


def _flag_values(args: list[str], flags: frozenset[str]) -> list[tuple[str, str]]:
    """``(flag, value)`` for each of ``flags`` in ``args``: ``--x v``,
    ``--x=v``, ``-x v``, ``-xv`` and a short cluster (``-am v``)."""
    shorts = {f[1] for f in flags if len(f) == 2}
    found: list[tuple[str, str]] = []
    index = 0
    while index < len(args):
        arg = args[index]
        nxt = args[index + 1] if index + 1 < len(args) else ""
        if arg.startswith("--"):
            name, eq, value = arg.partition("=")
            if name in flags:
                if eq:
                    found.append((name, value))
                else:
                    found.append((name, nxt))
                    index += 1
        elif arg.startswith("-") and len(arg) > 1:
            for pos, char in enumerate(arg[1:], start=1):
                if char in shorts:
                    tail = arg[pos + 1:]
                    if tail:
                        found.append((f"-{char}", tail))
                    else:
                        found.append((f"-{char}", nxt))
                        index += 1
                    break
        index += 1
    return found


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
    "EDIT_INSIDE_RULE",
    "EDIT_TOOLS",
    "INSIDE",
    "OUTSIDE",
    "SCOPES",
    "UNPARSED",
    "classification_from_wire",
    "classify_bash",
    "classify_edit",
    "classify_tool_call",
]
