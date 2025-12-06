# Roadmap

Strategic initiatives for upcoming releases. Organized by timeframe; actual delivery may shift based on user feedback.

## Near Term (0–3 months)

- **Key Management Upgrades**
  - ✅ Offer master-password-derived mode (no `secret.key`) with CLI/GUI switching and full vault re-encryption.
  - ✅ Surface KDF tuning UI (iterations, salt size benchmarking wizard) across both interfaces.
- **Browser Extension Bridge**
  - ✅ FastAPI-based local RPC service with pairing codes, CLI/GUI toggles, and token persistence.
  - ✅ Desktop approval prompts for credential access with remember-this-domain functionality.
  - ✅ Ship Chromium/Firefox extension prototype with auto-fill and credential saving (v1.10.0).
  - Add TLS support with certificate pinning for localhost connections.
- **UX Enhancements**
  - ✅ Clipboard auto-clear timers across CLI/GUI.
  - ✅ Password history with rotation metadata.
  - Category manager with colors/icons and persistent filters.
- **Security Audit Enhancements**
  - Parallelized breach checks with offline dictionary update packs.
  - Remediation actions (bulk rotate, notify).
- **Test & CI Coverage**
  - Achieve ≥90% coverage with branch protection.
  - Add pytest-qt smoke suite and coverage reporting in CI.

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
