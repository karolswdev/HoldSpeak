import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-95-07 — the Setup core: readiness truth, hosted anywhere.
// HS-98-05 — re-crafted native on the surface kit; wire calls unchanged.
import { useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps, SetupStatus } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { LampGadget } from "../../desk/surface/gadgets";
import { apiFetch, readableError } from "../../lib/api";
import { asRows, useResource } from "../pageSupport";
import {
  SurfaceColumns,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { CoreResourceGuard, renderHeroSlot } from "./core-layout";
import { deSnake, presentValue } from "../../desk/surface/format";

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
      {renderHeroSlot(
        hero,
        verbs,
        <LampGadget
          on
          tone={
            resource.data.overall === "ready"
              ? "ok"
              : resource.data.overall === "blocked"
                ? "fail"
                : "warn"
          }
          label={deSnake(String(resource.data.overall ?? "")) || "checking"}
        />,
      )}
      <CoreResourceGuard resource={resource}>
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
                        <LampGadget
                          on
                          tone={
                            status === "pass"
                              ? "ok"
                              : status === "fail"
                                ? "fail"
                                : "warn"
                          }
                          label={status}
                        />
                      }
                    />
                  );
                })}
              </SurfaceRows>
              {!sections.length ? (
                <SurfaceState empty emptyLabel="No readiness checks reported" />
              ) : null}
              {testResult ? (
                testResult.ok ? (
                  <p
                    className="surface-receipt-line"
                    data-tone="ok"
                    role="status"
                  >
                    ✓ {testResult.detail}
                  </p>
                ) : (
                  <SurfaceState
                    error={testResult.detail}
                    onRetry={() => void testRuntime()}
                  />
                )
              ) : null}
            </SurfaceSection>
          }
          side={
            <SurfaceSection label="Next step">
              <p>
                {resource.data.first_run
                  ? "Run one dictation to verify"
                  : "Ready"}
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
      </CoreResourceGuard>
      <SurfaceFooter />
    </>
  );
}
