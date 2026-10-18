# Parked: the old agent faces (Betterment AG1, 2026-10-18)

DECISIONS #3 (adopted 2026-10-17): "Agent" means only a coding agent
session. Its home is **Agents** (the Conductor window, code name kept).
These pieces left the face. Nothing imports them; `tsconfig.json` and
vitest exclude `_parked/`.

- `companionApplication.ts`: the old Agents application row
  (`inspect-personas-and-coders`, window `surface-companion`, route
  `/companion`). The address `/companion` now opens Agents.
  `pages/cores/CompanionCore.tsx` stays in place for its tests; no route
  or manifest row reaches it.
- `newAgentVerb.ts`: the Desk menu's **New Agent** (a saved persona,
  `desk.new-agent`). Saved prompts live on as thread modes ("Mode") and as
  Automation starters.
- `InstallHooksVerbs.tsx`: the unused export from `ConductorWindow.tsx`
  (one Install hooks verb per agent with nothing selected).
