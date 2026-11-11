import "./image-well.css";
/** One fitted evidence image, with its reading well as the scroll owner. */
export function ImageWell({ src, alt }: { src: string; alt: string }) {
  return (
    <div className="surface-image-well">
      <img src={src} alt={alt} />
    </div>
  );
}
