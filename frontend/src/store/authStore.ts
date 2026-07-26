import { create } from 'zustand'
import type { User } from '../api/auth'

interface AuthState {
  user: User | null
  isLoading: boolean
  isInitialized: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  setInitialized: () => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => {
  // Listen for 401 refresh failures from the axios interceptor
  if (typeof window !== 'undefined') {
    window.addEventListener('auth:logout', () => set({ user: null }))
  }

  return {
    user: null,
    isLoading: false,
    isInitialized: false,
    setUser: (user) => set({ user }),
    setLoading: (isLoading) => set({ isLoading }),
    setInitialized: () => set({ isInitialized: true }),
    logout: () => set({ user: null }),
  }
})
