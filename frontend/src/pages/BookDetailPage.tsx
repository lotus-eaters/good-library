import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Star, BookOpen, ChevronDown, Sparkles } from 'lucide-react'
import { booksApi, type Book } from '../api/books'
import { ratingsApi, type BookReview } from '../api/ratings'
import { useShelfStore } from '../store/shelfStore'
import { toast } from '../store/toastStore'
import BookCard from '../components/BookCard'
import { fadeUp, scaleUp } from '../utils/motion'
import { cn } from '../utils/cn'

const SHELF_LABELS: Record<string, string> = {
  want_to_read: 'Want to Read',
  currently_reading: 'Currently Reading',
  already_read: 'Already Read',
}

function RatingSection({ bookId }: { bookId: number }) {
  const [hovered, setHovered] = useState(0)
  const [selected, setSelected] = useState(0)
  const [reviewText, setReviewText] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    ratingsApi.getMyRating(bookId).then((r) => {
      if (r) {
        setSelected(r.score)
        setReviewText(r.review ?? '')
      }
    }).catch(() => {})
  }, [bookId])

  async function handleSave() {
    if (!selected) return
    setIsSaving(true)
    const previous = { score: selected, review: reviewText }
    try {
      await ratingsApi.rate(bookId, selected, reviewText || undefined)
      toast.success(`Rated ${selected} star${selected !== 1 ? 's' : ''}`)
    } catch {
      setSelected(previous.score)
      setReviewText(previous.review)
      toast.error('Failed to save rating')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      {/* Stars */}
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((score) => (
          <motion.button
            key={score}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
            onMouseEnter={() => setHovered(score)}
            onMouseLeave={() => setHovered(0)}
            onClick={() => setSelected(score)}
            className="p-0.5"
          >
            <Star
              className={cn(
                'w-6 h-6 transition-colors',
                score <= (hovered || selected)
                  ? 'fill-star text-star'
                  : 'fill-none text-text-secondary'
              )}
            />
          </motion.button>
        ))}
      </div>

      {/* Review textarea — only show after a star is selected */}
      <AnimatePresence>
        {selected > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2 overflow-hidden"
          >
            <textarea
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              placeholder="Write a review… (optional)"
              rows={3}
              maxLength={5000}
              className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-brand transition-colors resize-none"
            />
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-3 py-1.5 rounded-lg bg-brand text-white text-xs font-medium hover:bg-brand-dark transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save rating'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function AddToShelfDropdown({ book }: { book: Book }) {
  const [open, setOpen] = useState(false)
  const { shelves, isLoading, fetchShelves, addBook, removeBook, getShelfForBook } = useShelfStore()
  const currentShelfType = getShelfForBook(book.id)
  const currentShelf = shelves.find((s) => s.shelf_type === currentShelfType)

  function handleOpen() {
    if (shelves.length === 0) fetchShelves()
    setOpen((o) => !o)
  }

  async function handleSelect(shelfId: number) {
    setOpen(false)
    try {
      await addBook(shelfId, book)
    } catch { /* toast already fired in store */ }
  }

  async function handleRemove() {
    if (!currentShelf) return
    setOpen(false)
    try {
      await removeBook(currentShelf.id, book.id)
    } catch { /* toast already fired in store */ }
  }

  return (
    <div className="relative">
      <button
        onClick={handleOpen}
        className={cn(
          'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors',
          currentShelfType
            ? 'bg-brand text-white hover:bg-brand-dark'
            : 'border border-border text-text-primary hover:border-brand'
        )}
      >
        <BookOpen className="w-4 h-4" />
        {currentShelfType ? SHELF_LABELS[currentShelfType] : 'Add to Shelf'}
        <ChevronDown className={cn('w-4 h-4 transition-transform', open && 'rotate-180')} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            variants={scaleUp}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="absolute top-full mt-2 left-0 w-48 bg-surface-card border border-border rounded-xl shadow-lg overflow-hidden z-10"
          >
            {isLoading && shelves.length === 0 ? (
              <p className="px-4 py-3 text-sm text-text-secondary">Loading shelves…</p>
            ) : shelves.length === 0 ? (
              <p className="px-4 py-3 text-sm text-text-secondary">No shelves found</p>
            ) : (
              shelves.map((shelf) => (
                <button
                  key={shelf.id}
                  onClick={() => handleSelect(shelf.id)}
                  className={cn(
                    'w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-surface-raised',
                    shelf.shelf_type === currentShelfType ? 'text-brand' : 'text-text-primary'
                  )}
                >
                  {SHELF_LABELS[shelf.shelf_type]}
                </button>
              ))
            )}
            {currentShelfType && (
              <>
                <div className="h-px bg-border mx-3" />
                <button
                  onClick={handleRemove}
                  className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-surface-raised transition-colors"
                >
                  Remove from shelf
                </button>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function AISummary({ bookId }: { bookId: number }) {
  const [summary, setSummary] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [triggered, setTriggered] = useState(false)

  async function handleGenerate() {
    setTriggered(true)
    setIsLoading(true)
    try {
      const text = await booksApi.getSummary(bookId)
      setSummary(text)
    } catch {
      setSummary('Could not generate summary. Try again later.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mb-10 p-4 rounded-xl border border-brand/20 bg-brand/5">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-brand" />
        <h2 className="font-display text-lg text-text-primary">AI Summary</h2>
      </div>

      <AnimatePresence mode="wait">
        {!triggered && (
          <motion.button
            key="btn"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleGenerate}
            className="text-sm text-brand hover:text-brand-dark transition-colors underline underline-offset-2"
          >
            Generate a 2-sentence summary
          </motion.button>
        )}

        {isLoading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            <div className="h-3 bg-brand/10 rounded animate-pulse w-full" />
            <div className="h-3 bg-brand/10 rounded animate-pulse w-4/5" />
          </motion.div>
        )}

        {summary && !isLoading && (
          <motion.p
            key="summary"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-text-secondary leading-relaxed"
          >
            {summary}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}

function ReviewCard({ review }: { review: BookReview }) {
  return (
    <div className="bg-surface-raised border border-border rounded-xl p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-text-primary">{review.reviewer_name}</span>
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5].map((s) => (
            <Star
              key={s}
              className={cn(
                'w-3.5 h-3.5',
                s <= review.score ? 'fill-star text-star' : 'fill-none text-text-secondary'
              )}
            />
          ))}
        </div>
      </div>
      <p className="text-sm text-text-secondary leading-relaxed">{review.review}</p>
      <p className="text-xs text-text-secondary">
        {new Date(review.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
      </p>
    </div>
  )
}

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [book, setBook] = useState<Book | null>(null)
  const [similar, setSimilar] = useState<Book[]>([])
  const [reviews, setReviews] = useState<BookReview[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { fetchShelves, shelves } = useShelfStore()

  useEffect(() => {
    if (shelves.length === 0) fetchShelves()
  }, [fetchShelves, shelves.length])

  useEffect(() => {
    if (!id) return
    setIsLoading(true)
    const bookId = Number(id)
    booksApi.getById(bookId)
      .then((b) => {
        setBook(b)
        return Promise.all([
          booksApi.getSimilar(b.id),
          ratingsApi.getBookReviews(b.id),
        ])
      })
      .then(([sim, revs]) => {
        setSimilar(sim)
        setReviews(revs)
      })
      .catch((err) => console.error('BookDetailPage error:', err))
      .finally(() => setIsLoading(false))
  }, [id])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-brand border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!book) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-secondary">Book not found.</p>
      </div>
    )
  }

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="min-h-screen px-6 py-10 max-w-3xl mx-auto"
    >
      {/* Header */}
      <div className="flex gap-8 mb-10">
        <div className="flex-shrink-0 w-40 h-60 rounded-xl overflow-hidden bg-surface-raised border border-border">
          {book.cover_url ? (
            <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center p-4">
              <span className="font-display text-sm text-text-secondary text-center">{book.title}</span>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h1 className="font-display text-3xl text-text-primary mb-1 leading-tight">{book.title}</h1>
          {book.authors && (
            <p className="text-text-secondary mb-4">{book.authors}</p>
          )}

          <div className="flex flex-wrap gap-3 mb-4">
            <AddToShelfDropdown book={book} />
          </div>

          <div className="mb-2">
            <p className="text-xs text-text-secondary mb-2">Your rating</p>
            <RatingSection bookId={book.id} />
          </div>

          <div className="flex gap-4 text-xs text-text-secondary mt-4">
            {book.page_count && <span>{book.page_count} pages</span>}
            {book.published_date && <span>{book.published_date.slice(0, 4)}</span>}
            {(book.average_rating ?? 0) > 0 && (
              <span className="flex items-center gap-1">
                <Star className="w-3 h-3 fill-star text-star" />
                {book.average_rating!.toFixed(1)} ({book.ratings_count?.toLocaleString()} ratings)
              </span>
            )}
          </div>
        </div>
      </div>

      {/* AI Summary */}
      {book.description && <AISummary bookId={book.id} />}

      {/* Description */}
      {book.description && (
        <div className="mb-10">
          <h2 className="font-display text-lg text-text-primary mb-3">About this book</h2>
          <p className="text-text-secondary text-sm leading-relaxed">{book.description}</p>
        </div>
      )}

      {/* Community reviews */}
      {reviews.length > 0 && (
        <div className="mb-10">
          <h2 className="font-display text-lg text-text-primary mb-4">
            Community reviews
            <span className="ml-2 text-sm font-sans text-text-secondary">({reviews.length})</span>
          </h2>
          <div className="space-y-3">
            {reviews.map((r) => (
              <ReviewCard key={r.id} review={r} />
            ))}
          </div>
        </div>
      )}

      {/* Similar books */}
      {similar.length > 0 && (
        <div>
          <h2 className="font-display text-lg text-text-primary mb-4">Similar books</h2>
          <div className="flex gap-4 overflow-x-auto pb-2" style={{ scrollbarWidth: 'none' }}>
            {similar.map((b) => (
              <BookCard key={b.id} book={b} />
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
