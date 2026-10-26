/* Betterment Q12 — Memory is the answer desk.
 *
 * The unscoped Memory window opens on the two desk pages the owner uses.  A
 * `q:` scope opens the recall/search face, while a project scope continues to
 * open the Room through the same application registration.
 *
 * Window grammar (2026-10-24): Toolbar [Choose engine when none | Ask your
 * desk] → the written pages as a reader → Projects and People as dense list
 * views under sentence-case captions → StatusBar (`Written 3h ago · 4
 * projects · 4 people`, or `Not written yet`). The old recall face is not a
 * fold on this face any more (debug hides behind RAW on the desk floor).
 */
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../../desk/store";
import { openPerson, openRef } from "../../desk/openObject";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { apiFetch } from "../../lib/api";
import { Disclosure, RefTokens, StandingPage, StringGadget } from "../../desk/surface";
import { StatusBar, ToolGlyph, Toolbar, countWords, hueOf, initialsOf } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { humanTime } from "../../desk/surface/format";
import { ObjectList, type ObjectListRow } from "../../desk/surface/objects/ObjectList";
import { projectOpenHere, useNeedsYou } from "../../desk/needsYou";
import { useEngine } from "../../desk/hooks/useEngine";
import { builtToken, useStandingPagesRead, type StandingPageWire } from "../../desk/standingPages";
import { RecallFace } from "../../features/project-room/recall/RecallFace";
import { decodeRecall, type BeliefCardData } from "../../features/project-room/recall/model";
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

function AskYourDesk() {
  const [question, setQuestion] = useState("");
  const ask = useCallback(() => {
    const text = question.trim();
    if (!text) return;
    // No About chip means the Ask window uses the owner's whole desk.
    useDesk.getState().askQuestion(text);
  }, [question]);
  return (
    <span className="memory-ask" data-testid="memory-ask">
      <StringGadget
        label="Ask your desk"
        micLabel="Dictate into your question"
        type="search"
        value={question}
        placeholder="Ask your desk"
        onChange={setQuestion}
        onKeyDown={(event) => { if (event.key === "Enter") ask(); }}
      />
      <Button dense variant="secondary" disabled={!question.trim()} onClick={ask}>
        <ToolGlyph kind="ask" />
        Ask
      </Button>
    </span>
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
  const engine = useEngine("memory.page");
  const needs = useNeedsYou({ poll: false });
  const [beliefs, setBeliefs] = useState<BeliefCardData[]>([]);
  const [beliefsLoaded, setBeliefsLoaded] = useState(false);
  const [shown, setShown] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

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
    if (loaded && linksLoaded && beliefsLoaded && (hasPages || engine.state !== "unread")) setShown(true);
  }, [loaded, linksLoaded, beliefsLoaded, hasPages, engine.state]);

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
  const openLink = (ref: string) => {
    const [kind, ...rest] = ref.split(":");
    const id = rest.join(":");
    if (kind === "project") openProjectRoom(id);
    else openPerson(id);
  };
  const chosen = selected && [...projectRows, ...personRows].some((row) => row.id === selected) ? selected : null;
  const newest = ordered.map((page) => page.built_at).filter(Boolean).sort().pop();
  const noEngine = engine.state === "none";

  return (
    <div className="memory-home" data-testid="memory-home">
      <Toolbar label="Memory" data-testid="memory-toolbar" trailing={<AskYourDesk />}>
        {shown && noEngine ? (
          <Button dense variant="secondary" data-testid="memory-choose-engine"
            onClick={() => openSurfaceOr("open-concierge", "/models", "background")}>
            <ToolGlyph kind="engine" />
            Choose engine
          </Button>
        ) : null}
      </Toolbar>
      <div className="memory-body">
        {!shown ? <p className="room-empty-line">Loading…</p> : (<>
          {hasPages ? (
            <div className="memory-reader memory-home-pages">
              {ordered.map((page) => <DeskPage key={page.slug} page={page} beliefs={beliefs} />)}
            </div>
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
          items={[
            hasPages
              ? { key: "written", testId: "memory-written", text: newest ? `Written ${humanTime(newest)}` : "Written" }
              : loaded ? { key: "written", testId: "memory-empty", text: "Not written yet" } : null,
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
