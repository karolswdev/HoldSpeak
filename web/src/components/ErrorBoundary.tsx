import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button, InlineMessage, Panel } from "./signal/Signal";

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("HoldSpeak route failed", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="page-wrap">
        <Panel title="This surface needs a reset" eyebrow="Route error">
          <InlineMessage tone="error">
            {this.state.error.message || "The route could not render."}
          </InlineMessage>
          <Button
            onClick={() => {
              this.setState({ error: null });
              window.location.reload();
            }}
          >
            Reload HoldSpeak
          </Button>
        </Panel>
      </div>
    );
  }
}
