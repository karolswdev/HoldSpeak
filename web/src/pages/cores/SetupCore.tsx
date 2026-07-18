// HS-95-07 — the Setup core: readiness truth, hosted anywhere.
import { useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  InlineMessage,
  Panel,
  StatusPill,
} from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { ResourceState, asRows, useResource } from "../pageSupport";

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

  return (
    <>
      {hero ? hero(null) : null}
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <div className="page-grid">
          <Panel
            className="span-8"
            title={
              resource.data.overall === "ready"
                ? "Everything is ready"
                : "Readiness checks"
            }
            eyebrow="System"
            actions={
              <StatusPill
                tone={
                  resource.data.overall === "ready"
                    ? "success"
                    : resource.data.overall === "blocked"
                      ? "error"
                      : "warning"
                }
              >
                {resource.data.overall ?? "unknown"}
              </StatusPill>
            }
          >
            <ul className="data-list">
              {sections.map((section, index) => {
                const status = String(section.status ?? "unknown");
                return (
                  <li className="data-row" key={String(section.id ?? index)}>
                    <div>
                      <strong>
                        {String(
                          section.label ??
                            section.name ??
                            section.id ??
                            "Check",
                        )}
                      </strong>
                      <small>
                        {String(section.detail ?? section.description ?? "")}
                      </small>
                    </div>
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
                  </li>
                );
              })}
            </ul>
            {!sections.length ? (
              <InlineMessage tone="warning">
                The hub did not report individual readiness checks.
              </InlineMessage>
            ) : null}
            <div className="button-row">
              <Button variant="primary" loading={testing} onClick={testRuntime}>
                Test runtime
              </Button>
              <Button variant="ghost" onClick={() => void resource.reload()}>
                Refresh
              </Button>
            </div>
            {testResult ? (
              <InlineMessage tone={testResult.ok ? "success" : "error"}>
                {testResult.detail}
              </InlineMessage>
            ) : null}
          </Panel>
          <Panel className="span-4" title="Next step" eyebrow="Path">
            <p>
              {resource.data.first_run
                ? "Try one real dictation when the required checks pass."
                : "Your first dictation is complete. The Desk is ready."}
            </p>
            <div className="button-row">
              <button
                type="button"
                className="btn btn--primary"
                onClick={() =>
                  openSurfaceOr(
                    resource.data.first_run ? "arrival" : "return-to-desk",
                    resource.data.first_run ? "/welcome" : "/",
                  )
                }
              >
                {resource.data.first_run ? "Continue arrival" : "Open Desk"}
              </button>
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => openSurfaceOr("configure-runs-on", "/profiles")}
              >
                Runs on
              </button>
            </div>
          </Panel>
        </div>
      </ResourceState>
    </>
  );
}
