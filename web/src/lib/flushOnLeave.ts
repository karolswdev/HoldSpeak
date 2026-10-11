/* PHILO-17 words: a delayed save must not die with the page. When the page
 * hides (reload, close, tab switch), each Settings writer sends its pending
 * edit at once. The writer uses `keepalive: true` on that request, so the
 * browser finishes it after the page is gone. */
import { useEffect, useRef } from "react";

export function useFlushOnLeave(flush: () => void): void {
  const latest = useRef(flush);
  latest.current = flush;
  useEffect(() => {
    const onPageHide = () => latest.current();
    const onVisibility = () => {
      if (document.visibilityState === "hidden") latest.current();
    };
    window.addEventListener("pagehide", onPageHide);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);
}
