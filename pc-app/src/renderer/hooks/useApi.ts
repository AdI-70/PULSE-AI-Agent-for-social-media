import { useState, useCallback } from 'react'
import { ApiService, ApiSettings } from '../services/api'
import { PipelineConfig, SystemStatus, RunRequest } from '../types/api'

export const useApi = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRequest = useCallback(async <T>(request: () => Promise<T>): Promise<T | null> => {
    setLoading(true)
    setError(null)
    try {
      const result = await request()
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const getConfig = useCallback(() => {
    return handleRequest(() => ApiService.getConfig())
  }, [handleRequest])

  const saveConfig = useCallback((config: Omit<PipelineConfig, 'id' | 'created_at' | 'updated_at'>) => {
    return handleRequest(() => ApiService.saveConfig(config))
  }, [handleRequest])

  const getApiSettings = useCallback(() => {
    return handleRequest(() => ApiService.getApiSettings())
  }, [handleRequest])

  const updateApiSettings = useCallback((settings: ApiSettings) => {
    return handleRequest(() => ApiService.updateApiSettings(settings))
  }, [handleRequest])

  const runPipeline = useCallback((request: RunRequest) => {
    return handleRequest(() => ApiService.runPipeline(request))
  }, [handleRequest])

  const getSystemStatus = useCallback(() => {
    return handleRequest(() => ApiService.getSystemStatus())
  }, [handleRequest])

  const healthCheck = useCallback(() => {
    return handleRequest(() => ApiService.healthCheck())
  }, [handleRequest])

  return {
    loading,
    error,
    setError,
    getConfig,
    saveConfig,
    getApiSettings,
    updateApiSettings,
    runPipeline,
    getSystemStatus,
    healthCheck,
  }
}