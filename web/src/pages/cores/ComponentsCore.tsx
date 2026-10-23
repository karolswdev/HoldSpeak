import type { CoreProps } from "./core-types";
import { DesignReference } from "./design-reference/DesignReference";

/**
 * The Components window is the in-desk reference for composing real HoldSpeak
 * surfaces. Its examples keep their state in this window and never call a
 * connector or the engine.
 */
export function ComponentsCore({ hero }: CoreProps) {
  return <DesignReference hero={hero} />;
}

export { DesignReference } from "./design-reference/DesignReference";
