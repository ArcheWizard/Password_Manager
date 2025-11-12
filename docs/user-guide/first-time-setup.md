# First-Time Setup Guide

## Overview

When you run the Password Manager for the first time (either CLI or GUI), you'll be prompted to create a master password. This password is crucial as it protects all your stored passwords.

## CLI First-Time Setup

When you run `password-manager` for the first time:

```bash
password-manager
```

You'll see:

```text
==================================================
              Password Manager Login
==================================================
! First-time setup. You'll need to create a master password.
This password will protect all your stored passwords.
Make sure it's secure and you don't forget it!

Create master password:
```

**Steps:**

1. Enter a master password (at least 8 characters)
2. Confirm the password by entering it again
3. If your password is weak, you'll be warned but can still use it
4. Your master password is created and saved

## GUI First-Time Setup

When you run `password-manager-gui` for the first time, you'll see:

**Step 1: Welcome Dialog**

- A welcome message explaining this is first-time setup
- Information about the importance of the master password
- Warning that forgotten passwords cannot be recovered

**Step 2: Create Master Password**

- Enter a master password (minimum 8 characters)
- Confirm the password

**Step 3: Password Strength Check**

- If your password is weak (strength < 3/4), you'll get a warning
- You can choose to use it anyway or create a stronger password
- The system will provide suggestions for improvement

**Step 4: Complete**

- Success message confirming your master password is created
- You can now start using the Password Manager

## Master Password Requirements

- **Minimum length:** 8 characters
- **Recommended:** At least 12 characters with a mix of:
  - Uppercase letters
  - Lowercase letters
  - Numbers
  - Special characters

## Important Notes

⚠️ **Critical Information:**

1. **Don't forget your master password!** There is no password recovery option
2. **Keep it secure:** Don't share your master password with anyone
3. **Unique password:** Use a password you don't use elsewhere
4. **Write it down:** Consider keeping a secure physical backup in a safe place

## Data Storage Locations

### Development Mode

When running from source code:

- All data stored in: `<project-directory>/.data/`
- Files: `auth.json`, `passwords.db`, `secret.key`, etc.

### Production Mode

When installed via pip:

- Data directory: `~/.local/share/secure-password-manager/`
- Config directory: `~/.config/secure-password-manager/`
- Cache directory: `~/.cache/secure-password-manager/`

## Testing First-Time Setup

To test the first-time setup again:

```bash
# Backup your current data
mv .data/auth.json .data/auth.json.backup

# Run the application
password-manager-gui  # or password-manager

# Restore after testing
mv .data/auth.json.backup .data/auth.json
```

## Troubleshooting

### "First-time setup" appears every time

- Check that `auth.json` is being created in the correct location
- Run: `python -c "from secure_password_manager.utils.paths import print_paths_info; print_paths_info()"`
- Verify the auth file path matches where the file is being created

### GUI won't launch

- Ensure PyQt5 is installed: `pip install PyQt5`
- Check for error messages in the terminal
- Verify the package is installed: `pip show secure-password-manager`

### Password not accepted after setup

- The password hash might not have been saved correctly
- Check if `.data/auth.json` exists and has content
- You may need to delete it and go through first-time setup again

## Next Steps

After completing first-time setup:

- Add your first password
- Explore the backup options
- Consider enabling 2FA for additional security
- Review the security audit features
