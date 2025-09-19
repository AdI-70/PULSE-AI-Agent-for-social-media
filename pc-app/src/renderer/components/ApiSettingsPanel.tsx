import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

interface ApiSettings {
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

export function ApiSettingsPanel() {
  const { getApiSettings, updateApiSettings } = useApi();
  const [settings, setSettings] = useState<ApiSettings>({
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
  });
  const [isLoading, setIsLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<{type: 'success' | 'error' | null, message: string}>({type: null, message: ''});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const apiSettings = await getApiSettings();
      setSettings(prev => ({
        ...prev,
        ...apiSettings
      }));
    } catch (error) {
      setSaveStatus({type: 'error', message: 'Failed to load API settings'});
      console.error('Error loading API settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: parseInt(value) || 0
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateApiSettings(settings);
      setSaveStatus({type: 'success', message: 'API settings updated successfully'});
    } catch (error) {
      setSaveStatus({type: 'error', message: 'Failed to update API settings'});
      console.error('Error updating API settings:', error);
    }
  };

  if (isLoading) {
    return <div className="p-6">Loading API settings...</div>;
  }

  return (
    <div className="p-6 max-w-4xl mx-auto overflow-auto">
      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          {/* API Keys Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">API Keys</h2>
              <p className="text-sm text-gray-500 mt-1">
                Configure your API keys for external services
              </p>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="newsApiKey" className="block text-sm font-medium text-gray-700">
                    NewsAPI Key
                  </label>
                  <input
                    id="newsApiKey"
                    name="newsApiKey"
                    type="password"
                    value={settings.newsApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter NewsAPI key"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="googleSearchApiKey" className="block text-sm font-medium text-gray-700">
                    Google Search API Key
                  </label>
                  <input
                    id="googleSearchApiKey"
                    name="googleSearchApiKey"
                    type="password"
                    value={settings.googleSearchApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter Google Search API key"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="googleSearchEngineId" className="block text-sm font-medium text-gray-700">
                    Google Search Engine ID
                  </label>
                  <input
                    id="googleSearchEngineId"
                    name="googleSearchEngineId"
                    type="text"
                    value={settings.googleSearchEngineId}
                    onChange={handleInputChange}
                    placeholder="Enter Google Search Engine ID"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="openaiApiKey" className="block text-sm font-medium text-gray-700">
                    OpenAI API Key
                  </label>
                  <input
                    id="openaiApiKey"
                    name="openaiApiKey"
                    type="password"
                    value={settings.openaiApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter OpenAI API key"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="huggingfaceApiKey" className="block text-sm font-medium text-gray-700">
                    Hugging Face API Key
                  </label>
                  <input
                    id="huggingfaceApiKey"
                    name="huggingfaceApiKey"
                    type="password"
                    value={settings.huggingfaceApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter Hugging Face API key"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h3 className="text-lg font-medium mb-4">X (Twitter) API Credentials</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="xApiKey" className="block text-sm font-medium text-gray-700">
                      API Key
                    </label>
                    <input
                      id="xApiKey"
                      name="xApiKey"
                      type="password"
                      value={settings.xApiKey}
                      onChange={handleInputChange}
                      placeholder="Enter X API key"
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="xApiSecret" className="block text-sm font-medium text-gray-700">
                      API Secret
                    </label>
                    <input
                      id="xApiSecret"
                      name="xApiSecret"
                      type="password"
                      value={settings.xApiSecret}
                      onChange={handleInputChange}
                      placeholder="Enter X API secret"
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="xAccessToken" className="block text-sm font-medium text-gray-700">
                      Access Token
                    </label>
                    <input
                      id="xAccessToken"
                      name="xAccessToken"
                      type="password"
                      value={settings.xAccessToken}
                      onChange={handleInputChange}
                      placeholder="Enter X access token"
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="xAccessTokenSecret" className="block text-sm font-medium text-gray-700">
                      Access Token Secret
                    </label>
                    <input
                      id="xAccessTokenSecret"
                      name="xAccessTokenSecret"
                      type="password"
                      value={settings.xAccessTokenSecret}
                      onChange={handleInputChange}
                      placeholder="Enter X access token secret"
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Rate Limits Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Rate Limits</h2>
              <p className="text-sm text-gray-500 mt-1">
                Configure API request limits per day
              </p>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="newsFetchRateLimit" className="block text-sm font-medium text-gray-700">
                    News Fetch Rate Limit
                  </label>
                  <input
                    id="newsFetchRateLimit"
                    name="newsFetchRateLimit"
                    type="number"
                    value={settings.newsFetchRateLimit}
                    onChange={handleNumberChange}
                    min="1"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="googleSearchRateLimit" className="block text-sm font-medium text-gray-700">
                    Google Search Rate Limit
                  </label>
                  <input
                    id="googleSearchRateLimit"
                    name="googleSearchRateLimit"
                    type="number"
                    value={settings.googleSearchRateLimit}
                    onChange={handleNumberChange}
                    min="1"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="xPostRateLimit" className="block text-sm font-medium text-gray-700">
                    X Post Rate Limit
                  </label>
                  <input
                    id="xPostRateLimit"
                    name="xPostRateLimit"
                    type="number"
                    value={settings.xPostRateLimit}
                    onChange={handleNumberChange}
                    min="1"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="llmRequestRateLimit" className="block text-sm font-medium text-gray-700">
                    LLM Request Rate Limit
                  </label>
                  <input
                    id="llmRequestRateLimit"
                    name="llmRequestRateLimit"
                    type="number"
                    value={settings.llmRequestRateLimit}
                    onChange={handleNumberChange}
                    min="1"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
          
          {/* Mock Modes Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Mock Modes</h2>
              <p className="text-sm text-gray-500 mt-1">
                Enable mock modes for testing without real API keys
              </p>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Mock News Fetching
                  </label>
                  <p className="text-sm text-gray-500">
                    Use mock data instead of real news API calls
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.mockNewsFetching}
                  onChange={(e) => handleInputChange({...e, target: {...e.target, name: 'mockNewsFetching', type: 'checkbox'}})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Mock LLM Summarization
                  </label>
                  <p className="text-sm text-gray-500">
                    Use mock summaries instead of real LLM calls
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.mockLlmSummarization}
                  onChange={(e) => handleInputChange({...e, target: {...e.target, name: 'mockLlmSummarization', type: 'checkbox'}})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Mock X Posting
                  </label>
                  <p className="text-sm text-gray-500">
                    Simulate X posts without actually posting
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.mockXPosting}
                  onChange={(e) => handleInputChange({...e, target: {...e.target, name: 'mockXPosting', type: 'checkbox'}})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          
          {/* Status Message */}
          {saveStatus.type && (
            <div className={`p-4 rounded-md ${saveStatus.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
              {saveStatus.message}
            </div>
          )}
          
          <button
            type="submit"
            className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Save API Settings
          </button>
        </div>
      </form>
    </div>
  );
}