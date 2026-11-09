/* New decision as the plate (the native Decisions app, 2026-11-08): the
 * composer is the one raised thing of the Decisions window when he presses
 * New decision, never a second window. The decision's words (focused,
 * Enter creates), Why (optional), About (the Project in front), then
 * Create, the one primary (off until a title), and Cancel.
 *
 * PHILO-13-08 (B3): a decision is named before it is persisted. Cancel and
 * Escape write nothing. The store and the Components reference feed it;
 * it holds no state of its own. */
import { Button } from "../../components/signal/Signal";
import { PadGadget, StringGadget } from "../surface/gadgets";
import { ToolGlyph } from "../surface/kit";
import { spriteUrl } from "../sprites";
import "./decisions.css";

export type NewDecisionAbout = { id: string; name: string };

export function DecisionComposer({ title, why, about, onTitle, onWhy, onCreate, onCancel, autoFocus = false }: {
  title: string;
  why: string;
  about?: NewDecisionAbout | null;
  onTitle(next: string): void;
  onWhy(next: string): void;
  onCreate(): void;
  onCancel(): void;
  autoFocus?: boolean;
}) {
  const named = Boolean(title.trim());
  return (
    <section
      className="decisions-plate decisions-composer"
      data-tone="brass"
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
      <span className="decisions-plate-eyebrow">New decision</span>
      <StringGadget
        label="Decision title"
        value={title}
        autoFocus={autoFocus}
        onChange={onTitle}
        placeholder="What you decided"
        micLabel="Speak the decision"
        inputProps={{ "data-testid": "palette-name" } as Record<string, string>}
        onKeyDown={(event) => {
          if (event.key !== "Enter") return;
          event.preventDefault();
          if (named) onCreate();
        }}
      />
      <PadGadget
        label="Why"
        value={why}
        rows={3}
        placeholder="Why (optional)"
        micLabel="Speak why"
        onChange={onWhy}
        inputProps={{ "data-testid": "decision-why" } as Record<string, string>}
      />
      {about ? (
        <span className="decisions-composer-about" data-testid="decision-about-chip">
          <img src={spriteUrl("project", about.id, "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
          {about.name}
        </span>
      ) : null}
      <div className="decisions-plate-verbs">
        <Button variant="primary" disabled={!named} onClick={onCreate} data-testid="palette-name-save">
          <ToolGlyph kind="done" />Create
        </Button>
        <Button variant="ghost" onClick={onCancel} data-testid="new-decision-cancel">Cancel</Button>
      </div>
    </section>
  );
}
