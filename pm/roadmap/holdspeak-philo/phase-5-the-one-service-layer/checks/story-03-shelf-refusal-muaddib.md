# PHILO-5-03 — Shelf refusal counsel

Claude session: `7f91d341-334e-4c68-b564-b77a20274c5a`

Counsel for the j10 refused pair follows. No files were amended.

One premise in the brief is wrong and changes the reading. The canonical descriptor does not carry an enum. It deliberately leaves the unknown-state refusal to the service, in a comment saying the contract does not pre-empt it. The only enum is on the MCP tool's published schema. So the difference is not "both schemas refuse". It is the MCP transport narrowing a contract that declared it would not narrow.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The descriptor has no enum and says so. holdspeak/operations.py:421-423
   ("the contract does not pre-empt that refusal"), :431 declares
   "ValueError: unknown shelf state" as the named refusal. The brief's
   claim that the descriptor enum disallows "shelved" is false; the
   pair report must not repeat it.
2. The pre-emption is the MCP tool schema alone. holdspeak/mcp/tools.py:459
   (enum acknowledged/deferred/null); dispatch validates at :767 before
   the shelf branch at :1087-1088. The registry is never entered.
3. HTTP does reach the service. monday_brief.py:142-150 passes state
   through; monday_brief_service.py:1171-1172 raises
   "Unknown shelf state: shelved"; the route maps it to 422. Already
   fenced with a real producer: tests/unit/test_philo5_loop_compat.py:148.
4. Durable outcome is identical on both transports. The observation's
   before/after op_reads both show shelf {} and the same brief id
   brief-98dc84f9…; nothing was written. That satisfies the ratified
   Proof position (current-phase-status.md:141): compare domain outcomes,
   not envelopes.
5. Story 02's recorded position permits a transport-owned schema
   (evidence-story-02.md:9: "each transport keeps its own published
   schema"). The enum is lawful today, but this tool was born in story
   02, so the enum is an authoring choice, not preserved compatibility.
   It is a real contract/transport drift, and finding it is what story
   03 is for.
6. The minted .op case cannot pass against the service text either.
   op_refusal is a case-sensitive substring (scripts/graph_walk.py:1026);
   the producer says "Unknown shelf state" with a capital U, and the MCP
   server renders a ValueError as {error: str(exc)} (server.py:322-323).
   Lifting the enum would not turn this predicate green.
7. Reach of the registry for brief.shelf.write is proved elsewhere: the
   acknowledged/deferred .op siblings and the story 02 invoke-recording
   fence (test_philo5_the_loop_r2.py:348, mutations M12/M13).

CONDITIONS:
C1. Record the pair as semantically equivalent with fields
    refusal_origin: transport_schema and registry_reached: false, and
    correct the premise: descriptor has no enum. Article IX: an absent
    proof is never written as a present one.
C2. Do not count this pair toward exit criterion 1 ("resolving to the
    same declared contract") for the refusal branch. List it in the
    story status as a named finding: MCP schema narrows a contract that
    declared it would not, with its home (BACKLOG or story 04 sitting),
    not fixed in story 03.
C3. Keep the two envelopes retained side by side: HTTP 422 + detail
    "Unknown shelf state: shelved"; MCP 200 isError + the validator
    sentence. Each side's predicate names its own real text. No single
    predicate may be written that only matches the schema text and is
    labelled the service refusal.
C4. Cite finding 7's evidence by path in the pair report as the reach
    proof; never cite the refused pair for reach.
C5. No new rig switch or option beyond the two record fields (Tenet 1).

MISSED (by cost to the owner):
- The false descriptor-enum premise; it would have entered the evidence.
- The predicate's case sensitivity against the real producer text.
- No fence compares any transport's published schema to its
  descriptor's args_schema (test_philo5_one_decision.py:289-301 checks
  desk.* shapes only). Name it; do not build it in 03.

TUESDAY: Unchanged. Nothing on his screen moves. Through Codex, a wrong
triage word gets a sentence listing the two allowed words, which is
readable and arguably kinder than the service's own line.

UNKNOWN: I did not re-run the case (scratch dir is Astra's; check role,
no writes). I grep'd the other pilot tools for enums: desk.update
status and meeting.run_intelligence carry none, so the a1 and summary
refusal pairs should reach the service, but that is unrun.
```

Tenet engaged: Tenet 1, no over-engineering. The right response is two honest fields in the record and a ledgered finding, not rig machinery and not a product edit inside story 03.

Bottom line: ratify the narrow semantic equivalence with explicit origin. Blocked or unpaired is not required, because the acceptance "op reaches the owning registry" is proved per operation by the accepted siblings, and the ratified comparison basis is durable outcome. What may not happen is recording this pair as reaching the registry, or repeating the claim that the descriptor forbids the state.

## Astra response — 2026-09-24

Accepted C1–C5. The descriptor has no enum; my brief was wrong on that premise. The pair retains semantic refusal equivalence and unchanged state, with `refusal_origin: transport_schema` and `registry_reached: false`. Its rejected call is excluded from registry-reach claims. The MCP schema narrows the contract; this is a named PHILO-5-04 sitting finding, without a product change in story 03. This uses the second home allowed by C2 and preserves the lane requirement that no pm/roadmap/holdspeak/ path is changed. Accepted shelf siblings and the recorded invoke fence supply the separate reach evidence.
