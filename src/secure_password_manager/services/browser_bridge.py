"""Local browser bridge RPC service implemented with FastAPI."""

from __future__ import annotations

import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from pydantic import BaseModel

from secure_password_manager.utils import config
from secure_password_manager.utils.approval_manager import (
    ApprovalDecision,
    get_approval_manager,
)
from secure_password_manager.utils.crypto import decrypt_password, encrypt_password
from secure_password_manager.utils.database import add_password, get_passwords
from secure_password_manager.utils.domain_socket import (
    cleanup_socket,
    create_socket_server,
    get_socket_path,
    is_socket_available,
    receive_message,
    send_message,
)
from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_browser_bridge_tokens_path
from secure_password_manager.utils.payload_encryption import create_payload_encryptor
from secure_password_manager.utils.tls import (
    cert_exists,
    generate_self_signed_cert,
    get_cert_fingerprint,
    get_cert_paths,
)


class PairingRequest(BaseModel):
    code: str
    fingerprint: str
    browser: Optional[str] = None


class CredentialsQueryRequest(BaseModel):
    origin: str
    allow_autofill: bool = True


class TokenStore:
    """Simple JSON-backed token store."""

    def __init__(self, path: Path, ttl_hours: int = 24) -> None:
        self.path = path
        self.ttl = ttl_hours * 3600
        self._tokens = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            with open(self.path, encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            log_warning("Failed to load browser bridge tokens; regenerating store")
        return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._tokens, handle, indent=2, sort_keys=True)

    def issue_token(self, fingerprint: str, browser: Optional[str]) -> Dict[str, Any]:
        token = secrets.token_urlsafe(32)
        record = {
            "token": token,
            "fingerprint": fingerprint,
            "browser": browser or "unknown",
            "issued_at": int(time.time()),
            "expires_at": int(time.time() + self.ttl),
        }
        self._tokens[token] = record
        self._save()
        return record

    def validate(self, token: str) -> Optional[Dict[str, Any]]:
        record = self._tokens.get(token)
        if not record:
            return None
        if record.get("expires_at", 0) < time.time():
            self.revoke(token)
            return None
        return record

    def revoke(self, token: str) -> bool:
        if token in self._tokens:
            self._tokens.pop(token)
            self._save()
            return True
        return False

    def list_tokens(self) -> List[Dict[str, Any]]:
        now = time.time()
        return [rec for rec in self._tokens.values() if rec.get("expires_at", 0) > now]


class BrowserBridgeService:
    """Encapsulates the FastAPI server and token logic."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, enable_tls: Optional[bool] = None, enable_domain_socket: Optional[bool] = None) -> None:
        settings = config.load_settings().get("browser_bridge", {})
        self.host = host or settings.get("host", "127.0.0.1")
        self.port = port or int(settings.get("port", 43110))
        self.enable_tls = enable_tls if enable_tls is not None else settings.get("enable_tls", False)
        self.enable_domain_socket = enable_domain_socket if enable_domain_socket is not None else settings.get("enable_domain_socket", False)
        ttl_hours = int(settings.get("token_ttl_hours", 24))
        self._token_store = TokenStore(get_browser_bridge_tokens_path(), ttl_hours)
        self._pairing_window_seconds = int(settings.get("pairing_window_seconds", 120))
        self._pairing: Optional[Dict[str, Any]] = None
        self._cert_path: Optional[Path] = None
        self._key_path: Optional[Path] = None
        self._cert_fingerprint: Optional[str] = None

        # Generate TLS certificates if enabled
        if self.enable_tls:
            self._cert_path, self._key_path = generate_self_signed_cert()
            self._cert_fingerprint = get_cert_fingerprint(self._cert_path)

        self._app = self._build_app()
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

        # Domain socket support
        self._socket_server: Optional[Any] = None
        self._socket_thread: Optional[threading.Thread] = None
        self._socket_path = get_socket_path() if is_socket_available() else None

    @property
    def app(self) -> FastAPI:
        return self._app

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="Secure Password Manager Bridge", version="1.0")
        service = self

        # Add CORS middleware to allow browser extension requests
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^(chrome-extension|moz-extension)://.*$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

        def require_token(authorization: str = Header(...)) -> Dict[str, Any]:
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
            token = authorization.split(" ", 1)[1].strip()
            record = service._token_store.validate(token)
            if not record:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
            return record

        @app.get("/v1/status")
        async def status_endpoint() -> Dict[str, Any]:
            status_data = {
                "status": "ok",
                "host": service.host,
                "port": service.port,
                "running": service.is_running,
                "pairing_active": bool(service._pairing),
                "tls_enabled": service.enable_tls,
            }
            if service.enable_tls and service._cert_fingerprint:
                status_data["cert_fingerprint"] = service._cert_fingerprint
            return status_data

        @app.post("/v1/pair")
        async def pair_endpoint(payload: PairingRequest) -> Dict[str, Any]:
            if not service._pairing or service._pairing["expires_at"] < time.time():
                raise HTTPException(
                    status_code=status.HTTP_410_GONE, detail="No active pairing session"
                )
            if payload.code != service._pairing["code"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid pairing code",
                )
            record = service._token_store.issue_token(
                payload.fingerprint, payload.browser
            )
            service._pairing = None
            log_info(
                f"Issued browser bridge token for {payload.fingerprint} ({payload.browser or 'unknown'})"
            )
            return {"token": record["token"], "expires_at": record["expires_at"]}

        @app.post("/v1/credentials/query")
        async def credentials_query(
            payload: CredentialsQueryRequest,
            token: Dict[str, Any] = Depends(require_token),
        ) -> Dict[str, Any]:
            origin = payload.origin.lower()

            # First, collect matching entries
            entries = []
            username_preview = None

            # Extract domain from origin for better matching
            # e.g., "https://github.com" -> "github.com" -> "github"
            origin_domain = (
                origin.replace("https://", "").replace("http://", "").split("/")[0]
            )
            origin_name = (
                origin_domain.split(".")[0] if "." in origin_domain else origin_domain
            )

            for entry in get_passwords():
                (
                    _entry_id,
                    website,
                    username,
                    encrypted,
                    _category,
                    _notes,
                    _created,
                    _updated,
                    _expiry,
                    _favorite,
                ) = entry
                site = (website or "").lower()
                notes = (_notes or "").lower()

                # Match if:
                # 1. Origin is in website field (e.g., "https://github.com" in "https://github.com/login")
                # 2. Origin domain is in website (e.g., "github.com" in "Github")
                # 3. Origin name is in website (e.g., "github" matches "Github", "GitHub", etc.)
                # 4. Origin or domain is in notes field
                if not (
                    origin in site
                    or origin_domain in site
                    or origin_name in site
                    or origin in notes
                    or origin_domain in notes
                ):
                    continue
                try:
                    password = decrypt_password(encrypted)
                except Exception as exc:
                    log_warning(f"Failed to decrypt entry for site {website}: {exc}")
                    continue

                # Store for approval check
                entries.append(
                    {
                        "entry_id": _entry_id,
                        "label": website,
                        "website": website,
                        "username": username,
                        "password": password,
                        "token_id": token.get("fingerprint"),
                    }
                )

                # Save first username for preview
                if username_preview is None:
                    username_preview = username

            # If no entries found, return empty (no approval needed)
            if not entries:
                return {"entries": []}

            # Request approval from user
            try:
                approval_manager = get_approval_manager()
                response = approval_manager.request_approval(
                    origin=origin,
                    browser=token.get("browser", "unknown"),
                    fingerprint=token.get("fingerprint", "unknown"),
                    entry_count=len(entries),
                    username_preview=username_preview,
                )

                # Log the approval decision
                log_info(
                    f"Credential access for {origin}: {response.decision.value} "
                    f"(remember={response.remember}, browser={token.get('browser')})"
                )

                # Return credentials only if approved
                if response.decision == ApprovalDecision.APPROVED:
                    return {"entries": entries}
                else:
                    # Denied or timed out
                    return {
                        "entries": [],
                        "error": (
                            "Access denied"
                            if response.decision == ApprovalDecision.DENIED
                            else "Request timed out"
                        ),
                    }
            except Exception as exc:
                log_warning(f"Approval request failed: {exc}")
                return {"entries": [], "error": "Approval request failed"}

        @app.post("/v1/credentials/check")
        async def credentials_check(
            payload: Dict[str, Any],
            token: Dict[str, Any] = Depends(require_token),
        ) -> Dict[str, Any]:
            """Check if credentials exist without requiring approval (for duplicate detection)."""
            origin = payload.get("origin", "").lower()
            username = payload.get("username", "")

            if not origin or not username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing origin or username",
                )

            # Extract domain from origin for matching
            origin_domain = (
                origin.replace("https://", "").replace("http://", "").split("/")[0]
            )
            origin_name = (
                origin_domain.split(".")[0] if "." in origin_domain else origin_domain
            )

            # Check if credentials exist (without decrypting passwords)
            for entry in get_passwords():
                (
                    _entry_id,
                    website,
                    entry_username,
                    _encrypted,
                    _category,
                    _notes,
                    _created,
                    _updated,
                    _expiry,
                    _favorite,
                ) = entry
                site = (website or "").lower()
                notes = (_notes or "").lower()

                # Match origin with website/notes
                if not (
                    origin in site
                    or origin_domain in site
                    or origin_name in site
                    or origin in notes
                    or origin_domain in notes
                ):
                    continue

                # Check if username matches
                if entry_username == username:
                    return {"exists": True}

            return {"exists": False}

        @app.post("/v1/credentials/store")
        async def credentials_store(
            payload: Dict[str, Any],
            token: Dict[str, Any] = Depends(require_token),
        ) -> Dict[str, Any]:
            """Store new credentials in the vault."""
            try:
                origin = payload.get("origin", "")
                title = payload.get("title", "")
                username = payload.get("username", "")
                password = payload.get("password", "")
                metadata = payload.get("metadata", {})

                # Validate required fields
                if not all([origin, username, password]):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Missing required fields: origin, username, password",
                    )

                # Use title or fallback to origin for website field
                website = title or origin

                # Encrypt the password
                encrypted_password = encrypt_password(password)

                # Build notes from metadata if provided
                notes_parts = []
                if metadata.get("url"):
                    notes_parts.append(f"URL: {metadata['url']}")
                if metadata.get("saved_at"):
                    notes_parts.append(f"Saved: {metadata['saved_at']}")
                notes_parts.append(f"Source: Browser Extension ({token.get('browser', 'unknown')})")
                notes = "\n".join(notes_parts)

                # Add to database
                add_password(
                    website=website,
                    username=username,
                    encrypted_password=encrypted_password,
                    category="Web",
                    notes=notes,
                )

                log_info(
                    f"Browser bridge stored credentials for {website} (user: {username}) "
                    f"from {token.get('fingerprint')}"
                )

                return {
                    "status": "saved",
                    "website": website,
                    "username": username,
                }
            except HTTPException:
                raise
            except Exception as exc:
                log_warning(f"Failed to store credentials: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to store credentials: {str(exc)}",
                )

        @app.post("/v1/audit/report")
        async def audit_report(
            payload: Dict[str, Any],
            token: Dict[str, Any] = Depends(require_token),
        ) -> Dict[str, Any]:
            log_info(
                f"Received audit report from {token.get('fingerprint')}: {payload.get('summary', 'n/a')}"
            )
            return {"status": "recorded"}

        @app.post("/v1/clipboard/clear")
        async def clipboard_clear(
            token: Dict[str, Any] = Depends(require_token),
        ) -> Dict[str, Any]:
            log_info(f"Clipboard clear requested by {token.get('fingerprint')}")
            return {"status": "cleared"}

        return app

    @property
    def is_running(self) -> bool:
        http_running = bool(self._server and self._thread and self._thread.is_alive())
        socket_running = bool(self._socket_server and self._socket_thread and self._socket_thread.is_alive())
        return http_running or socket_running

    def _handle_socket_request(self, conn: Any) -> None:
        """Handle a single domain socket connection."""
        try:
            # Receive request
            request = receive_message(conn, timeout=30.0)

            # Route request based on path/action
            path = request.get("path", "")
            method = request.get("method", "GET")
            headers = request.get("headers", {})
            body = request.get("body", {})

            # Process request through FastAPI app endpoints
            # For now, handle the most common endpoints directly
            response = {"status_code": 404, "body": {"detail": "Not found"}}

            if path == "/v1/pair" and method == "POST":
                # Handle pairing
                try:
                    pair_request = PairingRequest(**body)
                    if not self._pairing or time.time() > self._pairing["expires_at"]:
                        response = {"status_code": 400, "body": {"detail": "No active pairing code"}}
                    elif self._pairing["code"] != pair_request.code:
                        response = {"status_code": 403, "body": {"detail": "Invalid pairing code"}}
                    else:
                        record = self._token_store.issue_token(pair_request.fingerprint, pair_request.browser)
                        self._pairing = None
                        response = {"status_code": 200, "body": {
                            "token": record["token"],
                            "expires_at": record["expires_at"],
                        }}
                except Exception as e:
                    response = {"status_code": 400, "body": {"detail": str(e)}}

            elif path == "/v1/credentials/query" and method == "POST":
                # Handle credentials query
                auth_header = headers.get("authorization", "")
                if not auth_header.startswith("Bearer "):
                    response = {"status_code": 401, "body": {"detail": "Missing authorization"}}
                else:
                    token_str = auth_header.split(" ", 1)[1].strip()
                    token_rec = self._token_store.validate(token_str)
                    if not token_rec:
                        response = {"status_code": 401, "body": {"detail": "Invalid or expired token"}}
                    else:
                        try:
                            query = CredentialsQueryRequest(**body)
                            # Process credentials query (simplified version)
                            origin = query.origin
                            entries = []

                            origin_domain = origin.replace("https://", "").replace("http://", "").split("/")[0]
                            origin_name = origin_domain.split(".")[0] if "." in origin_domain else origin_domain

                            for entry in get_passwords():
                                (_entry_id, website, username, encrypted, _category, _notes,
                                 _created, _updated, _expiry, _favorite) = entry
                                site = (website or "").lower()
                                notes = (_notes or "").lower()

                                if not (origin in site or origin_domain in site or origin_name in site or
                                       origin in notes or origin_domain in notes):
                                    continue

                                try:
                                    password = decrypt_password(encrypted)
                                    entries.append({
                                        "entry_id": _entry_id,
                                        "website": website,
                                        "username": username,
                                        "password": password,
                                    })
                                except Exception:
                                    continue

                            # Request approval
                            approval_manager = get_approval_manager()
                            username_preview = entries[0]["username"] if entries else None
                            approval_response = approval_manager.request_approval(
                                origin=origin,
                                browser=token_rec.get("browser", "unknown"),
                                fingerprint=token_rec["fingerprint"],
                                entry_count=len(entries),
                                username_preview=username_preview,
                            )

                            if approval_response.decision == ApprovalDecision.APPROVED:
                                response = {"status_code": 200, "body": {"credentials": entries}}
                            else:
                                response = {"status_code": 403, "body": {"detail": "User denied access"}}
                        except Exception as e:
                            response = {"status_code": 500, "body": {"detail": str(e)}}

            # Send response
            send_message(conn, response)

        except Exception as e:
            log_warning(f"Error handling socket request: {e}")
            try:
                send_message(conn, {"status_code": 500, "body": {"detail": "Internal server error"}})
            except Exception:
                pass
        finally:
            conn.close()

    def _run_socket_server(self) -> None:
        """Run the domain socket server loop."""
        if not self._socket_server or not self._socket_path:
            return

        log_info(f"Domain socket server listening on {self._socket_path}")

        while self._socket_server:
            try:
                conn, _ = self._socket_server.accept()
                # Handle each connection in a separate thread
                handler_thread = threading.Thread(
                    target=self._handle_socket_request,
                    args=(conn,),
                    daemon=True
                )
                handler_thread.start()
            except OSError:
                # Socket closed or error
                break
            except Exception as e:
                log_warning(f"Socket server error: {e}")

    def start(self) -> None:
        if self.is_running:
            return

        # Start HTTP/HTTPS server
        # Configure TLS if enabled
        if self.enable_tls and self._cert_path and self._key_path:
            log_info(f"Browser bridge TLS enabled with certificate fingerprint: {self._cert_fingerprint}")
            config_obj = uvicorn.Config(
                self._app,
                host=self.host,
                port=self.port,
                log_level="warning",
                ssl_keyfile=str(self._key_path),
                ssl_certfile=str(self._cert_path),
            )
        else:
            config_obj = uvicorn.Config(
                self._app,
                host=self.host,
                port=self.port,
                log_level="warning",
            )

        self._server = uvicorn.Server(config_obj)

        def _run_server() -> None:
            if self._server:
                self._server.run()

        self._thread = threading.Thread(target=_run_server, daemon=True)
        self._thread.start()
        protocol = "https" if self.enable_tls else "http"
        log_info(f"Browser bridge started on {protocol}://{self.host}:{self.port}")

        # Start domain socket server if enabled
        if self.enable_domain_socket and is_socket_available() and self._socket_path:
            try:
                self._socket_server = create_socket_server(self._socket_path)
                self._socket_thread = threading.Thread(target=self._run_socket_server, daemon=True)
                self._socket_thread.start()
                log_info(f"Domain socket bridge started on {self._socket_path}")
            except Exception as e:
                log_warning(f"Failed to start domain socket server: {e}")

    def stop(self) -> None:
        # Stop HTTP server
        if self._server:
            self._server.should_exit = True
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        self._server = None

        # Stop domain socket server
        if self._socket_server:
            try:
                self._socket_server.close()
            except Exception as e:
                log_warning(f"Error closing socket server: {e}")
            self._socket_server = None

        if self._socket_thread:
            self._socket_thread.join(timeout=3)
            self._socket_thread = None

        # Cleanup socket file
        if self._socket_path:
            cleanup_socket(self._socket_path)

        log_info("Browser bridge stopped")

    def generate_pairing_code(self) -> Dict[str, Any]:
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires = time.time() + self._pairing_window_seconds
        self._pairing = {"code": code, "expires_at": expires}
        log_info("Browser bridge pairing code generated")
        return {"code": code, "expires_at": int(expires)}

    def list_tokens(self) -> List[Dict[str, Any]]:
        return self._token_store.list_tokens()

    def revoke_token(self, token: str) -> bool:
        return self._token_store.revoke(token)


_service_instance: Optional[BrowserBridgeService] = None


def get_browser_bridge_service() -> BrowserBridgeService:
    global _service_instance
    if _service_instance is None:
        _service_instance = BrowserBridgeService()
    return _service_instance
