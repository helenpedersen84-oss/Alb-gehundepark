import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('App crash caught by ErrorBoundary:', error, info);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const msg = this.state.error?.message || String(this.state.error || 'Ukendt fejl');
      return (
        <div
          data-testid="error-boundary"
          className="min-h-screen bg-[#EFE9DE] flex flex-col items-center justify-center px-6 text-center"
        >
          <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-3xl p-10 max-w-md w-full shadow-xl">
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-2">Ups – noget gik galt</h1>
            <p className="text-[#5F584B] text-sm mb-6">
              Der opstod en uventet fejl. Prøv at genindlæse siden. Sker det igen, så kontakt os.
            </p>
            <pre className="text-[11px] text-left text-[#9A5252] bg-white border border-[#E2D9C9] rounded-xl p-3 mb-6 overflow-auto max-h-40 whitespace-pre-wrap">
              {msg}
            </pre>
            <button
              data-testid="error-boundary-reload"
              onClick={this.handleReload}
              className="bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm transition-colors"
            >
              Genindlæs siden
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
