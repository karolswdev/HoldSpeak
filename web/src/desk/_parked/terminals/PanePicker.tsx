/** Parked compatibility implementation of the pre-Terminals pane picker.
 * The live desk door is now the native Terminals application. Kept here as a
 * recoverable reference while old session fixtures and styles are retired. */
import { useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { useSteering } from "../../steering";
import { StringGadget, TransportKey } from "../../surface";

const GLYPH_CLOSE = String.fromCodePoint(0x2715);

export function PanePicker() {
  const panes = useSteering((s) => s.panes);
  const panesState = useSteering((s) => s.panesState);
  const factoryState = useSteering((s) => s.factoryState);
  const factoryDetail = useSteering((s) => s.factoryDetail);
  const [open, setOpen] = useState(false);
  const [spawnName, setSpawnName] = useState("");
  const doSpawn = async () => {
    const name = spawnName.trim();
    if (!name) return;
    if (await useSteering.getState().spawnSession(name)) {
      setSpawnName("");
      setOpen(false);
    }
  };
  useEffect(() => {
    if (open) void useSteering.getState().listPanes();
  }, [open]);
  return (
    <div className={"desk-panepicker" + (open ? " is-open" : "")}>
      <Button variant="chrome" onClick={() => setOpen((value) => !value)}>Legacy panes</Button>
      {open ? (
        <div className="desk-panepicker-list">
          <div className="desk-panepicker-spawn">
            <StringGadget label="New session name" value={spawnName} onChange={setSpawnName}
              onKeyDown={(event) => { if (event.key === "Enter") void doSpawn(); }} />
            <TransportKey compact label="SPAWN" glyph="＋" disabled={!spawnName.trim() || factoryState === "working"}
              onClick={() => void doSpawn()} />
          </div>
          {factoryState === "failed" ? <span className="desk-panepicker-empty desk-arm-refusal"><span aria-hidden="true">{GLYPH_CLOSE}</span> {factoryDetail}</span> : null}
          {panesState === "loading" ? <span className="desk-panepicker-empty">…</span> : null}
          {panesState === "error" ? <span className="desk-panepicker-empty">tmux unreachable</span> : null}
          {panesState === "loaded" && panes.length === 0 ? <span className="desk-panepicker-empty">no tmux panes</span> : null}
          {panes.map((pane) => (
            <Button key={pane.paneId} variant="chrome" className={"desk-panepicker-item" + (pane.active ? " is-active" : "")}
              onClick={() => { useSteering.setState({ attachedSession: pane.session }); useSteering.getState().openSession(`pane:${pane.paneId}`); setOpen(false); }}>
              <span className="desk-panepicker-id">{pane.paneId}</span>
              <span className="desk-panepicker-meta">{pane.session}{pane.command ? ` · ${pane.command}` : ""}</span>
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
