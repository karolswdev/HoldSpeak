import {
  createContext,
  useContext,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { fitStrip, VERB_OVERFLOW_WORD } from "./fitStrip";
import { textMeasure } from "./objects/fitName";

export const VerbRowContext = createContext(false);
type Props = HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  as?: "div" | "span";
  fitting?: boolean;
  nodeRef?: { current: HTMLElement | null };
};
/** Keep the original control parent. The shared fitter produces container
 * rules; viewport changes do not move or remount controls through React. */
export function VerbRow({
  as: Tag = "span",
  fitting = true,
  nodeRef,
  children,
  className,
  ...props
}: Props) {
  return useContext(VerbRowContext) || !fitting ? (
    <Tag
      {...props}
      ref={(node) => {
        if (nodeRef) nodeRef.current = node;
      }}
      className={className}
    >
      {children}
    </Tag>
  ) : (
    <FittingRow {...props} as={Tag} nodeRef={nodeRef} className={className}>
      {children}
    </FittingRow>
  );
}
function FittingRow({
  as: Tag = "span",
  nodeRef,
  children,
  className,
  ...props
}: Props) {
  const seat = useRef<HTMLElement>(null),
    anchor = useRef<HTMLButtonElement>(null),
    id = useId().replace(/[^a-z0-9]/gi, "");
  const [model, setModel] = useState<{
      nodes: HTMLElement[];
      signature: string;
    }>({ nodes: [], signature: "" }),
    [open, setOpen] = useState(false);
  useLayoutEffect(() => {
    const row = seat.current;
    if (!row) return;
    const sheet =
      typeof CSSStyleSheet !== "undefined" &&
      "replaceSync" in CSSStyleSheet.prototype
        ? new CSSStyleSheet()
        : null;
    if (sheet)
      document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];
    let live = true,
      lastRules = "";
    const refresh = () => {
      if (!live) return;
      const controls = [
        ...row.querySelectorAll<HTMLElement>("button.btn,.gadget-cycle"),
      ].filter(
        (control) =>
          control !== anchor.current &&
          control.closest(".surface-verb-row") === row &&
          !control.hasAttribute("aria-haspopup") &&
          !control.closest(".gadget-string,.surface-input-well") &&
          (!control.closest(".gadget-cycle") ||
            control.matches(".gadget-cycle")),
      );
      const signature = controls
        .map(
          (node) =>
            `${node.textContent}:${(node as HTMLButtonElement).disabled}`,
        )
        .join("|");
      const updateModel = () =>
        setModel((old) =>
          old.signature === signature &&
          old.nodes.length === controls.length &&
          old.nodes.every((node, index) => node === controls[index])
            ? old
            : { nodes: controls, signature },
        );
      // Without a layout engine there is no measured overflow. Declared
      // menu-only actions still use their ordinary Actions menu.
      if (!sheet) {
        updateModel();
        return;
      }
      const menuOnly = controls.filter((control) =>
        control.hasAttribute("data-verb-menu-only"),
      );
      const available = controls
        .filter((control) => !menuOnly.includes(control))
        .sort(
          (a, b) =>
            Number(a.hasAttribute("data-verb-secondary")) -
            Number(b.hasAttribute("data-verb-secondary")),
        );
      available.forEach(
        (node, index) => (node.dataset.verbIndex = String(index)),
      );
      const width = (element: HTMLElement) => {
        const select = element.querySelector<HTMLSelectElement>("select"),
          node = select ?? element,
          style = getComputedStyle(node),
          measure = textMeasure(style);
        const words = select
          ? (select.selectedOptions[0]?.text ?? "")
          : (element.textContent ?? "");
        const ink =
          measure?.width(words) ??
          words.length * (parseFloat(style.fontSize) || 13) * 0.6;
        const edges = [
          "paddingLeft",
          "paddingRight",
          "borderLeftWidth",
          "borderRightWidth",
        ].reduce(
          (sum, key) =>
            sum +
            (parseFloat(style[key as keyof CSSStyleDeclaration] as string) ||
              0),
          0,
        );
        const glyphs = [
          ...element.querySelectorAll<HTMLElement>("svg,img"),
        ].reduce(
          (sum, glyph) =>
            sum +
            (parseFloat(getComputedStyle(glyph).width) ||
              Number(glyph.getAttribute("width")) ||
              16),
          0,
        );
        const tracking =
          (parseFloat(style.letterSpacing) || 0) *
          Math.max(0, words.length - 1);
        return Math.ceil(
          Math.max(
            parseFloat(style.minWidth) || 0,
            ink +
              edges +
              tracking +
              glyphs +
              (glyphs ? parseFloat(style.columnGap) || 6 : 0) +
              (select ? 24 : 0),
          ),
        );
      };
      const sizes = available.map(width),
        gap = parseFloat(getComputedStyle(row).gap) || 8;
      const more = anchor.current ? width(anchor.current) : 90;
      const fixed = [...row.children]
        .filter(
          (child) =>
            child !== anchor.current &&
            !controls.some(
              (control) => child === control || child.contains(control),
            ),
        )
        .reduce((sum, child) => {
          const style = getComputedStyle(child);
          if (style.display === "none") return sum;
          const basis = parseFloat(style.flexBasis);
          return (
            sum +
            (child.querySelector("input,textarea") && Number.isFinite(basis)
              ? basis
              : style.flexShrink === "0"
                ? child.getBoundingClientRect().width
                : parseFloat(style.minWidth) || 0) +
            gap
          );
        }, 0);
      const safe = available.findIndex((control) =>
        control.hasAttribute("data-safe-answer"),
      );
      const primary =
        safe >= 0
          ? safe
          : row.classList.contains("kit-toolbar-verbs")
            ? available.findIndex(
                (control) =>
                  control.tagName === "BUTTON" &&
                  !control.hasAttribute("data-verb-secondary"),
              )
            : -1;
      const total =
        sizes.reduce((sum, n) => sum + n, 0) +
        gap * Math.max(0, sizes.length - 1);
      const breaks = new Set([
        total + fixed + (menuOnly.length ? more + gap : 0),
      ]);
      let prefix = 0;
      sizes.forEach((size, index) => {
        prefix += size;
        breaks.add(prefix + gap * index + more + gap + fixed);
      });
      const scope = `[data-verb-row="${id}"]`,
        rules = [
          `${scope} [data-verb-menu-only]{display:none!important;}`,
          `${scope}>[data-verb-overflow]{display:${menuOnly.length ? "inline-flex" : "none"};}`,
        ];
      for (const at of [...breaks].sort((a, b) => b - a)) {
        const room = at - 0.1 - fixed;
        const shown = fitStrip(
          room - (menuOnly.length ? more + gap : 0),
          sizes,
          menuOnly.length ? 0 : more,
          gap,
          primary,
        );
        rules.push(
          `@container verb-row (width < ${at}px){${available.map((_, index) => `${scope} [data-verb-index="${index}"]{display:${shown.includes(index) ? "inline-flex!important" : "none!important"};}`).join("")}${scope}>[data-verb-overflow]{display:${shown.length < sizes.length || menuOnly.length ? "inline-flex" : "none"};}}`,
        );
      }
      const css = rules.join("\n");
      if (sheet && css !== lastRules) {
        sheet.replaceSync(css);
        lastRules = css;
      }
      updateModel();
    };
    refresh();
    row.addEventListener("change", refresh);
    const changes = new MutationObserver(refresh);
    changes.observe(row, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["disabled"],
    });
    void document.fonts?.ready.then(refresh);
    return () => {
      live = false;
      changes.disconnect();
      row.removeEventListener("change", refresh);
      if (sheet)
        document.adoptedStyleSheets = document.adoptedStyleSheets.filter(
          (existing) => existing !== sheet,
        );
    };
  }, []);
  const folded = model.nodes.filter(
    (node) =>
      node.hasAttribute("data-verb-menu-only") ||
      (typeof CSSStyleSheet !== "undefined" &&
        "replaceSync" in CSSStyleSheet.prototype &&
        getComputedStyle(node).display === "none"),
  );
  const rect = open ? anchor.current?.getBoundingClientRect() : null;
  const entries: WorkMenuEntry[] = folded.map((element, index) => {
    const select = element.querySelector<HTMLSelectElement>("select");
    if (select) {
      const label = select.getAttribute("aria-label") || "Choice";
      return select.disabled
        ? {
            type: "item",
            id: String(index),
            label,
            disabled: true,
            onSelect: () => {},
          }
        : {
            type: "sub",
            id: String(index),
            label,
            entries: [...select.options].map((option) => ({
              type: "item",
              id: option.value,
              label: option.text,
              checked: option.selected ? "exclusive" : false,
              disabled: option.disabled,
              onSelect: () => {
                select.value = option.value;
                select.dispatchEvent(new Event("change", { bubbles: true }));
              },
            })),
          };
    }
    const button = element as HTMLButtonElement;
    return {
      type: "item",
      id: String(index),
      label: button.getAttribute("aria-label") || button.textContent || "",
      disabled: button.disabled,
      onSelect: () => button.click(),
    };
  });
  const hasMore =
    (typeof CSSStyleSheet !== "undefined" &&
      "replaceSync" in CSSStyleSheet.prototype &&
      model.nodes.length > 1) ||
    model.nodes.some((node) => node.hasAttribute("data-verb-menu-only"));
  return (
    <VerbRowContext.Provider value={true}>
      <Tag
        {...props}
        ref={(node) => {
          seat.current = node;
          if (nodeRef) nodeRef.current = node;
        }}
        className={["surface-verb-row", className].filter(Boolean).join(" ")}
        data-verb-row={id}
      >
        {children}
        {hasMore ? (
          <Button
            ref={anchor}
            dense
            variant="secondary"
            className="kit-toolbar-more"
            aria-label={VERB_OVERFLOW_WORD}
            data-verb-overflow
            style={
              !(
                typeof CSSStyleSheet !== "undefined" &&
                "replaceSync" in CSSStyleSheet.prototype
              ) &&
              !model.nodes.some((node) =>
                node.hasAttribute("data-verb-menu-only"),
              )
                ? { display: "none" }
                : undefined
            }
            aria-haspopup="menu"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            {VERB_OVERFLOW_WORD} ▾
          </Button>
        ) : null}
      </Tag>
      {rect ? (
        <WorkMenu
          label={VERB_OVERFLOW_WORD}
          x={rect.left}
          y={rect.bottom}
          opener={anchor.current}
          autoFocus
          returnFocus={() => anchor.current?.focus()}
          onClose={() => setOpen(false)}
          entries={entries}
        />
      ) : null}
    </VerbRowContext.Provider>
  );
}
