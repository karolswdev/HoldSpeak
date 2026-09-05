// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-170-04 — rebuilt to the settled artboards: one screen (talk, see
// it land, teach); the old cockpit strip folds behind > Details; the
// footer carries EgressChip THIS DEVICE + receipt + Review/Export.
import "../../desk/components/speak.css";
import { useCallback, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import { download } from "./history";
import type { CoreProps, DictationJournalResponse } from "./core-types";
import { useCoreWings } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import { Button } from "../../components/signal/Signal";
import { EgressChip } from "../../desk/surface/gadgets";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { countToken } from "../../desk/surface";
import { useResource } from "../pageSupport";
import {
  SpeakFace,
  Journal,
  Blocks,
  Readiness,
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

  // Journal count for the footer receipt
  const journalResource = useResource<DictationJournalResponse>(
    "/api/dictation/journal?limit=1",
    {},
  );
  const journalCount = Number(journalResource.data?.count ?? 0);

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

  // Receipt slot for the footer
  const receiptSlot = receipt ? (
    <span
      className="surface-footer-readiness"
      data-tone={receipt.tone === "warn" ? "warn" : undefined}
      role={receipt.tone === "warn" ? "alert" : "status"}
    >
      {receipt.text}
    </span>
  ) : null;

  // Journal count as a token (null at zero per UX-CANON A8)
  const journalToken = countToken(journalCount, "TODAY", "TODAY");

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
      {/* HS-170-04 — the footer: EgressChip THIS DEVICE · receipt ·
          Review (ghost) · Export (ghost). */}
      <SurfaceFooter
        className="speak-footer"
        egress={<EgressChip label="THIS DEVICE" />}
        receipt={
          receiptSlot || (journalToken ? (
            <span className="surface-footer-readiness" role="status">
              {journalToken}
            </span>
          ) : null)
        }
        verbs={
          <>
            <Button
              dense
              variant="ghost"
              onClick={() => wings.setDoorOpen(true)}
            >
              Review
            </Button>
            <Button
              dense
              variant="ghost"
              onClick={() => void exportJournal()}
            >
              Export
            </Button>
          </>
        }
      />
    </>
  );
}
