import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl text-white font-semibold mb-2">Что-то пошло не так</h2>
          <p className="text-sm text-[#ef4444] mb-4 max-w-md break-all">
            {this.state.error?.message || 'Неизвестная ошибка'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.href = '/';
            }}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors"
          >
            🔄 На главную
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
