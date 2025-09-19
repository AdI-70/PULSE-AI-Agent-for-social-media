// Test script to verify API settings functionality
async function testApiSettings() {
  const baseUrl = 'http://localhost:8000';
  
  try {
    // Test GET request
    console.log('Testing GET /api-settings/');
    const getResponse = await fetch(`${baseUrl}/api-settings/`);
    const getSettings = await getResponse.json();
    console.log('GET response:', getSettings);
    
    // Test POST request
    console.log('\nTesting POST /api-settings/');
    const testSettings = {
      newsApiKey: "test-key",
      googleSearchApiKey: "test-google-key",
      googleSearchEngineId: "test-engine-id",
      openaiApiKey: "test-openai-key",
      huggingfaceApiKey: "test-hf-key",
      xApiKey: "test-x-key",
      xApiSecret: "test-x-secret",
      xAccessToken: "test-x-token",
      xAccessTokenSecret: "test-x-token-secret",
      newsFetchRateLimit: 50,
      googleSearchRateLimit: 45,
      xPostRateLimit: 25,
      llmRequestRateLimit: 500,
      mockNewsFetching: true,
      mockLlmSummarization: true,
      mockXPosting: true
    };
    
    const postResponse = await fetch(`${baseUrl}/api-settings/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testSettings)
    });
    
    const postSettings = await postResponse.json();
    console.log('POST response:', postSettings);
    
    // Verify settings were saved
    console.log('\nVerifying settings were saved...');
    const verifyResponse = await fetch(`${baseUrl}/api-settings/`);
    const verifySettings = await verifyResponse.json();
    console.log('Verified settings:', verifySettings);
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testApiSettings();