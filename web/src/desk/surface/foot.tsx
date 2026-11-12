// HS-129-01 — the foot is frame anatomy. Window clients publish to the
// frame target; a composition with no frame keeps its inline foot.
import { createContext } from "react";

export const FootSlotContext = createContext<HTMLElement | null>(null);
