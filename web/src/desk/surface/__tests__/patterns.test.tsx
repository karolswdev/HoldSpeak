/** Surface patterns v1 — contract suites for all seven pattern components.
 *  Tests: named states, keyboard behavior, ARIA roles/attributes,
 *  class name patterns (token compliance). */
import { render, screen, fireEvent, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useRef, useState } from "react";
import { StateChip, type ChipState } from "../patterns/StateChip";
import { ActionNotice } from "../patterns/ActionNotice";
import { Disclosure } from "../patterns/Disclosure";
import { ProgressPlan, type PlanStep } from "../patterns/ProgressPlan";
import { ChoiceCardGroup, ChoiceCard } from "../patterns/ChoiceCardGroup";
import { Popover } from "../patterns/Popover";
import { ProvenanceChip, Receipt } from "../patterns/ProvenanceChip";

/* ────────────────────────────────────────────────────────────────────
   1. StateChip
   ──────────────────────────────────────────────────────────────────── */

describe("StateChip", () => {
  const ALL_STATES: ChipState[] = [
    "idle", "active", "working", "success", "warning", "failure", "unreachable",
  ];

  it("renders all seven states with correct data-state attribute", () => {
    const { container } = render(
      <>
        {ALL_STATES.map((s) => (
          <StateChip key={s} state={s} />
        ))}
      </>,
    );
    for (const state of ALL_STATES) {
      const chip = container.querySelector(`[data-state="${state}"]`);
      expect(chip).toBeTruthy();
    }
  });

  it("shows default label text for each state", () => {
    render(<StateChip state="success" />);
    expect(screen.getByText("Success")).toBeInTheDocument();
  });

  it("allows custom label override", () => {
    render(<StateChip state="failure" label="Offline" />);
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  it("allows custom icon override", () => {
    const { container } = render(<StateChip state="idle" icon="Z" />);
    const icon = container.querySelector(".surface-state-chip-icon");
    expect(icon?.textContent).toBe("Z");
  });

  it("has role=status for accessibility", () => {
    render(<StateChip state="active" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("uses the surface-state-chip class name (token compliance)", () => {
    const { container } = render(<StateChip state="working" />);
    expect(container.querySelector(".surface-state-chip")).toBeTruthy();
  });
});

/* ────────────────────────────────────────────────────────────────────
   2. ActionNotice
   ──────────────────────────────────────────────────────────────────── */

describe("ActionNotice", () => {
  it("renders message children", () => {
    render(<ActionNotice>Something happened</ActionNotice>);
    expect(screen.getByText("Something happened")).toBeInTheDocument();
  });

  it("renders icon when provided", () => {
    const { container } = render(
      <ActionNotice icon="!">Alert</ActionNotice>,
    );
    const icon = container.querySelector(".surface-action-notice-icon");
    expect(icon?.textContent).toBe("!");
  });

  it("renders action button and fires callback", () => {
    const onClick = vi.fn();
    render(
      <ActionNotice action={{ label: "Retry", onClick }}>
        Failed
      </ActionNotice>,
    );
    const btn = screen.getByRole("button", { name: "Retry" });
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("sets data-tone for each tone variant", () => {
    const tones = ["ok", "warn", "danger", "info"] as const;
    for (const tone of tones) {
      const { container, unmount } = render(
        <ActionNotice tone={tone}>msg</ActionNotice>,
      );
      expect(
        container.querySelector(`[data-tone="${tone}"]`),
      ).toBeTruthy();
      unmount();
    }
  });

  it("has role=status by default", () => {
    render(<ActionNotice>msg</ActionNotice>);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("allows custom role", () => {
    render(<ActionNotice role="alert">urgent</ActionNotice>);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("uses the surface-action-notice class (token compliance)", () => {
    const { container } = render(<ActionNotice>msg</ActionNotice>);
    expect(
      container.querySelector(".surface-action-notice"),
    ).toBeTruthy();
  });
});

/* ────────────────────────────────────────────────────────────────────
   3. Disclosure
   ──────────────────────────────────────────────────────────────────── */

describe("Disclosure", () => {
  it("renders closed by default", () => {
    render(<Disclosure label="Details">Body</Disclosure>);
    expect(screen.queryByText("Body")).toBeNull();
  });

  it("opens on click", () => {
    render(<Disclosure label="Details">Body</Disclosure>);
    fireEvent.click(screen.getByRole("button", { name: /Details/ }));
    expect(screen.getByText("Body")).toBeInTheDocument();
  });

  it("renders open by default when defaultOpen=true", () => {
    render(<Disclosure label="Details" defaultOpen>Body</Disclosure>);
    expect(screen.getByText("Body")).toBeInTheDocument();
  });

  it("closes on Escape", () => {
    render(<Disclosure label="Details" defaultOpen>Body</Disclosure>);
    expect(screen.getByText("Body")).toBeInTheDocument();
    fireEvent.keyDown(screen.getByText("Body").parentElement!, {
      key: "Escape",
    });
    expect(screen.queryByText("Body")).toBeNull();
  });

  it("has aria-expanded on the trigger button", () => {
    render(<Disclosure label="Details">Body</Disclosure>);
    const btn = screen.getByRole("button", { name: /Details/ });
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(btn);
    expect(btn.getAttribute("aria-expanded")).toBe("true");
  });

  it("renders the body as a region with aria-label", () => {
    render(<Disclosure label="Advanced" defaultOpen>Body</Disclosure>);
    expect(screen.getByRole("region", { name: "Advanced" })).toBeInTheDocument();
  });

  it("renders token slot", () => {
    render(
      <Disclosure label="Settings" token="3 items" defaultOpen>
        Body
      </Disclosure>,
    );
    expect(screen.getByText("3 items")).toBeInTheDocument();
  });

  it("fires onOpenChange callback", () => {
    const onOpenChange = vi.fn();
    render(
      <Disclosure label="Details" onOpenChange={onOpenChange}>
        Body
      </Disclosure>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Details/ }));
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it("uses surface-disclosure class (token compliance)", () => {
    const { container } = render(
      <Disclosure label="Details">Body</Disclosure>,
    );
    expect(container.querySelector(".surface-disclosure")).toBeTruthy();
  });
});

/* ────────────────────────────────────────────────────────────────────
   4. ProgressPlan
   ──────────────────────────────────────────────────────────────────── */

describe("ProgressPlan", () => {
  const steps: PlanStep[] = [
    { id: "1", label: "Download", status: "done" },
    { id: "2", label: "Extract", status: "running", progress: 0.6, rate: "2MB/s" },
    { id: "3", label: "Verify", status: "queued" },
    { id: "4", label: "Apply", status: "failed", detail: "Checksum mismatch" },
  ];

  it("renders all four step states", () => {
    const { container } = render(<ProgressPlan steps={steps} />);
    expect(container.querySelector('[data-status="done"]')).toBeTruthy();
    expect(container.querySelector('[data-status="running"]')).toBeTruthy();
    expect(container.querySelector('[data-status="queued"]')).toBeTruthy();
    expect(container.querySelector('[data-status="failed"]')).toBeTruthy();
  });

  it("renders step labels", () => {
    const { container } = render(<ProgressPlan steps={steps} />);
    const labels = container.querySelectorAll(".surface-plan-step-label");
    const texts = Array.from(labels).map((el) => el.textContent);
    expect(texts).toEqual(["Download", "Extract", "Verify", "Apply"]);
  });

  it("renders progressbar with aria attributes when progress is set", () => {
    render(<ProgressPlan steps={steps} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("60");
  });

  it("renders rate text", () => {
    render(<ProgressPlan steps={steps} />);
    expect(screen.getByText("2MB/s")).toBeInTheDocument();
  });

  it("renders detail text in non-compact mode", () => {
    render(<ProgressPlan steps={steps} />);
    expect(screen.getByText("Checksum mismatch")).toBeInTheDocument();
  });

  it("hides detail text in compact mode", () => {
    const { container } = render(<ProgressPlan steps={steps} compact />);
    expect(container.querySelector("[data-compact]")).toBeTruthy();
    // Detail is hidden via CSS display:none in compact mode, but
    // the element should not render at all
    expect(screen.queryByText("Checksum mismatch")).toBeNull();
  });

  it("renders receipt slot", () => {
    render(
      <ProgressPlan steps={steps} receipt={<span>Receipt text</span>} />,
    );
    expect(screen.getByText("Receipt text")).toBeInTheDocument();
  });

  it("renders action button and fires callback", () => {
    const onClick = vi.fn();
    render(
      <ProgressPlan
        steps={steps}
        action={{ label: "Retry", onClick }}
      />,
    );
    const btn = screen.getByRole("button", { name: "Retry" });
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("has role=group with aria-label", () => {
    render(<ProgressPlan steps={steps} ariaLabel="Update plan" />);
    expect(screen.getByRole("group", { name: "Update plan" })).toBeInTheDocument();
  });

  it("uses surface-progress-plan class (token compliance)", () => {
    const { container } = render(<ProgressPlan steps={steps} />);
    expect(container.querySelector(".surface-progress-plan")).toBeTruthy();
  });
});

/* ────────────────────────────────────────────────────────────────────
   5. ChoiceCardGroup
   ──────────────────────────────────────────────────────────────────── */

describe("ChoiceCardGroup", () => {
  function TestGroup({ initialValue = null }: { initialValue?: string | null }) {
    const [value, setValue] = useState<string | null>(initialValue);
    return (
      <ChoiceCardGroup
        name="plan"
        value={value}
        onChange={setValue}
        confirmLabel="Confirm"
        onConfirm={() => {}}
        ariaLabel="Select plan"
      >
        <ChoiceCard
          value="free"
          label="Free"
          description="Basic access"
          name="plan"
          selectedValue={value}
          onChange={setValue}
          facts={[{ label: "Users", value: "1" }]}
        />
        <ChoiceCard
          value="pro"
          label="Pro"
          description="Full access"
          recommended
          name="plan"
          selectedValue={value}
          onChange={setValue}
          cost={<span>$10/mo</span>}
        />
        <ChoiceCard
          value="ent"
          label="Enterprise"
          disabled
          name="plan"
          selectedValue={value}
          onChange={setValue}
        />
      </ChoiceCardGroup>
    );
  }

  it("renders as a radiogroup", () => {
    render(<TestGroup />);
    expect(screen.getByRole("radiogroup", { name: "Select plan" })).toBeInTheDocument();
  });

  it("renders radio inputs for each card", () => {
    render(<TestGroup />);
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(3);
  });

  it("selects a card on click", () => {
    render(<TestGroup />);
    const radios = screen.getAllByRole("radio");
    const freeRadio = radios[0]; // "Free" is the first card
    fireEvent.click(freeRadio);
    expect(freeRadio).toBeChecked();
  });

  it("marks recommended card visually", () => {
    const { container } = render(<TestGroup />);
    expect(container.querySelector("[data-recommended]")).toBeTruthy();
  });

  it("marks disabled card", () => {
    const { container } = render(<TestGroup />);
    expect(container.querySelector("[data-disabled]")).toBeTruthy();
    const entRadio = screen.getByRole("radio", { name: "Enterprise" });
    expect(entRadio).toBeDisabled();
  });

  it("renders facts as key-value pairs", () => {
    render(<TestGroup />);
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("renders cost slot", () => {
    render(<TestGroup />);
    expect(screen.getByText("$10/mo")).toBeInTheDocument();
  });

  it("renders confirm button, disabled when no selection", () => {
    render(<TestGroup />);
    const btn = screen.getByRole("button", { name: "Confirm" });
    expect(btn).toBeDisabled();
  });

  it("enables confirm button when a card is selected", () => {
    render(<TestGroup initialValue="free" />);
    const btn = screen.getByRole("button", { name: "Confirm" });
    expect(btn).not.toBeDisabled();
  });

  it("uses surface-choice-group class (token compliance)", () => {
    const { container } = render(<TestGroup />);
    expect(container.querySelector(".surface-choice-group")).toBeTruthy();
  });
});

/* ────────────────────────────────────────────────────────────────────
   5b. ChoiceCard object slots (HS-156-08): summary / emblem / tier / fold
   ──────────────────────────────────────────────────────────────────── */

describe("ChoiceCard object slots", () => {
  function SlotGroup() {
    const [value, setValue] = useState<string | null>(null);
    return (
      <ChoiceCardGroup
        name="tier"
        value={value}
        onChange={setValue}
        ariaLabel="Pick a tier"
        layout="row"
      >
        <ChoiceCard
          value="balanced"
          label="Balanced"
          tier="balanced"
          emblem="◐"
          summary="6 jobs → Qwen 9B"
          fold={<span>Thoughts and notes</span>}
          foldLabel="What's inside"
          name="tier"
          selectedValue={value}
          onChange={setValue}
        />
      </ChoiceCardGroup>
    );
  }

  it("renders the one-line summary anchor", () => {
    render(<SlotGroup />);
    expect(screen.getByText("6 jobs → Qwen 9B")).toBeInTheDocument();
  });

  it("renders the emblem as decoration (aria-hidden)", () => {
    const { container } = render(<SlotGroup />);
    const emblem = container.querySelector(".surface-choice-card-emblem");
    expect(emblem?.textContent).toBe("◐");
    expect(emblem?.getAttribute("aria-hidden")).toBe("true");
  });

  it("stamps data-tier on the card and data-layout + track count on the group", () => {
    const { container } = render(<SlotGroup />);
    expect(container.querySelector('[data-tier="balanced"]')).toBeTruthy();
    const group = container.querySelector('[data-layout="row"]') as HTMLElement;
    expect(group).toBeTruthy();
    expect(group.style.getPropertyValue("--choice-cards")).toBe("1");
  });

  it("folds detail behind a disclosure; opening it never selects the radio", () => {
    render(<SlotGroup />);
    expect(screen.queryByText("Thoughts and notes")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /What's inside/ }));
    expect(screen.getByText("Thoughts and notes")).toBeInTheDocument();
    expect(screen.getByRole("radio")).not.toBeChecked();
  });
});

/* ────────────────────────────────────────────────────────────────────
   6. Popover
   ──────────────────────────────────────────────────────────────────── */

describe("Popover", () => {
  function TestPopover() {
    const anchorRef = useRef<HTMLButtonElement>(null);
    const [open, setOpen] = useState(false);
    return (
      <>
        <button ref={anchorRef} onClick={() => setOpen(true)}>
          Open
        </button>
        <Popover
          anchor={anchorRef}
          open={open}
          onClose={() => setOpen(false)}
          ariaLabel="Test popover"
        >
          <p>Popover content</p>
          <button>Inner</button>
        </Popover>
      </>
    );
  }

  function openPopover() {
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
  }

  it("does not render when closed", () => {
    render(<TestPopover />);
    expect(screen.queryByText("Popover content")).toBeNull();
  });

  it("renders when opened", () => {
    render(<TestPopover />);
    openPopover();
    expect(screen.getByText("Popover content")).toBeInTheDocument();
  });

  it("carries its aria-label without dialog semantics (no-modals law)", () => {
    render(<TestPopover />);
    openPopover();
    expect(screen.getByLabelText("Test popover")).toBeInTheDocument();
  });

  it("closes on Escape", () => {
    render(<TestPopover />);
    openPopover();
    const dialog = document.querySelector(".surface-popover") as HTMLElement;
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByText("Popover content")).toBeNull();
  });

  it("closes on backdrop click", () => {
    render(<TestPopover />);
    openPopover();
    const backdrop = document.querySelector(".surface-popover-backdrop");
    expect(backdrop).toBeTruthy();
    fireEvent.click(backdrop!);
    expect(screen.queryByText("Popover content")).toBeNull();
  });

  it("uses surface-popover class (token compliance)", () => {
    render(<TestPopover />);
    openPopover();
    expect(document.querySelector(".surface-popover")).toBeTruthy();
  });

  /* ── Portal-target regression (HS-156 popover z-index fix) ────── */

  /** Wrapper that provides a #desk-next container, matching the real
   *  DeskApp shell, so the Popover portal lands inside it and scoped
   *  CSS rules (.desk-next .surface-popover) match. */
  function TestPopoverInDesk() {
    const anchorRef = useRef<HTMLButtonElement>(null);
    const [open, setOpen] = useState(false);
    const [clicked, setClicked] = useState(false);
    return (
      <div className="desk-next" id="desk-next">
        <button ref={anchorRef} onClick={() => setOpen(true)}>
          Open
        </button>
        <Popover
          anchor={anchorRef}
          open={open}
          onClose={() => setOpen(false)}
          ariaLabel="Desk popover"
        >
          <p>{clicked ? "Clicked!" : "Popover content"}</p>
          <button onClick={() => setClicked(true)}>Inner action</button>
        </Popover>
      </div>
    );
  }

  it("portals into #desk-next so scoped z-index rules apply", () => {
    render(<TestPopoverInDesk />);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    const popover = document.querySelector(".surface-popover");
    expect(popover).toBeTruthy();
    // The popover must be inside the desk-next root, not document.body
    const deskRoot = document.getElementById("desk-next");
    expect(deskRoot!.contains(popover!)).toBe(true);
  });

  it("content receives pointer events above the backdrop", () => {
    render(<TestPopoverInDesk />);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    // The backdrop sits behind the content — clicking a button inside
    // the popover must fire its handler, not the backdrop's onClose.
    const innerBtn = screen.getByRole("button", { name: "Inner action" });
    fireEvent.click(innerBtn);
    expect(screen.getByText("Clicked!")).toBeInTheDocument();
    // The popover must still be open (backdrop did not intercept).
    expect(document.querySelector(".surface-popover") as HTMLElement).toBeInTheDocument();
  });

  it("backdrop click still closes the popover", () => {
    render(<TestPopoverInDesk />);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    const backdrop = document.querySelector(".surface-popover-backdrop");
    expect(backdrop).toBeTruthy();
    fireEvent.click(backdrop!);
    expect(document.querySelector(".surface-popover")).toBeNull();
  });

  it("popover and backdrop have co-located z-index classes for CSS", () => {
    render(<TestPopoverInDesk />);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    const popover = document.querySelector(".surface-popover");
    const backdrop = document.querySelector(".surface-popover-backdrop");
    expect(popover).toBeTruthy();
    expect(backdrop).toBeTruthy();
    // Both must be inside the same portal target (#desk-next)
    const deskRoot = document.getElementById("desk-next");
    expect(deskRoot!.contains(popover!)).toBe(true);
    expect(deskRoot!.contains(backdrop!)).toBe(true);
  });
});

/* ────────────────────────────────────────────────────────────────────
   7. ProvenanceChip + Receipt
   ──────────────────────────────────────────────────────────────────── */

describe("ProvenanceChip", () => {
  it("renders source label", () => {
    render(<ProvenanceChip source="local" />);
    expect(screen.getByText("local")).toBeInTheDocument();
  });

  it("renders boundary badge when provided", () => {
    render(<ProvenanceChip source="api" boundary="cloud" />);
    expect(screen.getByText("cloud")).toBeInTheDocument();
  });

  it("renders inspect button and fires callback", () => {
    const onInspect = vi.fn();
    render(<ProvenanceChip source="api" onInspect={onInspect} />);
    const btn = screen.getByRole("button", { name: /Inspect api/i });
    fireEvent.click(btn);
    expect(onInspect).toHaveBeenCalledOnce();
  });

  it("omits inspect button when no callback", () => {
    render(<ProvenanceChip source="local" />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("uses surface-provenance-chip class (token compliance)", () => {
    const { container } = render(<ProvenanceChip source="local" />);
    expect(container.querySelector(".surface-provenance-chip")).toBeTruthy();
  });
});

describe("Receipt", () => {
  it("renders all three status tones", () => {
    const tones = ["ok", "warn", "danger"] as const;
    for (const status of tones) {
      const { container, unmount } = render(
        <Receipt status={status} label={`${status} label`} />,
      );
      expect(
        container.querySelector(`[data-status="${status}"]`),
      ).toBeTruthy();
      unmount();
    }
  });

  it("renders label text", () => {
    render(<Receipt status="ok" label="Synced" />);
    expect(screen.getByText("Synced")).toBeInTheDocument();
  });

  it("renders timestamp when provided", () => {
    render(<Receipt status="ok" label="Synced" timestamp="12:34" />);
    expect(screen.getByText("12:34")).toBeInTheDocument();
  });

  it("renders inspect button and fires callback", () => {
    const onInspect = vi.fn();
    render(<Receipt status="warn" label="Warning" onInspect={onInspect} />);
    const btn = screen.getByRole("button", { name: /Inspect Warning/i });
    fireEvent.click(btn);
    expect(onInspect).toHaveBeenCalledOnce();
  });

  it("uses surface-receipt class (token compliance)", () => {
    const { container } = render(
      <Receipt status="ok" label="Synced" />,
    );
    expect(container.querySelector(".surface-receipt")).toBeTruthy();
  });
});
