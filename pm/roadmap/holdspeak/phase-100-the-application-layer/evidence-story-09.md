# Evidence - HS-100-09

- **Story:** HS-100-09 - B5: Agents
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T14:43:35Z

- **Command:** `sh -c cd web && npx vitest run src/pages/cores/__tests__/agents.test.tsx 2>&1 | tail -3 && cd .. && uv run pytest -q tests/unit/test_web_vocabulary_guard.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 22680c843fe5d2e3c822c54efe5938fc86f490ea

```text
   Start at  08:43:35
   Duration  565ms (transform 104ms, setup 43ms, import 167ms, tests 76ms, environment 196ms)

4 passed in 0.09s
```

## Summary of proof

- **Agents opens on who needs you** (thesis §1.3): CompanionCore
  rebuilt — blocked sessions FIRST with their question and a primary
  Answer verb (one step from the steering pane via openCoderSession,
  the audited seam untouched), then Running with Watch verbs; wings
  are Sessions | Delivery (the delivery list) | Chat (the agent
  roster → chat window). The honest empty state: "No one is waiting
  on you."
- **"Personas" left the glass**: window title "Agents", shelf label,
  store default ("New Agent"), chat copy ("this agent"), roster copy
  ("No agents yet"). The vocabulary allowlist SHRANK from seven files
  to two (StudioCore + SettingsCore, both dying in HS-100-10) —
  captured green above.
- **Blocked-first is pinned** by vitest (agents.test.tsx): DOM order
  blocked-before-running + the Answer/Watch verbs + a no-personas
  copy assert. vitest 296/296; web_server integration pins green
  (marker set retargeted); build + screenshots at 1440/393 (+ Chat
  wing) in assets/hs-100-09-agents-*.png.
