// Conductor canvas seats: [product file (suffix), import line or null, [[anchor, replacement, count?], ...]].
// Each hook calls conductor.tsx; with the shim absent each is a no-op. A missing or doubled anchor
// stops the server (the seat guard in vite.config.mjs).
const G = "(globalThis as any)";

export default [
  // Q1: the Agents card after Connections.
  ["src/desk/firstrun/FirstRun.tsx", null, [
    ["        <ConnectionsCard step={connections} lit={connectionsLit} />\n      </div>\n",
      `        <ConnectionsCard step={connections} lit={connectionsLit} />\n      </div>\n      {${G}.__kFirstRun?.()}\n`],
  ]],
  // Q3: the launch sheet mounts beside the Ask AI panel (the same docked-window posture).
  ["src/desk/DeskApp.tsx", null, [
    ["      {!arrivalRequired && !showFloor && askOpen && <AskPanel />}\n",
      `      {!arrivalRequired && !showFloor && askOpen && <AskPanel />}\n      {!arrivalRequired && ${G}.__kDesk?.()}\n`],
  ]],
  // Q2/Q4/Q5 on the Door (Needs you): the coder row first, the head count, the flight chip, the row verb.
  ["src/desk/chair/ChairHome.tsx", null, [
    ["  const total = count + Math.max(0, pending);\n",
      `  const total = count + Math.max(0, pending) + (${G}.__kCoderCount?.() ?? 0);\n`],
    ["          <SurfaceLedger count={null} cols=\"room\">\n            {visible.map((item, i) => (\n",
      `          <SurfaceLedger count={null} cols="room">\n            {${G}.__kCoderRows?.(muted)}\n            {visible.map((item, i) => (\n`],
    ["    <SurfaceSection label={attentionCaption(visible.length, filtered.length, label)}>\n",
      `    <SurfaceSection label={attentionCaption(visible.length + (muted ? 0 : (${G}.__kCoderCount?.() ?? 0)), filtered.length + (muted ? 0 : (${G}.__kCoderCount?.() ?? 0)), label)}>\n`],
    ["                primary={!muted && i === 0}\n",
      `                primary={!muted && i === 0 && !${G}.__kCoderFirst?.()}\n`],
    ["            {reasonToken(doorOwnerNamed ? rowItem : item, now)}\n          </span>\n",
      `            {reasonToken(doorOwnerNamed ? rowItem : item, now)}\n          </span>\n          {${G}.__kRowChip?.(item)}\n`],
    ["      trailing={\n        <NeedsYouRowVerbs\n",
      "      trailing={<>\n        <NeedsYouRowVerbs\n"],
    ["          onCommitWell={(well) => { setCommitDraft(\"\"); setCommitWell(well); }}\n        />\n      }\n",
      `          onCommitWell={(well) => { setCommitDraft(""); setCommitWell(well); }}\n        />\n        {${G}.__kRowVerb?.(item)}\n      </>}\n`],
    // Q4 (K3's refetch): the arrival AGENTS section lists every live session from /api/coders/sessions.
    ["          {agentSessions.length > 0 ? (\n            <div data-testid=\"arrival-agents\">\n              <AgentsSection sessions={agentSessions} />\n",
      `          {(${G}.__kAgentSessions?.() ?? agentSessions).length > 0 ? (\n            <div data-testid="arrival-agents">\n              <AgentsSection sessions={${G}.__kAgentSessions?.() ?? agentSessions} />\n`],
    // Q4: the AGENTS row names its item and wears the flight chip.
    ["              cells={\n                <span className=\"arrival-meeting-badge\" data-badge={rowBlocked ? \"off\" : \"saved\"}>\n                  {rowBlocked ? \"BLOCKED\" : \"RUNNING\"}\n                </span>\n              }\n",
      `              cells={\n                ${G}.__kAgentCells?.(key, rowBlocked) ?? <span className="arrival-meeting-badge" data-badge={rowBlocked ? "off" : "saved"}>\n                  {rowBlocked ? "BLOCKED" : "RUNNING"}\n                </span>\n              }\n`],
  ]],
  // Q2/Q4/Q6 in the Room: OPEN HERE rows wear the chip and the verb; the receipt line names a closed item.
  ["src/features/project-room/ProjectRoomCore.tsx", null, [
    ["                    {needsYouWhyWords(item)}\n                  </span>\n                }\n                trailing={\n                  item.verb === \"decide\" ? (\n",
      `                    {needsYouWhyWords(item)}\n                  </span>\n                  {${G}.__kRoomChip?.(item)}</span>\n                }\n                trailing={<><span className="k-tokens">{${G}.__kRoomVerb?.(item)}</span>{\n                  item.verb === "decide" ? (\n`],
    ["                cells={\n                  <span\n                    className=\"surface-token room-why-token\"\n                    style={{ color: severityColor(item.severity) }}\n",
      "                cells={<span className=\"k-tokens k-room-cells\">\n                  <span\n                    className=\"surface-token room-why-token\"\n                    style={{ color: severityColor(item.severity) }}\n"],
    ["                      Open\n                    </Button>\n                  ) : null\n                }\n              />\n",
      `                      Open\n                    </Button>\n                  ) : null\n                }</>}\n              />\n`],
    ["        receipt={footerReceipt}\n",
      `        receipt={${G}.__kRoomReceipt?.() ?? footerReceipt}\n`],
  ]],
  // Q5: Speak answer opens the steer composer (already recording); Enter sends.
  ["src/desk/components/SessionPullout.tsx", null, [
    ["          onKeyDown={(event) => {\n            if (event.key !== \"Escape\") return;\n",
      "          onKeyDown={(event) => {\n            if (event.key === \"Enter\" && !event.shiftKey) { event.preventDefault(); void send(); return; }\n            if (event.key !== \"Escape\") return;\n"],
    // The question shows for a waiting session (the hook's Notification), and Speak answer opens an
    // answer well IN THE BODY under it: the steer composer, its mic already recording.
    ["        {session?.awaitingResponse && session.question ? (\n          <pre className=\"desk-pullout-md desk-session-question\">\n            {session.question}\n          </pre>\n        ) : null}\n",
      `        {(session?.awaitingResponse || ${G}.__kSteerOpen?.()) && session?.question ? (\n          <pre className="desk-pullout-md desk-session-question">\n            {session.question}\n          </pre>\n        ) : null}\n        {${G}.__kSteerOpen?.() ? <div className="k-answer-well" data-testid="k-answer-well"><SteerComposer /></div> : null}\n`],
  ]],
  ["src/desk/components/MicButton.tsx", null, [
    ["  const [state, setState] = useState<MicState>(\"idle\");\n",
      `  const [state, setState] = useState<MicState>(() => (${G}.__kMicStart?.(draftScope) ? "listening" : "idle"));\n`],
  ]],
];
