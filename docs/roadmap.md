# Roadmap

Strategic initiatives for upcoming releases. Organized by timeframe; actual delivery may shift based on user feedback.

## Completed (v1.10.0 and earlier)

- ✅ **Key Management Upgrades**: Master-password-derived mode with CLI/GUI switching and full vault re-encryption
- ✅ **KDF Tuning UI**: PBKDF2 benchmarking wizard with iteration and salt size tuning
- ✅ **Browser Extension Bridge**: FastAPI-based local RPC service with pairing codes and token management
- ✅ **Desktop Approval Prompts**: User approval required for all credential access with remember-this-domain functionality
- ✅ **Browser Extensions**: Chrome (Manifest v3) and Firefox (Manifest v2) extensions with auto-fill and credential saving
- ✅ **Clipboard Auto-Clear**: Configurable timers across CLI/GUI (default 25 seconds)
- ✅ **Password History**: Full rotation tracking with metadata (manual, expiry, breach, strength)
- ✅ **Comprehensive Testing**: Browser bridge, approval system, and integration test coverage

## Near Term (0–3 months)

- **Browser Extension Enhancements**
  - Add TLS support with certificate pinning for localhost connections
  - Encrypted payload negotiation for added security
  - Domain-socket transports for alternative IPC
  - Browser extension publishing to Chrome Web Store and Firefox Add-ons
- **UX Enhancements**
  - Category manager with colors/icons and persistent filters
  - Enhanced password generator UI with pattern-based generation
  - Bulk operations (select multiple entries for rotation/deletion)
- **Security Audit Enhancements**
  - Parallelized breach checks with offline dictionary update packs
  - Remediation actions (bulk rotate, notify)
  - Security score trending and historical analysis
- **Test & CI Coverage**
  - Achieve ≥90% coverage with branch protection
  - Add pytest-qt smoke suite and coverage reporting in CI
  - Automated release pipeline with version management

## Mid Term (3–9 months)

- **Architecture Refactor**
  - Break monolithic CLI/GUI files into feature modules, share services.
  - Establish plugin API and event bus.
- **Configurability & Profiles**
  - Custom data directories, portable mode, enterprise policy bundles.
- **Platform Integrations**
  - OS keyring binding for KEK storage (Secret Service, Keychain, Credential Manager).
  - Native notifications for expirations, browser events, job failures.
- **Data Model Growth**
  - Tags + attachments + password history tables.
  - Migration manager with schema version tracking.
- **Automation & Observability**
  - Job scheduler UI, Prometheus/statsd exporters, webhook alerts.

## Long Term (9+ months)

- **Advanced Security**
  - Hardware-backed unlock (TPM, Secure Enclave, FIDO2).
  - Key rotation policies, per-entry nonces, envelope encryption redesign.
- **Sync & Collaboration**
  - Encrypted sync providers (self-hosted server, S3/WebDAV, peer-to-peer).
  - Shared vaults with role-based permissions.
- **Packaging & Distribution**
  - Cross-platform installers (AppImage, Flatpak, MSI, PKG).
  - Signed browser extensions with coordinated release pipeline.
- **Ecosystem**
  - Plugin marketplace, documented IPC contracts for third parties.
  - Import/export wizards for major password managers.

## Guiding Principles

- Ship incremental, testable slices.
- Prioritize security improvements over feature count.
- Keep documentation and automation up to date with every milestone.
