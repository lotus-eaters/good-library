import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'
import { useToastStore, type Toast as ToastType } from '../store/toastStore'

const ICONS = {
  success: <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />,
  error: <XCircle className="w-4 h-4 text-red-400 shrink-0" />,
  info: <Info className="w-4 h-4 text-brand shrink-0" />,
}

const BORDER = {
  success: 'border-emerald-500/30',
  error: 'border-red-500/30',
  info: 'border-brand/30',
}

function ToastItem({ toast }: { toast: ToastType }) {
  const remove = useToastStore((s) => s.remove)

  useEffect(() => {
    const timer = setTimeout(() => remove(toast.id), 3000)
    return () => clearTimeout(timer)
  }, [toast.id, remove])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 60 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 60 }}
      transition={{ duration: 0.2 }}
      className={`flex items-center gap-3 bg-surface-card border ${BORDER[toast.type]} rounded-xl px-4 py-3 shadow-lg min-w-64 max-w-sm`}
    >
      {ICONS[toast.type]}
      <p className="text-sm text-text-primary flex-1">{toast.message}</p>
      <button onClick={() => remove(toast.id)} className="text-text-secondary hover:text-text-primary transition-colors">
        <X className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  )
}

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts)

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 items-end">
      <AnimatePresence>
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} />
        ))}
      </AnimatePresence>
    </div>
  )
}
