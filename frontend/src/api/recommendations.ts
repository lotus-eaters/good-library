import client from './client'

export const recommendationsApi = {
  getWhy: (bookId: number) =>
    client.get<{ explanation: string }>(`/recommendations/why/${bookId}`)
      .then((r) => r.data.explanation),
}
