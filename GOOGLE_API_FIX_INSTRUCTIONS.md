# Fixing Google Custom Search API Access Issues

## Problem
You're encountering a `403 Forbidden` error with the message `API_KEY_SERVICE_BLOCKED` when trying to access the Google Custom Search API. This means your API key doesn't have permission to use the Custom Search API service.

## Solution Steps

### 1. Enable Custom Search API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one if you haven't already)
3. Navigate to "APIs & Services" > "Library"
4. Search for "Custom Search API"
5. Click on "Custom Search API" in the results
6. Click the "Enable" button

### 2. Configure API Key Permissions

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Find your API key (AIzaSyAh19yAFUL1h-k_fEeUHrnrIMYEpU5MteA)
3. Click on the pencil/edit icon next to your API key
4. Under "API restrictions" section:
   - Select "Restrict key"
   - Check the box for "Custom Search API"
   - If you can't find "Custom Search API" in the list, you may need to:
     - First enable it (step 1 above)
     - Wait a few minutes for the API to appear in the list
     - Or temporarily select "Don't restrict key" for testing
5. Click "Save"

### 3. Verify Custom Search Engine Configuration

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Make sure your search engine (854d4d61625a042bb) is set to search the entire web:
   - Click on your search engine
   - Go to "Setup" > "Basics"
   - Ensure "Search the entire web" is enabled
   - In "Sites to search", you should either have "All sites" or specific sites you want to search

### 4. Wait for Changes to Propagate

After making these changes, wait 5-10 minutes for the changes to propagate through Google's systems.

## Testing the Fix

After completing the above steps, you can test if the integration works by running:

```bash
python test_google_search.py
```

## Alternative Solution

If you continue to have issues, you can create a new API key with broader permissions:

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API key"
3. Copy the new API key
4. Update your `.env` file with the new key:
   ```
   GOOGLE_API_KEY=your_new_api_key_here
   ```

## Verification Script

You can run the diagnosis script to check if the issue is resolved:

```bash
python diagnose_google_api.py
```

## Common Issues and Solutions

1. **API Key Restrictions**: If you restrict your API key to specific APIs, make sure Custom Search API is included.

2. **Billing Account**: Some Google APIs require a billing account to be associated with your project. Check if this is required for Custom Search API.

3. **Quota Limits**: Make sure you haven't exceeded your daily quota for the Custom Search API.

4. **CSE Configuration**: Ensure your Custom Search Engine is properly configured to search the web.

If you continue to have issues after following these steps, please check the [Google Custom Search API documentation](https://developers.google.com/custom-search/v1/overview) for more detailed information.