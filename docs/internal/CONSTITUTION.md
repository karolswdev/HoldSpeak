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
