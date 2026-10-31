// The briefing page's own entry (PG-DIRECTION DIR2): web/briefing.html, served
// by the hub at /b/<token>. It shares the desk's material and kit, never its
// auth client: no owner token is read, set or sent from this page.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BriefingApp } from "./BriefingApp";
import { tokenFromPath } from "./api";
// One stylesheet: briefing.css @imports the desk's material, so no desk
// stylesheet module is shared with the page (the desk's own CSS order stays).
import "./briefing.css";

const root = document.getElementById("root");
if (!root) throw new Error("HoldSpeak root element is missing");

createRoot(root).render(
  <StrictMode>
    <BriefingApp token={tokenFromPath(window.location.pathname)} />
  </StrictMode>,
);
