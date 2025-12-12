import React from 'react';

/**
 * Catches render-time errors so the UI doesn't go white-screen.
 * Shows a friendly message with the stack for quick debugging.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null, errorInfo: null };
  }

  componentDidCatch(error, errorInfo) {
    // Capture the error so we can show it in the UI and console
    this.setState({ error, errorInfo });
    console.error('UI ErrorBoundary caught an error', error, errorInfo);
  }

  render() {
    const { error, errorInfo } = this.state;

    if (errorInfo) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow border border-red-200 p-6">
            <h2 className="text-xl font-semibold text-red-600 mb-3">
              Something went wrong in the app
            </h2>
            <p className="text-gray-700 mb-4">
              The UI hit an unexpected error. Try reloading or sharing the details below.
            </p>
            <div className="bg-gray-50 border border-gray-200 rounded p-3 max-h-64 overflow-auto text-sm font-mono text-gray-800">
              {error && <div className="mb-2">{error.toString()}</div>}
              <pre className="whitespace-pre-wrap">
                {errorInfo.componentStack}
              </pre>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
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

export default ErrorBoundary;
