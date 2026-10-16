import { SurfaceFooter } from "../surface/SurfaceFooter";
import { Button } from "../../components/signal/Signal";
/** Directory (Zone) pullout content (HS-117-15). */
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { refAgent, spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objectByRef } from "../world";
import { normalizeRef } from "../screen/compose";
import { openScreenRef } from "../screen/open";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { productLabel } from "../../lib/productLanguage";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../surface/Surface";
import type { PulloutContentProps } from "./types";

export function DirectoryPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  if (o.ref.kind !== "directory") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const childRefs = (items.directory ?? [])
    .filter((directory) => directory.parentId === ir.id && directory.id !== ir.id)
    .map((directory) => qualifiedRef("directory", directory.id));
  const seen = new Set<string>();
  const members = [...childRefs, ...ir.memberIds].flatMap((storedRef) => {
    const member = objectByRef(items, normalizeRef(storedRef));
    const ref = member ? qualifiedRef(member.kind, member.id) : storedRef;
    if (seen.has(ref)) return [];
    seen.add(ref);
    return [{ ref, member }];
  });

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <SurfaceSection
          label="Contents"
          count={members.length}
        >
          {members.length ? (
            <SurfaceRows>
              {members.map(({ ref, member }) => (
                <SurfaceRow
                  key={ref}
                  glyph={member ? (
                    <img
                      src={spriteUrl(member.kind, member.id, "rest", refAgent(member.ref))}
                      width={22}
                      height={22}
                      alt=""
                    />
                  ) : undefined}
                  title={<span data-member-ref={ref}>{member?.title || "Item unavailable"}</span>}
                  detail={member ? member.kind === "directory" ? "Drawer" : productLabel(member.kind) : "Unavailable"}
                  onOpen={member ? () => openScreenRef(ref) : undefined}
                />
              ))}
            </SurfaceRows>
          ) : (
            <SurfaceState
              empty
              emptyLabel="No items"
              emptyGlyph="○"
            />
          )}
        </SurfaceSection>
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter verbs={<Button
          dense
          variant="ghost"
          onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}
        >
          Dictate about this
        </Button>} />
    </>
  );
}
