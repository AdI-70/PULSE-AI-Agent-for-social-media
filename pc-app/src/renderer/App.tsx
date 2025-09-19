import React, { useState, useEffect } from 'react'
import { Settings, Activity, PlayCircle, Pause, CheckCircle, AlertCircle } from 'lucide-react'
import { ConfigurationPanel } from './components/ConfigurationPanel'
import { StatusDashboard } from './components/StatusDashboard'
import { PreviewPanel } from './components/PreviewPanel'
import { ApiSettingsPanel } from './components/ApiSettingsPanel'
import { useApi } from './hooks/useApi'
import { PipelineConfig, SystemStatus } from './types/api'

function App() {
  const [activeTab, setActiveTab] = useState<'config' | 'dashboard' | 'preview' | 'api'>('config')
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const { getConfig, getSystemStatus, healthCheck, loading, error } = useApi()

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      const healthy = await healthCheck()
      setIsConnected(healthy || false)
      
      if (healthy) {
        const currentConfig = await getConfig()
        setConfig(currentConfig)
        
        const status = await getSystemStatus()
        setSystemStatus(status)
      }
    }

    loadData()
  }, [getConfig, getSystemStatus, healthCheck])

  // Auto-refresh system status
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(async () => {
      const status = await getSystemStatus()
      setSystemStatus(status)
    }, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [isConnected, getSystemStatus])

  const handleConfigSave = (newConfig: PipelineConfig) => {
    setConfig(newConfig)
  }

  const getStatusIcon = () => {
    if (!isConnected) return <AlertCircle className="h-4 w-4 text-red-500" />
    if (!systemStatus) return <Pause className="h-4 w-4 text-gray-500" />
    
    switch (systemStatus.system_health) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'busy':
        return <Activity className="h-4 w-4 text-yellow-500" />
      case 'degraded':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Pause className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <PlayCircle className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Pulse</h1>
              <p className="text-sm text-gray-500">News-to-X Automated Pipeline</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon()}
              <span className="text-sm text-gray-600">
                {isConnected ? (systemStatus?.system_health || 'Unknown') : 'Disconnected'}
              </span>
            </div>
            
            {systemStatus && (
              <div className="text-sm text-gray-500">
                Active Jobs: {systemStatus.active_jobs} | Total Posts: {systemStatus.total_posts}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 px-6">
        <div className="flex space-x-8">
          {[
            { id: 'config', label: 'Configuration', icon: Settings },
            { id: 'dashboard', label: 'Dashboard', icon: Activity },
            { id: 'preview', label: 'Preview', icon: PlayCircle },
            { id: 'api', label: 'API Settings', icon: Settings },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1 overflow-auto">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 mx-6 mt-4 rounded">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && (
          <div className="h-full overflow-auto">
            {activeTab === 'config' && (
              <ConfigurationPanel
                config={config}
                onConfigSave={handleConfigSave}
                isConnected={isConnected}
              />
            )}
            
            {activeTab === 'dashboard' && (
              <StatusDashboard
                systemStatus={systemStatus}
                isConnected={isConnected}
              />
            )}
            
            {activeTab === 'preview' && (
              <PreviewPanel
                config={config}
                isConnected={isConnected}
              />
            )}
            
            {activeTab === 'api' && (
              <ApiSettingsPanel />
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App