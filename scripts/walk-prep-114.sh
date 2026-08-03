#!/usr/bin/env bash
# HS-114-07 walk prep: nuke everything and seed a bare-minimum desk.
# Run this BEFORE starting the hub for the walk. It:
#   1. Deletes the DB (fresh schema on next boot)
#   2. Deletes the config (fresh defaults on next boot)
#   3. Boots the hub
#   4. Seeds the desk (creates Homelab profile + starter agent + workflow)
#   5. Stops the hub
#
# After this script, the desk is in the exact state a first-time user
# would see after running `holdspeak seed`. Nothing else.
#
# Usage: bash scripts/walk-prep-114.sh

set -euo pipefail

DB_PATH="${HOME}/.local/share/holdspeak/holdspeak.db"
CONFIG_PATH="${HOME}/.config/holdspeak/config.json"

echo "=== HS-114-07 Walk Prep ==="
echo ""

# 1. Nuke the DB
if [ -f "$DB_PATH" ]; then
  echo "[1/5] Removing DB: $DB_PATH"
  rm "$DB_PATH"
else
  echo "[1/5] No DB to remove (already fresh)"
fi

# 2. Nuke the config
if [ -f "$CONFIG_PATH" ]; then
  echo "[2/5] Removing config: $CONFIG_PATH"
  rm "$CONFIG_PATH"
else
  echo "[2/5] No config to remove (already fresh)"
fi

# 3. Seed via CLI (this boots the DB and config internally)
echo "[3/5] Running holdspeak seed..."
uv run holdspeak seed

echo ""
echo "[4/5] Verifying seed..."
# Quick check: the profile should exist
uv run python -c "
from holdspeak.db import get_database, reset_database
db = get_database()
profiles = db.profiles.list()
recipes = db.recipes.list()
workflows = db.workflows.list()
print(f'  Profiles: {len(profiles)} ({", ".join(p.name for p in profiles)})')
print(f'  Agents:   {len(recipes)} ({", ".join(r.name for r in recipes)})')
print(f'  Workflows:{len(workflows)} ({", ".join(w.name for w in workflows)})')
print(f'  Directories: {len(db.directories.list())}')
reset_database()
"

# 5. Check config adoption
echo ""
echo "[5/5] Checking config adoption..."
uv run python -c "
from holdspeak.config import Config
c = Config.load()
print(f'  Dictation profile_id: {c.dictation.runtime.profile_id}')
print(f'  Meeting intel_profile_id: {c.meeting.intel_profile_id}')
"

echo ""
echo "=== Walk prep complete ==="
echo ""
echo "Next steps:"
echo "  1. Start the hub:  uv run holdspeak serve"
echo "  2. Open browser:   http://localhost:8766"
echo "  3. Run the walk screenshots"
echo ""
echo "The desk is bare-minimum: 1 Homelab destination, 1 agent,"
echo "1 workflow, 6 drawers, 2 notes. Config points at Homelab."
echo "Nothing else exists."
