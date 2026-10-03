// Canvas plumbing for BOTH stories (not a proposal): the run's scratch HOME reads as ~, exactly as the
// product shows /Users/<name> as ~ (C1's channels.ts seat, widened to the proof and the preview field).
const HOME_RE = String.raw`.replace(/^\/(private\/)?tmp\/p13c57-[^/]+/, "~")`;

export default [
  ["src/desk/surface/send/SendWell.tsx#home", null, [
    ["  if (channel === \"file\") return <span className=\"surface-token send-literal send-wrap\" data-chip data-testid=\"proof\">{String(p.path ?? \"\")}</span>;",
      `  if (channel === "file") return <span className="surface-token send-literal send-wrap" data-chip data-testid="proof">{String(p.path ?? "")${HOME_RE}}</span>;`],
  ]],
  // The scratch HOME reads as ~ (the product shows a home folder as ~).
  ["src/features/channels/channels.ts", null, [
    ["    case \"file\": return String(t.folder ?? \"\").replace(/^\\/Users\\/[^/]+/, \"~\");",
      `    case "file": return String(t.folder ?? "").replace(/^\\/Users\\/[^/]+/, "~")${HOME_RE};`],
    ["        fields: [{ label: \"Folder\", value: String(t.folder ?? \"\") },",
      `        fields: [{ label: "Folder", value: String(t.folder ?? "")${HOME_RE} },`],
  ]],
];
