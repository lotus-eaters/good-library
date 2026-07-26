import { Component, type ErrorInfo, type ReactNode } from 'react'
import { toast } from '../store/toastStore'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Uncaught error:', error, info.componentStack)
    toast.error('Something went wrong. Please try refreshing.')
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center gap-4 text-center px-6">
          <p className="font-display text-4xl">💥</p>
          <h1 className="font-display text-2xl text-text-primary">Something went wrong</h1>
          <p className="text-text-secondary text-sm max-w-sm">
            An unexpected error occurred. Try refreshing the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 px-4 py-2 rounded-lg bg-brand text-white text-sm hover:bg-brand-dark transition-colors"
          >
            Refresh page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
