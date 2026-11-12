// HS-129-01 — the foot is frame anatomy: hosted cores publish into the
// host target; direct windows use the same context at the frame edge.
import { createContext } from "react";

export const FootSlotContext = createContext<HTMLElement | null>(null);
