// PHILO-14 B1 — the object species (contract.md "The object species").
export {
  OBJECT_KIND_WORD,
  objectKindWord,
  objectSprite,
  lampGadgetTone,
  type ObjectKind,
  type ObjectTone,
} from "./kinds";
export { DeskIcon, IconLamp, type DeskIconProps, type IconLampProps } from "./DeskIcon";
export { IconGrid, iconsInRect, type IconGridProps, type GridRect } from "./IconGrid";
export {
  ObjectList,
  type ObjectListProps,
  type ObjectListRow,
  type ObjectSort,
  type ObjectSortKey,
} from "./ObjectList";
export { GetInfo, type GetInfoProps, type GetInfoFacts } from "./GetInfo";
export {
  TimelineRail,
  StationTrack,
  type TimelineEntry,
  type Station,
  type LaneWord,
} from "./Timeline";
export { AskWell, type AskWellProps } from "./AskWell";
export { PRCard, FilesChanged, type PRCardProps, type ChangedFile } from "./PRCard";
export { ConfirmLine, type ConfirmLineProps, type ConfirmEnd } from "./ConfirmLine";
export {
  NeedsRow,
  NeedsList,
  DropTarget,
  DragGhost,
  type NeedsRowProps,
} from "./NeedsRow";
