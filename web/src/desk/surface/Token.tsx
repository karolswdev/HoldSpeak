/** Token — the kit's `surface-token` species as a component (STATECHIP,
 *  2026-10-29). A token is a short fact (`Prepared`, `Due today`,
 *  `3 checks`); its words draw in sentence case through `stateWords`, so a
 *  caller that passes a caps token draws `Not launched`, not `NOT
 *  LAUNCHED`. A token that is a code (an id, a hash, a port, a host, a
 *  path, a branch) sets `code`: its text stays exact and draws mono. */
import { forwardRef, type HTMLAttributes, type ReactNode } from "react";
import { sentenceChildren } from "./words";

export type TokenProps = HTMLAttributes<HTMLSpanElement> & {
  /** The token is a code or an id: no case change, mono. */
  code?: boolean;
  children?: ReactNode;
};

export const Token = forwardRef<HTMLSpanElement, TokenProps>(function Token(
  { code = false, className, children, ...rest },
  ref,
) {
  return (
    <span
      ref={ref}
      className={className ?? "surface-token"}
      data-literal={code ? "" : undefined}
      {...rest}
    >
      {code ? children : sentenceChildren(children)}
    </span>
  );
});
