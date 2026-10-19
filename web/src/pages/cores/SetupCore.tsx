import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-95-07 — the Setup core: readiness truth, hosted anywhere.
// HS-98-05 — re-crafted native on the surface kit; wire calls unchanged.
import { useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { openFirstRun } from "../../desk/firstrun/reopen";
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
import { SpeechSetup, useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { RuntimeDocsCore, sortChecks } from "./RuntimeDocsCore";
import { SetupFace, useSetupInventory } from "../../desk/firstrun/SetupFace";

/** The doctor's "Speech model" check (holdspeak/commands/doctor.py). */
const SPEECH_SECTION = "speech-model";

export { sortChecks } from "./RuntimeDocsCore";

/** Parked duplicate body. Setup and the compatibility route now use Guide. */
export function ParkedSetupCore({ hero }: CoreProps) {
  const resource = useResource<SetupStatus>("/api/setup/status", {});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    ok: boolean;
    detail: string;
  } | null>(null);
  // PHILO-17 U19: the face leads with what fails. A failing check comes
  // first, then a warning, then the rest in the doctor's order.
  const sections = sortChecks(asRows(resource.data.sections, []));
  // PHILO-17 speech: the speech row carries its one verb, the same download
  // the first-run page runs.
  const speech = useSpeechSetup();
  const reload = resource.reload;

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
                          on={status !== "info"}
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
                    >
                      {section.id === SPEECH_SECTION && status === "fail" ? (
                        <SpeechSetup
                          setup={speech}
                          bare
                          primary={false}
                          onReady={() => void reload()}
                          testId="setup-speech-setup"
                        />
                      ) : null}
                    </SurfaceRow>
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
                    {testResult.detail}
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
                {/* PHILO-17 U17: Get ready opens the SAME first-run cards
                    the fresh desk shows (was "Continue arrival" to /welcome).
                    "Open Desk" left: no surface answered "return-to-desk" and
                    this window is already on the desk (a dead verb). */}
                <Button
                  variant={resource.data.first_run ? "primary" : "secondary"}
                  dense
                  onClick={openFirstRun}
                >
                  Get ready
                </Button>
                <Button
                  dense
                  variant="ghost"
                  onClick={() =>
                    openSurfaceOr("configure-runs-on", "/profiles")
                  }
                >
                  Engines
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

export function SetupCore(props: CoreProps) {
  const setup = useSetupInventory();
  if (setup.loading && !setup.inventory) return <SurfaceState loading />;
  if (setup.error && !setup.inventory) {
    return <SurfaceState error={setup.error} onRetry={() => void setup.reload()} />;
  }
  if (!setup.inventory) {
    return <SurfaceState error="Setup could not be read." onRetry={() => void setup.reload()} />;
  }
  return <SetupFace initial={setup.inventory} />;
}
