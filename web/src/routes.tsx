import { lazy, type ComponentType, type LazyExoticComponent } from "react";

export interface ProductRoute {
  path: string;
  label: string;
  section: "daily" | "studio" | "support";
  component: LazyExoticComponent<ComponentType>;
  immersive?: boolean;
}

const Desk = lazy(() => import("./desk/DeskApp"));
const Welcome = lazy(() => import("./pages/WelcomePage"));
const Setup = lazy(() => import("./pages/SetupPage"));
const Settings = lazy(() => import("./pages/SettingsPage"));
const Profiles = lazy(() => import("./pages/ProfilesPage"));
const Dictation = lazy(() => import("./pages/DictationPage"));
const Activity = lazy(() => import("./pages/ActivityPage"));
const Commands = lazy(() => import("./pages/CommandsPage"));
const Cadence = lazy(() => import("./pages/CadencePage"));
const Live = lazy(() => import("./pages/LivePage"));
const History = lazy(() => import("./pages/HistoryPage"));
const Studio = lazy(() => import("./pages/StudioPage"));
const Workbench = lazy(() => import("./pages/WorkbenchPage"));
const Companion = lazy(() => import("./pages/CompanionPage"));
const Presence = lazy(() => import("./pages/PresencePage"));
const RuntimeDocs = lazy(() => import("./pages/RuntimeDocsPage"));
const Components = lazy(() => import("./pages/ComponentsPage"));

export const PRODUCT_ROUTES: ProductRoute[] = [
  {
    path: "/",
    label: "Desk",
    section: "daily",
    component: Desk,
    immersive: true,
  },
  {
    path: "/welcome",
    label: "Welcome",
    section: "support",
    component: Welcome,
    immersive: true,
  },
  { path: "/setup", label: "Setup", section: "support", component: Setup },
  {
    path: "/dictation",
    label: "Dictation",
    section: "daily",
    component: Dictation,
  },
  { path: "/live", label: "Live meeting", section: "daily", component: Live },
  { path: "/history", label: "Meetings", section: "daily", component: History },
  {
    path: "/meetings",
    label: "Meetings",
    section: "daily",
    component: History,
  },
  {
    path: "/settings",
    label: "Settings",
    section: "daily",
    component: Settings,
  },
  {
    path: "/activity",
    label: "Activity",
    section: "studio",
    component: Activity,
  },
  {
    path: "/commands",
    label: "Commands",
    section: "studio",
    component: Commands,
  },
  { path: "/cadence", label: "Cadence", section: "studio", component: Cadence },
  { path: "/studio", label: "Studio", section: "studio", component: Studio },
  {
    path: "/workbench",
    label: "Workbench",
    section: "studio",
    component: Workbench,
  },
  {
    path: "/profiles",
    label: "Profiles",
    section: "studio",
    component: Profiles,
  },
  {
    path: "/companion",
    label: "Companion",
    section: "support",
    component: Companion,
  },
  {
    path: "/presence",
    label: "Presence",
    section: "support",
    component: Presence,
    immersive: true,
  },
  {
    path: "/docs/dictation-runtime",
    label: "Runtime guide",
    section: "support",
    component: RuntimeDocs,
  },
  {
    path: "/design/components",
    label: "Components",
    section: "support",
    component: Components,
  },
];
