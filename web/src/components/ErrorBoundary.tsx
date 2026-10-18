import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[500px] flex items-center justify-center p-6">
          <div className="panel bg-[#0e161c] border-[#293b48] p-8 max-w-lg w-full text-center space-y-4 shadow-2xl">
            <div className="w-14 h-14 mx-auto rounded-xl bg-[#2a1a1d] text-[#ea857c] flex items-center justify-center border border-[#4d292f]">
              <AlertTriangle size={28} />
            </div>
            <h2 className="text-xl font-bold text-[#eff5f2] font-sans">
              View Rendering Notice
            </h2>
            <p className="text-sm text-[#8799a0] leading-relaxed">
              An unexpected error occurred while rendering this data view.
            </p>
            {this.state.error && (
              <pre className="text-xs text-[#ea857c] bg-[#1a1012] border border-[#3e1f24] rounded-lg p-3 text-left font-mono overflow-auto max-h-36">
                {this.state.error.message}
              </pre>
            )}
            <div className="flex items-center justify-center gap-3 pt-3">
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.reload();
                }}
                className="outline-button"
              >
                <RefreshCw size={14} />
                <span>Reload View</span>
              </button>
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.href = '/';
                }}
                className="px-4 py-2 bg-[#1b3a2d] text-[#8ce2be] hover:bg-[#234c3b] rounded-lg text-xs font-semibold font-mono transition inline-flex items-center gap-2"
              >
                <Home size={14} />
                <span>Back to Overview</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
