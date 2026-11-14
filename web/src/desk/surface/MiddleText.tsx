import { useLayoutEffect, useRef, useState } from "react";
import { fitName, textMeasure } from "./objects/fitName";
/** Measured text keeps both ends. File names keep all text when they need another line. */
export function MiddleText({value, title = value, className, testId, keepFileName = false, cut = "middle", lines = 1}: {value: string; title?: string; className?: string; testId?: string; keepFileName?: boolean; cut?: "middle" | "end" | "path"; lines?: number}) {
  const ref=useRef<HTMLSpanElement>(null), probe=useRef<HTMLSpanElement>(null), [shown,setShown]=useState(value);
  useLayoutEffect(() => {
    const node=ref.current; if(!node)return;
    const fit=() => {const width=node.clientWidth; if (!width) {setShown(value);return;} const measure=textMeasure(getComputedStyle(node));
      const tracking = parseFloat(getComputedStyle(node).letterSpacing) || 0;
      const fits = (line: string) => Boolean(measure && measure.width(line) + Math.max(0, [...line].length - 1) * tracking <= width);
      const tail = value.slice(value.lastIndexOf("/") + 1);
      if (keepFileName && measure && width > 0 && !fits(value)) {
        node.toggleAttribute("data-multiline", !fits(`…/${tail}`));
        if (!fits(`…/${tail}`)) { setShown(`${value.split("/")[0]}/…/${tail}`); return; }
        const head = value.slice(0, value.length - tail.length - 1);
        let at = head.length;
        while (at > 0 && !fits(`${head.slice(0, at)}…/${tail}`)) at--;
        setShown(`${head.slice(0, at)}…/${tail}`);
      } else { node.removeAttribute("data-multiline"); setShown(measure && width > 0 ? fitName(value,Math.max(4,Math.floor(width/measure.average)),lines,fits,cut).join("\n") : value); }};
    fit(); const watch=typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fit);
    watch?.observe(node); if(probe.current)watch?.observe(probe.current);
    let live=true; const fonts=document.fonts; fonts?.addEventListener?.("loadingdone",fit); void fonts?.ready.then(()=>{if(live)fit();});
    return ()=>{live=false;watch?.disconnect();fonts?.removeEventListener?.("loadingdone",fit);};
  },[value,keepFileName,cut,lines]);
  return <span ref={ref} className={className} title={title} aria-label={cut === "end" && lines === 1 ? undefined : value} data-testid={testId} data-feedback-redact="true">{shown}<span ref={probe} className="surface-name-measure" data-value={value} aria-hidden="true" /></span>;
}
