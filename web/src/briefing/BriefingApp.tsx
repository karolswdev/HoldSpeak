// The briefing page (PG-DIRECTION DIR2; the owner's verdicts of 2026-10-31;
// canvas docs/internal/betterment/programs/canvases/briefing-page-2026-10-31.html,
// direction A "where we are, then the question").
//
// The brief IS the page: nothing is boxed. From the top: the kind word with
// its lamp; the program's title and goal; the program's step line with this
// step lit (it breathes) and the steps that wait on it marked (they light
// once on load), and "Step 1 of 3 · started 21:14 · waited 1 h 20"; what the
// step was doing and what happened, in body type; the question as the
// page's headline; what this answer blocks; what changed (three plain lines
// at most). The choices are the ONLY raised thing: a tray at the bottom in
// thumb reach, each a library Button with its consequence under it; Later
// opens its four times in place (no menu, no chevron). Under the tray, one
// line of words opens a pane in place: The error · Check log · Brief ·
// Program text, each with a plain Close. After his press the page settles to
// one sentence with a lamp where the question was, and Open on the desk.
//
// It composes the thin kit (desk/surface/thin.ts) and the library Button,
// never the desk's auth client (the guard in __tests__/briefing.app.test.tsx).
// Package text is text: no HTML from a package is rendered.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
// The library Button itself (Signal.tsx re-exports it beside WorkbenchSelect,
// whose stylesheet the page does not need).
import { Button } from "../components/signal/Button";
import { StationTrack, StatusBar, SurfaceCode, type TrackStation } from "../desk/surface/thin";
import {
  PageRefusal,
  answerItem,
  readPage,
  readPane,
  type BriefingItem,
  type BriefingPage,
  type BriefingPane,
  type PaneBody,
  type TrackStep,
} from "./api";

const SETTLED = new Set(["decided", "gone", "later"]);
const GLYPHS = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/20/`;

/** The program's steps as the station track: this step lit, the steps that
 *  wait on it marked, the merged ones passed. */
export function stationsOf(track: readonly TrackStep[]): TrackStation[] {
  return track.map((step) => {
    const here = step.mark === "here";
    const state: TrackStation["state"] = here ? "current" : step.mark === "done" ? "passed"
      : step.mark === "parked" ? "skip" : "ahead";
    const tone = here ? "ask" : step.mark === "blocked" ? "warn" : step.mark === "running" ? "info"
      : step.mark === "done" ? "ok" : "idle";
    return { key: String(step.ordinal), word: String(step.ordinal), state, tone, live: here,
      mark: step.mark === "blocked" ? "blocked" : step.mark === "running" ? "running" : undefined };
  });
}

function trackWords(track: readonly TrackStep[]): string {
  const here = track.find((step) => step.mark === "here");
  const blocked = track.filter((step) => step.mark === "blocked").map((step) => step.ordinal);
  const head = here ? `Step ${here.ordinal} of ${track.length}, here` : `${track.length} steps`;
  if (!blocked.length) return head;
  return `${head}; step${blocked.length === 1 ? "" : "s"} ${blocked.join(", ")} wait${blocked.length === 1 ? "s" : ""} on it`;
}

/** The page: the brief on the surface, the status bar at the foot. */
function PageFrame({ children, status, settled }: { children: ReactNode; status: string[]; settled?: boolean }) {
  return (
    <div id="desk-next" className="desk-next briefing" data-testid="briefing-page">
      <main className="briefing-sheet" data-settled={settled ? "" : undefined}>
        {children}
        <StatusBar className="briefing-status" data-testid="briefing-status" items={status.map((text) => ({ key: text, text }))} />
      </main>
    </div>
  );
}

function KindLabel({ item, tone }: { item: BriefingItem; tone: "ask" | "ok" }) {
  return (
    <p className="briefing-kind" data-testid="briefing-kind">
      <span className="briefing-lamp" data-tone={tone} data-live={tone === "ask" ? "" : undefined} aria-hidden="true" />
      {item.kind_words}
    </p>
  );
}

function ProgramHead({ item, head }: { item: BriefingItem; head: string }) {
  return (
    <header className="briefing-program">
      <h1 className="briefing-title" data-testid="briefing-head">
        <img className="briefing-seat" src={`${GLYPHS}program.png`} alt="" width={20} height={20} />
        <span>{head}</span>
      </h1>
      {item.goal ? <p className="briefing-goal" data-testid="briefing-goal">{item.goal}</p> : null}
    </header>
  );
}

function Panes({ token, item }: { token: string; item: BriefingItem }) {
  const [open, setOpen] = useState<BriefingPane | null>(null);
  const [body, setBody] = useState<PaneBody | null>(null);
  const [failed, setFailed] = useState("");
  const show = (pane: BriefingPane) => {
    if (open?.pane === pane.pane) {
      setOpen(null);
      return;
    }
    setOpen(pane);
    setBody(null);
    setFailed("");
    readPane(token, item.ref, pane.pane).then(setBody, (error: unknown) => {
      setFailed(error instanceof PageRefusal && error.code === "page_expired" ? "This page has expired." : "This pane did not load. Close it and open it again.");
    });
  };
  if (!item.evidence.length) return null;
  return (
    <section className="briefing-evidence" aria-label="Evidence" data-testid="briefing-evidence">
      <p className="briefing-evidence-line">
        {item.evidence.map((pane, index) => (
          <span key={pane.pane} className="briefing-evidence-word">
            {index ? <span className="briefing-dot" aria-hidden="true">·</span> : null}
            <Button dense variant="ghost" className="briefing-link" aria-expanded={open?.pane === pane.pane}
              data-testid={`briefing-open-${pane.pane}`} onClick={() => show(pane)}>
              {pane.label}
            </Button>
          </span>
        ))}
      </p>
      {open ? (
        <div className="briefing-pane" data-testid={`briefing-pane-${open.pane}`}>
          <div className="briefing-pane-head">
            <span className="briefing-pane-title">{open.label}</span>
            <Button dense variant="ghost" className="briefing-link" data-testid="briefing-pane-close" onClick={() => setOpen(null)}>
              Close
            </Button>
          </div>
          {failed ? <p className="briefing-line" role="status">{failed}</p> : null}
          {!body && !failed ? <p className="briefing-line">Reading</p> : null}
          {body?.kind === "code" ? <SurfaceCode>{body.text || "Empty"}</SurfaceCode> : null}
          {body?.kind === "rows" ? (
            <>
              <dl className="briefing-facts">
                {body.rows.map((row, index) => (
                  <div key={`${row.label}-${index}`} className="briefing-fact">
                    <dt>{row.label}</dt>
                    <dd>{row.value}</dd>
                  </div>
                ))}
              </dl>
              {body.url ? (
                <Button dense variant="secondary" data-testid="briefing-open-pr"
                  onClick={() => window.open(String(body.url), "_blank", "noopener,noreferrer")}>
                  Open on GitHub
                </Button>
              ) : null}
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function ChoiceTray({ page, item, busy, onAnswer }: {
  page: BriefingPage;
  item: BriefingItem;
  busy: string;
  onAnswer(choice: string, later?: string): void;
}) {
  const [times, setTimes] = useState(false);
  return (
    <section className="briefing-tray" aria-label="Your choices" data-testid="briefing-choices">
      {item.choices.map((choice) => (
        <div key={choice.id} className="briefing-choice">
          <Button variant={choice.primary ? "primary" : "secondary"} loading={busy === choice.id}
            disabled={Boolean(busy)} onClick={() => onAnswer(choice.id)} data-testid={`briefing-choice-${choice.id}`}>
            {choice.label}
          </Button>
          <span className="briefing-consequence">{choice.consequence}</span>
        </div>
      ))}
      <div className="briefing-choice briefing-later">
        <Button variant="secondary" aria-expanded={times} loading={busy === "later"} disabled={Boolean(busy)}
          data-testid="briefing-later" onClick={() => setTimes((now) => !now)}>
          Later
        </Button>
        {times ? (
          <div className="briefing-times" role="group" aria-label="Later" data-testid="briefing-times">
            {page.later.map((row) => (
              <Button key={row.id} dense variant="secondary" disabled={Boolean(busy)}
                data-testid={`briefing-later-${row.id}`} onClick={() => onAnswer("later", row.id)}>
                {row.label.includes(row.at) ? row.label : `${row.label} · ${row.at}`}
              </Button>
            ))}
          </div>
        ) : (
          <span className="briefing-consequence">It waits. Nothing changes.</span>
        )}
      </div>
    </section>
  );
}

function Brief({ page, item, busy, onAnswer, token }: {
  page: BriefingPage;
  item: BriefingItem;
  busy: string;
  token: string;
  onAnswer(choice: string, later?: string): void;
}) {
  const track = item.track ?? [];
  return (
    <>
      <div className="briefing-read">
        <KindLabel item={item} tone="ask" />
        <ProgramHead item={item} head={page.package.head || item.head} />
        {track.length ? (
          <div className="briefing-where" data-testid="briefing-where">
            <StationTrack form="words" stations={stationsOf(track)} label={trackWords(track)} data-testid="briefing-track" />
            {item.place ? <p className="briefing-place" data-testid="briefing-place">{item.place}</p> : null}
          </div>
        ) : null}
        <div className="briefing-note" data-testid="briefing-note">
          {item.doing ? <p className="briefing-doing">{item.doing}</p> : null}
          {item.happened ? <p className="briefing-happened" data-testid="briefing-happened">{item.happened}</p> : null}
        </div>
        <h2 className="briefing-question" data-testid="briefing-question">{item.question}</h2>
        {item.blocked_words ? (
          <p className="briefing-blocked" data-blocked={item.blocked?.length ? "" : undefined} data-testid="briefing-blocked">
            {item.blocked_words}
          </p>
        ) : null}
        {item.changed.length ? (
          <section className="briefing-changed" aria-label="What changed" data-testid="briefing-changed">
            <h3 className="briefing-caption">What changed</h3>
            {item.changed.map((row) => (
              <p key={`${row.at}:${row.line}`} className="briefing-change">{row.line}</p>
            ))}
          </section>
        ) : null}
      </div>
      <ChoiceTray page={page} item={item} busy={busy} onAnswer={onAnswer} />
      <Panes token={token} item={item} />
    </>
  );
}

/** After his press: one sentence with a lamp, where the question was. */
function Settled({ page, item }: { page: BriefingPage; item: BriefingItem }) {
  const desk = page.package.desk;
  return (
    <div className="briefing-read briefing-settled" data-testid="briefing-well" data-state={item.state}>
      <p className="briefing-program-small">{page.package.head || item.head}</p>
      <p className="briefing-outcome" role="status" data-testid="briefing-outcome">
        <span className="briefing-lamp" data-tone={item.state === "later" ? "info" : "ok"} aria-hidden="true" />
        <span>{item.outcome?.words}</span>
      </p>
      {desk ? (
        <Button variant="secondary" data-testid="briefing-open-desk" onClick={() => window.location.assign(desk)}>
          Open on the desk
        </Button>
      ) : null}
    </div>
  );
}

function ExpiredFace() {
  return (
    <PageFrame status={[]}>
      <div className="briefing-read briefing-expired" data-testid="briefing-expired">
        <p className="briefing-outcome">
          <span className="briefing-lamp" data-tone="idle" aria-hidden="true" />
          <span>This page has expired.</span>
        </p>
        <p className="briefing-line">Open the item on your desk.</p>
      </div>
    </PageFrame>
  );
}

export function BriefingApp({ token }: { token: string }) {
  const [page, setPage] = useState<BriefingPage | null>(null);
  const [gone, setGone] = useState(!token);
  const [failed, setFailed] = useState("");
  const [busy, setBusy] = useState("");
  const top = useRef<HTMLDivElement | null>(null);

  const load = useCallback((clear = true) => {
    if (!token) return;
    if (clear) setFailed("");
    readPage(token).then(setPage, (error: unknown) => {
      if (error instanceof PageRefusal && error.code === "page_expired") setGone(true);
      else setFailed(error instanceof PageRefusal && error.detail ? error.detail : "The page did not load.");
    });
  }, [token]);
  useEffect(() => load(), [load]);

  if (gone) return <ExpiredFace />;
  if (!page) {
    return (
      <PageFrame status={[]}>
        <div className="briefing-read briefing-loading" data-testid="briefing-loading">
          <p className="briefing-line" role="status">{failed || "Reading the page"}</p>
          {failed ? <Button variant="secondary" onClick={() => load()} data-testid="briefing-retry">Try again</Button> : null}
        </div>
      </PageFrame>
    );
  }
  const item = page.items[0];
  const answer = async (choice: string, later?: string) => {
    setBusy(choice);
    setFailed("");
    try {
      const done = await answerItem(token, { ref: item.ref, choice, ...(later ? { later } : {}) });
      setPage({ ...page, items: [done.item] });
      top.current?.scrollIntoView?.({ block: "start" });
    } catch (error) {
      if (error instanceof PageRefusal && error.code === "page_expired") setGone(true);
      else if (error instanceof PageRefusal && error.code === "answered_already") {
        setFailed(error.detail);
        load(false);
      } else setFailed(error instanceof PageRefusal && error.detail ? error.detail : "Your answer did not reach the hub. Nothing changed. Try again.");
    } finally {
      setBusy("");
    }
  };
  const settled = SETTLED.has(item.state);
  return (
    <PageFrame settled={settled} status={[page.package.expires_words, `from HoldSpeak on ${page.package.hub}`]}>
      <div ref={top} />
      {settled ? <Settled page={page} item={item} /> : (
        <Brief page={page} item={item} busy={busy} token={token} onAnswer={(choice, later) => void answer(choice, later)} />
      )}
      {failed ? <p className="briefing-line briefing-failure" role="status" data-testid="briefing-failure">{failed}</p> : null}
    </PageFrame>
  );
}
