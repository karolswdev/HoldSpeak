/** Thin object-window composition of the kit's fitting toolbar and list menu. */
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { Toolbar, listVerbEntries, type ListVerb } from "../surface";
import { useStripFit } from "../surface/stripMenu";
import { WorkMenu } from "../components/DeskMenu";
import { useWindowId } from "../components/window/windowIdContext";
import { clearListMenu, publishListMenu, useListMenu } from "../components/window/listMenu";

export type ObjectVerb = ListVerb & { menuOnly?: boolean };

export function ObjectActions({ label, verbs, testId, autoFocus = false }: { label: string; verbs: ObjectVerb[]; testId?: string; autoFocus?: boolean }) {
  const windowId = useWindowId();
  const owner = useId();
  const entries = useMemo(() => listVerbEntries(verbs.map(verb => ({...verb,enabled:verb.enabled ?? (() => true)})), null), [verbs]);
  const laidOut = verbs.filter(verb => !verb.menuOnly);
  const menu = useListMenu(windowId);
  const published = useRef<typeof entries | null>(null);
  const publish = () => {
    if (windowId) {published.current = entries;publishListMenu(windowId,owner,entries);}
  };
  useEffect(() => {
    // A focused inner selection list owns the app menu until it leaves.
    if ((!menu.length || menu === published.current) && menu !== entries) publish();
  }, [windowId, owner, entries, menu]);
  useEffect(() => () => { if(windowId)clearListMenu(windowId,owner); }, [windowId,owner]);
  const { ref, fits } = useStripFit<HTMLSpanElement>(true, verbs.map(verb => verb.id + ":" + verb.label).join("|"));
  const anchor = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const rect = open ? anchor.current?.getBoundingClientRect() : null;
  const more = (className?: string) => <Button ref={anchor} dense variant="secondary" className={className} autoFocus={autoFocus} aria-haspopup="menu"
    aria-expanded={open} onClick={() => setOpen(!open)}>Actions ▾</Button>;
  return <Toolbar label={label} data-testid={testId} className="object-list-toolbar">
    <span ref={ref} className="object-list-toolbar-strip" onFocusCapture={publish}>
      {fits ? <span className="object-list-verbs">{laidOut.map((verb,index) => <Button key={verb.id} dense variant="secondary"
        autoFocus={autoFocus && index === 0} title={verb.title} data-testid={verb.testId} disabled={verb.enabled ? !verb.enabled(null) : false}
        onClick={() => verb.run(null)}>{verb.label}</Button>)}{laidOut.length < verbs.length ? more() : null}</span>
        : more()}
    </span>
    {rect ? <WorkMenu label={label + " actions"} x={rect.left} y={rect.bottom} entries={entries} autoFocus
      opener={anchor.current} returnFocus={() => anchor.current?.focus()} onClose={() => setOpen(false)} /> : null}
  </Toolbar>;
}
