import client from './client'

export interface Book {
  id: number
  google_books_id: string
  title: string
  authors: string
  description: string | null
  cover_url: string | null
  published_date: string | null
  page_count: number | null
  average_rating: number | null
  ratings_count: number | null
  genres: string[]
}

export const booksApi = {
  search: (q: string, limit = 20) =>
    client.get<Book[]>('/books/search', { params: { q, limit } }).then((r) => r.data),

  semanticSearch: (q: string, limit = 10) =>
    client.get<Book[]>('/books/search/semantic', { params: { q, limit } }).then((r) => r.data),

  getNewReleases: (genre?: string, limit = 20) =>
    client.get<Book[]>('/books/new-releases', { params: { genre, limit } }).then((r) => r.data),

  getById: (id: number) =>
    client.get<Book>(`/books/${id}`).then((r) => r.data),

  getSimilar: (bookId: number, limit = 8) =>
    client.get<Book[]>(`/recommendations/similar/${bookId}`, { params: { limit } }).then((r) => r.data),

  getPopular: (limit = 20) =>
    client.get<Book[]>('/books/popular', { params: { limit } }).then((r) => r.data),

  getForYou: (limit = 20) =>
    client.get<Book[]>('/recommendations/for-you', { params: { limit } }).then((r) => r.data),

  getSummary: (id: number) =>
    client.get<{ summary: string }>(`/books/${id}/summary`).then((r) => r.data.summary),
}
