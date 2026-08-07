import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Directory (Zone) pullout content (HS-117-15). */
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objectByRef } from "../world";
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
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "directory") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const members = ir.memberIds
    .map((m) => ({ ref: m, member: objectByRef(items, m) }))
    .filter(({ member }) => member);
  const memberCount = ir.memberIds.length;

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <SurfaceSection
          label={ir.name}
          actions={
            <span className="quiet">
              {memberCount} {memberCount === 1 ? "member" : "members"}
            </span>
          }
        >
          {members.length ? (
            <SurfaceRows>
              {members.map(({ ref, member }) => (
                <SurfaceRow
                  key={ref}
                  glyph={
                    <img
                      src={spriteUrl(member!.kind, member!.id)}
                      width={22}
                      height={22}
                      alt=""
                    />
                  }
                  title={member!.title}
                  detail={productLabel(member!.kind)}
                  onOpen={() => openPullout(member!.id)}
                />
              ))}
            </SurfaceRows>
          ) : (
            <SurfaceState
              empty
              emptyLabel="No members"
              emptyGlyph="○"
              actionLabel="Drop items here"
              onAction={() => undefined}
            />
          )}
        </SurfaceSection>
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter verbs={<> <button
          type="button"
          className="desk-chip quiet"
          onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}
        >
          Dictate about this
        </button> </>} />
    </>
  );
}
