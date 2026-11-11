import "./image-well.css";
import { useEffect, useState } from "react";
import { PaneNotice } from "./patterns/PreferencePane";
/** One fitted evidence image, with its reading well as the scroll owner. */
export function ImageWell({ src, alt }: { src: string; alt: string }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  return (
    <div className="surface-image-well" data-feedback-redact="true">
      {failed ? (
        <PaneNotice>The image did not load · The source could not be read · Your work is kept · Try again</PaneNotice>
      ) : (
        <img src={src} alt={alt} onError={() => setFailed(true)} />
      )}
    </div>
  );
}
