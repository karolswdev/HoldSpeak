/* Programs (design §9 "Programs"; canvas "The Programs window at 1440";
 * PG-REQ §7, canvas programs-requirements-2026-10-31 "Browse"): the app
 * window `surface-programs`, ⌃7, beside Agents.
 *
 * Window grammar: title bar → Toolbar (New program, the one primary;
 * Templates ▾; Find a program, a search well with its mic; Project ▾ and
 * Person ▾, only the ones that have a Program; at the right Group: State ▾
 * · Project) → a ListView of Programs, waiting first: Your turn, Running,
 * Drafting, Done, Parked (or one band per project, "No project" last), the
 * most recently changed first → the StatusBar (the Dock lamp's word, "3 of
 * 12 programs · “routes” · HoldSpeak · Alice" when a filter is on, then
 * the counts that are not zero for the rows shown).
 * A row: the program sprite · the title · its StateChip · "3 of 6 steps" ·
 * "4 of 5 met" · the time in its state (a Done program says "Done in 1 h
 * 12" in ok ink) · the last checkpoint. At 393 the toolbar keeps New
 * program and Find; Templates, Project, Person and Group fold into More ▾.
 * Empty: the 64 px program object, one line, one Button. */
import { useMemo, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "../../pages/cores/core-types";
import { WorkMenu } from "../components/DeskMenu";
import { spriteUrl } from "../sprites";
import { openProgram } from "./open";
import { ListView, StateChip, StatusBar, StringGadget, SurfaceState, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../surface";
import type { WorkMenuEntry } from "../components/DeskMenu";
import { useWindowInterior } from "../surface/interior";
import { plainFail } from "../surface/plainFailure";
import { TEMPLATES, createProgram, usePrograms } from "./api";
import { banded, bandedByProject, durationWords, matchesFind, metWords, personsOf, programChip, programTone } from "./model";
import type { ProgramState, ProgramSummary } from "./types";
import "./programs.css";

export { openProgram };

function ProgramRow({ row }: { row: ProgramSummary }) {
  // PG17: a Program of imported PRs says what merged and when.
  const inState = row.state === "done" && row.history ? row.history.words
    : row.state === "done" && row.done_in ? `Done in ${row.done_in}` : durationWords(row.in_state_seconds);
  const line = row.last_checkpoint?.line;
  const met = metWords(row.requirements_met);
  const steps = row.total ? `${row.done} of ${row.total} ${row.total === 1 ? "step" : "steps"}` : "No steps";
  return (
    <li className="kit-listrow pg-row" data-state={row.state} data-testid="programs-row" data-program={row.id}>
      <Button variant="chrome" className="pg-row-main" onClick={() => openProgram(row.id)} aria-label={`Open ${row.title}`}
        data-testid="programs-row-open">
        <img className="kit-listrow-glyph" src={spriteUrl("program", row.id, "rest", null, 20)} alt="" width={20} height={20} />
        <span className="pg-row-title">{row.title}</span>
      </Button>
      <span className="pg-row-state"><StateChip state={programChip(row.state)} label={row.state_word} data-testid="programs-row-state" /></span>
      <span className="pg-row-steps">{steps}</span>
      <span className="pg-row-met" data-testid="programs-row-met" data-all={met?.all ? "" : undefined} title={met?.title}>
        {met?.tone && !met.all ? <span className="kit-dot" data-tone={met.tone} aria-hidden="true" /> : null}
        {met?.text ?? ""}
      </span>
      <span className="pg-row-in" data-tone={row.state === "done" ? "ok" : undefined}>{inState}</span>
      <span className="pg-row-line" title={line ?? undefined}>{line ? `“${line}”` : ""}</span>
      <span className="pg-row-meta" aria-hidden="true">{[steps, met?.text, inState].filter(Boolean).join(" · ")}</span>
    </li>
  );
}

const CARET = (
  <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
    strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <path d="M2.5 3.75L5 6.25l2.5-2.5" />
  </svg>
);

type Group = "state" | "project";
type MenuKey = "templates" | "project" | "person" | "group" | "more";

/** The counts a status bar says for the rows shown (no zero). */
function countsOf(rows: readonly ProgramSummary[]): Partial<Record<ProgramState, number>> {
  const out: Partial<Record<ProgramState, number>> = {};
  for (const row of rows) out[row.state] = (out[row.state] ?? 0) + 1;
  return out;
}

const WORST: readonly ProgramState[] = ["waiting", "failed", "running", "drafting", "done", "parked"];

export function ProgramsCore(_props: CoreProps) {
  const { loading, error, list, reload } = usePrograms();
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const [menu, setMenu] = useState<{ key: MenuKey; rect: DOMRect; opener: HTMLElement } | null>(null);
  const [query, setQuery] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [personId, setPersonId] = useState<string | null>(null);
  const [group, setGroup] = useState<Group>("state");
  useWindowInterior("list");

  const make = async (template: string) => {
    setBusy(template);
    setFailed(null);
    try {
      const made = await createProgram({ title: "New program", template });
      if (made?.id) openProgram(made.id);
      void reload();
    } catch (cause) {
      setFailed(plainFail("The program was not made", cause, "Nothing changed", "Try again"));
    } finally {
      setBusy("");
    }
  };

  // Project ▾ and Person ▾ list only what has a Program (no item of zero).
  const projects = useMemo(() => {
    const out = new Map<string, string>();
    let none = false;
    for (const row of list.programs) {
      const id = row.project?.id ?? row.project_id;
      if (id) out.set(id, row.project?.name ?? id);
      else none = true;
    }
    return { rows: [...out].map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name)), none };
  }, [list.programs]);
  const persons = useMemo(() => {
    const out = new Map<string, string>();
    for (const row of list.programs) for (const person of personsOf(row)) out.set(person.id, person.name);
    return [...out].map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name));
  }, [list.programs]);
  const projectName = projectId === "" ? "No project" : projects.rows.find((row) => row.id === projectId)?.name ?? null;
  const personName = persons.find((row) => row.id === personId)?.name ?? null;

  const shown = list.programs.filter((row) =>
    matchesFind(row, query)
    && (projectId == null || (projectId === "" ? !(row.project?.id ?? row.project_id) : (row.project?.id ?? row.project_id) === projectId))
    && (personId == null || personsOf(row).some((person) => person.id === personId)));
  const filtered = Boolean(query.trim()) || projectId != null || personId != null;
  const bands = group === "project"
    ? bandedByProject(shown).map((band) => ({ key: band.key || "none", word: band.word, count: band.rows.length, rows: band.rows }))
    : banded(shown).map((band) => ({ key: band.state, word: band.word, count: 0, rows: band.rows }));
  const counts = filtered ? countsOf(shown) : list.counts;
  const worst = filtered ? WORST.find((state) => counts[state]) ?? null : list.worst;
  const worstWord = filtered ? (worst ? shown.find((row) => row.state === worst)?.state_word ?? "" : "") : list.worst_word;
  const worstTone = programTone(worst ?? "");
  const status: Array<StatusBarItem | null> = failed ? [
    { key: "failed", lamp: "warn", text: failed.words, testId: "programs-failure" },
  ] : [
    worst ? { key: "worst", lamp: worstTone === "idle" ? undefined : worstTone, live: worst === "running", text: worstWord, testId: "programs-status-worst" } : null,
    filtered && shown.length ? { key: "shown", text: `${shown.length || ""} of ${countWords(list.programs.length, "program")}`, testId: "programs-status-shown" } : null,
    filtered && query.trim() ? { key: "q", text: <span>{`“${query.trim()}”`}</span> } : null,
    filtered && projectName ? { key: "project", text: <span>{projectName}</span> } : null,
    filtered && personName ? { key: "person", text: <span>{personName}</span> } : null,
    counts.waiting ? { key: "waiting", text: `${counts.waiting} ${counts.waiting === 1 ? "waits" : "wait"} on you`, tick: counts.waiting } : null,
    counts.running ? { key: "running", text: `${counts.running} running`, tick: counts.running } : null,
    counts.drafting ? { key: "drafting", text: `${counts.drafting} drafting` } : null,
    counts.done ? { key: "done", text: `${counts.done} done` } : null,
    counts.parked ? { key: "parked", text: `${counts.parked} parked` } : null,
    !filtered && list.programs.length ? { key: "total", text: countWords(list.programs.length, "program") } : null,
  ];

  const clear = () => { setQuery(""); setProjectId(null); setPersonId(null); };
  let body;
  if (loading || (error && !list.programs.length)) {
    body = <SurfaceState loading={loading} error={error ? "The programs did not load. Nothing changed. Try again." : undefined} onRetry={() => void reload()} />;
  } else if (!list.programs.length) {
    body = (
      <SurfaceState empty emptyKind="program" emptyImage={spriteUrl("program", "programs")} emptyLabel="No program yet"
        emptyHint="A program is a goal cut into steps. An agent does each step."
        actionLabel="New program" onAction={() => void make("fast-cycle")} />
    );
  } else if (!shown.length) {
    body = <SurfaceState empty emptyKind="program" emptyLabel="No program matches" actionLabel="Clear the filter" onAction={clear} />;
  } else {
    body = (
      <ListView label="Programs" className="pg-list" data-testid="programs-list">
        <div className="pg-list-head" aria-hidden="true">
          <span>Program</span><span>State</span><span>Steps</span><span>Met</span><span>In state</span><span>Last checkpoint</span>
        </div>
        {bands.map((band) => (
          <section key={band.key} className="kit-listday pg-band" aria-label={band.word} data-band={band.key} data-testid="programs-band">
            <h3 className="kit-listday-label">{band.word}{band.count ? <span className="pg-band-count">{` · ${band.count}`}</span> : null}</h3>
            <ul className="kit-listrows">{band.rows.map((row) => <ProgramRow key={row.id} row={row} />)}</ul>
          </section>
        ))}
      </ListView>
    );
  }

  const open = (key: MenuKey) => (event: { currentTarget: HTMLElement }) => {
    const opener = event.currentTarget;
    setMenu((now) => (now?.key === key ? null : { key, rect: opener.getBoundingClientRect(), opener }));
  };
  const templateEntries: WorkMenuEntry[] = TEMPLATES.map((template) => ({
    type: "item" as const, id: template.id, label: `${template.name} · ${template.line}`,
    glyph: <img src={template.agent ? spriteUrl("coder", template.agent, "rest", template.agent, 20) : spriteUrl("project", template.id, "rest", null, 20)} alt="" width={20} height={20} />,
    onSelect: () => void make(template.id),
  }));
  const projectEntries: WorkMenuEntry[] = [
    { type: "item", id: "any", label: "Any project", checked: projectId == null ? "exclusive" : undefined, onSelect: () => setProjectId(null) },
    ...projects.rows.map((row) => ({
      type: "item" as const, id: row.id, label: row.name, checked: projectId === row.id ? "exclusive" as const : undefined,
      glyph: <img src={spriteUrl("project", row.id, "rest", null, 20)} alt="" width={20} height={20} />,
      onSelect: () => setProjectId(row.id),
    })),
    ...(projects.none ? [{ type: "item" as const, id: "none", label: "No project", checked: projectId === "" ? "exclusive" as const : undefined, onSelect: () => setProjectId("") }] : []),
  ];
  const personEntries: WorkMenuEntry[] = [
    { type: "item", id: "any", label: "Anyone", checked: personId == null ? "exclusive" : undefined, onSelect: () => setPersonId(null) },
    ...persons.map((row) => ({
      type: "item" as const, id: row.id, label: row.name, checked: personId === row.id ? "exclusive" as const : undefined,
      onSelect: () => setPersonId(row.id),
    })),
  ];
  const groupEntries: WorkMenuEntry[] = (["state", "project"] as const).map((value) => ({
    type: "item" as const, id: value, label: value === "state" ? "State" : "Project", checked: group === value ? "exclusive" as const : undefined,
    onSelect: () => setGroup(value),
  }));
  const entries: Record<MenuKey, { label: string; entries: WorkMenuEntry[] }> = {
    templates: { label: "Templates", entries: templateEntries },
    project: { label: "Project", entries: projectEntries },
    person: { label: "Person", entries: personEntries },
    group: { label: "Group", entries: groupEntries },
    more: {
      label: "More", entries: [
        { type: "sub", id: "templates", label: "Templates", entries: templateEntries },
        ...(projects.rows.length || projects.none ? [{ type: "sub" as const, id: "project", label: projectName ? `Project: ${projectName}` : "Project", entries: projectEntries }] : []),
        ...(persons.length ? [{ type: "sub" as const, id: "person", label: personName ? `Person: ${personName}` : "Person", entries: personEntries }] : []),
        { type: "sub", id: "group", label: `Group: ${group === "state" ? "State" : "Project"}`, entries: groupEntries },
      ],
    },
  };
  const menuButton = (key: MenuKey, words: ReactNode, testId: string, className = "pg-wide") => (
    <Button dense variant="ghost" className={className} aria-haspopup="menu" aria-expanded={menu?.key === key} disabled={Boolean(busy)}
      onClick={open(key)} data-testid={testId}>
      {words}
      {CARET}
    </Button>
  );

  return (
    <div className="pg-window" data-testid="programs-window">
      <Toolbar label="Programs" data-testid="programs-toolbar" trailing={menuButton("group", `Group: ${group === "state" ? "State" : "Project"}`, "programs-group")}>
        <Button dense variant="primary" loading={busy === "fast-cycle"} disabled={Boolean(busy)} onClick={() => void make("fast-cycle")}
          data-testid="programs-new">
          <ToolGlyph kind="new" />
          New program
        </Button>
        {menuButton("templates", "Templates", "programs-templates")}
        {list.programs.length ? (
          <span className="pg-find" data-testid="programs-find">
            <StringGadget label="Find a program" type="search" value={query} onChange={setQuery} placeholder="Find a program" />
          </span>
        ) : null}
        {projects.rows.length || projects.none ? menuButton("project", projectName ? `Project: ${projectName}` : "Project", "programs-project") : null}
        {persons.length ? menuButton("person", personName ? `Person: ${personName}` : "Person", "programs-person") : null}
        {menuButton("more", "More", "programs-more", "pg-narrow")}
      </Toolbar>
      <div className="pg-body">{body}</div>
      <StatusBar data-testid="programs-status" items={status} />
      {menu ? (
        <WorkMenu label={entries[menu.key].label} x={menu.rect.left} y={menu.rect.bottom} opener={menu.opener} autoFocus
          returnFocus={() => menu.opener.focus()} onClose={() => setMenu(null)} entries={entries[menu.key].entries} />
      ) : null}
    </div>
  );
}

export default ProgramsCore;
