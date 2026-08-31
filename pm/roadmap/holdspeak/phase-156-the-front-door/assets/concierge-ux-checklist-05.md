# Concierge UX Evidence Checklist (HS-156-05)

Every item from `concierge-ux-evidence.md` is addressed: FIXED (with
the story/test) or RECORDED (with the reason).

| # | Item | Disposition | Detail |
|---|------|-------------|--------|
| 1 | "Connect a LAN llama.cpp server" is not a front-door action | RECORDED | Backend API shape, not door-path wording. The front door recommender handles known endpoints (probed, displayed with human names). Connecting a new endpoint is an advanced-layer action. |
| 2 | define-endpoint creates v1 deployments with context_ceiling=0 | RECORDED | Backend schema bug in deployment_revisions. Not a wording/UI defect. Tracked in concierge evidence for the backend team. |
| 3 | Legacy profile assignment FK-errors at route freeze | RECORDED | Backend transaction bug in admit flow. Not a door-path wording defect. |
| 4 | Downloaded catalog models do not create assignable profiles | RECORDED | Backend acquisition flow gap. Not a door-path wording defect. |
| 5 | Assignment editor shows zero candidates for text capabilities | RECORDED | Backend compatibility checker bug (context_ceiling=0). Not a door-path wording defect. |
| 6 | 24-model catalog with no guidance for self-hosted users | RECORDED | Catalog UX gap. The front door recommender now shows human labels and the "Set up my own" button opens the advanced layer. |
| 7 | Legacy config routes not surfaced in assignment flow | RECORDED | Backend library/assignment service gap. Not a door-path wording defect. |
| 8 | Speech recognition works but assignment UI shows it broken | RECORDED | Assignment system disconnect. Not a door-path wording defect. |
| 9 | "no_compatible_assignment" is unexplained jargon | FIXED | HS-156-05: deny-list fence test (`frontDoor.test.tsx` copy fence) excludes "no_assignment", "no_compatible_assignment", "catalog", "provider_family", and ".gguf" from door-path rendered text. The door surface never renders these strings. |
| 10 | Request shapes require source-reading to discover | RECORDED | API documentation gap. Not a door-path wording defect. |
| 11 | "ready" indicator on provider profiles is misleading | RECORDED | Model Library advanced-layer UX. Not a door-path surface defect. |
| 12 | Broken acquisitions accumulate without cleanup | RECORDED | Library cleanup UX gap. Not a door-path wording defect. |

**Summary:** 1 FIXED, 11 RECORDED. Zero unaddressed items.
