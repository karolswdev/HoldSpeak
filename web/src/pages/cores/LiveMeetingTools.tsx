/* Window Program W2-LIVE (2026-10-27; canvas
 * docs/internal/betterment/canvases/live-direction-2026-10-27.html) — the
 * Live window's old gear wing ("Configure meeting"), moved to Settings ▸
 * Meetings. The Live window keeps no gear tab; its toolbar verb *Settings*
 * opens this group. Wire calls unchanged from the wing: the routing preset
 * (`/api/intents/control`, `/api/intents/profile`), the route preview
 * (`/api/intents/preview`), background work (`/api/plugin-jobs/summary`,
 * `/api/plugin-jobs/process`) and the attached devices
 * (`/api/devices/health`, `battery_pct`, `rssi_dbm`, `stale`). The live
 * Summary state went to the Live status bar, where the meeting is; the
 * engine's egress stays on the Summaries run on row above this group. */
import { useEffect, useMemo, useRef, useState } from "react";
import type {
  DevicesHealthResponse,
  IntentControlResponse,
  PluginJobsSummaryResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { useResource } from "../pageSupport";
import {
  CycleGadget,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  PadGadget,
} from "../../desk/surface/gadgets";
import { DotWord } from "../../desk/surface/kit";
import { presentValue } from "../../desk/surface/format";
import { useWaitWord } from "../../desk/surface/objects/ListView";
import { SurfaceCode, SurfaceWell } from "../../desk/surface/Surface";
import "./liveTranscript.css";

/** The hub's device list (`devices` or `items`), rows only. */
function deviceList(value: unknown): Array<Record<string, unknown>> {
  const read = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const rows = Array.isArray(read.devices) ? read.devices : Array.isArray(read.items) ? read.items : [];
  return rows.filter((row): row is Record<string, unknown> => Boolean(row) && typeof row === "object");
}

export function LiveMeetingTools() {
  const intentControl = useResource<IntentControlResponse>("/api/intents/control", {});
  const pluginJobs = useResource<PluginJobsSummaryResponse>("/api/plugin-jobs/summary", {});
  const devices = useResource<DevicesHealthResponse>("/api/devices/health", {});
  /* Settings can render with no live bus (a face test, a page before the
     runtime mounts): then this group keeps its first read and hears no
     frames. useRuntimeBus is one useContext, called on every render. */
  let subscribe: ReturnType<typeof useRuntimeBus>["subscribe"] | undefined;
  try {
    subscribe = useRuntimeBus().subscribe;
  } catch {
    subscribe = undefined;
  }
  const [previewText, setPreviewText] = useState("");
  const [previewResult, setPreviewResult] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const deviceReloadAt = useRef(0);

  // The dials other surfaces moved, the queue, and the device frames.
  const setIntentControls = intentControl.setData;
  const reloadPluginJobs = pluginJobs.reload;
  const reloadDevices = devices.reload;
  useEffect(() => {
    if (!subscribe) return;
    const offIntent = subscribe("intent_controls_updated", (frame) => {
      if (frame.data && typeof frame.data === "object")
        setIntentControls(frame.data as IntentControlResponse);
    });
    const offJobs = subscribe("plugin_jobs_processed", () => void reloadPluginJobs());
    // Battery/RSSI frames are chatty; one refetch per 5 s is enough.
    const offDevices = subscribe("device_health", () => {
      const now = Date.now();
      if (now - deviceReloadAt.current < 5000) return;
      deviceReloadAt.current = now;
      void reloadDevices();
    });
    return () => {
      offIntent();
      offJobs();
      offDevices();
    };
  }, [subscribe, setIntentControls, reloadPluginJobs, reloadDevices]);

  const run = async (work: () => Promise<void>) => {
    setBusy(true);
    setMessage("");
    try {
      await work();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };
  const previewRoute = () =>
    run(async () => {
      setPreviewResult(
        await apiFetch<Record<string, unknown>>("/api/intents/preview", {
          method: "POST",
          json: { text: previewText },
        }),
      );
    });

  /* HS-202-04 (UX-CANON A.8): the queue summary with its zero counts
     dropped; a null (`next_retry_at` on the idle wire) draws nothing. */
  const jobFacts = useMemo(() => {
    const wire = (pluginJobs.data ?? {}) as Record<string, unknown>;
    const kept: Array<[string, string]> = [];
    for (const [key, value] of Object.entries(wire)) {
      if (!["string", "number", "boolean"].includes(typeof value)) continue;
      if (typeof value === "number" && value <= 0) continue;
      if (typeof value === "string" && !value.trim()) continue;
      const word = key.replace(/_/g, " ");
      kept.push([word[0].toUpperCase() + word.slice(1), presentValue(value)]);
    }
    return kept;
  }, [pluginJobs.data]);
  const waiting = jobFacts.length > 0;

  const deviceRows = deviceList(devices.data);
  const devicesWait = useWaitWord(devices.loading);
  const routeFacts = previewResult
    ? (["route", "intent", "confidence"] as const)
        .map((key) => [key, presentValue(previewResult[key])] as const)
        .filter(([, value]) => value !== "")
    : [];

  return (
    <div data-testid="settings-live-meeting">
    <GadgetGroup material="inset" label="Live meeting">
      <GadgetRow label="Attached devices" controlWidth="full">
        <span className="live-tools-value" data-testid="settings-live-devices">
          {devicesWait ? (
            <DotWord tone={devicesWait.tone}>{devicesWait.word}</DotWord>
          ) : devices.error ? (
            <DotWord tone="fail">No answer</DotWord>
          ) : deviceRows.length ? null : (
            <span className="prefs-value live-tools-quiet">None attached</span>
          )}
        </span>
      </GadgetRow>
      {deviceRows.map((device, index) => {
        const battery = presentValue(device.battery_pct);
        const rssi = presentValue(device.rssi_dbm);
        const facts = [battery ? `Battery ${battery}%` : "", rssi ? `Signal ${rssi} dBm` : ""]
          .filter(Boolean)
          .join(" · ");
        return (
          <GadgetRow
            key={String(device.id ?? device.name ?? index)}
            label={String(device.name ?? device.id ?? "Device")}
            fact={facts || undefined}
          >
            <DotWord tone={device.stale ? "warn" : "ok"}>{device.stale ? "Stale" : "Live"}</DotWord>
          </GadgetRow>
        );
      })}
      <GadgetRow label="Background work" controlWidth="full">
        <span className="live-tools-value" data-testid="settings-live-jobs">
          {waiting ? (
            <>
              <span className="prefs-value">
                {jobFacts.map(([key, value]) => `${key} ${value}`).join(" · ")}
              </span>
              <Button
                dense
                variant="secondary"
                onClick={() =>
                  void run(async () => {
                    await apiFetch("/api/plugin-jobs/process", { method: "POST", json: {} });
                    await pluginJobs.reload();
                  })
                }
              >
                Process pending
              </Button>
            </>
          ) : pluginJobs.error ? (
            <DotWord tone="fail">No answer</DotWord>
          ) : (
            <span className="prefs-value live-tools-quiet">No jobs waiting</span>
          )}
        </span>
      </GadgetRow>
      <GadgetRow label="Routing">
        <CycleGadget
          label="Intent routing preset"
          value={String(intentControl.data?.profile ?? "auto")}
          onChange={(next) =>
            void run(async () => {
              await apiFetch("/api/intents/profile", { method: "PUT", json: { profile: next } });
              await intentControl.reload();
            })
          }
          options={[
            { value: "auto", label: "Auto" },
            { value: "off", label: "Off" },
            { value: "balanced", label: "Balanced" },
            { value: "aggressive", label: "Aggressive" },
          ]}
        />
      </GadgetRow>
      <GadgetRow
        label="Try a phrase"
        fact="Tests the route only, the live meeting does not change"
        wide
        controlWidth="full"
      >
        <span className="live-tools-try">
          <PadGadget label="Preview route" value={previewText} rows={2} onChange={setPreviewText} />
          <Button dense variant="secondary" loading={busy} disabled={!previewText.trim()} onClick={() => void previewRoute()}>
            Preview route
          </Button>
        </span>
      </GadgetRow>
      {routeFacts.map(([key, value]) => (
        <GadgetRow key={key} label={key[0].toUpperCase() + key.slice(1)}>
          <span className="prefs-value">{value}</span>
        </GadgetRow>
      ))}
      {previewResult ? (
        <FoldGadget title="Route as data">
          <SurfaceWell head="Route">
            <SurfaceCode>{JSON.stringify(previewResult, null, 2)}</SurfaceCode>
          </SurfaceWell>
        </FoldGadget>
      ) : null}
      {message ? (
        <p className="live-tools-error" role="alert">
          {message}
        </p>
      ) : null}
    </GadgetGroup>
    </div>
  );
}
