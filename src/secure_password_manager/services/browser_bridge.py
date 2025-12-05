"""Local browser bridge RPC service implemented with FastAPI."""

from __future__ import annotations

import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel
import uvicorn

from secure_password_manager.utils import config
from secure_password_manager.utils.approval_manager import (
    ApprovalDecision,
    get_approval_manager,
)
from secure_password_manager.utils.crypto import decrypt_password
from secure_password_manager.utils.database import get_passwords
from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_browser_bridge_tokens_path


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
            import json

            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            log_warning("Failed to load browser bridge tokens; regenerating store")
        return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        import json

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
        return [
            rec for rec in self._tokens.values() if rec.get("expires_at", 0) > now
        ]


class BrowserBridgeService:
    """Encapsulates the FastAPI server and token logic."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        settings = config.load_settings().get("browser_bridge", {})
        self.host = host or settings.get("host", "127.0.0.1")
        self.port = port or int(settings.get("port", 43110))
        ttl_hours = int(settings.get("token_ttl_hours", 24))
        self._token_store = TokenStore(get_browser_bridge_tokens_path(), ttl_hours)
        self._pairing_window_seconds = int(
            settings.get("pairing_window_seconds", 120)
        )
        self._pairing: Optional[Dict[str, Any]] = None
        self._app = self._build_app()
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def app(self) -> FastAPI:
        return self._app

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="Secure Password Manager Bridge", version="1.0")
        service = self

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
            return {
                "status": "ok",
                "host": service.host,
                "port": service.port,
                "running": service.is_running,
                "pairing_active": bool(service._pairing),
            }

        @app.post("/v1/pair")
        async def pair_endpoint(payload: PairingRequest) -> Dict[str, Any]:
            if not service._pairing or service._pairing["expires_at"] < time.time():
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="No active pairing session")
            if payload.code != service._pairing["code"]:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid pairing code")
            record = service._token_store.issue_token(payload.fingerprint, payload.browser)
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
                if origin not in site:
                    continue
                try:
                    password = decrypt_password(encrypted)
                except Exception as exc:  # pragma: no cover - defensive
                    log_warning(f"Failed to decrypt entry for site {website}: {exc}")
                    continue

                # Store for approval check
                entries.append(
                    {
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
                    "error": "Access denied" if response.decision == ApprovalDecision.DENIED else "Request timed out",
                }


        @app.post("/v1/credentials/store")
        async def credentials_store(
            payload: Dict[str, Any],
            token: Dict[str, Any] = Depends(require_token),
        ) -> Dict[str, Any]:
            log_info(
                f"Browser bridge store request from {token.get('fingerprint')}: {payload.get('origin', 'unknown')}"
            )
            return {"status": "accepted"}

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
        return bool(self._server and self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.is_running:
            return

        config_obj = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config_obj)

        def _run_server() -> None:
            self._server.run()

        self._thread = threading.Thread(target=_run_server, daemon=True)
        self._thread.start()
        log_info(f"Browser bridge started on {self.host}:{self.port}")

    def stop(self) -> None:
        if self._server:
            self._server.should_exit = True
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        self._server = None
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