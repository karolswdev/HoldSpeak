/* PHILO-13-15 (C5): the window a component renders inside. DeskWindowFrame
 * provides it around its content, so a document seat (a SEND well) can name
 * its window's document to `Send to ▸` (desk/windowSend.tsx). */
import { createContext, useContext } from "react";

export const WindowIdContext = createContext<string | null>(null);

export const useWindowId = (): string | null => useContext(WindowIdContext);
