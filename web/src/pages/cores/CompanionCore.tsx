/* PARKED (PHILO-14 C4, 2026-10-07): the old Agents application. Agents
 * live in the Conductor drawer now (`desk/conductor/`); the Dock's Agents
 * entry became Conductor. This file stays whole: its route `/companion`
 * still opens it, but no Dock, Go list, shortcut, mark or link reaches it.
 * Its other rows live elsewhere: Delivery and PR receipts on the desk list
 * view (DeskListView), saved agents (recipes) as desk objects. */
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useEffect, useMemo, useState } from "react";
import { countLabel } from "../../desk/surface";
import { openCoderSession, openPersona } from "../../desk/shell";
import type { CoreProps, RecipesResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  SurfaceFacts,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../../desk/surface/Surface";
import { FoldGadget, LampGadget } from "../../desk/surface/gadgets";
import { presentValue } from "../../desk/surface/format";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { renderHeroSlot } from "./core-layout";
import { DeliveryListSection } from "../../desk/components/DeliveryListSection";
import { PrReceiptsSection } from "../../desk/components/PrReceiptsSection";
import { deliveryListRows, useDelivery } from "../../desk/delivery";
import { usePrReceipts } from "../../desk/prReceipts";
import {
  liveAgentSessions,
  useAgentFlights,
  useAgentFlightsLive,
  type CoderSessionRow,
} from "../../desk/agentFlights";

const WINGS = [
  { id: "roster", label: "Roster" },
  { id: "delivery", label: "Delivery" },
];

export function CompanionCore({ hero }: CoreProps) {
  const [chosenView, setView] = useState("roster");
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
  const wings = hasDelivery ? WINGS : WINGS.filter((wing) => wing.id !== "delivery");
  const view = hasDelivery ? chosenView : "roster";
  const [doorOpen, setDoorOpen] = useState(false);
  const [toggled, setToggled] = useState<Record<string, boolean>>({});
  useWindowWings(
    <SurfaceWings
      wings={wings}
      active={view}
      onChange={setView}
      door="How it connects"
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((v) => !v)}
    />,
    [view, doorOpen, hasDelivery],
  );
  const recipes = useResource<RecipesResponse>("/api/recipes", {});
  // Conductor F2 (K4c): every live session, from `/api/coders/sessions`
  // (the agents store). `/api/coders/status` lists only sessions that set
  // `awaiting_response` in the last 30 minutes, so this roster read
  // "No sessions" while agents worked. The store re-reads on the
  // `scope:"coder"` frame (Conductor K3); the last read stays.
  useAgentFlightsLive();
  const sessionRows = useAgentFlights((s) => s.sessions);
  // Inventory 2026-10-03 (defect 9): the roster dropped every seeded agent
  // (Chase, Desk, Draft, ...: kind='mode') while the Floor showed them as
  // agents, so the roster read "New Agent" rows only. The roster reads the
  // same set the Floor does (desk/api.ts: every recipe that is not deleted).
  const recipeRows = asRows(recipes.data, ["recipes"]).filter((row) => !row.deleted);
  const allSessions = useMemo(() => liveAgentSessions(sessionRows), [sessionRows]);
  const isBlocked = (row: CoderSessionRow) => row.blocked;
  // Blocked-first is the ordering contract (pinned by test).
  const blocked = useMemo(() => allSessions.filter(isBlocked), [allSessions]);
  const running = useMemo(
    () => allSessions.filter((row) => !isBlocked(row)),
    [allSessions],
  );
  const sessionRow = (row: CoderSessionRow, index: number, tone: "blocked" | "run") => {
    const session = (row.raw.session as Record<string, unknown> | undefined) ?? row.raw;
    const key = row.key;
    // A blocked row opens in place by default: its question IS the board.
    const open = toggled[key] ?? tone === "blocked";
    return (
      <SurfaceLedgerRow
        key={rowId(session, index)}
        primary={row.name}
        open={open}
        onToggle={() => setToggled((t) => ({ ...t, [key]: !open }))}
        cells={
          <>
            <span className="surface-ledger-cell">
              {presentValue(session.summary ?? session.question)}
            </span>
            <span className="surface-ledger-cell">
              <LampGadget
                label={tone === "blocked" ? "BLOCKED" : "RUN"}
                on
                tone={tone === "blocked" ? "warn" : "ok"}
              />
            </span>
          </>
        }
      >
        {tone === "blocked" && session.question ? (
          <FoldGadget title="RAW · QUESTION">
            <pre className="desk-pullout-md desk-session-question">
              {String(session.question)}
            </pre>
          </FoldGadget>
        ) : null}
        <div className="surface-row-verbs">
          <Button
            dense
            variant={tone === "blocked" ? "primary" : "ghost"}
            onClick={() => openCoderSession(key)}
          >
            {tone === "blocked" ? "Answer" : "Watch"}
          </Button>
        </div>
      </SurfaceLedgerRow>
    );
  };
  const rosterFace = (
    <>
      {doorOpen ? (
        <SurfaceFacts
          value={{
            probe: "health before controls",
            token: "in memory, never in a payload",
            relay: "no hosted relay",
            autonomous_send: "never",
          }}
        />
      ) : null}
      <SurfaceLedger
        cols="crew"
        count={
          // A count of zero is not said (UX-CANON A8): the head read
          // "CREW · SESSIONS · BLOCKED" with no sessions.
          [
            recipeRows.length ? countLabel("CREW", recipeRows.length) : "",
            allSessions.length ? countLabel("SESSIONS", allSessions.length) : "",
            blocked.length ? countLabel("BLOCKED", blocked.length) : "",
          ].filter(Boolean).join(" · ")
        }
      >
        <h4 className="surface-ledger-band">Sessions</h4>
        {allSessions.length ? (
          <ul className="surface-ledger-rows">
            {blocked.map((row, index) => sessionRow(row, index, "blocked"))}
            {running.map((row, index) => sessionRow(row, index, "run"))}
          </ul>
        ) : (
          <SurfaceState empty emptyLabel="No sessions" />
        )}
        <h4 className="surface-ledger-band">Crew</h4>
        {recipes.error ? (
          <SurfaceState
            error={recipes.error}
            onRetry={() => void recipes.reload()}
          />
        ) : recipeRows.length ? (
          <ul className="surface-ledger-rows">
            {recipeRows.map((recipe, index) => (
              <SurfaceLedgerRow
                key={rowId(recipe, index)}
                primary={String(recipe.name ?? "Agent")}
                onToggle={() => openPersona(String(recipe.id))}
                cells={
                  <>
                    <span className="surface-ledger-cell">
                      {presentValue(recipe.role)}
                    </span>
                    <span className="surface-ledger-cell">
                      <LampGadget label="OK" on tone="ok" />
                    </span>
                  </>
                }
              />
            ))}
          </ul>
        ) : (
          <SurfaceState
            loading={recipes.loading}
            empty={!recipes.loading}
            emptyLabel="No agents"
          />
        )}
      </SurfaceLedger>
    </>
  );
  const deliveryFace = (
    <>
      <DeliveryListSection />
      <PrReceiptsSection />
    </>
  );
  return (
    <>
      {renderHeroSlot(hero, null)}
      {view === "delivery" ? deliveryFace : rosterFace}
      <SurfaceFooter />
    </>
  );
}
