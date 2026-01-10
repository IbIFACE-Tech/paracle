"""File locking mechanism for concurrent access control.

Provides file-level locks to prevent conflicts when multiple
agents access the same files simultaneously.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel


class FileLock(BaseModel):
    """Represents a lock on a file.

    Attributes:
        file_path: Path to locked file
        agent_id: ID of agent holding lock
        acquired_at: When lock was acquired
        expires_at: When lock expires
        operation: Operation being performed (read/write)
    """

    file_path: str
    agent_id: str
    acquired_at: datetime
    expires_at: datetime
    operation: str = "write"  # read or write


class LockManager:
    """Manages file locks for concurrent access control.

    Provides file-level locking to prevent conflicts when
    multiple agents modify the same files.
    """

    def __init__(self, lock_dir: Path | None = None):
        """Initialize lock manager.

        Args:
            lock_dir: Directory to store lock files
        """
        if lock_dir is None:
            lock_dir = Path(".parac") / "memory" / "data" / "locks"

        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock_path(self, file_path: str) -> Path:
        """Get path to lock file.

        Args:
            file_path: Path to file to lock

        Returns:
            Path to lock file
        """
        # Use hash of file path as lock file name
        import hashlib

        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.lock_dir / f"{file_hash}.lock"

    def acquire_lock(
        self,
        file_path: str,
        agent_id: str,
        timeout: int = 300,
        operation: str = "write",
    ) -> bool:
        """Acquire a lock on a file.

        Args:
            file_path: Path to file to lock
            agent_id: ID of agent requesting lock
            timeout: Lock timeout in seconds
            operation: Operation type (read/write)

        Returns:
            True if lock acquired
        """
        lock_path = self._get_lock_path(file_path)

        # Check if lock exists and is valid
        if lock_path.exists():
            try:
                with open(lock_path) as f:
                    lock_data = json.load(f)
                    lock = FileLock(**lock_data)

                # Check if lock has expired
                # expires_at is already datetime from Pydantic parsing
                expires_at = (
                    lock.expires_at
                    if isinstance(lock.expires_at, datetime)
                    else datetime.fromisoformat(str(lock.expires_at))
                )
                if expires_at > datetime.utcnow():
                    # Lock still valid
                    if lock.agent_id == agent_id:
                        # Same agent, extend lock
                        lock.expires_at = datetime.utcnow() + timedelta(seconds=timeout)
                        with open(lock_path, "w") as f:
                            json.dump(lock.model_dump(mode="json"), f, default=str)
                        return True
                    else:
                        # Different agent holds lock
                        return False
            except Exception:
                # Invalid lock file, proceed to acquire
                pass

        # Create new lock
        lock = FileLock(
            file_path=file_path,
            agent_id=agent_id,
            acquired_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=timeout),
            operation=operation,
        )

        try:
            with open(lock_path, "w") as f:
                json.dump(lock.model_dump(mode="json"), f, default=str)
            return True
        except Exception as e:
            print(f"Error acquiring lock: {e}")
            return False

    def release_lock(self, file_path: str, agent_id: str) -> bool:
        """Release a lock on a file.

        Args:
            file_path: Path to file
            agent_id: ID of agent holding lock

        Returns:
            True if lock released
        """
        lock_path = self._get_lock_path(file_path)

        if not lock_path.exists():
            return True  # No lock to release

        try:
            with open(lock_path) as f:
                lock_data = json.load(f)
                lock = FileLock(**lock_data)

            # Verify agent owns lock
            if lock.agent_id != agent_id:
                return False

            # Remove lock file
            lock_path.unlink()
            return True
        except Exception as e:
            print(f"Error releasing lock: {e}")
            return False

    def get_lock(self, file_path: str) -> FileLock | None:
        """Get current lock on a file.

        Args:
            file_path: Path to file

        Returns:
            FileLock if file is locked, None otherwise
        """
        lock_path = self._get_lock_path(file_path)

        if not lock_path.exists():
            return None

        try:
            with open(lock_path) as f:
                lock_data = json.load(f)
                lock = FileLock(**lock_data)

            # Check if expired
            # expires_at is already datetime from Pydantic parsing
            expires_at = (
                lock.expires_at
                if isinstance(lock.expires_at, datetime)
                else datetime.fromisoformat(str(lock.expires_at))
            )
            if expires_at <= datetime.utcnow():
                # Expired, remove lock
                lock_path.unlink()
                return None

            return lock
        except Exception:
            return None

    def is_locked(self, file_path: str) -> bool:
        """Check if a file is currently locked.

        Args:
            file_path: Path to file

        Returns:
            True if file is locked
        """
        return self.get_lock(file_path) is not None

    def wait_for_lock(
        self,
        file_path: str,
        agent_id: str,
        timeout: int = 60,
        poll_interval: float = 0.5,
    ) -> bool:
        """Wait for a lock to become available.

        Args:
            file_path: Path to file
            agent_id: ID of agent requesting lock
            timeout: Maximum wait time in seconds
            poll_interval: Time between lock attempts

        Returns:
            True if lock acquired
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.acquire_lock(file_path, agent_id):
                return True
            time.sleep(poll_interval)

        return False

    def clear_expired_locks(self) -> int:
        """Clear all expired locks.

        Returns:
            Number of locks cleared
        """
        cleared = 0

        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                with open(lock_file) as f:
                    lock_data = json.load(f)
                    lock = FileLock(**lock_data)

                # expires_at is already datetime from Pydantic parsing
                expires_at = (
                    lock.expires_at
                    if isinstance(lock.expires_at, datetime)
                    else datetime.fromisoformat(str(lock.expires_at))
                )
                if expires_at <= datetime.utcnow():
                    lock_file.unlink()
                    cleared += 1
            except Exception:
                # Invalid lock file, remove it
                lock_file.unlink()
                cleared += 1

        return cleared
