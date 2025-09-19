import axios from 'axios'
import { PipelineConfig, SystemStatus, RunRequest, RunResponse } from '../types/api'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Define the API settings interface
export interface ApiSettings {
  newsApiKey: string;
  googleSearchApiKey: string;
  googleSearchEngineId: string;
  openaiApiKey: string;
  huggingfaceApiKey: string;
  xApiKey: string;
  xApiSecret: string;
  xAccessToken: string;
  xAccessTokenSecret: string;
  // Rate limits
  newsFetchRateLimit: number;
  googleSearchRateLimit: number;
  xPostRateLimit: number;
  llmRequestRateLimit: number;
  // Mock modes
  mockNewsFetching: boolean;
  mockLlmSummarization: boolean;
  mockXPosting: boolean;
}

export class ApiService {
  // Configuration endpoints
  static async getConfig(): Promise<PipelineConfig | null> {
    try {
      const response = await api.get('/config/')
      return response.data
    } catch (error) {
      console.error('Failed to get config:', error)
      return null
    }
  }

  static async saveConfig(config: Omit<PipelineConfig, 'id' | 'created_at' | 'updated_at'>): Promise<PipelineConfig> {
    const response = await api.post('/config/', config)
    return response.data
  }

  // API Settings endpoints
  static async getApiSettings(): Promise<ApiSettings> {
    try {
      const response = await api.get('/api-settings/')
      return response.data
    } catch (error) {
      console.error('Failed to get API settings:', error)
      // Return default settings if API call fails
      return {
        newsApiKey: '',
        googleSearchApiKey: '',
        googleSearchEngineId: '',
        openaiApiKey: '',
        huggingfaceApiKey: '',
        xApiKey: '',
        xApiSecret: '',
        xAccessToken: '',
        xAccessTokenSecret: '',
        newsFetchRateLimit: 100,
        googleSearchRateLimit: 90,
        xPostRateLimit: 50,
        llmRequestRateLimit: 1000,
        mockNewsFetching: false,
        mockLlmSummarization: false,
        mockXPosting: false
      }
    }
  }

  static async updateApiSettings(settings: ApiSettings): Promise<ApiSettings> {
    try {
      const response = await api.post('/api-settings/', settings)
      return response.data
    } catch (error) {
      console.error('Failed to update API settings:', error)
      throw error
    }
  }

  // Pipeline endpoints
  static async runPipeline(request: RunRequest): Promise<RunResponse> {
    const response = await api.post('/run', request)
    return response.data
  }

  // Status endpoints
  static async getSystemStatus(): Promise<SystemStatus> {
    const response = await api.get('/status/')
    return response.data
  }

  static async getJobStatus(jobId: string) {
    const response = await api.get(`/status/job/${jobId}`)
    return response.data
  }

  // Health check
  static async healthCheck(): Promise<boolean> {
    try {
      await api.get('/health')
      return true
    } catch {
      return false
    }
  }
}

export default ApiService