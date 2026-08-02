// HS-111-09 — the agent face contract: custom text avatars render as
// text; the default (empty or legacy 🤖) wears the automaton sprite.
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { AgentAvatar } from "./AgentAvatar";
import { spriteUrl } from "../sprites";

describe("AgentAvatar", () => {
  it("empty avatar wears the deterministic automaton sprite", () => {
    const { container } = render(<AgentAvatar avatar="" id="a1" />);
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img!.getAttribute("src")).toBe(spriteUrl("agent", "a1"));
  });

  it("the legacy 🤖 default also wears the sprite (never the emoji)", () => {
    const { container } = render(<AgentAvatar avatar="🤖" id="a2" />);
    expect(container.querySelector("img")).not.toBeNull();
    expect(container.textContent).not.toContain("🤖");
  });

  it("a user-set custom avatar stays text", () => {
    const { container } = render(<AgentAvatar avatar="Z" id="a3" />);
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toBe("Z");
  });

  it("model kind wears the cartridge sprite", () => {
    const { container } = render(
      <AgentAvatar avatar="" id="m1" kind="model" />,
    );
    expect(container.querySelector("img")!.getAttribute("src")).toBe(
      spriteUrl("model", "m1"),
    );
  });
});
