/* The "Also called" field: the other names for the owner, as chips, then
 * one input. A comma or Enter adds; Backspace on an empty input removes the
 * last chip. One component, two faces: the first-run You card and
 * Settings › People › You (PHILO-15 B57). */
import { useState } from "react";
import { StringGadget } from "../surface";
import type { useOwnerName } from "./ownerName";
import "./firstrun.css";

export function OwnerAliasField({ owner }: { owner: ReturnType<typeof useOwnerName> }) {
  const [alias, setAlias] = useState("");
  const commit = () => {
    if (!alias.trim()) return;
    owner.addAliases(alias);
    setAlias("");
  };
  return (
    <span className="firstrun-alias-row">
      {owner.aliases.map((name) => (
        <span key={name} className="surface-token" data-chip>
          {name}
        </span>
      ))}
      <StringGadget
        label="Also called"
        value={alias}
        onChange={(next) => {
          // A spoken or pasted list arrives whole: commas split it.
          if (next.includes(",")) {
            owner.addAliases(next);
            setAlias("");
          } else setAlias(next);
        }}
        placeholder="Add"
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            commit();
          } else if (event.key === "Backspace" && !alias) owner.removeLastAlias();
        }}
        inputProps={{ onBlur: commit }}
      />
    </span>
  );
}
