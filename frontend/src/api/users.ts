import client from './client'

export interface Challenge {
  year: number
  goal: number
  books_read_this_year: number
}

export interface GraphNode {
  id: string
  type: 'book' | 'author' | 'genre'
  label: string
  cover_url?: string | null
  book_id?: number
}

export interface GraphEdge {
  source: string
  target: string
  type: 'wrote' | 'belongs-to'
}

export interface KnowledgeGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export const usersApi = {
  getChallenge: () =>
    client.get<Challenge>('/users/me/challenge').then((r) => r.data),

  updateChallenge: (goal: number) =>
    client.put<Challenge>('/users/me/challenge', { goal }).then((r) => r.data),

  getInsights: (refresh = false) =>
    client.get<{ insight: string }>('/users/me/insights', { params: refresh ? { refresh: true } : {} })
      .then((r) => r.data.insight),

  getKnowledgeGraph: () =>
    client.get<KnowledgeGraph>('/users/me/knowledge-graph').then((r) => r.data),
}
