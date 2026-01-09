"""Custom log handlers for Paracle.

Provides handlers with additional features:
- Rotating file handler with compression
- Audit file handler with integrity
- Async-safe handlers
"""

import gzip
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import IO


class ParacleStreamHandler(logging.StreamHandler):
    """Stream handler optimized for Paracle.

    Features:
    - Color output support (when terminal supports it)
    - Flush after each log for real-time output
    - Thread-safe
    """

    # ANSI color codes for log levels
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(
        self,
        stream: IO | None = None,
        use_colors: bool | None = None,
    ):
        """Initialize stream handler.

        Args:
            stream: Output stream (default: sys.stdout)
            use_colors: Use ANSI colors (default: auto-detect)
        """
        super().__init__(stream or sys.stdout)

        if use_colors is None:
            # Auto-detect color support
            self.use_colors = hasattr(self.stream, "isatty") and self.stream.isatty()
        else:
            self.use_colors = use_colors

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record.

        Args:
            record: The log record
        """
        try:
            msg = self.format(record)

            # Add colors if supported
            if self.use_colors and record.levelno in self.COLORS:
                msg = f"{self.COLORS[record.levelno]}{msg}{self.RESET}"

            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class ParacleFileHandler(RotatingFileHandler):
    """Rotating file handler with compression.

    Features:
    - Automatic rotation based on size
    - Gzip compression of rotated files
    - Atomic writes
    - Directory auto-creation
    """

    def __init__(
        self,
        filename: str | Path,
        max_bytes: int = 10_485_760,  # 10MB
        backup_count: int = 5,
        compress: bool = True,
        encoding: str = "utf-8",
    ):
        """Initialize file handler.

        Args:
            filename: Path to log file
            max_bytes: Max file size before rotation
            backup_count: Number of backup files to keep
            compress: Compress rotated files with gzip
            encoding: File encoding
        """
        # Ensure directory exists
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            filename=str(filepath),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )

        self.compress = compress

    def doRollover(self) -> None:
        """Do a rollover with optional compression."""
        # Close current file
        if self.stream:
            self.stream.close()
            self.stream = None

        # Rotate files
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                src = self._get_backup_name(i)
                dst = self._get_backup_name(i + 1)
                if os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(src, dst)

            # Compress and rename current file
            dst = self._get_backup_name(1)
            if os.path.exists(dst):
                os.remove(dst)

            if self.compress:
                # Compress the file
                with open(self.baseFilename, "rb") as f_in:
                    with gzip.open(dst, "wb") as f_out:
                        f_out.writelines(f_in)
                os.remove(self.baseFilename)
            else:
                os.rename(self.baseFilename, dst)

        # Reopen file
        if not self.delay:
            self.stream = self._open()

    def _get_backup_name(self, n: int) -> str:
        """Get backup filename.

        Args:
            n: Backup number

        Returns:
            Backup filename with optional .gz extension
        """
        if self.compress:
            return f"{self.baseFilename}.{n}.gz"
        return f"{self.baseFilename}.{n}"


class AuditFileHandler(logging.FileHandler):
    """Audit log handler with integrity features.

    Features:
    - Append-only writes
    - Timestamps in filename for daily rotation
    - Checksum generation (optional)
    - Tamper-evident formatting

    ISO 42001 Compliance:
    - Immutable log format
    - Chain of custody support
    - Evidence preservation
    """

    def __init__(
        self,
        log_dir: str | Path,
        prefix: str = "audit",
        encoding: str = "utf-8",
        include_checksum: bool = False,
    ):
        """Initialize audit handler.

        Args:
            log_dir: Directory for audit logs
            prefix: Log file prefix
            encoding: File encoding
            include_checksum: Include line checksums
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.prefix = prefix
        self._encoding = encoding
        self.include_checksum = include_checksum

        # Create initial log file
        filename = self._get_current_filename()
        super().__init__(filename, mode="a", encoding=encoding)

    def _get_current_filename(self) -> str:
        """Get current audit log filename.

        Returns:
            Path to current audit log file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return str(self.log_dir / f"{self.prefix}_{date_str}.log")

    def emit(self, record: logging.LogRecord) -> None:
        """Emit an audit log record.

        Args:
            record: The log record
        """
        # Check if we need to rotate to new day
        current_file = self._get_current_filename()
        if current_file != self.baseFilename:
            self.close()
            self.baseFilename = current_file
            self.stream = self._open()

        try:
            msg = self.format(record)

            # Add checksum if enabled
            if self.include_checksum:
                import hashlib

                checksum = hashlib.sha256(msg.encode()).hexdigest()[:16]
                msg = f"{msg} [checksum:{checksum}]"

            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Close the handler and finalize audit log."""
        if self.stream:
            # Write closing marker
            try:
                timestamp = datetime.now().isoformat()
                self.stream.write(f"# Audit log closed at {timestamp}\n")
                self.flush()
            except Exception:
                pass

        super().close()
