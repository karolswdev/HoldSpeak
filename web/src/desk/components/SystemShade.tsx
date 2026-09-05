// HS-101 B6 — the system shade (DESIGN_SYSTEM.md, "The interior
// canon", OS territory §1): ONE surface behind the bell for what
// happened while you were away. Groups are honest — real feeds, real
// counts, zero says zero. The full Desk-memory browser (search,
// filters, receipt detail) stays one verb away.
import "./attention.css";
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, type JsonRecord } from "../../lib/api";
import { gateAge, useGate } from "../gate";
import { useProjections } from "../projections";
import { humanTime } from "../surface/format";
import { countToken } from "../surface/count";
import { StringGadget } from "../surface/gadgets";
import { SurfaceState } from "../surface/Surface";
import { humanizeWireValue } from "../../lib/productLanguage";
import { MicButton } from "./MicButton";
import { openPrimitive, openSurfaceOr, openSurfaceWhenReady } from "../shell";

type Correction = Record<string, unknown>;

// ── HS-171-04: needs-you aggregate wire shape ───────────────────────
type NeedsYouItem = {
  projectId: string;
  projectName: string;
  ref: string;
  title: string;
  why: string;
  ageToken?: string;
  source?: string;
  verbHref?: string;
  severity?: string;
  muted?: boolean;
};

type NeedsYouAggregate = {
  count: number;
  mutedCount?: number;
  projects: string[];
  items: NeedsYouItem[];
  next?: { label: string; at: string } | null;
  computedAt?: string;
  stale?: boolean;
  sweepId?: string | null;
};

/** Group items by projectId, returning one entry per Room with items. */
function groupByRoom(items: NeedsYouItem[]): {
  projectId: string;
  projectName: string;
  items: NeedsYouItem[];
  muted: boolean;
}[] {
  const map = new Map<string, { projectName: string; items: NeedsYouItem[]; muted: boolean }>();
  for (const item of items) {
    const existing = map.get(item.projectId);
    if (existing) {
      existing.items.push(item);
    } else {
      map.set(item.projectId, {
        projectName: item.projectName,
        items: [item],
        muted: Boolean(item.muted),
      });
    }
  }
  // Non-muted first, then muted; within each group, preserve item order.
  return Array.from(map.entries())
    .map(([projectId, v]) => ({ projectId, ...v }))
    .sort((a, b) => (a.muted === b.muted ? 0 : a.muted ? 1 : -1));
}

export function SystemShade({
  open,
  onClose,
  onOpenMemory,
}: {
  open: boolean;
  onClose: () => void;
  onOpenMemory: () => void;
}) {
  const store = useProjections();
  const gate = useGate();
  const [corrections, setCorrections] = useState<Correction[] | null>(null);
  const [needsYou, setNeedsYou] = useState<NeedsYouAggregate | null>(null);
  const [brief, setBrief] = useState<{ itemCount: number; date: string } | null>(null);
  const [denyingId, setDenyingId] = useState<string | null>(null);
  const [denyReason, setDenyReason] = useState("");
  const panel = useRef<HTMLDivElement>(null);

  // A held proposal is a BLOCKED agent: poll while the shade is open
  // so a decision (or an expiry) resolves on glass without a reopen.
  useEffect(() => {
    if (!open) return;
    void useGate.getState().refresh();
    const timer = window.setInterval(() => {
      void useGate.getState().refresh();
    }, 3000);
    return () => window.clearInterval(timer);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    void store.refresh(true);
    void apiFetch<JsonRecord>("/api/dictation/corrections")
      .then((data) => {
        const rows = Array.isArray(data.items)
          ? data.items
          : Array.isArray(data.corrections)
            ? data.corrections
            : [];
        setCorrections(rows as Correction[]);
      })
      .catch(() => setCorrections([]));
    // HS-171-04: fetch needs-you aggregate (cached, cheap)
    void apiFetch<NeedsYouAggregate>("/api/desk/needs-you")
      .then((data) => setNeedsYou(data))
      .catch(() => setNeedsYou(null));
    // HS-171-04: fetch brief latest for the shade row
    void apiFetch<Record<string, unknown> | null>("/api/brief/latest")
      .then((data) => {
        if (!data || data.is_empty) { setBrief(null); return; }
        const sections = (data.sections ?? {}) as Record<string, unknown[]>;
        const itemCount = Object.values(sections).flat().length;
        const genAt = String(data.generated_at ?? "");
        const d = genAt ? new Date(genAt) : null;
        const date = d && !isNaN(d.getTime())
          ? d.toLocaleDateString("en-US", { month: "short", day: "2-digit" }).toUpperCase()
          : "";
        setBrief(itemCount > 0 ? { itemCount, date } : null);
      })
      .catch(() => setBrief(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    const onPointer = (event: PointerEvent) => {
      if (panel.current && !panel.current.contains(event.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open, onClose]);

  if (!open) return null;

  const needsAttentionCount = Number(store.counts.needs_attention || 0);
  const needs = store.projections
    .filter((row) => row.attention_state === "needs_attention")
    .slice(0, 4);
  const finished = store.projections
    .filter((row) => row.attention_state !== "needs_attention")
    .slice(0, 4);
  const learned = (corrections ?? []).slice(0, 3);
  const openSource = (row: (typeof store.projections)[number]) => {
    onClose();
    if (row.detail_url.startsWith("/history")) {
      openSurfaceWhenReady("review-meetings", row.subject_ref);
    } else if (row.detail_url === "/cadence") {
      openSurfaceWhenReady("configure-cadence", row.subject_ref);
    } else {
      openPrimitive(row.source_id);
    }
  };

  return (
    <div className="desk-shade" ref={panel} role="group" aria-label="Missed">
      <div className="desk-shade-head">
        <span className="desk-shade-title">Missed</span>
        <Button
          dense
          variant="ghost"
          className="desk-shade-memory"
          onClick={() => {
            onClose();
            onOpenMemory();
          }}
        >
          Desk memory
        </Button>
      </div>

      <ShadeProjects
        needsYou={needsYou}
        brief={brief}
        onClose={onClose}
      />

      <section className="desk-shade-group" aria-label="Needs you">
        <h4>
          Needs you <b>&middot; {needsAttentionCount + gate.held.length}</b>
        </h4>
        {gate.held.map((proposal) => (
          <div className="desk-shade-item desk-gate-item" key={proposal.id}>
            <span className="desk-shade-glyph" aria-hidden="true">
              ⊘
            </span>
            <div className="desk-shade-what">
              <strong>
                {humanizeWireValue(String(proposal.tool))} held
              </strong>
              <small>waiting {gateAge(proposal)}</small>
              {denyingId === proposal.id ? (
                <span className="desk-shade-do">
                  <StringGadget
                    label="Deny reason"
                    placeholder="Reason for the agent, one line"
                    value={denyReason}
                    autoFocus
                    onChange={setDenyReason}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        void gate.decide(proposal.id, "denied", denyReason);
                        setDenyingId(null);
                        setDenyReason("");
                      }
                      if (event.key === "Escape") setDenyingId(null);
                    }}
                  />
                  <MicButton draftScope="shade-deny" onText={(t: string) => setDenyReason(t)} />
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => {
                      void gate.decide(proposal.id, "denied", denyReason);
                      setDenyingId(null);
                      setDenyReason("");
                    }}
                  >
                    Send deny
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => setDenyingId(null)}
                  >
                    Back
                  </Button>
                </span>
              ) : (
                <span className="desk-shade-do">
                  <Button
                    dense
                    variant="primary"
                    onClick={() => void gate.decide(proposal.id, "approved")}
                  >
                    Approve
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => {
                      setDenyingId(proposal.id);
                      setDenyReason("");
                    }}
                  >
                    Deny
                  </Button>
                </span>
              )}
            </div>
          </div>
        ))}
        {needs.length ? (
          needs.map((row) => (
            <div className="desk-shade-item" key={row.id}>
              <span className="desk-shade-glyph" aria-hidden="true">
                ◎
              </span>
              <div className="desk-shade-what">
                <strong>{row.title}</strong>
                <small>
                  {row.subject_label} &middot; {humanTime(row.timestamp)}
                </small>
                <span className="desk-shade-do">
                  <Button dense variant="ghost" onClick={() => openSource(row)}>
                    Open
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => void store.present(row.id, "acknowledge")}
                  >
                    Acknowledge
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => void store.present(row.id, "dismiss")}
                  >
                    Dismiss
                  </Button>
                </span>
              </div>
            </div>
          ))
        ) : gate.held.length ? null : (
          <SurfaceState empty emptyLabel="Clear" />
        )}
      </section>

      <section className="desk-shade-group" aria-label="Finished">
        <h4>
          Finished <b>&middot; {store.counts.receipts || 0}</b>
        </h4>
        {finished.length ? (
          finished.map((row) => (
            <div className="desk-shade-item" key={row.id}>
              <span className="desk-shade-glyph" aria-hidden="true">
                ✦
              </span>
              <div className="desk-shade-what">
                <strong>{row.title}</strong>
                <small>
                  {row.outcome || row.subject_label} &middot; {humanTime(row.timestamp)}
                </small>
                <span className="desk-shade-do">
                  <Button dense variant="ghost" onClick={() => openSource(row)}>
                    Open
                  </Button>
                </span>
              </div>
            </div>
          ))
        ) : (
          <SurfaceState empty emptyLabel="No receipts" />
        )}
      </section>

      <section className="desk-shade-group" aria-label="Learned">
        <h4>
          Learned <b>&middot; {(corrections ?? []).length}</b>
        </h4>
        {learned.length ? (
          learned.map((row, index) => {
            const gist = row.gist
              ? String(row.gist)
              : row.kind
                ? humanizeWireValue(String(row.kind))
                : "";
            const val = String(row.value ?? row.replacement ?? "");
            return (
              <div className="desk-shade-item" key={String(row.id ?? index)}>
                <span className="desk-shade-glyph" aria-hidden="true">
                  ⌁
                </span>
                <div className="desk-shade-what">
                  <strong>{gist}</strong>
                  {val ? <span>{" → "}{val}</span> : null}
                </div>
              </div>
            );
          })
        ) : (
          <SurfaceState empty emptyLabel="No corrections" />
        )}
      </section>
    </div>
  );
}


// ── HS-171-04: PROJECTS section in the shade ─────────────────────────
//
// FIRST section, above Needs you. Absent when the aggregate count is 0
// and no brief exists. One row per Room with items; muted Rooms dimmed
// with a MUTED token and excluded from the caption count. The brief row
// renders when a brief exists (item count + date).

/** The severity tone for the count chip on a Room row. */
function roomTone(items: NeedsYouItem[]): "warn" | undefined {
  return items.some((i) => i.severity === "danger") ? "warn" : undefined;
}

function ShadeProjects({
  needsYou,
  brief,
  onClose,
}: {
  needsYou: NeedsYouAggregate | null;
  brief: { itemCount: number; date: string } | null;
  onClose: () => void;
}) {
  const rooms = needsYou ? groupByRoom(needsYou.items) : [];
  // The caption count excludes muted Rooms.
  const activeItems = rooms
    .filter((r) => !r.muted)
    .reduce((n, r) => n + r.items.length, 0);
  const captionCount = countToken(activeItems, "NEEDS YOU", "NEED YOU");

  // Absent when no active items and no brief (rule A.8).
  if (!captionCount && !brief) return null;

  return (
    <section
      className="desk-shade-group"
      aria-label="Projects"
      data-testid="shade-projects"
    >
      <h4>
        Projects{captionCount ? <b> &middot; {captionCount}</b> : null}
      </h4>

      {rooms.map((room) => {
        const roomCount = countToken(
          room.muted ? 0 : room.items.length,
          "NEEDS YOU", "NEED YOU",
        );
        const firstWhy = room.items[0]?.why || "";
        return (
          <div
            className={`desk-shade-item${room.muted ? " is-muted" : ""}`}
            key={room.projectId}
            data-testid="shade-project-row"
          >
            <span className="desk-shade-glyph" aria-hidden="true">
              {"|}"}
            </span>
            <div className="desk-shade-what">
              <strong>{room.projectName}</strong>
              <small>
                {room.muted ? (
                  <span className="desk-shade-project-tokens">
                    <span
                      className="surface-token"
                      data-chip
                      data-tone="muted"
                    >
                      MUTED
                    </span>
                  </span>
                ) : (
                  <span className="desk-shade-project-tokens">
                    {roomCount ? (
                      <span
                        className="surface-token"
                        data-chip
                        data-tone={roomTone(room.items)}
                      >
                        {roomCount}
                      </span>
                    ) : null}
                    {firstWhy ? (
                      <span className="desk-shade-why">
                        {firstWhy.length > 40 ? firstWhy.slice(0, 40) : firstWhy}
                      </span>
                    ) : null}
                  </span>
                )}
              </small>
              <span className="desk-shade-do">
                <Button
                  dense
                  variant="ghost"
                  onClick={() => {
                    onClose();
                    openSurfaceOr("project-room", "/projects", room.projectId);
                  }}
                >
                  Open
                </Button>
              </span>
            </div>
          </div>
        );
      })}

      {brief ? (
        <div className="desk-shade-item" data-testid="shade-brief-row">
          <span className="desk-shade-glyph" aria-hidden="true">
            {"="}
          </span>
          <div className="desk-shade-what">
            <strong>Monday brief</strong>
            <small>
              <span className="desk-shade-project-tokens">
                <span className="surface-token" data-chip>
                  {countToken(brief.itemCount, "THING") ?? ""}
                </span>
                {brief.date ? (
                  <span className="desk-shade-why">{brief.date}</span>
                ) : null}
              </span>
            </small>
            <span className="desk-shade-do">
              <Button
                dense
                variant="ghost"
                onClick={() => {
                  onClose();
                  openSurfaceOr("open-intelligence", "/");
                }}
              >
                Open
              </Button>
            </span>
          </div>
        </div>
      ) : null}
    </section>
  );
}
