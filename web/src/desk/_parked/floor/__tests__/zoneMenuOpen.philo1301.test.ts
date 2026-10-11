/** PHILO-13-01 B0-F7 — the Zone context menu resolves its own Zone.
 * The menu built a `directory:<id>` ref; objectByRef knows only the raw
 * id and the canonical `zone:<id>`, so Open, Get Info and Focus stayed
 * disabled ("Select an object") on every real Zone. */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { zoneMenuEntries } from "../floorMenu";
import { EMPTY_ITEMS } from "../api";

describe("zone context menu", () => {
  beforeEach(() => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        directory: [{ id: "dir-1", name: "Atlas Phase 13 Zone", memberIds: [] }],
      } as never,
    });
  });

  it("offers Open, Get Info and Focus for a real Zone", () => {
    const entries = zoneMenuEntries(
      { type: "zone", id: "dir-1", title: "Atlas Phase 13 Zone" } as never,
      { x: 10, y: 20 },
    );
    const byId = Object.fromEntries(
      entries.map((e) => [(e as { id: string }).id, e as { ghost: string | null }]),
    );
    expect(byId["object.open"].ghost).toBeNull();
    expect(byId["object.info"].ghost).toBeNull();
    expect(byId["zone.focus"].ghost).toBeNull();
  });

  it("Open opens the ZoneWindow for that Zone", () => {
    const openZoneWindow = vi.fn();
    useDesk.setState({ openZoneWindow } as never);
    const open = zoneMenuEntries(
      { type: "zone", id: "dir-1", title: "Atlas Phase 13 Zone" } as never,
      { x: 10, y: 20 },
    ).find((e) => (e as { id: string }).id === "object.open") as {
      onSelect: () => void;
    };
    open.onSelect();
    expect(openZoneWindow).toHaveBeenCalledWith("dir-1", { x: 10, y: 20 });
  });
});
