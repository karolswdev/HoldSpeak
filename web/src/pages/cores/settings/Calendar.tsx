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
import { StringGadget } from "../../../desk/surface/gadgets";
import { ListPane, ListView, CheckGadget, GadgetRow, PaneActions, PaneInspector, InspectorForm, InspectorQuestion, type ListVerb } from "../../../desk/surface";
import { useCalendarStep } from "../../../desk/firstrun/calendarStep";
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
export function CalendarSection({ b, cal, commitMany, onRefuse, beforeChange, onChanged }: {
  b: SettingsBindings;
  cal: CalendarSources;
  beforeChange?: () => Promise<boolean>;
  onChanged?: () => Promise<void>;
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
          pick(target === "new" ? null : target);
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
          <InspectorForm testId="calendar-well" completion={{ cancel: closeCalWell, primary: { label: "Save", busy: calWellSaving, disabled: !calWellValue.trim() && !editingIdentity?.native, run: () => void saveCalWell() } }} notice={calWellError ? <span className="gadget-fact" role="alert">{calWellError}</span> : null}>
            {editingSource ? <>
              <GadgetRow label="From">{editingIdentity?.type}</GadgetRow>
              {calFacts.get(editingSource.id)?.host ? <GadgetRow label="Host">{calFacts.get(editingSource.id)?.host}</GadgetRow> : null}
              {calStats.get(editingSource.id)?.event_count ? <GadgetRow label="Events"><span data-testid="calendar-source-events">{calStats.get(editingSource.id)?.event_count} events</span></GadgetRow> : null}
              {formatLocalClock(calStats.get(editingSource.id)?.last_read_at ?? calStats.get(editingSource.id)?.last_read) ? <GadgetRow label="Last read"><span data-testid="calendar-source-last-read">read {formatLocalClock(calStats.get(editingSource.id)?.last_read_at ?? calStats.get(editingSource.id)?.last_read)}</span></GadgetRow> : null}
            </> : null}
            <GadgetRow label="Calendar name"><StringGadget label="Calendar name" value={calWellName} placeholder={editingIdentity?.type ?? "Calendar name"} onChange={(value) => { ++calWellGeneration.current; setCalWellName(value); setCalWellError(""); }} /></GadgetRow>
            {!editingIdentity?.native && !editingIdentity?.snapshot ? (
            <GadgetRow label="URL or file"><StringGadget
              label="Calendar URL or file path"
              value={calWellValue}
              placeholder="ICS URL or file"
              onChange={(value) => { ++calWellGeneration.current; setCalWellValue(value); setCalWellError(""); }}
              mic
            /></GadgetRow>
            ) : <GadgetRow label="Source"><code className="prefs-source-location">{editingSource?.url}</code></GadgetRow>}
          </InspectorForm>
        );
    const [picked, pick] = useState<string | null>(null);
    const verbs: ListVerb[] = [
      { id: "add", label: "Add calendar", symbol: "+", run: () => {}, items: [
        { id: "feed", label: "Add feed", run: () => openCalWell("new", "") },
        { id: "mac", label: "Mac calendars", run: () => setChoosing(true) },
        { id: "image", label: "Import image", title: snapshotEgressChip(calSources?.snapshot_egress)?.title, run: () => importCalendarImage(onRefuse) },
      ] },
      { id: "remove", label: "Remove calendar", symbol: "−", key: "Delete", enabled: (row) => Boolean(row) && !calWellSaving, run: (row) => setCalRemoveFor(row?.id ?? null) },
      { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: (row) => {
        const source = sources.find((source) => source.id === row?.id);
        if (source) openCalWell(source.id, source.url, source.label);
      } },
    ];
    const [choosing, setChoosing] = useState(false);
    const list = (<ListView label="Calendars" ordered rows={sources.map((entry) => {
        const stat = calStats.get(entry.id);
        const identity = calendarSourceIdentity(entry, stat?.type);
        return { id: entry.id, kind: "calendar", name: identity.label, cells: {
          tick: <CheckGadget label={`Read ${identity.label}`} checked={entry.enabled} disabled={calWellSaving} onChange={(enabled) => patchSource(sources.indexOf(entry), { enabled })} />,
          from: identity.type,
        }, state: entry.enabled && stat?.status === "failure" ? { label: "Not read", tone: "warn" as const } : undefined };
      })} columns={[{ key: "name", word: "Calendar", priority: 100, track: "minmax(0, 1.5fr)" }, { key: "from", word: "From", priority: 20, track: "minmax(0, 1fr)" }, { key: "state", word: "State", priority: 30, track: "120px" }]}
        rowProps={(row) => ({ "data-testid": `calendar-source-${row.id}` })}
        selectedId={picked} onSelect={pick} verbs={verbs} defaultVerb="open" />);
    return <>
      {calReadError ? <PaneActions><span role="alert">Calendars not read</span><Button dense disabled={calLoading} onClick={() => void loadCalSources()}>Retry</Button></PaneActions> : null}
      <ListPane list={list} label="Calendar inspector">
      {calRemoveFor ? <InspectorQuestion targetId={calRemoveFor} question={`Remove ${sources.find((source) => source.id === calRemoveFor)?.label || "calendar"}?`} testId="calendar-remove-confirm" cancel={() => setCalRemoveFor(null)} verb={{ label: "Remove", disabled: calWellSaving, run: () => {
            const id = calRemoveFor;
            setCalWellSaving(true);
            void commitMany([[sourcesPath, sources.filter((source) => source.id !== id)]])
              .then((ok) => { if (ok) { setCalRemoveFor(null); pick(null); } })
              .finally(() => setCalWellSaving(false));
           } }} /> : choosing ? <PaneInspector pendingChoice label="Mac calendars" onClose={() => setChoosing(false)}><InspectorForm><GadgetRow label="Calendars"><MacCalendars beforeUse={beforeChange} onUsed={onChanged} /></GadgetRow></InspectorForm></PaneInspector>
      : calWellFor ? <PaneInspector label={calWellFor === "new" ? "Add feed" : "Calendar"}>{calWell}</PaneInspector>
 : null}
      </ListPane>
    </>;
}

function MacCalendars({ beforeUse, onUsed }: { beforeUse?: () => Promise<boolean>; onUsed?: () => Promise<void> }) {
  const step = useCalendarStep();
  const [picked, pick] = useState<string | null>(null);
  useEffect(() => { const read = () => void step.read(); window.addEventListener("focus", read); return () => window.removeEventListener("focus", read); }, [step.read]);
  const rows = step.rows.filter((row) => row.kind === "macos");
  return <>
    {step.unread ? <PaneActions><span role="alert">Calendars not read</span><Button dense onClick={() => void step.read()}>Retry</Button></PaneActions> : null}
    {step.macos?.can_request ? <PaneActions><Button dense disabled={Boolean(step.busy)} onClick={() => void step.requestAccess()}>Allow calendars</Button></PaneActions> : null}
    {step.notAllowed ? <PaneActions><span>Calendar access off</span><Button dense disabled={Boolean(step.busy)} onClick={() => void step.openSettings()}>Open calendar settings</Button></PaneActions> : null}
    {step.failure?.kind === "refused" ? <span role="alert">{step.failure.reason}</span> : null}
    <ListView label="Available Mac calendars" ordered rows={rows.map((row) => ({ id: row.id, kind: "calendar", name: row.label, cells: { account: row.account }, state: row.in_use ? { label: "Read", tone: "ok" as const } : undefined }))}
      columns={[{ key: "name", word: "Calendar", priority: 100 }, { key: "account", word: "Account", priority: 20, track: "minmax(0, 1fr)" }, { key: "state", word: "State", priority: 30, track: "90px" }]}
      selectedId={picked} onSelect={pick} defaultVerb="use" verbs={[{ id: "use", label: "Use", key: "Enter", enabled: (row) => !step.busy && Boolean(rows.find((source) => source.id === row?.id && !source.in_use)), run: (row) => {
        const source = rows.find((source) => source.id === row?.id); if (!source) return;
        void (async () => { if (beforeUse && !(await beforeUse())) return; if (await step.use(source)) await onUsed?.(); })();
      } }]} />
  </>;
}
