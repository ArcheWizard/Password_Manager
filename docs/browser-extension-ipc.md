# Browser Extension & IPC Specification

Defines the contract between the desktop application and companion browser extensions (Chromium/Firefox). The local RPC service is fully implemented with official Chrome and Firefox extensions available; no external cloud component is used.

## Goals

1. Auto-fill credentials in browsers without exposing the entire vault.
2. Allow the extension to push freshly saved credentials back into the desktop vault.
3. Maintain end-to-end encryption and user consent for each interaction.

## High-Level Architecture

```text
Browser Extension  <-->  Local RPC Service (127.0.0.1:43110)  <-->  Core Services
```

- The desktop app spawns a localhost HTTP/gRPC server when "Browser Bridge" is enabled.
- Extensions authenticate once per session using a pairing code displayed in the desktop app.
- Tokens expire quickly and are scoped per browser profile.

### Implementation Status (v1.10.0)

- `secure_password_manager/services/browser_bridge.py` hosts a FastAPI/uvicorn server embedded in the desktop app.
- The service is disabled by default; enable it via CLI `Settings > Browser Bridge` or via the GUI Settings tab.
- When enabled, the service auto-starts with the CLI/GUI process and shuts down automatically when the app exits.
- Pairing codes are six digits, randomly generated, and expire after `pairing_window_seconds` (configurable, default 120s).
- Issued tokens are persisted to `browser_bridge_tokens.json` inside the data directory and can be revoked from either interface.
- Token TTL is configurable via `browser_bridge.token_ttl_hours` in settings (default 24 hours).
- Implemented endpoints: `/v1/status`, `/v1/pair`, `/v1/credentials/query`, `/v1/credentials/store`, `/v1/audit/report`, `/v1/clipboard/clear`.
- All endpoints except `/v1/status` and `/v1/pair` require bearer token authentication.
- **Desktop approval prompts** protect credential access - users must explicitly approve each origin before credentials are returned.
- **"Remember this domain" feature** allows users to auto-approve trusted origins for future requests.
- **Approval decisions** are persisted in `approval_store.json` and can be managed from settings.
- **Browser extensions** for Chrome (Manifest v3) and Firefox (Manifest v2) are fully implemented with auto-fill, credential saving, and secure pairing.
- Upcoming work: encrypted payload negotiation, TLS and certificate pinning, domain-socket transports.

## Transport & Protocol

- **Transport**: Current implementation uses HTTP/1.1 on `127.0.0.1` without TLS (traffic stays local). TLS + certificate pinning and domain socket transports are planned for future releases.
- **Serialization**: JSON for request/response bodies. Future versions may support Protocol Buffers.
- **Port**: Dynamically assigned; default 43110. Advertised via mDNS/Bonjour for multi-device discovery (optional).

## Authentication Flow

1. User opens desktop settings → Browser Bridge → "Pair New Extension".
2. App displays a one-time code (6 digits) and starts a pairing window (2 minutes).
3. Extension prompts user for the code, then sends `POST /v1/pair` with the code + browser fingerprint hash.
4. Desktop verifies code, issues a signed token (JWT or MACed blob) tied to the fingerprint and grants scopes.
5. Extension stores token securely and includes it in `Authorization: Bearer <token>` headers.
6. Tokens expire after 24 hours or when revoked from settings.

## API Surface (v1)

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/v1/pair` | Exchange one-time code for access token. |
| `GET` | `/v1/status` | Health check; returns app version, lock state. |
| `POST` | `/v1/credentials/query` | Retrieve credentials matching requested URL/origin. |
| `POST` | `/v1/credentials/store` | Persist a new credential created in the browser. |
| `POST` | `/v1/clipboard/clear` | Optional remote clipboard wipe request. |
| `POST` | `/v1/audit/report` | Upload browser-side audit data (e.g., autofill failures) for logging. |

### Request/Response Examples

`POST /v1/credentials/query`

```json
{
  "origin": "https://app.example.com",
  "form_fingerprint": "a1b2c3d4",
  "allow_autofill": true
}
```

Response:

```json
{
  "entries": [
    {
      "entry_id": "c8be...",
      "label": "Example Admin",
      "username": "alice",
      "password": "decrypted password",
      "token_id": "fingerprint"
    }
  ]
}
```

Before returning credentials, the desktop app prompts the user for approval:

- CLI mode displays an interactive prompt with origin, browser, and entry count details with color-coded options
- GUI mode shows a modal dialog with approval/deny buttons and a "Remember this domain" checkbox
- If the user approves, credentials are returned; if denied or timeout occurs, an HTTP 403 error is returned
- Remembered approvals are stored in `approval_store.json` and automatically approved for future requests
- Approval decisions are logged in the audit trail with origin, browser, fingerprint, and decision details
- Users can manage remembered approvals in Settings (revoke, clear all)

`POST /v1/credentials/store`

```json
{
  "origin": "https://new.example.com",
  "title": "New Example",
  "username": "bob",
  "password": "encrypted payload",
  "metadata": { "form_id": "login", "notes": "Created from browser" }
}
```

Desktop app decrypts payload, performs policy checks, prompts user for approval, and stores entry. Conflicts prompt the user for merge/overwrite choices.

## Security Requirements

- **User approval**: Every credential access request triggers a desktop approval prompt unless the origin is pre-approved.
- **Remembered approvals**: Users can choose to remember approval decisions for trusted origins; stored in `approval_store.json` with audit logging.
- **Tokens scoped by origin**: Extension must request site-specific approvals; credentials filtered by origin.
- **Browser fingerprinting**: Tokens are bound to browser fingerprints to prevent cross-browser theft.
- **Rate limiting**: Max 5 credential pulls per second per origin to prevent abuse.
- **Audit logging**: Every API call logged with token ID hash, action result, approval decision, and origin.
- **User presence**: Desktop confirmation required for all credential access (auto-approved for remembered origins).
- **Localhost only**: Service binds to 127.0.0.1:43110 (no external network exposure).

## Browser Extensions

Official extensions are available for Chrome/Chromium (Manifest v3) and Firefox (Manifest v2):

- **Auto-Fill**: Click lock icon (🔒) on password fields to trigger credential query with desktop approval
- **Multi-Credential Selection**: Modal appears when multiple entries match the origin
- **Credential Saving**: Automatic save prompts on form submission with desktop approval required
- **Secure Pairing**: 6-digit codes with 120-second expiration window
- **Token Management**: Tokens expire after 24 hours (configurable) with automatic re-pairing prompts
- **Visual Indicators**: Lock icons on password fields, status indicator in popup

Build and installation instructions in `browser-extension/README.md`.

## Versioning & Compatibility

- API version is encoded in the URL (`/v1/...`).
- Breaking changes increment the major version; extensions must negotiate capabilities via `/status`.
- Feature flags (e.g., attachments, shared vaults) returned as part of the status payload.

## Error Handling

- Use standard HTTP codes:
  - `401 Unauthorized`: invalid or expired token.
  - `403 Forbidden`: scope denied, vault locked, or user rejected.
  - `409 Conflict`: duplicate credential.
  - `423 Locked`: vault currently locked; extension should prompt user to unlock desktop app.
- Response body contains `{ "error": { "code": "LOCKED", "message": "Vault locked" } }`.

## Revocation & Device Management

- Desktop settings display paired extensions with fingerprint, browser, last seen.
- User can revoke tokens individually, forcing re-pairing.
- Automatic revocation occurs when the vault password changes or after inactivity.

## Future Enhancements

- WebSocket event stream for real-time prompts (auto-fill approved, rotate now, clipboard cleared).
- Mutual attestation using WebAuthn/FIDO2 security keys.
- Enterprise policy profiles controlling which domains may use browser integration.
