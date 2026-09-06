import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useMemo, useState } from "react";
import { countLabel } from "../../desk/surface";
import { openCoderSession, openPersona } from "../../desk/shell";
import type {
  CoreProps,
  RecipesResponse,
  CodersStatusResponse,
} from "./core-types";
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

const WINGS = [
  { id: "roster", label: "Roster" },
  { id: "delivery", label: "Delivery" },
];

export function CompanionCore({ hero }: CoreProps) {
  const [view, setView] = useState("roster");
  const [doorOpen, setDoorOpen] = useState(false);
  const [toggled, setToggled] = useState<Record<string, boolean>>({});
  useWindowWings(
    <SurfaceWings
      wings={WINGS}
      active={view}
      onChange={setView}
      door="How it connects"
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((v) => !v)}
    />,
    [view, doorOpen],
  );
  const recipes = useResource<RecipesResponse>("/api/recipes", {});
  const coders = useResource<CodersStatusResponse>("/api/coders/status", {});
  const recipeRows = asRows(recipes.data, ["recipes"]).filter(
    // Thread modes (kind='mode', HS-153-01) are practices, not crew.
    (row) => !row.deleted && (row as Record<string, unknown>).kind !== "mode",
  );
  const allSessions = asRows(
    coders.data.agent?.sessions,
    ["items", "sessions"],
  );
  const isBlocked = (row: Record<string, unknown>) =>
    Boolean(
      (row.session as Record<string, unknown> | undefined)?.awaiting_response ??
        row.awaiting_response ??
        row.state === "waiting",
    );
  // Blocked-first is the ordering contract (pinned by test).
  const blocked = useMemo(() => allSessions.filter(isBlocked), [allSessions]);
  const running = useMemo(
    () => allSessions.filter((row) => !isBlocked(row)),
    [allSessions],
  );
  const sessionKey = (row: Record<string, unknown>, session: Record<string, unknown>) =>
    String(
      row.key ??
        session.key ??
        `${String(session.agent ?? "claude")}:${String(session.session_id ?? "")}`,
    );
  const sessionRow = (row: Record<string, unknown>, index: number, tone: "blocked" | "run") => {
    const session = (row.session as Record<string, unknown> | undefined) ?? row;
    const key = sessionKey(row, session);
    // A blocked row opens in place by default: its question IS the board.
    const open = toggled[key] ?? tone === "blocked";
    return (
      <SurfaceLedgerRow
        key={rowId(session, index)}
        primary={String(
          session.project ?? session.cwd ?? session.session_id ?? "session",
        )}
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
        count={[countLabel("CREW", recipeRows.length), countLabel("SESSIONS", allSessions.length), countLabel("BLOCKED", blocked.length)].filter(Boolean).join(" · ")}
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
