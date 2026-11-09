// PARKED 20261109 (lane subtract/mission-control): the rails grounding picks (HS-88-02),
// the session's session-to-story pins (HS-87-05) and their helpers. They read the
// Mission control belt's store, parked with it. From desk/grounding.ts and desk/steering.ts.

const PIN_KEY = "hs.steering.pins";

function loadPins(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(PIN_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function savePins(pins: Record<string, string>) {
  try {
    localStorage.setItem(PIN_KEY, JSON.stringify(pins));
  } catch {
    /* storage unavailable — the pin won't persist, honestly */
  }
}

  pinToStory(key, storyId) {
    const pins = { ...get().manualPins, [key]: storyId };
    set({ manualPins: pins });
    savePins(pins);
  },

  clearPin(key) {
    const { [key]: _dropped, ...rest } = get().manualPins;
    set({ manualPins: rest });
    savePins(rest);
  },


/** HS-88-02 — a picked rails object: a phase/story/evidence/roadmap
 * from the belt, priced by its real fetched file size. */
export interface RailsPick {
  repo: string;
  project: string;
  kind: string; // phase | story | evidence | roadmap
  id: string;
  title: string;
  chars: number; // real fetched length; 0 until hydrated
}

/** The rails wire refs (what the hub hydrator resolves). */
export function railsRefs(
  picks: RailsPick[],
): Array<{ repo: string; project: string; kind: string; id: string }> {
  return picks.map((p) => ({
    repo: p.repo,
    project: p.project,
    kind: p.kind,
    id: p.id,
  }));
}

/** The gauge's rails contribution — real file sizes + the provenance
 * header's own weight, in the same 4-chars/token estimate. */
export function railsTokens(picks: RailsPick[]): number {
  return tokens(picks.reduce((n, p) => n + p.chars + p.title.length + 32, 0));
}

/** One wire object for a run grounded on desk objects AND rails.
 * Null only when BOTH are empty. */
export function buildGrounding(
  sel: GroundingSelection,
  rails: RailsPick[],
): {
  meeting_ids: string[];
  artifact_ids: string[];
  refs?: string[];
  expand: "summary" | "full";
  rails?: Array<{ repo: string; project: string; kind: string; id: string }>;
} | null {
  const base = hubGrounding(sel);
  if (!base && rails.length === 0) return null;
  const wire = base || {
    meeting_ids: [],
    artifact_ids: [],
    expand: "summary" as const,
  };
  return rails.length ? { ...wire, rails: railsRefs(rails) } : wire;
}

/** Fetch the real hydrated size of picked rail refs (mirror of
 * fetchGroundingMeeting) so the gauge is honest, never guessed. The
 * hub reads the dw-named file; we keep only the size. */
export async function fetchRailsSizes(
  refs: Array<{ repo: string; project: string; kind: string; id: string }>,
): Promise<Record<string, number>> {
  if (refs.length === 0) return {};
  try {
    const res = await apiRequest("/api/missioncontrol/rails/size", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rails: refs }),
    });
    if (!res.ok) return {};
    const body = await res.json();
    const out: Record<string, number> = {};
    for (const row of body.sizes || [])
      out[`${row.kind}:${row.id}`] = row.chars || 0;
    return out;
  } catch {
    return {};
  }
}


// From desk/components/SessionPullout.tsx: the Classify section with the belt's Flip and Pin to story.
/*
/** Classify (HS-87-05): triage the session onto the desk and the rails —
 * keep the ask as a note, pin to a story, or flip a correlated story
 * through the Phase-82 proposal leg (the ProposalCard renders in the
 * conveyor). All through existing write paths. */
function ClassifySection({ sessionKey }: { sessionKey: string }) {
  const classifyState = useSteering((s) => s.classifyState);
  const manualPins = useSteering((s) => s.manualPins);
  const repos = useMissionControl((s) => s.repos);
  const mcSessions = useMissionControl((s) => s.sessions);
  const [pinInput, setPinInput] = useState("");

  const mc = mcSessions.find((s) => s.key === sessionKey);
  const correlated = mc?.storyRefs[0] || null;
  const flipTarget = correlated
    ? flipTargetForStory(repos, correlated.storyId, correlated.project)
    : null;
  const pinned = manualPins[sessionKey];

  return (
    <div className="desk-classify">
      <span className="desk-classify-label">Classify</span>
      <div className="desk-classify-row">
        <Button
          dense
          variant="ghost"
          className="desk-chip"
          onClick={() => void useSteering.getState().keepAsNote()}
        >
          {classifyState === "kept"
            ? "KEPT"
            : classifyState === "failed"
              ? "Retry keep"
              : "Keep as note"}
        </Button>
        {flipTarget && (
          <Button
            dense
            variant="ghost"
            className="desk-chip"
            title={`propose a status flip for ${flipTarget.story}`}
            onClick={() =>
              useMissionControl
                .getState()
                .proposeFlip(
                  flipTarget.repo,
                  flipTarget.project,
                  flipTarget.story,
                  "done",
                )
            }
          >
            Flip {flipTarget.story} →
          </Button>
        )}
      </div>
      <div className="desk-classify-row">
        {pinned ? (
          <Button
            dense
            variant="ghost"
            className="desk-chip quiet"
            title="clear the manual pin"
            onClick={() => useSteering.getState().clearPin(sessionKey)}
          >
            PINNED {pinned}
          </Button>
        ) : (
          <>
            <MicButton
              label="Pin to story"
              draftScope={`story-pin:${sessionKey}`}
              onText={(t) => setPinInput(t.trim())}
            />
            <StringGadget
              label="Story id"
              value={pinInput}
              placeholder="e.g. HS-87-05"
              onChange={setPinInput}
            />
            <Button
              dense
              variant="ghost"
              className="desk-chip quiet"
              disabled={!pinInput.trim()}
              onClick={() => {
                useSteering.getState().pinToStory(sessionKey, pinInput.trim());
                setPinInput("");
              }}
            >
              Pin
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

*/
