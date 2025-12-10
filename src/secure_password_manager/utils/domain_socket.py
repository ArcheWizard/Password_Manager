"""Domain socket transport utilities for browser bridge IPC.

This module provides Unix domain socket support as an alternative to HTTP
for local IPC between the browser extension and desktop app. Domain sockets
offer better security on Unix-like systems by leveraging filesystem permissions.
"""

from __future__ import annotations

import json
import os
import socket
import stat
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_data_dir


def get_socket_path() -> Path:
    """Get the path for the domain socket.

    Returns:
        Path to the Unix domain socket file.
    """
    # Use XDG runtime directory if available, otherwise data directory
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        socket_dir = Path(runtime_dir) / "secure-password-manager"
        socket_dir.mkdir(parents=True, exist_ok=True)
    else:
        socket_dir = get_data_dir() / "sockets"
        socket_dir.mkdir(parents=True, exist_ok=True)

    socket_path = socket_dir / "bridge.sock"

    # Ensure directory has restrictive permissions (owner only)
    try:
        os.chmod(socket_dir, stat.S_IRWXU)  # 700
    except OSError as e:
        log_warning(f"Failed to set socket directory permissions: {e}")

    return socket_path


def is_socket_available() -> bool:
    """Check if Unix domain sockets are supported on this platform.

    Returns:
        True if domain sockets are available, False otherwise.
    """
    # Unix domain sockets not available on Windows
    if os.name == "nt":
        return False

    # Check if socket module has AF_UNIX support
    return hasattr(socket, "AF_UNIX")


def cleanup_socket(socket_path: Path) -> None:
    """Remove an existing socket file if it exists.

    Args:
        socket_path: Path to the socket file to remove.
    """
    try:
        if socket_path.exists():
            socket_path.unlink()
            log_info(f"Cleaned up socket: {socket_path}")
    except OSError as e:
        log_warning(f"Failed to cleanup socket {socket_path}: {e}")


def create_socket_server(socket_path: Path) -> socket.socket:
    """Create and bind a Unix domain socket server.

    Args:
        socket_path: Path where the socket should be created.

    Returns:
        Bound socket server.

    Raises:
        OSError: If socket creation or binding fails.
        RuntimeError: If domain sockets are not available.
    """
    if not is_socket_available():
        raise RuntimeError("Unix domain sockets are not available on this platform")

    # Clean up any existing socket
    cleanup_socket(socket_path)

    # Create socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        # Bind to path
        sock.bind(str(socket_path))

        # Set restrictive permissions (owner read/write only)
        os.chmod(socket_path, stat.S_IRUSR | stat.S_IWUSR)  # 600

        # Start listening
        sock.listen(5)

        log_info(f"Domain socket server listening on {socket_path}")
        return sock

    except OSError as e:
        sock.close()
        cleanup_socket(socket_path)
        raise OSError(f"Failed to create socket server: {e}") from e


def send_message(sock: socket.socket, message: Dict[str, Any]) -> None:
    """Send a JSON message over a socket.

    Args:
        sock: Socket to send on.
        message: Message dictionary to send.

    Raises:
        OSError: If sending fails.
    """
    data = json.dumps(message).encode("utf-8")
    # Prefix with 4-byte length
    length = len(data).to_bytes(4, byteorder="big")
    sock.sendall(length + data)


def receive_message(sock: socket.socket, timeout: Optional[float] = 30.0) -> Dict[str, Any]:
    """Receive a JSON message from a socket.

    Args:
        sock: Socket to receive from.
        timeout: Timeout in seconds (None for blocking).

    Returns:
        Received message dictionary.

    Raises:
        OSError: If receiving fails.
        json.JSONDecodeError: If message is not valid JSON.
        TimeoutError: If timeout is reached.
    """
    if timeout is not None:
        sock.settimeout(timeout)

    # Read 4-byte length prefix
    length_data = _recv_exact(sock, 4)
    if not length_data:
        raise OSError("Connection closed before receiving length")

    message_length = int.from_bytes(length_data, byteorder="big")

    # Sanity check message length (max 10MB)
    if message_length > 10 * 1024 * 1024:
        raise ValueError(f"Message too large: {message_length} bytes")

    # Read message data
    data = _recv_exact(sock, message_length)
    if not data:
        raise OSError("Connection closed before receiving complete message")

    return json.loads(data.decode("utf-8"))


def _recv_exact(sock: socket.socket, length: int) -> bytes:
    """Receive exactly `length` bytes from socket.

    Args:
        sock: Socket to receive from.
        length: Number of bytes to receive.

    Returns:
        Received bytes.

    Raises:
        OSError: If receiving fails.
    """
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    return data


class DomainSocketClient:
    """Client for connecting to domain socket server."""

    def __init__(self, socket_path: Optional[Path] = None):
        """Initialize client.

        Args:
            socket_path: Path to socket file (default: get_socket_path()).
        """
        self.socket_path = socket_path or get_socket_path()
        self.sock: Optional[socket.socket] = None

    def connect(self, timeout: float = 5.0) -> None:
        """Connect to the socket server.

        Args:
            timeout: Connection timeout in seconds.

        Raises:
            RuntimeError: If domain sockets are not available.
            OSError: If connection fails.
        """
        if not is_socket_available():
            raise RuntimeError("Unix domain sockets are not available on this platform")

        if not self.socket_path.exists():
            raise OSError(f"Socket does not exist: {self.socket_path}")

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

        try:
            self.sock.connect(str(self.socket_path))
            log_info(f"Connected to domain socket: {self.socket_path}")
        except OSError as e:
            self.sock.close()
            self.sock = None
            raise OSError(f"Failed to connect to socket: {e}") from e

    def send(self, message: Dict[str, Any]) -> None:
        """Send a message to the server.

        Args:
            message: Message dictionary to send.

        Raises:
            RuntimeError: If not connected.
            OSError: If sending fails.
        """
        if not self.sock:
            raise RuntimeError("Not connected to socket server")

        send_message(self.sock, message)

    def receive(self, timeout: Optional[float] = 30.0) -> Dict[str, Any]:
        """Receive a message from the server.

        Args:
            timeout: Timeout in seconds (None for blocking).

        Returns:
            Received message dictionary.

        Raises:
            RuntimeError: If not connected.
            OSError: If receiving fails.
        """
        if not self.sock:
            raise RuntimeError("Not connected to socket server")

        return receive_message(self.sock, timeout)

    def close(self) -> None:
        """Close the connection."""
        if self.sock:
            try:
                self.sock.close()
                log_info("Closed domain socket connection")
            except OSError as e:
                log_warning(f"Error closing socket: {e}")
            finally:
                self.sock = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def get_socket_info() -> Dict[str, Any]:
    """Get information about the domain socket configuration.

    Returns:
        Dictionary with socket path, availability, and status.
    """
    socket_path = get_socket_path()
    available = is_socket_available()
    exists = socket_path.exists() if available else False

    info = {
        "available": available,
        "socket_path": str(socket_path) if available else None,
        "exists": exists,
    }

    if exists:
        try:
            stat_info = socket_path.stat()
            info["permissions"] = oct(stat_info.st_mode)[-3:]
            info["owner_uid"] = stat_info.st_uid
        except OSError:
            pass

    return info
