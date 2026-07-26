import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen, Search, ChevronRight, Trophy, Check, RefreshCw, Sparkles } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useShelfStore } from '../store/shelfStore'
import { usersApi, type Challenge } from '../api/users'
import { toast } from '../store/toastStore'
import BookCard from '../components/BookCard'
import { fadeUp, staggerContainer } from '../utils/motion'
import { cn } from '../utils/cn'

const SHELF_LABELS: Record<string, string> = {
  want_to_read: 'Want to Read',
  currently_reading: 'Currently Reading',
  already_read: 'Already Read',
}

const SHELF_ORDER = ['currently_reading', 'want_to_read', 'already_read']

function Avatar({ user }: { user: { display_name: string | null; username: string; avatar_url: string | null } }) {
  if (user.avatar_url) {
    return (
      <img
        src={user.avatar_url}
        alt={user.display_name ?? user.username}
        className="w-20 h-20 rounded-full object-cover border-2 border-border"
      />
    )
  }
  const initials = (user.display_name ?? user.username).slice(0, 2).toUpperCase()
  return (
    <div className="w-20 h-20 rounded-full bg-brand flex items-center justify-center border-2 border-border">
      <span className="font-display text-2xl text-white">{initials}</span>
    </div>
  )
}

function ChallengeCard() {
  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [editing, setEditing] = useState(false)
  const [inputVal, setInputVal] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    usersApi.getChallenge().then(setChallenge).catch(() => {})
  }, [])

  async function handleSave() {
    const goal = parseInt(inputVal)
    if (isNaN(goal) || goal < 0) return
    setIsSaving(true)
    // Optimistic update
    if (challenge) setChallenge({ ...challenge, goal })
    setEditing(false)
    try {
      const updated = await usersApi.updateChallenge(goal)
      setChallenge(updated)
      toast.success(`Reading goal set to ${goal} books`)
    } catch {
      toast.error('Failed to update goal')
    } finally {
      setIsSaving(false)
    }
  }

  if (!challenge) return null

  const { year, goal, books_read_this_year } = challenge
  const percent = goal > 0 ? Math.min((books_read_this_year / goal) * 100, 100) : 0
  const achieved = goal > 0 && books_read_this_year >= goal

  return (
    <div className="bg-surface-raised border border-border rounded-xl p-5 mb-10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Trophy className={cn('w-4 h-4', achieved ? 'text-star' : 'text-brand')} />
          <h2 className="font-display text-lg text-text-primary">
            {year} Reading Challenge
          </h2>
          {achieved && <span className="text-xs bg-star/20 text-star px-2 py-0.5 rounded-full">Achieved! 🎉</span>}
        </div>

        {!editing && (
          <button
            onClick={() => { setInputVal(String(goal)); setEditing(true) }}
            className="text-xs text-text-secondary hover:text-brand transition-colors"
          >
            {goal === 0 ? 'Set goal' : 'Edit goal'}
          </button>
        )}
      </div>

      {goal === 0 && !editing ? (
        <p className="text-sm text-text-secondary">
          Set a reading goal for {year} and track your progress.{' '}
          <button
            onClick={() => { setInputVal(''); setEditing(true) }}
            className="text-brand hover:underline"
          >
            Set a goal →
          </button>
        </p>
      ) : (
        <>
          <div className="flex items-end justify-between mb-2">
            <span className="text-3xl font-display text-text-primary">
              {books_read_this_year}
              <span className="text-lg text-text-secondary font-sans"> / {goal} books</span>
            </span>
            <span className="text-sm text-text-secondary">{Math.round(percent)}%</span>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-surface-card rounded-full overflow-hidden mb-4">
            <motion.div
              className={cn('h-full rounded-full', achieved ? 'bg-star' : 'bg-brand')}
              initial={{ width: 0 }}
              animate={{ width: `${percent}%` }}
              transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
            />
          </div>
        </>
      )}

      {editing && (
        <div className="flex items-center gap-2 mt-2">
          <input
            type="number"
            min={0}
            max={10000}
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            placeholder="e.g. 52"
            autoFocus
            className="w-28 bg-surface-card border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-brand transition-colors"
          />
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="p-1.5 rounded-lg bg-brand text-white hover:bg-brand-dark transition-colors disabled:opacity-50"
          >
            <Check className="w-4 h-4" />
          </button>
          <button
            onClick={() => setEditing(false)}
            className="text-xs text-text-secondary hover:text-text-primary transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}

function InsightsCard() {
  const [insight, setInsight] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [triggered, setTriggered] = useState(false)

  async function load(refresh = false) {
    setTriggered(true)
    setIsLoading(true)
    try {
      const text = await usersApi.getInsights(refresh)
      setInsight(text)
    } catch {
      setInsight('Could not generate insights right now. Try again later.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-surface-raised border border-brand/20 rounded-xl p-5 mb-10">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-brand" />
          <h2 className="font-display text-lg text-text-primary">Your reading insights</h2>
        </div>
        {triggered && !isLoading && (
          <button
            onClick={() => load(true)}
            className="text-text-secondary hover:text-brand transition-colors"
            title="Refresh insights"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {!triggered ? (
        <button
          onClick={() => load()}
          className="text-sm text-brand hover:text-brand-dark transition-colors underline underline-offset-2"
        >
          Generate insights about your reading patterns
        </button>
      ) : isLoading ? (
        <div className="space-y-2">
          <div className="h-3 bg-brand/10 rounded animate-pulse w-full" />
          <div className="h-3 bg-brand/10 rounded animate-pulse w-5/6" />
          <div className="h-3 bg-brand/10 rounded animate-pulse w-4/6" />
        </div>
      ) : (
        <motion.p
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-text-secondary leading-relaxed"
        >
          {insight}
        </motion.p>
      )}
    </div>
  )
}

function ShelfSection({ shelfType, books }: { shelfType: string; books: import('../api/books').Book[] }) {
  return (
    <section className="mb-10">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display text-xl text-text-primary">
          {SHELF_LABELS[shelfType]}
          <span className="ml-2 text-sm font-sans text-text-secondary font-normal">
            {books.length} {books.length === 1 ? 'book' : 'books'}
          </span>
        </h2>
        <Link
          to={`/shelves/${shelfType}`}
          className="flex items-center gap-1 text-sm text-text-secondary hover:text-brand transition-colors"
        >
          View all <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      {books.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 border border-dashed border-border rounded-xl text-center">
          <BookOpen className="w-8 h-8 text-text-secondary mb-3" />
          <p className="text-text-secondary text-sm mb-4">No books here yet</p>
          <Link
            to="/search"
            className="flex items-center gap-2 text-sm text-brand hover:text-brand-dark transition-colors"
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
          className="flex gap-4 overflow-x-auto pb-2"
          style={{ scrollbarWidth: 'none' }}
        >
          {books.map((book) => (
            <motion.div key={book.id} variants={fadeUp}>
              <BookCard book={book} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </section>
  )
}

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const { shelves, fetchShelves, isLoading } = useShelfStore()

  useEffect(() => {
    if (shelves.length === 0) fetchShelves()
  }, [fetchShelves, shelves.length])

  if (!user) return null

  const totalBooks = shelves.reduce((sum, s) => sum + (s.books?.length ?? 0), 0)
  const sortedShelves = SHELF_ORDER
    .map((type) => shelves.find((s) => s.shelf_type === type))
    .filter((s): s is NonNullable<typeof s> => s != null)

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="min-h-screen px-6 py-10 max-w-4xl mx-auto"
    >
      {/* Header */}
      <div className="flex items-center gap-6 mb-10">
        <Avatar user={user} />
        <div>
          <h1 className="font-display text-2xl text-text-primary mb-0.5">
            {user.display_name ?? user.username}
          </h1>
          <p className="text-text-secondary text-sm">@{user.username}</p>
          {user.bio && (
            <p className="text-text-secondary text-sm mt-2 max-w-sm">{user.bio}</p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {SHELF_ORDER.map((shelfType) => {
          const count = shelves
            .filter((s) => s.shelf_type === shelfType)
            .reduce((sum, s) => sum + (s.books?.length ?? 0), 0)
          return (
            <div key={shelfType} className="bg-surface-raised border border-border rounded-xl p-4 text-center">
              <p className="font-display text-3xl text-text-primary mb-1">{count}</p>
              <p className="text-text-secondary text-xs">{SHELF_LABELS[shelfType]}</p>
            </div>
          )
        })}
      </div>

      {totalBooks > 0 && (
        <p className="text-text-secondary text-sm mb-8">
          {totalBooks} {totalBooks === 1 ? 'book' : 'books'} in your library
        </p>
      )}

      {/* Reading Challenge */}
      <ChallengeCard />

      {/* AI Insights */}
      <InsightsCard />

      {/* Shelves */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 rounded-full border-2 border-brand border-t-transparent animate-spin" />
        </div>
      ) : (
        sortedShelves.map((shelf) => (
          <ShelfSection key={shelf.id} shelfType={shelf.shelf_type} books={shelf.books ?? []} />
        ))
      )}
    </motion.div>
  )
}
