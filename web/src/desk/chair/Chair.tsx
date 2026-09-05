// HS-170-04 -- the Chair surface: the arrival container.
// The lane vocabulary is PARKED (HS-170-04). The Chair is now a
// layout shell for the Arrival face: headline, sections, capture bar.

import { type ReactNode } from "react";
import "./chair.css";

export interface ChairProps {
  children: ReactNode;
}

export function Chair({ children }: ChairProps) {
  return (
    <div className="chair" data-testid="chair">
      {children}
    </div>
  );
}
