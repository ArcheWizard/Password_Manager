// Background script for Firefox (manifest v2 compatible)
// This is a compatibility layer that wraps the Chrome-style background.js

// Firefox uses browser.* APIs instead of chrome.*
const chrome = typeof browser !== 'undefined' ? browser : chrome;

// Load the main background script logic
// Note: In production, this would import or inline the background.js content
// with browser.* API calls instead of chrome.* API calls

// For now, we'll duplicate the necessary functions with Firefox compatibility

const API_BASE_URL = 'http://127.0.0.1:43110';
const STORAGE_KEYS = {
  TOKEN: 'auth_token',
  TOKEN_EXPIRES: 'token_expires_at',
  FINGERPRINT: 'browser_fingerprint',
  SETTINGS: 'extension_settings'
};

function generateFingerprint() {
  const parts = [
    navigator.userAgent,
    navigator.language,
    new Date().getTimezoneOffset(),
    screen.width + 'x' + screen.height,
    navigator.hardwareConcurrency || 'unknown'
  ];
  return btoa(parts.join('|')).substring(0, 32);
}

async function getFingerprint() {
  const result = await browser.storage.local.get(STORAGE_KEYS.FINGERPRINT);
  if (result[STORAGE_KEYS.FINGERPRINT]) {
    return result[STORAGE_KEYS.FINGERPRINT];
  }

  const fingerprint = generateFingerprint();
  await browser.storage.local.set({ [STORAGE_KEYS.FINGERPRINT]: fingerprint });
  return fingerprint;
}

async function getToken() {
  const result = await browser.storage.local.get([STORAGE_KEYS.TOKEN, STORAGE_KEYS.TOKEN_EXPIRES]);

  if (!result[STORAGE_KEYS.TOKEN]) {
    return null;
  }

  if (result[STORAGE_KEYS.TOKEN_EXPIRES] && Date.now() > result[STORAGE_KEYS.TOKEN_EXPIRES]) {
    await clearToken();
    return null;
  }

  return result[STORAGE_KEYS.TOKEN];
}

async function storeToken(token, expiresAt) {
  await browser.storage.local.set({
    [STORAGE_KEYS.TOKEN]: token,
    [STORAGE_KEYS.TOKEN_EXPIRES]: expiresAt
  });
}

async function clearToken() {
  await browser.storage.local.remove([STORAGE_KEYS.TOKEN, STORAGE_KEYS.TOKEN_EXPIRES]);
}

async function checkStatus() {
  try {
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
        browser: 'Firefox'
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

    if (data.error) {
      throw new Error(data.error);
    }

    return data.entries || [];
  } catch (error) {
    console.error('Credentials query error:', error);
    throw error;
  }
}

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

async function clearClipboard() {
  const token = await getToken();

  if (!token) {
    return;
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

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
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
    return true;
  }

  sendResponse({ error: 'Unknown action' });
  return false;
});

browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Secure Password Manager extension installed (Firefox)');
    browser.runtime.openOptionsPage();
  }
});

console.log('Secure Password Manager background script loaded (Firefox)');
