// HS-95-08 — the Companion core: the ONE roster of Personas and waiting
// Coder sessions; a persona opens the chat window, a session opens the
// session window (the reconciled surfaces — no duplicate chat/list).
// HS-98-07 — re-crafted native on the surface kit; wire calls unchanged.
import { openCoderSession, openPersona } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import { Disclosure, StatusPill } from "../../components/signal/Signal";
import { asRows, rowId, useResource } from "../pageSupport";
import { type JsonRecord } from "../../lib/api";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { presentValue } from "../../desk/surface/format";

export function CompanionCore({ hero }: CoreProps) {
  const recipes = useResource<JsonRecord>("/api/recipes", {});
  const coders = useResource<JsonRecord>("/api/coders/status", {});
  const recipeRows = asRows(recipes.data, ["recipes"]).filter(
    (row) => !row.deleted,
  );
  const sessions = asRows(
    (coders.data.agent as JsonRecord | undefined)?.sessions,
    ["items", "sessions"],
  ).filter((row) =>
    Boolean(
      (row.session as JsonRecord | undefined)?.awaiting_response ??
        row.awaiting_response ??
        row.state === "waiting",
    ),
  );
  return (
    <>
      {hero ? hero(null) : null}
      {sessions.length ? (
        <SurfaceSection label="Needs you">
          <SurfaceRows>
            {sessions.map((row, index) => {
              const session = (row.session as JsonRecord | undefined) ?? row;
              return (
                <SurfaceRow
                  key={rowId(session, index)}
                  title={String(
                    session.project ??
                      session.cwd ??
                      session.session_id ??
                      "Coder session",
                  )}
                  detail={
                    presentValue(session.summary ?? session.question) ||
                    "Awaiting your response"
                  }
                  meta={<StatusPill tone="warning">Awaiting response</StatusPill>}
                  onOpen={() =>
                    openCoderSession(
                      String(
                        row.key ??
                          session.key ??
                          `${String(session.agent ?? "claude")}:${String(
                            session.session_id ?? "",
                          )}`,
                      ),
                    )
                  }
                />
              );
            })}
          </SurfaceRows>
        </SurfaceSection>
      ) : null}
      <SurfaceSection label="Personas">
        <SurfaceState
          loading={recipes.loading}
          error={recipes.error}
          empty={!recipeRows.length}
          emptyLabel="No personas yet"
          emptyGlyph="🤖"
          onRetry={() => void recipes.reload()}
        >
          <SurfaceRows>
            {recipeRows.map((recipe, index) => (
              <SurfaceRow
                key={rowId(recipe, index)}
                glyph={String(recipe.avatar ?? "🤖")}
                title={String(recipe.name ?? "Persona")}
                detail={presentValue(recipe.role) || undefined}
                meta="→"
                onOpen={() => openPersona(String(recipe.id))}
              />
            ))}
          </SurfaceRows>
        </SurfaceState>
      </SurfaceSection>
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
}
