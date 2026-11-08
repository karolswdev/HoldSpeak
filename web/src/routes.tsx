// HS-95-08 — the routing truth of the Desk OS (Constitution, Article I):
// three real routes render surfaces (the Desk, the Welcome arrival, the
// Presence theater); every other product path is a DEEP LINK that walks
// home and opens the matching desk window at the right scope. Features do
// not own routes anymore — adding a surface means a SURFACES row in
// SurfaceWindows plus (optionally) one demoted-path row here.
import { type ComponentType, type LazyExoticComponent } from "react";
import { watchChunk } from "./runtime/freshBuild";
import { preloadable } from "./runtime/preloadable";

export interface ProductRoute {
  path: string;
  label: string;
  component: LazyExoticComponent<ComponentType>;
  immersive?: boolean;
}

const Desk = preloadable(watchChunk(() => import("./desk/DeskApp")));
const Welcome = preloadable(watchChunk(() => import("./pages/WelcomePage")));
const Presence = preloadable(watchChunk(() => import("./pages/PresencePage")));

/** Read the chunk of the surface this path draws: every path that is not
 * /welcome or /presence ends on the Desk. main.tsx renders after it, so the
 * first render does not suspend (a lazy Desk that suspended at boot was drawn
 * about 300 ms late; runtime/preloadable.ts). A failed read still renders:
 * the lazy fails into the error boundary, as before. */
export function preloadSurface(pathname: string): Promise<unknown> {
  const surface = pathname === "/welcome" ? Welcome : pathname === "/presence" ? Presence : Desk;
  return surface.preload();
}

export const PRODUCT_ROUTES: ProductRoute[] = [
  { path: "/", label: "Desk", component: Desk.component, immersive: true },
  { path: "/welcome", label: "Welcome", component: Welcome.component, immersive: true },
  {
    path: "/presence",
    label: "Presence",
    component: Presence.component,
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
  // Engines owns its own window; the legacy model addresses are deep links
  // to that host and keep their old paths for callers and bookmarks.
  { path: "/profiles", surface: "configure-runs-on", scope: "models" },
  { path: "/models", surface: "configure-runs-on", scope: "models" },
  // HS-100-10 — Studio died; its address lands on Settings (the tools
  // it launched are search-reachable).
  { path: "/studio", surface: "configure-settings" },
  // Betterment AG1: the old Agents application is unmapped; its address
  // opens Agents (the Conductor window).
  { path: "/companion", surface: "open-conductor" },
  // PHILO-14 C4: the Conductor drawer, where agents live.
  { path: "/conductor", surface: "open-conductor" },
  { path: "/terminals", surface: "open-terminals" },
  { path: "/docs/dictation-runtime", surface: "read-runtime-docs" },
  { path: "/design/components", surface: "design-components" },
];
