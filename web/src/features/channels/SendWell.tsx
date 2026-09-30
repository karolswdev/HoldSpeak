/* PHILO-10-04 / PHILO-11-04: the update's composition of the SEND well
 * species (desk/surface/send, contract.md "SendWell"). The update is one
 * document among eight: `project_update:<id>`, its prepared rows labelled
 * `REV n`. What stays the update's own (R8): its history slot, the one
 * DELIVERY history with the manual To + Mark delivered row (story 01's
 * table), and its list chips. Built to the owner's ratified canvases (Phase
 * 10 story 04, "Ratify as drawn"; Phase 11 story 03 canvas E1a).
 */
import { useCallback, useEffect } from "react";
import { Button } from "../../components/signal/Signal";
import { StateChip, StringGadget, SurfaceLedger, SurfaceLedgerRow, SurfaceSection } from "../../desk/surface";
import {
  ProofCell, SendWells, Unreadable, mergeKnown, openFar, useSends, type DocRef,
} from "../../desk/surface/send";
import type { UpdateController } from "../project-room/update/useUpdateController";
import { isDelivered, type Delivery, type ProjectUpdate } from "../project-room/update/model";
import { SENT_WORD, SEND_WORDS, farSide, refusedWord, sentWord, stamp, unknownWord, type Send } from "./channels";
import "./channels.css";

/** The update as a document reference (B1-B5). */
export const updateDoc = (update: ProjectUpdate): DocRef => ({
  ref: `project_update:${update.id}`,
  title: `Update REV ${update.draftRevision}`,
  label: `REV ${update.draftRevision}`,
});

/* ── the one DELIVERY history (story 01's table) ─────────────────────── */

export function DeliveryHistory({ ctrl, update, sends }: { ctrl: UpdateController; update: ProjectUpdate; sends: Send[] }) {
  const rows: Delivery[] = update.deliveries;
  const ok = rows.filter(isDelivered).length;
  const sendOf = (sendId: string | null | undefined) => (sendId ? sends.find((s) => s.id === sendId) : undefined);
  return (
    <div data-send="history" data-testid="delivery-section">
      <SurfaceSection label={ok > 0 ? `${SEND_WORDS.history} ${ok}` : SEND_WORDS.history}>
        <div className="update-deliver-line send-manual" data-testid="deliver-line">
          <span className="update-deliver-to">
            <StringGadget label="To" value={ctrl.deliverTo} onChange={ctrl.setDeliverTo} placeholder="To"
              disabled={ctrl.deliverBusy || ctrl.deliverLocked}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); void ctrl.markDelivered(); } }}
              inputProps={{ "data-testid": "deliver-to" } as never} />
          </span>
          <Button dense variant="ghost" loading={ctrl.deliverBusy} onClick={() => void ctrl.markDelivered()}
            data-testid={ctrl.deliverOutcome.kind === "uncertain" ? "deliver-retry" : "deliver-verb"}>
            {ctrl.deliverOutcome.kind === "uncertain" ? SEND_WORDS.retry : "Mark delivered"}
          </Button>
        </div>
        {ctrl.deliverOutcome.kind === "refused" ? (
          <span className="send-line" data-testid="deliver-refused" data-code={ctrl.deliverOutcome.code}>
            <StateChip state="failure" label="REFUSED" />
            <span className="surface-token" data-chip>{refusedWord(ctrl.deliverOutcome.code)}</span>
          </span>
        ) : ctrl.deliverOutcome.kind === "uncertain" ? (
          <span className="send-line" data-testid="deliver-uncertain"><StateChip state="warning" label={SEND_WORDS.lost} /></span>
        ) : null}
        {ctrl.deliveriesReadFailed ? (
          <Unreadable what="HISTORY" testid="history-unreadable" onRetry={() => void ctrl.reloadDeliveries()} />
        ) : null}
        {rows.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="delivery-history">
              {rows.map((r) => {
                const send = sendOf(r.sendId);
                if (!isDelivered(r)) {
                  // Story 01's UNKNOWN row; Check opens the far side.
                  const far = send ? farSide(send.channel, send.target, send.account) : null;
                  const reason = send?.reason ?? null;
                  return (
                    <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                      lead={<span data-outcome={r.outcome}><StateChip state="warning" label="" /></span>}
                      primary={<span className="surface-primary" data-to={r.deliveredTo ?? ""}>{`${SEND_WORDS.unknownChip} · CHECK ${r.deliveredTo ?? "—"}`}</span>}
                      cells={<span className="send-cells">
                        {reason ? <span className="surface-token" data-chip data-code={reason}>{unknownWord(reason)}</span> : null}
                        {far ? <Button dense variant="ghost" data-testid="history-check" data-href={far} onClick={() => openFar(far)}>{SEND_WORDS.check}</Button> : null}
                        <span className="surface-token" data-chip>{stamp(r.deliveredAt)}</span>
                      </span>} />
                  );
                }
                const manual = r.channel === "manual";
                return (
                  <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                    lead={<span data-outcome={r.outcome}><StateChip state="success" label="" /></span>}
                    primary={<span className="surface-primary" data-to={r.deliveredTo ?? ""}>{r.deliveredTo ?? "—"}</span>}
                    cells={<span className="send-cells">
                      <span className="surface-token" data-chip data-tone="ok" data-testid="history-word">
                        {manual ? SENT_WORD.manual : sentWord(r.channel, r.proof, send?.account)}
                      </span>
                      {manual
                        ? <span className="surface-token" data-chip>MANUAL</span>
                        : <ProofCell channel={r.channel} proof={r.proof ?? null} target={send?.target} account={send?.account} />}
                      <span className="surface-token" data-chip>{stamp(r.deliveredAt)}</span>
                    </span>} />
                );
              })}
            </ul>
          </SurfaceLedger>
        ) : null}
      </SurfaceSection>
    </div>
  );
}

/** The update list's chips, over story 01's table: PREPARED ×K (still
 *  waiting), RESULT UNKNOWN ×M, DELIVERY ×N (isDelivered rows). No chip at
 *  zero. */
export function ListChips({ update }: { update: ProjectUpdate }) {
  const ref = updateDoc(update).ref;
  const { data } = useSends(ref);
  const ok = update.deliveries.filter(isDelivered).length;
  const unknown = update.deliveries.length - ok;
  const prep = mergeKnown(ref, data ?? []).filter((s) => s.state === "prepared").length;
  return (
    <>
      {prep > 0 ? <span data-testid="update-prepared-chip"><StateChip state="active" icon="◆" label={`${SEND_WORDS.prepared} ×${prep}`} /></span> : null}
      {unknown > 0 ? <span data-testid="update-unknown-chip"><StateChip state="warning" label={`${SEND_WORDS.unknownChip} ×${unknown}`} /></span> : null}
      {ok > 0 ? <span data-testid="update-delivered-chip"><StateChip state="success" label={`${SEND_WORDS.history} ×${ok}`} /></span> : null}
    </>
  );
}

/** The two wells of a published update, over ONE read of its sends: the
 *  species' SEND well, and the update's own DELIVERY history in its slot. */
export function PublishedWells({ ctrl, update }: { ctrl: UpdateController; update: ProjectUpdate }) {
  const { reloadDeliveries } = ctrl;
  const settled = useCallback(() => { void reloadDeliveries(); }, [reloadDeliveries]);
  // Opening a published update reads its history again (story 01's table):
  // a send that settled while he was away shows; no answer is named.
  useEffect(() => { settled(); }, [update.id, settled]);
  return (
    <SendWells doc={updateDoc(update)} onSettled={settled}
      history={(sends) => <div data-section="delivery"><DeliveryHistory ctrl={ctrl} update={update} sends={sends} /></div>} />
  );
}
