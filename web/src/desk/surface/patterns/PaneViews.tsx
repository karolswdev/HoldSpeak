import { createContext, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { WorkMenu } from "../../components/DeskMenu";
import { Toolbar } from "../kit";

export const PaneViewContext = createContext<ReactNode>(null);
/** Records of a selected object use the selection toolbar, not a second tab strip. */
type Views = { label: string; value: string; onChange(id: string): void; tabs: readonly { id: string; label: string }[] };
export function PaneViews({ label, value, onChange, tabs, children }: Views & {children: ReactNode}) {
  const ref = useRef<HTMLDivElement>(null);
  const [toolbar, setToolbar] = useState(false);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return;
    const update = () => setToolbar(Boolean(node.querySelector('.object-list-toolbar')));
    update(); const watch = new MutationObserver(update);
    watch.observe(node, {childList:true,subtree:true}); return () => watch.disconnect();
  }, []);
  const view = <ViewPicker label={label} value={value} onChange={onChange} tabs={tabs} />;
  return <div ref={ref} className="surface-pane-views"><PaneViewContext.Provider value={view}>
    {!toolbar ? <Toolbar label={label}>{view}</Toolbar> : null}{children}
  </PaneViewContext.Provider></div>;
}
function ViewPicker({label,value,onChange,tabs}: Views) {
  const anchor=useRef<HTMLButtonElement>(null),[open,setOpen]=useState(false);
  const rect=open?anchor.current?.getBoundingClientRect():null;
  return <><Button dense variant="secondary" ref={anchor} aria-label={label} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(!open)}>
    View: {tabs.find(tab=>tab.id===value)?.label} ▾
  </Button>{rect ? <WorkMenu label={label} x={rect.left} y={rect.bottom} opener={anchor.current} autoFocus returnFocus={()=>anchor.current?.focus()} onClose={()=>setOpen(false)}
    entries={tabs.map(tab=>({type:"item",id:tab.id,label:tab.label,checked:tab.id===value?"exclusive":undefined,onSelect:()=>onChange(tab.id)}))} /> : null}</>;
}
