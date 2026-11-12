import { useLayoutEffect, type RefObject } from "react";

/** Keep a partial final reading line below the viewport edge.
 * The full scroll range stays available; no content or focus target is removed. */
export function useWholeLines(ref: RefObject<HTMLElement | null>, enabled = true) {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    const fit = () => {
      const box = el.getBoundingClientRect();
      const rectangles: DOMRect[] = [];
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        if (!node.textContent?.trim()) continue;
        const range = document.createRange(); range.selectNodeContents(node);
        if (typeof range.getClientRects === "function") rectangles.push(...range.getClientRects());
      }
      const partial = rectangles.filter(rect => rect.top > box.top + 1 && rect.top < box.bottom && rect.bottom > box.bottom + .5);
      const cut = Math.min(box.bottom, ...partial.map(rect => rect.top - 1));
      el.style.clipPath = cut < box.bottom ? `inset(0 0 ${Math.ceil(box.bottom - cut)}px 0)` : "";
    };
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(fit) : null;
    observer?.observe(el);
    const content = el.firstElementChild;
    if (content) observer?.observe(content);
    const mutations = new MutationObserver(fit);
    mutations.observe(el, {childList:true, subtree:true, characterData:true});
    fit(); el.addEventListener("scroll", fit, {passive:true});
    let active = true;
    void document.fonts?.ready.then(() => {if (active) fit();});
    return () => {active = false; observer?.disconnect(); mutations.disconnect(); el.removeEventListener("scroll", fit);};
  }, [ref, enabled]);
}
