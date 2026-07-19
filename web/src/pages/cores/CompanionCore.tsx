// HS-95-08 — the ONE roster of agents and coder sessions (reconciled
// surfaces — no duplicate chat/list). HS-98-07 — surface kit native.
// HS-100-09 — Agents (thesis §1.3): the application opens on WHO NEEDS
// YOU — blocked sessions first with their question and an Answer verb
// one step from the pane; then running. Delivery and Chat are the
// wings. "Personas" leaves the glass; the canon word is agents.
import { useMemo, useState } from "react";
import { openCoderSession, openPersona } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import { Button, Disclosure, StatusPill } from "../../components/signal/Signal";
import { asRows, rowId, useResource } from "../pageSupport";
import { type JsonRecord } from "../../lib/api";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { presentValue } from "../../desk/surface/format";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { DeliveryListSection } from "../../desk/components/DeliveryListSection";

const WINGS = [
  { id: "sessions", label: "Sessions" },
  { id: "delivery", label: "Delivery" },
  { id: "chat", label: "Chat" },
];

export function CompanionCore({ hero }: CoreProps) {
  const [view, setView] = useState("sessions");
  useWindowWings(
    <SurfaceWings wings={WINGS} active={view} onChange={setView} />,
    [view],
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
    return (
      <SurfaceRow
        key={rowId(session, index)}
        title={String(
          session.project ?? session.cwd ?? session.session_id ?? "Coder session",
        )}
        detail={
          presentValue(session.summary ?? session.question) ||
          (tone === "blocked" ? "Awaiting your response" : undefined)
        }
        meta={
          tone === "blocked" ? (
            <StatusPill tone="warning">Awaiting response</StatusPill>
          ) : (
            <StatusPill tone="success">Running</StatusPill>
          )
        }
        onOpen={() => openCoderSession(sessionKey(row, session))}
        verbs={
          <Button
            dense
            variant={tone === "blocked" ? "primary" : "ghost"}
            onClick={() => openCoderSession(sessionKey(row, session))}
          >
            {tone === "blocked" ? "Answer" : "Watch"}
          </Button>
        }
      />
    );
  };
  const sessionsFace = (
    <>
      <SurfaceSection label="Blocked — needs your answer">
        {blocked.length ? (
          <SurfaceRows>
            {blocked.map((row, index) => sessionRow(row, index, "blocked"))}
          </SurfaceRows>
        ) : (
          <SurfaceState empty emptyLabel="No one is waiting on you" emptyGlyph="✓" />
        )}
      </SurfaceSection>
      {running.length ? (
        <SurfaceSection label="Running">
          <SurfaceRows>
            {running.map((row, index) => sessionRow(row, index, "run"))}
          </SurfaceRows>
        </SurfaceSection>
      ) : null}
      <Disclosure title="How it connects">
        <ol>
          <li>Point the companion at your hub over your own network.</li>
          <li>
            It probes health and runtime readiness before offering controls.
          </li>
          <li>
            The session token is held in memory and joined to requests, never
            returned in a payload.
          </li>
          <li>There is no hosted relay and no autonomous send.</li>
        </ol>
      </Disclosure>
    </>
  );
  const chatFace = (
    <SurfaceSection label="Agents">
      <SurfaceState
        loading={recipes.loading}
        error={recipes.error}
        empty={!recipeRows.length}
        emptyLabel="No agents yet"
        emptyGlyph="🤖"
        onRetry={() => void recipes.reload()}
      >
        <SurfaceRows>
          {recipeRows.map((recipe, index) => (
            <SurfaceRow
              key={rowId(recipe, index)}
              glyph={String(recipe.avatar ?? "🤖")}
              title={String(recipe.name ?? "Agent")}
              detail={presentValue(recipe.role) || undefined}
              meta="→"
              onOpen={() => openPersona(String(recipe.id))}
            />
          ))}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );
  const deliveryFace = (
    <SurfaceSection label="Delivery work">
      <DeliveryListSection />
      <p className="quiet">
        Stories, attempts, and sessions ride the delivery board; open one to
        steer it.
      </p>
    </SurfaceSection>
  );
  return (
    <>
      {hero ? hero(null) : null}
      {view === "delivery" ? deliveryFace : view === "chat" ? chatFace : sessionsFace}
    </>
  );
}
