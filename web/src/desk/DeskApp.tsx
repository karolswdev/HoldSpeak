// The Desk island (HS-73-01: the foundation at render parity).
//
// React + Vite inside the existing Astro build — the owner's 2026-07-02 stack
// decision. This story renders the EXISTING world (atmosphere, sprites,
// float, drag-to-arrange, Tidy) from the same /api/* data the Alpine desk
// reads; the inhabitation verbs land in the following stories. The legacy
// desk stays frozen at /desk until the cutover story deletes it.
import { useEffect } from "react";
import { useDesk } from "./store";
import { Stage } from "./components/Stage";
import { World } from "./components/World";
import "./desk.css";

export default function DeskApp() {
  const loading = useDesk((s) => s.loading);
  const error = useDesk((s) => s.error);
  const positions = useDesk((s) => s.positions);
  const { refresh, tidyDesk } = useDesk.getState();

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div className="desk-next">
      <Stage />
      <div className="desk-toolbar">
        <span className="pill" data-testid="desk-next-marker">The Desk</span>
        <span className="spacer" />
        {Object.keys(positions).length > 0 && (
          <button type="button" className="btn ghost" onClick={tidyDesk} title="Reset the desk layout">
            Tidy
          </button>
        )}
        <button
          type="button"
          className="btn ghost"
          onClick={() => void refresh()}
          disabled={loading}
          aria-busy={loading}
          title="Refresh from hub"
        >
          Refresh
        </button>
      </div>
      {error ? <p className="inline-message">{error}</p> : null}
      <World />
    </div>
  );
}
