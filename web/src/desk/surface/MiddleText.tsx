import { useLayoutEffect, useRef, useState } from "react";
import { fitName, textMeasure } from "./objects/fitName";
/** A measured single line keeps both ends; title and copy retain the value. */
export function MiddleText({value, title = value, className, testId}: {value: string; title?: string; className?: string; testId?: string}) {
  const ref=useRef<HTMLSpanElement>(null), [shown,setShown]=useState(value);
  useLayoutEffect(() => {
    const node=ref.current; if(!node)return;
    const fit=() => {const measure=textMeasure(getComputedStyle(node)), width=node.clientWidth;
      setShown(measure && width > 0 ? fitName(value,Math.max(4,Math.floor(width/measure.average)),1,line=>measure.width(line)<=width).join("") : value);};
    fit(); const watch=typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fit);
    watch?.observe(node); let live=true; void document.fonts?.ready.then(()=>{if(live)fit();});
    return ()=>{live=false;watch?.disconnect();};
  },[value]);
  return <span ref={ref} className={className} title={title} aria-label={value} data-testid={testId} data-feedback-redact="true">{shown}</span>;
}
