/* Betterment Q12 — Memory is the answer desk.
 *
 * The unscoped Memory window opens on the two desk pages the owner uses.  The
 * older recall/search face remains available under RAW, while a project scope
 * continues to open the Room through the same application registration.
 */
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../../desk/store";
import { openPerson, openRef } from "../../desk/openObject";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { apiFetch } from "../../lib/api";
import { Disclosure, EngineLine, RefTokens, StandingPage, StringGadget, SurfaceFooter, SurfaceRows, SurfaceRow, SurfaceSection } from "../../desk/surface";
import { useEngine } from "../../desk/hooks/useEngine";
import { builtToken, useStandingPagesRead, type StandingPageWire } from "../../desk/standingPages";
import { RecallFace } from "../../features/project-room/recall/RecallFace";
import { decodeRecall, type BeliefCardData } from "../../features/project-room/recall/model";
import type { CoreProps } from "./core-types";
import { ProjectRoomCore } from "../../features/project-room/ProjectRoomCore";
import "./memory.css";

type ProjectRow = { id?: string; name?: string; title?: string };
type PersonRow = { id?: string; display_name?: string; name?: string };

const DESK_PAGE_ORDER = ["what-i-owe", "what-changed-this-week"] as const;

function useDeskLinks() {
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [people, setPeople] = useState<PersonRow[]>([]);
  useEffect(() => {
    let live = true;
    void Promise.allSettled([
      apiFetch<{ projects?: ProjectRow[] }>("/api/projects"),
      apiFetch<{ relationships?: PersonRow[] }>("/api/people/relationships"),
    ]).then(([projectResult, peopleResult]) => {
      if (!live) return;
      if (projectResult.status === "fulfilled") {
        setProjects(Array.isArray(projectResult.value?.projects) ? projectResult.value.projects : []);
      }
      if (peopleResult.status === "fulfilled") {
        setPeople(Array.isArray(peopleResult.value?.relationships) ? peopleResult.value.relationships : []);
      }
    });
    return () => { live = false; };
  }, []);
  return { projects, people };
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
    <div className="memory-ask" data-testid="memory-ask">
      <StringGadget
        label="Ask your desk"
        micLabel="Dictate into your question"
        type="search"
        value={question}
        placeholder="Ask your desk"
        onChange={setQuestion}
        onKeyDown={(event) => { if (event.key === "Enter") ask(); }}
      />
      <Button dense variant="secondary" disabled={!question.trim()} onClick={ask}>Ask</Button>
    </div>
  );
}

function MemoryHome() {
  const { loaded, pages } = useStandingPagesRead("desk");
  const { projects, people } = useDeskLinks();
  const engine = useEngine("memory.page");
  const [beliefs, setBeliefs] = useState<BeliefCardData[]>([]);

  useEffect(() => {
    let live = true;
    void apiFetch<Record<string, unknown>>("/api/memory/recall?recent=1&filter=all")
      .then((raw) => { if (live) setBeliefs(decodeRecall(raw).beliefs); })
      .catch(() => { if (live) setBeliefs([]); });
    return () => { live = false; };
  }, []);

  const ordered = DESK_PAGE_ORDER
    .map((slug) => pages.find((page) => page.slug === slug))
    .filter((page): page is StandingPageWire => Boolean(page));
  const hasPages = ordered.length > 0;

  return (
    <>
      <div className="room-body memory-home" data-testid="memory-home">
        <AskYourDesk />
        {!loaded ? <p className="room-empty-line">Loading…</p> : null}
        {loaded && !hasPages ? (
          <SurfaceStateEmpty engine={engine} />
        ) : null}
        {hasPages ? (
          <SurfaceSection label="Memory" className="memory-home-pages">
            {ordered.map((page) => <DeskPage key={page.slug} page={page} beliefs={beliefs} />)}
          </SurfaceSection>
        ) : null}
        {projects.length ? (
          <SurfaceSection label="Projects" className="memory-home-links">
            <SurfaceRows>
              {projects.map((project) => {
                const id = String(project.id || "");
                const name = String(project.name || project.title || id);
                return id ? <SurfaceRow key={id} title={name} onOpen={() => openProjectRoom(id)} /> : null;
              })}
            </SurfaceRows>
          </SurfaceSection>
        ) : null}
        {people.length ? (
          <SurfaceSection label="People" className="memory-home-links">
            <SurfaceRows>
              {people.map((person) => {
                const id = String(person.id || "");
                const name = String(person.display_name || person.name || id);
                return id ? <SurfaceRow key={id} title={name} onOpen={() => openPerson(id)} /> : null;
              })}
            </SurfaceRows>
          </SurfaceSection>
        ) : null}
        <Disclosure label="RAW" variant="dense">
          <RecallFace />
        </Disclosure>
      </div>
      <SurfaceFooter />
    </>
  );
}

function SurfaceStateEmpty({ engine }: { engine: ReturnType<typeof useEngine> }) {
  return (
    <div className="memory-home-empty" data-testid="memory-empty">
      <p>Not written yet.</p>
      <EngineLine
        engine={engine}
        onChoose={() => openSurfaceOr("open-concierge", "/models", "background")}
      />
    </div>
  );
}

/** The application has two scopes: Memory for the desk, Room for a project. */
export function MemoryCore(props: CoreProps) {
  if (props.scope?.startsWith("project:")) return <ProjectRoomCore {...props} />;
  if (props.scope?.startsWith("q:")) return <RecallFace initialQuery={props.scope.slice(2).trim()} />;
  return <MemoryHome />;
}
