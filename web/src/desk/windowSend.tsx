/* PHILO-13-15 (C5): `Send to ▸` from any document window, the Phase 12 fold.
 * Built to the owner's ratified canvas (phase-13 story 15, "Ratify, build it",
 * 2026-10-03; boards C5-1 to C5-16b; all six defaults stand).
 *
 * ONE composition (fork 5), from the window's own document, in two seats:
 * the window's right-button / long-press menu (first, its own group) and the
 * menu bar's Object menu (the front window; at 393 the Object group in Go).
 *   - rows: the active saved destinations, `<name> · <CHANNEL>`;
 *   - none saved: `Add destination` (Settings, at the form);
 *   - withheld where the window's document cannot send (UX-CANON A.11): a
 *     window with no document, a meeting known to have no summary, a project
 *     known to have no published update;
 *   - the reads: `Send to · CHECKING` while a fact is read (never a refusal),
 *     `Send to · CAN'T CHECK` when it failed (the pick still opens the well),
 *     `Send to · OFFLINE` when the destinations read gets no answer (the rows
 *     are the last read).
 * The pick resolves the document through the Phase 12 binding
 * (floorSendBinding.resolve), sets the well's destination through the push
 * seam (SendWell pickDestination) and brings the picked row, its preview and
 * Send into view. Nothing is sent: he presses Send in the well.
 *
 * This module carries no send code and no CSS: the SEND well species stays
 * in its own chunk (documentSendsLazy.tsx), loaded on the pick.
 */
import { useEffect, useSyncExternalStore } from "react";
import { useDesk } from "./store";
import { frontWindowId } from "./components/window/windowRegistry";
import { useWindowId } from "./components/window/windowIdContext";
import type { WorkMenuEntry } from "./components/DeskMenu";
import { resolve, type Fact, type MeetingForm } from "./floorSendBinding";
import { apiFetch } from "../lib/api";
import {
  CHANNEL_WORD, DEST_CHANGED, requestDestinationsFocus, wire, type Destination,
} from "../features/channels/channels";

/* ── the words (ASD-STE100; the canvas's own) ─────────────────────────── */

export const SEND_TO = {
  label: "Send to",
  checking: "Send to · CHECKING",
  cantCheck: "Send to · CAN'T CHECK",
  offline: "Send to · OFFLINE",
  add: "Add destination",
} as const;

/* ── the window's document ───────────────────────────────────────────── */

/** What a seat names for its window (the brief windows, the Meetings window). */
export type AnnouncedDoc =
  | { kind: "brief"; id: string }
  | { kind: "meeting"; id: string; form: MeetingForm };

export type WindowDoc =
  | { kind: "decision" | "artifact"; id: string }
  | { kind: "brief"; id: string }
  | { kind: "meeting"; id: string; form: MeetingForm; summary: Fact<boolean> }
  | { kind: "project"; id: string; update: Fact<string | null> };

/** The two windows a brief well names its brief in. */
const BRIEF_WINDOWS = new Set(["chair:brief", "pullout:intelligence:desk"]);
const ROOM_WINDOW = "surface-project-memory";
const MEETINGS_WINDOW = "surface-meetings";

/* ── the store: the last reads, the facts, the seats, the Room links ── */

type RoomLink =
  | { state: "open"; updateId: string; destinationId: string; at: number }
  | { state: "failed"; destinationId: string; at: number };

const S = {
  dests: null as Destination[] | null,          // the last read (OFFLINE keeps it)
  destsFailed: false,
  destsLoading: false,
  facts: new Map<string, Fact<unknown>>(),
  factsLoading: new Set<string>(),
  docs: new Map<string, AnnouncedDoc>(),        // window id -> its seat's document
  links: new Map<string, RoomLink>(),           // project id -> the Room link
  tick: 0,
  subs: new Set<() => void>(),
};
const bump = () => { S.tick++; S.subs.forEach((f) => f()); };
const subscribe = (f: () => void) => { S.subs.add(f); return () => { S.subs.delete(f); }; };

/** Re-render on a read transition while `active` (an open menu, a Room). */
export function useSendToTick(active = true): number {
  return useSyncExternalStore(subscribe, () => (active ? S.tick : 0), () => 0);
}

/** Test seam: a fresh page holds no reads. */
export function resetSendTo() {
  S.dests = null; S.destsFailed = false; S.destsLoading = false;
  S.facts.clear(); S.factsLoading.clear(); S.docs.clear(); S.links.clear(); bump();
}

if (typeof window !== "undefined") {
  window.addEventListener(DEST_CHANGED, () => { void readDestinations(); });
}

/** The destinations read. A failure keeps the last rows (OFFLINE). */
export function readDestinations(): Promise<void> {
  if (S.destsLoading) return Promise.resolve();
  S.destsLoading = true;
  return wire.destinations()
    .then((rows) => { S.dests = rows.filter((d) => d.state === "active"); S.destsFailed = false; })
    .catch(() => { S.destsFailed = true; })
    .finally(() => { S.destsLoading = false; bump(); });
}

const factKey = (kind: "meeting" | "project", id: string) => `${kind}:${id}`;
const factOfKey = <T,>(k: string): Fact<T> => (S.facts.get(k) as Fact<T> | undefined) ?? { state: "unread" };

/** The latest published update: the greatest `published_at`; on a tie, the
 *  first the hub lists (the tie rule, Muad'Dib 2026-09-30; the read's own
 *  order is handoff H-C5). */
export function latestPublished(updates: { id: unknown; lifecycle?: unknown; status?: unknown; published_at?: unknown }[]): string | null {
  const list = updates
    .map((u, i) => ({ u, i }))
    .filter(({ u }) => (u.lifecycle ?? u.status) === "published")
    .sort((a, b) => String(b.u.published_at ?? "").localeCompare(String(a.u.published_at ?? "")) || a.i - b.i);
  return list.length ? String(list[0].u.id) : null;
}

/** Read one fact. A known value stays shown while it is read again; an
 *  unknown one is `loading` until the answer (never a refusal). */
export function readFact(kind: "meeting" | "project", id: string): Promise<void> {
  const k = factKey(kind, id);
  if (S.factsLoading.has(k)) return Promise.resolve();
  S.factsLoading.add(k);
  if (factOfKey(k).state !== "known") S.facts.set(k, { state: "loading" });
  bump();
  const path = kind === "meeting"
    ? `/api/meetings/${encodeURIComponent(id)}`
    : `/api/projects/${encodeURIComponent(id)}/updates`;
  return apiFetch<Record<string, unknown>>(path)
    .then((b) => {
      if (kind === "meeting") {
        const intel = (b.intel ?? {}) as Record<string, unknown>;
        S.facts.set(k, { state: "known", value: !!String(intel.summary ?? b.summary ?? "").trim() });
      } else {
        S.facts.set(k, { state: "known", value: latestPublished((b.updates ?? []) as never[]) });
      }
    })
    .catch(() => { S.facts.set(k, { state: "failed" }); })
    .finally(() => { S.factsLoading.delete(k); bump(); });
}

/** The document of the window `winId`, or null when it cannot send. */
export function windowDoc(winId: string | null): WindowDoc | null {
  if (!winId) return null;
  const announced = S.docs.get(winId);
  const m = /^pullout:(decision|artifact|meeting):(.+)$/.exec(winId);
  if (m) {
    if (m[1] === "meeting") {
      const form = announced?.kind === "meeting" ? announced.form : "summary";
      return { kind: "meeting", id: m[2], form, summary: factOfKey<boolean>(factKey("meeting", m[2])) };
    }
    return { kind: m[1] as "decision" | "artifact", id: m[2] };
  }
  if (BRIEF_WINDOWS.has(winId)) return announced?.kind === "brief" ? announced : null;
  if (winId === MEETINGS_WINDOW) {
    // The open record's well names its meeting; it mounts only with a summary.
    return announced?.kind === "meeting"
      ? { ...announced, summary: { state: "known", value: true } }
      : null;
  }
  if (winId === ROOM_WINDOW) {
    const scope = String(useDesk.getState().windowsById?.[winId]?.scope ?? "");
    const p = /^project:(.+)$/.exec(scope);
    return p ? { kind: "project", id: p[1], update: factOfKey<string | null>(factKey("project", p[1])) } : null;
  }
  return null;   // notes, knowledge, people, settings ...: nothing else sends
}

const docFact = (d: WindowDoc): Fact<unknown> | null =>
  d.kind === "meeting" ? d.summary : d.kind === "project" ? d.update : null;

/** Start the reads a window's `Send to ▸` needs (an opening menu). */
export function primeSendTo(winId: string | null) {
  void readDestinations();
  const d = windowDoc(winId);
  if (d?.kind === "meeting" && winId !== MEETINGS_WINDOW) void readFact("meeting", d.id);
  if (d?.kind === "project") void readFact("project", d.id);
}

/* ── ONE composition ─────────────────────────────────────────────────── */

function sendToLabel(d: WindowDoc): string {
  if (S.destsFailed) return SEND_TO.offline;
  const f = docFact(d);
  if (S.dests === null || f?.state === "unread" || f?.state === "loading") return SEND_TO.checking;
  if (f?.state === "failed") return SEND_TO.cantCheck;
  return SEND_TO.label;
}

/** `Send to ▸` for the window `winId`, or null where it is withheld. */
export function sendToEntry(winId: string | null): WorkMenuEntry | null {
  const d = windowDoc(winId);
  if (!d || !winId) return null;
  const f = docFact(d);
  if (f?.state === "known" && !f.value) return null;          // a known absence withholds
  if (S.destsFailed && !S.dests?.length) return null;          // nothing known to send to
  const rows: WorkMenuEntry[] = S.dests === null ? []
    : S.dests.length ? S.dests.map((x) => ({
      type: "item" as const,
      id: `send-to.${x.id}`,
      label: `${x.name} · ${CHANNEL_WORD[x.channel] ?? String(x.channel).toUpperCase()}`,
      onSelect: () => pickFor(winId, x.id),
    }))
    : S.destsFailed ? []
    : [{
      type: "item" as const, id: "send-to.add", label: SEND_TO.add,
      onSelect: () => { requestDestinationsFocus(); useDesk.getState().openSurfaceWindow("configure-settings", "integrations"); },
    }];
  return { type: "sub", id: "send-to", label: sendToLabel(d), entries: rows };
}

/** The window menu: `Send to ▸` leads, its own group (default 1a). */
export function withSendTo(sendTo: WorkMenuEntry | null, entries: WorkMenuEntry[]): WorkMenuEntry[] {
  return sendTo ? [sendTo, { type: "sep", id: "send-to-sep" }, ...entries] : entries;
}

/* ── the pick, the push seam, the arrival ─────────────────────────────── */

const WELL_FORM: Record<MeetingForm, string> = { summary: "meeting_summary", digest: "meeting_digest", followup: "meeting_followup" };

/** The well of `ref` inside the window `winId`. */
const wellIn = (winId: string, ref: string) =>
  (document.getElementById(winId) ?? document).querySelector<HTMLElement>(`[data-testid=send-well][data-doc="${CSS.escape(ref)}"]`);

/** Set the pick through the species' one setter (its chunk loads on demand). */
export function pushPick(ref: string, destinationId: string): Promise<void> {
  return import("./surface/send").then((m) => { m.pickDestination(ref, destinationId); });
}

/** The pick: the window comes to the front, its well opens on the picked
 *  destination, and the row, its preview and Send come into view. A fact
 *  still read waits for its answer; a failed one still opens the well. */
export function pickFor(winId: string, destinationId: string, waited = 0): void {
  const d = windowDoc(winId);
  if (!d) return;
  const f = docFact(d);
  if (f && (f.state === "unread" || f.state === "loading") && waited < 600) {
    if (f.state === "unread") primeSendTo(winId);
    window.setTimeout(() => pickFor(winId, destinationId, waited + 1), 100);
    return;
  }
  useDesk.getState().focusPanel(winId);
  const destination = { id: destinationId, state: "active" as const };
  if (d.kind === "project") {
    const b = resolve({ kind: "project", id: d.id, latestPublishedUpdateId: d.update, destination });
    if ("ref" in b) linkRoom(d.id, { state: "open", updateId: b.ref.slice("project_update:".length), destinationId, at: Date.now() });
    else if ("pending" in b && b.pending === "failed") linkRoom(d.id, { state: "failed", destinationId, at: Date.now() });
    return;
  }
  let ref: string;
  if (d.kind === "meeting") {
    // A failed summary read still opens the well on the window's form.
    ref = `${WELL_FORM[d.form]}:${d.id}`;
    if (d.summary.state === "known") {
      const b = resolve({ kind: "meeting", id: d.id, summary: d.summary, form: d.form, destination });
      if (!("ref" in b)) return;
      ref = b.ref;
    }
  } else {
    const b = resolve(d.kind === "brief" ? { kind: "brief", briefId: d.id, destination } : { kind: d.kind, id: d.id, destination });
    if (!("ref" in b)) return;
    ref = b.ref;
  }
  void pushPick(ref, destinationId).then(() => arrive(ref, winId));
}

/** The arrival: once the preview has come, the picked row (the meeting's
 *  form picker, when the well has one) scrolls to the top of its window's
 *  body, clear of any sticky strip. Nothing else moves. */
export function arrive(ref: string, winId: string, tries = 0): void {
  const well = wellIn(winId, ref);
  const open = well?.querySelector<HTMLElement>("[data-testid=send-open]");
  const ready = open?.querySelector("[data-testid=send-preview], [data-testid=preview-refused], [data-testid=preview-failed]");
  if (!well || !open || !ready) {
    if (tries < 150) window.setTimeout(() => arrive(ref, winId, tries + 1), 100);
    return;
  }
  const target = (well.closest("[data-testid=meeting-send-well]")?.querySelector("[data-testid=doc-forms]")
    ?? open.closest("li.surface-ledger-row")) as HTMLElement | null;
  bringIntoView(target);
  well.dataset.arrived = "true";
}

/** Scroll `target` to the top of its scroller, then clear of what covers it. */
export function bringIntoView(target: HTMLElement | null): void {
  let sc: HTMLElement | null = target?.parentElement ?? null;
  while (sc && !(sc.scrollHeight > sc.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
  if (!target || !sc) return;
  sc.scrollTop += target.getBoundingClientRect().top - sc.getBoundingClientRect().top - 8;
  for (let i = 0; i < 4; i++) {
    const r = target.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + Math.min(40, r.width / 2), r.top + 3);
    if (!hit || target.contains(hit)) break;
    let cover: Element | null = hit;
    while (cover && cover !== sc && !/(sticky|fixed)/.test(getComputedStyle(cover).position)) cover = cover.parentElement;
    sc.scrollTop -= (cover && cover !== sc ? cover : hit).getBoundingClientRect().bottom - r.top + 8;
  }
}

/* ── the Room link { projectId, updateId, destinationId } ─────────────── */

function linkRoom(projectId: string, link: RoomLink) { S.links.set(projectId, link); bump(); }

/** The Room's side of the link: the linked update opens in the Update
 *  posture (also when the Room is open on another update), its well picked.
 *  A failed latest-update read -- the menu's, or the Room's own read of the
 *  linked update -- holds the failure until Retry. `open` resolves false when
 *  the update is not in the read, and rejects when the read fails. */
export function useRoomSendLink(projectId: string | null, open: (updateId: string) => Promise<boolean>): RoomLink | null {
  useSendToTick(Boolean(projectId));
  const link = projectId ? S.links.get(projectId) ?? null : null;
  useEffect(() => {
    if (!projectId || link?.state !== "open") return;
    S.links.delete(projectId);
    const ref = `project_update:${link.updateId}`;
    // Astra C5 check, condition 1: the Room's own read of the linked update can
    // fail after the menu's read succeeded. The handoff is kept: the Room's SEND
    // well shows CANNOT READ LATEST UPDATE + Retry, never nothing.
    const failed = () => linkRoom(projectId, { state: "failed", destinationId: link.destinationId, at: Date.now() });
    void pushPick(ref, link.destinationId)
      .then(() => open(link.updateId))
      .then((ok) => { if (ok) arrive(ref, ROOM_WINDOW); else failed(); })
      .catch(failed);
    bump();
  }, [projectId, link, open]);
  const failedAt = link?.state === "failed" ? link.at : 0;
  useEffect(() => {
    if (!failedAt) return;
    // The failure line and Retry come into view (P8).
    const t = window.setTimeout(() => bringIntoView(
      document.getElementById(ROOM_WINDOW)?.querySelector<HTMLElement>("[data-testid=send-well][data-doc^='project:']") ?? null), 0);
    return () => window.clearTimeout(t);
  }, [failedAt]);
  return link?.state === "failed" ? link : null;
}

/** Retry the Room's latest-update read (the real read); a known update links. */
export function retryRoomLink(projectId: string): void {
  const link = S.links.get(projectId);
  if (!link) return;
  S.facts.delete(factKey("project", projectId));
  void readFact("project", projectId).then(() => {
    const f = factOfKey<string | null>(factKey("project", projectId));
    if (f.state === "known") {
      if (f.value) linkRoom(projectId, { state: "open", updateId: f.value, destinationId: link.destinationId, at: Date.now() });
      else { S.links.delete(projectId); bump(); }
    } else linkRoom(projectId, { ...link, at: Date.now() });
  });
}

/* ── the seats name their window's document ───────────────────────────── */

/** A seat (a brief well, a meeting well) names its document to its window. */
export function useAnnounceWindowDocument(doc: AnnouncedDoc | null): void {
  const winId = useWindowId();
  const key = doc ? `${doc.kind}:${doc.id}:${doc.kind === "meeting" ? doc.form : ""}` : "";
  useEffect(() => {
    if (!winId || !doc) return;
    S.docs.set(winId, doc);
    bump();
    return () => {
      const now = S.docs.get(winId);
      if (now && `${now.kind}:${now.id}:${now.kind === "meeting" ? now.form : ""}` === key) { S.docs.delete(winId); bump(); }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [winId, key]);
}

/** The menu bar's Object menu: the front window's `Send to ▸`. */
export const frontSendTo = (): WorkMenuEntry | null => sendToEntry(frontWindowId());
