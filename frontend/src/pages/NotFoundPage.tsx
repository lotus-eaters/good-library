import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { fadeUp } from '../utils/motion'

export default function NotFoundPage() {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="min-h-screen flex flex-col items-center justify-center gap-4 text-center px-6"
    >
      <p className="font-display text-6xl text-brand">404</p>
      <h1 className="font-display text-2xl text-text-primary">Page not found</h1>
      <p className="text-text-secondary text-sm max-w-sm">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link
        to="/"
        className="mt-2 px-4 py-2 rounded-lg bg-brand text-white text-sm hover:bg-brand-dark transition-colors"
      >
        Go home
      </Link>
    </motion.div>
  )
}
