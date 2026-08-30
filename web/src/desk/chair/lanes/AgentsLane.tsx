// HS-135-10 -- the Agents lane: crew/sessions/blocked counts, sessions
// blocked-first with state badge, the Answer verb on blocked sessions
// opening the session window via the existing openCoderSession path.
// Header-click opens the Agents window (surface-companion). Composes
// through ChairLane; no new endpoints -- reuses /api/coders/status and
// /api/recipes.

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { openCoderSession, openSurface } from "../../shell";
import { SurfaceState } from "../../surface/Surface";
import { LampGadget } from "../../surface/gadgets";
import { ChairLane, type LaneItem } from "../Lane";
import { DEFAULT_MAX_ITEMS, type LaneProps } from "../laneContract";

// ---------------------------------------------------------------------------
// types -- reused shapes from CompanionCore (no new endpoints)
// ---------------------------------------------------------------------------

interface CodersStatusResponse {
  agent?: { sessions?: Record<string, unknown>[]; [key: string]: unknown };
  [key: string]: unknown;
}

interface RecipesResponse {
  recipes?: Record<string, unknown>[];
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// helpers -- lifted from CompanionCore verbatim to avoid cross-boundary
// imports (desk/ must not import from pages/)
// ---------------------------------------------------------------------------

/** Extract the flat session array from the coders/status response.
 *  The wire shape is `agent.sessions.items` (an object with count +
 *  selected_index + items array), not a bare array.  Handle both for
 *  forward-compat. */
function extractSessions(
  res: CodersStatusResponse,
): Array<Record<string, unknown>> {
  const sessions = res.agent?.sessions;
  const raw = Array.isArray(sessions)
    ? sessions
    : (sessions as Record<string, unknown> | undefined)?.items;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (row): row is Record<string, unknown> =>
      Boolean(row) && typeof row === "object",
  );
}

/** The blocked predicate (pinned by CompanionCore:62-67). */
function isBlocked(row: Record<string, unknown>): boolean {
  const session = (row.session as Record<string, unknown> | undefined) ?? row;
  return Boolean(
    session.awaiting_response ?? row.awaiting_response ?? row.state === "waiting",
  );
}

/** The session key (pinned by CompanionCore:74-79). */
function sessionKey(row: Record<string, unknown>): string {
  const session = (row.session as Record<string, unknown> | undefined) ?? row;
  return String(
    row.key ??
      session.key ??
      `${String(session.agent ?? "claude")}:${String(session.session_id ?? "")}`,
  );
}

/** The session's display name. */
function sessionName(row: Record<string, unknown>): string {
  const session = (row.session as Record<string, unknown> | undefined) ?? row;
  return String(session.project ?? session.cwd ?? session.session_id ?? "session");
}

// ---------------------------------------------------------------------------
// the lane
// ---------------------------------------------------------------------------

const SURFACE_ID = "surface-companion";

export function AgentsLane({
  maxItems = DEFAULT_MAX_ITEMS,
  onOpenInWindow,
}: LaneProps) {
  const [sessions, setSessions] = useState<Record<string, unknown>[]>([]);
  const [crewCount, setCrewCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [codersRes, recipesRes] = await Promise.all([
        apiFetch<CodersStatusResponse>("/api/coders/status"),
        apiFetch<RecipesResponse>("/api/recipes"),
      ]);
      setSessions(extractSessions(codersRes));
      // A Thread mode is a recipe with kind='mode' (HS-153-01); it is a
      // practice, not a crew member — the lane counts personas only.
      const recipes = (recipesRes.recipes ?? []).filter(
        (r) =>
          !(r as Record<string, unknown>).deleted &&
          (r as Record<string, unknown>).kind !== "mode",
      );
      setCrewCount(recipes.length);
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  // Blocked-first is the ordering contract (pinned by test).
  const blocked = useMemo(() => sessions.filter(isBlocked), [sessions]);
  const running = useMemo(
    () => sessions.filter((row) => !isBlocked(row)),
    [sessions],
  );

  if (loading) return <SurfaceState loading />;
  if (error && sessions.length === 0) {
    return <SurfaceState error={error} onRetry={() => void reload()} />;
  }

  // Blocked-first ordering.
  const ordered = [...blocked, ...running];

  const items: LaneItem[] = ordered.map((row) => {
    const key = sessionKey(row);
    const name = sessionName(row);
    const session = (row.session as Record<string, unknown> | undefined) ?? row;
    const tone = isBlocked(row) ? "blocked" : "run";
    return {
      id: key,
      title: name,
      detail: String(session.summary ?? session.question ?? ""),
      meta: (
        <span className="agents-lane-meta">
          <LampGadget
            label={tone === "blocked" ? "BLOCKED" : "RUN"}
            on
            tone={tone === "blocked" ? "warn" : "ok"}
          />
          {tone === "blocked" ? (
            <Button
              dense
              variant="primary"
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation();
                openCoderSession(key);
              }}
              aria-label={`Answer ${name}`}
            >
              Answer
            </Button>
          ) : null}
        </span>
      ),
    };
  });

  return (
    <ChairLane
      title={`AGENTS · CREW ${crewCount} · BLOCKED ${blocked.length}`}
      maxItems={maxItems}
      items={items}
      onOpenInWindow={(id) => {
        if (id === SURFACE_ID) {
          openSurface(SURFACE_ID);
        } else {
          openCoderSession(id);
        }
      }}
      surfaceId={SURFACE_ID}
      footerVerb="Open Agents"
      emptyState={<SurfaceState empty emptyLabel="No sessions" />}
    />
  );
}
