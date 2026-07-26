import { create } from 'zustand'
import type { Shelf, ShelfType } from '../api/shelves'
import type { Book } from '../api/books'
import { shelvesApi } from '../api/shelves'
import { toast } from './toastStore'

interface ShelfState {
  shelves: Shelf[]
  isLoading: boolean
  fetchShelves: () => Promise<void>
  addBook: (shelfId: number, book: Book) => Promise<void>
  removeBook: (shelfId: number, bookId: number) => Promise<void>
  getShelfForBook: (bookId: number) => ShelfType | null
}

export const useShelfStore = create<ShelfState>((set, get) => ({
  shelves: [],
  isLoading: false,

  fetchShelves: async () => {
    set({ isLoading: true })
    try {
      const shelves = await shelvesApi.getAll()
      set({ shelves })
    } finally {
      set({ isLoading: false })
    }
  },

  addBook: async (shelfId, book) => {
    const previous = get().shelves

    // Optimistic update
    set({
      shelves: previous.map((shelf) =>
        shelf.id === shelfId
          ? { ...shelf, books: [...shelf.books.filter((b) => b.id !== book.id), book] }
          : { ...shelf, books: shelf.books.filter((b) => b.id !== book.id) }
      ),
    })

    try {
      await shelvesApi.addBook(shelfId, book.id)
      const shelf = get().shelves.find((s) => s.id === shelfId)
      toast.success(`Added to ${shelf?.name ?? 'shelf'}`)
    } catch {
      set({ shelves: previous })
      toast.error('Failed to add book to shelf')
      throw new Error('Failed to add book to shelf')
    }
  },

  removeBook: async (shelfId, bookId) => {
    const previous = get().shelves

    set({
      shelves: previous.map((shelf) =>
        shelf.id === shelfId
          ? { ...shelf, books: shelf.books.filter((b) => b.id !== bookId) }
          : shelf
      ),
    })

    try {
      await shelvesApi.removeBook(shelfId, bookId)
      toast.info('Removed from shelf')
    } catch {
      set({ shelves: previous })
      toast.error('Failed to remove book from shelf')
      throw new Error('Failed to remove book from shelf')
    }
  },

  getShelfForBook: (bookId) => {
    const shelf = get().shelves.find((s) => s.books?.some((b) => b.id === bookId))
    return shelf?.shelf_type ?? null
  },
}))
