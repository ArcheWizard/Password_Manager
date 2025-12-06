# Secure Password Manager - Browser Extension

Official browser extension for **Secure Password Manager**, providing seamless credential autofill and secure credential storage directly from your web browser.

## 🌟 Features

- **🔐 Secure Pairing**: Pair with your desktop app using 6-digit codes
- **🔑 Auto-Fill Credentials**: Click the lock icon on password fields to fill credentials
- **💾 Save Credentials**: Automatically prompts to save new login credentials
- **✅ Desktop Approval**: All credential access requires approval from the desktop app
- **🔒 Token-Based Auth**: Secure communication with browser fingerprinting
- **🦊 Multi-Browser**: Chrome (Manifest v3) and Firefox (Manifest v2) support
- **📊 Token Expiration**: Automatic re-pairing when tokens expire

## 🚀 Installation

### Chrome/Chromium (Developer Mode)

1. **Build the Extension**:

   ```bash
   cd browser-extension
   ./build-chrome.sh
   ```

2. **Load in Chrome**:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable **Developer mode** (toggle in top right)
   - Click **Load unpacked**
   - Select the `browser-extension/build/chrome/` directory

3. **Verify Installation**:
   - Extension icon should appear in the toolbar
   - Click the icon to open the popup

### Firefox (Temporary Add-on)

1. **Build the Extension**:

   ```bash
   cd browser-extension
   ./build-firefox.sh
   ```

2. **Load in Firefox**:
   - Open Firefox and navigate to `about:debugging`
   - Click **This Firefox** in the sidebar
   - Click **Load Temporary Add-on**
   - Select the `browser-extension/build/firefox/manifest.json` file

3. **Note**: Temporary add-ons are removed when Firefox closes. For permanent installation, the extension needs to be signed by Mozilla Add-ons.

### Build All Browsers

```bash
cd browser-extension
./build-all.sh
```

## 🔗 Pairing with Desktop App

### Prerequisites

1. **Desktop App Running**: Start `password-manager` or `password-manager-gui`
2. **Browser Bridge Active**: The desktop app automatically starts the browser bridge on `http://127.0.0.1:43110`

### Pairing Process

1. **Open Extension Popup**:
   - Click the extension icon in your browser toolbar

2. **Initiate Pairing**:
   - Click **"Pair with Desktop App"** button
   - The desktop app will display a 6-digit pairing code

3. **Enter Code**:
   - Type the 6-digit code in the extension popup
   - Click **"Pair"**

4. **Confirm Success**:
   - Status indicator turns green: "Connected"
   - Token info displays fingerprint and expiration time

### Re-Pairing

Tokens expire after **30 days**. When expired:

- Extension status shows "Not Paired"
- Re-pair using the same process above

## 📖 Usage Guide

### Auto-Filling Credentials

1. **Navigate to Login Page**:
   - Visit any website with a login form

2. **Look for Autofill Icon**:
   - A small 🔒 lock icon appears next to password fields
   - Hover to see "Fill credentials from Secure Password Manager"

3. **Click to Fill**:
   - Click the lock icon
   - Extension queries credentials for the current origin
   - Desktop app shows approval prompt

4. **Approve on Desktop**:
   - Click **"Approve"** in the desktop app
   - Credentials are sent to the browser

5. **Select Credential** (if multiple):
   - Modal shows all matching credentials
   - Click on the desired credential to fill
   - Form is auto-filled with username and password

### Saving New Credentials

1. **Fill Out Login Form**:
   - Enter your username and password manually
   - Submit the form (e.g., click "Log in")

2. **Save Prompt**:
   - Extension detects form submission
   - Modal asks: "Save these credentials?"
   - Shows origin, username, and masked password

3. **Confirm Save**:
   - Click **"Save"** to store in desktop app
   - Desktop app prompts for approval
   - Approve to save permanently

4. **Skip Saving**:
   - Click **"Cancel"** or close the modal
   - No credentials are sent to the desktop app

### Managing Extension

#### Check Status

- **Open Popup**: Click extension icon
- **Status Indicator**:
  - 🟢 Green: "Connected" - Ready to use
  - 🟡 Yellow: "Not Paired" - Need to pair
  - 🔴 Red: "Disconnected" - Desktop app not running

#### Test Autofill

- Click **"Test Autofill"** in popup
- Opens current tab with content script injected
- Useful for debugging or testing on specific pages

#### Unpair Extension

- Click **"Unpair"** in popup
- Confirmation dialog appears
- Click **"OK"** to clear token and unpair
- Re-pair to use extension again

## 🔒 Security Model

### Token-Based Authentication

- **Browser Fingerprint**: Unique hash from browser properties (user agent, language, timezone, screen, hardware)
- **Pairing Code**: 6-digit code valid for **5 minutes**
- **Token Storage**: Stored in `chrome.storage.local` (encrypted by browser)
- **Token Expiration**: 30 days from pairing, automatic cleanup

### Origin Isolation

- **Origin Matching**: Credentials queried only for exact origin match
- **No Cross-Origin Access**: Extension can't access credentials from other sites
- **Subdomain Handling**: `login.example.com` vs `example.com` are separate origins

### Approval System

- **Desktop Approval Required**: Every credential query requires user approval in desktop app
- **Audit Trail**: All approvals logged in `~/.secure_password_manager/approval_audit.log`
- **Timeout**: Approval prompts expire after **60 seconds**

### Communication Security

- **Localhost Only**: Extension communicates with `http://127.0.0.1:43110` (desktop app)
- **Token Headers**: `Authorization: Bearer <token>` + `X-Browser-Fingerprint: <fingerprint>`
- **No Remote Servers**: All data stays on your local machine

**⚠️ Note**: Communication is currently **HTTP** (not HTTPS). TLS with certificate pinning is planned for v1.11.0.

## 🛠️ Development

### Project Structure

```
browser-extension/
├── manifest.json              # Chrome/Chromium manifest (v3)
├── manifest-firefox.json      # Firefox manifest (v2)
├── background.js              # Chrome service worker
├── background-firefox.js      # Firefox background script (browser.* APIs)
├── content.js                 # Content script (injected into web pages)
├── popup.html                 # Extension popup UI
├── popup.js                   # Popup logic
├── build-chrome.sh            # Build script for Chrome
├── build-firefox.sh           # Build script for Firefox
├── build-all.sh               # Build all browsers
├── README.md                  # This file
└── icons/                     # Extension icons (16x16, 48x48, 128x128)
```

### Key Components

#### Background Script (`background.js`)

- **API Communication**: Handles all requests to desktop app API
- **Token Management**: Stores and retrieves authentication tokens
- **Browser Fingerprinting**: Generates unique browser identifier
- **Message Routing**: Processes messages from content script and popup

**Key Functions**:

- `pairWithDesktop(code)`: POST `/v1/pair` with pairing code
- `queryCredentials(origin)`: POST `/v1/credentials/query` for autofill
- `storeCredentials(data)`: POST `/v1/credentials/store` for saving
- `checkStatus()`: GET `/v1/status` for connection check

#### Content Script (`content.js`)

- **Form Detection**: Finds password fields and associated username fields
- **Icon Injection**: Adds autofill icon next to password fields
- **Credential Filling**: Populates form fields with retrieved credentials
- **Save Prompts**: Monitors form submissions and prompts to save
- **UI Components**: Credential selector modal, notifications

**Key Functions**:

- `findPasswordFields()`: Detects all password inputs on page
- `handleAutofillClick(field)`: Queries credentials and fills form
- `promptToSaveCredentials(origin, username, password)`: Shows save modal
- `fillCredentials(username, password, passwordField)`: Fills form fields

#### Popup (`popup.html` + `popup.js`)

- **Pairing Interface**: 6-digit code input with validation
- **Status Display**: Connection and pairing status indicators
- **Token Info**: Shows fingerprint and expiration time
- **Management Actions**: Test autofill, unpair, help/settings

### Building Extensions

#### Chrome Build

```bash
./build-chrome.sh
```

**Output**: `build/chrome/`

- Copies `manifest.json` (Chrome v3)
- Copies `background.js` (service worker)
- Copies core files: `content.js`, `popup.html`, `popup.js`
- Creates `icons/` directory

#### Firefox Build

```bash
./build-firefox.sh
```

**Output**: `build/firefox/`

- Copies `manifest-firefox.json` → `manifest.json` (Firefox v2)
- Copies `background-firefox.js` → `background.js` (browser.* APIs)
- Copies core files: `content.js`, `popup.html`, `popup.js`
- Creates `icons/` directory

### Testing

1. **Load Extension**: Follow installation instructions above
2. **Start Desktop App**: Run `password-manager` or `password-manager-gui`
3. **Pair Extension**: Use pairing flow with 6-digit code
4. **Test Autofill**:
   - Visit a test login page (e.g., `https://example.com/login`)
   - Add test credentials in desktop app with origin `https://example.com`
   - Click autofill icon on password field
   - Approve in desktop app
   - Verify credentials fill correctly
5. **Test Saving**:
   - Fill out a form manually
   - Submit the form
   - Verify save prompt appears
   - Approve in desktop app
   - Check credentials saved in desktop app

### Debugging

#### Chrome DevTools

1. **Background Service Worker**:
   - Visit `chrome://extensions/`
   - Click "Service worker" link under extension
   - View console logs and debug

2. **Content Script**:
   - Right-click on any web page
   - Click "Inspect" → Console tab
   - Content script logs appear here

3. **Popup**:
   - Right-click on extension icon
   - Click "Inspect popup"
   - View popup console logs

#### Firefox Debugging

1. **Background Script**:
   - Visit `about:debugging#/runtime/this-firefox`
   - Click "Inspect" under extension
   - View console logs

2. **Content Script**:
   - Open web console on any page
   - Content script logs appear here

3. **Popup**:
   - Right-click on extension icon
   - Click "Inspect" → Console tab

### API Endpoints

Extension communicates with desktop app API at `http://127.0.0.1:43110`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/status` | GET | Check if desktop app is running |
| `/v1/pair` | POST | Pair extension with desktop app |
| `/v1/credentials/query` | POST | Request credentials for origin |
| `/v1/credentials/store` | POST | Save new credentials |

**Authentication**: All endpoints (except `/status` and `/pair`) require:

- `Authorization: Bearer <token>` header
- `X-Browser-Fingerprint: <fingerprint>` header

## 🐛 Troubleshooting

### Extension Not Loading

**Chrome**:

- Check `chrome://extensions/` for errors
- Ensure manifest.json is valid JSON
- Verify all referenced files exist in build directory

**Firefox**:

- Check `about:debugging` for errors
- Ensure manifest version is 2 for Firefox
- Verify `browser.*` APIs are used in background script

### Cannot Pair with Desktop App

**Symptoms**: "Failed to pair" error, "Desktop app not running"

**Solutions**:

1. **Check Desktop App**: Ensure `password-manager` or `password-manager-gui` is running
2. **Check Browser Bridge**: Verify bridge is running on port 43110

   ```bash
   curl http://127.0.0.1:43110/v1/status
   ```

3. **Firewall**: Ensure localhost port 43110 is not blocked
4. **Pairing Code**: Code expires after 5 minutes - generate new code
5. **Extension Permissions**: Check extension has `http://127.0.0.1:43110/*` permission

### Autofill Not Working

**Symptoms**: No lock icon appears, or clicking icon does nothing

**Solutions**:

1. **Content Script**: Check browser console for errors
2. **Re-inject Script**: Click "Test Autofill" in extension popup
3. **Field Detection**: Ensure page has `<input type="password">` elements
4. **Page Load**: Wait for page to fully load before expecting icon
5. **Dynamic Forms**: Extension uses MutationObserver, but some SPAs may need manual injection

### Credentials Not Filling

**Symptoms**: Approval works, but form doesn't fill

**Solutions**:

1. **Field Structure**: Check if form has unusual structure (shadow DOM, iframes)
2. **Event Dispatching**: Some sites require custom events - check console logs
3. **Username Field**: Extension may not detect username field correctly
4. **Re-try**: Close modal and try autofill again

### Save Prompt Not Appearing

**Symptoms**: Form submission doesn't trigger save prompt

**Solutions**:

1. **Form Detection**: Ensure form has `<form>` element (not div with onClick)
2. **Submission Method**: Extension detects `submit` events and clicks on submit buttons
3. **Async Submissions**: AJAX submissions may not trigger - extension monitors form changes
4. **Already Saved**: If credentials already exist, prompt may not appear

### Token Expired

**Symptoms**: "Not Paired" status after previously working

**Solutions**:

1. **Re-pair**: Tokens expire after 30 days - follow pairing process again
2. **Check Token**: Click extension icon to see token expiration time
3. **Clear Token**: Click "Unpair" and re-pair if token is corrupted

### Desktop App Not Approving

**Symptoms**: Approval prompt doesn't appear in desktop app

**Solutions**:

1. **Check Logs**: View desktop app logs for approval requests

   ```bash
   tail -f ~/.secure_password_manager/approval_audit.log
   ```

2. **Approval Timeout**: Prompts expire after 60 seconds - try again
3. **GUI vs CLI**: Ensure using `password-manager-gui` for desktop approval prompts
4. **Notification Settings**: Check OS notification permissions for desktop app

## 📦 Packaging for Distribution

### Chrome Web Store

1. **Create .crx Package**:

   ```bash
   # In chrome://extensions/, click "Pack extension"
   # Or use Chrome CLI:
   chromium --pack-extension=./build/chrome --pack-extension-key=key.pem
   ```

2. **Upload to Chrome Web Store**:
   - Visit [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole)
   - Create new item
   - Upload .crx file
   - Fill out store listing
   - Submit for review

### Firefox Add-ons

1. **Create .xpi Package**:

   ```bash
   cd build/firefox
   zip -r ../../secure-password-manager-firefox.xpi *
   ```

2. **Sign with Mozilla**:
   - Visit [Mozilla Add-on Developer Hub](https://addons.mozilla.org/developers/)
   - Create new add-on
   - Upload .xpi file
   - Fill out listing details
   - Submit for review

**Note**: Firefox requires all extensions to be signed by Mozilla for distribution.

## 🔮 Future Enhancements

- **TLS/HTTPS**: Secure communication with certificate pinning (v1.11.0)
- **Settings Page**: Configure autofill behavior, timeout settings
- **Password Generator**: Generate strong passwords directly in extension
- **Credential Editing**: Edit/delete credentials from extension
- **Search Credentials**: Search across all stored credentials
- **Browser History**: Track recent autofills and saves
- **Dark Mode**: Theme support for popup UI
- **Keyboard Shortcuts**: Hotkeys for autofill and save actions
- **Edge Support**: Microsoft Edge manifest v3 compatibility

## 📄 License

Same license as the main Secure Password Manager project.

## 🤝 Contributing

See main project's `docs/contributing.md` for contribution guidelines.

## 📞 Support

- **Issues**: Report bugs in the main project's issue tracker
- **Documentation**: See `docs/` directory for more details
- **IPC Protocol**: See `docs/browser-extension-ipc.md` for API details
