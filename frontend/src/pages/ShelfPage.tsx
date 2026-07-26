import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Search } from 'lucide-react'
import { useShelfStore } from '../store/shelfStore'
import BookCard from '../components/BookCard'
import { fadeUp, staggerContainer } from '../utils/motion'

const SHELF_LABELS: Record<string, string> = {
  want_to_read: 'Want to Read',
  currently_reading: 'Currently Reading',
  already_read: 'Already Read',
}

export default function ShelfPage() {
  const { shelfType } = useParams<{ shelfType: string }>()
  const { shelves, fetchShelves } = useShelfStore()

  useEffect(() => {
    if (shelves.length === 0) fetchShelves()
  }, [fetchShelves, shelves.length])

  const shelf = shelves.find((s) => s.shelf_type === shelfType)
  const books = shelf?.books ?? []
  const label = SHELF_LABELS[shelfType ?? ''] ?? 'Shelf'

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="min-h-screen px-6 py-10 max-w-4xl mx-auto"
    >
      <Link
        to="/profile"
        className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary text-sm mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to profile
      </Link>

      <div className="flex items-baseline gap-3 mb-8">
        <h1 className="font-display text-3xl text-text-primary">{label}</h1>
        <span className="text-text-secondary text-sm">
          {books.length} {books.length === 1 ? 'book' : 'books'}
        </span>
      </div>

      {books.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed border-border rounded-xl text-center">
          <p className="text-text-secondary mb-4">No books in this shelf yet</p>
          <Link
            to="/search"
            className="inline-flex items-center gap-2 text-sm text-brand hover:text-brand-dark transition-colors"
          >
            <Search className="w-4 h-4" />
            Explore books
          </Link>
        </div>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6"
        >
          {books.map((book) => (
            <motion.div key={book.id} variants={fadeUp}>
              <BookCard book={book} className="w-full" />
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}
