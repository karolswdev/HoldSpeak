import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { FoldGadget, StateChip, SurfaceRow, SurfaceRows, SurfaceState } from "../surface";

type Check = { id: string; status: string; detail?: string };

/** The existing doctor's microphone read, on the owner's request. */
export function SetupMicrophoneCheck({ requested }: { requested: number }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [check, setCheck] = useState<Check | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      const answer = await apiFetch<{ sections?: Check[] }>("/api/setup/status");
      const microphone = answer.sections?.find((row) => row.id === "microphone");
      if (!microphone) throw new Error("Microphone check was not returned.");
      setCheck(microphone);
    } catch (failure) {
      setError(readableError(failure));
    } finally {
      setBusy(false);
    }
  }, []);
  useEffect(() => {
    if (requested) {
      setOpen(true);
      void load();
    }
  }, [requested, load]);
  return (
    <FoldGadget title="Microphone" open={open} onToggle={(next) => {
      setOpen(next);
      if (next && !requested && !check && !busy && !error) void load();
    }}>
      {busy ? <SurfaceState loading /> : error ? <SurfaceState error={error} onRetry={() => void load()} /> : check ? (
        <SurfaceRows>
          <SurfaceRow title="Microphone" detail={check.detail} meta={
            <StateChip
              state={check.status === "pass" ? "success" : check.status === "fail" ? "failure" : "idle"}
              label={check.status === "pass" ? "Works" : check.status === "fail" ? "Does not work" : "Check"}
            />
          } verbs={<Button dense variant="secondary" onClick={() => void load()}>Check again</Button>} />
        </SurfaceRows>
      ) : null}
    </FoldGadget>
  );
}
