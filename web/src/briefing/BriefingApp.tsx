// The briefing page (PG-DIRECTION DIR2, DIRECTION-2026-10-31.md §6 "The face",
// direction A "the brief"; canvas canvases/direction-2026-10-31.html).
//
// One window of the desk grammar at phone width first: the title bar is the
// package's head (no close gadget: the window is the page); the question
// well (the Your turn ember) with the choices as 44 px library Buttons, each
// with what it does, and Later ▾ last; What changed; the evidence folded and
// read only; the status bar says when it expires and which hub sent it (no
// address). After an answer the well settles: the outcome takes the
// choices' place and nothing else is pressable.
//
// It composes the thin kit (desk/surface/thin.ts), the library Button and
// WorkMenu, and never the desk's auth client (the guard in
// __tests__/briefing.app.test.tsx). Package text is text: no HTML from a
// package is rendered.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
// The library Button itself (Signal.tsx re-exports it beside WorkbenchSelect,
// whose stylesheet the page does not need).
import { Button } from "../components/signal/Button";
import { WorkMenu } from "../desk/components/DeskMenu";
import { DotWord, FoldGadget, StatusBar, SurfaceCode } from "../desk/surface/thin";
import {
  PageRefusal,
  answerItem,
  readPage,
  readPane,
  type BriefingItem,
  type BriefingPage,
  type BriefingPane,
  type PaneBody,
} from "./api";

function waitWords(since: string, now = Date.now()): string {
  const at = Date.parse(since);
  if (!Number.isFinite(at)) return "";
  const minutes = Math.max(0, Math.round((now - at) / 60000));
  if (minutes < 1) return "waits now";
  if (minutes < 60) return `waits ${minutes} min`;
  const hours = Math.round(minutes / 60);
  return hours < 48 ? `waits ${hours} h` : `waits ${Math.round(hours / 24)} days`;
}

const SETTLED = new Set(["decided", "gone"]);

function Caret() {
  return (
    <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
      strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M2.5 3.75L5 6.25l2.5-2.5" />
    </svg>
  );
}

/** The window: title bar, body, status bar (the desk grammar, alone on a page). */
function PageWindow({ head, tone, children, status }: {
  head: string;
  tone: "ask" | "ok" | "idle";
  children: ReactNode;
  status: string[];
}) {
  return (
    <div id="desk-next" className="desk-next briefing" data-testid="briefing-page">
      <section className="desk-window desk-window-shell briefing-window" role="region" aria-label={head}>
        <header className="desk-pullout-head briefing-head">
          <h1 className="desk-pullout-title desk-window-title briefing-title" data-testid="briefing-head">{head}</h1>
          {tone !== "idle" ? <span className="desk-window-lamp" data-tone={tone} aria-hidden="true" /> : null}
        </header>
        <div className="briefing-body">{children}</div>
        <StatusBar className="briefing-status" data-testid="briefing-status" items={status.map((text) => ({ key: text, text }))} />
      </section>
    </div>
  );
}

function Pane({ token, item, pane }: { token: string; item: BriefingItem; pane: BriefingPane }) {
  const [body, setBody] = useState<PaneBody | null>(null);
  const [failed, setFailed] = useState("");
  const asked = useRef(false);
  const open = (isOpen: boolean) => {
    if (!isOpen || asked.current) return;
    asked.current = true;
    readPane(token, item.ref, pane.pane).then(setBody, (error: unknown) => {
      asked.current = false;
      setFailed(error instanceof PageRefusal && error.code === "page_expired" ? "This page has expired." : "This pane did not load. Close it and open it again.");
    });
  };
  return (
    <FoldGadget className="briefing-pane" title={pane.label} token={pane.token || undefined} onToggle={open}>
      <div data-testid={`briefing-pane-${pane.pane}`}>
        {failed ? <p className="briefing-line" role="status">{failed}</p> : null}
        {!body && !failed ? <p className="briefing-line">Reading</p> : null}
        {body?.kind === "code" ? <SurfaceCode>{body.text || "Empty"}</SurfaceCode> : null}
        {body?.kind === "rows" ? (
          <>
            <dl className="briefing-facts">
              {body.rows.map((row) => (
                <div key={row.label} className="briefing-fact">
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
    </FoldGadget>
  );
}

function QuestionWell({ page, item, busy, onAnswer }: {
  page: BriefingPage;
  item: BriefingItem;
  busy: string;
  onAnswer(choice: string, later?: string): void;
}) {
  const opener = useRef<HTMLButtonElement | null>(null);
  const [menu, setMenu] = useState<DOMRect | null>(null);
  const settled = SETTLED.has(item.state);
  const facts = [item.kind_words, settled ? "" : waitWords(item.since), item.level].filter(Boolean).join(" · ");
  return (
    <section className="pg-turn briefing-well" data-state={item.state} aria-label="The question" data-testid="briefing-well">
      <p className="briefing-facts-line">{settled ? <DotWord tone="ok">{item.state === "gone" ? "Answered" : "Decided"}</DotWord> : facts}</p>
      <p className="briefing-question" data-testid="briefing-question">{item.question}</p>
      {item.outcome ? <p className="briefing-outcome" role="status" data-testid="briefing-outcome">{item.outcome.words}</p> : null}
      {settled ? null : (
        <div className="briefing-choices" data-testid="briefing-choices">
          {item.choices.map((choice) => (
            <div key={choice.id} className="briefing-choice">
              <Button variant={choice.primary ? "primary" : "secondary"} loading={busy === choice.id}
                disabled={Boolean(busy)} onClick={() => onAnswer(choice.id)} data-testid={`briefing-choice-${choice.id}`}>
                {choice.label}
              </Button>
              <span className="briefing-consequence">{choice.consequence}</span>
            </div>
          ))}
          <div className="briefing-choice">
            <Button ref={opener} variant="secondary" aria-haspopup="menu" aria-expanded={Boolean(menu)}
              loading={busy === "later"} disabled={Boolean(busy)} data-testid="briefing-later"
              onClick={() => setMenu((now) => (now ? null : opener.current?.getBoundingClientRect() ?? null))}>
              Later <Caret />
            </Button>
            <span className="briefing-consequence">It waits. Nothing changes.</span>
          </div>
        </div>
      )}
      {menu ? (
        <WorkMenu label="Later" x={menu.left} y={menu.bottom} opener={opener.current} autoFocus
          returnFocus={() => opener.current?.focus()} onClose={() => setMenu(null)}
          entries={page.later.map((row) => ({
            type: "item" as const,
            id: row.id,
            label: row.label.includes(row.at) ? row.label : `${row.label} · ${row.at}`,
            onSelect: () => onAnswer("later", row.id),
          }))} />
      ) : null}
    </section>
  );
}

function ExpiredFace() {
  return (
    <PageWindow head="HoldSpeak" tone="idle" status={[]}>
      <div className="briefing-expired" data-testid="briefing-expired">
        <span className="briefing-expired-dot" aria-hidden="true" />
        <p className="briefing-question">This page has expired.</p>
        <p className="briefing-line">Open the item on your desk.</p>
      </div>
    </PageWindow>
  );
}

export function BriefingApp({ token }: { token: string }) {
  const [page, setPage] = useState<BriefingPage | null>(null);
  const [gone, setGone] = useState(!token);
  const [failed, setFailed] = useState("");
  const [busy, setBusy] = useState("");

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
      <PageWindow head="HoldSpeak" tone="idle" status={[]}>
        <div className="briefing-loading" data-testid="briefing-loading">
          <p className="briefing-line" role="status">{failed || "Reading the page"}</p>
          {failed ? <Button variant="secondary" onClick={() => load()} data-testid="briefing-retry">Try again</Button> : null}
        </div>
      </PageWindow>
    );
  }
  const item = page.items[0];
  const answer = async (choice: string, later?: string) => {
    setBusy(choice);
    setFailed("");
    try {
      const done = await answerItem(token, { ref: item.ref, choice, ...(later ? { later } : {}) });
      setPage({ ...page, items: [done.item] });
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
    <PageWindow head={page.package.head || item.head} tone={settled ? "ok" : "ask"}
      status={[page.package.expires_words, `from HoldSpeak on ${page.package.hub}`]}>
      <QuestionWell page={page} item={item} busy={busy} onAnswer={(choice, later) => void answer(choice, later)} />
      {failed ? <p className="briefing-line briefing-failure" role="status" data-testid="briefing-failure">{failed}</p> : null}
      {item.changed.length ? (
        <section className="briefing-section" aria-label="What changed">
          <h2 className="briefing-caption">What changed</h2>
          <ul className="briefing-changed" data-testid="briefing-changed">
            {item.changed.map((row) => (
              <li key={`${row.at}:${row.line}`} className="briefing-change">
                <span className="briefing-clock">{row.clock}</span>
                <span className="briefing-change-line">{row.line}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {item.evidence.length ? (
        <section className="briefing-section" aria-label="Evidence" data-testid="briefing-evidence">
          {item.evidence.map((pane) => <Pane key={pane.pane} token={token} item={item} pane={pane} />)}
        </section>
      ) : null}
    </PageWindow>
  );
}
