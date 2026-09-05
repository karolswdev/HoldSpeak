/** HS-101 B4 — Blocks reads like a library: the injection text IS
 * the tile's face, the name and spoken matches ride the spine,
 * create is a ghost tile in the shelf. Edits land on the material.
 * HS-111-02 — cosmetic refit: mono tile names, CycleGadget scope,
 * mics on every draft input, refusals in the footer bar. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { asRows, rowId, useResource } from "../../pageSupport";
import type { DictationBlocksResponse } from "../core-types";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceLibrary,
  SurfaceLibraryGhost,
  SurfaceLibraryTile,
  SurfaceSection,
  SurfaceState,
} from "../../../desk/surface/Surface";
import { countToken } from "../../../desk/surface";
import {
  CycleGadget,
  PadGadget,
  StringGadget,
} from "../../../desk/surface/gadgets";
import { useAnnounce } from "./shared";

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
  return (
    <SurfaceSection className="speak-blocks">
      <SurfaceLibrary
        count={rows.length || undefined}
        countLabel={countToken(rows.length, "BLOCK") ?? undefined}
        controls={
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
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          onRetry={() => void resource.reload()}
        >
          {rows.map((row, index) => {
            const match =
              row.match && typeof row.match === "object"
                ? (row.match as Record<string, unknown>)
                : {};
            const examples = Array.isArray(match.examples)
              ? match.examples
              : [];
            const inject =
              row.inject && typeof row.inject === "object"
                ? (row.inject as Record<string, unknown>)
                : {};
            const mode = String(inject.mode ?? "replace");
            return (
              <SurfaceLibraryTile
                key={rowId(row, index)}
                face={
                  <EditInPlace
                    value={String(inject.template ?? "")}
                    label={`${String(row.description ?? "Block")} template`}
                    multiline
                    onCommit={(next) =>
                      void save(row, { inject: { ...inject, template: next } })
                    }
                  />
                }
                name={
                  <EditInPlace
                    value={String(row.description ?? row.id ?? "Block")}
                    label={`${String(row.description ?? "Block")} name`}
                    onCommit={(next) => void save(row, { description: next })}
                  />
                }
                lamp={<span className="surface-mode">{mode}</span>}
                says={
                  examples.length
                    ? examples.slice(0, 3).map((say, sayIndex) => (
                        <span className="surface-say" key={sayIndex}>
                          {String(say)}
                        </span>
                      ))
                    : null
                }
                verbs={
                  <ConfirmVerb
                    label="Delete"
                    confirmLabel="Delete?"
                    onConfirm={() => void remove(row)}
                  />
                }
              />
            );
          })}
          {drafting ? (
            <li className="surface-tile surface-tile-drafting">
              <div className="surface-tile-face">
                <div className="desk-mic-row">
                  <PadGadget
                    label="Injection text"
                    placeholder="What this block injects"
                    rows={4}
                    value={draft.injection}
                    onChange={(next) =>
                      setDraft({ ...draft, injection: next })
                    }
                  />
                </div>
              </div>
              <div className="surface-tile-spine">
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
            </li>
          ) : (
            <SurfaceLibraryGhost
              label="New block"
              hint={
                rows.length ? undefined : "No routing blocks on this scope yet"
              }
              onCreate={() => setDrafting(true)}
            />
          )}
        </SurfaceState>
      </SurfaceLibrary>
    </SurfaceSection>
  );
}
