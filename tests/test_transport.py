"""Tests for paracle_transport package.

Unit tests for SSH transport, tunnel manager, and remote configuration.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from paracle_transport import RemoteConfig, SSHTransport, TunnelManager
from paracle_transport.remote_config import RemotesConfig, TunnelConfig


class TestRemoteConfig:
    """Test RemoteConfig model."""

    def test_create_remote_config(self):
        """Test creating a remote configuration."""
        config = RemoteConfig(
            name="test",
            host="user@example.com",
            workspace="/opt/paracle",
        )

        assert config.name == "test"
        assert config.host == "user@example.com"
        assert config.workspace == "/opt/paracle"
        assert config.port == 22
        assert config.type == "ssh"

    def test_username_property(self):
        """Test username extraction from host."""
        config = RemoteConfig(
            name="test",
            host="myuser@server.com",
            workspace="/opt/paracle",
        )

        assert config.username == "myuser"

    def test_hostname_property(self):
        """Test hostname extraction from host."""
        config = RemoteConfig(
            name="test",
            host="user@prod-server.com",
            workspace="/opt/paracle",
        )

        assert config.hostname == "prod-server.com"

    def test_invalid_host_format(self):
        """Test validation of host format."""
        with pytest.raises(ValueError, match="Host must be in format"):
            RemoteConfig(
                name="test",
                host="invalid-host",  # Missing user@
                workspace="/opt/paracle",
            )

    def test_tunnel_config(self):
        """Test tunnel configuration."""
        tunnel = TunnelConfig(
            local=8000,
            remote=8000,
            description="API server",
        )

        assert tunnel.local == 8000
        assert tunnel.remote == 8000
        assert tunnel.description == "API server"

    def test_tunnel_port_validation(self):
        """Test port number validation."""
        with pytest.raises(ValueError, match="Port must be between"):
            TunnelConfig(local=99999, remote=8000)

        with pytest.raises(ValueError, match="Port must be between"):
            TunnelConfig(local=8000, remote=0)


class TestRemotesConfig:
    """Test RemotesConfig model."""

    def test_empty_config(self):
        """Test empty remotes config."""
        config = RemotesConfig()

        assert config.remotes == {}
        assert config.default is None

    def test_add_remote(self):
        """Test adding remote to config."""
        config = RemotesConfig()

        remote = RemoteConfig(
            name="prod",
            host="user@prod.com",
            workspace="/opt/paracle",
        )

        config.remotes["prod"] = remote
        config.default = "prod"

        assert "prod" in config.remotes
        assert config.default == "prod"

    def test_get_remote(self):
        """Test retrieving remote by name."""
        config = RemotesConfig()
        remote = RemoteConfig(
            name="test",
            host="user@test.com",
            workspace="/opt/paracle",
        )
        config.remotes["test"] = remote

        retrieved = config.get_remote("test")
        assert retrieved.name == "test"

    def test_get_nonexistent_remote(self):
        """Test error when getting nonexistent remote."""
        config = RemotesConfig()

        with pytest.raises(KeyError, match="Remote 'missing' not found"):
            config.get_remote("missing")

    def test_get_default(self):
        """Test getting default remote."""
        config = RemotesConfig()
        remote = RemoteConfig(
            name="prod",
            host="user@prod.com",
            workspace="/opt/paracle",
        )
        config.remotes["prod"] = remote
        config.default = "prod"

        default = config.get_default()
        assert default is not None
        assert default.name == "prod"

    def test_get_default_when_none(self):
        """Test getting default when none set."""
        config = RemotesConfig()

        assert config.get_default() is None


class TestSSHTransport:
    """Test SSHTransport class."""

    @pytest.fixture
    def mock_connection(self):
        """Mock asyncssh connection."""
        conn = AsyncMock()
        conn.run = AsyncMock()
        conn.close = Mock()
        conn.wait_closed = AsyncMock()
        return conn

    @pytest.fixture
    def remote_config(self):
        """Sample remote configuration."""
        return RemoteConfig(
            name="test",
            host="user@test.com",
            workspace="/opt/paracle",
            tunnels=[
                TunnelConfig(local=8000, remote=8000),
            ],
        )

    @pytest.mark.asyncio
    async def test_connect(self, remote_config, mock_connection):
        """Test SSH connection."""
        transport = SSHTransport(remote_config)

        with patch("paracle_transport.ssh.asyncssh.connect") as mock_connect:
            mock_connect.return_value = mock_connection

            # Mock workspace verification
            verify_result = Mock()
            verify_result.exit_status = 0
            verify_result.stdout = "exists"
            mock_connection.run.return_value = verify_result

            # Mock tunnel creation
            mock_listener = Mock()
            mock_connection.forward_local_port = AsyncMock(
                return_value=mock_listener
            )

            await transport.connect()

            assert transport.connection == mock_connection
            assert len(transport.tunnels) == 1
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, remote_config, mock_connection):
        """Test SSH disconnection."""
        transport = SSHTransport(remote_config)
        transport.connection = mock_connection

        # Mock tunnel
        mock_tunnel = Mock()
        mock_tunnel.stop = AsyncMock()
        transport.tunnels[8000] = mock_tunnel

        await transport.disconnect()

        mock_tunnel.stop.assert_called_once()
        mock_connection.close.assert_called_once()
        assert transport.connection is None

    @pytest.mark.asyncio
    async def test_execute_command(self, remote_config, mock_connection):
        """Test command execution."""
        transport = SSHTransport(remote_config)
        transport.connection = mock_connection

        # Mock command result
        result = Mock()
        result.stdout = "output"
        result.stderr = ""
        result.exit_status = 0
        mock_connection.run.return_value = result

        response = await transport.execute("paracle --version")

        assert response["stdout"] == "output"
        assert response["stderr"] == ""
        assert response["exit_code"] == 0
        mock_connection.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected(self, remote_config, mock_connection):
        """Test connection status check."""
        transport = SSHTransport(remote_config)

        # Not connected
        assert not await transport.is_connected()

        # Connected
        transport.connection = mock_connection
        result = Mock()
        result.exit_status = 0
        mock_connection.run.return_value = result

        assert await transport.is_connected()


class TestTunnelManager:
    """Test TunnelManager class."""

    @pytest.fixture
    def remote_config(self):
        """Sample remote configuration."""
        return RemoteConfig(
            name="test",
            host="user@test.com",
            workspace="/opt/paracle",
            tunnels=[TunnelConfig(local=8000, remote=8000)],
        )

    @pytest.mark.asyncio
    async def test_start_manager(self, remote_config):
        """Test starting tunnel manager."""
        manager = TunnelManager(remote_config, health_check_interval=1)

        with patch.object(manager.transport, "connect", new_callable=AsyncMock):
            await manager.start()

            assert manager._running is True
            assert manager._monitor_task is not None

            await manager.stop()

    @pytest.mark.asyncio
    async def test_stop_manager(self, remote_config):
        """Test stopping tunnel manager."""
        manager = TunnelManager(remote_config)

        with patch.object(manager.transport, "connect", new_callable=AsyncMock):
            with patch.object(
                manager.transport, "disconnect", new_callable=AsyncMock
            ):
                await manager.start()
                await manager.stop()

                assert manager._running is False
                assert manager._monitor_task is None

    @pytest.mark.asyncio
    async def test_execute_via_manager(self, remote_config):
        """Test command execution via manager."""
        manager = TunnelManager(remote_config)

        with patch.object(
            manager.transport,
            "execute",
            new_callable=AsyncMock,
            return_value={"stdout": "test", "exit_code": 0},
        ):
            result = await manager.execute("paracle --version")

            assert result["stdout"] == "test"
            assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_context_manager(self, remote_config):
        """Test using manager as context manager."""
        manager = TunnelManager(remote_config)

        with patch.object(manager.transport, "connect", new_callable=AsyncMock):
            with patch.object(
                manager.transport, "disconnect", new_callable=AsyncMock
            ):
                async with manager:
                    assert manager._running is True

                # After exit
                assert manager._running is False
