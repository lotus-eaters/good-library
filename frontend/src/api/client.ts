import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8009/api/v1',
  withCredentials: true,
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
}> = []

function processQueue(error: unknown) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(undefined)
  })
  failedQueue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    const skipRefreshPaths = ['/auth/me', '/auth/refresh', '/auth/login', '/auth/signup']
    const isAuthEndpoint = skipRefreshPaths.some((p) => originalRequest.url?.includes(p))

    if (error.response?.status !== 401 || originalRequest._retry || isAuthEndpoint) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => client(originalRequest))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      await client.post('/auth/refresh')
      processQueue(null)
      return client(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError)
      // Refresh failed — clear auth state via custom event so the store can react
      window.dispatchEvent(new Event('auth:logout'))
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
