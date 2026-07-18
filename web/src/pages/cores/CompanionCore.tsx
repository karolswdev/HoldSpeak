// HS-95-08 — the Companion core: the ONE roster of Personas and waiting
// Coder sessions; a persona opens the chat window, a session opens the
// session window (the reconciled surfaces — no duplicate chat/list).
import { openCoderSession, openPersona } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  Disclosure,
  EmptyState,
  Panel,
  StatusPill,
} from "../../components/signal/Signal";
import {
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "../pageSupport";
import { type JsonRecord } from "../../lib/api";

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
        <Panel title="Needs you" eyebrow="Live coding sessions">
          <ul className="data-list">
            {sessions.map((row, index) => {
              const session = (row.session as JsonRecord | undefined) ?? row;
              return (
                <li className="data-row" key={rowId(session, index)}>
                  <button
                    type="button"
                    className="data-row-open"
                    onClick={() =>
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
                  >
                    <strong>
                      {String(
                        session.project ??
                          session.cwd ??
                          session.session_id ??
                          "Coder session",
                      )}
                    </strong>
                    <small>
                      {String(
                        session.summary ??
                          session.question ??
                          "Awaiting your response",
                      )}
                    </small>
                  </button>
                  <StatusPill tone="warning">Awaiting response</StatusPill>
                </li>
              );
            })}
          </ul>
        </Panel>
      ) : null}
      <Panel title="Personas" eyebrow={`${recipeRows.length} personas`}>
        <ResourceState
          loading={recipes.loading}
          error={recipes.error}
          empty={!recipeRows.length}
          onRetry={() => void recipes.reload()}
        >
          <div className="studio-grid">
            {recipeRows.map((recipe, index) => (
              <button
                type="button"
                className="studio-card"
                onClick={() => openPersona(String(recipe.id))}
                key={rowId(recipe, index)}
              >
                <span aria-hidden="true">{String(recipe.avatar ?? "🤖")}</span>
                <strong>{String(recipe.name ?? "Persona")}</strong>
                <p>{String(recipe.role ?? "")}</p>
                <b>Open chat →</b>
              </button>
            ))}
          </div>
        </ResourceState>
      </Panel>
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
