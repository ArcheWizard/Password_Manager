# Privacy Policy - Secure Password Manager Browser Extension

**Last Updated:** December 9, 2025

## Overview

The Secure Password Manager browser extension is designed with privacy as a core principle. This extension facilitates communication between your web browser and the Secure Password Manager desktop application running on your local machine. No data is collected, transmitted to external servers, or shared with third parties.

## Data Collection

**We do not collect any user data.** The extension does not track, log, or transmit any information about your browsing activity, credentials, or personal information to external servers.

## Data Storage

The extension stores minimal data locally in your browser's storage:

- **Authentication Token:** A temporary token used to authenticate with your local desktop application. This token is stored locally and expires after 24 hours (configurable).
- **Browser Fingerprint:** A randomly generated identifier used to distinguish browser instances during pairing.
- **API Base URL:** The localhost address used to communicate with the desktop app (default: `http://127.0.0.1:43110` or `https://127.0.0.1:43110`).
- **Extension Settings:** User preferences such as autofill behavior.

**All data is stored locally in your browser** using the browser's built-in storage APIs. This data never leaves your device.

## Communication

The extension communicates **exclusively with the Secure Password Manager desktop application** running on your local machine via:

- **Localhost HTTP/HTTPS:** Communication over `127.0.0.1:43110` (configurable port)
- **Unix Domain Sockets:** On supported platforms, communication via local socket files

**No external servers are contacted.** All communication is local-only and does not traverse the internet.

## Permissions

The extension requests the following permissions:

- **`storage`**: To store authentication tokens and extension settings locally in your browser.
- **`activeTab`**: To detect login forms on the currently active tab for autofill functionality.
- **`scripting`**: To inject autofill icons and functionality into web pages.
- **`host_permissions (localhost)`**: To communicate with the local desktop application.

These permissions are used solely for the extension's core functionality and are not used to access, collect, or transmit any data outside your local machine.

## Desktop Application Integration

The extension requires the Secure Password Manager desktop application to be installed and running on your local machine. Communication between the extension and desktop app is:

- **Token-based:** Requires explicit pairing via a 6-digit code displayed in the desktop app.
- **Approval-required:** Each credential access request requires explicit user approval in the desktop app.
- **Encrypted:** Optionally uses TLS encryption for localhost communication.

## Third-Party Services

**The extension does not use any third-party services.** No analytics, tracking, advertising, or external APIs are integrated.

## User Control

You have full control over the extension:

- **Pairing:** You must explicitly pair the extension with your desktop app. Unpair at any time.
- **Approvals:** Every credential access request requires your explicit approval in the desktop app.
- **Revocation:** Tokens can be revoked at any time through the desktop app or by unpairing.
- **Uninstall:** Uninstalling the extension removes all stored data from your browser.

## Source Code

The extension is open source. You can review the complete source code at:

[GitHub Repository URL]

## Changes to This Policy

We may update this privacy policy from time to time. Changes will be posted to this page with an updated "Last Updated" date. Continued use of the extension after changes constitutes acceptance of the updated policy.

## Contact

For questions or concerns about this privacy policy, please contact:

- **Email:** [Your Email]
- **GitHub Issues:** [GitHub Issues URL]

## Compliance

This extension complies with:

- Chrome Web Store Developer Program Policies
- Firefox Add-on Policies
- General Data Protection Regulation (GDPR) - No personal data is collected or processed
- California Consumer Privacy Act (CCPA) - No personal data is collected or sold

## Children's Privacy

The extension does not knowingly collect information from children under 13. If you are under 13, please do not use this extension.

## Data Retention

Authentication tokens expire after 24 hours (configurable) and are automatically removed. All other stored data persists until:

- The extension is uninstalled
- You manually clear browser data
- You unpair the extension from the desktop app

## Security

Security measures:

- **Local-only communication:** No internet connectivity
- **Token expiration:** Automatic token expiration
- **TLS encryption:** Optional TLS for localhost communication
- **Desktop approval:** Explicit user approval required for credential access
- **Open source:** Transparent and auditable code

## Your Rights

Since no personal data is collected or processed, there is no data to:

- Access
- Correct
- Delete
- Export
- Object to processing

All data generated by the extension is under your control and stored locally on your device.

---

**Summary:** This extension respects your privacy by design. No data collection, no tracking, no external communication. All data stays on your device.
