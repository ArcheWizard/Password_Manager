Secure Password Manager - Firefox Extension
===========================================

Installation (Developer Mode):
1. Open Firefox and navigate to about:debugging
2. Click "This Firefox" in the sidebar
3. Click "Load Temporary Add-on"
4. Select the manifest.json file from this directory (build/firefox)

Pairing with Desktop App:
1. Start the Secure Password Manager desktop app
2. Open the extension popup (click the extension icon)
3. Click "Pair with Desktop App"
4. Enter the 6-digit pairing code from the desktop app
5. Click "Pair" button

Usage:
- Navigate to any login page
- Click the lock icon next to password fields
- Select credentials from the desktop app (requires approval)
- Forms are automatically monitored for saving new credentials

Note: Temporary add-ons are removed when Firefox closes.
For permanent installation, the extension needs to be signed by Mozilla.

For more information, see the main README.md
