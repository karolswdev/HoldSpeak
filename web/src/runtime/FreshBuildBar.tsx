// The face of runtime/freshBuild.ts: a one-line kit StatusBar at the foot of
// the screen while a new desk build reloads the tab, or a Reload Button when
// an unsaved edit holds the reload back. Nothing draws while the build is the
// same.
import { useEffect, useRef, useState } from "react";
import { Button } from "../components/signal/Signal";
import { StatusBar } from "../desk/surface/kit";
import { stateWords } from "../desk/surface/words";
import { useOptionalRuntimeBus } from "./RuntimeBus";
import { type FreshBuild, type FreshBuildPhase, startFreshBuild } from "./freshBuild";
import "./freshBuild.css";

export function FreshBuildBar() {
  const [phase, setPhase] = useState<FreshBuildPhase>("idle");
  const fresh = useRef<FreshBuild | null>(null);
  const bus = useOptionalRuntimeBus();
  const state = bus?.state;
  const wasDown = useRef(false);

  useEffect(() => {
    fresh.current = startFreshBuild(setPhase);
  }, []);

  // The bus came back after a drop: the hub restarted, maybe on a new build.
  useEffect(() => {
    if (state === "reconnecting" || state === "offline") wasDown.current = true;
    else if (state === "connected" && wasDown.current) {
      wasDown.current = false;
      void fresh.current?.check();
    }
  }, [state]);

  if (phase === "idle") return null;
  return (
    <div className="fresh-build" data-testid="fresh-build">
      <StatusBar
        items={[
          {
            key: "build",
            lamp: "info",
            text: stateWords(phase === "reloading" ? "New desk build: reloading…" : "New desk build"),
          },
        ]}
        verbs={
          phase === "offer" ? (
            <Button dense onClick={() => fresh.current?.reloadNow()} data-testid="fresh-build-reload">
              Reload
            </Button>
          ) : undefined
        }
      />
    </div>
  );
}
