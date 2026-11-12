import { useLayoutEffect, useRef, useState } from "react";
import { fitName, textMeasure } from "./objects/fitName";
/** Measured text keeps both ends. File names keep all text when they need another line. */
export function MiddleText({value, title = value, className, testId, keepFileName = false}: {value: string; title?: string; className?: string; testId?: string; keepFileName?: boolean}) {
  const ref=useRef<HTMLSpanElement>(null), [shown,setShown]=useState(value);
  useLayoutEffect(() => {
    const node=ref.current; if(!node)return;
    const fit=() => {const measure=textMeasure(getComputedStyle(node)), width=node.clientWidth;
      const fits = (line: string) => Boolean(measure && measure.width(line) <= width);
      const tail = value.slice(value.lastIndexOf("/") + 1);
      if (keepFileName && measure && width > 0 && !fits(value)) {
        node.toggleAttribute("data-multiline", !fits(`…/${tail}`));
        if (!fits(`…/${tail}`)) { setShown(`${value.split("/")[0]}/…/${tail}`); return; }
        const head = value.slice(0, value.length - tail.length - 1);
        let at = head.length;
        while (at > 0 && !fits(`${head.slice(0, at)}…/${tail}`)) at--;
        setShown(`${head.slice(0, at)}…/${tail}`);
      } else { node.removeAttribute("data-multiline"); setShown(measure && width > 0 ? fitName(value,Math.max(4,Math.floor(width/measure.average)),1,fits).join("") : value); }};
    fit(); const watch=typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fit);
    watch?.observe(node); let live=true; void document.fonts?.ready.then(()=>{if(live)fit();});
    return ()=>{live=false;watch?.disconnect();};
  },[value,keepFileName]);
  return <span ref={ref} className={className} title={title} aria-label={value} data-testid={testId} data-feedback-redact="true">{shown}</span>;
}
