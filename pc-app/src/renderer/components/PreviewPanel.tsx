import React, { useState } from 'react'
import { Play, Eye, RefreshCw, AlertTriangle } from 'lucide-react'
import { PipelineConfig } from '../types/api'
import { useApi } from '../hooks/useApi'

interface PreviewPanelProps {
  config: PipelineConfig | null
  isConnected: boolean
}

export const PreviewPanel: React.FC<PreviewPanelProps> = ({
  config,
  isConnected
}) => {
  const { runPipeline, loading, error, setError } = useApi()
  const [previewResult, setPreviewResult] = useState<any>(null)
  const [isRunning, setIsRunning] = useState(false)

  const handlePreview = async (niche: string) => {
    if (!isConnected) {
      setError('Not connected to backend')
      return
    }

    setIsRunning(true)
    setPreviewResult(null)
    
    try {
      const result = await runPipeline({
        niche,
        preview_mode: true
      })
      
      if (result) {
        setPreviewResult(result)
        setError(null)
      }
    } catch (err) {
      console.error('Preview failed:', err)
    }
    
    setIsRunning(false)
  }

  const handleRun = async (niche: string) => {
    if (!isConnected) {
      setError('Not connected to backend')
      return
    }

    if (!config?.auto_post) {
      setError('Auto-posting is disabled. Enable it in configuration to run the pipeline.')
      return
    }

    setIsRunning(true)
    setPreviewResult(null)
    
    try {
      const result = await runPipeline({
        niche,
        preview_mode: false
      })
      
      if (result) {
        setPreviewResult(result)
        setError(null)
      }
    } catch (err) {
      console.error('Pipeline run failed:', err)
    }
    
    setIsRunning(false)
  }

  if (!config || !config.niches || config.niches.length === 0) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Configuration Found
          </h3>
          <p className="text-gray-500">
            Please configure your pipeline settings first before running previews.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 overflow-auto">
      {/* Current Configuration Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Current Configuration</h2>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Niches</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {config.niches.map(niche => (
                  <span
                    key={niche}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2 mb-2"
                  >
                    {niche}
                  </span>
                ))}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Frequency</dt>
              <dd className="mt-1 text-sm text-gray-900 capitalize">{config.frequency}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Tone</dt>
              <dd className="mt-1 text-sm text-gray-900 capitalize">{config.tone}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Auto Post</dt>
              <dd className="mt-1 text-sm text-gray-900">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  config.auto_post 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {config.auto_post ? 'Enabled' : 'Disabled'}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Pipeline Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Pipeline Controls</h3>
          <p className="text-sm text-gray-500 mt-1">
            Test the pipeline with your configured niches
          </p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {config.niches.map(niche => (
              <div key={niche} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 capitalize mb-3">{niche}</h4>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handlePreview(niche)}
                    disabled={!isConnected || isRunning || loading}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Preview
                  </button>
                  
                  <button
                    onClick={() => handleRun(niche)}
                    disabled={!isConnected || isRunning || loading || !config.auto_post}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Run Pipeline
                  </button>
                </div>
              </div>
            ))}
          </div>

          {!config.auto_post && (
            <div className="mt-4 p-3 rounded-md bg-yellow-50 border border-yellow-200">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    Auto-posting is disabled. Only preview mode is available. 
                    Enable auto-posting in configuration to run the full pipeline.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Loading State */}
      {(isRunning || loading) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <RefreshCw className="h-5 w-5 text-blue-500 animate-spin mr-3" />
            <div>
              <p className="text-sm font-medium text-blue-700">Running Pipeline...</p>
              <p className="text-sm text-blue-600">
                Fetching articles, generating summaries, and processing content.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Preview Results */}
      {previewResult && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Pipeline Result</h3>
          </div>
          <div className="p-6">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Job ID</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{previewResult.job_id}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1 text-sm text-gray-900 capitalize">{previewResult.status}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Niche</dt>
                <dd className="mt-1 text-sm text-gray-900 capitalize">{previewResult.niche}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Message</dt>
                <dd className="mt-1 text-sm text-gray-900">{previewResult.message}</dd>
              </div>
            </dl>
            
            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700">
                <strong>Next Steps:</strong> Check the Dashboard tab to monitor job progress 
                and view generated content.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}