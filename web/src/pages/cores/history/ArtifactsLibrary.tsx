// HS-117-09 — extracted from MeetingDetail (lines 593-664).
import { openPrimitive } from "../../../desk/shell";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceCode,
  SurfaceLibrary,
  SurfaceLibraryTile,
  SurfaceState,
  SurfaceWell,
} from "../../../desk/surface/Surface";
import { FoldGadget } from "../../../desk/surface/gadgets";
import { Material } from "../../../desk/surface/Material";
import { humanTime } from "../../../desk/surface/format";
import { rowId } from "../../pageSupport";
import { clockTime } from "./helpers";

export function ArtifactsLibrary({
  artifactRows,
  meetingTitle,
}: {
  artifactRows: Record<string, unknown>[];
  meetingTitle: string;
}) {
  if (!artifactRows.length) {
    return <SurfaceState empty emptyLabel="No artifacts yet" emptyGlyph="◇" />;
  }
  return (
    <SurfaceLibrary
      count={artifactRows.length}
      token={`${artifactRows.length} ${artifactRows.length === 1 ? "ARTIFACT" : "ARTIFACTS"}`}
    >
      {artifactRows.map((row, index) => {
        const title = String(row.title ?? row.artifact_type ?? "Artifact");
        let body = String(row.body_markdown ?? row.content ?? "").trim();
        // Plugin-authored bodies often self-title with a leading
        // markdown heading matching `title` — the tile's spine
        // already carries the name, so drop the redundant echo.
        const headingEcho = new RegExp(
          `^#{1,3}\\s+${title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*\\n+`,
          "i",
        );
        body = body.replace(headingEcho, "");
        const kind = String(row.artifact_type ?? "")
          .replace(/[_-]+/g, " ")
          .toUpperCase();
        const stamped = clockTime(row.created_at);
        return (
          <SurfaceLibraryTile
            key={rowId(row, index)}
            variant="receipt"
            stamp={[
              `ART ${String(index + 1).padStart(2, "0")}`,
              kind,
              stamped,
            ]
              .filter(Boolean)
              .join(" · ")}
            face={
              body ? (
                <Material>{body}</Material>
              ) : (
                // HS-111-07 — a body-less artifact face folds its
                // wire behind the RAW pattern, never bare JSON.
                <FoldGadget title="RAW · ARTIFACT">
                  <SurfaceWell head={`RAW · ${kind || "ARTIFACT"}`}>
                    <SurfaceCode>
                      {JSON.stringify(row, null, 2)}
                    </SurfaceCode>
                  </SurfaceWell>
                </FoldGadget>
              )
            }
            name={title}
            says={
              <span>
                {meetingTitle}
                {" · "}
                {humanTime(row.created_at) || "just now"}
              </span>
            }
            verbs={
              <Button
                dense
                onClick={() =>
                  openPrimitive(`artifact:${String(row.id)}`)
                }
              >
                Open
              </Button>
            }
          />
        );
      })}
    </SurfaceLibrary>
  );
}
