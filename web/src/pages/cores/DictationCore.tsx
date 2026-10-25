// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-170-04 — rebuilt to the settled artboards: one screen (talk, see
// it land, teach); the old cockpit strip folds behind > Details; the
// footer carries the receipt + Review/Export; the egress badge lives
// beside the verb, on the SPEAK wing's engine row (HS-202-02).
import "../../desk/components/speak.css";
import { useCallback, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import { download } from "./history";
import type { CoreProps, DictationJournalResponse } from "./core-types";
import { useCoreWings } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import { Button } from "../../components/signal/Signal";
import { StatusBar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { openSurfaceOr } from "../../desk/shell";
import { FoldGadget } from "../../desk/surface";
import { useResource } from "../pageSupport";
import { useBuilderTools } from "../../desk/builderTools";
import {
  SpeakFace,
  SpeakStatusContext,
  Journal,
  Learned,
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
import { CommandsCore } from "./CommandsCore";
/* C11 — the fifth wing. Imported from its module rather than the dictation
   barrel: `index.ts` belongs to story 03's lane in this branch. */

/* C11 — five wings, always present: SPEAK · JOURNAL · BLOCKS · LEARNED ·
   VOICE COMMANDS. `useCoreWings` takes the array, so the new wing needs no
   shape change. The corrections table moved OUT of the Configure door and
   became `Learned`; the door keeps the digest. */
const WINGS = [
  { id: "speak", label: "Speak" },
  { id: "journal", label: "Journal" },
  { id: "blocks", label: "Blocks" },
  { id: "learned", label: "Learned" },
  { id: "commands", label: "Voice commands" },
];

/* HS-100-07 — the one door: everything that is configuration
   (readiness diagnostics, memory, knowledge, runtime, hooks, nudges)
   stacked behind the gear. HS-111-02: the stack is ONE gadget sheet
   on the window material — full width, 26px rows, no settings mile. */
function Configure() {
  // Betterment C8: the diagnostics fold is behind RAW (Builder tools).
  const raw = useBuilderTools((state) => state.on);
  return (
    <div className="surface-door">
      <Readiness />
      {raw ? (
        <FoldGadget title="More diagnostics">
        <Memory />
        <Knowledge />
        <Runtime />
        <Hooks />
        <Nudges />
        </FoldGadget>
      ) : null}
    </div>
  );
}

export function DictationCore({ hero, scope, scopeLabel }: CoreProps) {
  const wings = useCoreWings(WINGS, "speak", "Configure dictation");
  // Window grammar (2026-10-24): one status bar for the window; the Speak
  // face reports its phase, fact and hold key into it.
  const [speakItems, setSpeakItems] = useState<StatusBarItem[] | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const announce = useCallback((text: string, tone: ReceiptTone = "ok") => {
    setReceipt(text ? { text, tone } : null);
  }, []);

  // Journal counts for the footer receipt (all-time `count`, today's `today`)
  const journalResource = useResource<DictationJournalResponse>(
    "/api/dictation/journal?limit=1",
    {},
  );
  /* HS-176 counsel C4 — the token says TODAY, so it counts TODAY. `count` is
     the all-time RETAINED total (what Export sizes its fetch by, below); the
     footer reads `today`, the rows recorded on the local calendar day. */
  const journalToday = Number(journalResource.data?.today ?? 0);

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
        learned: <Learned />,
        commands: <CommandsCore />,
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

  // The journal count in warm words (null at zero per UX-CANON A8).
  const journalWords = countWords(journalToday, "today", "today");
  const statusItems: Array<StatusBarItem | null> = [
    ...(active === "speak" && speakItems ? speakItems : []),
    receiptSlot ? { key: "receipt", lamp: receipt?.tone === "warn" ? "warn" : undefined, text: receiptSlot }
      : journalWords ? { key: "journal", text: <span className="surface-footer-readiness">{journalWords}</span> } : null,
  ];

  return (
    <>
      {renderHeroSlot(hero, null)}
      {scope ? (
        <p className="desk-scope-chip">
          <span aria-hidden="true">⌁</span> About {scopeLabel || scope}
        </p>
      ) : null}
      <ReceiptContext.Provider value={announce}>
        <SpeakStatusContext.Provider value={setSpeakItems}>
          {current}
        </SpeakStatusContext.Provider>
      </ReceiptContext.Provider>
      {/* HS-170-04 — the footer: receipt · Review (ghost) · Export (ghost).
          HS-202-02 — the egress slot carried a hardcoded `THIS DEVICE` on a
          face whose own engine row reads a LAN IP or CLOUD
          (03-interaction-walk.md Appendix B.2). The badge that pays
          Article III is the one beside the verb — the SPEAK wing's engine
          row (dictation/SpeakFace.tsx:753) — so the footer states nothing
          it has not read. */}
      <StatusBar
        className="speak-footer"
        data-testid="speak-footer"
        items={statusItems}
        verbs={
          <>
            {/* HS-176-05 (design D2(b).9) — `Review` reviews: it crosses to
                the Journal wing, where the utterances are. It opened the
                Configure DOOR until now, which is the gear's job and still
                is. The verb is kept, not retired (a working verb is never
                dropped). */}
            <Button
              dense
              variant="ghost"
              onClick={() => {
                wings.setDoorOpen(false);
                wings.setView("journal");
              }}
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
            <Button
              dense
              variant="ghost"
              onClick={() => openSurfaceOr("configure-settings", "/settings", "speak")}
            >
              Settings
            </Button>
          </>
        }
      />
    </>
  );
}
