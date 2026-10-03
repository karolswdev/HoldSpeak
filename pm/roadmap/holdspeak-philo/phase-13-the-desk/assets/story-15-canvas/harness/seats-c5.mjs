// PHILO-13-15 (C5) seats: [product file (suffix, #tag), import line or null, [[anchor, replacement, count?], ...]].
// Each hook calls c5.tsx; with the shim absent each is a no-op.
const G = "(globalThis as any)";
const HOME_RE = String.raw`.replace(/^\/(private\/)?tmp\/p13c57-[^/]+/, "~")`;

export default [
  // P1: the window's right-button / long-press menu leads with `Send to ▸` (one composition).
  ["src/desk/components/DeskWindow.tsx", null, [
    ["          entries={headMenuEntries({",
      `          entries={(${G}.__c5HeadMenu ?? ((_i: string, e: unknown) => e))(id, headMenuEntries({`],
    ["            toBack: () => sendWindowToBack(id),\n          })}",
      "            toBack: () => sendWindowToBack(id),\n          }))}"],
  ]],
  // P1: the menu bar's Object menu (393: the Object group inside Go), from the FRONT window's document.
  ["src/desk/components/DeskMenuBar.tsx", null, [
    ["      for (const m of MENUS) if (m.id !== \"go\") menuEntries(m.id, out);\n    return out;",
      `      for (const m of MENUS) if (m.id !== "go") menuEntries(m.id, out);\n    ${G}.__c5BarSend?.(id, compact, out);\n    return out;`],
  ]],
  // P3: the push seam -- a pick set into the well; an open well reacts in place.
  ["src/desk/surface/send/SendWell.tsx", null, [
    ["const bump = () => { store.tick++; store.subs.forEach((f) => f()); };",
      `const bump = () => { store.tick++; store.subs.forEach((f) => f()); };\n${G}.__c5Pick = (ref: string, id: string | null) => { store.picked.set(ref, id); bump(); };\n${G}.__c5Picked = (ref: string) => store.picked.get(ref) ?? null;`],
  ]],
  // P3 (G8): Summary -> Digest -> Follow-up keeps the picked destination.
  ["src/meetings/MeetingSendWell.tsx", null, [
    ["onChange={(v) => { formPick.set(meetingId, v as Form); setKind(v as Form); }} />",
      `onChange={(v) => { ${G}.__c5FormMove?.(meetingId, kind, v); formPick.set(meetingId, v as Form); setKind(v as Form); }} />`],
  ]],
  // P1 (project): the Room link { projectId, updateId, destinationId }, also when the Room is open.
  ["src/features/project-room/ProjectRoomCore.tsx", `import { fetchUpdates as __c5FetchUpdates } from "./update/api";`, [
    ["  const updateCtrl = useUpdateController(\n    ctrl.projectId, () => void ctrl.load(),\n  );\n",
      `  const updateCtrl = useUpdateController(\n    ctrl.projectId, () => void ctrl.load(),\n  );\n  useEffect(() => {\n    const on = (e: Event) => {\n      const d = (e as CustomEvent).detail;\n      if (!d || d.projectId !== ctrl.projectId) return;\n      ${G}.__c5RoomLinkTaken = d.token;\n      void __c5FetchUpdates(d.projectId).then((list) => {\n        const u = list.find((x) => x.id === d.updateId);\n        if (!u) return;\n        updateCtrl.openUpdate(u);\n        window.setTimeout(() => { ${G}.__c5Pick?.(\`project_update:\${u.id}\`, d.destinationId); ${G}.__c5Arrive?.(\`project_update:\${u.id}\`, "surface-project-memory"); }, 400);\n      });\n    };\n    window.addEventListener("c5:room-link", on);\n    return () => window.removeEventListener("c5:room-link", on);\n  }, [ctrl.projectId, updateCtrl.openUpdate]);\n`],
  ]],
  // P5: the artifact window -- its SEND well on artifact:<id>; its three raw buttons are library Buttons.
  ["src/desk/pullouts/ArtifactPullout.tsx",
    `import { Button as __C5Button } from "../../components/signal/Signal";\nimport { SendWells as __C5SendWells } from "../surface/send";`, [
    ["          <Material>{body}</Material>\n        </section>",
      `          <Material>{body}</Material>\n        </section>\n        {${G}.__c5 ? <div data-seat="artifact"><__C5SendWells doc={{ ref: \`artifact:\${o.id}\`, title: String(ir.title || "Artifact"), label: \`ARTIFACT · \${String(ir.artifactType || "artifact").replace(/[_-]+/g, " ").toUpperCase()}\` }} /></div> : null}`],
    ["                <button\n                  key={f.ref}\n                  type=\"button\"\n                  className=\"desk-chip quiet\"\n                  onClick={() => f.resolved && openPullout(f.ref)}\n                >\n                  {f.label}\n                </button>",
      "                <__C5Button key={f.ref} dense variant=\"ghost\" onClick={() => f.resolved && openPullout(f.ref)}>\n                  {f.label}\n                </__C5Button>"],
    ["        <button\n          type=\"button\"\n          className=\"desk-chip quiet\"\n          onClick={() => void copy(body)}\n        >\n          Copy\n        </button>",
      "        <__C5Button dense variant=\"ghost\" onClick={() => void copy(body)}>Copy</__C5Button>"],
    ["        <button\n          type=\"button\"\n          className=\"desk-chip quiet\"\n          onClick={() =>\n            openSurfaceOr(\"dictate\", \"/dictation\", resourceRef)\n          }\n        >\n          Dictate about this\n        </button> </>} />",
      "        <__C5Button dense variant=\"ghost\" onClick={() => openSurfaceOr(\"dictate\", \"/dictation\", resourceRef)}>Dictate about this</__C5Button></>} />"],
  ]],
];
