import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { AmbientLayer } from "@w/components/AmbientLayer";
import { publishAftercare } from "@w/desk/intelligenceAttention";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import "@w/styles/global.css";
import "@w/styles/react-app.css";

class FixtureWebSocket {
  static readonly OPEN = 1;
  readonly readyState = 0;
  addEventListener() {}
  send() {}
  close() {}
}

Object.defineProperty(window, "WebSocket", {
  configurable: true,
  value: FixtureWebSocket,
});

function Fixture() {
  useEffect(() => {
    publishAftercare({
      meeting_id: "component-fixture-zero",
      title: "Morning review",
      open_total: 0,
      decided_total: 0,
    });
  }, []);

  return (
    <RuntimeBusProvider>
      <AmbientLayer />
    </RuntimeBusProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Fixture />
  </StrictMode>,
);
