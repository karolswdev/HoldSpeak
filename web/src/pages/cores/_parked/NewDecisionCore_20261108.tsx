/* The owner, 2026-10-25: "go -> new decision -> opens up a cluster fuck of a
 * window." New Decision now opens a small window of its own (it was a
 * popover in the ⌘K palette). Window grammar (2026-10-24):
 *
 *   title bar   ◈ New decision
 *   body        the decision's picture | label/control grid
 *               Decision  [title well + mic]   (focused on open; Enter creates)
 *               Why       [pad + mic]          (optional)
 *               About     [▣ Project]          (only with a Project in front)
 *   status bar  Cancel · Create (the one primary, off until a title)
 *
 * PHILO-13-08 (B3): a decision is named before it is persisted. Cancel,
 * Escape and the title bar's close write nothing. Create closes this window
 * and the record opens in the Decisions window, selected (dataSlice
 * createNow). The unfinished title and Why return after a reload
 * (NEW_DECISION_DRAFT). */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../../desk/store";
import { PadGadget, StringGadget } from "../../desk/surface/gadgets";
import { StatusBar, ToolGlyph } from "../../desk/surface/kit";
import { FootSlotContext } from "../../desk/surface/foot";
import { spriteUrl } from "../../desk/sprites";
import { forgetDraft, keepDraft, keptDraft } from "../../desk/deskMemory";
import { NEW_DECISION_DRAFT } from "../../desk/newDecision";
import type { CoreProps } from "./core-types";
import "./newDecision.css";

export type NewDecisionAbout = { id: string; name: string };

/** The window's face, with no store: the core feeds it, and the Components
 *  Window group shows it with fixture words (`inline` keeps its status bar
 *  inside the specimen instead of the window frame's foot). */
export function NewDecisionForm({
  title,
  why,
  about,
  onTitle,
  onWhy,
  onCreate,
  onCancel,
  autoFocus = false,
  inline = false,
}: {
  title: string;
  why: string;
  about?: NewDecisionAbout | null;
  onTitle: (next: string) => void;
  onWhy: (next: string) => void;
  onCreate: () => void;
  onCancel: () => void;
  autoFocus?: boolean;
  inline?: boolean;
}) {
  const named = Boolean(title.trim());
  const bar = (
    <StatusBar
      className="new-decision-status"
      data-testid="new-decision-status"
      items={[]}
      verbs={<>
        <Button dense variant="ghost" onClick={onCancel} data-testid="new-decision-cancel">Cancel</Button>
        <Button dense variant="primary" disabled={!named} onClick={onCreate} data-testid="palette-name-save">
          <ToolGlyph kind="done" />Create
        </Button>
      </>}
    />
  );
  return (
    <div
      className="new-decision"
      data-testid="new-decision"
      role="group"
      aria-label="New decision"
      onKeyDown={(event) => {
        if (event.key !== "Escape") return;
        event.preventDefault();
        event.stopPropagation();
        onCancel();
      }}
    >
      <img className="new-decision-picture" src={spriteUrl("decision", "new")} alt="" width={64} height={64} draggable={false} />
      <div className="new-decision-grid">
        <label className="new-decision-row">
          <span className="new-decision-label">Decision</span>
          <span className="new-decision-control">
            <StringGadget
              label="Decision title"
              value={title}
              autoFocus={autoFocus}
              onChange={onTitle}
              micLabel="Speak the decision"
              inputProps={{ "data-testid": "palette-name" } as Record<string, string>}
              onKeyDown={(event) => {
                if (event.key !== "Enter") return;
                event.preventDefault();
                if (named) onCreate();
              }}
            />
          </span>
        </label>
        <label className="new-decision-row">
          <span className="new-decision-label">Why</span>
          <span className="new-decision-control">
            <PadGadget
              label="Why"
              value={why}
              rows={3}
              placeholder="Optional"
              micLabel="Speak why"
              onChange={onWhy}
              inputProps={{ "data-testid": "decision-why" } as Record<string, string>}
            />
          </span>
        </label>
        {about ? (
          <div className="new-decision-row">
            <span className="new-decision-label">About</span>
            <span className="new-decision-control">
              <span className="new-decision-about" data-testid="decision-about-chip">
                <img src={spriteUrl("project", about.id, "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
                {about.name}
              </span>
            </span>
          </div>
        ) : null}
      </div>
      {inline ? <FootSlotContext.Provider value={null}>{bar}</FootSlotContext.Provider> : bar}
    </div>
  );
}

/** The hosted window: the scope is the Project in front (`project:<id>`). */
export function NewDecisionCore({ scope, scopeLabel }: CoreProps) {
  const projects = useDesk((state) => state.projects);
  const projectId = scope?.startsWith("project:") ? scope.slice("project:".length) : "";
  const about: NewDecisionAbout | null = projectId
    ? { id: projectId, name: scopeLabel || projects.find((item) => item.id === projectId)?.name || "Project" }
    : null;
  const [title, setTitleState] = useState(() => keptDraft(NEW_DECISION_DRAFT.title) ?? "");
  const [why, setWhyState] = useState(() => keptDraft(NEW_DECISION_DRAFT.why) ?? "");
  const setTitle = (next: string) => { keepDraft(NEW_DECISION_DRAFT.title, next); setTitleState(next); };
  const setWhy = (next: string) => { keepDraft(NEW_DECISION_DRAFT.why, next); setWhyState(next); };
  const close = () => {
    forgetDraft(NEW_DECISION_DRAFT.title);
    forgetDraft(NEW_DECISION_DRAFT.why);
    useDesk.getState().closeSurfaceWindow("new-decision");
  };
  const create = () => {
    const name = title.trim();
    if (!name) return;
    const reason = why.trim();
    close();
    void useDesk.getState().createPrimitive("decision", {
      title: name,
      ...(reason ? { why: reason } : {}),
      ...(about ? { project_id: about.id, project_name: about.name } : {}),
    });
  };
  return (
    <NewDecisionForm
      title={title}
      why={why}
      about={about}
      onTitle={setTitle}
      onWhy={setWhy}
      onCreate={create}
      onCancel={close}
      autoFocus
    />
  );
}
