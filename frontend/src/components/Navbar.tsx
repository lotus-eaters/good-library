import { Link, useNavigate } from 'react-router-dom'
import { Search, User, LogOut, Network } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/auth'

export default function Navbar() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  async function handleLogout() {
    await authApi.logout().catch(() => {})
    logout()
    navigate('/login')
  }

  return (
    <nav className="border-b border-border px-6 py-3 flex items-center justify-between sticky top-0 bg-surface z-20">
      <Link to="/" className="font-display text-xl text-text-primary hover:text-brand transition-colors">
        good_library
      </Link>

      <div className="flex items-center gap-3">
        <Link
          to="/search"
          className="p-2 text-text-secondary hover:text-text-primary transition-colors"
        >
          <Search className="w-4 h-4" />
        </Link>

        {user && (
          <>
            <Link
              to="/graph"
              className="p-2 text-text-secondary hover:text-text-primary transition-colors"
              title="Knowledge Graph"
            >
              <Network className="w-4 h-4" />
            </Link>
            <Link
              to="/profile"
              className="p-2 text-text-secondary hover:text-text-primary transition-colors"
            >
              <User className="w-4 h-4" />
            </Link>
          </>
        )}

        <button
          onClick={handleLogout}
          className="p-2 text-text-secondary hover:text-red-400 transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </nav>
  )
}
