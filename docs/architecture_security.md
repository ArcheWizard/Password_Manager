# Architecture Security Notes

This optional appendix cross-links architecture and security decisions.

- All encryption/decryption is isolated to `utils.crypto` and only receives plaintext at the boundary
- App layers never store plaintext beyond immediate use (except clipboard by user action)
- Security audit computes on decrypted in-memory data and does not persist plaintext
- Backups ensure at-rest encryption using password-derived keys independent of `secret.key`
