/* HS-102-06 — Knowledge is `{kb: {<KEY>: <string|null>, ...}}`
   (`/api/dictation/project-kb`, validated `[A-Za-z_][A-Za-z0-9_]*`
   keys) — a facts glossary, not free text. HS-111-02: the glossary is
   a GadgetTable (KEY | VALUE, EditInPlace values, ghost +ADD row of
   StringGadgets — mics included by the kit); the key refusal and the
   save whisper land in the footer bar. Instructions binds to the
   primary `.hs/instructions.md` file. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { useResource } from "../../pageSupport";
import type {
  DictationProjectKbResponse,
  DictationProjectHsResponse,
} from "../core-types";
import {
  ConfirmVerb,
  EditInPlace,
} from "../../../desk/surface/Surface";
import {
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  StringGadget,
} from "../../../desk/surface/gadgets";
import { clockNow, useAnnounce } from "./shared";

export function Knowledge() {
  const announce = useAnnounce();
  const [root, setRoot] = useState(
    () => localStorage.getItem("holdspeak.projectRootOverride") ?? "",
  );
  const query = root ? `?project_root=${encodeURIComponent(root)}` : "";
  const kb = useResource<DictationProjectKbResponse>(`/api/dictation/project-kb${query}`, {});
  const hs = useResource<DictationProjectHsResponse>(`/api/dictation/project-hs${query}`, {});
  const [drafting, setDrafting] = useState(false);
  const [draftKey, setDraftKey] = useState("");
  const [draftValue, setDraftValue] = useState("");
  const kbFacts = (kb.data.kb ?? {}) as Record<string, unknown>;
  const kbEntries = Object.entries(kbFacts);
  const instructionsFile = (
    ((hs.data.files ?? {}) as Record<string, unknown>)["instructions.md"] ?? {}
  ) as Record<string, unknown>;
  const putKb = async (next: Record<string, unknown>) => {
    announce("Saving…");
    try {
      await apiFetch(`/api/dictation/project-kb${query}`, {
        method: "PUT",
        json: { kb: next },
      });
      announce(`Written ${clockNow()}`);
      await kb.reload();
    } catch (error) {
      announce(readableError(error), "warn");
    }
  };
  const setFact = (key: string, value: string) =>
    void putKb({ ...kbFacts, [key]: value });
  const forgetFact = (key: string) => {
    const next = { ...kbFacts };
    delete next[key];
    void putKb(next);
  };
  const addFact = () => {
    const key = draftKey.trim();
    if (!key || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
      announce("REFUSED · key format A-Z _ 0-9, letter first", "warn");
      return;
    }
    void putKb({ ...kbFacts, [key]: draftValue.trim() });
    setDraftKey("");
    setDraftValue("");
    setDrafting(false);
  };
  const saveInstructions = async (content: string) => {
    announce("Saving…");
    try {
      await apiFetch(`/api/dictation/project-hs${query}`, {
        method: "PUT",
        json: { files: { "instructions.md": content } },
      });
      announce(`Written ${clockNow()}`);
      await hs.reload();
    } catch (error) {
      announce(readableError(error), "warn");
    }
  };
  return (
    <>
      <GadgetGroup label="Project scope">
        <GadgetRow label="Project root">
          <StringGadget
            label="Project root"
            placeholder="this device's working directory"
            value={root}
            onChange={setRoot}
          />
          <Button
            dense
            onClick={() => {
              localStorage.setItem("holdspeak.projectRootOverride", root);
              void kb.reload();
              void hs.reload();
            }}
          >
            Use
          </Button>
        </GadgetRow>
      </GadgetGroup>
      <GadgetGroup label="Knowledge">
        <GadgetTable
          head={["Key", "Value"]}
          rows={kbEntries.map(([key, value]) => [
            key,
            <EditInPlace
              key={key}
              value={String(value ?? "") || "(empty) click to add"}
              label={`${key} value`}
              onCommit={(next) => setFact(key, next)}
            />,
          ])}
          verbs={(index) => (
            <ConfirmVerb
              label="×"
              confirmLabel="Forget?"
              onConfirm={() => forgetFact(kbEntries[index][0])}
            />
          )}
          onAdd={drafting ? undefined : () => setDrafting(true)}
        />
        {drafting ? (
          <div className="surface-actions">
            <StringGadget
              label="Fact name"
              placeholder="BLUEBIRD"
              value={draftKey}
              onChange={setDraftKey}
            />
            <StringGadget
              label="Fact value"
              placeholder="the codename for…"
              value={draftValue}
              onChange={setDraftValue}
            />
            <Button
              dense
              variant="primary"
              disabled={!draftKey.trim()}
              onClick={addFact}
            >
              Add
            </Button>
            <Button
              dense
              variant="ghost"
              onClick={() => {
                setDrafting(false);
                setDraftKey("");
                setDraftValue("");
              }}
            >
              Cancel
            </Button>
          </div>
        ) : null}
      </GadgetGroup>
      <GadgetGroup label="Instructions">
        <EditInPlace
          value={
            String(instructionsFile.content ?? "") ||
            "No instructions yet. Click to add."
          }
          label="Project instructions"
          multiline
          onCommit={(next) => void saveInstructions(next)}
        />
      </GadgetGroup>
    </>
  );
}
