/** HS-101 B4 — Blocks reads like a library: the injection text IS
 * the tile's face, the name and spoken matches ride the spine,
 * create is a ghost tile in the shelf. Edits land on the material.
 * HS-111-02 — cosmetic refit: mono tile names, CycleGadget scope,
 * mics on every draft input, refusals in the footer bar.
 * Lane speak (2026-10-25): the library became a dense list window (the
 * window grammar): toolbar, one 30 px row per block, an in-place open. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { asRows, rowId, useResource } from "../../pageSupport";
import type { DictationBlocksResponse } from "../core-types";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
} from "../../../desk/surface/Surface";
import { ToolGlyph, Toolbar } from "../../../desk/surface/kit";
import { SpeakEmpty } from "./SpeakEmpty";
import { useWindowInterior } from "../../../desk/surface/interior";
import {
  CycleGadget,
  PadGadget,
  StringGadget,
} from "../../../desk/surface/gadgets";
import { useAnnounce } from "./shared";

/** How a block injects, in plain words (the wire's `inject.mode`). */
const MODE_WORDS: Record<string, string> = {
  replace: "Replaces",
  append: "Adds after",
  prepend: "Adds before",
};

function blockSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function Blocks() {
  const announce = useAnnounce();
  const [scope, setScope] = useState("global");
  const resource = useResource<DictationBlocksResponse>(
    `/api/dictation/blocks?scope=${scope}`,
    {},
  );
  const rows = asRows(
    (resource.data.document as Record<string, unknown> | undefined)?.blocks,
    [],
  );
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState({ name: "", examples: "", injection: "" });
  const save = async (row: Record<string, unknown>, patch: Record<string, unknown>) => {
    try {
      await apiFetch(
        `/api/dictation/blocks/${encodeURIComponent(String(row.id))}?scope=${scope}`,
        { method: "PUT", json: { block: { ...row, ...patch } } },
      );
      await resource.reload();
    } catch (error) {
      announce(readableError(error), "warn");
    }
  };
  const remove = async (row: Record<string, unknown>) => {
    try {
      await apiFetch(
        `/api/dictation/blocks/${encodeURIComponent(String(row.id))}?scope=${scope}`,
        { method: "DELETE" },
      );
      await resource.reload();
    } catch (error) {
      announce(readableError(error), "warn");
    }
  };
  const create = async () => {
    const name = draft.name.trim();
    if (!name) return;
    try {
      await apiFetch(`/api/dictation/blocks?scope=${scope}`, {
        method: "POST",
        json: {
          block: {
            id: blockSlug(name),
            description: name,
            match: {
              examples: draft.examples
                .split(/[,\n]/)
                .map((part) => part.trim())
                .filter(Boolean),
            },
            inject: { mode: "replace", template: draft.injection },
          },
        },
      });
      setDraft({ name: "", examples: "", injection: "" });
      setDrafting(false);
      await resource.reload();
    } catch (error) {
      announce(readableError(error), "warn");
    }
  };
  // Lane speak (2026-10-25): the wing is a list window — a toolbar (New
  // block · the scope at the right), then one dense row per block (name ·
  // what he says · how it injects), edge to edge. A row opens in place to
  // edit the name and the template; Delete is the row's verb.
  useWindowInterior("list");
  const [openId, setOpenId] = useState("");
  return (
    <SurfaceSection className="speak-blocks">
      <Toolbar
        label="Blocks"
        data-testid="blocks-toolbar"
        trailing={
          <CycleGadget
            label="Block scope"
            value={scope}
            options={[
              { value: "global", label: "Global" },
              { value: "project", label: "Project" },
            ]}
            onChange={setScope}
          />
        }
      >
        <Button dense variant="secondary" disabled={drafting} onClick={() => setDrafting(true)}>
          <ToolGlyph kind="new" />
          New block
        </Button>
      </Toolbar>
      {drafting ? (
        <div className="blocks-draft" role="group" aria-label="New block">
          <StringGadget
            label="Block name"
            placeholder="Name"
            value={draft.name}
            onChange={(name) => setDraft({ ...draft, name })}
          />
          <StringGadget
            label="Spoken matches, comma separated"
            placeholder="Say: standup notes, stand up"
            value={draft.examples}
            onChange={(examples) => setDraft({ ...draft, examples })}
          />
          <div className="desk-mic-row">
            <PadGadget
              label="Injection text"
              placeholder="What this block injects"
              rows={3}
              value={draft.injection}
              onChange={(next) => setDraft({ ...draft, injection: next })}
            />
          </div>
          <div className="surface-actions">
            <Button
              dense
              variant="primary"
              disabled={!draft.name.trim()}
              onClick={() => void create()}
            >
              Create
            </Button>
            <Button dense variant="ghost" onClick={() => setDrafting(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : null}
      <SurfaceLedger cols="blocks">
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          empty={!rows.length && !drafting}
          emptyLabel="No blocks yet"
          emptyContent={<SpeakEmpty label="No blocks yet" hint="Say the name of a block to type its saved text" />}
          onRetry={() => void resource.reload()}
        >
          <ul className="surface-ledger-rows">
            {rows.map((row, index) => {
              const id = String(row.id ?? rowId(row, index));
              const match =
                row.match && typeof row.match === "object"
                  ? (row.match as Record<string, unknown>)
                  : {};
              const examples = Array.isArray(match.examples)
                ? match.examples.map(String)
                : [];
              const inject =
                row.inject && typeof row.inject === "object"
                  ? (row.inject as Record<string, unknown>)
                  : {};
              const mode = String(inject.mode ?? "replace");
              const name = String(row.description ?? row.id ?? "Block");
              return (
                <SurfaceLedgerRow
                  key={id}
                  primary={name}
                  open={openId === id}
                  onToggle={() => setOpenId(openId === id ? "" : id)}
                  cells={
                    <span className="blocks-cells">
                      {examples.length ? (
                        <span className="blocks-says">Say “{examples.slice(0, 3).join("”, “")}”</span>
                      ) : null}
                      <span className="blocks-mode">{MODE_WORDS[mode] ?? mode}</span>
                    </span>
                  }
                  trailing={
                    <ConfirmVerb
                      label="Delete"
                      confirmLabel="Delete?"
                      onConfirm={() => void remove(row)}
                    />
                  }
                >
                  <div className="blocks-open">
                    <EditInPlace
                      value={name}
                      label={`${name} name`}
                      onCommit={(next) => void save(row, { description: next })}
                    />
                    <EditInPlace
                      value={String(inject.template ?? "")}
                      label={`${name} template`}
                      multiline
                      onCommit={(next) =>
                        void save(row, { inject: { ...inject, template: next } })
                      }
                    />
                  </div>
                </SurfaceLedgerRow>
              );
            })}
          </ul>
        </SurfaceState>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
