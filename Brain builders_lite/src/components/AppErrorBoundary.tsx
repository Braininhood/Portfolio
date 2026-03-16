import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class AppErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error("AppErrorBoundary caught:", error);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6" style={{ background: "#fef2f2" }}>
          <div className="max-w-lg w-full rounded-lg border-2 border-red-300 bg-white p-6 shadow-lg">
            <h1 className="text-xl font-bold text-red-700">Something went wrong</h1>
            <p className="mt-3 text-sm text-gray-800 font-mono break-all">{this.state.error.message}</p>
            <pre className="mt-3 text-xs text-gray-600 overflow-auto max-h-32">{this.state.error.stack}</pre>
            <button
              type="button"
              className="mt-4 px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
