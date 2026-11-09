#!/usr/bin/env bash
# Lanes: make, list, finish and purge git worktrees for parallel work.
#
#   scripts/lane.sh new <name> [base]   worktree ../wt-<name>, shared web/node_modules,
#                                       uv sync --extra dev (no npm), print the path
#   scripts/lane.sh done <name>         drop the installs, remove the worktree,
#                                       delete the branch when merged
#   scripts/lane.sh purge               drop every lane's installs; remove merged+clean lanes
#   scripts/lane.sh ls                  one line per worktree
#
# A lane links web/node_modules to the main checkout's install (never its own copy)
# and clones the main checkout's holdspeak/static/_built (APFS clone, no space), so
# `uv sync` runs no npm. Environment:
#   HOLDSPEAK_SERVED_TREE   worktree that serves the hub; purge never touches it
#                           (default wt-desk-main-20261025)
#   HOLDSPEAK_LANE_NO_SYNC  1 = skip uv sync in `new` (tests)
#   HOLDSPEAK_LANE_MIN_AGE_H  purge keeps a lane with git activity in the last N hours (default 2)
#   HOLDSPEAK_LANE_BASE     ref that "merged" means (default origin/main, else main)
# Bash 3.2 compatible (macOS /bin/bash).

set -euo pipefail

die() { echo "lane: $*" >&2; exit 1; }

COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
  || die "run inside the HoldSpeak repository"
MAIN="$(dirname "$COMMON_DIR")"
PARENT="$(dirname "$MAIN")"
SERVED="${HOLDSPEAK_SERVED_TREE:-wt-desk-main-20261025}"
MIN_AGE_H="${HOLDSPEAK_LANE_MIN_AGE_H:-2}"

base_ref() {
  if [ -n "${HOLDSPEAK_LANE_BASE:-}" ]; then echo "$HOLDSPEAK_LANE_BASE"
  elif git -C "$MAIN" rev-parse -q --verify origin/main >/dev/null; then echo origin/main
  else echo main; fi
}

# name -> directory name and branch: "pipe/lane-tool" -> wt-pipe-lane-tool, branch pipe/lane-tool
dir_for() { echo "wt-$(echo "$1" | tr '/' '-')"; }

# Print "path<TAB>branch-or-(detached)<TAB>head" for each worktree that exists.
worktrees() {
  git -C "$MAIN" worktree list --porcelain | awk '
    /^worktree / { if (p != "") print p "\t" b "\t" h; p = substr($0, 10); b = "(detached)"; h = "" }
    /^HEAD /     { h = $2 }
    /^branch /   { b = substr($2, 12) }
    END          { if (p != "") print p "\t" b "\t" h }'
}

is_merged() {  # head sha
  [ -n "$1" ] && git -C "$MAIN" merge-base --is-ancestor "$1" "$(base_ref)" 2>/dev/null
}

dirty_files() {  # path; prints porcelain lines (ignored files excluded)
  git -C "$1" status --porcelain 2>/dev/null || echo "?? (git status failed)"
}

label() {  # path -> short name: the directory beside the main checkout, else the path
  if [ "$(dirname "$1")" = "$PARENT" ]; then basename "$1"; else echo "${1/#$HOME/~}"; fi
}

size_of() { du -sh "$1" 2>/dev/null | awk '{print $1}'; }
kb_of() { du -sk "$1" 2>/dev/null | awk '{print $1}'; }

hours_since_activity() {  # path
  local gd log now mt
  gd="$(git -C "$1" rev-parse --path-format=absolute --git-dir 2>/dev/null)" || { echo 999; return; }
  log="$gd/logs/HEAD"; [ -f "$log" ] || log="$gd/HEAD"
  now="$(date +%s)"; mt="$(stat -f %m "$log" 2>/dev/null || stat -c %Y "$log")"
  echo $(( (now - mt) / 3600 ))
}

cmd_new() {
  local name="${1:-}" base="${2:-origin/main}" dir path t0 t1
  [ -n "$name" ] || die "usage: lane.sh new <name> [base]"
  dir="$(dir_for "$name")"; path="$PARENT/$dir"
  [ -e "$path" ] && die "$path already exists"
  git -C "$MAIN" fetch -q origin 2>/dev/null || echo "lane: fetch failed; using the local refs" >&2

  # The shared install matches the main checkout's lock file; the lane must use the same one.
  if [ -f "$MAIN/web/package-lock.json" ] \
     && ! git -C "$MAIN" show "$base:web/package-lock.json" 2>/dev/null | cmp -s - "$MAIN/web/package-lock.json"; then
    cat >&2 <<EOF
lane: the main checkout's web/package-lock.json differs from $base's.
      The shared web/node_modules was installed for the main checkout's lock file,
      so a lane on $base would run against the wrong packages. Do one of:
        - update the main checkout to $base (git -C $MAIN pull --ff-only), then
          run 'cd $MAIN/web && npm ci' while no lane runs tests;
        - or give a base whose lock file matches the main checkout.
EOF
    exit 1
  fi

  git -C "$MAIN" worktree add -q "$path" -b "$name" "$base"
  if [ -d "$MAIN/web/node_modules" ]; then
    ln -s "$MAIN/web/node_modules" "$path/web/node_modules"
  fi
  if [ ! -d "$MAIN/web/node_modules/.bin" ]; then
    echo "lane: the shared install $MAIN/web/node_modules is empty or missing;" >&2
    echo "      run 'cd $MAIN/web && npm ci' once while no lane runs tests." >&2
  fi
  if [ -f "$MAIN/holdspeak/static/_built/index.html" ]; then
    mkdir -p "$path/holdspeak/static"
    cp -Rc "$MAIN/holdspeak/static/_built" "$path/holdspeak/static/_built" 2>/dev/null \
      || cp -R "$MAIN/holdspeak/static/_built" "$path/holdspeak/static/_built"
  fi
  if [ "${HOLDSPEAK_LANE_NO_SYNC:-}" != "1" ]; then
    t0="$(date +%s)"
    if [ -f "$path/holdspeak/static/_built/index.html" ]; then
      (cd "$path" && HOLDSPEAK_SKIP_WEB_BUILD=1 uv sync -q --extra dev)
    else
      # No built output to clone: hatch_build.py builds it with the shared install (no npm ci).
      (cd "$path" && uv sync -q --extra dev)
    fi
    t1="$(date +%s)"
    echo "lane: uv sync --extra dev took $((t1 - t0)) s" >&2
  fi
  echo "$path"
}

resolve() {  # name -> path of an existing worktree (by directory name, wt-<name>, or branch)
  local name="$1" want path branch head
  want="$(dir_for "$name")"
  while IFS="$(printf '\t')" read -r path branch head; do
    case "$(basename "$path")" in "$name"|"$want") echo "$path"; return 0 ;; esac
    [ "$branch" = "$name" ] && { echo "$path"; return 0; }
  done < <(worktrees)
  return 1
}

drop_installs() {  # path; removes .venv and web/node_modules (link or real copy)
  rm -rf "$1/.venv"
  if [ -L "$1/web/node_modules" ]; then rm -f "$1/web/node_modules"
  elif [ -d "$1/web/node_modules" ]; then rm -rf "$1/web/node_modules"; fi
}

cmd_done() {
  local name="${1:-}" path branch dirty head
  [ -n "$name" ] || die "usage: lane.sh done <name>"
  path="$(resolve "$name")" || die "no worktree named $name"
  [ "$path" = "$MAIN" ] && die "refusing to remove the main checkout"
  [ "$(basename "$path")" = "$SERVED" ] && die "refusing to remove the served tree $SERVED"
  branch="$(git -C "$path" symbolic-ref -q --short HEAD || true)"
  head="$(git -C "$path" rev-parse HEAD)"
  dirty="$(dirty_files "$path")"
  if [ -n "$dirty" ]; then
    echo "lane: $path has changes; nothing removed:" >&2
    echo "$dirty" >&2
    exit 1
  fi
  drop_installs "$path"
  git -C "$MAIN" worktree remove --force "$path"
  echo "removed $path"
  if [ -n "$branch" ]; then
    if is_merged "$head"; then
      git -C "$MAIN" branch -q -D "$branch" && echo "deleted branch $branch (merged into $(base_ref))"
    else
      echo "kept branch $branch (not merged into $(base_ref))"
    fi
  fi
}

cmd_ls() {
  local path branch head merged clean venv size
  printf '%-44s %-44s %-6s %-5s %-5s %s\n' NAME BRANCH MERGED CLEAN VENV SIZE
  while IFS="$(printf '\t')" read -r path branch head; do
    [ -d "$path" ] || { printf '%-44s %-44s %s\n' "$(label "$path")" "$branch" "(missing; git worktree prune)"; continue; }
    if is_merged "$head"; then merged=yes; else merged=no; fi
    if [ -z "$(dirty_files "$path")" ]; then clean=yes; else clean=no; fi
    if [ -d "$path/.venv" ]; then venv=yes; else venv=no; fi
    size="$(size_of "$path")"
    printf '%-44s %-44s %-6s %-5s %-5s %s\n' "$(label "$path")" "$branch" "$merged" "$clean" "$venv" "$size"
  done < <(worktrees)
}

cmd_purge() {
  local path branch head name kb freed=0 removed=0 kept=0 action why age
  git -C "$MAIN" fetch -q origin 2>/dev/null || echo "lane: fetch failed; using the local refs" >&2
  printf '%-44s %-8s %8s  %s\n' NAME ACTION FREED WHY
  while IFS="$(printf '\t')" read -r path branch head; do
    name="$(label "$path")"
    if [ "$path" = "$MAIN" ] || [ "$(basename "$path")" = "$SERVED" ]; then
      printf '%-44s %-8s %8s  %s\n' "$name" kept "-" "main checkout or served tree"; kept=$((kept + 1)); continue
    fi
    [ -d "$path" ] || continue
    kb=0; action=kept
    if is_merged "$head" && [ -z "$(dirty_files "$path")" ]; then
      age="$(hours_since_activity "$path")"
      if [ "$age" -lt "$MIN_AGE_H" ]; then
        why="merged and clean, but active ${age} h ago (a new lane)"
      else
        kb="$(kb_of "$path")"
        drop_installs "$path"
        git -C "$MAIN" worktree remove --force "$path"
        if [ "$branch" != "(detached)" ]; then git -C "$MAIN" branch -q -D "$branch" 2>/dev/null || true; fi
        action=removed; why="merged into $(base_ref) and clean"
      fi
    else
      if is_merged "$head"; then why="has changes"; else why="not merged into $(base_ref)"; fi
      if [ -d "$path/.venv" ] || { [ -d "$path/web/node_modules" ] && [ ! -L "$path/web/node_modules" ]; }; then
        [ -d "$path/.venv" ] && kb=$((kb + $(kb_of "$path/.venv")))
        if [ -d "$path/web/node_modules" ] && [ ! -L "$path/web/node_modules" ]; then
          kb=$((kb + $(kb_of "$path/web/node_modules"))); rm -rf "$path/web/node_modules"
        fi
        rm -rf "$path/.venv"
        action=slimmed; why="$why; installs removed"
      fi
    fi
    if [ "$action" = removed ]; then removed=$((removed + 1)); else kept=$((kept + 1)); fi
    freed=$((freed + kb))
    printf '%-44s %-8s %7sM  %s\n' "$name" "$action" "$((kb / 1024))" "$why"
  done < <(worktrees)
  git -C "$MAIN" worktree prune
  echo "removed $removed worktrees, kept $kept, freed $((freed / 1024 / 1024)) GB ($((freed / 1024)) MB)"
}

case "${1:-}" in
  new) shift; cmd_new "$@" ;;
  done) shift; cmd_done "$@" ;;
  purge) shift; cmd_purge "$@" ;;
  ls) shift; cmd_ls "$@" ;;
  *) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
