import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { bootstrapAuth } from "./lib/auth";
import { DeskChangedRefresh } from "./desk/useDeskChangedRefresh";
import { RuntimeBusProvider } from "./runtime/RuntimeBus";
import "./styles/global.css";
import "./styles/react-app.css";

bootstrapAuth();

const root = document.getElementById("root");
if (!root) throw new Error("HoldSpeak root element is missing");

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <RuntimeBusProvider>
        {/* HS-200-45 R4: a write from any caller -- another tab, the iPad, an
            agent over MCP -- reaches this desk as one `desk_changed` frame. */}
        <DeskChangedRefresh />
        <App />
      </RuntimeBusProvider>
    </BrowserRouter>
  </StrictMode>,
);
