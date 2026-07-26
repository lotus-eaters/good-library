import client from './client'

export interface Rating {
  id: number
  book_id: number
  score: number
  review: string | null
}

export interface BookReview {
  id: number
  score: number
  review: string
  created_at: string
  reviewer_name: string
}

export const ratingsApi = {
  rate: (bookId: number, score: number, review?: string) =>
    client.post<Rating>('/ratings/', { book_id: bookId, score, review }).then((r) => r.data),

  getMyRating: (bookId: number) =>
    client.get<Rating | null>(`/ratings/${bookId}`).then((r) => r.data),

  getBookReviews: (bookId: number) =>
    client.get<BookReview[]>(`/ratings/book/${bookId}/reviews`).then((r) => r.data),

  delete: (bookId: number) => client.delete(`/ratings/${bookId}`),
}
