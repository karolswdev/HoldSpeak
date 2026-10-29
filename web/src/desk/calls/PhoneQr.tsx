/* Phone (PHONE-DESIGN-2026-10-28 §9): the pairing QR, drawn from the
 * pairing link with `qrcode-generator` (MIT, Kazuhiko Arase; a dependency
 * in web/package.json, named in the third-party notices). One SVG path of
 * dark modules on a white well, with the call mark in the middle (error
 * correction M keeps the code readable under the mark). */
import qrcode from "qrcode-generator";
import { useMemo } from "react";
import { spriteUrl } from "../sprites";

/** The dark modules as one SVG path (a quiet zone of 4 modules around). */
export function qrPath(text: string): { size: number; path: string } {
  const code = qrcode(0, "M");
  code.addData(text);
  code.make();
  const count = code.getModuleCount();
  let path = "";
  for (let row = 0; row < count; row += 1) {
    for (let col = 0; col < count; col += 1) {
      if (code.isDark(row, col)) path += `M${col + 4} ${row + 4}h1v1h-1z`;
    }
  }
  return { size: count + 8, path };
}

export function PhoneQr({ text }: { text: string }) {
  const { size, path } = useMemo(() => qrPath(text), [text]);
  return (
    <span className="phone-qr" data-testid="phone-qr" data-qr={text}>
      <svg viewBox={`0 0 ${size} ${size}`} shapeRendering="crispEdges" role="img" aria-label="Pairing code">
        <rect width={size} height={size} fill="#fff" />
        <path d={path} fill="#253449" />
      </svg>
      <span className="phone-qr-mark" aria-hidden="true">
        <img src={spriteUrl("call", "calls", "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
      </span>
    </span>
  );
}
