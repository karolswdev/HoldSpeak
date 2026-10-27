/* Betterment Q12 — Memory is the answer desk.
 *
 * The unscoped Memory window opens on the two desk pages the owner uses.  A
 * `q:` scope opens the recall/search face, while a project scope continues to
 * open the Room through the same application registration.
 *
 * Window grammar (2026-10-24) + Window Program W2 (2026-10-27): the toolbar
 * is the Ask window's composer row (askFace AskComposer) over the whole
 * desk: one field that finds as it is typed (results are dense rows of
 * name · kind · date) and asks on Ask ⏎ (the question runs in the Ask
 * window and lands in its Recent). Under it: the written pages as a
 * reader, then Projects and People as dense list views under sentence-case
 * captions → StatusBar (`Written 3h ago · 4 projects · 6 people`). The old
 * "Ask your desk" well is parked (`_parked/memoryAskYourDesk.v1-2026-10-27.tsx`).
 */
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../../desk/store";
import { openPerson, openRef } from "../../desk/openObject";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { apiFetch } from "../../lib/api";
import { Disclosure, MicButton, RefTokens, StandingPage, StringGadget } from "../../desk/surface";
import { DotWord, StatusBar, ToolGlyph, countWords, hueOf, initialsOf } from "../../desk/surface/kit";
import { AskComposer, AskEngineWord, AskSendButton } from "../../desk/components/askFace";
import { useWindowInterior } from "../../desk/surface/interior";
import { humanTime, wireDate } from "../../desk/surface/format";
import { ObjectList, type ObjectListRow } from "../../desk/surface/objects/ObjectList";
import { projectOpenHere, useNeedsYou } from "../../desk/needsYou";
import { refreshEngine, useEngine } from "../../desk/hooks/useEngine";
import { builtToken, useStandingPagesRead, type StandingPageWire } from "../../desk/standingPages";
import { RecallFace } from "../../features/project-room/recall/RecallFace";
import { decodeRecall, type BeliefCardData, type RecallResult } from "../../features/project-room/recall/model";
import type { CoreProps } from "./core-types";
import { ProjectRoomCore } from "../../features/project-room/ProjectRoomCore";
import "./memory.css";

type ProjectRow = { id?: string; name?: string; title?: string; meeting_count?: number };
type PersonRow = { id?: string; display_name?: string; name?: string; relationship_kind?: string; you_owe_count?: number };

const DESK_PAGE_ORDER = ["what-i-owe", "what-changed-this-week"] as const;

function useDeskLinks() {
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [people, setPeople] = useState<PersonRow[]>([]);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let live = true;
    void Promise.allSettled([
      apiFetch<{ projects?: ProjectRow[] }>("/api/projects"),
      apiFetch<{ relationships?: PersonRow[] }>("/api/people/relationships?counts=1"),
    ]).then(([projectResult, peopleResult]) => {
      if (!live) return;
      if (projectResult.status === "fulfilled") {
        setProjects(Array.isArray(projectResult.value?.projects) ? projectResult.value.projects : []);
      }
      if (peopleResult.status === "fulfilled") {
        setPeople(Array.isArray(peopleResult.value?.relationships) ? peopleResult.value.relationships : []);
      }
      setLoaded(true);
    });
    return () => { live = false; };
  }, []);
  return { projects, people, loaded };
}

function pageBeliefs(page: StandingPageWire, beliefs: BeliefCardData[]): BeliefCardData[] {
  const refs = new Set(page.sentences.flatMap((sentence) => sentence.refs.map((ref) => ref.ref)));
  return beliefs.filter((belief) => belief.evidence.some((ref) => refs.has(ref.ref)));
}

function Why({ page, beliefs }: { page: StandingPageWire; beliefs: BeliefCardData[] }) {
  const rows = pageBeliefs(page, beliefs);
  if (!rows.length) return null;
  return (
      <Disclosure label="Why" variant="dense">
      <div className="memory-why" data-testid="memory-why">
        {rows.map((belief) => (
          <div className="memory-why-row" key={belief.id} data-testid="memory-belief">
            <span className="surface-primary">{belief.text}</span>
            <RefTokens refs={belief.evidence} onOpen={openRef} label="Belief sources" />
          </div>
        ))}
      </div>
    </Disclosure>
  );
}

function DeskPage({ page, beliefs }: { page: StandingPageWire; beliefs: BeliefCardData[] }) {
  return (
    <article className="memory-home-page" data-testid={`memory-page-${page.slug}`}>
      <StandingPage
        title={page.slug === "what-i-owe" ? "What I owe" : "What changed this week"}
        sentences={page.sentences}
        built={builtToken(page.built_at)}
        stale={page.stale}
        newSources={page.new_sources}
        onOpenRef={openRef}
      />
      <Why page={page} beliefs={beliefs} />
    </article>
  );
}

/** Sentence-case kind words for a found row (the kit's are caps). */
const FOUND_KIND: Record<string, string> = {
  project: "Project", person: "Person", decision: "Decision", action: "Commitment",
  meeting: "Meeting", note: "Note", brief: "Brief", artifact: "Result",
  desk_decision: "Decision", calendar_event: "Calendar", thought: "Note", action_item: "Commitment",
};

function shortDay(value: unknown): string {
  const date = wireDate(value);
  return date ? date.toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "";
}

function foundMeta(kind: string, at?: unknown): string {
  const plain = kind.replace(/_/g, " ");
  return [FOUND_KIND[kind] ?? (plain ? plain[0].toUpperCase() + plain.slice(1) : ""), shortDay(at)].filter(Boolean).join(" · ");
}

/** What the desk remembers that matches the words: decisions, commitments,
 *  meetings and briefs from `/api/memory/recall` as found rows. */
function recallRows(result: RecallResult): ObjectListRow[] {
  const rows: ObjectListRow[] = [];
  const seen = new Set<string>();
  const glyphKind: Record<string, string> = {
    desk_decision: "decision", calendar_event: "meeting", brief: "note", thought: "note", action_item: "action",
  };
  const add = (ref: string, kind: string, name: string, at?: unknown) => {
    if (!ref || !name || seen.has(ref)) return;
    seen.add(ref);
    rows.push({ id: ref, kind: glyphKind[kind] ?? kind, name, cells: { meta: foundMeta(kind, at) }, sortValues: { none: rows.length } });
  };
  for (const d of [...result.current, ...result.disputed, ...result.superseded]) add(d.ref, "decision", d.text, d.decided_at);
  for (const o of result.owed) add(o.ref, "action", o.text, o.due_at);
  for (const h of [...result.meetings, ...result.briefs, ...result.also]) {
    add(h.source_ref, h.kind, h.title || h.snippet, h.occurred_at);
  }
  return rows;
}

/** The found rows for the words, read after a short pause in typing. */
function useFound(query: string) {
  const [state, setState] = useState<{ query: string; rows: ObjectListRow[]; status: "idle" | "reading" | "ready" | "failed" }>(
    { query: "", rows: [], status: "idle" },
  );
  useEffect(() => {
    const words = query.trim();
    if (words.length < 2) { setState({ query: words, rows: [], status: "idle" }); return undefined; }
    let live = true;
    setState((current) => ({ ...current, query: words, status: "reading" }));
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({ query: words, filter: "all" });
      void apiFetch<Record<string, unknown>>(`/api/memory/recall?${params}`)
        .then((raw) => { if (live) setState({ query: words, rows: recallRows(decodeRecall(raw)), status: "ready" }); })
        .catch(() => { if (live) setState({ query: words, rows: [], status: "failed" }); });
    }, 250);
    return () => { live = false; window.clearTimeout(timer); };
  }, [query]);
  return state;
}

/** Memory's toolbar: the Ask composer row over the whole desk. The field
 *  finds as it is typed; Ask ⏎ asks the Ask window. */
function MemoryComposer({ value, onChange }: { value: string; onChange: (next: string) => void }) {
  const engine = useEngine("ask.answer");
  const ask = () => {
    const text = value.trim();
    if (!text) return;
    // No About chip means the Ask window uses the owner's whole desk.
    useDesk.getState().askQuestion(text);
  };
  return (
    <AskComposer
      className="memory-composer"
      data-testid="memory-toolbar"
      scope={<span className="desk-ask-scope-word desk-ask-scope-preset" title="About: My whole desk"><span className="desk-ask-scope-text">My whole desk</span></span>}
      field={
        <span className="memory-ask" data-testid="memory-ask">
          <StringGadget
            label="Find or ask your desk"
            mic={false}
            type="search"
            value={value}
            placeholder="Find or ask your desk"
            onChange={onChange}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); ask(); }
              if (event.key === "Escape" && value) { event.stopPropagation(); onChange(""); }
            }}
          />
        </span>
      }
      capture={
        <MicButton
          label="Speak your question"
          draftScope="memory-ask"
          onText={(text) => onChange(value ? `${value} ${text}` : text)}
        />
      }
      engine={engine.state === "unread" ? null : (
        <AskEngineWord
          state={engine.state}
          name={engine.model}
          onPress={engine.state === "failed" ? () => void refreshEngine("ask.answer") : () => openSurfaceOr("configure-runs-on", "/settings", "models")}
        />
      )}
      action={<AskSendButton disabled={!value.trim()} onClick={ask} />}
    />
  );
}

const ROLE_WORDS: Record<string, string> = {
  direct_report: "Direct report",
  peer: "Peer",
  extended: "Extended",
};

// The link lists: one dense list view per group, the group caption above
// it stands for the column head.
const LINK_COLUMNS = [
  { key: "name", word: "Name", track: "minmax(0, 1fr)" },
  { key: "meta", word: "Details", track: "minmax(0, max-content)" },
];
const LINK_SORT = { key: "none", dir: "asc" } as const;

function LinkGroup({ label, rows, selected, onSelect, onOpen }: {
  label: string;
  rows: ObjectListRow[];
  selected: string | null;
  onSelect: (id: string) => void;
  onOpen: (id: string) => void;
}) {
  if (!rows.length) return null;
  return (
    <section className="memory-group" aria-label={label} data-testid={`memory-${label.toLowerCase()}`}>
      <h3 className="memory-caption">{label}</h3>
      <ObjectList
        label={label}
        density="dense"
        rows={rows}
        columns={LINK_COLUMNS.filter((column) => column.key === "name" || rows.some((row) => row.cells?.meta))}
        sort={LINK_SORT}
        selectedId={selected}
        onSelect={onSelect}
        onOpen={onOpen}
      />
    </section>
  );
}

function MemoryHome() {
  useWindowInterior("list");
  const { loaded, pages } = useStandingPagesRead("desk");
  const { projects, people, loaded: linksLoaded } = useDeskLinks();
  const pageEngine = useEngine("memory.page");
  const needs = useNeedsYou({ poll: false });
  const [beliefs, setBeliefs] = useState<BeliefCardData[]>([]);
  const [beliefsLoaded, setBeliefsLoaded] = useState(false);
  const [shown, setShown] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const found = useFound(query);

  useEffect(() => {
    let live = true;
    void apiFetch<Record<string, unknown>>("/api/memory/recall?recent=1&filter=all")
      .then((raw) => { if (live) setBeliefs(decodeRecall(raw).beliefs); })
      .catch(() => { if (live) setBeliefs([]); })
      .finally(() => { if (live) setBeliefsLoaded(true); });
    return () => { live = false; };
  }, []);

  const ordered = DESK_PAGE_ORDER
    .map((slug) => pages.find((page) => page.slug === slug))
    .filter((page): page is StandingPageWire => Boolean(page));
  const hasPages = ordered.length > 0;
  // First paint keeps every control below the answers in one settled batch.
  // Ask stays available while independent reads finish or fail.
  useEffect(() => {
    if (loaded && linksLoaded && beliefsLoaded && (hasPages || pageEngine.state !== "unread")) setShown(true);
  }, [loaded, linksLoaded, beliefsLoaded, hasPages, pageEngine.state]);

  const openHere = projectOpenHere(needs);
  const projectRows: ObjectListRow[] = projects.flatMap((project, index) => {
    const id = String(project.id || "");
    if (!id) return [];
    const open = openHere[id] ?? 0;
    const meta = [open > 0 ? `${open} open` : null, countWords(Number(project.meeting_count) || 0, "meeting")]
      .filter(Boolean).join(" · ");
    return [{
      id: `project:${id}`, kind: "project", name: String(project.name || project.title || id),
      cells: meta ? { meta } : undefined,
      sortValues: { none: index },
    }];
  });
  const personRows: ObjectListRow[] = people.flatMap((person, index) => {
    const id = String(person.id || "");
    if (!id) return [];
    const name = String(person.display_name || person.name || id);
    const owe = Number(person.you_owe_count) || 0;
    const role = ROLE_WORDS[String(person.relationship_kind || "")] ?? null;
    const meta = [role, owe > 0 ? `You owe ${owe}` : null].filter(Boolean).join(" · ");
    return [{
      id: `person:${id}`, kind: "person", name,
      avatar: { initials: initialsOf(name), hue: hueOf(name) },
      cells: meta ? { meta } : undefined,
      sortValues: { none: index },
    }];
  });
  const words = query.trim().toLowerCase();
  const finding = words.length > 0;
  // Found: the projects and people whose names hold the words, then what
  // the desk remembers (decisions, commitments, meetings, briefs).
  const foundRows = useMemo<ObjectListRow[]>(() => {
    if (!finding) return [];
    const named = [...projectRows, ...personRows]
      .filter((row) => row.name.toLowerCase().includes(words))
      .map((row, index) => ({ ...row, cells: { meta: foundMeta(row.kind) }, sortValues: { none: index } }));
    const recalled = found.query.toLowerCase() === words ? found.rows : [];
    return [...named, ...recalled.map((row, index) => ({ ...row, sortValues: { none: named.length + index } }))];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [finding, words, projects, people, found]);
  const openLink = (ref: string) => {
    const [kind, ...rest] = ref.split(":");
    const id = rest.join(":");
    if (kind === "project") openProjectRoom(id);
    else if (kind === "person") openPerson(id);
    else openRef(ref);
  };
  const visible = finding ? foundRows : [...projectRows, ...personRows];
  const chosen = selected && visible.some((row) => row.id === selected) ? selected : null;
  const newest = ordered.map((page) => page.built_at).filter(Boolean).sort().pop();
  const nothingYet = shown && !hasPages && !projectRows.length && !personRows.length;
  const reading = finding && found.status === "reading";

  return (
    <div className="memory-home" data-testid="memory-home">
      <MemoryComposer value={query} onChange={setQuery} />
      <div className="memory-body">
        {!shown ? <p className="room-empty-line">Reading your desk</p> : finding ? (
          foundRows.length ? (
            <LinkGroup label="Found" rows={foundRows} selected={chosen} onSelect={setSelected} onOpen={openLink} />
          ) : reading ? null : (
            <p className="memory-line" data-testid="memory-none-found">
              {found.status === "failed" ? <DotWord tone="warn">Memory not read</DotWord> : "Nothing on this desk has these words"}
            </p>
          )
        ) : (<>
          {hasPages ? (
            <div className="memory-reader memory-home-pages">
              {ordered.map((page) => <DeskPage key={page.slug} page={page} beliefs={beliefs} />)}
            </div>
          ) : pageEngine.state === "none" ? (
            <p className="memory-line" data-testid="memory-pages-line">
              <DotWord tone="idle">No engine writes the desk pages</DotWord>
              <Button dense variant="ghost" data-testid="memory-choose-engine"
                onClick={() => openSurfaceOr("open-concierge", "/models", "background")}>
                <ToolGlyph kind="engine" />
                Choose engine
              </Button>
            </p>
          ) : null}
          {nothingYet ? (
            <p className="memory-line" data-testid="memory-nothing">No projects or people yet</p>
          ) : null}
          <LinkGroup label="Projects" rows={projectRows} selected={chosen} onSelect={setSelected} onOpen={openLink} />
          <LinkGroup label="People" rows={personRows} selected={chosen} onSelect={setSelected} onOpen={openLink} />
        </>)}
      </div>
      {shown ? (
        <StatusBar
          data-testid="memory-status"
          verbs={chosen ? (
            <Button dense variant="secondary" data-testid="memory-open-selected" onClick={() => openLink(chosen)}>
              <ToolGlyph kind="open" />
              Open
            </Button>
          ) : null}
          items={finding ? [
            reading ? { key: "found", text: "Finding" } : foundRows.length ? { key: "found", testId: "memory-found-count", text: `${foundRows.length} found` } : null,
          ] : [
            hasPages
              ? { key: "written", testId: "memory-written", text: newest ? `Written ${humanTime(newest)}` : "Written" }
              : loaded ? { key: "written", testId: "memory-empty", text: "Desk pages not written yet" } : null,
            { key: "projects", text: countWords(projectRows.length, "project") },
            { key: "people", text: countWords(personRows.length, "person", "people") },
          ]}
        />
      ) : null}
    </div>
  );
}

/** The application has two scopes: Memory for the desk, Room for a project. */
export function MemoryCore(props: CoreProps) {
  if (props.scope?.startsWith("project:")) return <ProjectRoomCore {...props} />;
  if (props.scope?.startsWith("q:")) return <RecallFace initialQuery={props.scope.slice(2).trim()} />;
  return <MemoryHome />;
}
