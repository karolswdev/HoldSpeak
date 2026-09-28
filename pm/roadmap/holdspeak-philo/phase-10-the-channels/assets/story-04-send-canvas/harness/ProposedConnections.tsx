/* PHILO-10-04 CANVAS (PROPOSAL): SettingsCore's "./connections" import,
 * swapped by harness/vite.config.mjs. Everything is the product's barrel
 * (web/src/pages/cores/connections/index.ts) except ConnectionsPane, which
 * renders the REAL pane and then the proposed Destinations group under
 * Tools. Credentials and RAW stay below, as today (SettingsCore.tsx:2324).
 */
import { ConnectionsPane as RealPane } from "@w/pages/cores/connections/ConnectionsPane";
import { Destinations } from "./Destinations";

export * from "@w/pages/cores/connections/index";

export function ConnectionsPane(props: Parameters<typeof RealPane>[0]) {
  return (
    <>
      <RealPane {...props} />
      <Destinations />
    </>
  );
}
