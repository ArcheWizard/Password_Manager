# Browser Extension Publishing Guide

This guide covers the steps to publish the Secure Password Manager browser extensions to the Chrome Web Store and Firefox Add-ons.

## Version

Current version: **1.10.4**

## Prerequisites

### Chrome Web Store

- Google account
- Developer account ($5 one-time registration fee)
- Chrome Web Store Developer Dashboard access
- Privacy policy URL (required for extensions requesting host permissions)

### Firefox Add-ons

- Firefox account
- Add-ons Developer Hub access
- AMO (addons.mozilla.org) API credentials for automated uploads

## Pre-Publishing Checklist

- [ ] Version numbers match across all manifests and main package
- [ ] Extension icons created (16x16, 32x32, 48x48, 128x128 PNG)
- [ ] Screenshots prepared (1280x800 or 640x400 recommended)
- [ ] Privacy policy published and URL available
- [ ] Extension tested on both Chrome and Firefox
- [ ] Build scripts produce clean artifacts
- [ ] All permissions justified in store listing

## Building for Distribution

### Chrome Extension

```bash
cd browser-extension
./build-chrome.sh
```

This creates `build/chrome/` directory with:

- `manifest.json` (Manifest v3)
- `background.js` (service worker)
- `content.js`
- `popup.html`, `popup.js`
- `icons/` directory

**Create ZIP for upload:**

```bash
cd build/chrome
zip -r secure-password-manager-chrome-1.10.3.zip .
```

### Firefox Extension

```bash
cd browser-extension
./build-firefox.sh
```

This creates `build/firefox/` directory with:

- `manifest.json` (Manifest v2)
- `background.js` (background script)
- `content.js`
- `popup.html`, `popup.js`
- `icons/` directory

**Create ZIP for upload:**

```bash
cd build/firefox
zip -r secure-password-manager-firefox-1.10.3.zip .
```

**Or create signed XPI with web-ext:**

```bash
cd build/firefox
npx web-ext build
# Creates .xpi file in web-ext-artifacts/
```

## Chrome Web Store Publishing

### Initial Submission

1. **Go to Chrome Web Store Developer Dashboard**
   - <https://chrome.google.com/webstore/devconsole>

2. **Click "New Item"**
   - Upload `secure-password-manager-chrome-1.10.3.zip`

3. **Fill Store Listing**

   **Product Details:**
   - **Name:** Secure Password Manager
   - **Summary:** Secure credential autofill and management from your desktop password manager
   - **Description:**

     ```
     Official browser extension for Secure Password Manager - a local-first password vault.

     Features:
     • Secure credential autofill on any website
     • Desktop approval required for all credential access
     • Local communication only (no cloud sync)
     • Token-based authentication with automatic expiration
     • Save new credentials directly from browser
     • TLS encryption for localhost communication

     Requirements:
     • Desktop app must be installed and running
     • Pair extension with desktop app using 6-digit code
     • Desktop approval required for each credential request

     Privacy:
     • All credentials stored locally on your device
     • No telemetry or tracking
     • Open source software

     Get the desktop app: [GitHub URL]
     Documentation: [Docs URL]
     ```

   **Category:** Productivity

   **Language:** English

4. **Privacy & Security**

   **Privacy Policy:** [Your URL]

   **Justification for Permissions:**
   - `storage`: Store authentication tokens and extension settings
   - `activeTab`: Detect login forms on current tab
   - `scripting`: Inject autofill functionality into web pages
   - `host_permissions (localhost)`: Communicate with local desktop app

   **Single Purpose Description:**
   > This extension provides secure credential autofill by communicating with the Secure Password Manager desktop application running on the user's local machine.

5. **Assets**

   - **Icons:** Upload 16x16, 32x32, 48x48, 128x128 PNG icons
   - **Screenshots:** Upload 1-5 screenshots (1280x800 recommended)
   - **Promotional tile:** 440x280 PNG (optional)
   - **Marquee promo tile:** 1400x560 PNG (optional)

6. **Distribution**

   - **Visibility:** Public
   - **Regions:** All regions

7. **Submit for Review**

   Review typically takes 1-3 business days.

### Updates

For subsequent versions:

1. Upload new ZIP with updated version in manifest
2. Update "What's New" section with changelog
3. Submit for review

**Note:** Minor updates (bug fixes) typically review faster than major feature additions.

## Firefox Add-ons Publishing

### Initial Submission

1. **Go to Firefox Add-ons Developer Hub**
   - <https://addons.mozilla.org/developers/>

2. **Click "Submit a New Add-on"**

   - **Where will your add-on be listed?** On this site
   - **Do you have a signed add-on?** No (unless you pre-signed with web-ext)

3. **Upload Add-on**

   - Upload `secure-password-manager-firefox-1.10.3.zip`
   - Select **Firefox** as platform
   - Select distribution channel: **Listed** (appears in AMO) or **Unlisted** (direct distribution)

4. **Describe Add-on**

   **Name:** Secure Password Manager

   **Summary:** (Maximum 250 characters)

   ```
   Secure credential autofill from your local password vault. Requires desktop app.
   All data stays on your device with no cloud sync.
   ```

   **Description:**

   ```
   Official browser extension for Secure Password Manager - a local-first password vault.

   FEATURES
   • Secure credential autofill on any website
   • Desktop approval required for all credential access
   • Local communication only (no cloud sync)
   • Token-based authentication with automatic expiration
   • Save new credentials directly from browser
   • TLS encryption for localhost communication

   REQUIREMENTS
   • Desktop app must be installed and running (download from GitHub)
   • Pair extension with desktop app using 6-digit code
   • Desktop approval required for each credential request

   PRIVACY
   • All credentials stored locally on your device
   • No telemetry or tracking
   • Open source software

   SUPPORT
   Get the desktop app: [GitHub URL]
   Documentation: [Docs URL]
   Report issues: [GitHub Issues URL]
   ```

   **Homepage:** [GitHub repo URL]

   **Support email:** [Your email]

   **License:** MIT

   **Privacy Policy:** [Your URL]

   **Category:** Privacy & Security

5. **Version Details**

   **Version number:** 1.10.3

   **License:** MIT License

   **Release notes:**

   ```
   Initial release with core features:
   - Secure pairing with desktop app
   - Credential autofill with approval prompts
   - Credential saving
   - TLS support
   ```

   **Source code:** [GitHub repo URL or upload source ZIP]

   **Technical details:**
   - Compatible with Firefox 109+
   - Uses Manifest V2 (V3 migration planned)

6. **Media**

   - **Icon:** 128x128 PNG
   - **Screenshots:** 1-10 images (up to 4MB each)

7. **Submit for Review**

   Initial review typically takes 1-5 business days. Mozilla reviews code for security and policy compliance.

### Updates

For subsequent versions:

1. **Click "Upload New Version"** on add-on page
2. Upload new ZIP with updated version in manifest
3. Add release notes describing changes
4. Submit for review

### Automated Uploads with web-ext

Install web-ext globally:

```bash
npm install -g web-ext
```

Sign and upload:

```bash
cd browser-extension/build/firefox
web-ext sign \
  --api-key=YOUR_AMO_API_KEY \
  --api-secret=YOUR_AMO_API_SECRET \
  --channel=listed
```

This creates a signed XPI and uploads to AMO.

## Post-Publishing Tasks

After both extensions are published:

- [ ] Update README.md with store links
- [ ] Update browser-extension/README.md with installation instructions
- [ ] Add badges to GitHub repository
- [ ] Announce on release notes
- [ ] Update documentation with direct install links

## Store Badges

### Chrome Web Store

```markdown
[![Chrome Web Store](https://img.shields.io/chrome-web-store/v/YOUR_EXTENSION_ID.svg)](https://chrome.google.com/webstore/detail/YOUR_EXTENSION_ID)
[![Chrome Web Store Users](https://img.shields.io/chrome-web-store/users/YOUR_EXTENSION_ID.svg)](https://chrome.google.com/webstore/detail/YOUR_EXTENSION_ID)
[![Chrome Web Store Rating](https://img.shields.io/chrome-web-store/rating/YOUR_EXTENSION_ID.svg)](https://chrome.google.com/webstore/detail/YOUR_EXTENSION_ID)
```

### Firefox Add-ons

```markdown
[![Mozilla Add-on](https://img.shields.io/amo/v/secure-password-manager.svg)](https://addons.mozilla.org/firefox/addon/secure-password-manager/)
[![Mozilla Add-on Users](https://img.shields.io/amo/users/secure-password-manager.svg)](https://addons.mozilla.org/firefox/addon/secure-password-manager/)
[![Mozilla Add-on Rating](https://img.shields.io/amo/rating/secure-password-manager.svg)](https://addons.mozilla.org/firefox/addon/secure-password-manager/)
```

## Privacy Policy Template

Required for Chrome Web Store. Host at your own URL or use GitHub Pages.

**Key sections to include:**

1. **Data Collection:** State that no user data is collected or transmitted
2. **Storage:** Describe that tokens are stored locally in browser storage
3. **Communication:** Explain localhost-only communication
4. **Third Parties:** State no third-party services are used
5. **User Rights:** Describe how users can revoke access/uninstall

Example URL: `https://github.com/YOUR_USERNAME/Password_Manager/blob/main/PRIVACY.md`

## Review Tips

### Chrome Web Store

- **Minimize permissions:** Only request what's necessary
- **Justify host permissions:** Clearly explain why localhost access is needed
- **Single purpose:** Stick to password management features
- **No obfuscation:** Code must be readable (no minification with source maps)

### Firefox Add-ons

- **Source code required:** Must provide source if using build tools
- **No external scripts:** All code must be bundled or reviewed
- **Security best practices:** Follow MDN extension security guidelines
- **Manifest permissions:** Document each permission in description

## Maintenance

### Version Scheme

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **PATCH:** Bug fixes, no new features
- **MINOR:** New features, backward compatible
- **MAJOR:** Breaking changes

### Release Schedule

- Bug fixes: As needed
- Feature releases: Coordinate with desktop app releases
- Security updates: Immediate

### Monitoring

- Watch for user reviews and ratings
- Monitor support email for issues
- Track download statistics
- Check for policy violations notices

## Troubleshooting

### Chrome Review Rejection

Common reasons:

- Missing privacy policy
- Insufficient permission justification
- Misleading description
- Trademark issues

**Solution:** Address concerns in appeal or update submission

### Firefox Review Rejection

Common reasons:

- Security vulnerabilities detected
- Policy violations (data collection, permissions)
- Missing source code
- Incomplete documentation

**Solution:** Review feedback, fix issues, resubmit

### Slow Review Times

- Chrome: Typically 1-3 days, can be longer for complex extensions
- Firefox: Typically 1-5 days, security reviews take longer

**Expedite:** Contact support if urgent (security fix, broken functionality)

## References

- [Chrome Web Store Developer Program Policies](https://developer.chrome.com/docs/webstore/program-policies/)
- [Firefox Add-on Policies](https://extensionworkshop.com/documentation/publish/add-on-policies/)
- [Chrome Extension Best Practices](https://developer.chrome.com/docs/extensions/mv3/security/)
- [Firefox Extension Security Best Practices](https://extensionworkshop.com/documentation/develop/build-a-secure-extension/)
