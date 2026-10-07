# Handover — Muad'Dib XXXIII (2026-10-07)

Read first, in order: `CLAUDE.md`, `pm/STATUS.md`, `docs/internal/CONDUCTOR.md`, this file. Memory index: `MEMORY.md` (see `project_the_conductor.md`, `feedback_agents_read_people.md`).

## What happened this session (2026-10-05 → 07)

1. **Docs sweep** (#887): a Sonnet 5.5 fleet rewrote README, CONTRIBUTING and every `docs/*.md` against source.
2. **README as a front page** (#889, #891): it now sells the whole product (Ask AI, Threads, memory, Send, coders, Extend).
3. **The Conductor** (owner: "work with agents, semi-autonomously, as an orchestrator, out of the box"): plan #893; K0–K6 (#894 #895 #896 #898 #900 #904 #903); faces F1 #905, F2 #906 from the ratified canvas #902.
4. **Hardening** (owner: "address the things still open"): R1 #916 (real Claude Code + Codex walk), R2 #911 (durable credentials), R3 #914 (Codex gated), R4 #912 (issues, closes, every merge), R5 #915 (paper cuts, flakes, port race), R6 #913 (library Buttons), R7 #919 (agents read People + `people.mcp_access`, Settings › People).

All merged. Canvas and built shots: artifact https://claude.ai/artifact/JmT9yCMah1NwcXqKu7ppGv.

## Owner rulings this session (binding)

- **K5 Control-mode mapping**, with YOLO the default:
  - Secure: the owner approves everything.
  - Normal: read, test and git-read commands pass; a drafted answer waits for the owner to send it.
  - YOLO: commands pass inside the agent's own worktree; routine questions are answered with a receipt; real ones go to Needs you.
- **Canvas** (#902) ratified: Claude Code is the default agent, and the launch sheet shows on every hand-off.
- **People:** agents READ People via MCP with no People cut; People writes stay owner-only; `people.mcp_access` defaults to on. K7a is ratified: the Settings › People panel, with the strip disabled while the environment variable overrides it.
- **The weekly update** reports every merge (`report_merged_prs`, on by default).

## Lessons (scars)

- **The real-agent walk (R1) found what 14k green tests missed:**
  - every Bash call was held;
  - Codex never received its brief;
  - questions never reached Needs you.

  Do one real walk before calling an agent feature done. Use ISOLATED credentials: a separate `CLAUDE_CONFIG_DIR`/`CODEX_HOME` login or API keys, never a symlink to the owner's keychain or `auth.json`. The R1 walk broke this rule, and that is disclosed in the PR.
- **Astra is worth the rounds.** Almost every PR had real P1s, mostly People/secret leaks, gate escapes, ownership and races.
  - Brief her with the owner's rulings up front.
  - She cannot review prompts worded as "adversarial attack" (her provider's filter cut a run); word the brief as a correctness review.
- **Under heavy load (six lanes) FAST flakes.** Rerun any failure alone before treating it as real. Real failures were usually census and doc-claim fences: regenerate them, never weaken them.
- **`git mv` + `sed` + `git commit -m` without `-a` leaves the edits unstaged** (my #906 slip, fixed in #917).
- **Lane worktrees live in `HoldSpeak/wt-conductor-*`, inside the main checkout.** They are leftovers; park or remove them when idle (never delete branches).

## Open (also in `pm/STATUS.md`)

- No atlas walk of launch → PR → merge: the rig lacks an agent double, a GitHub-shaped clone step and a gh double at PR receipts.
- Not on any face yet (each needs a canvas): the Room's PR link on merge, and a `report_merged_prs` control.
- The live hub's preferred-port path is IPv4-only.
- Bugs on main that predate this work: the meeting window shows its summary twice (first-use smoke), and the J4 meetings import times out.
- Load flakes: workbench deadline, `agent_hand_round1` thread hand, the sidecar cold start (cause fixed in R5).
- Still waiting on the owner's go: the 2026-10-05 "open by default" OSS pass (public GitHub hygiene, examples/, good-first-issues, v0.5.0, parking `pm/`).

## Next (my recommendation to the owner)

Hand the Conductor one small real action item from one of the owner's own Projects, on his real desk, and watch launch → PR → merge. Then the OSS pass, if he says go.
