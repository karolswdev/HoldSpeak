import { useEffect, useState } from "react";
import { apiRequest } from "../../lib/api";
import { qualifiedRef } from "../api";
import { useDesk } from "../store";
import { FoldGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState } from "../surface/Surface";
import { play as sfx } from "../../lib/sfx";

interface DeskFilingStripProps {
  objectRef: string;
  objectKind: string;
  objectId: string;
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

/** The one filing disclosure: Zone, Knowledge, and Project membership. */
export function DeskFilingStrip({
  objectRef,
  objectKind,
  objectId,
}: DeskFilingStripProps) {
  const items = useDesk((state) => state.items);
  const [relationships, setRelationships] = useState<any>(null);
  const [knowledgeChoices, setKnowledgeChoices] = useState<any[]>([]);
  const [projectChoices, setProjectChoices] = useState<any[]>([]);
  const [relationshipError, setRelationshipError] = useState("");
  const zones = items.directory || [];

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
  const knowledgeHomes = knowledgeChoices.filter(
    (knowledge) => objectRef !== qualifiedRef("kb", knowledge.id),
  );
  const knowledgeCount = (relationships.knowledge || []).length;
  const projectCount = (relationships.projects || []).length;
  const filedSummary = [
    homeZone ? String(homeZone.name || homeZone.id) : "Desk root",
    knowledgeCount ? `${knowledgeCount} Knowledge` : "",
    projectCount ? `${projectCount} Project${projectCount === 1 ? "" : "s"}` : "",
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <FoldGadget title={`Filed · ${filedSummary}`}>
        <div className="desk-pullout-filed">
          {zones.length > 0 && (
            <div className="desk-pullout-filed-axis">
              <span className="surface-eyebrow">Zone</span>
              <div className="desk-pullout-lineage">
                {zones.map((zone) => {
                  const members = zone.memberIds || [];
                  const inZone = members.includes(objectId) || members.includes(objectRef);
                  return (
                    <button
                      key={String(zone.id)}
                      type="button"
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
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          {knowledgeHomes.length > 0 && (
            <div className="desk-pullout-filed-axis">
              <span className="surface-eyebrow">Knowledge</span>
              <div className="desk-pullout-lineage">
                {knowledgeHomes.map((knowledge) => {
                  const active = (relationships.knowledge || []).some(
                    (row: any) => row.knowledge_id === knowledge.id,
                  );
                  return (
                    <button
                      key={knowledge.id}
                      type="button"
                      className={`desk-chip quiet${active ? " in-zone" : ""}`}
                      aria-pressed={active}
                      onClick={() => void toggleRelationship("knowledge", knowledge.id, active)}
                    >
                      {active ? <><span aria-hidden="true">✓</span>{" "}</> : "+ "}
                      {knowledge.name}
                    </button>
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
                      <button
                        type="button"
                        className={`desk-chip quiet${active ? " in-zone" : ""}`}
                        aria-label={`${active ? "Remove from" : "Assign to"} ${project.name} Project`}
                        aria-pressed={active}
                        onClick={() => void toggleRelationship("projects", project.id, active)}
                      >
                        {active ? <><span aria-hidden="true">✓</span>{" "}</> : "+ "}
                        {project.name}
                      </button>
                      <button
                        type="button"
                        className="desk-chip quiet"
                        aria-label={`Inspect ${project.name} Project`}
                        onClick={() => useDesk.getState().openToolInspector("project", String(project.id))}
                      >
                        Inspect
                      </button>
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
      </FoldGadget>
      {relationshipError ? (
        <FilingRefusal
          detail={relationshipError}
          onRetry={() => void refreshRelationships()}
        />
      ) : null}
    </>
  );
}
