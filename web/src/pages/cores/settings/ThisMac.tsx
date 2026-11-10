// Settings > This Mac: the hub place, the device name and the diagnostics
// fold (HS-174, HS-200-02). Moved out of SettingsCore.tsx.
import { useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { documentBuildId } from "../../../lib/buildId";
import { CheckGadget, FoldGadget, GadgetGroup, GadgetRow, StringGadget } from "../../../desk/surface/gadgets";
import { PreferencePane, SegmentedTabs, PaneActions, humanTime, StateChip } from "../../../desk/surface";
import { useBuilderTools } from "../../../desk/builderTools";
import { DeskModule } from "./prefs";
import { CredentialsGroup, type SecretChanges } from "./Accounts";
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
  ownership?: {
    held?: boolean | null;
    lock_path?: string | null;
    owner?: Record<string, unknown> | null;
  };
  bundle_on_disk?: string;
};

const shortToken = (value: string, length = 12) => (value && value.length > length ? value.slice(0, length) : value);

/** The tokens that need him: the hub's repair list, plus a STALE BUNDLE
 *  when the loaded document disagrees with the process. Never twice. */
export function repairTokens(wire: RuntimeIdentityWire | null): string[] {
  if (!wire) return [];
  const served = wire.identity?.frontend_build ?? "";
  const document_ = documentBuildId();
  const tokens = [...(wire.repair ?? [])];
  if (document_ && served && document_ !== served && !tokens.includes("STALE BUNDLE")) tokens.push("STALE BUNDLE");
  return tokens;
}

/** The one read of `/api/system/identity`, with Retry. */
export function useRuntimeIdentity() {
  const [wire, setWire] = useState<RuntimeIdentityWire | null>(null);
  const [error, setError] = useState("");
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    let live = true;
    apiFetch<RuntimeIdentityWire>("/api/system/identity")
      .then((next) => {
        if (live) {
          setWire(next);
          setError("");
        }
      })
      .catch((err) => {
        if (live) setError(readableError(err));
      });
    return () => {
      live = false;
    };
  }, [nonce]);
  return {
    wire,
    error,
    retry: () => {
      setError("");
      setNonce((n) => n + 1);
    },
  };
}

export type RuntimeIdentity = ReturnType<typeof useRuntimeIdentity>;

export function RuntimeIdentityModule() {
  return <RuntimeIdentityDetails identity={useRuntimeIdentity()} />;
}

export function RepairChips({ tokens }: { tokens: string[] }) {
  return (
    <div className="surface-pane-actions" data-testid="runtime-repair">
      {tokens.map((token) => (
        <StateChip key={token} state="warning" label={token} />
      ))}
    </div>
  );
}

/** The hub's place in words: the wire's `THIS DEVICE` reads `This Mac`. */
export function hubPlaceWord(host: string): string {
  const clean = String(host || "").trim();
  if (!clean || /^this (device|mac)$/i.test(clean)) return "This Mac";
  return clean;
}

function RuntimeIdentityDetails({ identity }: { identity: RuntimeIdentity }) {
  const id = identity.wire?.identity;
  const tokens = repairTokens(identity.wire);
  const stale = tokens.includes("STALE BUNDLE");
  return (
    <PreferencePane label="Device details">
      {identity.error ? (
        <div className="surface-pane-actions" role="alert" data-testid="runtime-unreadable">
          <span>Device read failed · Settings unchanged · Retry</span>
          <Button dense onClick={identity.retry}>
            Retry
          </Button>
        </div>
      ) : null}
      {tokens.length ? (
        <PaneActions>
          <RepairChips tokens={tokens} />
          <Button dense onClick={stale ? () => window.location.reload() : identity.retry}>
            {stale ? "Reload" : "Check again"}
          </Button>
        </PaneActions>
      ) : null}
      {identity.wire ? (
        <FoldGadget title="Device details">
          <GadgetGroup>
            <GadgetRow label="Backend">
              <span data-testid="runtime-backend">
                {id?.backend_version} · {shortToken(id?.backend_revision ?? "unknown")}
              </span>
            </GadgetRow>
            <GadgetRow label="Bundle">
              <span data-testid="runtime-bundle">{shortToken(id?.frontend_build || "None")}</span>
            </GadgetRow>
            <GadgetRow label="Document">
              <span data-testid="runtime-document">{shortToken(documentBuildId() || "None")}</span>
            </GadgetRow>
            <GadgetRow label="Started">
              <span data-testid="runtime-started">{humanTime(id?.process_start ?? "")}</span>
            </GadgetRow>
            <GadgetRow label="Process">
              <span>{id?.pid ?? "—"}</span>
            </GadgetRow>

            <GadgetRow label="Schema">
              <span data-testid="runtime-schema">{id?.schema_version_loaded ?? id?.schema_version_expected ?? "None"}</span>
            </GadgetRow>
            <GadgetRow label="Database">
              <span data-testid="runtime-database">{shortToken(id?.database_id ?? "unknown", 8)}</span>
            </GadgetRow>
            <GadgetRow label="Owns database">
              <span data-testid="runtime-owns">
                {identity.wire?.owns_database === true ? "Owner" : identity.wire?.owns_database === false ? "Tenant" : "Unknown"}
              </span>
            </GadgetRow>
            <GadgetRow label="Config">
              <span>{shortToken(id?.config_revision ?? "unknown", 8)}</span>
            </GadgetRow>
            <GadgetRow label="Path" wide>
              <code className="surface-command-code" data-testid="runtime-path" title={id?.database_path ?? undefined}>
                {id?.database_path}
              </code>
            </GadgetRow>
          </GadgetGroup>
        </FoldGadget>
      ) : null}
    </PreferencePane>
  );
}

/** Settings > System (the language, 2026-11-11): the mast says where the
 *  hub runs and who can reach it; the plate is a repair finding when one
 *  needs him, else remote access, the section's primary setting; the
 *  ledger holds the device name, Builder tools, the Engines window and Setup; the
 *  fold holds the desk reset and the diagnostics. */
export function ThisMacSection({
  b,
  hubSystem,
  grantAct,
  receiptOpen,
  onGrantAct,
  focusHighlight,
  secrets,
}: {
  b: SettingsBindings;
  secrets: SecretChanges;
  hubSystem: { host: string; mesh: boolean; remote?: boolean };
  grantAct: GrantAct | null;
  receiptOpen: boolean;
  onGrantAct: (act: GrantAct) => void;
  focusHighlight: string;
}) {
  const { update, val } = b;
  const identity = useRuntimeIdentity();
  const [tab, setTab] = useState(focusHighlight.startsWith("remote") ? "access" : "device");
  const cachedBuilder = useBuilderTools((state) => state.on);
  const setCachedBuilder = useBuilderTools((state) => state.setOn);
  return (
    <PreferencePane label="This Mac">
      <SegmentedTabs
        label="This Mac"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "device", label: "Device" },
          { id: "access", label: "Access" },
          { id: "keys", label: "Keys" },
          { id: "diagnostics", label: "Details" },
        ]}
      >
        <div className="surface-tab-panel" hidden={tab !== "device"}>
          <GadgetGroup label="Device">
            <GadgetRow label="Hub runs on">
              <span data-testid="system-hub-chips">
                <span data-testid="system-display">{hubPlaceWord(hubSystem.host)}</span>
              </span>
            </GadgetRow>
            <GadgetRow label="Device name" highlight={focusHighlight === "mesh.device_name"}>
              <StringGadget
                label="Device name"
                value={String(val(["mesh", "device_name"]) ?? "")}
                onChange={(next) => update(["mesh", "device_name"], next || null)}
              />
            </GadgetRow>
            <GadgetRow label="Builder tools">
              <CheckGadget
                variant="state"
                label="Builder tools"
                checked={Boolean(val(["ui", "builder_tools"]) ?? cachedBuilder)}
                onChange={(next) => {
                  setCachedBuilder(next);
                  update(["ui", "builder_tools"], next);
                }}
              />
            </GadgetRow>
          </GadgetGroup>
          <DeskModule />
        </div>
        <div className="surface-tab-panel" hidden={tab !== "access"}>
          <RemoteAccessModule bare grantAct={grantAct} receiptOpen={receiptOpen} onGrantAct={onGrantAct} />
        </div>
        <div className="surface-tab-panel" hidden={tab !== "keys"}>
          <CredentialsGroup b={b} secrets={secrets} />
        </div>
        {tab === "diagnostics" ? <RuntimeIdentityDetails identity={identity} /> : null}
      </SegmentedTabs>
    </PreferencePane>
  );
}
