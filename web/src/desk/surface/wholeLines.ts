import { useLayoutEffect, type RefObject } from "react";

/** Keep a partial final reading line below the viewport edge.
 * The full scroll range stays available; no content or focus target is removed. */
export function useWholeLines(ref: RefObject<HTMLElement | null>, enabled = true, rows?: string) {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    const fit = () => {
      const savedScroll = el.scrollTop;
      if (rows) { el.style.maxHeight = ""; el.style.marginBottom = ""; }
      let box = el.getBoundingClientRect();
      const rectangles: DOMRect[] = [];
      if (rows) rectangles.push(...[...el.querySelectorAll<HTMLElement>(rows)].map(row => row.getBoundingClientRect()).filter(rect => rect.height <= box.height));
      else {
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          if (!node.textContent?.trim()) continue;
          const range = document.createRange(); range.selectNodeContents(node);
          if (typeof range.getClientRects === "function") rectangles.push(...range.getClientRects());
        }
      }
      const partial = rectangles.filter(rect => rect.top > box.top + 1 && rect.top < box.bottom && rect.bottom > box.bottom + .5);
      let cut = Math.min(box.bottom, ...partial.map(rect => rect.top - (rows ? 0 : 1)));
      if (rows) {
        // Reserve the full seat while its field box ends at a whole row.
        // Clearing the previous fit above lets a changed form grow again.
        const height = Math.max(0, cut - box.top);
        el.style.maxHeight = `${height}px`;
        el.style.marginBottom = `${box.height - height}px`;
        el.scrollTop = savedScroll;
        box = el.getBoundingClientRect();
        rectangles.splice(0, rectangles.length, ...[...el.querySelectorAll<HTMLElement>(rows)].map(row => row.getBoundingClientRect()).filter(rect => rect.height <= box.height));
        const partial = rectangles.filter(rect => rect.top > box.top + 1 && rect.top < box.bottom && rect.bottom > box.bottom + .5);
        cut = Math.min(box.bottom, ...partial.map(rect => rect.top));
      }
      const start = rows ? Math.max(box.top, ...rectangles.filter(rect => rect.top < box.top - .5 && rect.bottom > box.top).map(rect => rect.bottom)) : box.top;
      el.style.clipPath = cut < box.bottom || start > box.top ? `inset(${start === box.top ? "0" : `${rows ? start - box.top : Math.ceil(start - box.top)}px`} 0 ${rows ? box.bottom - cut : Math.ceil(box.bottom - cut)}px 0)` : "";
    };
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(fit) : null;
    observer?.observe(el);
    if (rows && el.parentElement) observer?.observe(el.parentElement);
    const content = el.firstElementChild;
    if (content) observer?.observe(content);
    if (rows) for (const child of el.children) observer?.observe(child);
    const reveal = (event: Event) => {
      if (!rows || !(event.target instanceof HTMLElement)) return;
      const row = event.target.closest<HTMLElement>(".gadget-row"), box = el.getBoundingClientRect(), rect = row?.getBoundingClientRect();
      if (rect && rect.height <= box.height) el.scrollTop += rect.bottom > box.bottom ? rect.bottom - box.bottom : rect.top < box.top ? rect.top - box.top : 0;
      fit();
    };
    el.addEventListener("focusin", reveal);
    const mutations = new MutationObserver(fit);
    mutations.observe(el, {childList:true, subtree:true, characterData:true});
    fit(); el.addEventListener("scroll", fit, {passive:true});
    let active = true;
    void document.fonts?.ready.then(() => {if (active) fit();});
    return () => {active = false; observer?.disconnect(); mutations.disconnect(); el.removeEventListener("scroll", fit); el.removeEventListener("focusin", reveal); el.style.clipPath = ""; if (rows) { el.style.maxHeight = ""; el.style.marginBottom = ""; }};
  }, [ref, enabled, rows]);
}
