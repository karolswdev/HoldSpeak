// HS-83-01 — "Ground this ask" on the web composer (the HSM-15-12 parity):
// an inline expandable section on AskPanel. Pick meetings; each expands to
// digest / transcript / its bound artifacts, each independently toggleable;
// the budget prices the selection live from REAL fetched lengths and a
// past-budget selection refuses here, before any run.
// HS-111-05 — the rack grammar (audit §3.4): rows are full-width hover
// bands built on CheckGadget (no per-row borders, no ✓-chips), titles
// ellipsize inside minmax(0,1fr) so a long name can never blow the panel
// width, and the hand-rolled hex gauge is dead — the LedMeter is the one
// budget instrument.
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  fetchGroundingMeeting,
  fetchGroundingResource,
  groundingIsEmpty,
  groundingLabel,
  groundingTokens,
  type GroundingMeeting,
  type GroundingSelection,
} from "../grounding";
import { CheckGadget, FoldGadget, LedMeter } from "../surface/gadgets";

const fmt = (n: number): string =>
  n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);

const tok = (chars: number): number =>
  chars <= 0 ? 0 : Math.max(1, Math.floor(chars / 4));

export function GroundingSection(props: {
  meetings: Array<{ id: string; title: string; startedAt?: string }>;
  resources?: Array<{ ref: string; kind: string; id: string; title: string }>;
  selection: GroundingSelection;
  onChange: (s: GroundingSelection) => void;
  limitTokens: number;
  /** HS-111-05 — a host that owns a shared budget meter (the Ask rack
   * lip, the steer composer) passes false; standalone mounts keep the
   * section's own LedMeter. */
  meter?: boolean;
}) {
  const {
    meetings,
    resources = [],
    selection,
    onChange,
    limitTokens,
    meter = true,
  } = props;
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  // HS-101 B7 — the well lights while a desk object is in flight and
  // receives it through the glass (the engine dispatches the drop).
  const rootRef = useRef<HTMLDivElement>(null);
  const draggingObject = useDesk(
    (s) => Boolean(s.draggingId) && !String(s.draggingId).startsWith("zone:"),
  );

  const used = groundingTokens(selection);
  const over = used > limitTokens;
  const frac = limitTokens > 0 ? Math.min(1, used / limitTokens) : 0;
  const tone = over || frac >= 0.85 ? "danger" : frac >= 0.6 ? "warn" : undefined;

  const picked = (id: string) => selection.meetings.find((m) => m.id === id);

  // The whole band is the press target (a row convenience, not a second
  // control): the CheckGadget stays the ONE focusable gadget, and a click
  // that originated on it is not doubled.
  const bandPress =
    (fn: () => void, disabled?: boolean) =>
    (event: { target: EventTarget }) => {
      if (disabled) return;
      if ((event.target as HTMLElement).closest(".gadget-check")) return;
      fn();
    };

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

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const onGlassDrop = (event: Event) => {
      const detail = (event as CustomEvent).detail as {
        id?: string;
        kind?: string;
      } | null;
      if (!detail?.id) return;
      setOpen(true);
      const meeting = meetings.find((m) => m.id === detail.id);
      if (meeting) {
        if (!picked(meeting.id)) void toggleMeeting(meeting);
        return;
      }
      const res = resources.find(
        (row) =>
          row.id === detail.id ||
          row.ref === detail.id ||
          row.ref === `${detail.kind}:${detail.id}`,
      );
      if (
        res &&
        !(selection.resources || []).some((r) => r.ref === res.ref)
      ) {
        void toggleResource(res);
      }
    };
    el.addEventListener("desk:glass-drop", onGlassDrop);
    return () => el.removeEventListener("desk:glass-drop", onGlassDrop);
  });

  return (
    <div
      ref={rootRef}
      data-glass-accept="desk-object"
      className={
        "desk-ground" +
        (open ? " is-open" : "") +
        (draggingObject ? " is-drop-ready" : "")
      }
    >
      <FoldGadget
        className="desk-ground-fold"
        glyph={
          <span
            className={
              "desk-ground-glyph" +
              (groundingIsEmpty(selection) ? "" : " is-on")
            }
          >
            ▤
          </span>
        }
        title={
          groundingIsEmpty(selection)
            ? "Ground this ask"
            : `Grounded on ${groundingLabel(selection)}`
        }
        token={
          groundingIsEmpty(selection) ? undefined : (
            <span className="surface-token" data-tone={tone}>
              {fmt(used)} / {fmt(limitTokens)} tok
            </span>
          )
        }
        open={open}
        onToggle={setOpen}
      >
        {open && (
        <div className="desk-ground-body">
          {meter && !groundingIsEmpty(selection) && (
            <LedMeter label="CTX" value={frac} />
          )}
          {over && (
            <p className="desk-ground-refusal">
              ✕ PAST THE WINDOW · DROP THE TRANSCRIPT OR PICK LESS
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
                  <div
                    className="desk-ground-line is-press"
                    onClick={bandPress(() => void toggleMeeting(row))}
                  >
                    <CheckGadget
                      label={row.title}
                      checked={Boolean(sel)}
                      onChange={() => void toggleMeeting(row)}
                    />
                    <span className="desk-ground-name">{row.title}</span>
                    {loading === row.id && (
                      <span className="desk-ground-loading">…</span>
                    )}
                    {sel?.day && (
                      <span className="desk-ground-fig">{sel.day}</span>
                    )}
                  </div>
                  {sel && (
                    <div className="desk-ground-sub">
                      <div
                        className={
                          "desk-ground-line is-sub" +
                          (sel.hasIntel ? " is-press" : " is-off")
                        }
                        data-on={sel.includeIntel || undefined}
                        onClick={bandPress(
                          () =>
                            mutate(row.id, (m) => ({
                              ...m,
                              includeIntel: !m.includeIntel,
                            })),
                          !sel.hasIntel,
                        )}
                      >
                        <CheckGadget
                          label="Digest"
                          checked={sel.includeIntel}
                          disabled={!sel.hasIntel}
                          onChange={() =>
                            mutate(row.id, (m) => ({
                              ...m,
                              includeIntel: !m.includeIntel,
                            }))
                          }
                        />
                        <span className="desk-ground-name">Digest</span>
                        {sel.intelChars > 0 && (
                          <span className="desk-ground-fig">
                            {fmt(tok(sel.intelChars))} tok
                          </span>
                        )}
                      </div>
                      <div
                        className={
                          "desk-ground-line is-sub" +
                          (sel.transcriptLines === 0 ? " is-off" : " is-press")
                        }
                        data-on={sel.includeTranscript || undefined}
                        onClick={bandPress(
                          () =>
                            mutate(row.id, (m) => ({
                              ...m,
                              includeTranscript: !m.includeTranscript,
                            })),
                          sel.transcriptLines === 0,
                        )}
                      >
                        <CheckGadget
                          label={`Transcript · ${sel.transcriptLines}`}
                          checked={sel.includeTranscript}
                          disabled={sel.transcriptLines === 0}
                          onChange={() =>
                            mutate(row.id, (m) => ({
                              ...m,
                              includeTranscript: !m.includeTranscript,
                            }))
                          }
                        />
                        <span className="desk-ground-name">
                          Transcript · {sel.transcriptLines}
                        </span>
                        {sel.transcriptChars > 0 && (
                          <span className="desk-ground-fig">
                            {fmt(tok(sel.transcriptChars))} tok
                          </span>
                        )}
                      </div>
                      {sel.artifacts.map((a) => (
                        <div
                          key={a.id}
                          className="desk-ground-line is-sub is-press"
                          data-on={a.on || undefined}
                          onClick={bandPress(() =>
                            mutate(row.id, (m) => ({
                              ...m,
                              artifacts: m.artifacts.map((x) =>
                                x.id === a.id ? { ...x, on: !x.on } : x,
                              ),
                            })),
                          )}
                        >
                          <CheckGadget
                            label={a.title}
                            checked={a.on}
                            onChange={() =>
                              mutate(row.id, (m) => ({
                                ...m,
                                artifacts: m.artifacts.map((x) =>
                                  x.id === a.id ? { ...x, on: !x.on } : x,
                                ),
                              }))
                            }
                          />
                          <span className="desk-ground-name">{a.title}</span>
                          <span className="desk-ground-fig">
                            {fmt(tok(a.chars))} tok
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
          {resources.length > 0 && (
            <>
              <p className="desk-ground-sect">DESK OBJECTS · COLLECTIONS</p>
              <ul className="desk-ground-list">
                {resources.map((row) => {
                  const selected = (selection.resources || []).some(
                    (resource) => resource.ref === row.ref,
                  );
                  const priced = (selection.resources || []).find(
                    (resource) => resource.ref === row.ref,
                  );
                  return (
                    <li
                      key={row.ref}
                      className={`desk-ground-row${selected ? " is-picked" : ""}`}
                    >
                      <div
                        className="desk-ground-line is-press"
                        onClick={bandPress(() => void toggleResource(row))}
                      >
                        <CheckGadget
                          label={row.title}
                          checked={selected}
                          onChange={() => void toggleResource(row)}
                        />
                        <span className="desk-rails-kind">{row.kind}</span>
                        <span className="desk-ground-name">{row.title}</span>
                        {loading === row.ref && (
                          <span className="desk-ground-loading">…</span>
                        )}
                        {priced && (
                          <span className="desk-ground-fig">
                            {fmt(tok(priced.chars))} tok
                          </span>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>
        )}
      </FoldGadget>
    </div>
  );
}
