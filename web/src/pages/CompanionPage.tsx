import { Link } from "react-router-dom";
import {
  Disclosure,
  EmptyState,
  Panel,
  StatusPill,
} from "../components/signal/Signal";
import {
  PageHero,
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "./pageSupport";
import { type JsonRecord } from "../lib/api";

export default function CompanionPage() {
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
    <div className="page-wrap">
      <PageHero eyebrow="Companion" title="Personas and coder sessions">
        Your recipes and the coders that need you, on the desk your iPad shares.
      </PageHero>
      {sessions.length ? (
        <Panel title="Needs you" eyebrow="Live coding sessions">
          <ul className="data-list">
            {sessions.map((row, index) => {
              const session = (row.session as JsonRecord | undefined) ?? row;
              return (
                <li className="data-row" key={rowId(session, index)}>
                  <div>
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
                  </div>
                  <StatusPill tone="warning">awaiting</StatusPill>
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
              <Link
                className="studio-card"
                to={`/?agent=${encodeURIComponent(String(recipe.id))}`}
                key={rowId(recipe, index)}
              >
                <span aria-hidden="true">{String(recipe.avatar ?? "🤖")}</span>
                <strong>{String(recipe.name ?? "Persona")}</strong>
                <p>{String(recipe.role ?? "")}</p>
                <b>Open on Desk →</b>
              </Link>
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
    </div>
  );
}
