// HS-95-08 — the one shell. The flat header/nav world is gone: the Desk
// is the operating surface and every product path lands there (Article I).
// What remains is the immersive frame every real route renders in.
import { type ReactNode, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { AmbientLayer } from "./AmbientLayer";

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();

  useEffect(() => {
    document.title = `HoldSpeak${
      location.pathname === "/"
        ? ""
        : ` — ${location.pathname.split("/").filter(Boolean).at(-1) ?? "Web"}`
    }`;
  }, [location.pathname]);

  return (
    <>
      <main id="main" className="app-immersive" tabIndex={-1}>
        {children}
      </main>
      <AmbientLayer />
    </>
  );
}
