// Parked 2026-11-11: this Room drawing is replaced by the shared list and inspector seats.
// @ts-nocheck
// The Sources fold: the watched sources, the suggested ones, Add source,
// Register and the Steward's entry.
import { useEffect, useRef, useState } from "react";
import {
  ConfirmVerb, DotWord, StateChip, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState, humanTime,
} from "../../../desk/surface";
import { FoldGadget } from "../../../desk/surface/gadgets";
import { registerProjectRepository, registrable, useProjectRepository } from "../../../desk/projectRepository";
import { plainFail, type PlainFail } from "../../../desk/surface/plainFailure";
import { Button } from "../../../components/signal/Signal";
import type { RoomSnapshot } from "../model";
import * as api from "../api";
import { AddSourcesWell } from "../door/DoorCore";
import { useRoomRead } from "../roomReads";
import type { useProjectRoomController } from "../useProjectRoomController";
import type { useStewardController } from "../steward/useStewardController";
import { emblemFor } from "./rows";
import { formatMMDD, formatTimeShort, sentenceToken } from "./format";

/* ── SOURCES section ── */

export function SourcesSection({
  room,
  onReload,
  stewardCtrl,
  ctrl,
  onAdding,
}: {
  room: RoomSnapshot;
  onReload: () => Promise<void>;
  stewardCtrl: ReturnType<typeof useStewardController>;
  ctrl: ReturnType<typeof useProjectRoomController>;
  /** One filled primary per face: while Add source is open, Add is it. */
  onAdding?: (adding: boolean) => void;
}) {
  const [busyWatch, setBusyWatch] = useState<string>("");
  const watchPending = useRef(false);
  type WatchAction = "Pause" | "Resume" | "Remove";
  const [watchFailures, setWatchFailures] = useState<Record<string, { action: WatchAction; ids: string[]; reason: PlainFail }>>({});
  // Astra r2 on #1068: an older project that watches a repository nobody
  // registered registers it here (the call New Project makes on create).
  const repository = useProjectRepository(room.projectId);
  useRoomRead("repository", repository.state !== null || repository.failed);
  const toRegister = registrable(repository.state);
  const [registering, setRegistering] = useState(false);
  const [registerFailure, setRegisterFailure] = useState<PlainFail | null>(null);
  const register = async () => {
    if (!toRegister) return;
    setRegistering(true);
    setRegisterFailure(null);
    try {
      await registerProjectRepository(room.projectId, toRegister);
      repository.reload();
    } catch (reason) {
      setRegisterFailure(plainFail(`Could not register ${toRegister}`, reason, undefined, "Try again"));
    } finally {
      setRegistering(false);
    }
  };
  // Setup is an explicit Sources → Add source action. A new Project keeps
  // its filed work in view instead of opening three idle provider rows.
  const [adding, setAdding] = useState(false);

  const showsAdding = adding && room.sources.state === "ok";
  useEffect(() => { onAdding?.(showsAdding); }, [showsAdding, onAdding]);

  if (room.sources.state === "degraded")
    return (
      <SurfaceSection label="Sources">
        {/* W6-I words: the state is the chip; the line says what failed and what stayed. */}
        <StateChip state="failure" label="Sources not read" data-testid="room-sources-not-read" />
        <SurfaceState error="Could not read the sources · Nothing changed · Try again" onRetry={() => void onReload()} />
      </SurfaceSection>
    );
  if (room.sources.state !== "ok") return null;
  const { items, count } = room.sources;

  // HS-169-04: act on every watchId in the merged row.
  const changeWatches = async (action: WatchAction, watchIds: string[], rowId = watchIds[0]) => {
    if (watchPending.current || !watchIds.length) return;
    watchPending.current = true;
    setBusyWatch(rowId);
    const mutate = action === "Pause" ? api.pauseWatch : action === "Resume" ? api.resumeWatch : api.retireWatch;
    try {
      const outcomes = await Promise.allSettled(watchIds.map((id) => mutate(id)));
      const rejected = outcomes.flatMap((outcome, index) => outcome.status === "rejected" ? [{ id: watchIds[index], cause: outcome.reason }] : []);
      // Read only after all siblings settle. Retry never replays an accepted watch.
      setWatchFailures((current) => {
        const next = { ...current };
        if (rejected.length) next[rowId] = {
          action, ids: rejected.map((failure) => failure.id),
          reason: plainFail(
            `Could not ${action.toLowerCase()} the watch on ${items.find((source) => source.watchIds.includes(rowId))?.scope ?? rowId}`,
            rejected[0].cause,
            // W6-G words: what stayed is true when some siblings landed.
            rejected.length < watchIds.length ? "The other watches changed" : "Nothing changed",
          ),
        };
        else delete next[rowId];
        return next;
      });
      await onReload();
    } finally {
      watchPending.current = false;
      setBusyWatch("");
    }
  };

  const sorted = [...items].sort((a, b) => {
    const order = { live: 0, paused: 1, cant_check: 2 } as Record<string, number>;
    const aOrder = a.suggested ? 3 : (order[a.state] ?? 1);
    const bOrder = b.suggested ? 3 : (order[b.state] ?? 1);
    return aOrder - bOrder;
  });

  // HS-172-06: suggested sources sit ABOVE existing sources
  const suggestions = ctrl.suggestedSources;

  // SOURCES N counts accepted sources only (F9 ruling); count absent at zero
  const acceptedCount = items.filter((s) => !s.suggested).length;

  return (
    <SurfaceSection
      label="Sources"
      count={acceptedCount || null}
      actions={
        /* HS-169-07 park candidate: the steward's settings live under the
           sources (D4/D5).  Until per-source Adjust exists, this ghost verb
           is the honest interim entry point to the StewardPosture. */
        <>
          {toRegister ? (
            <Button dense variant="ghost" loading={registering} onClick={() => void register()} data-testid="room-register" title={`Register ${toRegister}`}>
              Register
            </Button>
          ) : null}
          {!adding ? (
            <Button dense variant="ghost" onClick={() => setAdding(true)} data-testid="room-add-source" data-verb="add-source">
              Add source
            </Button>
          ) : null}
          <FoldGadget title="Raw" className="room-sources-raw">
            <Button dense variant="ghost" loading={stewardCtrl.loading} onClick={() => void stewardCtrl.enterSteward()} data-testid="steward-verb" data-verb="steward">
              Watch sources
            </Button>
          </FoldGadget>
        </>
      }
    >
      {Object.entries(watchFailures).map(([rowId, failure]) => <div key={rowId} className="room-failure-title" title={failure.reason.title}><SurfaceState error={failure.reason.words} onRetry={busyWatch ? undefined : () => void changeWatches(failure.action, failure.ids, rowId)} /></div>)}
      {registerFailure ? (
        <span role="status" data-testid="room-register-failure" title={registerFailure.title}><DotWord tone="fail">{registerFailure.words}</DotWord></span>
      ) : null}
      {adding && room.projectId ? (
        <AddSourcesWell
          projectId={room.projectId}
          onAdded={() => { setAdding(false); onReload(); }}
          onCancel={() => setAdding(false)}
        />
      ) : null}
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {/* HS-172-06: suggested sources sit above existing */}
          {suggestions.map((sug) => {
            // Resolve meeting title from the needs-you items or proposals
            const mtgItem = room.needsYou.state === "ok"
              ? room.needsYou.items.find((it) => it.meetingTitle)
              : undefined;
            const sugMeetingTitle = mtgItem?.meetingTitle || "";
            return (
            <SurfaceLedgerRow
              key={`sug-${sug.id}`}
              data-testid="suggested-source-row"
              lead={emblemFor(sug.provider)}
              primary={<span className="surface-primary" data-testid="suggested-ref">{sug.reference}</span>}
              wrap
              cells={
                <span className="room-source-tok" data-testid="suggested-caption">
                  {`Suggested from ${sugMeetingTitle || "a meeting"} ${formatMMDD(sug.createdAt)}`.trim()}
                </span>
              }
              trailing={
                <span className="room-suggestion-verbs" data-testid="suggested-verbs">
                  <Button dense variant="secondary" loading={ctrl.suggestionBusy === sug.reference} onClick={() => void ctrl.handleAddSuggestion(sug.reference)} data-testid="suggested-add">
                    Add
                  </Button>
                  <Button dense variant="ghost" onClick={() => void ctrl.handleDismissSuggestion(sug.reference)} data-testid="suggested-dismiss">
                    Dismiss
                  </Button>
                </span>
              }
            />
            );
          })}
          {sorted.map((src) => {
            if (src.state === "cant_check") {
              return (
                <SurfaceLedgerRow
                  key={src.watchId}
                  lead={emblemFor(src.provider)}
                  primary={<span className="surface-primary">{src.scope}</span>}
                  wrap
                  open
                  expands={false}
                  cells={<DotWord tone="warn">Can't check</DotWord>}
                  trailing={
                    <>
                      {/* S-3 / HS-169-07 park candidate: the design names "Fix"
                          (opens Adjust) beside "Remove".  Adjust is withheld in
                          this phase; "Fix" will arrive with the extracted
                          AdjustWell component (PUT /api/watches/{id}/rules). */}
                      <ConfirmVerb
                        label="Remove"
                        targetId={src.watchIds.join(":")}
                        confirmLabel="Remove?"
                        busy={busyWatch === src.watchIds[0]}
                        disabled={Boolean(busyWatch) || Object.values(watchFailures).some((failure) => failure.ids.some((id) => src.watchIds.includes(id)))}
                        onConfirm={() => void changeWatches("Remove", src.watchIds)}
                      />
                    </>
                  }
                >
                  {src.plainReason ? (
                    <div className="room-source-line2">
                      <span className="room-source-reason">{src.plainReason}</span>
                    </div>
                  ) : null}
                </SurfaceLedgerRow>
              );
            }

            if (src.suggested) {
              // PHILO-9-03 (F15, UX-CANON A.11): this Add had no action -- a
              // verb that does nothing is a lie. The hub's source read never
              // sets `suggested` (project_service.py: every source item is
              // `suggested: False`); a suggestion is added from the SUGGESTED
              // rows above (Add / Dismiss, wired). The verb is withheld.
              return (
                <SurfaceLedgerRow
                  key={src.watchId}
                  lead={emblemFor(src.provider)}
                  primary={<span className="surface-primary">{src.scope}</span>}
                  wrap
                  cells={<DotWord tone="info">Suggested</DotWord>}
                  data-testid="source-suggested-row"
                />
              );
            }

            /* LINE 1: emblem . scope (primary) . [gap] . tokens left-aligned . [spacer] . verbs
               LINE 2: checked (no host: owner ruling 2026-10-25), starting at the scope's left edge.
               The tokens sit INSIDE the primary slot so they follow the scope
               inline, not right-aligned as cells.
               HS-175-04: meeting rows use the same grammar — one grammar for
               all source rows. CHECKED/NEVER chip replaces "checked N ago"
               when no egress host (the meeting source is local-only). */
            const isMeeting = src.provider === "meeting";
            return (
              <SurfaceLedgerRow
                key={src.watchId}
                lead={emblemFor(src.provider)}
                data-testid={isMeeting ? "source-meeting-row" : undefined}
                primary={
                  <span className="room-source-primary">
                    <span className="surface-primary" data-testid="source-scope">{src.scope}</span>
                    {src.tokens.map((tok, ti) => (
                      <span key={ti} className="room-source-tok" data-testid={isMeeting ? "source-meeting-token" : undefined}>
                        {ti > 0 ? " · " : ""}{sentenceToken(tok)}
                      </span>
                    ))}
                  </span>
                }
                wrap
                open
                expands={false}
                trailing={
                  <Button
                    dense
                    variant="ghost"
                    loading={busyWatch === src.watchIds[0]}
                    disabled={Boolean(busyWatch) || Object.values(watchFailures).some((failure) => failure.ids.some((id) => src.watchIds.includes(id)))}
                    onClick={() => {
                      void changeWatches(src.state === "paused" ? "Resume" : "Pause", src.watchIds);
                    }}
                    data-testid={isMeeting ? "source-meeting-verb" : undefined}
                  >
                    {src.state === "paused" ? "Resume" : "Pause"}
                  </Button>
                }
              >
                <div className="room-source-line2">
                  {/* HS-175 counsel C7(b): a paused Watch SAYS so (idle chip)
                      beside its Resume verb -- one grammar for MTG / GH / J. */}
                  {src.state === "paused" ? (
                    <span data-testid="source-paused"><DotWord tone="idle">Paused</DotWord></span>
                  ) : null}
                  {/* PHILO-15 B69: the source's one state, the one Needs you shows. */}
                  {src.freshness === "stale" ? (
                    <span data-testid="source-freshness"><DotWord tone="warn">Stale</DotWord></span>
                  ) : src.freshness === "quiet" && src.quietUntil ? (
                    <span data-testid="source-freshness">
                      <DotWord tone="idle">{`Quiet until ${formatTimeShort(src.quietUntil)}`}</DotWord>
                    </span>
                  ) : null}
                  {isMeeting ? (
                    <span data-testid="source-meeting-checked">
                      {src.checkedAt ? (
                        <DotWord tone="ok">{`Checked ${formatTimeShort(src.checkedAt)}`}</DotWord>
                      ) : (
                        <DotWord tone="idle">Never checked</DotWord>
                      )}
                    </span>
                  ) : (
                    <>
                      {src.checkedAt ? (
                        <span className="room-source-checked">Checked {humanTime(src.checkedAt)}</span>
                      ) : null}
                    </>
                  )}
                </div>
              </SurfaceLedgerRow>
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
