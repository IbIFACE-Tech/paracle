"""Tests for platform-specific logging paths."""

import os
from pathlib import Path
from unittest.mock import patch

from paracle_core.logging.platform import (
    PlatformPaths,
    detect_platform,
    ensure_directories,
    get_docker_paths,
    get_info,
    get_linux_paths,
    get_log_path,
    get_macos_paths,
    get_platform_paths,
    get_windows_paths,
)


class TestPlatformDetection:
    """Test platform detection logic."""

    def test_detect_docker_via_dockerenv(self, tmp_path):
        """Test Docker detection via /.dockerenv."""
        dockerenv = Path("/.dockerenv")
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda p: p == "/.dockerenv"
            assert detect_platform() == "docker"

    def test_detect_docker_via_containerenv(self):
        """Test Docker detection via /run/.containerenv."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda p: p == "/run/.containerenv"
            assert detect_platform() == "docker"

    def test_detect_docker_via_kubernetes(self):
        """Test Docker detection via Kubernetes env var."""
        with patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}):
            with patch("os.path.exists", return_value=False):
                assert detect_platform() == "docker"

    def test_detect_windows(self):
        """Test Windows detection."""
        with patch("sys.platform", "win32"):
            with patch("os.path.exists", return_value=False):
                with patch.dict(os.environ, {}, clear=True):
                    assert detect_platform() == "windows"

    def test_detect_macos(self):
        """Test macOS detection."""
        with patch("sys.platform", "darwin"):
            with patch("os.path.exists", return_value=False):
                with patch.dict(os.environ, {}, clear=True):
                    assert detect_platform() == "macos"

    def test_detect_linux(self):
        """Test Linux detection."""
        with patch("sys.platform", "linux"):
            with patch("os.path.exists", return_value=False):
                with patch.dict(os.environ, {}, clear=True):
                    assert detect_platform() == "linux"


class TestWindowsPaths:
    """Test Windows path generation."""

    def test_windows_paths_with_localappdata(self):
        """Test Windows paths using LOCALAPPDATA."""
        with patch.dict(
            os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}
        ):
            paths = get_windows_paths()

            assert paths.log_dir == Path(
                "C:\\Users\\test\\AppData\\Local\\Paracle\\logs"
            )
            assert paths.cache_dir == Path(
                "C:\\Users\\test\\AppData\\Local\\Paracle\\cache"
            )
            assert paths.data_dir == Path(
                "C:\\Users\\test\\AppData\\Local\\Paracle\\data"
            )
            assert paths.config_dir == Path(
                "C:\\Users\\test\\AppData\\Local\\Paracle\\config"
            )

    def test_windows_paths_fallback_to_home(self):
        """Test Windows paths fallback when LOCALAPPDATA not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.home", return_value=Path("C:\\Users\\test")):
                paths = get_windows_paths()

                assert paths.log_dir == Path(
                    "C:\\Users\\test\\AppData\\Local\\Paracle\\logs"
                )


class TestLinuxPaths:
    """Test Linux path generation."""

    def test_linux_paths_with_xdg_vars(self):
        """Test Linux paths using XDG environment variables."""
        with patch.dict(
            os.environ,
            {
                "XDG_DATA_HOME": "/custom/data",
                "XDG_CACHE_HOME": "/custom/cache",
                "XDG_CONFIG_HOME": "/custom/config",
            },
        ):
            paths = get_linux_paths()

            assert paths.log_dir == Path("/custom/data/paracle/logs")
            assert paths.cache_dir == Path("/custom/cache/paracle")
            assert paths.data_dir == Path("/custom/data/paracle")
            assert paths.config_dir == Path("/custom/config/paracle")

    def test_linux_paths_default_xdg(self):
        """Test Linux paths with default XDG locations."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                paths = get_linux_paths()

                assert paths.log_dir == Path("/home/test/.local/share/paracle/logs")
                assert paths.cache_dir == Path("/home/test/.cache/paracle")
                assert paths.data_dir == Path("/home/test/.local/share/paracle")
                assert paths.config_dir == Path("/home/test/.config/paracle")


class TestMacOSPaths:
    """Test macOS path generation."""

    def test_macos_paths(self):
        """Test macOS paths using Application Support."""
        with patch("pathlib.Path.home", return_value=Path("/Users/test")):
            paths = get_macos_paths()

            assert paths.log_dir == Path(
                "/Users/test/Library/Application Support/Paracle/logs"
            )
            assert paths.cache_dir == Path("/Users/test/Library/Caches/Paracle")
            assert paths.data_dir == Path(
                "/Users/test/Library/Application Support/Paracle"
            )
            assert paths.config_dir == Path(
                "/Users/test/Library/Application Support/Paracle/config"
            )


class TestDockerPaths:
    """Test Docker/container path generation."""

    def test_docker_paths_var_log_exists(self):
        """Test Docker paths when /var/log/paracle exists."""
        with patch("pathlib.Path.exists", return_value=True):
            paths = get_docker_paths()

            assert paths.log_dir == Path("/var/log/paracle/logs")
            assert paths.cache_dir == Path("/var/log/paracle/cache")

    def test_docker_paths_fallback_to_tmp(self):
        """Test Docker paths fallback to /tmp."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch(
                "paracle_core.logging.platform._is_writable_parent", return_value=False
            ):
                paths = get_docker_paths()

                assert paths.log_dir == Path("/tmp/paracle/logs")
                assert paths.cache_dir == Path("/tmp/paracle/cache")

    def test_docker_paths_var_log_writable_parent(self):
        """Test Docker paths when /var/log is writable."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch(
                "paracle_core.logging.platform._is_writable_parent", return_value=True
            ):
                paths = get_docker_paths()

                assert paths.log_dir == Path("/var/log/paracle/logs")


class TestPlatformPaths:
    """Test platform path resolution."""

    def test_get_platform_paths_windows(self):
        """Test get_platform_paths on Windows."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="windows"
        ):
            with patch.dict(
                os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}
            ):
                paths = get_platform_paths()

                assert "Paracle" in str(paths.log_dir)
                assert "logs" in str(paths.log_dir)

    def test_get_platform_paths_linux(self):
        """Test get_platform_paths on Linux."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="linux"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                paths = get_platform_paths()

                assert paths.log_dir == Path("/home/test/.local/share/paracle/logs")

    def test_get_platform_paths_macos(self):
        """Test get_platform_paths on macOS."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="macos"
        ):
            with patch("pathlib.Path.home", return_value=Path("/Users/test")):
                paths = get_platform_paths()

                assert paths.log_dir == Path(
                    "/Users/test/Library/Application Support/Paracle/logs"
                )

    def test_get_platform_paths_docker(self):
        """Test get_platform_paths in Docker."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="docker"
        ):
            with patch("pathlib.Path.exists", return_value=False):
                with patch(
                    "paracle_core.logging.platform._is_writable_parent",
                    return_value=False,
                ):
                    paths = get_platform_paths()

                    assert paths.log_dir == Path("/tmp/paracle/logs")


class TestLogPaths:
    """Test log file path generation."""

    def test_get_log_path_main(self):
        """Test main log path."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="linux"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                log_path = get_log_path("main")

                assert log_path.name == "paracle.log"
                assert log_path.parent == Path("/home/test/.local/share/paracle/logs")

    def test_get_log_path_cli(self):
        """Test CLI log path."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="linux"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                log_path = get_log_path("cli")

                assert log_path.name == "paracle-cli.log"

    def test_get_log_path_agent(self):
        """Test agent log path."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="linux"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                log_path = get_log_path("agent")

                assert log_path.name == "paracle-agent.log"

    def test_get_log_path_errors(self):
        """Test errors log path."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="linux"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                log_path = get_log_path("errors")

                assert log_path.name == "paracle-errors.log"

    def test_get_log_path_audit(self):
        """Test audit log path."""
        with patch(
            "paracle_core.logging.platform.detect_platform", return_value="linux"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                log_path = get_log_path("audit")

                assert log_path.name == "paracle-audit.log"

    def test_get_log_path_creates_directory(self, tmp_path):
        """Test that get_log_path creates directory if needed."""
        with patch("paracle_core.logging.platform.get_platform_paths") as mock_paths:
            mock_paths.return_value = PlatformPaths(
                log_dir=tmp_path / "logs",
                cache_dir=tmp_path / "cache",
                data_dir=tmp_path / "data",
                config_dir=tmp_path / "config",
            )

            log_path = get_log_path("main")

            assert log_path.parent.exists()
            assert log_path.parent == tmp_path / "logs"


class TestDirectoryEnsurance:
    """Test directory creation."""

    def test_ensure_directories_creates_all(self, tmp_path):
        """Test that ensure_directories creates all needed directories."""
        with patch("paracle_core.logging.platform.get_platform_paths") as mock_paths:
            mock_paths.return_value = PlatformPaths(
                log_dir=tmp_path / "logs",
                cache_dir=tmp_path / "cache",
                data_dir=tmp_path / "data",
                config_dir=tmp_path / "config",
            )

            paths = ensure_directories()

            assert paths.log_dir.exists()
            assert paths.cache_dir.exists()
            assert paths.data_dir.exists()
            assert paths.config_dir.exists()

    def test_ensure_directories_idempotent(self, tmp_path):
        """Test that ensure_directories is idempotent."""
        with patch("paracle_core.logging.platform.get_platform_paths") as mock_paths:
            mock_paths.return_value = PlatformPaths(
                log_dir=tmp_path / "logs",
                cache_dir=tmp_path / "cache",
                data_dir=tmp_path / "data",
                config_dir=tmp_path / "config",
            )

            paths1 = ensure_directories()
            paths2 = ensure_directories()

            assert paths1.log_dir == paths2.log_dir
            assert paths1.log_dir.exists()


class TestInfo:
    """Test platform info generation."""

    def test_get_info_returns_all_fields(self):
        """Test that get_info returns all expected fields."""
        info = get_info()

        expected_keys = {
            "platform",
            "log_dir",
            "cache_dir",
            "data_dir",
            "config_dir",
            "main_log",
            "cli_log",
            "agent_log",
            "errors_log",
            "audit_log",
        }

        assert set(info.keys()) == expected_keys

    def test_get_info_platform_matches_detect(self):
        """Test that get_info platform matches detect_platform."""
        info = get_info()
        detected = detect_platform()

        assert info["platform"] == detected

    def test_get_info_all_paths_strings(self):
        """Test that all paths in info are strings."""
        info = get_info()

        for key, value in info.items():
            assert isinstance(value, str), f"{key} should be string, got {type(value)}"
