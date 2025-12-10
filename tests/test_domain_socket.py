"""Tests for domain socket transport utilities."""

import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.domain_socket import (
    DomainSocketClient,
    cleanup_socket,
    create_socket_server,
    get_socket_info,
    get_socket_path,
    is_socket_available,
    receive_message,
    send_message,
)


@pytest.fixture
def temp_socket_dir(tmp_path):
    """Create a temporary directory for socket testing."""
    socket_dir = tmp_path / "sockets"
    socket_dir.mkdir()
    return socket_dir


@pytest.fixture
def temp_socket_path(temp_socket_dir):
    """Get a temporary socket path."""
    return temp_socket_dir / "test.sock"


def test_is_socket_available():
    """Test socket availability detection."""
    available = is_socket_available()

    # Should be True on Unix-like systems, False on Windows
    if os.name == "nt":
        assert not available
    else:
        assert available


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_cleanup_socket_removes_existing(temp_socket_path):
    """Test that cleanup_socket removes existing socket files."""
    # Create a dummy file
    temp_socket_path.touch()
    assert temp_socket_path.exists()

    # Cleanup should remove it
    cleanup_socket(temp_socket_path)
    assert not temp_socket_path.exists()


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_cleanup_socket_handles_nonexistent(temp_socket_path):
    """Test that cleanup_socket handles non-existent sockets gracefully."""
    # Should not raise even if socket doesn't exist
    cleanup_socket(temp_socket_path)
    assert not temp_socket_path.exists()


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_create_socket_server(temp_socket_path):
    """Test creating a socket server."""
    sock = create_socket_server(temp_socket_path)

    try:
        # Socket file should exist
        assert temp_socket_path.exists()

        # Should be listening
        assert sock.fileno() != -1

        # Check permissions (owner read/write only)
        stat_info = temp_socket_path.stat()
        perms = oct(stat_info.st_mode)[-3:]
        assert perms == "600"

    finally:
        sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_create_socket_server_cleans_up_existing(temp_socket_path):
    """Test that creating a server cleans up existing socket."""
    # Create a dummy socket file
    temp_socket_path.touch()

    sock = create_socket_server(temp_socket_path)

    try:
        # Should have replaced the dummy file with a real socket
        assert temp_socket_path.exists()
    finally:
        sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_send_and_receive_message(temp_socket_path):
    """Test sending and receiving messages over socket."""
    test_message = {"type": "test", "data": "hello world", "count": 42}

    # Start server in background thread
    server_sock = create_socket_server(temp_socket_path)
    received_message = {}

    def server_thread():
        conn, _ = server_sock.accept()
        try:
            received_message.update(receive_message(conn, timeout=5.0))
        finally:
            conn.close()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

    # Give server time to start
    time.sleep(0.1)

    try:
        # Connect and send message
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(str(temp_socket_path))

        send_message(client_sock, test_message)
        client_sock.close()

        # Wait for server to receive
        thread.join(timeout=2.0)

        # Verify message was received correctly
        assert received_message == test_message

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_domain_socket_client_connect(temp_socket_path):
    """Test DomainSocketClient connection."""
    # Start server
    server_sock = create_socket_server(temp_socket_path)

    try:
        client = DomainSocketClient(temp_socket_path)
        client.connect(timeout=2.0)

        assert client.sock is not None

        client.close()
        assert client.sock is None

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_domain_socket_client_send_receive(temp_socket_path):
    """Test DomainSocketClient send and receive."""
    request = {"action": "get_credentials", "domain": "example.com"}
    response = {"status": "success", "credentials": []}

    # Start server that echoes back a response
    server_sock = create_socket_server(temp_socket_path)

    def server_thread():
        conn, _ = server_sock.accept()
        try:
            # Receive request
            received = receive_message(conn, timeout=5.0)
            # Send response
            send_message(conn, response)
        finally:
            conn.close()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

    time.sleep(0.1)

    try:
        # Connect and communicate
        client = DomainSocketClient(temp_socket_path)
        client.connect(timeout=2.0)

        client.send(request)
        received_response = client.receive(timeout=5.0)

        assert received_response == response

        client.close()
        thread.join(timeout=2.0)

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_domain_socket_client_context_manager(temp_socket_path):
    """Test DomainSocketClient as context manager."""
    server_sock = create_socket_server(temp_socket_path)

    try:
        with DomainSocketClient(temp_socket_path) as client:
            client.connect(timeout=2.0)
            assert client.sock is not None

        # Should be closed after context exit
        assert client.sock is None

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_domain_socket_client_not_connected_error():
    """Test that operations fail when not connected."""
    client = DomainSocketClient()

    with pytest.raises(RuntimeError, match="Not connected"):
        client.send({"test": "message"})

    with pytest.raises(RuntimeError, match="Not connected"):
        client.receive()


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_domain_socket_client_nonexistent_socket():
    """Test connecting to non-existent socket fails."""
    client = DomainSocketClient(Path("/tmp/nonexistent.sock"))

    with pytest.raises(OSError, match="Socket does not exist"):
        client.connect()


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_receive_message_large_message(temp_socket_path):
    """Test receiving large messages."""
    # Create a large message (1MB)
    large_data = "x" * (1024 * 1024)
    test_message = {"type": "large", "data": large_data}

    server_sock = create_socket_server(temp_socket_path)
    received_message = {}

    def server_thread():
        conn, _ = server_sock.accept()
        try:
            received_message.update(receive_message(conn, timeout=10.0))
        finally:
            conn.close()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

    time.sleep(0.1)

    try:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(str(temp_socket_path))

        send_message(client_sock, test_message)
        client_sock.close()

        thread.join(timeout=5.0)

        assert received_message == test_message

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_receive_message_too_large_rejected(temp_socket_path):
    """Test that excessively large messages are rejected."""
    server_sock = create_socket_server(temp_socket_path)

    def server_thread():
        conn, _ = server_sock.accept()
        try:
            # Try to receive - should fail due to size limit
            with pytest.raises(ValueError, match="Message too large"):
                receive_message(conn, timeout=5.0)
        finally:
            conn.close()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

    time.sleep(0.1)

    try:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(str(temp_socket_path))

        # Send a length prefix claiming 20MB message
        fake_length = (20 * 1024 * 1024).to_bytes(4, byteorder="big")
        client_sock.sendall(fake_length)

        thread.join(timeout=2.0)

        client_sock.close()

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


def test_get_socket_info():
    """Test getting socket information."""
    info = get_socket_info()

    assert "available" in info
    assert "socket_path" in info
    assert "exists" in info

    if os.name == "nt":
        assert not info["available"]
        assert info["socket_path"] is None
    else:
        assert info["available"]
        assert info["socket_path"] is not None


@pytest.mark.skipif(os.name == "nt", reason="Unix domain sockets not supported on Windows")
def test_get_socket_info_with_existing_socket(temp_socket_path, monkeypatch):
    """Test socket info for an existing socket."""
    # Mock get_socket_path to return our test path
    monkeypatch.setattr(
        "secure_password_manager.utils.domain_socket.get_socket_path",
        lambda: temp_socket_path
    )

    # Create socket
    server_sock = create_socket_server(temp_socket_path)

    try:
        info = get_socket_info()

        assert info["available"]
        assert info["exists"]
        assert info["permissions"] == "600"
        assert "owner_uid" in info

    finally:
        server_sock.close()
        cleanup_socket(temp_socket_path)


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix domain sockets not supported")
def test_socket_path_uses_xdg_runtime_dir(tmp_path, monkeypatch):
    """Test that XDG_RUNTIME_DIR is preferred for socket location."""
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime_dir))

    socket_path = get_socket_path()

    assert str(runtime_dir) in str(socket_path)
    assert socket_path.parent.name == "secure-password-manager"
    assert socket_path.name == "bridge.sock"
