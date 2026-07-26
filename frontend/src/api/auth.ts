import client from './client'

export interface User {
  id: number
  email: string
  username: string
  display_name: string | null
  avatar_url: string | null
  bio: string | null
  is_verified: boolean
}

export interface SignupRequest {
  email: string
  username: string
  password: string
  display_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export const authApi = {
  signup: (data: SignupRequest) =>
    client.post<User>('/auth/signup', data).then((r) => r.data),

  login: (data: LoginRequest) =>
    client.post<User>('/auth/login', data).then((r) => r.data),

  logout: () => client.post('/auth/logout'),

  getMe: () => client.get<User>('/auth/me').then((r) => r.data),

  refresh: () => client.post('/auth/refresh'),
}
