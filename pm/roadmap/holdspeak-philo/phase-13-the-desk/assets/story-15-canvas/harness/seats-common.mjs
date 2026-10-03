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
  // BUILD OBLIGATION of C5/C7 (Astra canvas r1, conditions 2 and 4), drawn here, built in DeskMenu.tsx:
  //  (a) 393: a submenu inside a submenu opens (Go ▸ Object ▸ Send to ▸); main stops after the first
  //      level (the replaced panel's rows get setOpenSub={() => {}}). The back row climbs one level.
  //  (b) 1440: a submenu opens NEXT TO its parent panel (right side if it fits, else left side); main's
  //      fallback clamped it to the viewport's right edge, far from the parent.
  ["src/desk/components/DeskMenu.tsx", null, [
    ["  const [openSub, setOpenSub] = useState<string | null>(null);\n",
      "  const [openSub, setOpenSub] = useState<string | null>(null);\n  const [__c57Sub2, __c57SetSub2] = useState<string | null>(null);\n  useEffect(() => { __c57SetSub2(null); }, [openSub]);\n"],
    ["      const overParent = Boolean(flipFrom && r.left < flipFrom.right - 1 && r.right > flipFrom.left);\n      if (!NARROW() && (r.right > window.innerWidth - margin || overParent)) {\n        const flipped = flipFrom ? flipFrom.left - r.width - 1 : -1;\n        el.style.left = `${flipped >= margin ? flipped : Math.max(margin, window.innerWidth - margin - r.width)}px`;\n      }",
      "      if (!NARROW() && flipFrom) {\n        const right = flipFrom.right + 1, left = flipFrom.left - r.width - 1;\n        el.style.left = `${right + r.width <= window.innerWidth - margin ? right : left >= margin ? left : Math.max(margin, window.innerWidth - margin - r.width)}px`;\n      } else if (!NARROW() && r.right > window.innerWidth - margin) {\n        el.style.left = `${Math.max(margin, window.innerWidth - margin - r.width)}px`;\n      }"],
    ["            className=\"desk-menu-back\"\n            onClick={() => setOpenSub(null)}\n          >",
      "            className=\"desk-menu-back\"\n            onClick={() => (__c57Sub2 ? __c57SetSub2(null) : setOpenSub(null))}\n          >"],
    ["            <span className=\"desk-menu-label\">{sub.label}</span>\n          </Button>\n          <WorkMenuSep />\n          <WorkMenuRows\n            entries={sub.entries}\n            onClose={onClose}\n            openSub={null}\n            setOpenSub={() => {}}\n            onSubAnchor={() => {}}\n            hasLane={panelHasLane(sub.entries)}\n            collapsedReason={collapseGhostReason(sub.entries)}\n          />",
      "            <span className=\"desk-menu-label\">{(__c57Sub2 && (sub.entries.find((e) => e.type === \"sub\" && e.id === __c57Sub2) as any)?.label) || sub.label}</span>\n          </Button>\n          <WorkMenuSep />\n          {(() => { const s2 = __c57Sub2 ? (sub.entries.find((e) => e.type === \"sub\" && e.id === __c57Sub2) as Extract<WorkMenuEntry, { type: \"sub\" }> | undefined) : undefined; const rows = s2 ? s2.entries : sub.entries; return (\n          <WorkMenuRows\n            entries={rows}\n            onClose={onClose}\n            openSub={null}\n            setOpenSub={s2 ? () => {} : (id: string | null) => __c57SetSub2(id)}\n            onSubAnchor={() => {}}\n            hasLane={panelHasLane(rows)}\n            collapsedReason={collapseGhostReason(rows)}\n          />); })()}"],
  ]],
];
