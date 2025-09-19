import React, { useState } from 'react'
import { Save, Globe } from 'lucide-react'
import { PipelineConfig } from '../types/api'
import { useApi } from '../hooks/useApi'

interface ConfigurationPanelProps {
  config: PipelineConfig | null
  onConfigSave: (config: PipelineConfig) => void
  isConnected: boolean
}

const AVAILABLE_NICHES = [
  'technology',
  'artificial intelligence',
  'cybersecurity',
  'fintech',
  'business',
  'science',
  'health',
  'climate',
  'startup',
  'blockchain'
]

const FREQUENCIES = [
  { value: 'hourly', label: 'Every Hour' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' }
]

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'creative', label: 'Creative' }
]

export const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  config,
  onConfigSave,
  isConnected
}) => {
  const { saveConfig, loading, error, setError } = useApi()
  const [formData, setFormData] = useState<Omit<PipelineConfig, 'id' | 'created_at' | 'updated_at'>>({
    niches: config?.niches || [],
    frequency: config?.frequency || 'hourly',
    tone: config?.tone || 'professional',
    auto_post: config?.auto_post || false
  })
  const [isSaving, setIsSaving] = useState(false)

  const handleNicheToggle = (niche: string) => {
    setFormData(prev => ({
      ...prev,
      niches: prev.niches.includes(niche)
        ? prev.niches.filter(n => n !== niche)
        : [...prev.niches, niche]
    }))
  }

  const handleSave = async () => {
    if (!isConnected) {
      setError('Not connected to backend')
      return
    }

    if (formData.niches.length === 0) {
      setError('Please select at least one niche')
      return
    }

    setIsSaving(true)
    try {
      const savedConfig = await saveConfig(formData)
      if (savedConfig) {
        onConfigSave(savedConfig)
        setError(null)
      }
    } catch (err) {
      console.error('Failed to save config:', err)
    }
    setIsSaving(false)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto overflow-auto">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Pipeline Configuration</h2>
          <p className="text-sm text-gray-500 mt-1">
            Configure your news-to-X pipeline settings
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Connection Status */}
          <div className="flex items-center space-x-2 p-3 rounded-md bg-gray-50">
            <Globe className={`h-4 w-4 ${isConnected ? 'text-green-500' : 'text-red-500'}`} />
            <span className="text-sm">
              Backend: {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Niches Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Content Niches
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {AVAILABLE_NICHES.map(niche => (
                <label key={niche} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.niches.includes(niche)}
                    onChange={() => handleNicheToggle(niche)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 capitalize">
                    {niche}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Frequency */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Posting Frequency
            </label>
            <select
              value={formData.frequency}
              onChange={(e) => setFormData(prev => ({ ...prev, frequency: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {FREQUENCIES.map(freq => (
                <option key={freq.value} value={freq.value}>
                  {freq.label}
                </option>
              ))}
            </select>
          </div>

          {/* Tone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content Tone
            </label>
            <select
              value={formData.tone}
              onChange={(e) => setFormData(prev => ({ ...prev, tone: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {TONES.map(tone => (
                <option key={tone.value} value={tone.value}>
                  {tone.label}
                </option>
              ))}
            </select>
          </div>

          {/* Auto Post */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="auto-post"
              checked={formData.auto_post}
              onChange={(e) => setFormData(prev => ({ ...prev, auto_post: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="auto-post" className="ml-2 block text-sm text-gray-900">
              Enable automatic posting
            </label>
            <span className="ml-2 text-xs text-gray-500">
              (When disabled, posts will be previewed only)
            </span>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
              {error}
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={!isConnected || isSaving || loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}