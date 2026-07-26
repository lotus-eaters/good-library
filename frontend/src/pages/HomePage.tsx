import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Sparkles } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { booksApi, type Book } from '../api/books'
import { recommendationsApi } from '../api/recommendations'
import BookCarousel from '../components/BookCarousel'
import BookCard from '../components/BookCard'
import { fadeUp } from '../utils/motion'
import { cn } from '../utils/cn'

function WhyCard({ book }: { book: Book }) {
  const [explanation, setExplanation] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)

  async function handleWhy(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    setShowTooltip(true)
    if (explanation) return
    setIsLoading(true)
    try {
      const text = await recommendationsApi.getWhy(book.id)
      setExplanation(text)
    } catch {
      setExplanation('Recommended based on your reading taste.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative flex-shrink-0">
      <BookCard book={book} />
      <button
        onClick={handleWhy}
        className="absolute top-2 right-2 p-1 rounded-full bg-surface-card/90 border border-border hover:border-brand transition-colors"
        title="Why this?"
      >
        <Sparkles className="w-3 h-3 text-brand" />
      </button>

      <AnimatePresence>
        {showTooltip && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowTooltip(false)} />
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.15 }}
              className="absolute top-10 right-0 z-50 w-56 bg-surface-card border border-brand/30 rounded-xl p-3 shadow-xl"
            >
              <div className="flex items-center gap-1.5 mb-2">
                <Sparkles className="w-3 h-3 text-brand shrink-0" />
                <span className="text-xs font-medium text-brand">Why this?</span>
              </div>
              {isLoading ? (
                <div className="space-y-1.5">
                  <div className="h-2.5 bg-surface-raised rounded animate-pulse w-full" />
                  <div className="h-2.5 bg-surface-raised rounded animate-pulse w-4/5" />
                  <div className="h-2.5 bg-surface-raised rounded animate-pulse w-3/5" />
                </div>
              ) : (
                <p className="text-xs text-text-secondary leading-relaxed">{explanation}</p>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function HomePage() {
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const [newReleases, setNewReleases] = useState<Book[]>([])
  const [forYou, setForYou] = useState<Book[]>([])
  const [popular, setPopular] = useState<Book[]>([])
  const [loadingNew, setLoadingNew] = useState(true)
  const [loadingForYou, setLoadingForYou] = useState(true)
  const [loadingPopular, setLoadingPopular] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    booksApi.getNewReleases(undefined, 20)
      .then(setNewReleases)
      .finally(() => setLoadingNew(false))

    booksApi.getForYou(20)
      .then(setForYou)
      .finally(() => setLoadingForYou(false))

    booksApi.getPopular(20)
      .then(setPopular)
      .finally(() => setLoadingPopular(false))
  }, [])

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (searchQuery.trim()) navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
  }

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        className="px-6 pt-16 pb-12 text-center"
      >
        <h1 className="font-display text-5xl text-text-primary mb-3">
          Your reading life,<br />
          <span className="italic text-brand">organised.</span>
        </h1>
        <p className="text-text-secondary mb-8 text-sm">
          Welcome back, {user?.display_name ?? user?.username}
        </p>

        <form onSubmit={handleSearchSubmit} className="max-w-md mx-auto relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search books, authors…"
            className="w-full bg-surface-raised border border-border rounded-xl pl-11 pr-4 py-3 text-text-primary text-sm focus:outline-none focus:border-brand transition-colors"
          />
        </form>
      </motion.div>

      {/* For You — custom cards with "Why this?" button */}
      <div className="mb-10">
        <div className="px-6 mb-4">
          <h2 className="font-display text-xl text-text-primary">For You</h2>
        </div>
        {loadingForYou ? (
          <BookCarousel title="" books={[]} isLoading={true} />
        ) : (
          <div className="px-6 flex gap-4 overflow-x-auto pb-2" style={{ scrollbarWidth: 'none' }}>
            {forYou.map((book) => (
              <WhyCard key={book.id} book={book} />
            ))}
          </div>
        )}
      </div>

      <BookCarousel title="Popular Right Now" books={popular} isLoading={loadingPopular} />
      <BookCarousel title="New Releases" books={newReleases} isLoading={loadingNew} />

      {/* Browse link */}
      <div className="text-center pb-16">
        <Link
          to="/search"
          className="text-sm text-text-secondary hover:text-brand transition-colors"
        >
          Browse all books →
        </Link>
      </div>
    </div>
  )
}
