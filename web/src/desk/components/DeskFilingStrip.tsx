import { useEffect, useRef, useState } from "react";
import { apiRequest } from "../../lib/api";
import { qualifiedRef } from "../api";
import { useDesk } from "../store";
import { FoldGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState } from "../surface/Surface";
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
function filedWords(relationships: any, zones: any[], knowledgeChoices: any[], objectRef: string, objectId: string, objectKind: string): string {
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
  const projects = (relationships.projects || []).length;
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
}: DeskFilingStripProps) {
  const items = useDesk((state) => state.items);
  const [relationships, setRelationships] = useState<any>(null);
  const [knowledgeChoices, setKnowledgeChoices] = useState<any[]>([]);
  const [projectChoices, setProjectChoices] = useState<any[]>([]);
  const [relationshipError, setRelationshipError] = useState("");
  const zones = items.directory || [];
  const onSummaryRef = useRef(onSummary);
  onSummaryRef.current = onSummary;

  const refreshRelationships = async () => {
    try {
      const [axesRes, knowledgeRes, projectRes] = await Promise.all([
        apiRequest(`/api/desk/relationships/${encodeURIComponent(objectRef)}`),
        apiRequest("/api/kbs"),
        apiRequest("/api/projects"),
      ]);
      const [axes, knowledge, projects] = await Promise.all([
        axesRes.json(),
        knowledgeRes.json(),
        projectRes.json(),
      ]);
      setRelationships(axes);
      setKnowledgeChoices((knowledge.kbs || []).filter((entry: any) => !entry.deleted));
      setProjectChoices(
        (projects.projects || []).filter((entry: any) => !entry.is_archived),
      );
      setRelationshipError("");
    } catch (error) {
      setRelationshipError(String(error));
    }
  };

  useEffect(() => {
    setRelationships(null);
    void refreshRelationships();
  }, [objectRef]);

  const toggleRelationship = async (
    axis: "knowledge" | "projects",
    ownerId: string,
    active: boolean,
  ) => {
    const base = axis === "knowledge" ? "kbs" : "projects";
    try {
      await apiRequest(
        `/api/${base}/${encodeURIComponent(ownerId)}/${axis === "knowledge" ? "members" : "resources"}/${encodeURIComponent(objectRef)}`,
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
      sfx("file");
      await refreshRelationships();
      await useDesk.getState().refresh();
    } catch (error) {
      sfx("error");
      setRelationshipError(String(error));
    }
  };

  // The summary in words for a status bar (`Desk`, `Ledger · 1 Project`).
  const summaryWords = relationships ? filedWords(relationships, zones, knowledgeChoices, objectRef, objectId, objectKind) : "";
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
  const projectCount = (relationships.projects || []).length;
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
          {projectChoices.length > 0 && (
            <div className="desk-pullout-filed-axis">
              <span className="surface-eyebrow">Projects</span>
              <div className="desk-pullout-lineage">
                {projectChoices.map((project) => {
                  const active = (relationships.projects || []).some(
                    (row: any) => row.project_id === project.id,
                  );
                  return (
                    <span className="desk-project-choice" key={project.id}>
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
