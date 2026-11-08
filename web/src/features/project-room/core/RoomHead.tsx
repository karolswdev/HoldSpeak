// The Room's head: the state line, the toolbar (Review, Write update), the
// facts, the draft's run and the outcome. A failed health read is named.
import { useEffect, useRef, useState } from "react";
import { DotWord, RunLine, StateChip, SurfaceSection, Toolbar, ToolGlyph } from "../../../desk/surface";
import { spriteUrl } from "../../../desk/sprites";
import { refOpener } from "../../../desk/openObject";
import { openSurfaceOr } from "../../../desk/shell";
import { useEngine } from "../../../desk/hooks/useEngine";
import { Button } from "../../../components/signal/Signal";
import type { RoomNowData, RoomSnapshot } from "../model";
import { headFacts, stateLine, type StateLine } from "../now/model";
import type { useReviewController } from "../review/useReviewController";
import type { useUpdateController } from "../update/useUpdateController";
import { sourcesWord } from "./format";

/* ── the head (Betterment P3: where it stands in ten seconds) ── */

/** The head's one big fact: the state and its reason, in his words
 *  ("At risk: tokenization waits on the HSM ceremony"). The reason's source
 *  opens from it. */
function RoomHeadline({ line }: { line: StateLine }) {
  const open = line.ref ? refOpener(line.ref) : null;
  // Window grammar (2026-10-24): the state word leads in its colour with a
  // lamp; the reason follows in ink. The words stay one line of text.
  const split = line.text.indexOf(": ");
  const words = split > 0
    ? <><span className="room-state-word">{line.text.slice(0, split + 1)}</span>{" "}<span className="room-state-reason">{line.text.slice(split + 2)}</span></>
    : <span className="room-state-word">{line.text}</span>;
  return (
    <span className="room-headline" data-testid="room-headline" data-tone={line.tone}>
      {open ? (
        <Button variant="chrome" className="room-headline-open" data-testid="room-headline-open"
          aria-label={`${line.text}. Open the source`} onClick={open}>
          {words}
        </Button>
      ) : words}
    </span>
  );
}

export function RoomHead({
  room,
  updateCtrl,
  reviewCtrl,
  pendingCount,
  quiet = false,
}: {
  room: RoomSnapshot;
  updateCtrl: ReturnType<typeof useUpdateController>;
  reviewCtrl: ReturnType<typeof useReviewController>;
  pendingCount: number;
  /** PHILO-17: another well holds the face's one primary (Add source's Add). */
  quiet?: boolean;
}) {
  const updateEngine = useEngine("project.update_draft");
  const sources = room.sources.state === "ok" ? room.sources.items : [];
  const sourceWord = sourcesWord(sources, room.sources.state === "ok" ? room.sources.quietUntil : null);
  const now = room.now?.state === "ok" ? (room.now as RoomNowData & { state: "ok" }) : null;
  const facts = headFacts(now);
  // PHILO-15 B69/B60: a STALE source, or quiet hours holding the sweep, is
  // said on the head (a plain CHECKED time is not: the window reads itself).
  const sourceFact = sourceWord && !/^Checked /.test(sourceWord.word) ? sourceWord : null;

  const nameRef = useRef<HTMLSpanElement>(null);
  const [showOutcome, setShowOutcome] = useState(false);
  useEffect(() => {
    const el = nameRef.current;
    if (!el) return;
    const check = () => {
      const overflows = el.scrollWidth > el.clientWidth;
      const outcome = room.project.outcomeText || room.project.name;
      setShowOutcome(overflows || outcome.length > 80);
    };
    check();
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => ro.disconnect();
  }, [room.project.name, room.project.outcomeText]);

  const draftRun = updateCtrl.draftRun;

  return (
    <div className="room-head" data-testid="room-head">
      <span ref={nameRef} className="room-head-name-measure" aria-hidden="true">
        {room.project.name}
      </span>
      {/* Window grammar (2026-10-24): the window's verbs are the kit
          Toolbar under the title bar, Write update the one primary. */}
      <Toolbar label="Project actions" className="room-toolbar">
          {pendingCount > 0 ? <Button dense variant={quiet ? "secondary" : "primary"}
            loading={reviewCtrl.loading} onClick={() => void reviewCtrl.enterReview()} data-testid="room-head-review">
            <ToolGlyph kind="tasks" />
            Review {pendingCount}
          </Button> : null}
          <Button
            dense
            variant={quiet || pendingCount > 0 ? "secondary" : "primary"}
            loading={updateCtrl.loading || updateCtrl.draftBusy}
            disabled={updateEngine.state === "unread"}
            // Betterment P1: the records draft at once; the engine's after.
            onClick={() => void updateCtrl.write(updateEngine.state === "set")}
            data-testid="updates-verb"
          >
            <ToolGlyph kind="edit" />
            Write update
          </Button>
      </Toolbar>
      <div className="room-head-line">
        <img className="room-head-glyph desk-chrome-sprite" src={spriteUrl("project", room.project.id, "rest", null, 32)}
          alt="" width={28} height={28} draggable={false} />
        <RoomHeadline line={stateLine(room, Boolean(sourceWord?.stale))} />
        {room.project.isArchived ? (
          <span className="kit-pill" data-tone="danger" data-dot="">Archived</span>
        ) : null}
      </div>
      {facts.length || sourceFact ? (
        <p className="room-now-facts" data-testid="room-head-facts">
          {facts.map((fact) => <span key={fact}>{fact}</span>)}
          {sourceFact ? (
            <DotWord tone={sourceFact.stale ? "warn" : "idle"} data-testid="room-sources-word">{sourceFact.word}</DotWord>
          ) : null}
        </p>
      ) : null}
      {/* P0 (betterment/projects): the draft's run where he pressed it.
          The Update posture draws its own line once it is open. */}
      {updateCtrl.posture === "off" && (draftRun.phase === "running" || draftRun.phase === "failure") ? (
        <div className="room-head-run" data-testid="room-head-draft-run">
          <RunLine
            phase={draftRun.phase}
            verb="Working"
            pastVerb="Drafted"
            model={draftRun.generator === "model" ? updateEngine.model : ""}
            startedAt={draftRun.startedAt}
            elapsedSeconds={draftRun.elapsedSeconds}
            reason={draftRun.reason}
            detail={draftRun.detail}
            onRetry={draftRun.generator ? () => void updateCtrl.draft(draftRun.generator!) : undefined}
            onAction={draftRun.reason === "no_engine"
              ? () => openSurfaceOr("configure-runs-on", "/settings", "models") : undefined}
          />
          {draftRun.phase === "failure" && draftRun.generator === "model" ? (
            <Button dense variant="ghost" onClick={() => void updateCtrl.draft("deterministic")}
              data-testid="room-head-draft-records">
              Use a draft from your records
            </Button>
          ) : null}
        </div>
      ) : null}
      {showOutcome ? (
        <p className="room-head-outcome" data-testid="room-head-outcome">
          {room.project.outcomeText || room.project.name}
        </p>
      ) : null}
    </div>
  );
}

/* A failed health read is named, with Retry (the head then says "Not all
 * read"; it never claims a state it could not read). Betterment P3 keeps
 * this from the parked SIGNALS plate. */
export function HealthNotRead({ onRetry }: { onRetry: () => void }) {
  return (
    <SurfaceSection
      label="Health"
      actions={<Button dense variant="ghost" onClick={onRetry} data-testid="health-retry">Retry</Button>}
    >
      <span data-testid="health-not-read">
        <StateChip state="unreachable" label="HEALTH NOT READ" />
      </span>
    </SurfaceSection>
  );
}
