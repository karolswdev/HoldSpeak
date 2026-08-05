import type { Primitive, PrimitiveKind } from "../lib/primitives";
import type { Items } from "./api";
import { qualifiedRef } from "./api";
import type { TrustDestination } from "./setup";
import { allObjects, type WorldObject } from "./world";

export interface SelectedMaterial {
  id: string;
  ref: string;
  kind: PrimitiveKind;
  title: string;
  text: string;
  object: WorldObject;
}

export interface ContextualCapabilityAction {
  id: string;
  kind: "recipe" | "chain" | "workflow";
  label: string;
  input: string;
  selected: SelectedMaterial[];
}

export interface ContextualIntegrationAction {
  id: "slack" | "companion_webhook" | "github";
  label: string;
  destination: TrustDestination;
  source: SelectedMaterial;
}

export interface ContextualCoderAction {
  id: string;
  label: string;
  session: Primitive;
  source: SelectedMaterial;
}

const CAPABILITY_KINDS = new Set<PrimitiveKind>(["recipe", "chain", "workflow"]);
const TEXT_MATERIAL_KINDS = new Set<PrimitiveKind>(["note", "artifact"]);
const INTEGRATION_IDS = new Set(["slack", "companion_webhook", "github"]);

function selectionMatches(object: WorldObject, selected: string): boolean {
  return (
    selected === object.id || selected === qualifiedRef(object.kind, object.id)
  );
}

function materialText(item: Primitive): string {
  return String("bodyMarkdown" in item ? item.bodyMarkdown : "").trim();
}

export function selectedMaterials(
  items: Items,
  selectedIds: string[],
): SelectedMaterial[] {
  const objects = allObjects(items);
  const result: SelectedMaterial[] = [];
  for (const selected of selectedIds) {
    const object = objects.find((candidate) =>
      selectionMatches(candidate, selected),
    );
    if (!object || !TEXT_MATERIAL_KINDS.has(object.kind)) continue;
    const text = materialText(object.ref);
    if (!text) continue;
    result.push({
      id: object.id,
      ref: qualifiedRef(object.kind, object.id),
      kind: object.kind,
      title: object.title,
      text,
      object,
    });
  }
  return result;
}

export function selectedMaterialInput(selected: SelectedMaterial[]): string {
  return selected
    .map((material) => `## ${material.title}\n${material.text}`)
    .join("\n\n");
}

export function contextualCapabilityActions(
  items: Items,
  selectedIds: string[],
): ContextualCapabilityAction[] {
  const selected = selectedMaterials(items, selectedIds);
  if (!selected.length) return [];
  const input = selectedMaterialInput(selected);
  return allObjects(items)
    .filter((object) => CAPABILITY_KINDS.has(object.kind))
    .filter((object) => {
      const ref = object.ref;
      const capability = ("capability" in ref ? ref.capability : null) as Record<string, unknown> | null | undefined;
      if (!capability || typeof capability !== "object") return false;
      const readiness = capability.readiness as Record<string, unknown> | undefined;
      const inputSchema = capability.input_schema as Record<string, unknown> | undefined;
      const effectClasses = capability.effect_classes as string[] | undefined;
      return (
        readiness?.state === "ready" &&
        Array.isArray(inputSchema?.required) && (inputSchema?.required as string[]).includes("input") &&
        Array.isArray(effectClasses) && effectClasses.includes("creates_artifact")
      );
    })
    .map((object) => ({
      id: object.id,
      kind: object.kind as "recipe" | "chain" | "workflow",
      label:
        object.kind === "recipe"
          ? `Ask ${object.title} about ${selected.length === 1 ? selected[0].title : `${selected.length} items`}`
          : `Run ${object.title} on ${selected.length === 1 ? selected[0].title : `${selected.length} items`}`,
      input,
      selected,
    }));
}

export function contextualIntegrationActions(
  destinations: TrustDestination[],
  items: Items,
  selectedIds: string[],
): ContextualIntegrationAction[] {
  const selected = selectedMaterials(items, selectedIds);
  if (selected.length !== 1) return [];
  return destinations
    .filter(
      (
        destination,
      ): destination is TrustDestination & {
        id: ContextualIntegrationAction["id"];
      } => destination.enabled && INTEGRATION_IDS.has(destination.id),
    )
    .map((destination) => ({
      id: destination.id,
      label:
        destination.id === "github"
          ? `Create GitHub issue from ${selected[0].title}`
          : destination.id === "slack"
            ? `Send ${selected[0].title} to Slack`
            : `Post ${selected[0].title} to Custom webhook`,
      destination,
      source: selected[0],
    }));
}

export function contextualCoderSessions(
  items: Items,
  selectedIds: string[],
): ContextualCoderAction[] {
  const selected = selectedMaterials(items, selectedIds);
  if (selected.length !== 1) return [];
  return items.coder
    .filter(
      (session) => session.state === "waiting" || Boolean(session.question),
    )
    .map((session) => {
      const target = String(session.title || session.project || "").trim();
      return {
        id: session.id,
        label: `Send ${selected[0].title} to ${target ? `${target} Coder session` : "Coder session"}`,
        session: session as Primitive,
        source: selected[0],
      };
    });
}
