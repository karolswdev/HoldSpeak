// Settings > Accounts > Calendar (HS-175-03): the source rows, Add feed,
// Import image and the one connect well. Moved out of SettingsCore.tsx.
import { wireDate } from "../../../desk/surface/format";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { CalendarSourceFact } from "../core-types";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { FoldGadget, GadgetGroup, StringGadget } from "../../../desk/surface/gadgets";
import { SurfaceLedger, SurfaceLedgerRow } from "../../../desk/surface";
import { importCalendarImage, snapshotEgressChip } from "../../../desk/calendarImageImport";
import type { SettingsBindings } from "./bindings";
import type { SettingsWriter } from "./writer";

/** HS-175 counsel C8 -- the viewer's LOCAL clock (HH:MM) from an ISO
 * instant (``...Z`` or an offset).  Naive strings parse as local, which
 * is what a hub-local stamp means; an unparseable value prints nothing. */
export function formatLocalClock(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = wireDate(iso);
  if (!d) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Source identity comes from the stored name and canonical source type. */
export function calendarSourceIdentity(source: { label: string; url: string }, reportedType?: string) {
  const native = source.url.trim().toLowerCase().startsWith("eventkit:") || reportedType?.toUpperCase() === "MACOS";
  const snapshot = !native && (reportedType?.toUpperCase() === "SNAPSHOT" || /(?:^|[\\/])calendar-snapshots[\\/][^\\/]+\.ics$/i.test(source.url));
  const type = native ? "Mac calendar" : snapshot ? "Snapshot" : "Calendar feed";
  const name = source.label.trim();
  const technical = /^eventkit:/i.test(name) || /^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(name) || name === source.url;
  return { native, snapshot, type, label: name && !technical ? name : type };
}

// W1-TRUTH: the snapshot egress words live with the one Import image flow.
export { snapshotEgressChip } from "../../../desk/calendarImageImport";

/** Render one egress chip per source with off-device reach. */
export function calendarSourceEgressChips(
  facts: CalendarSourceFact[] | undefined,
): Array<{ id: string; label: string; title: string; scope: "cloud" }> {
  if (!facts) return [];
  const chips: Array<{ id: string; label: string; title: string; scope: "cloud" }> = [];
  for (const fact of facts) {
    if (!fact.egress || !fact.host || !fact.refresh_seconds || !fact.enabled) continue;
    const minutes = Math.round(fact.refresh_seconds / 60);
    if (minutes < 1) continue;
    const host = fact.host;
    const name = fact.label || host;
    chips.push({
      id: fact.id ?? host,
      label: `FETCHES ${name} · ${host} · ${minutes} MIN`,
      title: `Fetches ${fact.label || fact.host} every ${minutes} minutes. No credentials or headers are sent.`,
      scope: "cloud",
    });
  }
  return chips;
}

/** The calendar source facts and the one connect well. The face holds them,
 *  so the well and the facts outlive a remount of the section. */
export function useCalendarSources() {
  // HS-175-03: calendar sources facts for the CALENDAR section.
  const [calSources, setCalSources] = useState<{
    sources: Array<{
      id: string; label: string; type: string; status: string;
      host: string | null; event_count: number;
      last_read: string | null; last_read_at?: string | null; egress: boolean;
    }>;
    auto_record: string;
    auto_record_lead_minutes: number;
    matched_this_week: number;
    snapshot_egress?: { scope: string; host?: string | null } | null;
  } | null>(null);
  // The ONE connect well, two uses: "new" under the Connect row, or a
  // source id under that source's row (pre-filled, Save rewrites its URL).
  const [calWellFor, setCalWellFor] = useState<string | null>(null);
  const [calWellValue, setCalWellValue] = useState("");
  const [calWellName, setCalWellName] = useState("");
  const [calWellError, setCalWellError] = useState("");
  const [calWellSaving, setCalWellSaving] = useState(false);
  const calWellGeneration = useRef(0);
  const calSavePending = useRef(false);
  // The in-world Remove confirm step (never a modal): the armed source id.
  const [calRemoveFor, setCalRemoveFor] = useState<string | null>(null);
  const [calLoading, setCalLoading] = useState(false);
  const [calReadError, setCalReadError] = useState("");
  const loadCalSources = useCallback(async () => {
    setCalLoading(true);
    try {
      setCalSources(await apiFetch<typeof calSources>("/api/calendar/sources"));
      setCalReadError("");
    } catch (error) {
      setCalReadError(readableError(error));
    } finally { setCalLoading(false); }
  }, []);
  // Betterment setup ST1: the one page keeps Calendar in Accounts while
  // Meetings reads the same source facts for Auto-record. Load once when the
  // face mounts so an owner who opens Settings at the top and scrolls to
  // either section sees the real source state without pressing the index.
  useEffect(() => { void loadCalSources(); }, [loadCalSources]);
  return {
    calSources, calLoading, calReadError, loadCalSources,
    calWellFor, setCalWellFor, calWellValue, setCalWellValue,
    calWellName, setCalWellName, calWellError, setCalWellError,
    calWellSaving, setCalWellSaving, calWellGeneration, calSavePending,
    calRemoveFor, setCalRemoveFor,
  };
}

export type CalendarSources = ReturnType<typeof useCalendarSources>;

/* Betterment setup ST1: Calendar has one home, Settings ▸ Accounts. The
   source rows, Add feed and Import image moved here from Meetings (the
   HS-175-03 block, unchanged); Accounts' Calendar row chooses a calendar. */
export function CalendarSection({ b, cal, commitMany, onRefuse }: {
  b: SettingsBindings;
  cal: CalendarSources;
  commitMany: SettingsWriter["commitMany"];
  onRefuse: (refusal: string) => void;
}) {
        const { val, update } = b;
        const {
          calSources, calLoading, calReadError, loadCalSources,
          calWellFor, setCalWellFor, calWellValue, setCalWellValue,
          calWellName, setCalWellName, calWellError, setCalWellError,
          calWellSaving, setCalWellSaving, calWellGeneration, calSavePending,
          calRemoveFor, setCalRemoveFor,
        } = cal;
        const data = b.data;
        const sourcesPath: string[] = ["calendar", "sources"];
        const sources: Array<{
          id: string;
          label: string;
          url: string;
          enabled: boolean;
        }> = (val(sourcesPath) as any[]) ?? [];
        const patchSource = (
          index: number,
          patch: Record<string, unknown>,
        ) => {
          const next = sources.map((s, i) =>
            i === index ? { ...s, ...patch } : s,
          );
          update(sourcesPath, next);
        };
        // HS-175-03: rows come from the settings sources (first paint
        // carries them), the per-source egress fact from _calendar_sources,
        // and counts / last-read / status from /api/calendar/sources.
        const calFacts = new Map(
          ((data._calendar_sources ?? []) as CalendarSourceFact[]).map((f) => [f.id ?? "", f]),
        );
        const calStats = new Map((calSources?.sources ?? []).map((s) => [s.id, s]));
        const editingSource = sources.find((source) => source.id === calWellFor);
        const editingIdentity = editingSource ? calendarSourceIdentity(editingSource, calStats.get(editingSource.id)?.type) : null;
        const openCalWell = (target: string, prefill: string, name = "") => {
          ++calWellGeneration.current;
          setCalRemoveFor(null);
          setCalWellFor(target);
          setCalWellValue(prefill);
          setCalWellName(name);
          setCalWellError("");
        };
        const closeCalWell = () => {
          ++calWellGeneration.current;
          setCalWellFor(null);
          setCalWellValue("");
          setCalWellName("");
          setCalWellError("");
        };
        const saveCalWell = async () => {
          const url = calWellValue.trim();
          if ((!url && !editingIdentity?.native) || calWellFor === null || calSavePending.current) return;
          const generation = calWellGeneration.current;
          calSavePending.current = true;
          setCalWellSaving(true);
          setCalWellError("");
          const nextSources =
            calWellFor === "new"
              ? [...sources, { id: crypto.randomUUID(), label: calWellName.trim(), url, enabled: true }]
              : sources.map((s) => (s.id === calWellFor ? { ...s, label: calWellName.trim(), ...(editingIdentity?.native || editingIdentity?.snapshot ? {} : { url }) } : s));
          const ok = await commitMany([[sourcesPath, nextSources]]);
          calSavePending.current = false;
          setCalWellSaving(false);
          if (generation !== calWellGeneration.current) return;
          if (ok) {
            closeCalWell();
          } else {
            setCalWellError("Not saved");
          }
        };
        const calWell = (
          <div className="prefs-calendar-well" data-testid="calendar-well">
            <StringGadget label="Calendar name" caption value={calWellName} placeholder={editingIdentity?.type ?? "Calendar name"} onChange={(value) => { ++calWellGeneration.current; setCalWellName(value); setCalWellError(""); }} />
            {!editingIdentity?.native && !editingIdentity?.snapshot ? (
            <StringGadget
              label="Calendar URL or file path"
              value={calWellValue}
              placeholder="Paste an ICS URL or a file path"
              onChange={(value) => { ++calWellGeneration.current; setCalWellValue(value); setCalWellError(""); }}
              caption
              mic
            />
            ) : <FoldGadget title="Details"><code className="prefs-source-location">{editingSource?.url}</code></FoldGadget>}
            {calWellError ? <span className="gadget-fact" role="alert">{calWellError}</span> : null}
            <div className="prefs-calendar-well-actions">
              <Button variant="ghost" dense onClick={closeCalWell}>Cancel</Button>
              <Button dense loading={calWellSaving} disabled={!calWellValue.trim() && !editingIdentity?.native} onClick={() => void saveCalWell()}>Save</Button>
            </div>
          </div>
        );
    // HS-175-03: CALENDAR section replaces the 146 Calendar GadgetGroup.
    // Source rows, the Connect calendar well, Snapshot.
    return (
              <div className="prefs-calendar-section"><GadgetGroup label="Calendar feeds" material="inset" actions={
                  <div data-testid="calendar-connect-row" className="prefs-inline-controls">
                    <Button variant="secondary" dense onClick={() => openCalWell("new", "")} data-testid="calendar-add-btn">Add feed</Button>
                    {/* UX-CANON A.9 (amended 2026-10-25): where the image goes is
                        said at the act, in the verb's hover title, never as a
                        host chip resting on the pane. */}
                    <Button variant="secondary" dense data-testid="calendar-snapshot-btn" title={snapshotEgressChip(calSources?.snapshot_egress)?.title} onClick={() => importCalendarImage(onRefuse)}>Import image</Button>
                  </div>
                }>
                {calLoading && !calSources ? <span className="gadget-fact" role="status">Reading calendars…</span> : null}
                {calReadError ? <div className="prefs-read-failure" role="alert"><span>Calendar read failed · Sources unchanged · Retry</span><Button dense variant="ghost" disabled={calLoading} onClick={() => void loadCalSources()}>Retry</Button></div> : null}
                {sources.length ? <SurfaceLedger count={null} cols="settings-calendar" label="Calendar sources">
                  {sources.map((entry, index) => {
                    const fact = calFacts.get(entry.id);
                    const stat = calStats.get(entry.id);
                    const host = fact?.egress && fact.host ? String(fact.host) : null;
                    const identity = calendarSourceIdentity(entry, stat?.type);
                    const label = identity.label;
                    const type = identity.type;
                    const minutes = fact?.refresh_seconds ? Math.round(fact.refresh_seconds / 60) : 15;
                    const state = (!entry.enabled ? "idle" : stat?.status ?? "idle") as "success" | "failure" | "idle";
                    const editing = calWellFor === entry.id;
                    const removing = calRemoveFor === entry.id;
                    return (
                      <SurfaceLedgerRow
                        key={entry.id}
                        data-testid={`calendar-source-${entry.id}`}
                        wrap
                        // Window grammar: one 32 px row: dot + name · source, the
                        // quiet facts, Edit at the right.
                        lead={<span className="prefs-calendar-dot" role="status" aria-label={entry.enabled ? (state === "failure" ? "Not read" : state === "success" ? "Read" : "Not read yet") : "Disabled"} data-state={state}><span className="kit-dot" data-tone={state === "success" ? "ok" : state === "failure" ? "fail" : "idle"} /></span>}
                        primary={<span className="prefs-calendar-name"><span data-muted={!entry.enabled || undefined} style={!entry.enabled ? { color: "var(--text-muted)" } : undefined}>{label}</span>{label !== type ? <span className="gadget-fact">{type}</span> : null}</span>}
                        cells={
                          <span className="surface-ledger-cells prefs-calendar-facts">
                            {!entry.enabled ? <span className="gadget-fact">Disabled</span> : null}
                            {/* C9(b): COUNT(DISTINCT uid) counts events -- named so. */}
                            {stat && stat.event_count > 0 ? <span className="gadget-fact" data-testid="calendar-source-events">{stat.event_count} {stat.event_count === 1 ? "event" : "events"}</span> : null}
                            {/* C8: the viewer's local clock from the ISO instant. */}
                            {(() => { const clock = formatLocalClock(stat?.last_read_at) ?? stat?.last_read ?? null; return clock ? <span className="gadget-fact" data-testid="calendar-source-last-read">read {clock}</span> : null; })()}
                          </span>
                        }
                        trailing={
                          <>
                            {/* HS-175 counsel C9 (H2-2), as amended by UX-CANON A.9
                                (2026-10-25): an HTTPS source names its host in the
                                Edit verb's hover title; a file source names none. */}
                            <Button variant="secondary" dense data-testid="calendar-source-edit" title={host ? `Fetches ${label} from ${host} every ${minutes} minutes. No credentials or headers are sent.` : undefined} onClick={(e) => { e.stopPropagation(); openCalWell(entry.id, entry.url, entry.label); }}>Edit</Button>
                          </>
                        }
                        open={editing || removing}
                        onToggle={() => {
                          if (editing) closeCalWell(); else openCalWell(entry.id, entry.url, entry.label);
                        }}
                      >
                        {editing ? <>{calWell}<div className="prefs-calendar-well-actions"><Button variant="ghost" dense data-testid="calendar-source-toggle" onClick={() => patchSource(index, { enabled: !entry.enabled })}>{entry.enabled ? "Disable" : "Enable"}</Button><Button variant="ghost" dense data-testid="calendar-source-remove" onClick={() => { closeCalWell(); setCalRemoveFor(entry.id); }}>Remove</Button></div></> : null}
                        {removing ? (
                          <div className="prefs-calendar-well" data-testid="calendar-remove-confirm">
                            <span className="gadget-fact" data-tone="danger">Remove {label}?</span>
                            <div className="prefs-calendar-well-actions">
                              <Button variant="danger" dense onClick={() => { setCalRemoveFor(null); update(sourcesPath, sources.filter((_, i) => i !== index)); }}>Remove</Button>
                              <Button variant="ghost" dense onClick={() => setCalRemoveFor(null)}>Cancel</Button>
                          </div>
                        </div>
                      ) : null}
                    </SurfaceLedgerRow>
                  );
                })}
              </SurfaceLedger> : null}
                {/* Add feed reuses the existing source editor. */}
                {calWellFor === "new" ? calWell : null}
                {/* PARKED (Settings audit): a full Connect row repeated Add. */}
            </GadgetGroup></div>
    );
  }
