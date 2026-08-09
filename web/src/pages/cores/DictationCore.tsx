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
import { apiFetch } from "../../lib/api";
import { download } from "./history";
import type { CoreProps, DictationJournalResponse } from "./core-types";
import { useCoreWings } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import {
  SpeakFace,
  Journal,
  Blocks,
  Readiness,
  ReadinessFooter,
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
  const exportJournal = async () => {
    try {
      const overview = await apiFetch<DictationJournalResponse>(
        "/api/dictation/journal?limit=1",
      );
      const { items = [] } = await apiFetch<DictationJournalResponse>(
        `/api/dictation/journal?limit=${Math.max(Number(overview.count) || 0, 1)}`,
      );
      const markdown = [
        "# HoldSpeak journal",
        "",
        ...items.flatMap((entry) => {
          const timestamp = String(entry.created_at ?? entry.timestamp ?? "");
          const destination = String(entry.target_profile ?? entry.intent ?? "");
          return [
            `## ${timestamp || "Undated"}`,
            "",
            String(entry.transcript ?? ""),
            ...(destination ? ["", `- Destination: ${destination}`] : []),
            "",
          ];
        }),
      ].join("\n");
      download(
        new Blob([markdown], { type: "text/markdown;charset=utf-8" }),
        `holdspeak-journal-${new Date().toISOString().slice(0, 10)}.md`,
      );
      announce("EXPORTED MD");
    } catch {
      announce("EXPORT FAILED", "warn");
    }
  };
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
      {/* HS-129-05 — Speak publishes one frame-owned foot: pipeline state,
          the landing receipt, Review, and Export share the same slots. */}
      <ReadinessFooter
        onOpenDoor={() => wings.setDoorOpen(true)}
        receipt={receipt}
        exportVerb={
          <button
            type="button"
            className="desk-chip"
            onClick={() => void exportJournal()}
          >
            Export
          </button>
        }
      />
    </>
  );
}
