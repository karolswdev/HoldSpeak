/** StartVerb — a plated library Button, glyph over word, 72 px tall.
 *
 *  First run, option A "One screen" (owner ratified 2026-10-05). The set
 *  of "what you can do now" verbs at the top of a finished face, made
 *  from the owner's own data (`Record Atlas weekly · 10:30`). It is the
 *  library Button (UX-CANON: every verb the library Button) with a larger
 *  plate; StartVerbs lays the set out as equal columns that stack at the
 *  narrow container.
 */
import type { ComponentPropsWithRef, ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import "./start-verb.css";

export function StartVerb({
  glyph,
  children,
  variant = "secondary",
  className,
  ...rest
}: Omit<ComponentPropsWithRef<"button">, "children"> & {
  /** One character drawn over the word (aria-hidden). */
  glyph: string;
  /** The verb. */
  children: ReactNode;
  /** `primary` for the one verb the face leads with. */
  variant?: "primary" | "secondary";
  loading?: boolean;
}) {
  return (
    <Button
      variant={variant}
      className={className ? `surface-start-verb ${className}` : "surface-start-verb"}
      {...rest}
    >
      <span className="surface-start-verb-glyph" aria-hidden="true">
        {glyph}
      </span>
      <span className="surface-start-verb-word">{children}</span>
    </Button>
  );
}

export function StartVerbs({ children, ariaLabel = "Start" }: { children: ReactNode; ariaLabel?: string }) {
  return (
    <div className="surface-start-verbs" role="group" aria-label={ariaLabel}>
      {children}
    </div>
  );
}
