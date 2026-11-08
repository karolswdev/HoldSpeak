import { useEffect, useRef, useState } from "react";
import { apiRequest } from "../../lib/api";
import { qualifiedRef } from "../api";
import { useDesk } from "../store";
import { FoldGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState } from "../surface/Surface";
import { DotWord } from "../surface/kit";
import { play as sfx } from "../../lib/sfx";
import { Button } from "../../components/signal/Signal";

interface DeskFilingStripProps {
  objectRef: string;
  objectKind: string;
  objectId: string;
  /** W1-TRUTH (reader grammar): the drawers and Projects open, with no
   *  "Filed · …" fold around them (the window's status bar names where it
   *  is filed and opens this). */
  bare?: boolean;
  /** Where the object is filed, in words (`Desk`, `Ledger · 1 Project`). */
  onSummary?: (summary: string) => void;
  /** HS-S42: the ref the Projects axis reads and writes. Left out, it is
   *  `objectRef` (every existing consumer). A string is a canonical record
   *  (`decision_record:<id>`): Projects act on it while drawers keep
   *  `objectRef`, and the source's own project rows show read-only. `null`:
   *  the identity is not established, so the Projects axis does nothing. */
  projectRef?: string | null;
  /** Why the Projects axis is closed while `projectRef` is null. */
  projectNote?: string;
  onProjectRetry?: () => void;
}

const RELATIONSHIP_KINDS = new Set(["member", "source", "output", "related"]);

async function readJson(response: Response): Promise<any> {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function FilingRefusal({
  detail,
  onRetry,
}: {
  detail: string;
  onRetry: () => void;
}) {
  return (
    <>
      <SurfaceState error="Filing unavailable" onRetry={onRetry} />
      <FoldGadget title="RAW · DETAIL">
        <SurfaceCode>{detail}</SurfaceCode>
      </FoldGadget>
    </>
  );
}

/** Where an object is filed, in words: its drawer (`Desk` at the root), its
 *  collections and its Project count. */
function filedWords(relationships: any, zones: any[], knowledgeChoices: any[], objectRef: string, objectId: string, objectKind: string, projectRows?: any[]): string {
  const home = zones.find((zone) => {
    const members = zone.memberIds || [];
    return members.includes(objectId) || members.includes(objectRef);
  });
  const parentId = objectKind === "directory" ? zones.find((zone) => zone.id === objectId)?.parentId : null;
  const parent = parentId ? zones.find((zone) => zone.id === parentId) : undefined;
  const collections = knowledgeChoices
    .filter((knowledge) => objectRef !== qualifiedRef("kb", knowledge.id))
    .filter((knowledge) => (relationships.knowledge || []).some((row: any) => row.knowledge_id === knowledge.id))
    .map((knowledge) => String(knowledge.name || "Drawer"));
  const projects = (projectRows ?? relationships.projects ?? []).length;
  return [
    parent ? String(parent.name || parent.id) : home ? String(home.name || home.id) : "Desk",
    ...collections,
    projects ? `${projects} Project${projects === 1 ? "" : "s"}` : "",
  ].filter(Boolean).join(" · ");
}

/** The one filing disclosure: named drawers and project membership. */
export function DeskFilingStrip({
  objectRef,
  objectKind,
  objectId,
  bare = false,
  onSummary,
  projectRef,
  projectNote,
  onProjectRetry,
}: DeskFilingStripProps) {
  const items = useDesk((state) => state.items);
  const [relationships, setRelationships] = useState<any>(null);
  const [knowledgeChoices, setKnowledgeChoices] = useState<any[]>([]);
  const [projectChoices, setProjectChoices] = useState<any[]>([]);
  const [relationshipError, setRelationshipError] = useState("");
  // HS-S42: the canonical record's own project rows, when projectRef names one.
  const [canonicalRows, setCanonicalRows] = useState<any[] | null>(null);
  const generation = useRef(0);
  const toggling = useRef(false);
  const canonical = typeof projectRef === "string" && projectRef !== objectRef;
  const zones = items.directory || [];
  const onSummaryRef = useRef(onSummary);
  onSummaryRef.current = onSummary;

  const refreshRelationships = async () => {
    const mine = generation.current;
    try {
      const [axes, knowledge, projects, canonicalAxes] = await Promise.all([
        apiRequest(`/api/desk/relationships/${encodeURIComponent(objectRef)}`).then(readJson),
        apiRequest("/api/kbs").then(readJson),
        apiRequest("/api/projects").then(readJson),
        canonical
          ? apiRequest(`/api/desk/relationships/${encodeURIComponent(projectRef as string)}`).then(readJson)
          : Promise.resolve(null),
      ]);
      // A late answer for another identity never lands here.
      if (mine !== generation.current) return;
      if (canonical && !Array.isArray(canonicalAxes?.projects)) throw new Error("The hub answered no project rows");
      setRelationships(axes);
      setCanonicalRows(canonical ? canonicalAxes.projects : null);
      setKnowledgeChoices((knowledge.kbs || []).filter((entry: any) => !entry.deleted));
      setProjectChoices(
        (projects.projects || []).filter((entry: any) => !entry.is_archived),
      );
      setRelationshipError("");
    } catch (error) {
      if (mine !== generation.current) return;
      setRelationshipError(String(error));
    }
  };

  useEffect(() => {
    generation.current += 1;
    setRelationships(null);
    setCanonicalRows(null);
    void refreshRelationships();
  }, [objectRef, projectRef]);

  const toggleRelationship = async (
    axis: "knowledge" | "projects",
    ownerId: string,
    active: boolean,
  ) => {
    if (toggling.current) return;
    if (axis === "projects" && projectRef === null) return;
    toggling.current = true;
    const base = axis === "knowledge" ? "kbs" : "projects";
    const target = axis === "projects" && canonical ? (projectRef as string) : objectRef;
    const mine = generation.current;
    try {
      const response = await apiRequest(
        `/api/${base}/${encodeURIComponent(ownerId)}/${axis === "knowledge" ? "members" : "resources"}/${encodeURIComponent(target)}`,
        {
          method: active ? "DELETE" : "PUT",
          ...(axis === "projects" && !active
            ? {
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ relationship: "member" }),
              }
            : {}),
        },
      );
      // HS-S42: a refused write is no success: no sound, no count.
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (mine === generation.current) sfx("file");
    } catch (error) {
      toggling.current = false;
      if (mine !== generation.current) return;
      sfx("error");
      setRelationshipError(String(error));
      return;
    }
    toggling.current = false;
    // The write is known; a failed read after it shows as a read failure.
    await refreshRelationships();
    await useDesk.getState().refresh();
  };

  // The summary in words for a status bar (`Desk`, `Ledger · 1 Project`).
  const projectRows: any[] = canonical
    ? (canonicalRows ?? []).filter((row: any) => row?.relationship === "member")
    : projectRef === null ? [] : (relationships?.projects || []);
  const summaryWords = relationships ? filedWords(relationships, zones, knowledgeChoices, objectRef, objectId, objectKind, projectRows) : "";
  useEffect(() => {
    if (summaryWords) onSummaryRef.current?.(summaryWords);
  }, [summaryWords]);

  if (!relationships) return relationshipError ? (
    <FilingRefusal
      detail={relationshipError}
      onRetry={() => void refreshRelationships()}
    />
  ) : null;

  const homeZone = zones.find((zone) => {
    const members = zone.memberIds || [];
    return members.includes(objectId) || members.includes(objectRef);
  });
  const parentId = objectKind === "directory"
    ? zones.find((zone) => zone.id === objectId)?.parentId : null;
  const parentZone = parentId ? zones.find((zone) => zone.id === parentId) : undefined;
  const knowledgeHomes = knowledgeChoices.filter(
    (knowledge) => objectRef !== qualifiedRef("kb", knowledge.id),
  );
  const collectionNames = knowledgeHomes
    .filter((knowledge) => (relationships.knowledge || []).some((row: any) => row.knowledge_id === knowledge.id))
    .map((knowledge) => String(knowledge.name || "Drawer"));
  const projectCount = projectRows.length;
  const sourceProjects = canonical ? (relationships.projects || []) : [];
  const filedSummary = [
    parentZone ? String(parentZone.name || parentZone.id)
      : homeZone ? String(homeZone.name || homeZone.id) : "Desk root",
    ...collectionNames,
    projectCount ? `${projectCount} Project${projectCount === 1 ? "" : "s"}` : "",
  ]
    .filter(Boolean)
    .join(" · ");

  const body = (
        <div className="desk-pullout-filed">
          {(zones.length > 0 || knowledgeHomes.length > 0) && (
            <div className="desk-pullout-filed-axis">
              <span className="surface-eyebrow">Drawers</span>
              <div className="desk-pullout-lineage">
                {zones.map((zone) => {
                  const members = zone.memberIds || [];
                  const inZone = members.includes(objectId) || members.includes(objectRef);
                  return (
                    <Button
                      variant="chrome"
                      key={`directory:${zone.id}`}
                      className={`desk-chip quiet${inZone ? " in-zone" : ""}`}
                      aria-pressed={inZone}
                      onClick={() =>
                        void (inZone
                          ? useDesk.getState().removeFromDir(objectId, String(zone.id), objectKind)
                          : useDesk.getState().fileIntoDir(objectId, String(zone.id), objectKind))
                      }
                    >
                      {inZone ? <><span aria-hidden="true">✓</span>{" "}</> : "+ "}
                      {String(zone.name || zone.id)}
                    </Button>
                  );
                })}
                {knowledgeHomes.map((knowledge) => {
                  const active = (relationships.knowledge || []).some(
                    (row: any) => row.knowledge_id === knowledge.id,
                  );
                  return (
                    <Button
                      variant="chrome"
                      key={`kb:${knowledge.id}`}
                      className={`desk-chip quiet${active ? " in-zone" : ""}`}
                      aria-pressed={active}
                      onClick={() => void toggleRelationship("knowledge", knowledge.id, active)}
                    >
                      {active ? <><span aria-hidden="true">✓</span>{" "}</> : "+ "}
                      {knowledge.name}
                    </Button>
                  );
                })}
              </div>
            </div>
          )}
          {projectRef === null ? (
            <div className="desk-pullout-filed-axis" data-testid="filing-projects-closed">
              <span className="surface-eyebrow">Projects</span>
              <div className="desk-pullout-lineage">
                <DotWord tone="warn">{projectNote || "Projects not read"}</DotWord>
                {onProjectRetry ? (
                  <Button variant="chrome" className="desk-chip quiet" onClick={onProjectRetry}>Read again</Button>
                ) : null}
              </div>
            </div>
          ) : projectChoices.length > 0 && (
            <div className="desk-pullout-filed-axis">
              <span className="surface-eyebrow">Projects</span>
              <div className="desk-pullout-lineage">
                {projectChoices.map((project) => {
                  // HS-S42: on a canonical record only a live `member` row is
                  // a filing; a row of another kind is shown, never toggled.
                  const row = (canonical ? canonicalRows ?? [] : relationships.projects || []).find(
                    (candidate: any) => candidate.project_id === project.id,
                  );
                  const active = canonical ? row?.relationship === "member" : Boolean(row);
                  const otherKind = canonical && row && !active
                    ? (RELATIONSHIP_KINDS.has(String(row.relationship)) ? String(row.relationship) : "unknown")
                    : "";
                  return (
                    <span className="desk-project-choice" key={project.id}>
                      {otherKind ? (
                        <Button
                          variant="chrome"
                          className="desk-chip quiet"
                          aria-label={`${project.name} Project links it as ${otherKind}`}
                          disabled
                        >
                          {project.name} · {otherKind}
                        </Button>
                      ) : (
                        <Button
                          variant="chrome"
                          className={`desk-chip quiet${active ? " in-zone" : ""}`}
                          aria-label={`${active ? "Remove from" : "Assign to"} ${project.name} Project`}
                          aria-pressed={active}
                          onClick={() => void toggleRelationship("projects", project.id, active)}
                        >
                          {active ? <><span aria-hidden="true">✓</span>{" "}</> : "+ "}
                          {project.name}
                        </Button>
                      )}
                      <Button
                        variant="chrome"
                        className="desk-chip quiet"
                        aria-label={`Inspect ${project.name} Project`}
                        onClick={() => useDesk.getState().openToolInspector("project", String(project.id))}
                      >
                        Inspect
                      </Button>
                    </span>
                  );
                })}
              </div>
            </div>
          )}
          {sourceProjects.length > 0 && (
            <div className="desk-pullout-filed-axis" data-testid="filing-source-projects">
              <span className="surface-eyebrow">Source projects</span>
              <div className="desk-pullout-lineage">
                {sourceProjects.map((row: any) => (
                  <DotWord key={`source:${row.project_id}`}>
                    {String(projectChoices.find((project) => project.id === row.project_id)?.name || row.project_id)}
                  </DotWord>
                ))}
              </div>
            </div>
          )}
          {!zones.length && !knowledgeChoices.length && !projectChoices.length && (
            <SurfaceState empty emptyLabel="No destinations" />
          )}
        </div>
  );
  return (
    <>
      {bare ? body : <FoldGadget title={`Filed · ${filedSummary}`}>{body}</FoldGadget>}
      {relationshipError ? (
        <FilingRefusal
          detail={relationshipError}
          onRetry={() => void refreshRelationships()}
        />
      ) : null}
    </>
  );
}
