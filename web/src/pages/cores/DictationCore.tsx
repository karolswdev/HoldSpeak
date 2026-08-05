// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-98-02 — re-crafted native on the window material.
// HS-100-07 — Speak: the application opens ON the job (speak, see it
// land, judge it, teach it — trace B's loop is the entire front face);
// Journal and Blocks are the wings; Memory/Knowledge/Runtime/Hooks/
// Nudges and full readiness fold behind the one gear door
// (APPLICATION_LAYER_THESIS.md §1.1). Wire calls and verbs unchanged.
// HS-111-02 — the OS's dictation deck (audit §3): the cockpit is an
// instrument strip (TALK transport key, LED level meter, STATE
// register, etched readout cells); the Journal is a machine ledger
// (SurfaceLedger); the gear door is ONE gadget sheet; and every toast
// banner died into the footer receipt bar (the Prefs pattern).
// HS-117-08 — decomposed: sub-components live under dictation/.
import "../../desk/components/speak.css";
import { useCallback, useMemo, useState } from "react";
import type { CoreProps } from "./core-types";
import { useCoreWings } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import {
  SpeakFace,
  Journal,
  Blocks,
  Readiness,
  ReadinessLine,
  Memory,
  Knowledge,
  Runtime,
  Hooks,
  Nudges,
  ReceiptContext,
  type Receipt,
  type ReceiptTone,
} from "./dictation";

const WINGS = [
  { id: "speak", label: "Speak" },
  { id: "journal", label: "Journal" },
  { id: "blocks", label: "Blocks" },
];

/* HS-100-07 — the one door: everything that is configuration
   (readiness diagnostics, memory, knowledge, runtime, hooks, nudges)
   stacked behind the gear. HS-111-02: the stack is ONE gadget sheet
   on the window material — full width, 26px rows, no settings mile. */
function Configure() {
  return (
    <div className="surface-door">
      <Readiness />
      <Memory />
      <Knowledge />
      <Runtime />
      <Hooks />
      <Nudges />
    </div>
  );
}

export function DictationCore({ hero, scope, scopeLabel }: CoreProps) {
  const wings = useCoreWings(WINGS, "speak", "Configure dictation");
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const announce = useCallback((text: string, tone: ReceiptTone = "ok") => {
    setReceipt(text ? { text, tone } : null);
  }, []);
  const active = wings.doorOpen ? "configure" : wings.view;
  const current = useMemo(
    () =>
      ({
        speak: <SpeakFace />,
        journal: <Journal />,
        blocks: <Blocks />,
        configure: <Configure />,
      })[active],
    [active],
  );
  return (
    <>
      {renderHeroSlot(hero, null)}
      {scope ? (
        <p className="desk-scope-chip">
          <span aria-hidden="true">⌁</span> About {scopeLabel || scope}
        </p>
      ) : null}
      <ReceiptContext.Provider value={announce}>
        {current}
      </ReceiptContext.Provider>
      <ReadinessLine onOpenDoor={() => wings.setDoorOpen(true)} receipt={receipt} />
    </>
  );
}
