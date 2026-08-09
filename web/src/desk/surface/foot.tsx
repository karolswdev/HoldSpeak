// HS-129-01 — the foot is frame anatomy: hosted cores publish into the
// SurfaceWindowHost target, while pullouts and direct windows remain in place.
import { createContext } from "react";

export const FootSlotContext = createContext<HTMLElement | null>(null);
