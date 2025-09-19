export const isDev = process.env.NODE_ENV === 'development'

export const API_BASE_URL = isDev 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000' // In production, this could be different