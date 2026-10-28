// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls: no call yet.
import type { CallSummary } from "../types";

export const callsEmpty: { calls: CallSummary[] } = { calls: [] };
