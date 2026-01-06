"""Paracle CLI - API Client.

HTTP client for communicating with the Paracle API.
Provides a consistent interface for CLI commands to call API endpoints.

Architecture: CLI -> API -> Core (API-first design)
Falls back to direct core access if API is unavailable.
"""

from typing import Any

import httpx

# Default API base URL
DEFAULT_API_URL = "http://localhost:8000"


class APIClient:
    """HTTP client for Paracle API.

    Handles authentication, error handling, and provides
    typed methods for each API endpoint group.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        """Initialize API client.

        Args:
            base_url: API base URL (defaults to localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or DEFAULT_API_URL).rstrip("/")
        self.timeout = timeout
        self._token: str | None = None

    def set_token(self, token: str) -> None:
        """Set authentication token."""
        self._token = token

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including auth if set."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising on errors.

        Args:
            response: HTTP response

        Returns:
            Parsed JSON response

        Raises:
            APIError: On HTTP errors
        """
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise APIError(response.status_code, detail)

        return response.json()

    # =========================================================================
    # Health Endpoints
    # =========================================================================

    def health(self) -> dict[str, Any]:
        """Check API health."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/health")
            return self._handle_response(response)

    def is_available(self) -> bool:
        """Check if API is available.

        Returns:
            True if API responds to health check
        """
        try:
            self.health()
            return True
        except Exception:
            return False

    # =========================================================================
    # Parac/Governance Endpoints
    # =========================================================================

    def parac_status(self) -> dict[str, Any]:
        """Get project status from .parac/.

        Returns:
            StatusResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/parac/status",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def parac_sync(
        self,
        update_git: bool = True,
        update_metrics: bool = True,
    ) -> dict[str, Any]:
        """Synchronize .parac/ state.

        Args:
            update_git: Sync git information
            update_metrics: Sync file metrics

        Returns:
            SyncResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/parac/sync",
                headers=self._get_headers(),
                json={
                    "update_git": update_git,
                    "update_metrics": update_metrics,
                },
            )
            return self._handle_response(response)

    def parac_validate(self) -> dict[str, Any]:
        """Validate .parac/ workspace.

        Returns:
            ValidationResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/parac/validate",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def parac_session_start(self) -> dict[str, Any]:
        """Start a work session.

        Returns:
            SessionStartResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/parac/session/start",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def parac_session_end(
        self,
        progress: int | None = None,
        completed: list[str] | None = None,
        in_progress: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """End a work session.

        Args:
            progress: New progress percentage (0-100)
            completed: Items to mark as completed
            in_progress: Items to mark as in-progress
            dry_run: If true, show changes without applying

        Returns:
            SessionEndResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/parac/session/end",
                headers=self._get_headers(),
                json={
                    "progress": progress,
                    "completed": completed or [],
                    "in_progress": in_progress or [],
                    "dry_run": dry_run,
                },
            )
            return self._handle_response(response)

    # =========================================================================
    # IDE Endpoints
    # =========================================================================

    def ide_list(self) -> dict[str, Any]:
        """List supported IDEs.

        Returns:
            IDEListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/ide/list",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def ide_status(self) -> dict[str, Any]:
        """Get IDE integration status.

        Returns:
            IDEStatusResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/ide/status",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def ide_init(
        self,
        ides: list[str] | None = None,
        force: bool = False,
        copy: bool = True,
    ) -> dict[str, Any]:
        """Initialize IDE configurations.

        Args:
            ides: List of IDEs to initialize (empty = all)
            force: Overwrite existing files
            copy: Copy to project root

        Returns:
            IDEInitResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/ide/init",
                headers=self._get_headers(),
                json={
                    "ides": ides or [],
                    "force": force,
                    "copy": copy,
                },
            )
            return self._handle_response(response)

    def ide_sync(self, copy: bool = True) -> dict[str, Any]:
        """Synchronize IDE configurations.

        Args:
            copy: Copy to project root

        Returns:
            IDESyncResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/ide/sync",
                headers=self._get_headers(),
                json={"copy": copy},
            )
            return self._handle_response(response)

    def ide_generate(self, ide: str) -> dict[str, Any]:
        """Generate single IDE configuration.

        Args:
            ide: IDE to generate config for

        Returns:
            IDEGenerateResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/ide/generate",
                headers=self._get_headers(),
                json={"ide": ide},
            )
            return self._handle_response(response)

    # =========================================================================
    # Agents Endpoints
    # =========================================================================

    def agents_list(self) -> dict[str, Any]:
        """List all agents.

        Returns:
            AgentsListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/agents",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def agents_get(self, agent_id: str) -> dict[str, Any]:
        """Get agent details.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/agents/{agent_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def agents_get_spec(self, agent_id: str) -> dict[str, Any]:
        """Get agent specification.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentSpec as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/agents/{agent_id}/spec",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Logs Endpoints
    # =========================================================================

    def logs_list(self) -> dict[str, Any]:
        """List available log files.

        Returns:
            LogsListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/logs",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def logs_show(
        self,
        log_name: str = "actions",
        tail: int = 50,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """Show log contents.

        Args:
            log_name: Name of log file
            tail: Number of lines to show
            pattern: Filter pattern

        Returns:
            LogsShowResponse as dict
        """
        params: dict[str, str | int] = {"tail": tail}
        if pattern:
            params["pattern"] = pattern

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/logs/{log_name}",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    # =========================================================================
    # Workflow Endpoints
    # =========================================================================

    def workflow_list(
        self, limit: int = 100, offset: int = 0, status: str | None = None
    ) -> dict[str, Any]:
        """List workflows.

        Args:
            limit: Maximum number of workflows to return
            offset: Offset for pagination
            status: Optional status filter

        Returns:
            WorkflowListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            response = client.get(
                f"{self.base_url}/api/workflows",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    def workflow_get(self, workflow_id: str) -> dict[str, Any]:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow details as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/workflows/{workflow_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def workflow_execute(
        self,
        workflow_id: str,
        inputs: dict[str, Any] | None = None,
        async_execution: bool = True,
        auto_approve: bool = False,
    ) -> dict[str, Any]:
        """Execute a workflow.

        Args:
            workflow_id: Workflow identifier
            inputs: Workflow inputs
            async_execution: Run asynchronously (returns immediately)
            auto_approve: YOLO mode - auto-approve all approval gates

        Returns:
            WorkflowExecuteResponse as dict with execution_id
        """
        with httpx.Client(timeout=self.timeout) as client:
            payload = {
                "workflow_id": workflow_id,
                "inputs": inputs or {},
                "async_execution": async_execution,
                "auto_approve": auto_approve,
            }
            response = client.post(
                f"{self.base_url}/api/workflows/execute",
                headers=self._get_headers(),
                json=payload,
            )
            return self._handle_response(response)

    def workflow_execution_status(self, execution_id: str) -> dict[str, Any]:
        """Get workflow execution status.

        Args:
            execution_id: Execution identifier

        Returns:
            ExecutionStatusResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/workflows/executions/{execution_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def workflow_execution_cancel(self, execution_id: str) -> dict[str, Any]:
        """Cancel a running workflow execution.

        Args:
            execution_id: Execution identifier

        Returns:
            ExecutionCancelResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/workflows/executions/{execution_id}/cancel",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def workflow_executions_list(
        self,
        workflow_id: str,
        status: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List executions for a workflow.

        Args:
            workflow_id: Workflow identifier
            status: Optional status filter (running, completed, failed)
            limit: Maximum number of executions to return
            offset: Offset for pagination

        Returns:
            ExecutionListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            response = client.get(
                f"{self.base_url}/api/workflows/{workflow_id}/executions",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)


class APIError(Exception):
    """API request error."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


def get_client(base_url: str | None = None) -> APIClient:
    """Get API client instance.

    Args:
        base_url: Optional API base URL

    Returns:
        Configured APIClient instance
    """
    return APIClient(base_url=base_url)


def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    """Try API first, fall back to direct core access.

    This is a utility function for CLI commands to implement
    API-first architecture with graceful fallback.

    Args:
        api_func: Function to call via API (receives client as first arg)
        fallback_func: Function to call directly if API unavailable
        *args, **kwargs: Arguments to pass to both functions

    Returns:
        Result from either function
    """
    from rich.console import Console
    console = Console()

    client = get_client()
    if client.is_available():
        try:
            return api_func(client, *args, **kwargs)
        except APIError as e:
            if e.status_code == 404:
                # .parac/ not found - let fallback handle gracefully
                pass
            else:
                console.print(f"[yellow]API error:[/yellow] {e.detail}")
                console.print("[dim]Falling back to direct access...[/dim]")
        except Exception as e:
            console.print(f"[yellow]API unavailable:[/yellow] {e}")
            console.print("[dim]Falling back to direct access...[/dim]")

    return fallback_func(*args, **kwargs)
