import React from "react";

interface State {
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Unhandled render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen w-full flex items-center justify-center bg-paper px-6">
          <div className="max-w-md text-center">
            <h1 className="font-serif text-xl text-ink font-semibold mb-2">Something went wrong</h1>
            <p className="text-sm text-slate mb-4">
              {this.state.error.message || "An unexpected error occurred while rendering this page."}
            </p>
            <button
              onClick={() => { this.setState({ error: null }); window.location.href = "/"; }}
              className="text-sm font-medium px-4 py-2 rounded-md bg-ink text-paper"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
