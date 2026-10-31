/* Programs (design §9 "Programs"; canvas "The Programs window at 1440"):
 * the app window `surface-programs`, ⌃7, beside Agents.
 *
 * Window grammar: title bar → Toolbar (New program, the one primary;
 * Templates, a fold with one row per template) → a ListView of Programs,
 * waiting first: Your turn, Running, Drafting, Done, Parked, each band
 * under a quiet sentence-case caption, the most recently changed first →
 * the StatusBar (the Dock lamp's word, then the counts that are not zero).
 * A row: the program sprite · the title · its StateChip · "3 of 6 steps" ·
 * the time in its state (a Done program says "Done in 1 h 12" in ok ink) ·
 * the last checkpoint. Empty: the 64 px program object, one line, one
 * Button. */
import { useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "../../pages/cores/core-types";
import { WorkMenu } from "../components/DeskMenu";
import { spriteUrl } from "../sprites";
import { openProgram } from "./open";
import { ListView, StateChip, StatusBar, SurfaceState, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../surface";
import { useWindowInterior } from "../surface/interior";
import { plainFail } from "../surface/plainFailure";
import { TEMPLATES, createProgram, usePrograms } from "./api";
import { banded, durationWords, programChip, programTone } from "./model";
import type { ProgramSummary } from "./types";
import "./programs.css";

export { openProgram };

function ProgramRow({ row }: { row: ProgramSummary }) {
  // PG17: a Program of imported PRs says what merged and when.
  const inState = row.state === "done" && row.history ? row.history.words
    : row.state === "done" && row.done_in ? `Done in ${row.done_in}` : durationWords(row.in_state_seconds);
  const line = row.last_checkpoint?.line;
  return (
    <li className="kit-listrow pg-row" data-state={row.state} data-testid="programs-row" data-program={row.id}>
      <Button variant="chrome" className="pg-row-main" onClick={() => openProgram(row.id)} aria-label={`Open ${row.title}`}
        data-testid="programs-row-open">
        <img className="kit-listrow-glyph" src={spriteUrl("program", row.id, "rest", null, 20)} alt="" width={20} height={20} />
        <span className="pg-row-title">{row.title}</span>
      </Button>
      <span className="pg-row-state"><StateChip state={programChip(row.state)} label={row.state_word} data-testid="programs-row-state" /></span>
      <span className="pg-row-steps">{row.total ? `${row.done} of ${row.total} ${row.total === 1 ? "step" : "steps"}` : "No steps"}</span>
      <span className="pg-row-in" data-tone={row.state === "done" ? "ok" : undefined}>{inState}</span>
      <span className="pg-row-line" title={line ?? undefined}>{line ? `“${line}”` : ""}</span>
    </li>
  );
}

export function ProgramsCore(_props: CoreProps) {
  const { loading, error, list, reload } = usePrograms();
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const [menu, setMenu] = useState<DOMRect | null>(null);
  const templatesRef = useRef<HTMLButtonElement | null>(null);
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

  const bands = banded(list.programs);
  const counts = list.counts;
  const worstTone = programTone(list.worst ?? "");
  const status: Array<StatusBarItem | null> = failed ? [
    { key: "failed", lamp: "warn", text: failed.words, testId: "programs-failure" },
  ] : [
    list.worst ? { key: "worst", lamp: worstTone === "idle" ? undefined : worstTone, live: list.worst === "running", text: list.worst_word, testId: "programs-status-worst" } : null,
    counts.waiting ? { key: "waiting", text: `${counts.waiting} ${counts.waiting === 1 ? "waits" : "wait"} on you`, tick: counts.waiting } : null,
    counts.running ? { key: "running", text: `${counts.running} running`, tick: counts.running } : null,
    counts.drafting ? { key: "drafting", text: `${counts.drafting} drafting` } : null,
    counts.done ? { key: "done", text: `${counts.done} done` } : null,
    counts.parked ? { key: "parked", text: `${counts.parked} parked` } : null,
    list.programs.length ? { key: "total", text: countWords(list.programs.length, "program") } : null,
  ];

  let body;
  if (loading || (error && !list.programs.length)) {
    body = <SurfaceState loading={loading} error={error ? "The programs did not load. Nothing changed. Try again." : undefined} onRetry={() => void reload()} />;
  } else if (!list.programs.length) {
    body = (
      <SurfaceState empty emptyKind="program" emptyImage={spriteUrl("program", "programs")} emptyLabel="No program yet"
        emptyHint="A program is a goal cut into steps. An agent does each step."
        actionLabel="New program" onAction={() => void make("fast-cycle")} />
    );
  } else {
    body = (
      <ListView label="Programs" className="pg-list" data-testid="programs-list">
        <div className="pg-list-head" aria-hidden="true">
          <span>Program</span><span>State</span><span>Steps</span><span>In state</span><span>Last checkpoint</span>
        </div>
        {bands.map((band) => (
          <section key={band.state} className="kit-listday pg-band" aria-label={band.word} data-band={band.state} data-testid="programs-band">
            <h3 className="kit-listday-label">{band.word}</h3>
            <ul className="kit-listrows">{band.rows.map((row) => <ProgramRow key={row.id} row={row} />)}</ul>
          </section>
        ))}
      </ListView>
    );
  }

  return (
    <div className="pg-window" data-testid="programs-window">
      <Toolbar label="Programs" data-testid="programs-toolbar">
        <Button dense variant="primary" loading={busy === "fast-cycle"} disabled={Boolean(busy)} onClick={() => void make("fast-cycle")}
          data-testid="programs-new">
          <ToolGlyph kind="new" />
          New program
        </Button>
        <Button ref={templatesRef} dense variant="ghost" aria-haspopup="menu" aria-expanded={Boolean(menu)} disabled={Boolean(busy)}
          onClick={() => setMenu((now) => (now ? null : templatesRef.current?.getBoundingClientRect() ?? null))} data-testid="programs-templates">
          Templates
          <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
            strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
            <path d="M2.5 3.75L5 6.25l2.5-2.5" />
          </svg>
        </Button>
      </Toolbar>
      <div className="pg-body">{body}</div>
      <StatusBar data-testid="programs-status" items={status} />
      {menu ? (
        <WorkMenu label="Templates" x={menu.left} y={menu.bottom} opener={templatesRef.current} autoFocus
          returnFocus={() => templatesRef.current?.focus()} onClose={() => setMenu(null)}
          entries={TEMPLATES.map((template) => ({
            type: "item" as const, id: template.id, label: `${template.name} · ${template.line}`,
            glyph: <img src={template.agent ? spriteUrl("coder", template.agent, "rest", template.agent, 20) : spriteUrl("project", template.id, "rest", null, 20)} alt="" width={20} height={20} />,
            onSelect: () => void make(template.id),
          }))} />
      ) : null}
    </div>
  );
}

export default ProgramsCore;
