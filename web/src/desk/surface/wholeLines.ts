import { useLayoutEffect, type RefObject } from "react";

/** Keep a partial final reading line below the viewport edge.
 * The full scroll range stays available; no content or focus target is removed. */
export function useWholeLines(ref: RefObject<HTMLElement | null>, enabled = true, rows?: string) {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    const fit = () => {
      const box = el.getBoundingClientRect();
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
      const cut = Math.min(box.bottom, ...partial.map(rect => rect.top - (rows ? 0 : 1)));
      if (rows && el.parentElement) {
        // Bound the scroll box itself, so the touch area ends with its last
        // whole row too. Measure the form's available seat rather than the
        // previously fitted box; a larger window must be able to grow it.
        const form = el.parentElement, style = getComputedStyle(form);
        const siblings = [...form.children].filter(child => child !== el && getComputedStyle(child).display !== "none");
        const available = form.clientHeight - (parseFloat(style.paddingTop) || 0) - (parseFloat(style.paddingBottom) || 0)
          - siblings.reduce((sum, child) => sum + child.getBoundingClientRect().height, 0) - (parseFloat(style.rowGap) || 0) * siblings.length;
        if (available > 0) {
          const edge = box.top + available;
          const crossing = rectangles.filter(rect => rect.top > box.top + 1 && rect.top < edge && rect.bottom > edge + .5);
          const end = Math.min(edge, ...crossing.map(rect => rect.top));
          el.style.maxHeight = `${Math.floor(end - box.top)}px`;
        }
      }
      const start = rows ? Math.max(box.top, ...rectangles.filter(rect => rect.top < box.top - .5 && rect.bottom > box.top).map(rect => rect.bottom)) : box.top;
      el.style.clipPath = cut < box.bottom || start > box.top ? `inset(${start === box.top ? "0" : `${Math.ceil(start - box.top)}px`} 0 ${Math.ceil(box.bottom - cut)}px 0)` : "";
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
    return () => {active = false; observer?.disconnect(); mutations.disconnect(); el.removeEventListener("scroll", fit); el.removeEventListener("focusin", reveal); el.style.clipPath = ""; if (rows) el.style.maxHeight = "";};
  }, [ref, enabled, rows]);
}
