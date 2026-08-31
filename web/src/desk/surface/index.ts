// HS-156-03 — the surface barrel: the ONE supported import path for feature code.

export {
  SurfaceVerbs,
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
} from "./citations";

export {
  humanTime,
  deSnake,
  presentValue,
  streamDate,
  streamDayLabel,
  streamTime,
  isSameStreamDay,
} from "./format";

export { FootSlotContext } from "./foot";
export { SPARSE_THRESHOLD } from "./sparse";

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
  ChoiceCardGroup,
  ChoiceCard,
  Popover,
  ProvenanceChip,
  Receipt,
} from "./patterns";

export { MicButton, type MicState } from "./controls/MicButton";

export {
  TopologySurface,
  type GraphNode,
  type GraphFlow,
  type TopologySurfaceProps,
} from "./graph/TopologySurface";
