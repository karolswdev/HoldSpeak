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
  RefTokens,
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
    for (const [i, row] of (day?.needs_you.top ?? []).entries())
      seats.push({
        id: `need:${row.ref || row.id || i}`,
        kind: row.kind || "action-item",
        name: row.title || "Needs you",
        detail: [row.projectName, row.why].filter(Boolean).join(" · "),
        when: ago(row.since || row.ageToken),
        group: 0,
        leadingLamp: { state: "waiting", label: "Waits on you" },
        state: { label: "Needs you", tone: "ask" },
        cells: { with: row.person_name || row.owner },
        facts: [
          { label: "Why", value: row.why },
          { label: "Due", value: row.dueAt },
          { label: "With", value: row.person_name || row.owner },
          { label: "Project", value: row.projectName },
        ],
        open: () => openChairWindow("chair:needs"),
      });
    const weekDays = day?.day.week?.days ?? [];
    if (week)
      for (const row of weekDays.filter((row) => row.count > 0))
        seats.push({
          id: `week:${row.date}`,
          kind: "meeting",
          name: `${row.dow} · ${row.count} ${row.count === 1 ? "meeting" : "meetings"}`,
          group: 1,
          facts: [
            { label: "Day", value: row.date },
            { label: "Meetings", value: row.count },
          ],
        });
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
        group: 1,
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
        cells: { with: event.person_label },
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
        name: humanizeDate(split >= 0 ? item.text.slice(split + 2) : item.text),
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
        facts: [
          { label: "What it says", value: item.detail },
          {
            label: "Kind",
            value:
              split >= 0 ? humanizeDate(item.text.slice(0, split)) : undefined,
          },
        ],
      });
    }
    for (const page of pages)
      seats.push({
        id: `page:${page.slug}`,
        kind: "note",
        name: pageTitle(page),
        group: 2,
        summary: page.sentences.map((s) => s.text).join("\n"),
        facts: [
          ...page.sentences.flatMap((sentence, i) => [
            { label: String(i + 1), value: sentence.text },
            {
              label: "Sources",
              value: sentence.refs.length ? (
                <RefTokens refs={sentence.refs} onOpen={openRef} />
              ) : undefined,
            },
          ]),
          { label: "Built", value: page.built_at },
          { label: "New sources", value: page.new_sources || undefined },
          { label: "State", value: page.stale ? "Out of date" : undefined },
          { label: "Written by", value: preparedBy("", page.model) },
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
        facts: [
          { label: "Since last here", value: row.line },
          { label: "When", value: row.at },
        ],
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
        facts: [
          { label: "Result", value: row.word },
          { label: "When", value: row.at },
        ],
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
      enabled: (row) => Boolean(seatFor(row)?.open),
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
            enabled: () => Boolean(day?.prepared.automation && !busy),
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
            },
          },
          {
            id: "automation",
            label: "Open the automation",
            enabled: () => Boolean(day?.prepared.prepared),
            run: () => {
              const prepared = day?.prepared.prepared;
              if (prepared)
                useDesk.getState().openWorkbenchWindow(prepared.workbench_id);
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
        {failed ? (
          <div data-testid="today-read-failed">
            <SurfaceState retryLabel="Retry" error={failed} onRetry={retry} />
          </div>
        ) : null}
        {summary.receipt?.tone === "danger" ? (
          <div data-testid="today-summary-failed">
            <SurfaceState error={summary.receipt.text} />
          </div>
        ) : null}
        {actionError ? (
          <div data-testid="today-action-failed">
            <SurfaceState error={actionError} />
          </div>
        ) : null}
        {view === "activity" && activityFailed ? (
          <div data-testid="today-done-failed">
            <SurfaceState
              retryLabel="Retry"
              error="Could not read today's work · Saved work stays · Retry"
              onRetry={readSince}
            />
          </div>
        ) : null}
        {view === "day" && day?.needs_you.complete === false ? (
          <PaneNotice>Needs you is not fully read</PaneNotice>
        ) : null}
        <PaneViews
          key={view}
          label="Today view"
          tabs={VIEWS}
          value={view}
          onChange={changeView}
        >
          <ListPane
            deck={seats.length > 0 && !send}
            label="Today inspector"
            open={detail}
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
                  groups={GROUPS[view]}
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
                    { key: "when", word: "At", track: "65px", priority: 1 },
                    {
                      key: "name",
                      word: view === "brief" ? "Since yesterday" : "What",
                    },
                    { key: "with", word: "With", track: "100px", priority: 0 },
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
                subtitle={selected.detail}
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
                    figures={
                      selected.event?.ends_at &&
                      next?.id === selected.event.id &&
                      minutes != null
                        ? [
                            { value: minutes || "Now", label: "min to start" },
                            {
                              value: Math.max(
                                0,
                                Math.round(
                                  (when(selected.event.ends_at)!.getTime() -
                                    when(selected.event.starts_at)!.getTime()) /
                                    60_000,
                                ),
                              ),
                              label: "min long",
                            },
                          ]
                        : undefined
                    }
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
                          ![
                            "record",
                            "needs",
                            "calendar",
                            "week",
                            "decisions",
                          ].includes(verb.id) &&
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
              <SurfaceState
                empty
                emptyLabel={seats.length ? "Select an item" : emptyWords}
              />
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
