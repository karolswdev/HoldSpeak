// HS-143-12 — Settings' Models slot is the availability-only Model Library.
// Assignments, target tables, and Settings pointer writes deliberately have no
// home here; the aggregate library authority owns all truth and commands.
import { ModelLibraryCore } from "./ModelLibraryCore";

export function ModelsModule({ onRefuse: _onRefuse }: { onRefuse(refusal: string): void }) {
  // The core owns its in-flow receipt/error grammar. Keeping the slot adapter
  // means Settings remains the host, rather than creating a competing route.
  void _onRefuse;
  return <ModelLibraryCore />;
}
