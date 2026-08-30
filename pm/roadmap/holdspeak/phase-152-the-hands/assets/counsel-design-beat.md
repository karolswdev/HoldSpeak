# Counsel design-beat — DC-02..DC-05, holistic (2026-08-30)

One Opus counsel ruling for the four remaining phases after the owner
ruled the port ships holistically. Orchestrator dispositions in **bold**.

Verdicts: DC-02 The Hands RATIFY-W-C · DC-03 The Practice RATIFY-W-C ·
DC-04 The Call RATIFY-W-C · DC-05 The Crew RATIFY.

## MUST-FIX (all ACCEPTED)
- **M1 (02)** multi-pass People redactor: `_sensitive_texts` accumulated across passes, redactor on every pass's payload → D3.
- **M2 (02)** `people.*` result parts `sensitive=1` at insert → D3.
- **M3 (02)** the three-way composition (thread policy > control_mode × class) as a truth table → D2.
- **M4 (02)** tool calls as kernel children of the turn via the existing ToolCallCodec/ToolTurnController; no new admission path → D2.
- **M5 (02)** abort mid-loop cancels in-flight executions; 250 ms contract across the whole loop → D1.
- **M6 (02)** elicitation wire format: schema in the part's meta, `thread_tool_pending.elicitation`, `POST /api/threads/{id}/decide` → D2/D4.
- **M7 (03)** compaction summary inherits `sensitive=1` and joins `_sensitive_texts`.
- **M8 (03)** guardrail runs after extraction, before admission; advisory; safe flips the default to Deny; never auto-denies.
- **M9 (04)** call mode persisted on the thread (`call_mode`), toggle route, `thread_call_state` frame; refresh keeps it ON.

## SHOULD-FIX (accepted as riders)
S1 error taxonomy (02, D1) · S2 append-only `thread_tool_policy` (02) · S3 typed renderers for known kinds (02, D5) · S4 seeded modes' allow-lists in the 153 design · S5 annotations persisted as draft parts · S6 TTS sentence-chunk streaming contract · S7 subthread validation + configurable 30 s.

## Recorded notes
R1 adaptive pass cap after real use · R2 paraphrase laundering = the DC-03 egress-guard · R3 `/` only at line start · R4 CPU Kokoro quality → browser fallback if > 2 s · R5 concurrent parent/child writes, last writer wins.

## Story cuts
02: loop · gate · People fence · pending box · renderers+status · walk (6).
03: modes as recipes · prompts + slash · guardrails · annotations · compaction+todo · walk (6).
04: TTS route · VAD · call mode · speaker glyph · walk (5).
05: subthread tool · conductor · notifications · child on the desk · walk (5).
