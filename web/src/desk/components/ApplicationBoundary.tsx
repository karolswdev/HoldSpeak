import { Component, type ErrorInfo, type ReactNode } from "react";

interface ApplicationBoundaryProps {
  label: string;
  children: ReactNode;
  onRetry?: () => void;
}

interface ApplicationBoundaryState {
  failed: boolean;
  failure: Error | null;
}

/** A failed Desk program loses its own glass, never the operating room. */
export class ApplicationBoundary extends Component<
  ApplicationBoundaryProps,
  ApplicationBoundaryState
> {
  state: ApplicationBoundaryState = { failed: false, failure: null };

  static getDerivedStateFromError(failure: Error): ApplicationBoundaryState {
    return { failed: true, failure };
  }

  componentDidCatch(_failure: Error, _info: ErrorInfo): void {
    // Rendering the named in-window refusal is the recovery contract. Error
    // telemetry can subscribe above this boundary without console noise.
  }

  private retry = () => {
    this.props.onRetry?.();
    this.setState({ failed: false, failure: null });
  };

  render(): ReactNode {
    if (!this.state.failed) return this.props.children;
    return (
      <section className="desk-application-error" role="alert">
        <strong>{this.props.label} stopped</strong>
        <p>{this.state.failure?.message || "The application could not draw."}</p>
        <button type="button" className="desk-chip" onClick={this.retry}>
          Reload application
        </button>
      </section>
    );
  }
}
