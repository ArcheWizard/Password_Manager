# Browser Extension & IPC Specification

Defines the contract between the desktop application and companion browser extensions (Chromium/Firefox). This document focuses on the planned local RPC service; no external cloud component is assumed.

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

### Implementation Status (v0)

- `secure_password_manager/services/browser_bridge.py` hosts a FastAPI/uvicorn server embedded in the desktop app.
- The service is disabled by default; enable it via CLI `Settings > Browser Bridge` or via the GUI Settings tab.
- When enabled, the service auto-starts with the CLI/GUI process and shuts down automatically when the app exits.
- Pairing codes are six digits and expire after `pairing_window_seconds` (default 120s).
- Issued tokens are persisted to `browser_bridge_tokens.json` inside the config directory and can be revoked from either interface.
- Implemented endpoints: `/v1/status`, `/v1/pair`, `/v1/credentials/query`, `/v1/credentials/store`, `/v1/audit/report`, `/v1/clipboard/clear`.
- Upcoming work: desktop approval prompts, encrypted payload negotiation, TLS and domain-socket transports.

## Transport & Protocol

- **Transport**: Current alpha uses HTTP/1.1 on `127.0.0.1` without TLS (traffic stays local). TLS + certificate pinning and domain socket transports are planned.
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
      "password": "base64(fernet ciphertext)",
      "totp": "optional current code",
      "requires_user_confirm": true
    }
  ]
}
```

- Passwords remain encrypted during transit. The extension derives the session key shared during pairing to decrypt.
- If `requires_user_confirm` is true, the desktop app displays a prompt before releasing plaintext.

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

Desktop app decrypts payload, performs policy checks, and stores entry. Conflicts prompt the user for merge/overwrite choices.

## Security Requirements

- Tokens scoped by origin: extension must request site-specific approvals.
- Rate limiting: max 5 credential pulls per second per origin.
- Audit logging: every API call logged with token ID hash and action result.
- User presence: optionally require desktop confirmation for high-risk domains.

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
