// Background service worker for Secure Password Manager extension
// Handles API communication with the local desktop app

// Try HTTPS first, fallback to HTTP
const API_BASE_URLS = [
  'https://127.0.0.1:43110',
  'http://127.0.0.1:43110'
];
let API_BASE_URL = API_BASE_URLS[0]; // Start with HTTPS

const STORAGE_KEYS = {
  TOKEN: 'auth_token',
  TOKEN_EXPIRES: 'token_expires_at',
  FINGERPRINT: 'browser_fingerprint',
  SETTINGS: 'extension_settings',
  API_URL: 'api_base_url'
};

// Generate a unique browser fingerprint
// Note: Service workers don't have access to screen/window objects
function generateFingerprint() {
  const parts = [
    navigator.userAgent,
    navigator.language,
    new Date().getTimezoneOffset().toString(),
    navigator.hardwareConcurrency || 'unknown',
    // Generate a random component since we can't access screen in service worker
    Math.random().toString(36).substring(2, 15)
  ];
  return btoa(parts.join('|')).substring(0, 32);
}

// Get or create browser fingerprint
async function getFingerprint() {
  const result = await chrome.storage.local.get(STORAGE_KEYS.FINGERPRINT);
  if (result[STORAGE_KEYS.FINGERPRINT]) {
    return result[STORAGE_KEYS.FINGERPRINT];
  }

  const fingerprint = generateFingerprint();
  await chrome.storage.local.set({ [STORAGE_KEYS.FINGERPRINT]: fingerprint });
  return fingerprint;
}

// Get the working API base URL (try HTTPS first, fallback to HTTP)
async function getApiBaseUrl() {
  // Check if we have a saved working URL
  const result = await chrome.storage.local.get(STORAGE_KEYS.API_URL);
  if (result[STORAGE_KEYS.API_URL]) {
    API_BASE_URL = result[STORAGE_KEYS.API_URL];
    return API_BASE_URL;
  }

  // Try each URL until one works
  for (const url of API_BASE_URLS) {
    try {
      const response = await fetch(`${url}/v1/status`, {
        method: 'GET',
        // Ignore certificate errors for self-signed certs in development
        // In production, we'd implement proper certificate pinning
      });
      if (response.ok) {
        API_BASE_URL = url;
        // Save the working URL
        await chrome.storage.local.set({ [STORAGE_KEYS.API_URL]: url });
        return url;
      }
    } catch (error) {
      console.log(`Failed to connect to ${url}:`, error.message);
    }
  }

  // Default to HTTPS if nothing works
  return API_BASE_URLS[0];
}

// Get stored auth token
async function getToken() {
  const result = await chrome.storage.local.get([STORAGE_KEYS.TOKEN, STORAGE_KEYS.TOKEN_EXPIRES]);

  if (!result[STORAGE_KEYS.TOKEN]) {
    return null;
  }

  // Check if token is expired
  if (result[STORAGE_KEYS.TOKEN_EXPIRES] && Date.now() > result[STORAGE_KEYS.TOKEN_EXPIRES]) {
    await clearToken();
    return null;
  }

  return result[STORAGE_KEYS.TOKEN];
}

// Store auth token
async function storeToken(token, expiresAt) {
  await chrome.storage.local.set({
    [STORAGE_KEYS.TOKEN]: token,
    [STORAGE_KEYS.TOKEN_EXPIRES]: expiresAt
  });
}

// Clear auth token
async function clearToken() {
  await chrome.storage.local.remove([STORAGE_KEYS.TOKEN, STORAGE_KEYS.TOKEN_EXPIRES]);
}

// Check API status
async function checkStatus() {
  try {
    // Ensure we have the working API URL
    await getApiBaseUrl();

    const response = await fetch(`${API_BASE_URL}/v1/status`);
    if (!response.ok) {
      throw new Error(`Status check failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to connect to desktop app:', error);
    throw new Error('Desktop app not running or unreachable');
  }
}

// Pair with desktop app using pairing code
async function pairWithDesktop(pairingCode) {
  const fingerprint = await getFingerprint();

  try {
    const response = await fetch(`${API_BASE_URL}/v1/pair`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        code: pairingCode,
        fingerprint: fingerprint,
        browser: 'Chrome'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Pairing failed');
    }

    const data = await response.json();
    await storeToken(data.token, data.expires_at * 1000);

    return { success: true, expiresAt: data.expires_at };
  } catch (error) {
    console.error('Pairing error:', error);
    throw error;
  }
}

// Query credentials for a specific origin
async function queryCredentials(origin) {
  const token = await getToken();

  if (!token) {
    throw new Error('Not paired with desktop app');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/credentials/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        origin: origin,
        allow_autofill: true
      })
    });

    if (response.status === 401) {
      await clearToken();
      throw new Error('Token expired, please pair again');
    }

    if (!response.ok) {
      throw new Error(`Query failed: ${response.status}`);
    }

    const data = await response.json();

    // Check if access was denied
    if (data.error) {
      throw new Error(data.error);
    }

    return data.entries || [];
  } catch (error) {
    console.error('Credentials query error:', error);
    throw error;
  }
}

// Check if credentials exist (without approval prompt)
async function checkCredentials(origin, username) {
  const token = await getToken();

  if (!token) {
    throw new Error('Not paired with desktop app');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/credentials/check`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        origin: origin,
        username: username
      })
    });

    if (response.status === 401) {
      await clearToken();
      throw new Error('Token expired, please pair again');
    }

    if (!response.ok) {
      throw new Error(`Check failed: ${response.status}`);
    }

    const data = await response.json();
    return data.exists || false;
  } catch (error) {
    console.error('Credentials check error:', error);
    throw error;
  }
}

// Store new credentials
async function storeCredentials(origin, website, username, password, metadata = {}) {
  const token = await getToken();

  if (!token) {
    throw new Error('Not paired with desktop app');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/credentials/store`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        origin: origin,
        title: website,
        username: username,
        password: password,
        metadata: metadata
      })
    });

    if (response.status === 401) {
      await clearToken();
      throw new Error('Token expired, please pair again');
    }

    if (!response.ok) {
      throw new Error(`Store failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Credentials store error:', error);
    throw error;
  }
}

// Request clipboard clear
async function clearClipboard() {
  const token = await getToken();

  if (!token) {
    return; // Silent fail if not paired
  }

  try {
    await fetch(`${API_BASE_URL}/v1/clipboard/clear`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  } catch (error) {
    console.error('Clipboard clear error:', error);
  }
}

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handlers = {
    'check_status': async () => {
      try {
        const status = await checkStatus();
        const token = await getToken();
        return { ...status, paired: !!token };
      } catch (error) {
        return { error: error.message };
      }
    },

    'pair': async () => {
      try {
        const result = await pairWithDesktop(message.code);
        return result;
      } catch (error) {
        return { error: error.message };
      }
    },

    'unpair': async () => {
      await clearToken();
      return { success: true };
    },

    'query_credentials': async () => {
      try {
        const entries = await queryCredentials(message.origin);
        return { entries };
      } catch (error) {
        return { error: error.message };
      }
    },

    'check_credentials': async () => {
      try {
        const exists = await checkCredentials(message.origin, message.username);
        return { exists };
      } catch (error) {
        return { error: error.message };
      }
    },

    'store_credentials': async () => {
      try {
        await storeCredentials(
          message.origin,
          message.website,
          message.username,
          message.password,
          message.metadata
        );
        return { success: true };
      } catch (error) {
        return { error: error.message };
      }
    },

    'clear_clipboard': async () => {
      await clearClipboard();
      return { success: true };
    }
  };

  const handler = handlers[message.action];
  if (handler) {
    handler().then(sendResponse);
    return true; // Will respond asynchronously
  }

  sendResponse({ error: 'Unknown action' });
  return false;
});

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Secure Password Manager extension installed');
    // Open options page for first-time setup
    chrome.runtime.openOptionsPage();
  }
});

console.log('Secure Password Manager background service worker loaded');
