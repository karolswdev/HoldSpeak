/** Decision pullout content (HS-117-15). */
import { useState } from "react";
import { apiRequest } from "../../lib/api";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { Material } from "../surface/Material";
import {
  SurfaceRow,
  SurfaceRows,
} from "../surface/Surface";
import { humanTime } from "../surface/format";
import { FoldGadget } from "../surface/gadgets";
import type { PulloutContentProps } from "./types";

export function DecisionPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "decision") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  const [editingDecision, setEditingDecision] = useState(false);
  const [decisionDraft, setDecisionDraft] = useState({
    context_markdown: "",
    decision_markdown: "",
    consequences_markdown: "",
  });

  const startDecisionEdit = () => {
    setDecisionDraft({
      context_markdown: String(ir.contextMarkdown || ""),
      decision_markdown: String(ir.decisionMarkdown || ""),
      consequences_markdown: String(ir.consequencesMarkdown || ""),
    });
    setEditingDecision(true);
  };
  const commitDecisionEdit = () => {
    void useDesk.getState().updatePrimitive("decision", o.id, decisionDraft);
    setEditingDecision(false);
  };
  const cycleDecisionStatus = () => {
    const cycle = ["proposed", "accepted", "superseded", "deprecated"];
    const current = String(ir.status || "proposed");
    const status = cycle[(cycle.indexOf(current) + 1) % cycle.length];
    void apiRequest(`/api/decisions/${encodeURIComponent(o.id)}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }).then(() => useDesk.getState().refresh());
  };

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section className="desk-decision-card">
          <div className="desk-pullout-facts">
            <button type="button" className="desk-chip quiet" onClick={cycleDecisionStatus}>
              {String(ir.status || "proposed")}
            </button>
            {Array.isArray(ir.deciders) && ir.deciders.length ? (
              <span>{ir.deciders.join(" · ")}</span>
            ) : null}
            {ir.decidedAt ? <span>{humanTime(String(ir.decidedAt))}</span> : null}
          </div>
          {editingDecision ? (
            <div className="desk-decision-editor">
              {(["context_markdown", "decision_markdown", "consequences_markdown"] as const).map((field) => (
                <label key={field} className="surface-eyebrow">
                  {field.replace("_markdown", "").replace("_", " ")}
                  <textarea
                    className="desk-pullout-editbox"
                    value={decisionDraft[field]}
                    rows={5}
                    onChange={(event) => setDecisionDraft({ ...decisionDraft, [field]: event.target.value })}
                  />
                </label>
              ))}
            </div>
          ) : (
            <>
              <section><h3>Context</h3><Material>{String(ir.contextMarkdown || "")}</Material></section>
              <section><h3>Decision</h3><Material>{String(ir.decisionMarkdown || "")}</Material></section>
              <section><h3>Consequences</h3><Material>{String(ir.consequencesMarkdown || "")}</Material></section>
            </>
          )}
          {Array.isArray(ir.alternatives) && ir.alternatives.length ? (
            <FoldGadget title="Alternatives considered">
              <SurfaceRows>{ir.alternatives.map((alternative: any, index: number) => (
                <SurfaceRow key={`${alternative.name}-${index}`} title={String(alternative.name || "Alternative")} detail={String(alternative.reason || "")} />
              ))}</SurfaceRows>
            </FoldGadget>
          ) : null}
          {(items.decision || []).filter((candidate) => candidate.supersededBy === o.id).map((candidate) => (
            <button key={candidate.id} type="button" className="desk-chip quiet" onClick={() => openPullout(String(candidate.id))}>
              Supersedes {String(candidate.title || candidate.id)}
            </button>
          ))}
          {ir.supersededBy ? (
            <button type="button" className="desk-chip quiet" onClick={() => openPullout(String(ir.supersededBy))}>
              Superseded by {String(ir.supersededBy)}
            </button>
          ) : null}
        </section>
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <footer className="desk-pullout-foot">
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </button>
        {editingDecision ? (
          <>
            <button type="button" className="desk-chip quiet" onClick={() => setEditingDecision(false)}>Cancel</button>
            <button type="button" className="desk-chip is-primary" onClick={commitDecisionEdit}>Done</button>
          </>
        ) : (
          <button type="button" className="desk-chip is-primary" onClick={startDecisionEdit}>Edit</button>
        )}
      </footer>
    </>
  );
}
