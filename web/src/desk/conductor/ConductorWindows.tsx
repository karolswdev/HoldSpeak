/** PHILO-14 C4 — the Agents window and the surface key that opens it (the
 *  screen's icon, the Dock, Go, ⌘3, the `/conductor` address). The agent's
 *  facts are its pane's Details (the Get Info windows are parked).
 *
 *  One face per agent (2026-11-08): a launched agent opens here, picked: a
 *  coder object of a launch, and a session window asked for a launch's
 *  session (Watch live, a restored window), open Agents on that launch. */
import { useEffect } from "react";
import { ApplicationBoundary } from "../components/ApplicationBoundary";
import { useAgentFlights } from "../agentFlights";
import { answerCoderOpenFirst } from "../lane/coderOpen";
import { launchForSession, useLane } from "../lane/laneStore";
import { openAgentLane, registerSurface } from "../shell";
import { useSteering } from "../steering";
import { ConductorWindow } from "./ConductorWindow";
import { CONDUCTOR_KEY, openConductor, useConductor } from "./store";

export function ConductorWindows() {
  const open = useConductor((s) => s.open);
  useEffect(() => registerSurface(CONDUCTOR_KEY, () => openConductor()), []);
  useEffect(
    () =>
      answerCoderOpenFirst((coder) => {
        const key = `${coder.agent || "claude"}:${coder.sessionId || coder.id}`;
        const launch = launchForSession(key);
        if (!launch) return false;
        openAgentLane(launch, { sessionKey: key });
        return true;
      }),
    [],
  );
  // A session window opened on a launch's session: that agent, in Agents.
  const openKey = useSteering((s) => s.openKey);
  const bound = useLane((s) => s.launchId);
  const fromKey = useAgentFlights((s) => s.flights.find((f) => openKey && f.sessionKey === openKey && f.launchId)?.launchId ?? null);
  useEffect(() => {
    if (fromKey && fromKey !== bound) openAgentLane(fromKey, { sessionKey: openKey });
  }, [fromKey, bound, openKey]);
  // The flights tell which session is a launch's: read once if no face has.
  useEffect(() => {
    if (!useAgentFlights.getState().loaded) void useAgentFlights.getState().load(true);
  }, []);
  return (
    <>
      {open ? (
        <ApplicationBoundary label="Agents">
          <ConductorWindow />
        </ApplicationBoundary>
      ) : null}
    </>
  );
}
