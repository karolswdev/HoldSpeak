// HS-83-01 — "Ground this ask" on the web composer (the HSM-15-12 parity):
// an inline expandable section on AskPanel. Pick meetings; each expands to
// digest / transcript / its bound artifacts, each independently toggleable;
// the gauge prices the selection live from REAL fetched lengths and a
// past-budget selection refuses here, before any run.
import { useState } from "react";
import {
  fetchGroundingMeeting,
  fetchGroundingResource,
  groundingIsEmpty,
  groundingLabel,
  groundingTokens,
  type GroundingMeeting,
  type GroundingSelection,
} from "../grounding";

const fmt = (n: number): string =>
  n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);

export function GroundingSection(props: {
  meetings: Array<{ id: string; title: string; startedAt?: string }>;
  resources?: Array<{ ref: string; kind: string; id: string; title: string }>;
  selection: GroundingSelection;
  onChange: (s: GroundingSelection) => void;
  limitTokens: number;
}) {
  const { meetings, resources = [], selection, onChange, limitTokens } = props;
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);

  const used = groundingTokens(selection);
  const over = used > limitTokens;
  const frac = limitTokens > 0 ? Math.min(1, used / limitTokens) : 0;
  const tone = over || frac >= 0.85 ? "bad" : frac >= 0.6 ? "warn" : "ok";

  const picked = (id: string) => selection.meetings.find((m) => m.id === id);

  const toggleMeeting = async (row: {
    id: string;
    title: string;
    startedAt?: string;
  }) => {
    if (picked(row.id)) {
      onChange({ ...selection, meetings: selection.meetings.filter((m) => m.id !== row.id) });
      return;
    }
    setLoading(row.id);
    const m = await fetchGroundingMeeting(row.id, row.title, row.startedAt);
    setLoading(null);
    onChange({ ...selection, meetings: [...selection.meetings, m] });
  };

  const toggleResource = async (row: { ref: string; kind: string; id: string; title: string }) => {
    const current = selection.resources || [];
    if (current.some((resource) => resource.ref === row.ref)) {
      onChange({ ...selection, resources: current.filter((resource) => resource.ref !== row.ref) });
      return;
    }
    setLoading(row.ref);
    const resolved = await fetchGroundingResource(row.ref, row.kind, row.id, row.title);
    setLoading(null);
    if (resolved) onChange({ ...selection, resources: [...current, resolved] });
  };

  const mutate = (
    id: string,
    change: (m: GroundingMeeting) => GroundingMeeting,
  ) => {
    onChange({
      ...selection,
      meetings: selection.meetings.map((m) =>
        m.id === id ? change({ ...m }) : m,
      ),
    });
  };

  return (
    <div className={"desk-ground" + (open ? " is-open" : "")}>
      <button
        type="button"
        className="desk-ground-head"
        onClick={() => setOpen((v) => !v)}
      >
        <span
          className={
            "desk-ground-glyph" + (groundingIsEmpty(selection) ? "" : " is-on")
          }
          aria-hidden="true"
        >
          ▤
        </span>
        <span className="desk-ground-title">
          {groundingIsEmpty(selection)
            ? "Ground this ask"
            : `Grounded on ${groundingLabel(selection)}`}
        </span>
        {!groundingIsEmpty(selection) && (
          <span className={"desk-ground-tokens is-" + tone}>
            {fmt(used)} / {fmt(limitTokens)} tok
          </span>
        )}
        <span className="desk-ground-chev" aria-hidden="true">
          {open ? "▴" : "▾"}
        </span>
      </button>

      {open && (
        <div className="desk-ground-body">
          {!groundingIsEmpty(selection) && (
            <div
              className="desk-ground-gauge"
              role="meter"
              aria-valuenow={used}
              aria-valuemax={limitTokens}
            >
              <span
                className={"desk-ground-fill is-" + tone}
                style={{ width: `${Math.round(frac * 100)}%` }}
              />
            </div>
          )}
          {over && (
            <p className="desk-run-warning">
              ⚠ Past the window — drop the transcript or pick less
            </p>
          )}
          {meetings.length === 0 && (
            <p className="desk-ground-empty">No meetings on this desk yet</p>
          )}
          <ul className="desk-ground-list">
            {meetings.map((row) => {
              const sel = picked(row.id);
              return (
                <li
                  key={row.id}
                  className={"desk-ground-row" + (sel ? " is-picked" : "")}
                >
                  <button
                    type="button"
                    className="desk-ground-pick"
                    onClick={() => void toggleMeeting(row)}
                  >
                    <span className="desk-ground-check" aria-hidden="true">
                      {sel ? "●" : "○"}
                    </span>
                    <span className="desk-ground-name">{row.title}</span>
                    {loading === row.id && (
                      <span className="desk-ground-loading">…</span>
                    )}
                    {sel?.day && (
                      <span className="desk-ground-day">{sel.day}</span>
                    )}
                  </button>
                  {sel && (
                    <div className="desk-ground-expand">
                      <button
                        type="button"
                        className={
                          "desk-chip" + (sel.includeIntel ? "" : " quiet")
                        }
                        disabled={!sel.hasIntel}
                        onClick={() =>
                          mutate(row.id, (m) => ({
                            ...m,
                            includeIntel: !m.includeIntel,
                          }))
                        }
                      >
                        {sel.includeIntel ? "✓ " : ""}Digest
                      </button>
                      <button
                        type="button"
                        className={
                          "desk-chip" + (sel.includeTranscript ? "" : " quiet")
                        }
                        disabled={sel.transcriptLines === 0}
                        onClick={() =>
                          mutate(row.id, (m) => ({
                            ...m,
                            includeTranscript: !m.includeTranscript,
                          }))
                        }
                      >
                        {sel.includeTranscript ? "✓ " : ""}Transcript ·{" "}
                        {sel.transcriptLines}
                      </button>
                      {sel.artifacts.map((a) => (
                        <button
                          key={a.id}
                          type="button"
                          className={"desk-chip" + (a.on ? "" : " quiet")}
                          onClick={() =>
                            mutate(row.id, (m) => ({
                              ...m,
                              artifacts: m.artifacts.map((x) =>
                                x.id === a.id ? { ...x, on: !x.on } : x,
                              ),
                            }))
                          }
                        >
                          {a.on ? "✓ " : ""}
                          {a.title}
                        </button>
                      ))}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
          {resources.length > 0 && (
            <>
              <p className="desk-ground-empty">Desk objects and collections</p>
              <ul className="desk-ground-list">
                {resources.map((row) => {
                  const selected = (selection.resources || []).some((resource) => resource.ref === row.ref);
                  return (
                    <li key={row.ref} className={`desk-ground-row${selected ? " is-picked" : ""}`}>
                      <button type="button" className="desk-ground-pick"
                        aria-pressed={selected} onClick={() => void toggleResource(row)}>
                        <span className="desk-ground-check" aria-hidden="true">{selected ? "●" : "○"}</span>
                        <span className="desk-ground-name">{row.title}</span>
                        <span className="desk-ground-day">{row.kind}</span>
                        {loading === row.ref && <span className="desk-ground-loading">…</span>}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
