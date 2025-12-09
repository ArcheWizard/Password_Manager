// Content script for Secure Password Manager extension
// Detects login forms and provides autofill functionality

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    formDetectionDelay: 500,
    autofillIconSize: 24,
    iconColor: '#4CAF50'
  };

  // State
  let detectedForms = [];
  let currentOrigin = window.location.origin;

  // Detect password input fields
  function findPasswordFields() {
    return Array.from(document.querySelectorAll('input[type="password"]'));
  }

  // Find associated username field for a password field
  function findUsernameField(passwordField) {
    const form = passwordField.closest('form');

    if (form) {
      // Look for email, text, or tel inputs in the same form
      const candidates = form.querySelectorAll('input[type="email"], input[type="text"], input[type="tel"]');

      // Find the closest input before the password field
      let bestCandidate = null;
      let minDistance = Infinity;

      candidates.forEach(input => {
        const distance = Math.abs(
          input.getBoundingClientRect().top - passwordField.getBoundingClientRect().top
        );

        if (distance < minDistance && input.offsetParent !== null) {
          minDistance = distance;
          bestCandidate = input;
        }
      });

      return bestCandidate;
    }

    // Fallback: look for nearby text input
    const allInputs = Array.from(document.querySelectorAll('input[type="email"], input[type="text"]'));
    for (const input of allInputs) {
      if (input.offsetParent === null) continue;

      const rect1 = input.getBoundingClientRect();
      const rect2 = passwordField.getBoundingClientRect();

      if (Math.abs(rect1.top - rect2.top) < 100) {
        return input;
      }
    }

    return null;
  }

  // Create autofill icon
  function createAutofillIcon() {
    const icon = document.createElement('div');
    icon.className = 'spm-autofill-icon';
    icon.innerHTML = `
      <svg width="${CONFIG.autofillIconSize}" height="${CONFIG.autofillIconSize}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="${CONFIG.iconColor}"/>
      </svg>
    `;
    icon.title = 'Autofill from Secure Password Manager';
    icon.style.cssText = `
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      cursor: pointer;
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
      width: ${CONFIG.autofillIconSize}px;
      height: ${CONFIG.autofillIconSize}px;
      border-radius: 50%;
      background: white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      transition: all 0.2s;
    `;

    icon.addEventListener('mouseenter', () => {
      icon.style.transform = 'translateY(-50%) scale(1.1)';
    });

    icon.addEventListener('mouseleave', () => {
      icon.style.transform = 'translateY(-50%) scale(1)';
    });

    return icon;
  }

  // Add autofill icon to password field
  function addAutofillIcon(passwordField, usernameField) {
    // Check if icon already exists
    if (passwordField.dataset.spmIconAdded) {
      return;
    }

    // Make parent position relative if needed
    const parent = passwordField.parentElement;
    if (getComputedStyle(parent).position === 'static') {
      parent.style.position = 'relative';
    }

    const icon = createAutofillIcon();
    icon.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      await handleAutofillClick(passwordField, usernameField);
    });

    parent.appendChild(icon);
    passwordField.dataset.spmIconAdded = 'true';
    passwordField.dataset.spmIcon = 'icon';
  }

  // Handle autofill icon click
  async function handleAutofillClick(passwordField, usernameField) {
    try {
      // Query credentials from background script
      const response = await chrome.runtime.sendMessage({
        action: 'query_credentials',
        origin: currentOrigin
      });

      if (response.error) {
        showNotification('error', response.error);
        return;
      }

      const entries = response.entries;

      if (!entries || entries.length === 0) {
        showNotification('info', 'No credentials found for this site');
        return;
      }

      if (entries.length === 1) {
        // Auto-fill single entry
        fillCredentials(usernameField, passwordField, entries[0]);
        showNotification('success', 'Credentials filled');
      } else {
        // Show selection modal
        showCredentialSelector(entries, usernameField, passwordField);
      }
    } catch (error) {
      console.error('Autofill error:', error);
      showNotification('error', 'Failed to retrieve credentials');
    }
  }

  // Fill credentials into form fields
  function fillCredentials(usernameField, passwordField, entry) {
    if (usernameField && entry.username) {
      usernameField.value = entry.username;
      usernameField.dispatchEvent(new Event('input', { bubbles: true }));
      usernameField.dispatchEvent(new Event('change', { bubbles: true }));
    }

    if (passwordField && entry.password) {
      passwordField.value = entry.password;
      passwordField.dispatchEvent(new Event('input', { bubbles: true }));
      passwordField.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  // Show credential selector modal
  function showCredentialSelector(entries, usernameField, passwordField) {
    // Remove existing modal if present
    const existing = document.getElementById('spm-credential-selector');
    if (existing) {
      existing.remove();
    }

    const modal = document.createElement('div');
    modal.id = 'spm-credential-selector';
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
    `;

    const content = document.createElement('div');
    content.style.cssText = `
      background: white;
      border-radius: 8px;
      padding: 20px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;

    const title = document.createElement('h3');
    title.textContent = 'Select Account';
    title.style.cssText = 'margin: 0 0 15px 0; font-size: 18px; color: #333;';
    content.appendChild(title);

    const list = document.createElement('div');
    entries.forEach((entry, index) => {
      const item = document.createElement('div');
      item.style.cssText = `
        padding: 12px;
        margin: 8px 0;
        border: 1px solid #ddd;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;
      `;

      item.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 4px;">${escapeHtml(entry.username)}</div>
        <div style="font-size: 12px; color: #666;">${escapeHtml(entry.website)}</div>
      `;

      item.addEventListener('mouseenter', () => {
        item.style.background = '#f0f0f0';
      });

      item.addEventListener('mouseleave', () => {
        item.style.background = 'white';
      });

      item.addEventListener('click', () => {
        fillCredentials(usernameField, passwordField, entry);
        modal.remove();
        showNotification('success', 'Credentials filled');
      });

      list.appendChild(item);
    });

    content.appendChild(list);

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.cssText = `
      margin-top: 15px;
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      background: #ddd;
      cursor: pointer;
      width: 100%;
    `;

    cancelBtn.addEventListener('click', () => {
      modal.remove();
    });

    content.appendChild(cancelBtn);
    modal.appendChild(content);

    // Close on outside click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });

    document.body.appendChild(modal);
  }

  // Show notification
  function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 4px;
      color: white;
      font-size: 14px;
      z-index: 999999;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      animation: spm-slide-in 0.3s ease-out;
    `;

    const colors = {
      success: '#4CAF50',
      error: '#f44336',
      info: '#2196F3'
    };

    notification.style.background = colors[type] || colors.info;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'spm-slide-out 0.3s ease-out';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // Escape HTML
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Detect forms and add autofill icons
  function detectForms() {
    const passwordFields = findPasswordFields();

    passwordFields.forEach(passwordField => {
      if (passwordField.dataset.spmIconAdded) {
        return;
      }

      const usernameField = findUsernameField(passwordField);

      // Only add icon if field is visible
      if (passwordField.offsetParent !== null) {
        addAutofillIcon(passwordField, usernameField);

        detectedForms.push({
          password: passwordField,
          username: usernameField
        });
      }
    });
  }

  // Monitor for credential save opportunities
  function monitorFormSubmissions() {
    document.addEventListener('submit', async (e) => {
      const form = e.target;

      if (!(form instanceof HTMLFormElement)) {
        return;
      }

      const passwordField = form.querySelector('input[type="password"]');

      if (!passwordField || !passwordField.value) {
        return;
      }

      const usernameField = findUsernameField(passwordField);

      if (!usernameField || !usernameField.value) {
        return;
      }

      // Check if credentials already exist before prompting
      setTimeout(async () => {
        try {
          const response = await chrome.runtime.sendMessage({
            action: 'check_credentials',
            origin: currentOrigin,
            username: usernameField.value
          });

          if (response.error) {
            // If not paired or error, show save prompt anyway
            promptToSaveCredentials(usernameField.value, passwordField.value);
            return;
          }

          if (response.exists) {
            // Credentials already exist, don't prompt to save
            return;
          }

          // Credentials don't exist, prompt to save
          promptToSaveCredentials(usernameField.value, passwordField.value);
        } catch (error) {
          // On error, show save prompt anyway
          console.error('Failed to check existing credentials:', error);
          promptToSaveCredentials(usernameField.value, passwordField.value);
        }
      }, 1000);
    });
  }

  // Prompt to save credentials
  function promptToSaveCredentials(username, password) {
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      z-index: 999999;
      max-width: 320px;
    `;

    modal.innerHTML = `
      <div style="margin-bottom: 15px; font-weight: bold;">Save Password?</div>
      <div style="margin-bottom: 15px; font-size: 14px; color: #666;">
        Do you want to save credentials for ${escapeHtml(username)}?
      </div>
      <div style="display: flex; gap: 10px;">
        <button id="spm-save-yes" style="flex: 1; padding: 8px; border: none; border-radius: 4px; background: #4CAF50; color: white; cursor: pointer;">
          Save
        </button>
        <button id="spm-save-no" style="flex: 1; padding: 8px; border: none; border-radius: 4px; background: #ddd; cursor: pointer;">
          Not Now
        </button>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('spm-save-yes').addEventListener('click', async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: 'store_credentials',
          origin: currentOrigin,
          website: window.location.hostname,
          username: username,
          password: password,
          metadata: {
            url: window.location.href,
            saved_at: new Date().toISOString()
          }
        });

        if (response.error) {
          showNotification('error', 'Failed to save: ' + response.error);
        } else if (response.success) {
          showNotification('success', `Credentials saved for ${escapeHtml(username)}`);
        } else {
          showNotification('error', 'Failed to save credentials');
        }
      } catch (error) {
        showNotification('error', 'Failed to save credentials');
      }

      modal.remove();
    });

    document.getElementById('spm-save-no').addEventListener('click', () => {
      modal.remove();
    });

    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      if (modal.parentElement) {
        modal.remove();
      }
    }, 10000);
  }

  // Add CSS animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spm-slide-in {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes spm-slide-out {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);

  // Initialize
  function init() {
    // Initial detection
    setTimeout(detectForms, CONFIG.formDetectionDelay);

    // Watch for DOM changes
    const observer = new MutationObserver(() => {
      detectForms();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Monitor form submissions
    monitorFormSubmissions();
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
