import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import type { Book } from '../api/books'
import { cn } from '../utils/cn'

interface Props {
  book: Book
  className?: string
}

export default function BookCard({ book, className }: Props) {
  return (
    <motion.div
      layout
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={cn('flex-shrink-0 w-36', className)}
    >
      <Link to={`/books/${book.id}`} className="block group">
        <div className="relative w-36 h-52 rounded-lg overflow-hidden bg-surface-raised border border-border mb-2">
          {book.cover_url ? (
            <img
              src={book.cover_url}
              alt={book.title}
              loading="lazy"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center p-3">
              <span className="font-display text-xs text-text-secondary text-center leading-snug line-clamp-4">
                {book.title}
              </span>
            </div>
          )}
        </div>

        <p className="text-text-primary text-sm font-medium leading-snug line-clamp-2 mb-0.5">
          {book.title}
        </p>

        {book.authors && (
          <p className="text-text-secondary text-xs line-clamp-1">
            {book.authors}
          </p>
        )}

        {(book.average_rating ?? 0) > 0 && (
          <div className="flex items-center gap-1 mt-1">
            <Star className="w-3 h-3 fill-star text-star" />
            <span className="text-xs text-text-secondary">{book.average_rating.toFixed(1)}</span>
          </div>
        )}
      </Link>
    </motion.div>
  )
}
