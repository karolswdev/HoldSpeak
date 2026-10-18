/** The words of a running Ask that waits (Betterment Q2, "Ask goes first").
 *  The hub sends an `ask_progress` frame: `busy` when background work holds
 *  the engine 5 s after the Ask starts, `retry` for every attempt after the
 *  first. These are its words; `runWords.ts` keeps the failure words. */

/** The engine, by where it is: "the LAN engine". */
export function engineWords(boundary: string | undefined): string {
  const value = String(boundary || "").toLowerCase();
  if (value === "private_network" || value === "lan") return "the LAN engine";
  if (value === "same_device" || value === "local") return "the engine on this Mac";
  if (value === "private_mesh" || value === "mesh" || value === "paired_device") return "the paired engine";
  if (value === "external_service" || value === "cloud") return "the cloud engine";
  return "the engine";
}

/** "Waiting for the LAN engine, busy with meeting analysis". */
export function busyWords(job: string, boundary: string | undefined): string {
  const engine = engineWords(boundary);
  return job ? `Waiting for ${engine}, busy with ${job}` : `Waiting for ${engine}`;
}

/** "Trying again, 1 of 3". */
export function retryWords(attempt: number, of: number): string {
  return `Trying again, ${Math.max(1, attempt)} of ${Math.max(attempt, of)}`;
}

/** The verb that runs this one Ask on another engine. It names a cloud
 *  engine as cloud: the press is where the egress happens. */
export function otherEngineVerb(label: string, boundary?: string): string {
  const name = label || "another engine";
  const cloud = ["cloud", "external_service"].includes(String(boundary || "").toLowerCase());
  return `Use ${name}${cloud ? " (cloud)" : ""} for this one`;
}
