// HS-95-08 — the routing truth of the Desk OS (Constitution, Article I):
// three real routes render surfaces (the Desk, the Welcome arrival, the
// Presence theater); every other product path is a DEEP LINK that walks
// home and opens the matching desk window at the right scope. Features do
// not own routes anymore — adding a surface means a SURFACES row in
// SurfaceWindows plus (optionally) one demoted-path row here.
import { lazy, type ComponentType, type LazyExoticComponent } from "react";

export interface ProductRoute {
  path: string;
  label: string;
  component: LazyExoticComponent<ComponentType>;
  immersive?: boolean;
}

const Desk = lazy(() => import("./desk/DeskApp"));
const Welcome = lazy(() => import("./pages/WelcomePage"));
const Presence = lazy(() => import("./pages/PresencePage"));

export const PRODUCT_ROUTES: ProductRoute[] = [
  { path: "/", label: "Desk", component: Desk, immersive: true },
  { path: "/welcome", label: "Welcome", component: Welcome, immersive: true },
  {
    path: "/presence",
    label: "Presence",
    component: Presence,
    immersive: true,
  },
];

export interface DemotedRoute {
  path: string;
  /** The shell surface the deep link opens. */
  surface: string;
  /** Kind used to decode a subject from `?room=`/legacy params. */
  subjectKind?: "meeting" | "integration" | "workflow";
  /** Legacy bare query param carrying the same subject id. */
  legacyParam?: string;
  /** Fixed wing for routes whose old page had no object subject. */
  scope?: string;
}

export const DEMOTED_ROUTES: DemotedRoute[] = [
  { path: "/setup", surface: "project-setup" },
  { path: "/dictation", surface: "dictate" },
  { path: "/live", surface: "record-live" },
  {
    path: "/history",
    surface: "review-meetings",
    subjectKind: "meeting",
    legacyParam: "meeting",
  },
  {
    path: "/meetings",
    surface: "review-meetings",
    subjectKind: "meeting",
    legacyParam: "meeting",
  },
  {
    path: "/settings",
    surface: "configure-settings",
    subjectKind: "integration",
  },
  { path: "/activity", surface: "inspect-activity" },
  { path: "/commands", surface: "configure-commands" },
  { path: "/cadence", surface: "configure-cadence" },
  {
    path: "/workbenches",
    surface: "open-workbenches",
  },
  { path: "/profiles", surface: "configure-settings", scope: "models" },
  { path: "/models", surface: "configure-settings", scope: "models" },
  // HS-100-10 — Studio died; its address lands on Settings (the tools
  // it launched are search-reachable).
  { path: "/studio", surface: "configure-settings" },
  // Betterment AG1: the old Agents application is unmapped; its address
  // opens Agents (the Conductor window).
  { path: "/companion", surface: "open-conductor" },
  // PHILO-14 C4: the Conductor drawer, where agents live.
  { path: "/conductor", surface: "open-conductor" },
  { path: "/docs/dictation-runtime", surface: "read-runtime-docs" },
  { path: "/design/components", surface: "design-components" },
];
