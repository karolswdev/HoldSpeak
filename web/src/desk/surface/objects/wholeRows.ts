import { useLayoutEffect, type RefObject } from "react";
import { cancelRowLayout, scheduleRowLayout } from "./rowLayout";

/** A scroll has ended: `scrollend` where the browser has it, else 120 ms
 * with no scroll event (Safari before 26 has no `scrollend`; without this the
 * fitter stayed off after the first scroll there). Returns the cleanup. */
export function onScrollEnd(target: HTMLElement, ended: () => void, native = typeof window !== "undefined" && "onscrollend" in window): () => void {
  if (native) {
    target.addEventListener("scrollend", ended);
    return () => target.removeEventListener("scrollend", ended);
  }
  let timer = 0;
  const quiet = () => { window.clearTimeout(timer); timer = window.setTimeout(ended, 120); };
  target.addEventListener("scroll", quiet, { passive: true });
  return () => { window.clearTimeout(timer); target.removeEventListener("scroll", quiet); };
}

/** One row boundary policy for every ObjectList. The unfilled remainder is
 * outside the well. Wheel/touch scrolling stays native until scrollend. */
export function useWholeRows(listRef: RefObject<HTMLDivElement | null>, wellRef: RefObject<HTMLDivElement | null>, enabled: boolean) {
  useLayoutEffect(() => {
    const list = listRef.current, well = wellRef.current;
    if (!enabled || !list || !well) return;
    let moving = false, active = true, followResize = true, follow: HTMLElement | null = null;
    const read = () => {
      if (!active || moving || !list.isConnected || !well.isConnected) return;
      const box = list.getBoundingClientRect(), bounds = well.getBoundingClientRect();
      const style = getComputedStyle(list), ws = getComputedStyle(well);
      const number = (value: string) => parseFloat(value) || 0;
      const border = number(ws.borderTopWidth) + number(ws.borderBottomWidth);
      let end = box.bottom - number(style.paddingBottom) - number(style.borderBottomWidth);
      // A dense list can keep a footer after its well. Prefix chrome is
      // already included in the well's actual top: never subtract it twice.
      const after = [...list.children].slice([...list.children].indexOf(well) + 1);
      for (const child of after) {
        const cs = getComputedStyle(child);
        if (cs.display !== "none" && !["absolute", "fixed"].includes(cs.position)) end -= child.getBoundingClientRect().height + number(cs.marginTop) + number(cs.marginBottom) + number(style.rowGap);
      }
      const available = end - bounds.top - border;
      const budget = Math.max(0, available);
      const scroll = well.scrollTop, top = bounds.top + number(ws.borderTopWidth);
      const headings = new Map<Element, number>();
      const rows = [...well.querySelectorAll<HTMLElement>(".object-list-row, .object-list-group > .kit-toolbar")].map(node => {
        const rect = node.getBoundingClientRect(), group = node.closest(".object-list-group");
        if (group && !headings.has(group)) headings.set(group, group.querySelector(".object-list-group-label")?.getBoundingClientRect().height ?? 0);
        const heading = group ? headings.get(group)! : 0;
        const start = rect.top - top + scroll;
        return { node, start, end: start + rect.height, heading, anchor: Math.max(0, start - heading) };
      });
      // A content-sized recap can shrink after the well is fitted. Its first
      // row is part of its intrinsic floor, before the sibling facts begin.
      const intrinsic = list.parentElement?.matches('.surface-inspector-body[data-fit="rows"]');
      // A bounded seat can be unallocated while its tab or read mounts.
      // Leave its natural well until the seat exists; intrinsic recaps can
      // establish that seat themselves through their measured row floor.
      if (!intrinsic && (!rows.length || !budget)) return;
      const boxInsets = style.boxSizing === "border-box" ? 0
        : number(style.borderTopWidth) + number(style.borderBottomWidth) + number(style.paddingTop) + number(style.paddingBottom);
      const target = follow && rows.find(row => row.node === follow);
      const picked = rows.find(row => row.node.getAttribute("aria-selected") === "true");
      const rowFloor = Math.max(rows[0]?.end ?? 0, target ? target.end - target.start + target.heading : 0, picked ? picked.end - picked.start + picked.heading : 0);
      const floor = `${rows.length ? Math.max(0, box.height - available + rowFloor - boxInsets) : 0}px`;
      const changeFloor = intrinsic && list.style.getPropertyValue("--object-list-row-floor") !== floor;
      let anchor = scroll, height = 0;
      if (rows.length && budget) {
        // The closest boundary avoids jumping backwards after a wheel gesture.
        anchor = rows.reduce((best, row) => Math.abs(row.anchor - scroll) < Math.abs(best - scroll) ? row.anchor : best, 0);
        const tail = rows.at(-1)!;
        anchor = Math.min(anchor, rows.find(row => row.anchor >= tail.end - budget - .01)?.anchor ?? tail.anchor);
        if (target && (target.start < anchor + target.heading - .01 || target.end > anchor + budget + .01)) {
          anchor = rows.find(row => row.anchor >= target.end - budget - .01 && row.anchor <= target.anchor + .01)?.anchor ?? target.anchor;
        }
        follow = null;
        const last = rows.filter(row => row.end <= anchor + budget + .01 && row.end > anchor).at(-1);
        height = last ? last.end - anchor + border : 0;
      }
      const value = `${height}px`;
      const changeHeight = well.style.height !== value;
      const changeScroll = Math.abs(scroll - anchor) > .01;
      return () => {
        if (!active || moving) return;
        if (changeFloor) list.style.setProperty("--object-list-row-floor", floor);
        if (changeHeight) well.style.setProperty("height", value);
        if (changeScroll) well.scrollTop = anchor;
      };
    };
    const schedule = () => scheduleRowLayout(read);
    const resized = () => {
      // A toolbar or form can take focus while the list shrinks. Keep the
      // selection in view then; a manual gesture disables that following.
      const focused = document.activeElement?.closest<HTMLElement>(".object-list-row");
      if (!moving && followResize) follow = focused && well.contains(focused)
        ? focused : well.querySelector('[aria-selected="true"]');
      schedule();
    };
    const focus = (event: FocusEvent) => {
      followResize = true;
      follow = (event.target as HTMLElement).closest(".object-list-row");
      schedule();
    };
    const scrolled = () => { moving = true; cancelRowLayout(read); };
    const ended = () => { moving = false; schedule(); };
    const gesture = (event: Event) => {
      // A press ON a row is not a scroll gesture: the second press of a
      // double-click opens the row's inspector, the list shrinks, and the
      // selected row must still be followed into view (Settings › Keys).
      if (event.type === "pointerdown" && (event.target as Element | null)?.closest?.(".object-list-row")) return;
      followResize = false; follow = null; cancelRowLayout(read);
    };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resized);
    observer?.observe(list);
    for (const child of list.children) if (child !== well) observer?.observe(child);
    const mutations = new MutationObserver(changes => {
      // Width probes are inserted and removed in the same task. Their detached
      // clones do not change row geometry and must not sustain a frame loop.
      const relevant = changes.filter(change => {
        if (change.type === "characterData") return Boolean(change.target.parentElement?.closest(".object-list-row"));
        if (change.type !== "childList") return true;
        const moved = [...change.addedNodes, ...change.removedNodes];
        if (moved.length && moved.every(node => node instanceof Element && node.hasAttribute("data-width-probe"))) return false;
        if (change.target instanceof Element && change.target.closest(".object-list-row")) return true;
        return [...change.addedNodes, ...change.removedNodes].some(node => node instanceof Element && (
          node.matches(".object-list-row,.object-list-group,.object-list-head,.object-list-inner-toolbar") || node.querySelector(".object-list-row")
        ));
      });
      if (!relevant.length) return;
      const selected = relevant.find(change => change.attributeName === "aria-selected" && (change.target as Element).getAttribute("aria-selected") === "true");
      if (selected) { followResize = true; follow = selected.target as HTMLElement; }
      schedule();
    });
    mutations.observe(list, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["aria-selected", "data-detail"] });
    well.addEventListener("scroll", scrolled, { passive: true });
    const offScrollEnd = onScrollEnd(well, ended);
    well.addEventListener("wheel", gesture, { passive: true });
    well.addEventListener("pointerdown", gesture, { passive: true });
    well.addEventListener("focusin", focus);
    document.fonts?.addEventListener("loadingdone", resized);
    void document.fonts?.ready.then(() => { if (active) schedule(); });
    follow = well.querySelector('[aria-selected="true"]');
    schedule();
    return () => {
      active = false; cancelRowLayout(read); observer?.disconnect(); mutations.disconnect();
      document.fonts?.removeEventListener("loadingdone", resized);
      well.removeEventListener("scroll", scrolled); offScrollEnd();
      well.removeEventListener("wheel", gesture); well.removeEventListener("pointerdown", gesture); well.removeEventListener("focusin", focus);
      well.style.height = "";
      list.style.removeProperty("--object-list-row-floor");
    };
  }, [enabled, listRef, wellRef]);
}
