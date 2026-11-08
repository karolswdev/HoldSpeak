// Settings > This Mac: the hub place, the device name and the diagnostics
// fold (HS-174, HS-200-02). Moved out of SettingsCore.tsx.
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { documentBuildId } from "../../../lib/buildId";
import { FoldGadget, GadgetGroup, GadgetRow } from "../../../desk/surface/gadgets";
import { humanTime, StateChip, SurfaceColumns } from "../../../desk/surface";
import { openSurfaceOr } from "../../../desk/shell";
import { BuilderToolsModule, DeskModule } from "../settingsPrefs";
import { Token } from "../../../desk/surface/Token";
import { RemoteAccessModule } from "./RemoteAccess";
import type { GrantAct } from "./grants";
import type { SettingsBindings } from "./bindings";

/* ── HS-200-02: the loaded runtime identity (contract C1) ──────────
 * What this hub ACTUALLY loaded — captured at its process start, so a
 * later checkout cannot move it. The repair chips are the compact state
 * C1 asks the ordinary Desk to fly; the paths and the pid stay inside
 * the RAW fold, which is the diagnostics surface. */

export type RuntimeIdentityWire = {
  identity: {
    backend_version?: string;
    backend_revision?: string;
    backend_revision_source?: string;
    process_start?: string;
    pid?: number;
    frontend_build?: string;
    database_id?: string;
    database_path?: string;
    schema_version_expected?: number | null;
    schema_version_loaded?: number | null;
    config_revision?: string;
  };
  repair?: string[];
  owns_database?: boolean | null;
  diagnoses?: { id: string; token: string; detail: string }[];
  ownership?: { held?: boolean | null; lock_path?: string | null; owner?: Record<string, unknown> | null };
  bundle_on_disk?: string;
};

const shortToken = (value: string, length = 12) =>
  value && value.length > length ? value.slice(0, length) : value;

export function RuntimeIdentityModule({ children }: { children?: ReactNode } = {}) {
  const [wire, setWire] = useState<RuntimeIdentityWire | null>(null);
  const [error, setError] = useState("");
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let live = true;
    apiFetch<RuntimeIdentityWire>("/api/system/identity")
      .then((next) => { if (live) { setWire(next); setError(""); } })
      .catch((err) => { if (live) setError(readableError(err)); });
    return () => { live = false; };
  }, [nonce]);

  // PHILO-17 U35: the build hashes, the schema and the mesh name are
  // diagnostics. They live in ONE RAW fold; only a repair finding (a stale
  // bundle, a second writer) stays on the face, because it needs him.
  if (error) {
    return (
      <>
        <div className="prefs-read-failure" data-testid="runtime-unreadable" role="alert">
          <span>Device read failed · Settings unchanged · Retry</span>
          <Button variant="ghost" dense onClick={() => { setError(""); setNonce((n) => n + 1); }}>Retry</Button>
        </div>
        {children ? <FoldGadget title="More">{children}</FoldGadget> : null}
      </>
    );
  }
  if (!wire) return <><span className="gadget-fact" role="status">Reading device details…</span>{children ? <FoldGadget title="More">{children}</FoldGadget> : null}</>;

  const id = wire.identity ?? {};
  const served = id.frontend_build ?? "";
  const document_ = documentBuildId();
  const tokens = [...(wire.repair ?? [])];
  // The loaded document disagreeing with the process is the same finding,
  // seen from the browser. Never list a token twice.
  if (document_ && served && document_ !== served && !tokens.includes("STALE BUNDLE")) {
    tokens.push("STALE BUNDLE");
  }
  const schema = id.schema_version_loaded ?? id.schema_version_expected;

  return (
    <>
      {tokens.length ? (
        <div className="prefs-hub-chips" data-testid="runtime-repair">
          {tokens.map((token) => (
            <StateChip key={token} state="warning" label={token} />
          ))}
        </div>
      ) : null}
      <FoldGadget title="More">
        <GadgetGroup material="inset" label="Diagnostics">
          <GadgetRow label="Backend">
            <Token code className="surface-token" data-chip data-testid="runtime-backend">
              {`${id.backend_version ?? "unknown"} · ${shortToken(id.backend_revision ?? "unknown")}`}
            </Token>
          </GadgetRow>
          <GadgetRow label="Bundle">
            <Token code={Boolean(served)} className="surface-token" data-chip data-testid="runtime-bundle">
              {served ? shortToken(served) : "NONE"}
            </Token>
          </GadgetRow>
          <GadgetRow label="Document">
            <Token code={Boolean(document_)} className="surface-token" data-chip data-testid="runtime-document">
              {document_ ? shortToken(document_) : "NONE"}
            </Token>
          </GadgetRow>
          <GadgetRow label="Schema">
            <Token className="surface-token" data-chip data-testid="runtime-schema">
              {schema == null ? "NONE" : `SCHEMA ${schema}`}
            </Token>
          </GadgetRow>
          <GadgetRow label="Database">
            <Token code className="surface-token" data-chip data-testid="runtime-database">
              {shortToken(id.database_id ?? "unknown", 8)}
            </Token>
          </GadgetRow>
          <GadgetRow label="Started">
            <Token className="surface-token" data-chip data-testid="runtime-started">
              {humanTime(id.process_start ?? "")}
            </Token>
          </GadgetRow>
          <GadgetRow label="Identity">
            <Button variant="secondary" dense onClick={() => setNonce((n) => n + 1)}>
              Recheck
            </Button>
          </GadgetRow>
          <GadgetRow label="Config">
            <Token code className="surface-token" data-chip>{shortToken(id.config_revision ?? "unknown", 8)}</Token>
          </GadgetRow>
          <GadgetRow label="Process">
            <Token className="surface-token" data-chip>{`PID ${id.pid ?? "—"}`}</Token>
          </GadgetRow>
          <GadgetRow label="Owns database">
            <Token className="surface-token" data-chip data-testid="runtime-owns">
              {wire.owns_database === true ? "OWNER" : wire.owns_database === false ? "TENANT" : "UNKNOWN"}
            </Token>
          </GadgetRow>
          {id.database_path ? (
            <GadgetRow label="Path" wide>
              <Token code className="surface-token" data-chip data-testid="runtime-path">{id.database_path}</Token>
            </GadgetRow>
          ) : null}
          {(wire.diagnoses ?? []).map((finding) => (
            <GadgetRow key={finding.id} label={finding.token} wide>
              <Token className="surface-token" data-chip>{finding.detail}</Token>
            </GadgetRow>
          ))}
        </GadgetGroup>
        {children}
      </FoldGadget>
    </>
  );
}

/** HS-174: the System module face — owns the display step + hub chips
 *  so the REMOTE chip updates live when the toggle fires. */
/** The hub's place in words: the wire's `THIS DEVICE` reads `This Mac`. */
export function hubPlaceWord(host: string): string {
  const clean = String(host || "").trim();
  if (!clean || /^this (device|mac)$/i.test(clean)) return "This Mac";
  return clean;
}

function SystemModule({
  hubSystem,
  deviceName,
  deskModule,
  rawWell,
  grantAct,
  receiptOpen,
  onGrantAct,
}: {
  hubSystem: { host: string; mesh: boolean; remote?: boolean };
  deviceName: ReactNode;
  deskModule: ReactNode;
  rawWell: ReactNode;
  grantAct?: GrantAct | null;
  receiptOpen?: boolean;
  onGrantAct?: (act: GrantAct) => void;
}) {
  return (
    <>
      <SurfaceColumns
        variant="preferences"
        main={<RemoteAccessModule grantAct={grantAct} receiptOpen={receiptOpen} onGrantAct={onGrantAct} />}
        side={deskModule}
      />
      <GadgetGroup material="inset" label="This Mac">
        {/* Window Program W4 (the words): the hub's place is a row of this
            group in sentence case, never an orphan caps caption. */}
        <GadgetRow label="Hub runs on">
          <span className="gadget-fact" data-testid="system-hub-chips">
            <span data-testid="system-display">{hubPlaceWord(hubSystem.host)}</span>
          </span>
        </GadgetRow>
        {deviceName}
      </GadgetGroup>
      {/* PHILO-17 U35: one RAW fold holds the diagnostics (build hashes,
          schema), and the device rows. */}
      <RuntimeIdentityModule>
        {rawWell}
      </RuntimeIdentityModule>
    </>
  );
}

export function ThisMacSection({ b, hubSystem, grantAct, receiptOpen, onGrantAct, focusHighlight }: {
  b: SettingsBindings;
  hubSystem: { host: string; mesh: boolean; remote?: boolean };
  grantAct: GrantAct | null;
  receiptOpen: boolean;
  onGrantAct: (act: GrantAct) => void;
  focusHighlight: string;
}) {
  const { data, update, val, str, walkerRows } = b;
  const engineLink = (
    <GadgetGroup material="inset" label="HoldSpeak">
      <GadgetRow label="Engines" highlight={focusHighlight === "engines"}>
        <Button variant="secondary" dense onClick={() => openSurfaceOr("configure-runs-on", "/models")} data-testid="settings-engines-page-link">Engines ›</Button>
      </GadgetRow>
      <GadgetRow label="Setup" highlight={focusHighlight === "setup"}>
        <Button variant="secondary" dense onClick={() => openSurfaceOr("configure-setup", "/")} data-testid="settings-setup-page-link">Setup ›</Button>
      </GadgetRow>
    </GadgetGroup>
  );
  /* ── System: display + remote access + desk reset + one RAW (diagnostics, mesh, devices) ── */
  const device = (data.device ?? {}) as Record<string, unknown>;
  const deviceCount = Object.keys(device).length;
  return <>
    {engineLink}
    <SystemModule
          grantAct={grantAct}
          receiptOpen={receiptOpen}
          onGrantAct={onGrantAct}
          hubSystem={hubSystem}
          deviceName={str(["mesh", "device_name"], "Device name")}
          deskModule={<><DeskModule /><BuilderToolsModule
            checked={Boolean(val(["ui", "builder_tools"]) ?? false)}
            onChange={(next) => update(["ui", "builder_tools"], next)}
          /></>}
          rawWell={deviceCount ? (
            <GadgetGroup material="inset" label="Device">
              {walkerRows(device, ["device"])}
            </GadgetGroup>
          ) : null}
        />
  </>;
}
