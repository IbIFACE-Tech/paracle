"""Policy loader for YAML-based policy definitions.

This module provides functionality to load policies from YAML files,
supporting both single-file and directory-based policy configurations.
"""

from pathlib import Path
from typing import Any

import yaml

from .exceptions import InvalidPolicyConfigError
from .policies import Policy, PolicyAction, PolicyCondition, PolicyType


class PolicyLoader:
    """Loads governance policies from YAML files.

    Supports:
    - Single YAML file with multiple policies
    - Directory with multiple YAML files
    - Policy inheritance and composition
    - Environment variable substitution

    Example YAML format:
        ```yaml
        policies:
          - id: deny_system_files
            name: Deny System File Access
            type: deny
            actions:
              - delete_file
              - write_file
            conditions:
              - field: context.path
                operator: matches
                value: "^/etc/.*"
            priority: 900
            enabled: true
            iso_control: "8.2"
            risk_level: critical
        ```
    """

    def __init__(self, base_path: Path | str | None = None):
        """Initialize the policy loader.

        Args:
            base_path: Base path for resolving relative policy file paths.
        """
        self._base_path = Path(base_path) if base_path else Path.cwd()

    def load_file(self, path: Path | str) -> list[Policy]:
        """Load policies from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            List of loaded policies.

        Raises:
            InvalidPolicyConfigError: If the file is invalid or cannot be parsed.
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self._base_path / file_path

        if not file_path.exists():
            raise InvalidPolicyConfigError(
                f"Policy file not found: {file_path}",
            )

        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise InvalidPolicyConfigError(
                f"Invalid YAML in policy file: {e}",
            ) from e

        if not data:
            return []

        return self._parse_policies(data)

    def load_directory(self, path: Path | str) -> list[Policy]:
        """Load policies from all YAML files in a directory.

        Args:
            path: Path to the directory.

        Returns:
            List of loaded policies from all files.

        Raises:
            InvalidPolicyConfigError: If the directory doesn't exist.
        """
        dir_path = Path(path)
        if not dir_path.is_absolute():
            dir_path = self._base_path / dir_path

        if not dir_path.exists() or not dir_path.is_dir():
            raise InvalidPolicyConfigError(
                f"Policy directory not found: {dir_path}",
            )

        policies = []
        for yaml_file in sorted(dir_path.glob("*.yaml")):
            policies.extend(self.load_file(yaml_file))
        for yaml_file in sorted(dir_path.glob("*.yml")):
            policies.extend(self.load_file(yaml_file))

        return policies

    def load_string(self, yaml_string: str) -> list[Policy]:
        """Load policies from a YAML string.

        Args:
            yaml_string: YAML content as a string.

        Returns:
            List of loaded policies.

        Raises:
            InvalidPolicyConfigError: If the YAML is invalid.
        """
        try:
            data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise InvalidPolicyConfigError(
                f"Invalid YAML: {e}",
            ) from e

        if not data:
            return []

        return self._parse_policies(data)

    def _parse_policies(self, data: dict[str, Any]) -> list[Policy]:
        """Parse policies from loaded YAML data.

        Args:
            data: Parsed YAML data.

        Returns:
            List of Policy objects.

        Raises:
            InvalidPolicyConfigError: If the policy data is invalid.
        """
        policies = []

        # Support both 'policies' list and direct policy dict
        if "policies" in data:
            policy_list = data["policies"]
        elif "id" in data:
            # Single policy at root
            policy_list = [data]
        else:
            policy_list = []

        for policy_data in policy_list:
            try:
                policy = self._parse_single_policy(policy_data)
                policies.append(policy)
            except Exception as e:
                policy_id = policy_data.get("id", "unknown")
                raise InvalidPolicyConfigError(
                    f"Error parsing policy: {e}",
                    policy_id=policy_id,
                ) from e

        return policies

    def _parse_single_policy(self, data: dict[str, Any]) -> Policy:
        """Parse a single policy from data.

        Args:
            data: Policy data dictionary.

        Returns:
            Policy object.
        """
        # Parse actions
        actions = []
        for action in data.get("actions", []):
            if isinstance(action, str):
                # Try to convert to PolicyAction enum
                try:
                    actions.append(PolicyAction(action))
                except ValueError:
                    # Keep as string for custom actions
                    actions.append(action)
            else:
                actions.append(action)

        # Parse conditions
        conditions = []
        for cond in data.get("conditions", []):
            conditions.append(
                PolicyCondition(
                    field=cond["field"],
                    operator=cond.get("operator", "eq"),
                    value=cond["value"],
                )
            )

        # Parse policy type
        policy_type = PolicyType(data["type"])

        return Policy(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            type=policy_type,
            actions=actions,
            conditions=conditions,
            priority=data.get("priority", 100),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
            iso_control=data.get("iso_control"),
            risk_level=data.get("risk_level"),
            approval_required_by=data.get("approval_required_by", []),
        )

    def save_policies(
        self,
        policies: list[Policy],
        path: Path | str,
    ) -> None:
        """Save policies to a YAML file.

        Args:
            policies: List of policies to save.
            path: Path to the output file.
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self._base_path / file_path

        # Convert policies to serializable format
        data = {"policies": [self._policy_to_dict(policy) for policy in policies]}

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def _policy_to_dict(self, policy: Policy) -> dict[str, Any]:
        """Convert a policy to a serializable dictionary.

        Args:
            policy: Policy to convert.

        Returns:
            Dictionary representation of the policy.
        """
        data: dict[str, Any] = {
            "id": policy.id,
            "name": policy.name,
            "type": policy.type.value,
            "actions": [
                a.value if isinstance(a, PolicyAction) else a for a in policy.actions
            ],
            "priority": policy.priority,
            "enabled": policy.enabled,
        }

        if policy.description:
            data["description"] = policy.description

        if policy.conditions:
            data["conditions"] = [
                {
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                }
                for c in policy.conditions
            ]

        if policy.metadata:
            data["metadata"] = policy.metadata

        if policy.iso_control:
            data["iso_control"] = policy.iso_control

        if policy.risk_level:
            data["risk_level"] = policy.risk_level

        if policy.approval_required_by:
            data["approval_required_by"] = policy.approval_required_by

        return data


# Default policy file template
DEFAULT_POLICY_TEMPLATE = """# Paracle Governance Policies
# ISO 42001 Compliance Configuration

policies:
  # High-priority security policies
  - id: deny_system_files
    name: Deny System File Modification
    description: Prevent agents from modifying critical system files
    type: deny
    actions:
      - write_file
      - delete_file
    conditions:
      - field: context.path
        operator: matches
        value: "^/(etc|usr|bin|sbin|var/log).*"
    priority: 900
    enabled: true
    iso_control: "8.2"
    risk_level: critical

  # Approval workflows
  - id: approve_external_api
    name: Require Approval for External APIs
    description: Human approval required before calling external APIs
    type: require_approval
    actions:
      - external_api
      - http_request
    conditions:
      - field: context.is_external
        operator: eq
        value: true
    priority: 800
    enabled: true
    iso_control: "6.2"
    risk_level: high
    approval_required_by:
      - admin
      - security

  # Audit policies
  - id: audit_file_writes
    name: Audit All File Writes
    description: Log all file write operations for compliance
    type: audit
    actions:
      - write_file
    priority: 100
    enabled: true
    iso_control: "9.1"
    risk_level: medium

  - id: audit_command_execution
    name: Audit Command Execution
    description: Log all shell command executions
    type: audit
    actions:
      - execute_command
    priority: 100
    enabled: true
    iso_control: "9.1"
    risk_level: medium
"""
