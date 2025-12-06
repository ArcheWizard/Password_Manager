// Popup script for Secure Password Manager extension

// DOM elements
const statusEl = document.getElementById('status');
const statusTextEl = document.getElementById('status-text');
const pairingSectionEl = document.getElementById('pairing-section');
const connectedSectionEl = document.getElementById('connected-section');
const pairingCodeInput = document.getElementById('pairing-code');
const pairBtn = document.getElementById('pair-btn');
const pairBtnText = document.getElementById('pair-btn-text');
const unpairBtn = document.getElementById('unpair-btn');
const testAutofillBtn = document.getElementById('test-autofill-btn');
const fingerprintValue = document.getElementById('fingerprint-value');
const expiresValue = document.getElementById('expires-value');

// State
let isPaired = false;
let isConnected = false;

// Initialize popup
async function init() {
  await checkStatus();
  setupEventListeners();
}

// Check connection and pairing status
async function checkStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'check_status' });

    if (response.error) {
      setDisconnectedStatus(response.error);
      return;
    }

    isConnected = response.status === 'ok';
    isPaired = response.paired;

    if (!isConnected) {
      setDisconnectedStatus('Desktop app not running');
    } else if (!isPaired) {
      setNotPairedStatus();
    } else {
      await setConnectedStatus();
    }
  } catch (error) {
    console.error('Status check error:', error);
    setDisconnectedStatus('Failed to connect to extension');
  }
}

// Set disconnected status UI
function setDisconnectedStatus(message) {
  statusEl.className = 'status disconnected';
  statusTextEl.textContent = message || 'Desktop app not running';
  pairingSectionEl.classList.add('hidden');
  connectedSectionEl.classList.add('hidden');
}

// Set not paired status UI
function setNotPairedStatus() {
  statusEl.className = 'status warning';
  statusTextEl.textContent = 'Not paired with desktop app';
  pairingSectionEl.classList.remove('hidden');
  connectedSectionEl.classList.add('hidden');
}

// Set connected status UI
async function setConnectedStatus() {
  statusEl.className = 'status connected';
  statusTextEl.textContent = 'Connected to desktop app';
  pairingSectionEl.classList.add('hidden');
  connectedSectionEl.classList.remove('hidden');

  // Load and display token info
  const storage = await chrome.storage.local.get(['browser_fingerprint', 'token_expires_at']);

  if (storage.browser_fingerprint) {
    fingerprintValue.textContent = storage.browser_fingerprint.substring(0, 12) + '...';
  }

  if (storage.token_expires_at) {
    const expiresDate = new Date(storage.token_expires_at);
    const now = new Date();
    const hoursLeft = Math.floor((expiresDate - now) / (1000 * 60 * 60));

    if (hoursLeft > 24) {
      const daysLeft = Math.floor(hoursLeft / 24);
      expiresValue.textContent = `in ${daysLeft} day${daysLeft > 1 ? 's' : ''}`;
    } else if (hoursLeft > 0) {
      expiresValue.textContent = `in ${hoursLeft} hour${hoursLeft > 1 ? 's' : ''}`;
    } else {
      expiresValue.textContent = 'Soon (re-pair recommended)';
      expiresValue.style.color = '#f44336';
    }
  }
}

// Setup event listeners
function setupEventListeners() {
  pairBtn.addEventListener('click', handlePair);
  unpairBtn.addEventListener('click', handleUnpair);
  testAutofillBtn.addEventListener('click', handleTestAutofill);

  pairingCodeInput.addEventListener('input', (e) => {
    // Only allow digits
    e.target.value = e.target.value.replace(/[^0-9]/g, '');

    // Enable pair button if code is 6 digits
    pairBtn.disabled = e.target.value.length !== 6;
  });

  pairingCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && pairingCodeInput.value.length === 6) {
      handlePair();
    }
  });

  // Footer links
  document.getElementById('help-link').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'https://github.com/ArcheWizard/Password_Manager/wiki' });
  });

  document.getElementById('settings-link').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  document.getElementById('about-link').addEventListener('click', (e) => {
    e.preventDefault();
    showAboutDialog();
  });
}

// Handle pairing
async function handlePair() {
  const code = pairingCodeInput.value.trim();

  if (code.length !== 6) {
    showError('Please enter a 6-digit code');
    return;
  }

  // Disable button and show loading
  pairBtn.disabled = true;
  pairBtnText.innerHTML = '<span class="loading"></span>Pairing...';

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'pair',
      code: code
    });

    if (response.error) {
      showError(response.error);
      pairBtn.disabled = false;
      pairBtnText.textContent = 'Pair Extension';
      return;
    }

    // Success!
    showSuccess('Successfully paired!');

    // Refresh status after a short delay
    setTimeout(() => {
      checkStatus();
      pairingCodeInput.value = '';
    }, 1000);

  } catch (error) {
    console.error('Pairing error:', error);
    showError('Failed to pair. Please try again.');
    pairBtn.disabled = false;
    pairBtnText.textContent = 'Pair Extension';
  }
}

// Handle unpair
async function handleUnpair() {
  if (!confirm('Are you sure you want to unpair this extension? You will need to pair again to use autofill.')) {
    return;
  }

  unpairBtn.disabled = true;
  unpairBtn.textContent = 'Unpairing...';

  try {
    await chrome.runtime.sendMessage({ action: 'unpair' });
    showSuccess('Extension unpaired');

    setTimeout(() => {
      unpairBtn.disabled = false;
      unpairBtn.textContent = 'Unpair Extension';
      checkStatus();
    }, 1000);

  } catch (error) {
    console.error('Unpair error:', error);
    showError('Failed to unpair');
    unpairBtn.disabled = false;
    unpairBtn.textContent = 'Unpair Extension';
  }
}

// Handle test autofill
async function handleTestAutofill() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab) {
      showError('No active tab found');
      return;
    }

    // Inject content script if not already present
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
    } catch (e) {
      // Script might already be injected
    }

    showSuccess('Check the current page for password fields with autofill icons');
    window.close();

  } catch (error) {
    console.error('Test autofill error:', error);
    showError('Failed to activate autofill');
  }
}

// Show error message
function showError(message) {
  const errorDiv = document.createElement('div');
  errorDiv.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    padding: 10px;
    background: #f44336;
    color: white;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    animation: slideDown 0.3s ease-out;
  `;
  errorDiv.textContent = message;
  document.body.appendChild(errorDiv);

  setTimeout(() => {
    errorDiv.style.animation = 'slideUp 0.3s ease-out';
    setTimeout(() => errorDiv.remove(), 300);
  }, 3000);
}

// Show success message
function showSuccess(message) {
  const successDiv = document.createElement('div');
  successDiv.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    padding: 10px;
    background: #4CAF50;
    color: white;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    animation: slideDown 0.3s ease-out;
  `;
  successDiv.textContent = message;
  document.body.appendChild(successDiv);

  setTimeout(() => {
    successDiv.style.animation = 'slideUp 0.3s ease-out';
    setTimeout(() => successDiv.remove(), 300);
  }, 2000);
}

// Show about dialog
function showAboutDialog() {
  alert(`Secure Password Manager Extension
Version: 0.1.0

A browser extension for secure password autofill and management.

© 2024 ArcheWizard
Licensed under MIT`);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideDown {
    from {
      transform: translateY(-100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideUp {
    from {
      transform: translateY(0);
      opacity: 1;
    }
    to {
      transform: translateY(-100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Initialize on load
init();
