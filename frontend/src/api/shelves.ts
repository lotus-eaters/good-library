import client from './client'
import type { Book } from './books'

export type ShelfType = 'want_to_read' | 'currently_reading' | 'already_read'

export interface Shelf {
  id: number
  name: string
  shelf_type: ShelfType
  books: Book[]
}

export const shelvesApi = {
  getAll: () =>
    client.get<Shelf[]>('/shelves/').then((r) => r.data),

  addBook: (shelfId: number, bookId: number) =>
    client.post(`/shelves/${shelfId}/books`, { book_id: bookId }),

  removeBook: (shelfId: number, bookId: number) =>
    client.delete(`/shelves/${shelfId}/books/${bookId}`),
}
