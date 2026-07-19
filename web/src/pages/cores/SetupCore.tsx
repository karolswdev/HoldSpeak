// HS-95-07 — the Setup core: readiness truth, hosted anywhere.
// HS-98-05 — re-crafted native on the surface kit; wire calls unchanged.
import { useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  InlineMessage,
  StatusPill,
} from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { asRows, useResource } from "../pageSupport";
import {
  SurfaceColumns,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { presentValue } from "../../desk/surface/format";

type SetupStatus = {
  overall?: string;
  first_run?: boolean;
  sections?: Array<Record<string, unknown>>;
  trust?: Record<string, unknown>;
  presence?: Record<string, unknown>;
};

export function SetupCore({ hero }: CoreProps) {
  const resource = useResource<SetupStatus>("/api/setup/status", {});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    ok: boolean;
    detail: string;
  } | null>(null);
  const sections = asRows(resource.data.sections, []);

  const testRuntime = async () => {
    setTesting(true);
    try {
      const value = await apiFetch<{ ok?: boolean; detail?: string }>(
        "/api/setup/runtime-test",
        { method: "POST" },
      );
      setTestResult({
        ok: Boolean(value.ok),
        detail: value.detail ?? "Runtime test finished.",
      });
    } catch (error) {
      setTestResult({ ok: false, detail: readableError(error) });
    } finally {
      setTesting(false);
    }
  };

  const verbs = (
    <>
      <Button variant="primary" dense loading={testing} onClick={testRuntime}>
        Test runtime
      </Button>
      <Button dense variant="ghost" onClick={() => void resource.reload()}>
        Refresh
      </Button>
    </>
  );
  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs
          status={
            <StatusPill
              tone={
                resource.data.overall === "ready"
                  ? "success"
                  : resource.data.overall === "blocked"
                    ? "error"
                    : "warning"
              }
            >
              {presentValue(resource.data.overall) || "checking"}
            </StatusPill>
          }
        >
          {verbs}
        </SurfaceVerbs>
      )}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceColumns
          main={
            <SurfaceSection
              label={
                resource.data.overall === "ready"
                  ? "Everything is ready"
                  : "Readiness checks"
              }
            >
              <SurfaceRows>
                {sections.map((section, index) => {
                  const status = String(section.status ?? "unknown");
                  return (
                    <SurfaceRow
                      key={String(section.id ?? index)}
                      title={String(
                        section.label ?? section.name ?? section.id ?? "Check",
                      )}
                      detail={
                        presentValue(section.detail ?? section.description) ||
                        undefined
                      }
                      meta={
                        <StatusPill
                          tone={
                            status === "pass"
                              ? "success"
                              : status === "fail"
                                ? "error"
                                : "warning"
                          }
                        >
                          {status}
                        </StatusPill>
                      }
                    />
                  );
                })}
              </SurfaceRows>
              {!sections.length ? (
                <InlineMessage tone="warning">
                  The hub did not report individual readiness checks.
                </InlineMessage>
              ) : null}
              {testResult ? (
                <InlineMessage tone={testResult.ok ? "success" : "error"}>
                  {testResult.detail}
                </InlineMessage>
              ) : null}
            </SurfaceSection>
          }
          side={
            <SurfaceSection label="Next step">
              <p>
                {resource.data.first_run
                  ? "Try one real dictation when the required checks pass."
                  : "Your first dictation is complete. The Desk is ready."}
              </p>
              <div className="surface-actions">
                <Button
                  variant="primary"
                  dense
                  onClick={() =>
                    openSurfaceOr(
                      resource.data.first_run ? "arrival" : "return-to-desk",
                      resource.data.first_run ? "/welcome" : "/",
                    )
                  }
                >
                  {resource.data.first_run ? "Continue arrival" : "Open Desk"}
                </Button>
                <Button
                  dense
                  variant="ghost"
                  onClick={() =>
                    openSurfaceOr("configure-runs-on", "/profiles")
                  }
                >
                  Runs on
                </Button>
              </div>
            </SurfaceSection>
          }
        />
      </SurfaceState>
    </>
  );
}
