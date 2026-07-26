import { useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { Book } from '../api/books'
import BookCard from './BookCard'
import { staggerContainer, fadeUp } from '../utils/motion'

interface Props {
  title: string
  books: Book[]
  isLoading?: boolean
}

export default function BookCarousel({ title, books, isLoading }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)

  function scroll(direction: 'left' | 'right') {
    if (!scrollRef.current) return
    scrollRef.current.scrollBy({ left: direction === 'right' ? 600 : -600, behavior: 'smooth' })
  }

  return (
    <section className="mb-12">
      <div className="flex items-center justify-between mb-4 px-6">
        <h2 className="font-display text-xl text-text-primary">{title}</h2>
        <div className="flex gap-1">
          <button
            onClick={() => scroll('left')}
            className="p-1.5 rounded-lg border border-border text-text-secondary hover:text-text-primary hover:border-brand transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="p-1.5 rounded-lg border border-border text-text-secondary hover:text-text-primary hover:border-brand transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto px-6 pb-2 scrollbar-hide"
        style={{ scrollbarWidth: 'none' }}
      >
        <AnimatePresence mode="wait">
          {isLoading ? (
            <div key="skeleton" className="flex gap-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="flex-shrink-0 w-36">
                  <div className="w-36 h-52 rounded-lg bg-surface-raised animate-pulse mb-2" />
                  <div className="h-3 bg-surface-raised rounded animate-pulse mb-1.5 w-4/5" />
                  <div className="h-3 bg-surface-raised rounded animate-pulse w-3/5" />
                </div>
              ))}
            </div>
          ) : (
            <motion.div
              key="books"
              className="flex gap-4"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {books.map((book) => (
                <motion.div key={book.id} variants={fadeUp}>
                  <BookCard book={book} />
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}
