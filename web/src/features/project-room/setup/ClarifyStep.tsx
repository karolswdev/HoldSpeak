// HS-159-05 -- bounded clarify step (INT-009): cadence preset picker,
// action choice, scope narrowing.  No unbounded chat.

import { useCallback, useState } from "react";
import {
  CADENCE_PRESETS,
  ACTION_LABELS,
  cadenceLabel,
  type CadencePresetKey,
  type SetupProposal,
} from "./model";

const CADENCE_KEYS: CadencePresetKey[] = [
  "active_work",
  "normal",
  "daily",
  "weekdays",
];

const ACTION_KINDS = [
  "project.observe",
  "project.update.draft",
  "door.add_item",
  "project.steward.run_once",
] as const;

export function ClarifyStep({
  proposal,
  onClarify,
  onDone,
}: {
  proposal: SetupProposal;
  onClarify: (
    proposalId: string,
    patch: { cadence?: CadencePresetKey; action?: string },
  ) => void;
  onDone: () => void;
}) {
  const [cadence, setCadence] = useState<CadencePresetKey | null>(null);
  const [action, setAction] = useState(proposal.spec.action.kind);

  const handleCadenceChange = useCallback(
    (key: CadencePresetKey) => {
      setCadence(key);
      onClarify(proposal.id, { cadence: key });
    },
    [proposal.id, onClarify],
  );

  const handleActionChange = useCallback(
    (kind: string) => {
      setAction(kind);
      onClarify(proposal.id, { action: kind });
    },
    [proposal.id, onClarify],
  );

  return (
    <div className="setup-clarify" data-testid="setup-clarify">
      <h3 className="setup-clarify-heading">
        Configure: {proposal.spec.name}
      </h3>

      {/* Cadence picker */}
      <fieldset className="setup-clarify-section">
        <legend className="setup-clarify-legend">
          How closely should HoldSpeak watch this?
        </legend>
        <div className="setup-clarify-options" role="radiogroup">
          {CADENCE_KEYS.map((key) => {
            const preset = CADENCE_PRESETS[key];
            const isActive =
              cadence === key ||
              (!cadence && proposal.spec.trigger.everyMinutes === preset.minutes);
            return (
              <label
                key={key}
                className="setup-clarify-option"
                data-active={isActive || undefined}
              >
                <input
                  type="radio"
                  name="cadence"
                  value={key}
                  checked={isActive}
                  onChange={() => handleCadenceChange(key)}
                />
                <span className="setup-clarify-option-label">
                  {preset.label}
                </span>
                <span className="setup-clarify-option-detail">
                  Every {preset.minutes < 60 ? `${preset.minutes} min` : `${Math.round(preset.minutes / 60)} hr`}
                  {preset.weekdaysOnly ? ", weekdays" : ""}
                </span>
              </label>
            );
          })}
        </div>
        <div className="setup-clarify-current">
          Current: {cadenceLabel(proposal.spec.trigger)}
        </div>
      </fieldset>

      {/* Action choice */}
      <fieldset className="setup-clarify-section">
        <legend className="setup-clarify-legend">
          When this happens, what should HoldSpeak do?
        </legend>
        <div className="setup-clarify-options" role="radiogroup">
          {ACTION_KINDS.map((kind) => (
            <label
              key={kind}
              className="setup-clarify-option"
              data-active={action === kind || undefined}
            >
              <input
                type="radio"
                name="action"
                value={kind}
                checked={action === kind}
                onChange={() => handleActionChange(kind)}
              />
              <span className="setup-clarify-option-label">
                {ACTION_LABELS[kind]}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <button
        type="button"
        className="setup-clarify-done"
        onClick={onDone}
      >
        Done
      </button>
    </div>
  );
}
