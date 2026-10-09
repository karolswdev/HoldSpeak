// PHILO-16 (A1) §5 — the icon each open window shows in its title bar, kept
// for the Dock: a seated window without an application tile gets its own
// seat tile, and that tile wears the same icon. DeskWindowFrame writes it;
// the Dock reads it when it draws the seat.
import type { ReactNode } from "react";

export const windowIcons = new Map<string, ReactNode>();
