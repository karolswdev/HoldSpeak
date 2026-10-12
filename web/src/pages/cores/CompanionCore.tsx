/* PARKED (PHILO-14 C4, 2026-10-07): the old Agents application. Agents
 * live in the Conductor drawer now (`desk/conductor/`); the Dock's Agents
 * entry became Conductor. This file stays whole: its route `/companion`
 * still opens it, but no Dock, Go list, shortcut, mark or link reaches it.
 *
 * PHILO-17 THE REFIT: the window reads like Today. Canon words: agents are
 * the saved agents he authors; coders are the live coding sessions (they
 * live in the Conductor). The window leads with a coder that asks (its
 * question and Answer, one press), then the agents as quiet rows, and
 * Delivery as its own wing in plain words. */
import "./companion.css";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useEffect, useMemo, useState } from "react";
import { openCoderSession, openPersona } from "../../desk/shell";
import type { CoreProps, RecipesResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { asRows, rowId, useResource } from "../pageSupport";
import { SurfaceState } from "../../desk/surface/Surface";
import { objectSprite } from "../../desk/surface/objects/kinds";
import { AgentWords } from "../../desk/components/AgentWords";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { renderHeroSlot } from "./core-layout";
import { PrReceiptsSection } from "../../desk/components/PrReceiptsSection";
import { deliveryListRows, useDelivery, type DeliveryListRow } from "../../desk/delivery";
import { useDeliveryDossier } from "../../desk/deliveryDossier";
import { targetHandle, useDeliveryFactory } from "../../desk/deliveryFactory";
import { useDeliveryTerminal } from "../../desk/deliveryTerminal";
import { usePrReceipts } from "../../desk/prReceipts";
import { useConductor } from "../../desk/conductor/store";
import { AGENT_NAME, type AgentId } from "../../desk/firstrun/agentsStep";
import { useDesk } from "../../desk/store";
import {
  liveAgentSessions,
  useAgentFlights,
  useAgentFlightsLive,
  type AgentFlight,
  type CoderSessionRow,
} from "../../desk/agentFlights";

const WINGS = [
  { id: "agents", label: "Agents" },
  { id: "delivery", label: "Delivery" },
];

/** The wings are drawn after this long even when a read is still out. */
const WINGS_READS_CAP_MS = 8000; // the Room's cap (roomReads.ts ROOM_READS_CAP_MS)

/** `working` → `Working`; a wire state in plain words. */
function stateWord(state: string): string {
  const word = state.replace(/[_-]+/g, " ").trim();
  return word ? word.charAt(0).toUpperCase() + word.slice(1) : "";
}

/** The tone of a delivery state's pill. */
function stateTone(state: string): "ok" | "warn" | "danger" | "info" | "idle" {
  const s = state.toLowerCase();
  if (/(done|merged|closed|complete)/.test(s)) return "ok";
  if (/(fail|error|blocked)/.test(s)) return "danger";
  if (/(wait|review|held|ask)/.test(s)) return "warn";
  if (/(work|run|progress|start)/.test(s)) return "info";
  return "idle";
}

/** A Delivery row in plain words: the item's title (the coder's launch
 *  names it when the row only has an id), the state as a pill. */
export function deliveryRowWords(row: DeliveryListRow, flights: readonly AgentFlight[]): { title: string; state: string; meta: string } {
  if (row.ref.type === "story") {
    return { title: row.detail || row.label, state: "", meta: row.label };
  }
  const id = row.label.replace(/^action-/, "");
  const flight = flights.find((f) => f.originRef === `action:${id}` || f.id === id);
  const state = row.detail.split(" · ")[0] ?? "";
  return {
    title: flight?.title || row.label,
    state,
    meta: flight ? AGENT_NAME[flight.agent as AgentId] ?? flight.agent : "Coder",
  };
}

function DeliveryWork() {
  const sources = useDelivery((s) => s.sources);
  const attempts = useDelivery((s) => s.attempts);
  const targets = useDeliveryFactory((s) => s.targets);
  const flights = useAgentFlights((s) => s.flights);
  const rows = deliveryListRows(sources, attempts);
  if (!rows.length) return null;
  const openRow = (row: DeliveryListRow) => {
    const ref = row.ref;
    if (ref.type === "story") {
      void useDeliveryDossier.getState().openStory(ref.project, ref.storyId, ref.sourceId);
      return;
    }
    const target = ref.targetId ? targets.find((t) => t.targetId === ref.targetId) : null;
    if (target) useDeliveryTerminal.getState().open(targetHandle(target));
  };
  return (
    <section className="ag-section" aria-label="Delivery work" data-testid="agents-delivery">
      <h3 className="ag-cap">WORK</h3>
      <ul className="ag-well">
        {rows.map((row) => {
          const words = deliveryRowWords(row, flights);
          const openable = row.ref.type === "story" || Boolean(row.ref.targetId && targets.some((t) => t.targetId === (row.ref as { targetId?: string }).targetId));
          return (
            <li key={row.key} className="ag-row" data-testid="agents-delivery-row">
              <div className="ag-row-text">
                <span className="ag-row-name">{words.title}</span>
                <span className="ag-row-meta">
                  {words.state ? <span className="kit-pill" data-tone={stateTone(words.state) === "idle" ? undefined : stateTone(words.state)} data-dot="">{stateWord(words.state)}</span> : null}
                  <span>{words.meta}</span>
                </span>
              </div>
              {openable ? (
                <Button dense variant="ghost" onClick={() => openRow(row)}>
                  Open
                </Button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function CompanionCore({ hero }: CoreProps) {
  const [chosenView, setView] = useState("agents");
  // The Delivery wing shows repository work and pull request receipts. With
  // neither, both sections draw nothing and the wing was a blank window
  // (inventory 2026-10-03). An empty wing is withheld.
  const deliverySources = useDelivery((s) => s.sources);
  const deliveryAttempts = useDelivery((s) => s.attempts);
  const prSources = usePrReceipts((s) => s.sources);
  useEffect(() => {
    void usePrReceipts.getState().load();
  }, []);
  const hasDelivery =
    deliveryListRows(deliverySources, deliveryAttempts).length > 0 ||
    prSources.some((source) => source.prs !== null || source.status !== "unavailable");
  const view = hasDelivery ? chosenView : "agents";
  // PHILO-17 (the desk sweep): the wings are drawn once the reads that
  // decide the Delivery wing have ended (or at the cap); a Delivery wing
  // that arrived late moved the window's words 44 px (UX-CANON D).
  const prLoaded = usePrReceipts((s) => s.loaded);
  const deliveryRead = useDelivery((s) => s.updatedAt !== null || s.error !== "");
  // The wings wait on the delivery read, so this face starts it when nothing
  // has read it yet (the desk's poller may not run here; single-flight).
  useEffect(() => {
    const st = useDelivery.getState();
    if (st.updatedAt === null && st.error === "") void st.refresh();
  }, []);
  const [wingsCapped, setWingsCapped] = useState(false);
  useEffect(() => {
    const timer = window.setTimeout(() => setWingsCapped(true), WINGS_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, []);
  const wingsKnown = wingsCapped || (prLoaded && deliveryRead);
  // One wing is no choice: the strip shows only with Delivery.
  useWindowWings(
    !wingsKnown || !hasDelivery ? null : <SurfaceWings wings={WINGS} active={view} onChange={setView} />,
    [view, hasDelivery, wingsKnown],
  );
  const recipes = useResource<RecipesResponse>("/api/recipes", {});
  // Conductor F2 (K4c): every live session, from `/api/coders/sessions`
  // (the agents store). The store re-reads on the `scope:"coder"` frame
  // (Conductor K3); the last read stays.
  useAgentFlightsLive();
  const sessionRows = useAgentFlights((s) => s.sessions);
  // Inventory 2026-10-03 (defect 9): the list reads the same set the Floor
  // does (desk/api.ts: every recipe that is not deleted).
  const recipeRows = asRows(recipes.data, ["recipes"]).filter((row) => !row.deleted);
  const allSessions = useMemo(() => liveAgentSessions(sessionRows), [sessionRows]);
  // Blocked-first is the ordering contract (pinned by test).
  const blocked = useMemo(() => allSessions.filter((row) => row.blocked), [allSessions]);
  const running = allSessions.length - blocked.length;
  const openConductor = () => useConductor.getState().openWindow();
  const newAgent = () => void useDesk.getState().createPrimitive("recipe");

  const askRow = (row: CoderSessionRow, index: number) => {
    const session = (row.raw.session as Record<string, unknown> | undefined) ?? row.raw;
    const question = session.question ?? session.summary;
    return (
      <li key={rowId(session, index)} className="ag-ask" data-testid="agents-ask">
        <div className="ag-row-text">
          <span className="ag-row-name">{row.name}</span>
          <span className="ag-row-meta">
            <span className="kit-pill" data-tone="warn" data-dot="" data-live="">Asks you</span>
            <span>{AGENT_NAME[row.agent as AgentId] ?? row.agent}</span>
          </span>
          {typeof question === "string" && question.trim() ? <AgentWords compact text={question} className="ag-ask-q" /> : null}
        </div>
        <Button dense variant={index === 0 ? "primary" : "secondary"} onClick={() => openCoderSession(row.key, { answer: true })}>
          Answer
        </Button>
      </li>
    );
  };

  const agentsFace = (
    <div className="ag" data-testid="agents-face">
      <div className="ag-head">
        <h2 className="ag-title" data-testid="agents-head">
          {recipeRows.length ? `${recipeRows.length} ${recipeRows.length === 1 ? "agent" : "agents"}` : "Agents"}
        </h2>
        <span className="ag-strip">
          {blocked.length ? <span><b>{blocked.length}</b> {blocked.length === 1 ? "coder asks" : "coders ask"}</span> : null}
          {running ? <span><b>{running}</b> at work</span> : null}
        </span>
        <span className="ag-head-sp" />
        {allSessions.length ? (
          <Button dense variant="ghost" onClick={openConductor} data-testid="agents-open-conductor">
            Conductor
          </Button>
        ) : null}
        <Button dense variant={blocked.length ? "secondary" : "primary"} onClick={newAgent} data-testid="agents-new">
          New agent
        </Button>
      </div>
      {blocked.length ? (
        <section className="ag-section" aria-label="Coders that ask">
          <h3 className="ag-cap">NEEDS YOU</h3>
          <ul className="ag-well ag-asks">{blocked.map(askRow)}</ul>
        </section>
      ) : null}
      <section className="ag-section" aria-label="Agents">
        {recipes.error ? (
          <SurfaceState
            error={recipes.error}
            onRetry={() => void recipes.reload()}
          />
        ) : recipeRows.length ? (
          <ul className="ag-well" data-testid="agents-list">
            {recipeRows.map((recipe, index) => {
              const id = String(recipe.id ?? "");
              const role = typeof recipe.role === "string" ? recipe.role : "";
              return (
                <li key={rowId(recipe, index)} className="ag-row" data-testid="agents-row">
                  <span className="ag-row-sprite" aria-hidden="true">
                    <img src={objectSprite("recipe", id, "rest", 32)} alt="" draggable={false} />
                  </span>
                  <div className="ag-row-text">
                    <Button variant="chrome" className="ag-row-title" onClick={() => openPersona(id)}>
                      {String(recipe.name ?? "Agent")}
                    </Button>
                    {role ? <span className="ag-row-meta">{role}</span> : null}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <SurfaceState
            loading={recipes.loading}
            empty={!recipes.loading}
            emptyLabel="No agents yet"
          />
        )}
      </section>
    </div>
  );
  const deliveryFace = (
    <div className="ag">
      <DeliveryWork />
      <PrReceiptsSection />
    </div>
  );
  return (
    <>
      {renderHeroSlot(hero, null)}
      {view === "delivery" ? deliveryFace : agentsFace}
      <SurfaceFooter />
    </>
  );
}
