import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../../lib/api";
import { type OwnerNameAdapter, type OwnerSetting } from "../../../desk/firstrun/ownerName";
import { StateChip } from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import { OwnerNameFields, ownerSaveState, useOwnerPreferences } from "../settingsPeople";
import { SETTINGS_SECTIONS, SettingsRailGlyph } from "../settingsPrefs";
import { PrefSection, PrefStatus, PrefWindow } from "../settingsWindow";

export type OwnerPreferencesState = "saved" | "edited" | "saving" | "refused" | "retried" | "newer";

/** Only this local adapter can acknowledge the Components specimen. No API,
 * config, key store, or microphone is touched by its read or write methods. */
function createFixtureAdapter(state: OwnerPreferencesState, onPending: (pending: boolean) => void) {
  let stored: OwnerSetting = { name: "Karol", aliases: ["Carol"] };
  let revision = 1;
  let writes = 0;
  let pending: { owner: OwnerSetting; resolve: (value: Awaited<ReturnType<OwnerNameAdapter["write"]>>) => void } | null = null;
  const acknowledge = (owner: OwnerSetting) => {
    stored = { name: owner.name, aliases: [...owner.aliases] };
    revision += 1;
    return { settings: { owner: stored, _revision: `fixture-${revision}` } };
  };
  const adapter: OwnerNameAdapter = {
    read: async () => ({ owner: { ...stored, aliases: [...stored.aliases] }, _revision: `fixture-${revision}` }),
    write: async (owner) => {
      writes += 1;
      // Two revision refusals exhaust the writer's bounded automatic retry.
      // Its visible Retry then reads the current draft and succeeds locally.
      if ((state === "refused" || state === "retried") && writes <= 2) {
        throw new ApiError(409, "Revision changed", { revision: `fixture-${revision + writes}` });
      }
      if ((state === "saving" || state === "newer") && writes === 1) {
        return new Promise((resolve) => {
          pending = { owner: { name: owner.name, aliases: [...owner.aliases] }, resolve };
          onPending(true);
        });
      }
      return acknowledge(owner);
    },
  };
  return {
    adapter,
    complete: () => {
      if (!pending) return;
      const captured = pending;
      pending = null;
      onPending(false);
      captured.resolve(acknowledge(captured.owner));
    },
  };
}

function OwnerPreferencesSpecimen({ state }: { state: OwnerPreferencesState }) {
  const [pending, setPending] = useState(false);
  const [fixture] = useState(() => createFixtureAdapter(state, setPending));
  const prefs = useOwnerPreferences(fixture.adapter);
  const { owner } = prefs;
  const started = useRef(false);
  const [paneOpen, setPaneOpen] = useState(true);

  useEffect(() => {
    if (owner.loading || owner.readError || started.current) return;
    started.current = true;
    if (state === "saved") return;
    owner.setName("Karol A");
    if (state === "edited") return; // The real 600 ms autosave advances this case.
    if (state === "retried") {
      void owner.flush().then(() => owner.flush());
      return;
    }
    void owner.flush();
    if (state === "newer") owner.setName("Karol B");
  }, [owner, started, state]);

  // The same rail as Settings; only You has a local writer here.
  const rail = SETTINGS_SECTIONS.map((section) => ({
    id: section.id,
    label: section.label,
    glyph: <SettingsRailGlyph section={section} />,
    disabled: section.id !== "you",
  }));
  return (
    <section className="reference-example" data-testid="reference-owner-preferences" aria-label="Settings You pattern">
      <div className="reference-example-head">
        <h2>Settings · You</h2>
        <StateChip state="idle" label="PROPOSED" />
      </div>
      {pending ? (
        <div className="reference-actions">
          <Button variant="secondary" onClick={fixture.complete}>Complete local write</Button>
        </div>
      ) : null}
      <div className="reference-pref-window">
        <PrefWindow
          items={rail}
          selected="you"
          onSelect={() => setPaneOpen(true)}
          paneOpen={paneOpen}
          onBack={() => setPaneOpen(false)}
          label="Settings sections (specimen)"
          railTestIdPrefix="reference-settings-index-"
        >
          <PrefSection id="you" label="You" quiet>
            <h3 className="reference-accessible-heading">You fields</h3>
            <OwnerNameFields prefs={prefs} mic={false} />
          </PrefSection>
        </PrefWindow>
        <PrefStatus
          inline
          save={ownerSaveState(prefs)}
          facts={["Local specimen"]}
          onRetry={prefs.state === "Not saved" ? () => void owner.flush() : undefined}
        />
      </div>
    </section>
  );
}

export function OwnerPreferencesReference({ state }: { state: OwnerPreferencesState }) {
  // A preset change starts with a fresh local revision and a fresh real hook.
  return <OwnerPreferencesSpecimen key={state} state={state} />;
}
