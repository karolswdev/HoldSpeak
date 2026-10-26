// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-170-04 — rebuilt to the settled artboards: one screen (talk, see
// it land, teach); the old cockpit strip folds behind > Details; the
// footer carries the receipt + Review/Export. No egress badge on this
// working window (owner ruling 2026-10-25): Settings ▸ Engines says where
// the clean-up engine runs.
import "../../desk/components/speak.css";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
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
  SpeakVerbsContext,
  type SpeakStatusReport,
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
  { id: "commands", label: "Commands" },
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
      {/* Lane speak (2026-10-25): Settings left the status bar for the
          gear; the door hands over to Settings ▸ Speak. */}
      <div className="speak-door-settings">
        <Button dense variant="secondary" onClick={() => openSurfaceOr("configure-settings", "/settings", "speak")}>
          Open Settings
        </Button>
      </div>
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
  // Lane speak (2026-10-25): a window opened on a wing (`Voice commands`
  // in Go opens this window scoped `commands`) lands on that wing; it is
  // not an "About commands" subject.
  const wingScope = scope && WINGS.some((wing) => wing.id === scope) ? scope : null;
  const wings = useCoreWings(WINGS, wingScope ?? "speak", "Configure dictation");
  const { setView, setDoorOpen } = wings;
  useEffect(() => {
    if (!wingScope) return;
    setDoorOpen(false);
    setView(wingScope);
  }, [wingScope, setView, setDoorOpen]);
  // Window grammar (2026-10-24): one status bar for the window; the Speak
  // face reports its phase, fact, clean-up and hold key into it.
  const [speakReport, setSpeakReport] = useState<SpeakStatusReport | null>(null);
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
    ...(active === "speak" && speakReport ? speakReport.items : []),
    receiptSlot ? { key: "receipt", lamp: receipt?.tone === "warn" ? "warn" : undefined, text: receiptSlot }
      : journalWords ? { key: "journal", text: <span className="speak-today">{journalWords}</span> } : null,
  ];

  /* HS-176-05 (design D2(b).9) — `Review` reviews: it crosses to the
     Journal wing, where the utterances are. It opened the Configure DOOR
     until now, which is the gear's job and still is. The verb is kept, not
     retired (a working verb is never dropped). Lane speak (2026-10-25): on
     the Speak wing both verbs sit at the toolbar's right end; on the other
     wings they stay on the status bar. */
  const windowVerbs: ReactNode = (
    <>
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
      <Button dense variant="ghost" onClick={() => void exportJournal()}>
        Export
      </Button>
    </>
  );
  const onSpeak = active === "speak";

  return (
    <>
      {renderHeroSlot(hero, null)}
      {scope && !wingScope ? (
        <p className="desk-scope-chip">
          <span aria-hidden="true">⌁</span> About {scopeLabel || scope}
        </p>
      ) : null}
      <ReceiptContext.Provider value={announce}>
        <SpeakStatusContext.Provider value={setSpeakReport}>
          <SpeakVerbsContext.Provider value={windowVerbs}>
            {current}
          </SpeakVerbsContext.Provider>
        </SpeakStatusContext.Provider>
      </ReceiptContext.Provider>
      {/* HS-170-04 — the footer: the window's ONE status bar. On the Speak
          wing: the level, the phase, the fact, clean-up · the one verb and
          the hold key at the right. On the other wings: the receipt or the
          day's count · Review, Export. No egress slot (owner ruling
          2026-10-25). */}
      <StatusBar
        className="speak-footer"
        data-testid="speak-footer"
        items={statusItems}
        verbs={onSpeak ? (speakReport?.trailing ?? null) : windowVerbs}
      />
    </>
  );
}
