// HS-156-03 — the surface barrel: the ONE supported import path for feature code.

export {
  SurfaceVerbs,
  SurfaceIdentity,
  SurfaceSection,
  SurfaceRows,
  SurfaceRow,
  SurfaceState,
  SurfaceColumns,
  SurfaceSplit,
  MetricStrip,
  SurfaceFacts,
  SurfaceCode,
  SurfaceWell,
  PaneWell,
  SurfaceTraffic,
  SurfaceTrafficTurn,
  SurfaceGroup,
  SurfaceSettingRow,
  SurfaceToggle,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceLibrary,
  SurfaceLibraryTile,
  SurfaceLibraryGhost,
  SurfaceSwitchboard,
  SurfaceBay,
  EditInPlace,
  ConfirmVerb,
  ScrollHint,
  useScrollHint,
  computeScrollHint,
  type ScrollHintState,
} from "./Surface";

export {
  GadgetGroup,
  GadgetRow,
  CheckGadget,
  CycleGadget,
  type CycleOption,
  MxRadio,
  type MxOption,
  StringGadget,
  PadGadget,
  FoldGadget,
  StepperGadget,
  PropGadget,
  GadgetTable,
  LedMeter,
  LampGadget,
  TransportKey,
  TransportRow,
  EgressChip,
  SecretRow,
} from "./gadgets";

export { SurfaceFooter } from "./SurfaceFooter";
export { Material } from "./Material";
export { useRovingRows } from "./roving";

export {
  SurfaceWings,
  type WingSpec,
  WingSlotContext,
  useWindowWings,
} from "./wings";

export {
  CitationChips,
  groundedMatchCount,
  sourceLabel,
  openSourceRef,
  NO_WINDOW_REF_KINDS,
  refOpensWindow,
} from "./citations";

export {
  wireDate,
  wireClock,
  wireDayClock,
  humanTime,
  deSnake,
  presentValue,
  streamDate,
  streamDayLabel,
  streamTime,
  isSameStreamDay,
} from "./format";

export { FootSlotContext } from "./foot";
export { TitleSlotContext, useWindowTitle } from "./title";
export { SPARSE_THRESHOLD } from "./sparse";

export { FilterTokens, type FilterTokenOption } from "./FilterTokens";

export {
  LedgerFilterBar,
  useLedgerFilter,
  type LedgerFilterToken,
  type UseLedgerFilterOpts,
} from "./LedgerFilter";

export {
  StateChip,
  type ChipState,
  ActionNotice,
  Disclosure,
  ProgressPlan,
  type PlanStep,
  HeardQuote,
  heardFacts,
  heardWordCount,
  heardDuration,
  ChoiceCardGroup,
  ChoiceCard,
  ChoiceCardShell,
  type ChoiceCardShellProps,
  ReadyStrip,
  type ReadyStripItem,
  StartVerb,
  StartVerbs,
  Popover,
  ProvenanceChip,
  Receipt,
  ClaimAxes,
  claimKindToken,
  claimSupportToken,
  claimAcceptanceToken,
  claimUnknownToken,
  type ClaimAxisToken,
  type ClaimUnknownValue,
  type ClaimAxesProps,
  TaskResume,
  TaskResumeList,
  type TaskResumeState,
  type TaskResumeProps,
  CoverageRow,
  CoverageLedger,
  coverageEmblem,
  type CoverageRowProps,
  type CoverageLedgerProps,
  ProjectButton,
  type ProjectButtonProps,
  LedgerRemainder,
  type LedgerRemainderProps,
  ParkReceipt,
  ParkedStrip,
  parkClock,
  parkedOutcome,
  restoredOutcome,
  restoreFailedOutcome,
  notParkedOutcome,
  RESTORE_REFUSED,
  type ParkOutcome,
  type ParkedRow,
  FoundBy,
  foundByWord,
  foundByDay,
  FOUND_BY_WORD,
  StandingPage,
  RefTokens,
  type MemoryRefToken,
  type StandingSentence,
} from "./patterns";

export { MicButton, type MicState } from "./controls/MicButton";

export {
  TopologySurface,
  type GraphNode,
  type GraphFlow,
  type TopologySurfaceProps,
} from "./graph/TopologySurface";

export { countToken, countLabel } from "./count";

// PHILO-14 B1 — the object species (DeskIcon, ObjectList, TimelineRail, ...).
export * from "./objects";
