// Parked: the declared walk now lives in the window app menu.
/** Show me: the one standard verb at the end of every native mast (owner,
 * 2026-11-09). It runs the app's own walk in place, on the desk, through the
 * desk's one WalkRunner. An app that declares no walk draws no verb. On the
 * phone (393) the verb is inside More. A mast that has its own More puts the
 * verb there with `useShowMe` (`showMeEntry`) and draws `<ShowMe inMore />`. */
import { useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { useWindowId } from "../components/window/windowIdContext";
import { useCompactViewport } from "../useCompactViewport";
import { appWalk, startAppWalk } from "./appWalks";

export const SHOW_ME = "Show me";

export function useShowMe(app: string) {
  const origin = useWindowId();
  const compact = useCompactViewport();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const declared = Boolean(appWalk(app));
  const start = () => {
    if (busy) return;
    setBusy(true);
    setFailed(false);
    startAppWalk(app, origin)
      .catch(() => { setFailed(true); })
      .finally(() => setBusy(false));
  };
  /** The More entry, on the phone only (the Button is the verb at desk width). */
  const entry: WorkMenuEntry | null = declared && compact
    ? { type: "item", id: "show-me", label: SHOW_ME, ghost: busy ? "Busy" : undefined, onSelect: start }
    : null;
  return { declared, compact, busy, failed, start, entry };
}

export function ShowMe({ app, inMore = false }: { app: string; inMore?: boolean }) {
  const { declared, compact, busy, failed, start, entry } = useShowMe(app);
  const moreRef = useRef<HTMLButtonElement | null>(null);
  const [open, setOpen] = useState(false);
  if (!declared || (compact && inMore)) return null;
  const failure = failed
    ? <span className="walk-show-me-failure" role="alert" data-testid="show-me-failure">The walk did not start. Try again.</span>
    : null;
  if (compact && entry) {
    const rect = open ? moreRef.current?.getBoundingClientRect() : null;
    return (
      <>
        <Button ref={moreRef} dense variant="secondary" aria-haspopup="menu" aria-expanded={open}
          loading={busy} onClick={() => setOpen((value) => !value)} data-testid="show-me-more">
          More
        </Button>
        {open && rect ? (
          <WorkMenu label="More" anchor="below" x={rect.left} y={rect.bottom} opener={moreRef.current} autoFocus
            returnFocus={() => moreRef.current?.focus()} entries={[entry]} onClose={() => setOpen(false)} />
        ) : null}
        {failure}
      </>
    );
  }
  return (
    <>
      <Button dense variant="secondary" loading={busy} disabled={busy} onClick={start} data-testid="show-me">
        {SHOW_ME}
      </Button>
      {failure}
    </>
  );
}
