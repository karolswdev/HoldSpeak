// HS-95-08 — the ONE roster of agents and coder sessions (reconciled
// surfaces — no duplicate chat/list). HS-100-09 — Agents (thesis §1.3):
// the application opens on WHO NEEDS YOU — blocked sessions first with
// their question and an Answer verb one step from the pane.
// HS-111-04 — the crew board (audit §3.1): ONE SurfaceLedger, two
// bands — SESSIONS (blocked-first, lamp + state token, the question as
// an open-in-place aerogel receipt) and CREW (lamp, mono handle, role
// token). Wings collapse to Roster | Delivery; the connection facts
// are tokens behind the gear door, never a prose accordion.
import { useMemo, useState } from "react";
import { openCoderSession, openPersona } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import { Button } from "../../components/signal/Signal";
import { asRows, rowId, useResource } from "../pageSupport";
import { type JsonRecord } from "../../lib/api";
import {
  SurfaceFacts,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../../desk/surface/Surface";
import { LampGadget } from "../../desk/surface/gadgets";
import { presentValue } from "../../desk/surface/format";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
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
  const recipes = useResource<JsonRecord>("/api/recipes", {});
  const coders = useResource<JsonRecord>("/api/coders/status", {});
  const recipeRows = asRows(recipes.data, ["recipes"]).filter(
    (row) => !row.deleted,
  );
  const allSessions = asRows(
    (coders.data.agent as JsonRecord | undefined)?.sessions,
    ["items", "sessions"],
  );
  const isBlocked = (row: JsonRecord) =>
    Boolean(
      (row.session as JsonRecord | undefined)?.awaiting_response ??
        row.awaiting_response ??
        row.state === "waiting",
    );
  // Blocked-first is the ordering contract (pinned by test).
  const blocked = useMemo(() => allSessions.filter(isBlocked), [allSessions]);
  const running = useMemo(
    () => allSessions.filter((row) => !isBlocked(row)),
    [allSessions],
  );
  const sessionKey = (row: JsonRecord, session: JsonRecord) =>
    String(
      row.key ??
        session.key ??
        `${String(session.agent ?? "claude")}:${String(session.session_id ?? "")}`,
    );
  const sessionRow = (row: JsonRecord, index: number, tone: "blocked" | "run") => {
    const session = (row.session as JsonRecord | undefined) ?? row;
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
          <pre className="desk-pullout-md desk-session-question">
            {String(session.question)}
          </pre>
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
        count={`CREW ${recipeRows.length} · SESSIONS ${allSessions.length} · BLOCKED ${blocked.length}`}
      >
        <h4 className="surface-ledger-band">Sessions</h4>
        {allSessions.length ? (
          <ul className="surface-ledger-rows">
            {blocked.map((row, index) => sessionRow(row, index, "blocked"))}
            {running.map((row, index) => sessionRow(row, index, "run"))}
          </ul>
        ) : (
          <div className="surface-ledger-empty">
            NO SESSIONS · NO ONE WAITING
          </div>
        )}
        <h4 className="surface-ledger-band">Crew</h4>
        {recipes.error ? (
          <div className="surface-ledger-empty">
            {recipes.error}{" "}
            <Button dense variant="ghost" onClick={() => void recipes.reload()}>
              Try again
            </Button>
          </div>
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
          <div className="surface-ledger-empty">
            {recipes.loading ? "READING" : "NO AGENTS"}
          </div>
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
      {hero ? hero(null) : null}
      {view === "delivery" ? deliveryFace : rosterFace}
    </>
  );
}
