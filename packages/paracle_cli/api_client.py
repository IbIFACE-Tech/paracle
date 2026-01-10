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
            except (ValueError, KeyError, AttributeError):
                # JSON decode error or missing 'detail' key
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
        import logging

        logger = logging.getLogger("paracle.cli.api")

        try:
            self.health()
            return True
        except (
            APIError,
            ConnectionError,
            TimeoutError,
            httpx.ConnectError,
            OSError,
        ) as e:
            # Expected errors when API is unavailable
            # OSError includes WinError 10061 (connection refused)
            logger.debug(f"API not available: {type(e).__name__}: {e}")

            # Log to error registry if available (but don't fail if not)
            try:
                from paracle_observability import ErrorSeverityLevel, get_error_registry

                registry = get_error_registry()
                registry.record_error(
                    error=e,
                    component="api_health_check",
                    severity=ErrorSeverityLevel.DEBUG,
                    context={
                        "api_url": self.base_url,
                        "error_type": type(e).__name__,
                    },
                    include_traceback=False,
                )
            except ImportError:
                # Observability not available, continue
                pass
            except Exception as reg_error:
                # Don't fail on error registry issues
                logger.debug(f"Error registry unavailable: {reg_error}")

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
            url = f"{self.base_url}/api/workflows/" f"executions/{execution_id}/cancel"
            response = client.post(
                url,
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

    def workflow_plan(
        self,
        workflow_id: str,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate execution plan for a workflow.

        Args:
            workflow_id: Workflow identifier
            inputs: Optional workflow inputs for better estimation

        Returns:
            ExecutionPlan as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/workflows/{workflow_id}/plan",
                headers=self._get_headers(),
                json={"inputs": inputs or {}},
            )
            return self._handle_response(response)

    # =========================================================================
    # Approval Endpoints (Human-in-the-Loop)
    # =========================================================================

    def approvals_list_pending(
        self,
        workflow_id: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        """List pending approval requests.

        Args:
            workflow_id: Optional filter by workflow ID
            priority: Optional filter by priority (low, medium, high, critical)

        Returns:
            ApprovalListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params = {}
            if workflow_id:
                params["workflow_id"] = workflow_id
            if priority:
                params["priority"] = priority
            response = client.get(
                f"{self.base_url}/approvals/pending",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    def approvals_list_decided(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List decided approval requests.

        Args:
            workflow_id: Optional filter by workflow ID
            status: Optional filter by status
                (approved, rejected, expired, cancelled)
            limit: Maximum number of results

        Returns:
            ApprovalListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params: dict[str, Any] = {"limit": limit}
            if workflow_id:
                params["workflow_id"] = workflow_id
            if status:
                params["approval_status"] = status
            response = client.get(
                f"{self.base_url}/approvals/decided",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    def approvals_get(self, approval_id: str) -> dict[str, Any]:
        """Get approval request by ID.

        Args:
            approval_id: Approval request identifier

        Returns:
            ApprovalRequestResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/approvals/{approval_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def approvals_approve(
        self,
        approval_id: str,
        approver: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Approve a pending request.

        Args:
            approval_id: Approval request identifier
            approver: ID/email of the approver
            reason: Optional reason for approval

        Returns:
            ApprovalRequestResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/approvals/{approval_id}/approve",
                headers=self._get_headers(),
                json={"approver": approver, "reason": reason},
            )
            return self._handle_response(response)

    def approvals_reject(
        self,
        approval_id: str,
        approver: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Reject a pending request.

        Args:
            approval_id: Approval request identifier
            approver: ID/email of the approver
            reason: Optional reason for rejection

        Returns:
            ApprovalRequestResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/approvals/{approval_id}/reject",
                headers=self._get_headers(),
                json={"approver": approver, "reason": reason},
            )
            return self._handle_response(response)

    def approvals_cancel(self, approval_id: str) -> dict[str, Any]:
        """Cancel a pending request.

        Args:
            approval_id: Approval request identifier

        Returns:
            ApprovalRequestResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/approvals/{approval_id}/cancel",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def approvals_stats(self) -> dict[str, Any]:
        """Get approval statistics.

        Returns:
            ApprovalStatsResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/approvals/stats",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Review Endpoints (Artifact Reviews)
    # =========================================================================

    def reviews_list(
        self,
        status: str | None = None,
        sandbox_id: str | None = None,
    ) -> dict[str, Any]:
        """List artifact reviews.

        Args:
            status: Optional filter by status
                (pending, approved, rejected, timeout)
            sandbox_id: Optional filter by sandbox ID

        Returns:
            ReviewListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params = {}
            if status:
                params["status_filter"] = status
            if sandbox_id:
                params["sandbox_id"] = sandbox_id
            response = client.get(
                f"{self.base_url}/reviews/",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    def reviews_get(self, review_id: str) -> dict[str, Any]:
        """Get review by ID.

        Args:
            review_id: Review identifier

        Returns:
            ReviewResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/reviews/{review_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def reviews_approve(
        self,
        review_id: str,
        reviewer: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Approve an artifact review.

        Args:
            review_id: Review identifier
            reviewer: Reviewer ID/email
            comment: Optional comment

        Returns:
            ReviewResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/reviews/{review_id}/approve",
                headers=self._get_headers(),
                json={"reviewer": reviewer, "comment": comment},
            )
            return self._handle_response(response)

    def reviews_reject(
        self,
        review_id: str,
        reviewer: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Reject an artifact review.

        Args:
            review_id: Review identifier
            reviewer: Reviewer ID/email
            comment: Optional comment

        Returns:
            ReviewResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/reviews/{review_id}/reject",
                headers=self._get_headers(),
                json={"reviewer": reviewer, "comment": comment},
            )
            return self._handle_response(response)

    def reviews_cancel(self, review_id: str) -> None:
        """Cancel a pending review.

        Args:
            review_id: Review identifier
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(
                f"{self.base_url}/reviews/{review_id}",
                headers=self._get_headers(),
            )
            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                raise APIError(response.status_code, detail)

    def reviews_stats(self) -> dict[str, Any]:
        """Get review statistics.

        Returns:
            ReviewStatsResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/reviews/stats/summary",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Kanban Board Endpoints
    # =========================================================================

    def boards_list(self, include_archived: bool = False) -> dict[str, Any]:
        """List all boards.

        Args:
            include_archived: Include archived boards

        Returns:
            BoardListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/boards",
                headers=self._get_headers(),
                params={"include_archived": include_archived},
            )
            return self._handle_response(response)

    def boards_create(
        self,
        name: str,
        description: str = "",
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new board.

        Args:
            name: Board name
            description: Board description
            columns: Custom columns (default: TODO, IN_PROGRESS, REVIEW, DONE)

        Returns:
            BoardResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            payload = {"name": name, "description": description}
            if columns:
                payload["columns"] = columns
            response = client.post(
                f"{self.base_url}/api/boards",
                headers=self._get_headers(),
                json=payload,
            )
            return self._handle_response(response)

    def boards_get(self, board_id: str) -> dict[str, Any]:
        """Get board by ID.

        Args:
            board_id: Board identifier

        Returns:
            BoardResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/boards/{board_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def boards_stats(self, board_id: str) -> dict[str, Any]:
        """Get board statistics.

        Args:
            board_id: Board identifier

        Returns:
            BoardStatsResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/boards/{board_id}/stats",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def boards_update(
        self,
        board_id: str,
        name: str | None = None,
        description: str | None = None,
        columns: list[str] | None = None,
        archived: bool | None = None,
    ) -> dict[str, Any]:
        """Update a board.

        Args:
            board_id: Board identifier
            name: New name
            description: New description
            columns: New columns
            archived: Archive status

        Returns:
            BoardResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            payload = {}
            if name is not None:
                payload["name"] = name
            if description is not None:
                payload["description"] = description
            if columns is not None:
                payload["columns"] = columns
            if archived is not None:
                payload["archived"] = archived
            response = client.put(
                f"{self.base_url}/api/boards/{board_id}",
                headers=self._get_headers(),
                json=payload,
            )
            return self._handle_response(response)

    def boards_delete(self, board_id: str) -> dict[str, Any]:
        """Delete a board.

        Args:
            board_id: Board identifier

        Returns:
            BoardDeleteResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(
                f"{self.base_url}/api/boards/{board_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Kanban Task Endpoints
    # =========================================================================

    def tasks_list(
        self,
        board_id: str | None = None,
        status: str | None = None,
        assigned_to: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        """List tasks with optional filters.

        Args:
            board_id: Filter by board ID
            status: Filter by status
            assigned_to: Filter by assignee
            priority: Filter by priority

        Returns:
            TaskListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params = {}
            if board_id:
                params["board_id"] = board_id
            if status:
                params["status"] = status
            if assigned_to:
                params["assigned_to"] = assigned_to
            if priority:
                params["priority"] = priority
            response = client.get(
                f"{self.base_url}/api/tasks",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    def tasks_create(
        self,
        board_id: str,
        title: str,
        description: str = "",
        priority: str = "MEDIUM",
        task_type: str = "FEATURE",
        assigned_to: str | None = None,
        tags: list[str] | None = None,
        depends_on: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new task.

        Args:
            board_id: Board identifier
            title: Task title
            description: Task description
            priority: Task priority
            task_type: Task type
            assigned_to: Assignee agent ID
            tags: Task tags
            depends_on: Dependency task IDs

        Returns:
            TaskResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            payload = {
                "board_id": board_id,
                "title": title,
                "description": description,
                "priority": priority,
                "task_type": task_type,
            }
            if assigned_to:
                payload["assigned_to"] = assigned_to
            if tags:
                payload["tags"] = tags
            if depends_on:
                payload["depends_on"] = depends_on
            response = client.post(
                f"{self.base_url}/api/tasks",
                headers=self._get_headers(),
                json=payload,
            )
            return self._handle_response(response)

    def tasks_get(self, task_id: str) -> dict[str, Any]:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/tasks/{task_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def tasks_update(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        task_type: str | None = None,
        tags: list[str] | None = None,
        depends_on: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a task.

        Args:
            task_id: Task identifier
            title: New title
            description: New description
            priority: New priority
            task_type: New type
            tags: New tags
            depends_on: New dependencies

        Returns:
            TaskResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            payload = {}
            if title is not None:
                payload["title"] = title
            if description is not None:
                payload["description"] = description
            if priority is not None:
                payload["priority"] = priority
            if task_type is not None:
                payload["task_type"] = task_type
            if tags is not None:
                payload["tags"] = tags
            if depends_on is not None:
                payload["depends_on"] = depends_on
            response = client.put(
                f"{self.base_url}/api/tasks/{task_id}",
                headers=self._get_headers(),
                json=payload,
            )
            return self._handle_response(response)

    def tasks_move(
        self,
        task_id: str,
        status: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Move task to a different status.

        Args:
            task_id: Task identifier
            status: Target status
            reason: Reason (required for BLOCKED)

        Returns:
            TaskResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            payload = {"status": status}
            if reason:
                payload["reason"] = reason
            response = client.put(
                f"{self.base_url}/api/tasks/{task_id}/move",
                headers=self._get_headers(),
                json=payload,
            )
            return self._handle_response(response)

    def tasks_assign(self, task_id: str, agent_id: str) -> dict[str, Any]:
        """Assign task to an agent.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier

        Returns:
            TaskResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.put(
                f"{self.base_url}/api/tasks/{task_id}/assign",
                headers=self._get_headers(),
                json={"agent_id": agent_id},
            )
            return self._handle_response(response)

    def tasks_unassign(self, task_id: str) -> dict[str, Any]:
        """Unassign task.

        Args:
            task_id: Task identifier

        Returns:
            TaskResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.put(
                f"{self.base_url}/api/tasks/{task_id}/unassign",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def tasks_delete(self, task_id: str) -> dict[str, Any]:
        """Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            TaskDeleteResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(
                f"{self.base_url}/api/tasks/{task_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Observability - Metrics Endpoints
    # =========================================================================

    def metrics_list(self) -> dict[str, Any]:
        """List all registered metrics.

        Returns:
            MetricsListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/metrics",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def metrics_export(self, format: str = "prometheus") -> dict[str, Any]:
        """Export metrics.

        Args:
            format: Export format (prometheus, json)

        Returns:
            MetricsExportResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/metrics/export",
                headers=self._get_headers(),
                params={"format": format},
            )
            return self._handle_response(response)

    def metrics_reset(self) -> dict[str, Any]:
        """Reset all metrics.

        Returns:
            Confirmation message
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/metrics/reset",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Observability - Tracing Endpoints
    # =========================================================================

    def traces_list(self, limit: int = 20) -> dict[str, Any]:
        """List completed traces.

        Args:
            limit: Maximum traces to return

        Returns:
            TraceListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/traces",
                headers=self._get_headers(),
                params={"limit": limit},
            )
            return self._handle_response(response)

    def traces_get(self, trace_id: str) -> dict[str, Any]:
        """Get trace details.

        Args:
            trace_id: Trace identifier

        Returns:
            TraceListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/traces/{trace_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def traces_export(self) -> dict[str, Any]:
        """Export traces in Jaeger format.

        Returns:
            TraceExportResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/traces/export",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def traces_clear(self) -> dict[str, Any]:
        """Clear all traces.

        Returns:
            Confirmation message
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/traces/clear",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # =========================================================================
    # Observability - Alert Endpoints
    # =========================================================================

    def alerts_list(
        self,
        severity: str | None = None,
        active_only: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List alerts.

        Args:
            severity: Filter by severity
            active_only: Show only active alerts
            limit: Maximum alerts to return

        Returns:
            AlertListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            params = {"active_only": active_only, "limit": limit}
            if severity:
                params["severity"] = severity
            response = client.get(
                f"{self.base_url}/api/alerts",
                headers=self._get_headers(),
                params=params,
            )
            return self._handle_response(response)

    def alerts_rules(self) -> dict[str, Any]:
        """List alert rules.

        Returns:
            AlertRuleListResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/alerts/rules",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def alerts_evaluate(self) -> dict[str, Any]:
        """Evaluate alert rules.

        Returns:
            AlertEvaluateResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/alerts/evaluate",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    def alerts_silence(self, fingerprint: str, duration: int = 3600) -> dict[str, Any]:
        """Silence an alert.

        Args:
            fingerprint: Alert fingerprint
            duration: Silence duration in seconds

        Returns:
            AlertSilenceResponse as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/alerts/{fingerprint}/silence",
                headers=self._get_headers(),
                json={"duration": duration},
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

    ALL errors are managed through the error registry for tracking,
    analysis, and reporting.

    Args:
        api_func: Function to call via API (receives client as first arg)
        fallback_func: Function to call directly if API unavailable
        *args, **kwargs: Arguments to pass to both functions

    Returns:
        Result from either function

    Raises:
        Exception: Re-raises after logging to error registry
    """
    import logging

    from rich.console import Console

    console = Console()
    logger = logging.getLogger("paracle.cli.api")

    # Get error registry if available
    error_registry = None
    try:
        from paracle_observability import get_error_registry

        error_registry = get_error_registry()
    except ImportError:
        # Observability not available, continue without error tracking
        pass

    client = get_client()

    # Try API first
    if client.is_available():
        try:
            return api_func(client, *args, **kwargs)
        except APIError as e:
            # Log to error registry
            if error_registry:
                error_registry.record_error(
                    error=e,
                    component="api_client",
                    context={
                        "status_code": e.status_code,
                        "detail": e.detail,
                        "function": api_func.__name__,
                        "fallback_available": True,
                    },
                )

            if e.status_code == 404:
                # .parac/ not found - let fallback handle gracefully
                logger.debug(f"API returned 404, falling back: {e.detail}")
            else:
                console.print(f"[yellow]API error:[/yellow] {e.detail}")
                console.print("[dim]Falling back to direct access...[/dim]")
                logger.warning(f"API error, falling back: {e.detail}")
        except Exception as e:
            # Log to error registry
            if error_registry:
                error_registry.record_error(
                    error=e,
                    component="api_connection",
                    context={
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "function": api_func.__name__,
                        "fallback_available": True,
                    },
                )

            console.print(f"[yellow]API unavailable:[/yellow] {e}")
            console.print("[dim]Falling back to direct access...[/dim]")
            logger.debug(f"API connection failed, falling back: {e}")

    # Try fallback
    try:
        return fallback_func(*args, **kwargs)
    except Exception as e:
        # Log to error registry with CRITICAL severity (no fallback available)
        if error_registry:
            from paracle_observability import ErrorSeverityLevel

            error_registry.record_error(
                error=e,
                component="fallback_execution",
                severity=ErrorSeverityLevel.CRITICAL,
                context={
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "function": fallback_func.__name__,
                    "api_attempted": client.is_available(),
                    "fallback_failed": True,
                },
            )

        # Log and re-raise
        logger.error(f"Fallback execution failed: {e}")
        raise
