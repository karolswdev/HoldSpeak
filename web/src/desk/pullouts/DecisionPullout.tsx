import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Decision pullout content (HS-117-15). */
import { useState } from "react";
import { apiRequest } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
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
import { FoldGadget, PadGadget } from "../surface/gadgets";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";

export function DecisionPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "decision") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const decisionContent = [
    `# Context\n\n${String(ir.contextMarkdown || "")}`,
    `# Decision\n\n${String(ir.decisionMarkdown || "")}`,
    `# Consequences\n\n${String(ir.consequencesMarkdown || "")}`,
  ].join("\n\n");

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
            <Button variant="ghost" dense onClick={cycleDecisionStatus}>
              {String(ir.status || "proposed")} ↻
            </Button>
            {Array.isArray(ir.deciders) && ir.deciders.length ? (
              <span>{ir.deciders.join(" · ")}</span>
            ) : null}
            {ir.decidedAt ? <span>{humanTime(String(ir.decidedAt))}</span> : null}
          </div>
          {editingDecision ? (
            <div className="desk-decision-editor">
              {([
                ["context_markdown", "Context"],
                ["decision_markdown", "Decision"],
                ["consequences_markdown", "Consequences"],
              ] as const).map(([field, label]) => (
                <label key={field} className="surface-eyebrow">
                  {label}
                  <PadGadget
                    label={label}
                    value={decisionDraft[field]}
                    rows={5}
                    onChange={(value) => setDecisionDraft({ ...decisionDraft, [field]: value })}
                  />
                </label>
              ))}
            </div>
          ) : (
            <>
              <section><h3>Decision context</h3><Material>{String(ir.contextMarkdown || "")}</Material></section>
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
            <Button key={candidate.id} variant="ghost" dense onClick={() => openPullout(String(candidate.id))}>
              Supersedes {String(candidate.title || candidate.id)}
            </Button>
          ))}
          {ir.supersededBy ? (
            <Button variant="ghost" dense onClick={() => openPullout(String(ir.supersededBy))}>
              Superseded by {String(ir.supersededBy)}
            </Button>
          ) : null}
        </section>
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter receipt={copyReceipt} verbs={<>
        <Button
          variant="ghost"
          dense
          onClick={() => void copy(decisionContent)}
        >
          Copy
        </Button>
        <Button
          variant="ghost"
          dense
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </Button>
        {editingDecision ? (
          <>
            <Button variant="ghost" dense onClick={() => setEditingDecision(false)}>Cancel</Button>
            <Button variant="primary" dense onClick={commitDecisionEdit}>Done</Button>
          </>
        ) : (
          <Button variant="primary" dense onClick={startDecisionEdit}>Edit</Button>
        )} </>} />
    </>
  );
}
