import { useEffect, useState, useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, SlidersHorizontal } from 'lucide-react'
import { booksApi, type Book } from '../api/books'
import BookCard from '../components/BookCard'
import { fadeUp, staggerContainer } from '../utils/motion'
import { cn } from '../utils/cn'

type SortOption = 'relevant' | 'rating' | 'newest'
type SearchMode = 'keyword' | 'semantic'

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [books, setBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [activeGenre, setActiveGenre] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortOption>('relevant')
  const [showSort, setShowSort] = useState(false)
  const [mode, setMode] = useState<SearchMode>('keyword')

  const debouncedQuery = useDebounce(query, mode === 'keyword' ? 300 : 600)

  const search = useCallback(async (q: string, searchMode: SearchMode) => {
    if (!q.trim()) {
      setBooks([])
      setHasSearched(false)
      setActiveGenre(null)
      return
    }
    setIsLoading(true)
    setHasSearched(true)
    setActiveGenre(null)
    try {
      const results = searchMode === 'semantic'
        ? await booksApi.semanticSearch(q.trim())
        : await booksApi.search(q.trim())
      setBooks(results)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    setSearchParams(debouncedQuery ? { q: debouncedQuery } : {}, { replace: true })
    search(debouncedQuery, mode)
  }, [debouncedQuery, mode, search, setSearchParams])

  // Derive unique genres from results
  const genres = useMemo(() => {
    const all = books.flatMap((b) => b.genres ?? [])
    return [...new Set(all)].sort()
  }, [books])

  // Filter then sort — no API call, pure in-memory
  const filteredAndSorted = useMemo(() => {
    let result = activeGenre
      ? books.filter((b) => b.genres?.includes(activeGenre))
      : books

    if (sortBy === 'rating') {
      result = [...result].sort((a, b) => (b.average_rating ?? 0) - (a.average_rating ?? 0))
    } else if (sortBy === 'newest') {
      result = [...result].sort((a, b) => {
        const ya = a.published_date ? parseInt(a.published_date.slice(0, 4)) : 0
        const yb = b.published_date ? parseInt(b.published_date.slice(0, 4)) : 0
        return yb - ya
      })
    }

    return result
  }, [books, activeGenre, sortBy])

  const SORT_LABELS: Record<SortOption, string> = {
    relevant: 'Most Relevant',
    rating: 'Highest Rated',
    newest: 'Newest First',
  }

  return (
    <div className="min-h-screen px-6 pt-10">
      {/* Search input */}
      <div className="max-w-2xl mx-auto mb-4 relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search books, authors…"
          autoFocus
          className="w-full bg-surface-raised border border-border rounded-xl pl-11 pr-4 py-3 text-text-primary text-sm focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      {/* Mode toggle */}
      <div className="max-w-2xl mx-auto mb-6 flex items-center gap-1 p-1 bg-surface-raised border border-border rounded-xl w-fit">
        {(['keyword', 'semantic'] as SearchMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              'px-4 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize',
              mode === m
                ? 'bg-brand text-white shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
            {m === 'semantic' ? '✦ Semantic' : 'Keyword'}
          </button>
        ))}
      </div>

      {/* Filters row — only shown when there are results */}
      <AnimatePresence>
        {books.length > 0 && !isLoading && (
          <motion.div
            key="filters"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="max-w-2xl mx-auto mb-6 flex items-center gap-2 flex-wrap"
          >
            {/* Genre chips */}
            <button
              onClick={() => setActiveGenre(null)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors border',
                activeGenre === null
                  ? 'bg-brand text-white border-brand'
                  : 'border-border text-text-secondary hover:border-brand hover:text-text-primary'
              )}
            >
              All
            </button>
            {genres.map((genre) => (
              <button
                key={genre}
                onClick={() => setActiveGenre(activeGenre === genre ? null : genre)}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium transition-colors border capitalize',
                  activeGenre === genre
                    ? 'bg-brand text-white border-brand'
                    : 'border-border text-text-secondary hover:border-brand hover:text-text-primary'
                )}
              >
                {genre}
              </button>
            ))}

            {/* Sort dropdown */}
            <div className="relative ml-auto">
              <button
                onClick={() => setShowSort((s) => !s)}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-border text-text-secondary hover:border-brand hover:text-text-primary transition-colors"
              >
                <SlidersHorizontal className="w-3 h-3" />
                {SORT_LABELS[sortBy]}
              </button>
              <AnimatePresence>
                {showSort && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.1 }}
                    className="absolute right-0 top-full mt-1.5 w-40 bg-surface-card border border-border rounded-xl shadow-lg overflow-hidden z-10"
                  >
                    {(['relevant', 'rating', 'newest'] as SortOption[]).map((opt) => (
                      <button
                        key={opt}
                        onClick={() => { setSortBy(opt); setShowSort(false) }}
                        className={cn(
                          'w-full text-left px-4 py-2.5 text-xs transition-colors hover:bg-surface-raised',
                          sortBy === opt ? 'text-brand' : 'text-text-primary'
                        )}
                      >
                        {SORT_LABELS[opt]}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence mode="wait">
        {isLoading && (
          <motion.div
            key="loading"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6"
          >
            {[...Array(12)].map((_, i) => (
              <div key={i}>
                <div className="w-full aspect-[2/3] rounded-lg bg-surface-raised animate-pulse mb-2" />
                <div className="h-3 bg-surface-raised rounded animate-pulse mb-1.5 w-4/5" />
                <div className="h-3 bg-surface-raised rounded animate-pulse w-3/5" />
              </div>
            ))}
          </motion.div>
        )}

        {!isLoading && hasSearched && filteredAndSorted.length === 0 && (
          <motion.p
            key="empty"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            className="text-center text-text-secondary text-sm mt-16"
          >
            {activeGenre
              ? `No ${activeGenre} books in these results`
              : `No books found for "${debouncedQuery}"`}
          </motion.p>
        )}

        {!isLoading && filteredAndSorted.length > 0 && (
          <motion.div
            key="results"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6"
          >
            {filteredAndSorted.map((book) => (
              <motion.div key={book.id} variants={fadeUp}>
                <BookCard book={book} className="w-full" />
              </motion.div>
            ))}
          </motion.div>
        )}

        {!hasSearched && (
          <motion.p
            key="prompt"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            className="text-center text-text-secondary text-sm mt-16"
          >
            {mode === 'semantic'
              ? 'Describe what you\'re in the mood for — "a quiet book about grief" works'
              : 'Search for a book or author to get started'}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}
