/** Today projects the hub's ranked attention read; answers stay in Needs you. */
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { apiFetch } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { openSurfaceOr, openAgentLane } from "../../shell";
import { openChairWindow } from "../../chair/chairWindows";
import {
  calendarOpener,
  refOpener,
  openRef,
  openDecisionRecord,
} from "../../openObject";
import { useDesk } from "../../store";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { useProgramFrames } from "../../programs/api";
import {
  programsTodayLine,
  type ProgramsSinceMorning,
} from "../../programs/fleetStatus";
import { openProgram } from "../../programs/open";
import { useAgentFlights, useAgentFlightsLive } from "../../agentFlights";
import { newsWords, useAutomationNews } from "../../automationNews";
import { usePhoneToday } from "../../calls/phoneApi";
import { openPhoneWing } from "../../calls/phoneFocus";
import { pageTitle, useStandingPages } from "../../standingPages";
import { AGENT_NAME, type AgentId } from "../../firstrun/agentsStep";
import { meetingRowState } from "../../../pages/cores/history/helpers";
import { useSummaryRun } from "../../../pages/cores/history/useSummaryRun";
import {
  executedReceipt,
  readPlannedRoute,
  readRunReceipt,
  routeReady,
} from "../../../meetings/summaryRoute";
import {
  RouteDisclosure,
  RunAttempts,
  routeTitle,
} from "../../../meetings/RouteDisclosure";
import { BriefSendWells } from "../../documentSendsLazy";
import { SYSTEM_48 } from "../../systemSprites";
import { spriteUrl } from "../../sprites";
import { useGuideView } from "../../walk/viewState";
import { ShowMe } from "../../walk/ShowMe";
import {
  PreferencePane,
  PaneViews,
  ListPane,
  ListView,
  PaneInspector,
  InspectorBody,
  InspectorFacts,
  ActionNotice,
  refWords,
  type MemoryRefToken,
  PaneNotice,
  StatusBar,
  SurfaceState,
  PaneActions,
  Meter,
  useWindowMast,
  faceTimeWords,
  useWindowInterior,
  useWindowBack,
  useHasWindowBack,
  type ObjectListRow,
  type ListVerb,
  type InspectorFact,
} from "../../surface";
import { useCompactViewport } from "../../useCompactViewport";
import {
  lookbackItems,
  sinceKind,
  blockerKey,
  humanizeDate,
  type MondayBrief,
} from "./today/brief";
import {
  readPrepared,
  preparedBy,
  preparedOther,
  nothingLine,
  addToAgenda,
  type PreparedRead,
} from "./today/prepared";
import {
  clock,
  countdown,
  startOfDay,
  localDay,
  when,
  toFinish,
  SHORT_DAYS,
  type DoorRead,
  type DayEvent,
  type MeetingRow,
} from "./today/time";

type Pane = "day" | "brief" | "prepared" | "activity";
type NeedRow = {
  id?: string;
  ref?: string;
  title?: string;
  why?: string;
  owner?: string;
  person_name?: string;
  person_id?: string;
  meetingTitle?: string;
  meetingId?: string;
  projectName?: string;
  dueAt?: string;
  since?: string;
  ageToken?: string;
  kind?: string;
  direction?: string;
  waiting?: boolean;
  muted?: boolean;
  counted?: boolean;
};
type TodayRead = {
  needs_you: { count: number; top: NeedRow[]; complete?: boolean };
  day: DoorRead & { meetings: MeetingRow[] };
  since_yesterday: MondayBrief | null;
  prepared: PreparedRead;
};
type DoneRead = {
  items?: {
    kind: string;
    ref: string;
    title: string;
    word: string;
    at: string;
  }[];
  programs?: ProgramsSinceMorning | null;
  since_last_here?: {
    lines: { program_id: string; title: string; line: string; at: string }[];
    partial_words?: string;
    capped_words?: string;
  } | null;
};
type Seat = ObjectListRow & {
  facts?: InspectorFact[];
  open?: () => void;
  prep?: () => void;
  event?: DayEvent;
  meeting?: MeetingRow;
  add?: { person: string; point: string };
  summary?: string;
  sources?: MemoryRefToken[];
  context?: DayEvent;
};
const VIEWS = [
  { id: "day", label: "The day" },
  { id: "brief", label: "Brief" },
  { id: "prepared", label: "Prepared" },
  { id: "activity", label: "Activity" },
];
const GROUPS = {
  day: [
    { id: 0, label: "Waits on you" },
    { id: 1, label: "Ahead" },
    { id: 2, label: "To finish" },
  ],
  brief: [
    { id: 0, label: "Changed and needs you" },
    { id: 1, label: "Changed, no action" },
    { id: 2, label: "Desk pages" },
  ],
  prepared: [
    { id: 0, label: "Meetings" },
    { id: 1, label: "Mine today" },
    { id: 2, label: "Nudges to send" },
    { id: 3, label: "Prepared" },
  ],
  activity: [
    { id: 0, label: "Since you were last here" },
    { id: 1, label: "Since this morning" },
    { id: 2, label: "Results" },
  ],
};
const title = (event: DayEvent) =>
  event.title || event.event_title || "Meeting";
const openDone = (ref: string) =>
  ref.startsWith("decision_record:")
    ? openDecisionRecord(ref.slice("decision_record:".length))
    : openRef(ref);

export function TodayView({ sinceRequest = 0 }: { sinceRequest?: number }) {
  useWindowInterior("list");
  const face = useRef<HTMLDivElement>(null);
  const [view, setView] = useState<Pane>(sinceRequest ? "brief" : "day");
  const [picked, setPicked] = useState<string | null>(null);
  const [detail, setDetail] = useState(false);
  const [day, setDay] = useState<TodayRead | null>(null);
  const [activity, setActivity] = useState<DoneRead | null>(null);
  const [failed, setFailed] = useState("");
  const [activityFailed, setActivityFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [receipt, setReceipt] = useState("");
  const [added, setAdded] = useState<Set<string>>(() => new Set());
  const [send, setSend] = useState(false);
  const [sendBrief, setSendBrief] = useState<MondayBrief | null>(null);
  const [week, setWeek] = useState(false);
  const [lastSummary, setLastSummary] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());
  const mounted = useRef(true),
    reading = useRef(false),
    again = useRef(false),
    sinceRound = useRef(0);
  const acting = useRef(false);
  const actionRetry = useRef<(() => void) | null>(null);
  const firstRead = useRef(true);
  const pages = useStandingPages("desk");
  const readSince = useCallback(async () => {
    const round = ++sinceRound.current;
    try {
      const answer = await apiFetch<DoneRead>("/api/today/since-morning");
      if (mounted.current && round === sinceRound.current) {
        setActivity(answer);
        setActivityFailed(false);
      }
    } catch {
      if (mounted.current && round === sinceRound.current)
        setActivityFailed(true);
    }
  }, []);
  const load = useCallback(async () => {
    if (reading.current) {
      again.current = true;
      return;
    }
    reading.current = true;
    try {
      do {
        again.current = false;
        try {
          const answer = await apiFetch<TodayRead>("/api/today");
          if (!mounted.current) return;
          if (!answer?.day || !Array.isArray(answer.needs_you?.top))
            throw new Error("Today is not read");
          setDay(answer);
          setFailed("");
          if (firstRead.current) {
            firstRead.current = false;
            const next = answer.day.upcoming?.[0];
            if (next) setPicked(`event:${next.id}`);
          }
        } catch {
          if (mounted.current)
            setFailed("Could not read Today · Saved work stays · Retry");
        }
        if (mounted.current) setLoaded(true);
      } while (again.current && mounted.current);
    } finally {
      reading.current = false;
    }
  }, []);
  useEffect(() => {
    mounted.current = true;
    void load();
    void readSince();
    return () => {
      mounted.current = false;
      sinceRound.current++;
    };
  }, [load, readSince]);
  useOnDeskChanged(() => {
    void load();
    void readSince();
  });
  useProgramFrames(() => {
    void load();
    void readSince();
  });
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    setView(sinceRequest ? "brief" : "day");
    setPicked(null);
    setDetail(false);
    setSend(false);
  }, [sinceRequest]);
  const retry = () => {
    void load();
    void readSince();
  };
  const act = async (
    run: () => Promise<unknown>,
    success: string,
    failure: string,
    onDone?: () => void,
  ) => {
    if (acting.current) return;
    actionRetry.current = () => void act(run, success, failure, onDone);
    acting.current = true;
    setBusy(true);
    setActionError("");
    try {
      if ((await run()) === false) throw new Error(failure);
      if (mounted.current) {
        setReceipt(success);
        onDone?.();
        void load();
      }
    } catch {
      if (mounted.current) setActionError(failure);
    } finally {
      acting.current = false;
      if (mounted.current) setBusy(false);
    }
  };
  const meetings = day?.day.meetings ?? [];
  const summary = useSummaryRun(
    (id) => readPlannedRoute(meetings.find((row) => String(row.id) === id)),
    retry,
  );
  const finish = toFinish(meetings, now);
  const events = (day?.day.upcoming ?? []).filter((event) => {
    const start = when(event.starts_at),
      end = when(event.ends_at) ?? start;
    return (
      start &&
      end &&
      startOfDay(start) === startOfDay(now) &&
      end.getTime() >= now.getTime()
    );
  });
  const next =
    events[0] ??
    day?.day.upcoming?.find((event) => {
      const at = when(event.starts_at);
      return (
        at &&
        at.getTime() > now.getTime() &&
        at.getTime() < now.getTime() + 12 * 3_600_000
      );
    });
  if (next && !events.includes(next)) events.push(next);
  const needCount = day?.needs_you.count ?? 0;
  const minutes = next
    ? Math.max(
        0,
        Math.ceil(
          ((when(next.starts_at)?.getTime() ?? 0) - now.getTime()) / 60_000,
        ),
      )
    : null;
  useWindowMast({
    glyph: SYSTEM_48.dockIntelligence,
    line:
      view === "day"
        ? `${now.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}${events.length ? ` · ${events.length} ${events.length === 1 ? "meeting" : "meetings"} ahead` : ""}`
        : `${VIEWS.find((tab) => tab.id === view)?.label}${view === "brief" && day?.since_yesterday?.period_label ? ` · ${day.since_yesterday.period_label}` : ""}`,
    figures: [
      ...(needCount
        ? [{ value: needCount, label: "need you", tone: "ask" as const }]
        : []),
      ...(minutes ? [{ value: minutes, label: "min · next" }] : []),
    ],
  });
  useAgentFlightsLive();
  const flights = useAgentFlights((state) => state.flights);
  const news = useAutomationNews();
  const phone = usePhoneToday(true);
  const seats: Seat[] = [];
  const ago = (value: unknown) => {
    const at = when(value);
    return at
      ? startOfDay(at) === startOfDay(now)
        ? clock(at)
        : SHORT_DAYS[at.getDay()]
      : "";
  };
  if (view === "day") {
    for (const [i, row] of (day?.needs_you.top ?? []).entries()) {
      const kind =
        row.ref?.startsWith("people:") || row.kind === "commitment" ? "Commitment" : row.kind === "proposal"
          ? "Decision"
          : row.kind
            ? row.kind[0].toUpperCase() + row.kind.slice(1).replaceAll("_", " ")
            : "Work";
      const due = row.dueAt?.slice(0, 10);
      const state =
        row.direction === "decide" || row.kind === "proposal"
          ? "To decide"
          : due && due < localDay(now)
            ? "Late"
            : due === localDay(now) || /^DUE TODAY/i.test(row.why || "")
              ? "Due today"
              : /^OVERDUE/i.test(row.why || "") ? "Late" : "Asks";
      const context = day?.day.upcoming?.find(event=>event.person_relationship_id && event.person_relationship_id === row.person_id);
      seats.push({
        id: `need:${row.ref || row.id || i}`,
        kind: row.kind || "action-item",
        name: row.title || "Needs you",
        detail: [kind, row.projectName || row.meetingTitle || context?.title]
          .filter(Boolean)
          .join(" · "),
        when: ago(row.since || row.ageToken),
        group: 0,
        context: day?.day.upcoming?.find(
          (event) =>
            event.person_relationship_id &&
            event.person_relationship_id === row.person_id,
        ),
        leadingLamp: { state: "waiting", label: "Waits on you" },
        state: { label: state, tone: "ask" },
        cells: { with: row.person_name || row.owner },
        facts: [
          { label: "With", value: row.person_name || row.owner },
          { label: "Project", value: row.projectName },
          { label: "Due", value: row.dueAt },
          { label: "From the meeting", value: row.meetingTitle },
          { label: "Next meeting", value: !row.meetingTitle ? context?.title : undefined },
          {
            label: "Whose move",
            value:
              row.direction === "mine"
                ? "You owe"
                : row.direction === "theirs"
                  ? "They owe"
                  : undefined,
          },
        ],
        open: () => openChairWindow("chair:needs"),
      });
    }
    const weekDays = day?.day.week?.days ?? [];
    const ahead = week
      ? (day?.day.upcoming ?? []).filter((event) =>
          weekDays.some(
            (row) =>
              when(event.starts_at) &&
              row.date === localDay(when(event.starts_at)!),
          ),
        )
      : events;
    for (const event of ahead)
      seats.push({
        id: `event:${event.id}`,
        kind: "meeting",
        name: title(event),
        detail: event.project_name,
        when: week
          ? `${SHORT_DAYS[when(event.starts_at)?.getDay() ?? 0]} ${ago(event.starts_at)}`
          : ago(event.starts_at),
        group: week
          ? 100 +
            weekDays.findIndex(
              (day) => day.date === localDay(when(event.starts_at)!),
            )
          : 1,
        event,
        leadingLamp: {
          state: event.armed ? "working" : "off",
          label: event.armed ? "Armed" : "Not armed",
        },
        state: {
          label:
            event.armed || event.source === "scheduled_recording"
              ? "Armed"
              : "Not armed",
          tone: event.armed ? "info" : "idle",
        },
        cells: {
          with:
            event.person_label ||
            (event.people_count ? `${event.people_count} people` : undefined),
        },
        meter:
          next?.id === event.id && minutes != null
            ? {
                label: "Time to the next meeting",
                current: Math.max(0, 60 - minutes),
                total: 60,
                state: "waiting",
              }
            : undefined,
        meterColumn: "name",
        open: calendarOpener(event) ?? undefined,
        prep: calendarOpener(event) ?? undefined,
        facts: [
          { label: "With", value: event.person_label },
          { label: "Project", value: event.project_name },
          { label: "Starts", value: event.starts_at },
          { label: "Ends", value: event.ends_at },
          {
            label: "Record",
            value:
              event.armed || event.source === "scheduled_recording"
                ? "Armed"
                : "Not armed",
          },
        ],
      });
    const justMade = meetings.find(
      (row) => String(row.id) === lastSummary && !finish.includes(row),
    );
    for (const row of justMade ? [...finish, justMade] : finish)
      seats.push({
        id: `finish:${row.id}`,
        kind: "meeting",
        name: String(row.title || "Meeting"),
        cells: {with: Array.isArray(row.attendees) && row.attendees.length ? `${row.attendees.length} ${row.attendees.length === 1 ? "person" : "people"}` : undefined},
        when: ago(row.started_at ?? row.created_at),
        group: 2,
        meeting: row,
        leadingLamp: {
          state: row.has_summary
            ? "done"
            : meetingRowState(row).verb === "Retry"
              ? "failed"
              : "waiting",
          label: row.has_summary ? "Summary made" : "Summary needed",
        },
        state: {
          label: row.has_summary
            ? "Made"
            : meetingRowState(row).verb === "Retry"
              ? "Failed"
              : "To make",
          tone: row.has_summary
            ? "info"
            : meetingRowState(row).verb === "Retry"
              ? "fail"
              : "ask",
        },
        open: () => openRef(`meeting:${row.id}`),
        facts: [
          {
            label: "Recorded",
            value: String(row.started_at ?? row.created_at ?? ""),
          },
        ],
      });
  }
  if (view === "brief") {
    for (const item of lookbackItems(day?.since_yesterday)) {
      const kind = sinceKind(item),
        needs =
          ["promise", "failed", "unread"].includes(kind) ||
          item.section === "decisions";
      const split = item.text.indexOf(": ");
      const blocker = blockerKey(item.source_ref);
      seats.push({
        id: `brief:${item.id}`,
        kind: "note",
        name: split >= 0 ? item.text.slice(split + 2) : item.text,
        detail:
          split >= 0 ? humanizeDate(item.text.slice(0, split)) : undefined,
        group: needs ? 0 : 1,
        leadingLamp: {
          state: needs ? "waiting" : "done",
          label: needs ? "Needs you" : "Changed",
        },
        state: {
          label: needs ? "Needs you" : "Read",
          tone: needs ? "ask" : "idle",
        },
        summary: item.detail || undefined,
        open: blocker
          ? () => openSurfaceOr("open-concierge", "/models", blocker)
          : (refOpener(item.source_ref) ?? undefined),
        facts: [{ label: "What it says", value: item.detail }],
      });
    }
    for (const page of pages)
      seats.push({
        id: `page:${page.slug}`,
        kind: "note",
        name: pageTitle(page),
        group: 2,
        summary: page.sentences.map((s) => s.text).join("\n"),
        sources: page.sentences
          .flatMap((sentence) => sentence.refs)
          .filter((ref) => ref.opens),
        facts: [
          ...page.sentences.flatMap((sentence, i) => [
            { label: i ? "Also" : "Answer", value: sentence.text },
            {
              label: "Sources",
              value:
                sentence.refs.map((ref) => refWords(ref.token)).join(" · ") ||
                undefined,
            },
          ]),
          { label: "Built", value: page.built_at },
          { label: "New sources", value: page.new_sources || undefined },
          { label: "State", value: page.stale ? "Out of date" : undefined },
          {
            label: "Written by",
            value:
              page.model && page.model !== "pages"
                ? preparedBy("", page.model)
                : undefined,
          },
        ],
      });
  }
  if (view === "prepared" && day?.prepared.prepared) {
    const prepared = day.prepared.prepared,
      parsed = readPrepared(prepared.result.text || "");
    const open = () =>
      useDesk.getState().openWorkbenchWindow(prepared.workbench_id);
    for (const [i, card] of parsed.cards.entries()) {
      const event = day.day.upcoming?.find(
        (event) =>
          title(event).trim().toLowerCase() === card.title.trim().toLowerCase(),
      );
      seats.push({
        id: `prep:${i}`,
        kind: "meeting",
        name: card.title,
        when: card.time,
        group: 0,
        open,
        prep: event ? (calendarOpener(event) ?? undefined) : undefined,
        facts: card.lines.map((line, i) => ({
          label: i ? "Also" : "Prepared",
          value: line,
        })),
      });
      for (const [j, point] of card.raise.entries())
        seats.push({
          id: `raise:${i}:${j}`,
          kind: "action-item",
          name: point,
          detail: card.title,
          when: card.time,
          group: 0,
          leadingLamp: { state: "waiting", label: "Suggested" },
          state: { label: "To add", tone: "ask" },
          add: event?.person_relationship_id
            ? { person: event.person_relationship_id, point }
            : undefined,
          open,
          facts: [
            { label: "Meeting", value: card.title },
            { label: "To raise", value: point },
          ],
        });
    }
    for (const [group, lines] of [
      [1, parsed.mine],
      [2, parsed.nudges],
      [3, preparedOther(parsed)],
    ] as const)
      for (const [i, line] of lines.entries())
        seats.push({
          id: `prepared:${group}:${i}`,
          kind: "note",
          name: line,
          group,
          open,
          facts: [{ label: "Prepared", value: line }],
        });
    const nothing = nothingLine(prepared.result.text || "", parsed);
    if (nothing)
      seats.push({
        id: "prepared:nothing",
        kind: "note",
        name: nothing,
        group: 3,
        open,
      });
  }
  if (view === "activity") {
    for (const row of activity?.since_last_here?.lines ?? [])
      seats.push({
        id: `last:${row.program_id}`,
        kind: "program",
        name: row.title,
        detail: row.line,
        when: ago(row.at),
        group: 0,
        open: () => openProgram(row.program_id),
        facts: [{ label: "When", value: row.at }],
      });
    for (const row of activity?.items ?? [])
      seats.push({
        id: `done:${row.ref}`,
        kind: row.kind,
        name: row.title,
        detail: row.word,
        when: ago(row.at),
        group: 1,
        open: () => openDone(row.ref),
        facts: [{ label: "When", value: row.at }],
      });
    const programs = programsTodayLine(activity?.programs);
    if (programs)
      seats.push({
        id: "programs",
        kind: "program",
        name: programs,
        group: 1,
        open: () => openSurfaceOr("open-programs", "/"),
      });
    if (phone)
      seats.push({
        id: "phone",
        kind: "phone",
        name: phone,
        group: 1,
        open: () => openPhoneWing(),
      });
    for (const flight of flights.filter(
      (f) => f.state === "done" && f.isNew && f.launchId,
    ))
      seats.push({
        id: `agent:${flight.launchId}`,
        kind: "agent",
        name: `${AGENT_NAME[flight.agent as AgentId] ?? flight.agent} finished ${flight.title || "its work"}`,
        group: 2,
        open: () => openAgentLane(String(flight.launchId)),
      });
    for (const row of news.rows ?? [])
      if (row.workbench_id !== day?.prepared.prepared?.workbench_id)
        seats.push({
          id: `result:${row.workbench_id}`,
          kind: "automation",
          name: newsWords(row),
          when: ago(row.newest_at),
          group: 2,
          open: () => useDesk.getState().openWorkbenchWindow(row.workbench_id),
        });
  }
  const listGroups =
    view === "day" && week
      ? [
          GROUPS.day[0],
          ...(day?.day.week?.days ?? []).map((d, i) => ({
            id: 100 + i,
            label: `Ahead · ${new Intl.DateTimeFormat(undefined, { weekday: "long" }).format(when(d.date)!)}`,
          })),
          GROUPS.day[2],
        ]
      : GROUPS[view];
  const selected = seats.find((row) => row.id === picked) ?? null;
  const compact = useCompactViewport(),
    hosted = useHasWindowBack();
  const back = () => {
    setDetail(false);
    setSend(false);
  };
  useWindowBack(
    compact && detail
      ? { label: "Back", testId: "today-back", onBack: back }
      : null,
    [compact, detail],
  );
  const wasDetail = useRef(detail);
  useLayoutEffect(() => {
    if (wasDetail.current && !detail)
      face.current
        ?.querySelector<HTMLElement>('.object-list-row[aria-selected="true"]')
        ?.focus();
    wasDetail.current = detail;
  }, [detail]);
  useGuideView(
    () => ({ view, picked, detail, send, week }),
    (saved) => {
      setView(saved.view);
      setPicked(saved.picked);
      setDetail(saved.detail);
      setSend(saved.send);
      setWeek(saved.week);
    },
    () => {
      setView("day");
      setPicked(null);
      setDetail(false);
      setSend(false);
      setWeek(false);
    },
    1,
  );
  const changeView = (id: string) => {
    setView(id as Pane);
    setPicked(null);
    setDetail(false);
    setSend(false);
  };
  const choose = (id: string) => {
    setActionError("");
    actionRetry.current = null;
    setPicked(id);
    setDetail(true);
    setSend(false);
  };
  const seatFor = (row: ObjectListRow | null) =>
    seats.find((seat) => seat.id === row?.id) ?? null;
  const agendaIdentity = (row: Seat | null) =>
    row?.add
      ? JSON.stringify([
          day?.prepared.prepared?.result.text,
          row.add.person,
          row.add.point,
        ])
      : "";
  const verbs: ListVerb[] = [
    {
      id: "record",
      label: "Record now",
      variant: "primary",
      testId: "today-record-now",
      enabled: () => true,
      run: () => openSurfaceOr("record-live", "/live"),
    },
    {
      id: "open",
      label: view === "brief" ? "Open source" : "Open",
      key: "Enter",
      enabled: (row) =>
        Boolean(seatFor(row)?.open || seatFor(row)?.sources?.length),
      items: selected?.sources?.map((source, i) => ({
        id: `source:${i}`,
        label: refWords(source.token),
        run: () => openRef(source.ref),
      })),
      run: (row) => seatFor(row)?.open?.(),
    },
    ...((view === "day" && !selected?.meeting) || view === "prepared"
      ? [
          {
            id: "prep",
            label: "Prep",
            testId: "today-open-prep",
            enabled: (row: ObjectListRow | null) => Boolean(seatFor(row)?.prep),
            run: (row: ObjectListRow | null) => seatFor(row)?.prep?.(),
          },
        ]
      : []),
    ...(view === "day" && !selected?.meeting
      ? [
          {
            id: "arm",
            label: "Record when it starts",
            enabled: (row: ObjectListRow | null) =>
              Boolean(
                !busy &&
                seatFor(row)?.event?.source === "calendar_event" &&
                !seatFor(row)?.event?.armed,
              ),
            run: (row: ObjectListRow | null) => {
              const event = seatFor(row)?.event;
              if (event)
                void act(
                  () => useDesk.getState().armEventRecording(event.id),
                  "Recording armed",
                  "Could not arm recording · Saved work stays · Try again",
                );
            },
          },
        ]
      : []),
    ...(selected?.meeting
      ? [
          {
            id: "summary",
            label: "Make the summary",
            testId: "today-make-summary",
            title: routeTitle(readPlannedRoute(selected.meeting)),
            enabled: (row: ObjectListRow | null) =>
              Boolean(
                !summary.runningId &&
                seatFor(row)?.meeting &&
                !seatFor(row)?.meeting?.has_summary &&
                routeReady(readPlannedRoute(seatFor(row)?.meeting)),
              ),
            run: (row: ObjectListRow | null) => {
              const meeting = seatFor(row)?.meeting;
              if (meeting) {
                setLastSummary(String(meeting.id));
                void summary.run(String(meeting.id), readPlannedRoute(meeting));
              }
            },
          },
          ...(!routeReady(readPlannedRoute(selected.meeting))
            ? [
                {
                  id: "engine",
                  label: "Choose engine",
                  enabled: () => true,
                  run: () =>
                    openSurfaceOr("open-concierge", "/models", "meetings"),
                },
              ]
            : []),
        ]
      : []),
    ...(view === "brief"
      ? [
          {
            id: "send",
            label: send ? "Hide send" : "Send…",
            enabled: () => Boolean(day?.since_yesterday),
            run: () => {
              if (!send) setSendBrief(day?.since_yesterday ?? null);
              setSend(!send);
              setDetail(!send || Boolean(selected));
            },
          },
          {
            id: "decisions",
            label: "Decisions",
            enabled: () => true,
            run: () => openSurfaceOr("open-decisions", "/decisions"),
          },
        ]
      : []),
    ...(view === "prepared"
      ? [
          {
            id: "prepare",
            label: "Prepare now",
            enabled: () => !busy,
            run: () => {
              const automation = day?.prepared.automation;
              if (automation)
                void act(
                  () =>
                    apiFetch(
                      `/api/workbenches/${encodeURIComponent(automation.id)}/run`,
                      { method: "POST", json: {} },
                    ),
                  "Preparation started",
                  "Could not prepare · Saved work stays · Try again",
                );
              else openSurfaceOr("open-workbenches", "/workbenches");
            },
          },
          {
            id: "automation",
            label: "Open the automation",
            enabled: () => true,
            run: () => {
              const id =
                day?.prepared.automation?.id ||
                day?.prepared.prepared?.workbench_id;
              if (id) useDesk.getState().openWorkbenchWindow(id);
              else openSurfaceOr("open-workbenches", "/workbenches");
            },
          },
          {
            id: "add",
            label: "Add to the agenda",
            enabled: (row: ObjectListRow | null) =>
              Boolean(
                seatFor(row)?.add &&
                !busy &&
                !added.has(agendaIdentity(seatFor(row))),
              ),
            run: (row: ObjectListRow | null) => {
              const target = seatFor(row),
                add = target?.add,
                key = agendaIdentity(target);
              if (add)
                void act(
                  () => addToAgenda(add.person, add.point),
                  "On the agenda",
                  "Not added. Try again",
                  () => setAdded((previous) => new Set(previous).add(key)),
                );
            },
          },
        ]
      : []),
    ...(view === "day"
      ? [
          {
            id: "needs",
            label: "Open Needs you",
            enabled: () => true,
            run: () => openChairWindow("chair:needs"),
          },
          {
            id: "week",
            label: week ? "Today only" : "This week",
            enabled: () => true,
            run: () => {
              setWeek(!week);
              setPicked(null);
              setDetail(false);
            },
          },
          {
            id: "calendar",
            label: "Connect calendar",
            enabled: () => !day?.day.calendar_configured,
            run: () =>
              openSurfaceOr(
                "configure-settings",
                "/settings",
                "integration:calendar",
              ),
          },
        ]
      : []),
  ];
  const inline = new Set([
    "record",
    "open",
    ...(selected?.event ? ["prep", "arm"] : []),
    ...(selected?.meeting
      ? [routeReady(readPlannedRoute(selected.meeting)) ? "summary" : "engine"]
      : []),
    ...(selected?.add ? ["add"] : []),
    ...(view === "brief" ? ["send"] : []),
  ]);
  for (const verb of verbs) verb.toolbar = inline.has(verb.id);
  const answers = selected?.event
    ? ["prep", "arm"]
    : selected?.meeting
      ? ["summary", "engine"]
      : selected?.add
        ? ["add"]
        : selected?.prep
          ? ["prep"]
          : [];
  const context = selected?.event || selected?.context;
  const figures: Parameters<typeof InspectorFacts>[0]["figures"] = context
    ? [
        {
          value: Math.max(
            0,
            Math.ceil(
              (when(context.starts_at)!.getTime() - now.getTime()) / 60_000,
            ),
          ),
          label: "min to start",
        },
        context.you_owe_count != null
          ? { value: context.you_owe_count, label: "you owe" }
          : {
              value: context.ends_at
                ? Math.round(
                    (when(context.ends_at)!.getTime() -
                      when(context.starts_at)!.getTime()) /
                      60_000,
                  )
                : 0,
              label: "min long",
            },
      ]
    : undefined;
  const failedWords =
    failed ||
    actionError ||
    (summary.receipt?.tone === "danger" ? summary.receipt.text : "") ||
    (view === "activity" && activityFailed
      ? "Could not read today's work"
      : "");
  const retryFailed = failed
    ? retry
    : actionError
      ? () => actionRetry.current?.()
      : summary.receipt?.tone === "danger" && selected?.meeting
        ? () =>
            void summary.run(
              String(selected.meeting!.id),
              readPlannedRoute(selected.meeting),
            )
        : readSince;
  const prepared = day?.prepared.prepared;
  const preparedStamp = prepared?.result.completed_at
    ? ago(prepared.result.completed_at)
    : "";
  const emptyWords = failed
    ? "Today is not read"
    : view === "day"
      ? day?.day.calendar_configured
        ? "No more meetings today"
        : "No meetings and no calendar yet"
      : view === "brief"
        ? "No changes"
        : view === "prepared"
          ? "No prepared work yet"
          : activityFailed
            ? "Activity is not read"
            : "Nothing done yet";
  return (
    <div
      ref={face}
      className="desk-surface-body intelligence-pullout"
      data-interior="list"
      data-feedback-redact="true"
    >
      <PreferencePane
        label="Today"
        testId="today-body"
        aria-busy={!loaded || undefined}
      >
        <ShowMe app="open-intelligence" />
        <PaneViews
          key={view}
          label="Today view"
          tabs={VIEWS}
          value={view}
          onChange={changeView}
        >
          <ListPane
            deck={!send}
            listShare={2 / 3}
            label="Today inspector"
            open={detail || !seats.length}
            onBack={back}
            onReveal={() => setDetail(true)}
            hostBack={compact && hosted}
            backLabel="Back"
            listTestId={view === "brief" ? "today-since-rows" : "today-day"}
            previewTestId="today-inspector"
            list={
              <>
                <ListView
                  label={VIEWS.find((tab) => tab.id === view)!.label}
                  selection
                  ordered
                  groups={listGroups.map((group) => ({
                    ...group,
                    count: view === "day" && group.id === 0 ? needCount : true,
                    tone:
                      (view === "day" || view === "brief") && group.id === 0
                        ? ("ask" as const)
                        : undefined,
                  }))}
                  rows={seats}
                  selectedId={selected?.id ?? null}
                  onSelect={choose}
                  onClearSelection={() => {
                    setPicked(null);
                    setDetail(false);
                  }}
                  onOpen={(id) => seats.find((row) => row.id === id)?.open?.()}
                  defaultVerb="open"
                  verbs={verbs}
                  toolbar={{ testId: "today-toolbar" }}
                  columns={[
                    { key: "when", word: "At", track: "60px", priority: 0 },
                    {
                      key: "name",
                      word: "What",
                      minWidth: 240,
                    },
                    ...(seats.some((seat) => seat.cells?.with)
                      ? [
                          {
                            key: "with",
                            word: "With",
                            track: "112px",
                            priority: 0,
                          },
                        ]
                      : []),
                    {
                      key: "state",
                      word: "State",
                      track: "110px",
                      priority: 2,
                    },
                  ]}
                  rowProps={() => ({ "data-feedback-redact": "true" })}
                />
              </>
            }
          >
            {send && sendBrief ? (
              <BriefSendWells
                onBack={() => {
                  setSend(false);
                  setDetail(Boolean(selected));
                }}
                brief={
                  sendBrief as Parameters<typeof BriefSendWells>[0]["brief"]
                }
              />
            ) : selected ? (
              <PaneInspector
                label={selected.name}
                object={
                  <img
                    src={spriteUrl(
                      selected.kind,
                      selected.id,
                      "rest",
                      null,
                      32,
                    )}
                    width={32}
                    height={32}
                    alt=""
                  />
                }
              >
                <InspectorBody>
                  <InspectorFacts
                    header={false}
                    name={selected.name}
                    data-feedback-redact="true"
                    figures={figures}
                    rows={(selected.facts ?? []).map((row) => ({
                      ...row,
                      value:
                        typeof row.value === "string"
                          ? faceTimeWords(row.value)
                          : row.value,
                    }))}
                  />
                  {selected.meeting ? (
                    <>
                      <RunAttempts
                        receipt={executedReceipt(
                          String(selected.meeting.id),
                          summary.runRefusal?.meetingId ===
                            String(selected.meeting.id)
                            ? summary.runRefusal.refusal.receipt
                            : undefined,
                          readRunReceipt(selected.meeting),
                        )}
                      />
                      <RouteDisclosure
                        route={
                          summary.runRefusal?.meetingId ===
                          String(selected.meeting.id)
                            ? summary.runRefusal.refusal.route
                            : readPlannedRoute(selected.meeting)
                        }
                      />
                    </>
                  ) : null}
                  {prepared && view === "prepared" ? (
                    <InspectorFacts
                      header={false}
                      name="Prepared result"
                      rows={[
                        {
                          label: "Prepared",
                          value: preparedBy(preparedStamp, prepared.engine),
                        },
                        {
                          label: "Looked at",
                          value: prepared.result.used?.looked_at
                            ?.map((row) => row.label || row.ref)
                            .join(", "),
                        },
                      ]}
                      data-feedback-redact="true"
                    />
                  ) : null}
                  <PaneActions>
                    {verbs
                      .filter(
                        (verb) =>
                          answers.includes(verb.id) &&
                          (verb.enabled?.(selected) ?? Boolean(selected)),
                      )
                      .map((verb) => (
                        <Button
                          key={verb.id}
                          dense
                          variant="secondary"
                          onClick={() => verb.run(selected)}
                        >
                          {verb.label}
                        </Button>
                      ))}
                  </PaneActions>
                </InspectorBody>
              </PaneInspector>
            ) : (
              <PaneInspector
                label={next ? title(next) : "The day"}
                object={
                  <img
                    src={spriteUrl("meeting", "today", "rest", null, 32)}
                    width={32}
                    height={32}
                    alt=""
                  />
                }
              >
                <InspectorBody>
                  {seats.length || failed ? null : (
                    <SurfaceState empty emptyLabel={emptyWords} />
                  )}
                  <InspectorFacts
                    header={false}
                    name="The day"
                    figures={
                      !day ? undefined : minutes != null
                        ? [
                            { value: needCount, label: "need you" },
                            { value: minutes, label: "min to start" },
                          ]
                        : [
                            { value: needCount, label: "need you" },
                            { value: events.length, label: "meetings" },
                          ]
                    }
                    rows={[
                      { label: "With", value: next?.person_label },
                      { label: "Project", value: next?.project_name },
                      {
                        label: "Starts",
                        value: next?.starts_at
                          ? faceTimeWords(next.starts_at)
                          : undefined,
                      },
                      {
                        label: "Ends",
                        value: next?.ends_at
                          ? faceTimeWords(next.ends_at)
                          : undefined,
                      },
                    ]}
                  />
                </InspectorBody>
              </PaneInspector>
            )}
          </ListPane>
        </PaneViews>
        {view === "activity" &&
        (activity?.since_last_here?.partial_words ||
          activity?.since_last_here?.capped_words) ? (
          <PaneNotice>
            {[
              activity.since_last_here.partial_words,
              activity.since_last_here.capped_words,
            ]
              .filter(Boolean)
              .join(" · ")}
          </PaneNotice>
        ) : null}
        {failedWords && !send ? (
          <div
            data-testid={
              failed
                ? "today-read-failed"
                : actionError
                  ? "today-action-failed"
                  : summary.receipt?.tone === "danger"
                    ? "today-summary-failed"
                    : "today-done-failed"
            }
          >
            <ActionNotice
              tone="danger"
              keeps="Saved work stays"
              action={{
                label: "Try again",
                onClick: retryFailed,
                disabled: busy,
              }}
            >
              {failedWords.split(" · ")[0].replace(/\. Try again$/, "")}
            </ActionNotice>
          </div>
        ) : null}
        {!send ? (
          <StatusBar
            data-testid="today-status"
            items={[
              {
                key: "failed",
                text: failed || actionError ? "Failed" : undefined,
                lamp: "fail",
              },
              {
                key: "summary",
                text:
                  summary.receipt?.tone === "danger"
                    ? "Failed"
                    : summary.receipt?.text,
                lamp: summary.receipt?.text.includes("did not")
                  ? "fail"
                  : undefined,
              },
              { key: "receipt", text: receipt },
              {
                key: "needs",
                text: needCount
                  ? `${needCount} ${needCount === 1 ? "needs" : "need"} you`
                  : undefined,
                lamp: "ask",
              },
              {
                key: "next",
                text: next
                  ? `${title(next)} ${countdown(when(next.starts_at)!, now)}`
                  : undefined,
              },
            ]}
            trailing={
              next && minutes != null ? (
                <Meter
                  label="Time to the next meeting"
                  current={Math.max(0, 60 - minutes)}
                  total={60}
                  state="waiting"
                />
              ) : undefined
            }
          />
        ) : null}
      </PreferencePane>
    </div>
  );
}
