# Council opinion — Sol, second pass: Article XI (ratification review)

**Date:** 2026-07-26
**Council member:** Sol (gpt-5.6-sol)
**Subject:** proposed Article XI — The Kernel, drafted at
`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md` §10, reviewed before
ratification into `docs/internal/CONSTITUTION.md`.
**Prior pass by the same member:** `kernel-council-sol-opinion.md`
("ratify with six amendments" — all six adopted).
**Owner's stated stance, given as the grounding for this pass:**

> "We do not invent and over-complicate, but we certainly build for
> the future of an agent-connected workflow into nearly anything —
> and anything — including just being an awesome power user."

**Verdict: DO NOT RATIFY YET.**

The opinion is reproduced verbatim below.

---

Do not ratify yet.

The six amendments from my first opinion fixed the defects I identified, but the proposed Article now has a different problem: it turns the RFC's destination into present-tense constitutional fact. There is no `holdspeak/kernel/` package today. More importantly, the proposed Phase 106 scope only implements the journal, principal separation, and two thin drivers. The RFC deliberately postpones the broad typing census and other operation families until later (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:288-317`). Clauses 2, 3, 4, and 6 would therefore be false when ratified and still false at the end of Phase 106.

There is also a definition error that the previous council missed. Clause 1 treats a process boundary as proof of consequence. On the web Desk, almost every server mutation crosses the browser/server process boundary, including the reversible shell bookkeeping that §12 says must never enter the kernel (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:423-430`). At the same time, a same-process authority mutation can escape clause 1. Consequence cannot depend on deployment topology.

## Clause 1

> "A consequential operation is one that crosses a principal, process, machine, model/egress, or irreversible-effect boundary. An operation's consequence is judged for itself: nesting inside an admitted operation never exempts it."

The second sentence is sound and should remain. It closes the nested-effect loophole from my first opinion.

The first sentence does not hold.

There are clear present-day examples that belong on the consequential side. `tmux_transport.send_text_to_pane` launches `tmux send-keys`, types the payload into another process, and optionally submits it (`holdspeak/tmux_transport.py:20-45`). The delivery protocol binds that kind of effect to an immutable node, target, generation, payload hash, and sequence (`holdspeak/delivery/commands.py:1-23`, `holdspeak/delivery/commands.py:202-283`). Calling it consequential is neither invention nor speculation.

The problem is using process topology as the definition. The Desk runs in a browser while durable Desk state lives behind the web runtime. A reversible zone filing, window persistence update, or similar Desk mutation crosses a process boundary merely because React and Python are different processes. Clause 5 does not exempt such a mutation because it is not a read, presentation, or side-effect-free computation. Yet the RFC says window placement and drop physics never go through the kernel and that ordinary reversible local edits do not pay remote-command ceremony (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:423-430`). The Constitution also requires the user's window arrangement to persist (`docs/internal/CONSTITUTION.md:79-86`). Clause 1 would make implementation topology outrank those product rules.

The definition also under-reaches. Changing control posture is an authority mutation whether it arrives over HTTP or through an in-process call. Today the route edits configuration, revokes actuator grants, and clears coder grants directly (`holdspeak/web/routes/authority.py:65-114`). If the same function is invoked inside the web process, it crosses none of clause 1's listed boundaries. Its constitutional classification changes depending on where the caller happens to run. That is not a stable law for an agent-connected system.

"Model/egress" is also too compressed. Invoking a local model and sending data out of the machine are distinct events with distinct authority and privacy consequences. A slash does not define their relationship.

Assessment:

- Today: the examples fit, but the definition does not consistently classify the code.
- Over-invented: yes. "Process boundary" routes ordinary web implementation traffic through constitutional machinery.
- Under-reaching: yes. Same-process authority and delegated effects can escape it.
- Agent future: brittle. Splitting or combining processes silently changes what the Constitution governs.

## Clause 2

> "Every consequential operation enters the system through the kernel's one admission path and produces a receipt, including on refusal. A consequential effect performed by a tool inside a model's run is submitted as a causally linked child operation of that run."

The child-operation sentence is correct. Keep it.

The universal first sentence is false today. Dictation calls `TextTyper.type_text` directly on the ordinary typing path, preview path, voice-command path, remote dictation path, and focused-app path (`holdspeak/runtime/dictation_capture.py:178-201`, `holdspeak/runtime/dictation_capture.py:271-294`, `holdspeak/runtime/dictation_capture.py:360-388`, `holdspeak/runtime/dictation_capture.py:450-511`). Dictation-to-agent also imports and calls `send_text_to_pane` directly (`holdspeak/runtime/dictation_capture.py:422-435`). Cadence has another direct tmux path (`holdspeak/web/routes/cadence.py:235-256`). These effects do not enter a kernel because no kernel exists.

The current steering chokepoint does not guarantee a receipt either. It performs the transport first, then catches any audit failure and returns `audit_id = None` (`holdspeak/coder_steering.py:538-586`, `holdspeak/coder_steering.py:645-658`). The effect can succeed without the promised receipt.

Phase 104's gate does not make this clause true. Its proposal row is explicitly "never authority"; only the live external hook can allow the tool to proceed (`holdspeak/db/gate.py:1-15`, `holdspeak/web/routes/system/gate_routes.py:1-18`). Approval records that HoldSpeak allowed a call. It does not establish whether the external tool ran, failed before effect, partly succeeded, or became indeterminate. A decision receipt is not an execution receipt.

The scope is also too broad. "Every consequential operation enters the system" can be read to cover any action an attached agent takes through its own ambient tools. HoldSpeak cannot truthfully claim that until raw effects are confined. The RFC itself limits today's claim to cooperating, migrated surfaces and says the stronger claim requires a privileged executor process (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:47-60`, `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:220-239`). The Constitution must name what HoldSpeak controls: operations it performs, brokers, or authorizes.

The receipt requirement under-reaches in a different way. "Produces a receipt" does not say whether the receipt records admission, approval, dispatch, or terminal outcome. Phase 104 proves that these are not interchangeable. Constitutional wording should require a terminal receipt and name indeterminate outcome.

Assessment:

- Today: false.
- End of Phase 106: still false. Two thin drivers do not migrate dictation, Cadence, every tool gate, inference, plugin jobs, or every raw effect. The RFC postpones broad migration to rung 5 (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:288-311`).
- Much later: satisfiable after broad migration; enforceable against untrusted or agent-authored code only after §5b confinement.
- Over-invented: not in intent, but universal scope overclaims what HoldSpeak can observe.
- Under-reaching: yes, because an admission or approval row can masquerade as the promised receipt.

This is the main reason not to ratify now. It is dishonest as present law, not merely ambitious as a north star.

## Clause 3

> "The caller never asserts its own authority; authority is derived at admission and bound immutably to the admitted operation."

This is the right rule, and one subsystem nearly implements it. `HubCommandService.submit` rejects a client-supplied authority block by name (`holdspeak/delivery/commands.py:779-792`). The service derives policy at the hub and stamps the result into an envelope bound to the target and payload (`holdspeak/delivery/commands.py:722-775`, `holdspeak/delivery/commands.py:834-879`). The node consumes that snapshot rather than deciding again (`holdspeak/delivery/commands.py:187-199`, `holdspeak/delivery/commands.py:418-541`).

The rule is false system-wide. Loopback is explicitly open without authentication (`holdspeak/web_auth.py:1-12`, `holdspeak/web_auth.py:82-98`). The gate proposal route accepts `session_key` and `agent` directly from the request body (`holdspeak/web/routes/system/gate_routes.py:67-105`). Its decision route accepts `actor` from the request body and defaults it to `"owner"` (`holdspeak/web/routes/system/gate_routes.py:134-166`). The grant route likewise accepts an actor string supplied by the caller (`holdspeak/web/routes/authority.py:175-225`). Those values may be useful labels, but they are not authenticated principals.

"Bound immutably" also needs one qualification. The admitted payload, target, and authority basis must remain immutable; the right to execute must still expire or be revoked. The RFC's own warrant rule checks expiry and revocation before effect (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:191-204`). Constitutional language should not accidentally turn immutable binding into irrevocable authority.

Assessment:

- Today: true for the delivery envelope, false for the web and gate surfaces.
- End of Phase 106: satisfiable for kernel operations if principal separation covers every kernel entry and the two drivers use warrants. It remains false as a system-wide statement while old authority routes survive.
- Later: satisfiable after migration and route hardening.
- Over-invented: no.
- Under-reaching: slightly. It should distinguish immutable binding from expiry and revocation.

## Clause 4

> "Humans and agents share the kernel's schemas and never its rights; only the owner decides."

The intended rule is good. The wording is not constitutional quality.

Current code has shared data shapes without shared principal enforcement. The capability ledger classifies adapters as authoritative, inferred, or unavailable (`holdspeak/agent_capabilities.py:33-101`), and its enforcement hook refuses unavailable capabilities (`holdspeak/agent_capabilities.py:132-152`). That is an honesty ledger, not a principal or delegation system. It cannot establish that an incoming gate request is an agent, that a decision came from the owner, or that one principal may see only delegated refs. The unauthenticated, caller-labelled routes cited under clause 3 make the clause false today.

"Share the schemas and never its rights" is an aphorism where the Article needs a rule. Some rights may be shared through bounded delegation. What must never be shared is owner identity and owner-only authority. The RFC already says an agent may submit delegated work but may not call `decide`, change posture, or claim ownership (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:206-218`).

"Only the owner decides" is also ambiguous for the power user. The policy code already recognizes direct gesture, a scoped grant, and configured control posture as distinct authority bases (`holdspeak/operation_policy.py:227-285`). If this clause means every owner action requires a separate `decide` call, it adds ceremony that Article V does not necessarily require. If it means only the owner may approve, reject, or delegate authority, it is correct. The Article should say that.

Assessment:

- Today: false.
- End of Phase 106: satisfiable if loopback principal separation protects submission, decision, posture, grant, and read endpoints, not only the new broker route.
- Over-invented: the separation is not. The slogan-like wording is.
- Under-reaching: yes. It does not define which rights remain owner-only or how bounded delegation works.

## Clause 5

> "Reads, presentation, and side-effect-free computation, including the token stream inside a model's run, are not consequential operations and owe the kernel nothing. This clause exempts computation, never effects."

The low-ceremony intent is right. Capture, transcription windows, and token streams should not be journal events. That matches the RFC's non-goals (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:423-429`) and keeps the latency-sensitive path out of the broker.

"Reads ... owe the kernel nothing" is too broad. The RFC defines `read` as one of the kernel's four public calls and says even cheap reads pay authentication (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:102-124`). It also says an agent sees only delegated refs (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:206-218`). Those rules matter more in the agent-connected future, not less. A read need not create a consequential-operation receipt, but it still needs authenticated principal and read authority. Otherwise an agent can read material outside its delegated scope while remaining compliant with Article XI.

"Presentation" also needs to mean ephemeral shell presentation. As written, it could be stretched to cover a presentation operation that persists or discloses user data.

The last sentence is good. It preserves the nested-effect fix without journaling inference internals.

Assessment:

- Today: the computation exemption matches practice, but there is no agent-safe read boundary.
- End of Phase 106: satisfiable after principal separation if the wording preserves authentication and read authority.
- Over-invented: no. This is necessary protection against kernel ceremony.
- Under-reaching: yes. It drops confidentiality and delegation controls from reads.

## Clause 6

> "Nothing in this Article narrows Article V: whatever types, sends, files, spawns, or kills passes propose/approve/execute regardless of how local or reversible it appears."

The first half is legally redundant. The Constitution already says it wins wherever another document disagrees (`docs/internal/CONSTITUTION.md:3-9`).

The second half creates an unresolved collision with the RFC. Section 7 leaves reversible zone filing in its existing state path (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:312-317`), while §12 says ordinary reversible local edits do not pay remote-command ceremony (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:423-430`). Clause 6 says locality and reversibility never matter. Both cannot govern the same act.

The phrase also threatens the power-user case. Article V says actions pass propose, approve, execute (`docs/internal/CONSTITUTION.md:58-67`), but it does not say those must always be three separate interactions. Clause 6's "regardless of how local or reversible" invites exactly that implementation: a second confirmation for the owner's direct, local action even when the initiating gesture already expresses approval.

Current code cannot satisfy it. Direct dictation typing and direct tmux delivery bypass the proposed kernel (`holdspeak/runtime/dictation_capture.py:178-201`, `holdspeak/runtime/dictation_capture.py:422-435`). Phase 106, as scoped, will not migrate them.

Assessment:

- Today: false.
- End of Phase 106: false.
- Later: satisfiable only after broad migration and after the owner resolves what "files" means for direct reversible Desk organization.
- Over-invented: yes. It repeats constitutional supremacy and adds an absolute that conflicts with the RFC's explicit non-goal.
- Under-reaching: no. It reaches too far.

Delete this clause. The nested-effect loophole is already closed by clauses 1, 2, and 5.

## The power-user test

Consider the owner holding the dictation key, speaking a short edit, and releasing into the focused editor. No agent participates.

Capture, transcription, punctuation, and presentation should stay outside consequential admission. The final `desktop.type_text` is the effect. The existing policy already treats ordinary dictation as allowed by the owner's direct gesture, with preview required only under the configured policy (`holdspeak/operation_policy.py:227-244`, `holdspeak/operation_policy.py:376-395`). The runtime then types into the focused application without auto-submit (`holdspeak/runtime/dictation_capture.py:496-511`).

A corrected Article helps here if it allows the held-key gesture to serve as proposal and approval, while the final typing operation gets one receipt. That gives the power user speed and gives HoldSpeak one honest effect record.

The draft can get in the way. The exact wording is clause 6's "passes propose/approve/execute regardless of how local or reversible it appears," combined with clause 4's "only the owner decides." Read literally, those words encourage a separate broker decision after the owner has already made a direct gesture. That buys no consent and adds latency to the product's primary input path.

Now consider an agent connected to a surface HoldSpeak does not support yet, for example an issue tracker other than GitHub. The agent proposes a typed `external.tracker.create_issue` operation with a project ref, destination, and payload. Until trusted startup code registers and implements that operation, the kernel should refuse it by name. Once integrated, the agent submits through the same schema family as the owner, receives only delegated project access, and cannot approve its own proposal. The external API invocation becomes a child operation of the agent run and ends with a terminal receipt.

The Article helps that scenario. It forces a new integration to state its operation, target, authority, egress, and result instead of handing the agent a general network tool. It does not require a special "CTO syscall."

There is one present-tense lie: an agent with ambient Python, shell, or network authority can bypass the whole structure. `PermissionGate` explicitly admits that malicious code can call `subprocess.run` directly (`holdspeak/connector_runtime.py:16-23`), and the raw tmux transport is a public function backed by `subprocess.run` (`holdspeak/tmux_transport.py:20-45`, `holdspeak/tmux_transport.py:85-100`). The Article becomes enforceable for arbitrary agent-connected surfaces only after §5b confinement. Before then it can govern cooperating integrations, but it cannot honestly govern "anything."

## Honest-satisfiability audit

| Clause | Today | End of Phase 106 | Later |
|---|---|---|---|
| 1 | No. Its classification changes with process topology and conflicts with the reversible-shell non-goal. | No as drafted. The kernel spine does not repair the definition. | Only after wording is based on authority and effects rather than process boundaries. |
| 2 | No. Direct typing, tmux, Cadence, and external tool execution bypass it; some successful effects can lack receipts. | No. Terminal and actuator slices do not constitute universal migration. | Yes for cooperating surfaces after broad migration; yes against untrusted code only after confinement. |
| 3 | Partly. Delivery derives and binds authority; gate and authority routes accept caller assertions. | Yes for migrated kernel slices, no as a universal system claim unless old routes are also hardened. | Yes after all authority-bearing entrances use authenticated principals and revocable warrants. |
| 4 | No. The ledger describes adapter capabilities but does not authenticate owner and agent principals. | Potentially yes, but only if principal separation covers decisions, grants, posture, reads, and submissions. | Yes. This is a valid constitutional north star once worded precisely. |
| 5 | Partly. Computation stays cheap, but agent-scoped read authority does not exist. | Yes after amendment and principal separation. | Yes. |
| 6 | No. Existing direct effect paths violate it. | No. Broad typing migration comes later. | Possibly, but only after resolving the contradiction over reversible local filing. |

Clauses 3 and 4 are acceptable north stars while implementation catches up, provided Article X records named drift in every affected story (`docs/internal/CONSTITUTION.md:108-115`). Clauses 2 and 6 are different. They make universal present-tense claims that the adopted migration plan intentionally will not satisfy at the end of Phase 106. Ratifying them now would be dishonest law.

## Amendments ready to paste

Replace clauses 1 through 5 with:

> 1. A consequential operation is an attempted effect governed by Article V, changes or exercises authority, controls a process or machine, invokes a model, crosses egress, or may be irreversible. UI and process topology alone do not make an operation consequential. Each effect is judged for itself; nesting inside an admitted operation never exempts it.
> 2. Every consequential operation that HoldSpeak performs, brokers, or authorizes is admitted exactly once through the kernel before effect and ends in a terminal receipt, including refusal, failure, and indeterminate outcome. Each consequential tool invocation made available to an agent or model is admitted as a causally linked child operation.
> 3. The caller supplies neither a trusted principal nor its own authority. The kernel authenticates the principal and derives the authority basis at admission. The admitted payload, target, and authority basis are immutable; authority may still expire or be revoked before effect.
> 4. Humans and agents use the same operation schemas. Their rights derive from authenticated principal and bounded delegation. Only the owner principal may approve or reject an operation or create and revoke delegation. The owner's direct gesture or prior bounded authorization may supply approval without a redundant hold.
> 5. Reads, ephemeral presentation, and side-effect-free computation, including the token stream inside a model's run, require no consequential-operation admission or receipt. Authentication and read authority still apply. This clause exempts computation and presentation, never effects.

Delete clause 6.

Do not ratify even that replacement until the owner chooses one of these honesty points:

1. Ratify after broad effect migration and confinement, when clause 2 is materially true; or
2. Add an explicit, temporary constitutional migration provision naming unmigrated cooperating paths as declared debt and forbidding agent access to them.

I prefer the first. A migration exception in the Constitution would preserve schedule at the cost of putting scaffolding into permanent law.

## What I would cut

1. Delete clause 6 in full. Constitutional supremacy already exists, and the rest conflicts with §12.
2. Cut "process" from clause 1 as an independent consequence trigger. Process topology is not product semantics.
3. Cut the slash construction "model/egress." Name model invocation and egress separately.
4. Cut "owe the kernel nothing" from clause 5. It is catchy but wrong for authenticated, delegated reads.
5. Cut the explanatory parenthetical after Article XI once the revised clauses stand on their own (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:385-390`). It records a council argument, not constitutional law, and §11 already preserves the amendment history (`docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:406-421`).

The kernel design remains viable. The proposed Article is not ready because it confuses an intended invariant with a currently enforced one, and because its process-boundary definition would put kernel ceremony on ordinary Desk plumbing while missing same-process authority changes. Ratify the law when the code can obey it.
