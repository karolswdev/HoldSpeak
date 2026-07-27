# The Constitution of HoldSpeak

Ratified by the owner's charter of 2026-07-17, born from the first live UAT
sitting. This is the north star: the supreme canon of the product. Every
phase, story, design decision, and doc is measured against these articles.
Where any other document disagrees with this one, this one wins and the
other must be amended (or this one must be, by the owner, in Article X's
process). Positioning, plans, and phase charters elaborate these articles;
they do not override them.

## Preamble

HoldSpeak is one local copilot with a place to live: the Desk. Your voice
types anywhere and learns how you work; your meetings end with their loops
closed; your agents, terminals, and delivery work sit on the same surface
you do. All of it local, all of it yours, all of it through the Desk.

## Article I — The Desk is the operating surface

1. The Desk is not a feature, a view, or a tier. It is the product's
   operating surface: the place where everything is seen, opened, and done.
2. Features do not own surfaces. The OS owns surfaces (objects, windows,
   the dock, the stage) and features plug into them.
3. No interaction that starts on the Desk may eject the user to a
   feature-owned screen. Routes exist only as deep links that open the Desk
   in the right state.
4. This article supersedes the page-based information architecture in
   `POSITIONING.md` (Phase 70). That section is to be amended, not obeyed.

## Article II — Everything is a primitive

1. Every capability the product offers is a system primitive: dictation,
   meetings, intelligence, steering, terminals, delivery, configuration,
   profiles, the mesh.
2. A primitive exposes a contract (API, schema, events) and a core surface.
   The OS decides where and how that surface appears.
3. Every thing the user touches is a DeskPrimitive with derived UI. New
   capability means a new primitive or a new affordance on one, never a new
   world.

## Article III — Local first, honest egress

1. Nothing leaves the machine by default. Intelligence runs where the user
   put it: in process, on their metal, or at an endpoint they named.
2. Egress is disclosed by the badge (local / local+cloud / cloud) at the
   point of decision. Never by prose, never by reassurance.
3. No account, no telemetry, no silent cloud dependency. Ever.

## Article IV — Voice is a first-class input

1. Every text input can be spoken into. The mic is an affordance of the OS,
   not of any one feature.
2. Voice arms; it does not fire. Wake and command surfaces prepare actions
   for a human to confirm, in line with Article V.
3. One mic authority at a time: surfaces never compete for capture, and the
   owner of the mic is always visible.

## Article V — Consent is the spine of action

1. Watching is free; acting is armed. Anything that types, sends, files,
   spawns, or kills passes propose, approve, execute.
2. Every attempt leaves a receipt: who, what, where, outcome. The audit is
   part of the act, not an accessory.
3. Refusal is by name. When the product will not act, it says which rule
   refused and what would satisfy it.
4. Reach never outruns consent: more machines, more panes, more connectors
   always ride the same chokepoints.
5. Article XI names the one chokepoint and what it must record. It carries
   this article's spine into the kernel; it never narrows it.

## Article VI — Honest by construction

1. The product states its own limits where the user meets them: the doctor
   reports what is broken, counts are honest at zero, approximations are
   labeled.
2. No demo state, no seeded flattery, no fallback that hides a failure. A
   broken dependency produces a named failure, not a quiet degradation.
3. Copy never promises what the code does not do. The test suite locks the
   honest claims.

## Article VII — The interface serves, it does not speak

1. No prose in the UI. Labels state what, in the fewest words. No how-to,
   no reassurance, no selling.
2. No modals. Everything is created and edited in-world, in place, on the
   Desk.
3. Chrome is quiet: one window grammar, one z ladder, one dock. The user's
   arrangement is sacred and persists.

## Article VIII — Native-grade craft

1. The Desk must feel like an OS, not a website: GPU-rendered world,
   compositor-only motion, 60fps interaction budget on the production
   bundle.
2. Physics are contracts: drag, resize, raise, persist, coexist, snap. Once
   shipped, they are a floor no change may regress.
3. Every glass is first-class: the workstation window, the phone's bottom
   sheet, the iPad's diorama. Craft is not a desktop-only property.

## Article IX — Proof over claim

1. Nothing is done because its code merged. It is done when it ran: real
   hub, real mic, real model, real device, real viewport.
2. UI ships only after it was seen: production screenshot walks at real
   sizes, and the owner's eyes for anything that changes the feel.
3. Evidence rides with the change through the delivery rails. A claim
   without a receipt is a defect.
4. The owner's live verdict outranks every green suite.

## Article X — Amendment

1. Only the owner amends this constitution. Agents propose; the owner
   ratifies.
2. A phase that touches an article cites it in its charter. A story that
   cannot satisfy an article says so before it starts, not after it ships.
3. When practice and constitution drift, one of them is wrong on purpose.
   The drift is named and resolved; it is never ignored.

## Article XI — The Kernel

1. A consequential operation is one that acts under Article V, exercises or
   changes authority, controls a process or machine, invokes a model,
   crosses egress, or may be irreversible. Topology decides nothing:
   crossing a process boundary does not make an act consequential, and
   staying inside one does not exempt it. Each effect is judged for itself;
   nesting inside an admitted operation exempts nothing.
2. Every consequential operation HoldSpeak performs, brokers, or authorizes
   is admitted once through the kernel before it acts, and ends in a
   terminal receipt — including refusal, failure, and the outcome that
   cannot be determined. A tool effect offered to a model or an agent is
   admitted as a child of the run that offered it.
3. The caller supplies neither its principal nor its authority. The kernel
   authenticates the one and derives the other at admission. Payload,
   target, and authority basis are then immutable; the right to execute may
   still expire or be revoked.
4. Humans and agents share the kernel's schemas, never its rights. Rights
   come from an authenticated principal and bounded delegation. Only the
   owner approves, rejects, or delegates. The owner's own gesture is
   approval; consent is not a second confirmation of what the owner just
   did.
5. Reads, presentation, and computation without effect — including the
   token stream inside a model's run — owe the kernel no admission and no
   receipt. They still owe it an authenticated principal and read
   authority. This exempts computation, never effects.
6. *(Transitional.)* Until the effect register is empty, the paths it names
   act outside the kernel as declared debt. The register is checked in and
   enumerated; no path joins it silently; no agent principal may reach a
   path it names. This clause and the register expire together, on the day
   the register is empty.

## Amendment record

- **2026-07-26 — Article XI (The Kernel) ratified**, and Article V gained
  clause 5 pointing to it. Proposed in
  `PLAN_KERNEL_OPERATION_BROKER.md` §10, amended by the fourth council
  pass, ratified by the owner in Phase 106 (HS-106-01).
  Clause 6 is transitional and self-repealing: it expires with the effect
  register (`holdspeak/kernel/effect_ledger.json`), which is empty when
  every path it names has been migrated. The council's dissent — that
  ratification should wait until clause 2 is materially true — is recorded
  at `pm/roadmap/holdspeak/proposals/kernel-council-sol-article-xi.md`
  and was overruled under Article X.1.
