import { createContext, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../../components/DeskMenu";
import { Toolbar } from "../kit";

export const PaneViewContext = createContext<ReactNode>(null);
/** Records of a selected object use the selection toolbar, not a second tab strip. */
type Views = { label: string; value: string; onChange(id: string): void; tabs: readonly { id: string; label: string; inspector?: boolean }[] };
export function PaneViews({ label, value, onChange, tabs, children, inspectorShown, onLayoutChange }: Views & {children: ReactNode; inspectorShown?: boolean; onLayoutChange?(layout:"split"|"compact"):void}) {
  const ref = useRef<HTMLDivElement>(null);
  const [wide,setWide] = useState(false);
  const [toolbar, setToolbar] = useState(false);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return;
    const update = () => {setToolbar(Boolean(node.querySelector('.object-list-toolbar')));setWide(node.clientWidth>620);};
    update(); const watch = new MutationObserver(update);
    const resize=typeof ResizeObserver==='undefined'?null:new ResizeObserver(update);resize?.observe(node);
    watch.observe(node, {childList:true,subtree:true}); return () => {watch.disconnect();resize?.disconnect();};
  }, []);
  useLayoutEffect(()=>onLayoutChange?.(wide ? "split" : "compact"),[wide,onLayoutChange]);
  const available = tabs.filter(tab=>!tab.inspector || !inspectorShown || !wide);
  useLayoutEffect(()=>{if(available.length && tabs.some(tab=>tab.id===value && tab.inspector) && !available.some(tab=>tab.id===value))onChange(available[0].id);},[wide,inspectorShown,value,tabs.map(tab=>tab.id).join("|")]);
  const view = available.length>1 ? <ViewPicker key="pane-view" label={label} value={value} onChange={onChange} tabs={available} /> : null;
  return <div ref={ref} className="surface-pane-views"><PaneViewContext.Provider value={view}>
    {!toolbar && view ? <Toolbar label={label}>{view}</Toolbar> : null}{children}
  </PaneViewContext.Provider></div>;
}
export function paneViewEntries({tabs,value,onChange}: Views): WorkMenuEntry[] {
  return tabs.map(tab=>({type:"item",id:tab.id,label:tab.label,checked:tab.id===value?"exclusive":undefined,onSelect:()=>onChange(tab.id)}));
}
function ViewPicker({label,value,onChange,tabs}: Views) {
  const anchor=useRef<HTMLButtonElement>(null),[open,setOpen]=useState(false);
  const rect=open?anchor.current?.getBoundingClientRect():null;
  return <><Button dense variant="secondary" ref={anchor} data-pane-view="" aria-label={label} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(!open)}>
    View: {tabs.find(tab=>tab.id===value)?.label} ▾
  </Button>{rect ? <WorkMenu label={label} x={rect.left} y={rect.bottom} opener={anchor.current} autoFocus returnFocus={()=>anchor.current?.focus()} onClose={()=>setOpen(false)}
    entries={paneViewEntries({label,value,onChange,tabs})} /> : null}</>;
}
