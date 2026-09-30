// PHILO-11-03 canvas harness: the PRODUCT app (web/index.html, web/src/main.tsx)
// served by vite against a REAL hub on an isolated HOME (the Phase 10 method,
// ../../../phase-10-the-channels/assets/story-04-send-canvas/harness/).
//   CANVAS_MODE=proposal:
//     - every import of web/src/features/channels/channels.ts resolves to
//       harness/p11channels.ts (Slack words; the generic document_ref wire);
//     - SettingsCore's ./connections/Destinations resolves to
//       harness/ProposedDestinations.tsx (Slack in the form);
//     - SEATS: each face where a document lives gets ONE host from
//       harness/P11Hosts.tsx at a NAMED anchor in its product file (SEATS
//       below). A missing or doubled anchor stops the build: the canvas never
//       draws a seat the product file does not have;
//     - REMOVALS (R7): the aftercare Slack rows; the Credentials Slack webhook row;
//     - shim.ts (the unbuilt wire, stated) and canvas.css, loaded before the app.
//   CANVAS_MODE=today: the product exactly as on this branch, no swap, no shim.
// HUB = the real hub's origin (shoot.py starts it and sets this).
import { fileURLToPath, URL } from "node:url";
import { createRequire } from "node:module";

const harness = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("../../../../../../../web/", import.meta.url));
const require = createRequire(`${web}package.json`);
const react = require("@vitejs/plugin-react").default;
const hub = process.env.HUB || "http://127.0.0.1:48901";
const proposal = (process.env.CANVAS_MODE || "proposal") === "proposal";
const hosts = `${harness}P11Hosts.tsx`;
const realChannels = `${web}src/features/channels/channels.ts`;

/** [product file (suffix), import line, [[anchor, replacement], ...]] */
const SEATS = [
  ["src/desk/chair/ChairHome.tsx", `import { P11BriefChip, P11BriefWell, P11MeetingWell } from "${hosts}";`, [
    // A4: the PREPARED ×K chip in the BRIEF head, before the badge and Generate.
    ["      <BriefEgress />\n      <Button", "      {brief ? <P11BriefChip brief={brief} /> : null}\n      <BriefEgress />\n      <Button"],
    // A: the well under the untriaged brief ...
    ["          {generateStatus}\n        </div>\n      ) : !briefLoading && brief ? (",
      "          {generateStatus}\n          {brief ? <P11BriefWell brief={brief} /> : null}\n        </div>\n      ) : !briefLoading && brief ? ("],
    // ... and T3: in the branch the Chair takes after the last item is triaged.
    ["            {generateStatus}\n          </SurfaceSection>\n        </div>\n      ) : null}",
      "            {generateStatus}\n          </SurfaceSection>\n          <P11BriefWell brief={brief} />\n        </div>\n      ) : null}"],
    // C6: the Chair's MEETINGS row, unfolded: SUMMARY, then SEND.
    ["        <MeetingSummarySlab\n          intel={{ summary, topics: meeting.intelTopics ?? [] }}\n          receipt={receipt}\n        />",
      "        <><MeetingSummarySlab\n          intel={{ summary, topics: meeting.intelTopics ?? [] }}\n          receipt={receipt}\n        /><P11MeetingWell id={meeting.id} startedAt={meeting.startedAt} /></>"],
  ]],
  ["src/desk/pullouts/views/BriefView.tsx", `import { P11BriefWell } from "${hosts}";`, [
    // A: the Intelligence BRIEF view: after the person sections.
    ["      ) : null}\n    </>\n  );\n\n  return (", "      ) : null}\n      <P11BriefWell brief={brief} />\n    </>\n  );\n\n  return ("],
  ]],
  ["src/desk/pullouts/DecisionPullout.tsx", `import { P11DeskDecisionWell } from "${hosts}";`, [
    // B1: the decision window, under the record, above the filing strip and the footer.
    ["        </section>\n        <DeskFilingStrip", "          {!editingDecision ? <P11DeskDecisionWell id={o.id} /> : null}\n        </section>\n        <DeskFilingStrip"],
  ]],
  ["src/desk/pullouts/views/DecisionsView.tsx", `import { P11RecordWell } from "${hosts}";`, [
    // B5: Intelligence -> DECISIONS, the record: after its fields.
    ["      </dl>\n      <section className=\"receipt-provenance\"", "      </dl>\n      <P11RecordWell id={receipt.id} />\n      <section className=\"receipt-provenance\""],
  ]],
  ["src/features/project-room/ProjectRoomCore.tsx", `import { P11RoomRow } from "${hosts}";`, [
    // B5/B4: the Room's DECISIONS & COMMITMENTS rows (decision RECORDS, design 6a), both row shapes.
    [/<SurfaceLedgerRow(\s+)key=\{`dec-\$\{dec\.id\}`\}/g, "<P11RoomRow dec={dec}$1key={`dec-${dec.id}`}", 2],
  ]],
  ["src/pages/cores/history/MeetingDetail.tsx", `import { P11MeetingWell } from "${hosts}";`, [
    // C1: the Meetings record: SUMMARY, then SEND (no well without a summary: C4).
    ["<MeetingSummarySlab intel={summaryIntel} receipt={runReceipt} />",
      "<MeetingSummarySlab intel={summaryIntel} receipt={runReceipt} />\n          {summaryIntel?.summary ? <P11MeetingWell id={id} startedAt={String((detail ?? meeting)?.started_at ?? \"\")} /> : null}"],
    // C5 / R7: the aftercare Slack group is gone (its Send only proposed).
    ["          <AftercareGadgets\n            aftercare={aftercare}\n            authority={authority}\n            busy={busy}\n            proposeSlack={proposeSlack}\n          />", "          {null}"],
  ]],
  ["src/desk/pullouts/MeetingPullout.tsx", `import { P11MeetingWell } from "${hosts}";`, [
    // C6: the meeting window: summary and topics, then SEND.
    ["        {detail?.intel?.action_items &&\n          detail.intel.action_items.length > 0 && (",
      "        {detail?.intel?.summary ? <P11MeetingWell id={o.id} startedAt={String(detail?.started_at ?? \"\")} /> : null}\n        {detail?.intel?.action_items &&\n          detail.intel.action_items.length > 0 && ("],
  ]],
  ["src/pages/cores/SettingsCore.tsx", null, [
    // D4 / R7: Credentials without the Slack webhook row (no migration: he adds a Slack destination).
    ["([id]) => !RAW_SECRETS.has(id),", "([id]) => !RAW_SECRETS.has(id) && id !== \"slack_webhook_url\","],
  ]],
  ["src/features/project-room/update/UpdatePosture.tsx", null, [
    // E1: the update composes the same species (its Phase 10 history and manual row stay).
    ["import { ListChips, PublishedWells } from \"../../channels/SendWell\";", `import { ListChips, PublishedWells } from "${hosts}";`],
  ]],
];

function seats() {
  return {
    name: "philo-11-03-seats",
    enforce: "pre",
    transform(code, id) {
      const file = id.split("?")[0];
      for (const [suffix, imp, edits] of SEATS) {
        if (!file.endsWith(`/web/${suffix}`)) continue;
        let out = code;
        for (const [anchor, repl, want = 1] of edits) {
          const n = typeof anchor === "string" ? out.split(anchor).length - 1 : (out.match(anchor) || []).length;
          if (n !== want) throw new Error(`PHILO-11-03 seat anchor in ${suffix}: found ${n}, want ${want}: ${String(anchor).slice(0, 80)}`);
          out = typeof anchor === "string" ? out.replace(anchor, repl) : out.replace(anchor, repl);
        }
        return imp ? `${imp}\n${out}` : out;
      }
      return null;
    },
    async resolveId(source, importer, options) {
      if (!importer || importer.includes("/story-03-canvas/harness/p11channels.ts")) return null;
      if (source.endsWith("/channels") || source.endsWith("/channels/channels") || source === "./channels") {
        const r = await this.resolve(source, importer, { ...options, skipSelf: true });
        if (r && r.id.split("?")[0] === realChannels) return `${harness}p11channels.ts`;
      }
      if (source === "./connections/Destinations" && importer.endsWith("/SettingsCore.tsx")) return `${harness}ProposedDestinations.tsx`;
      return null;
    },
  };
}

export default {
  root: web,
  base: "/",
  configFile: false,
  plugins: [
    // The seats read the product SOURCE: before the React transform.
    proposal && seats(),
    react(),
    // Mount as the production bundle mounts (no StrictMode double effects; Phase 10 README).
    {
      name: "philo-11-03-no-strict-double-mount",
      enforce: "pre",
      transform: (code, id) =>
        id.endsWith("/web/src/main.tsx") ? code.replace("<StrictMode>", "<>").replace("</StrictMode>", "</>") : null,
    },
    {
      name: "philo-11-03-canvas",
      transformIndexHtml: (html) =>
        html.replace(
          "</head>",
          (proposal
            ? `<link rel="stylesheet" href="/@fs${harness}canvas.css"><script type="module" src="/@fs${harness}shim.ts"></script>`
            : "") + `<script type="module" src="/@fs${harness}nav.ts"></script></head>`,
        ),
    },
  ].filter(Boolean),
  define: { __HOLDSPEAK_BUILD__: JSON.stringify(proposal ? "canvas-philo-11-03" : "canvas-philo-11-03-today") },
  resolve: {
    alias: [
      { find: "@w/features/channels/channels.real", replacement: realChannels },
      { find: "@w", replacement: `${web}src` },
    ],
  },
  server: {
    host: "127.0.0.1",
    port: Number(process.env.CANVAS_PORT || 4461),
    strictPort: true,
    fs: { allow: [web, harness] },
    proxy: {
      "/api": { target: hub, changeOrigin: true, ws: true },
      "/ws": { target: hub, changeOrigin: true, ws: true },
    },
  },
};
