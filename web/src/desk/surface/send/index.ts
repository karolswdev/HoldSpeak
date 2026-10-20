// PHILO-11-04 — the SEND well species' sub-barrel. It carries the channel
// wire (features/channels/channels.ts), so it rides its own import path and
// the main barrel (../index.ts) stays wire-free (no import cycle through the
// desk store). Sanctioned in contract.md ("SendWell").
export {
  SendWell,
  SendWells,
  SendWellsFold,
  SendHistory,
  PreparedChip,
  PreviewWell,
  discardPrepared,
  retryInline,
  sendPrepared,
  ProofCell,
  ReceiptEgress,
  Unreadable,
  HISTORY_HEAD,
  accountChip,
  latestFor,
  mergeKnown,
  openFar,
  pickDestination,
  pickedDestination,
  proofLink,
  resetSendStore,
  useConnections,
  useDestinations,
  useSends,
  type DocRef,
  type RetryCommand,
  type Read,
} from "./SendWell";
