methods = """

    async def assign_task(self, task_name: str, agent_name: str) -> CapabilityResult:
        """Assign task to agent by name."""
        task = next((t for t in self.tasks.values() if t.name == task_name), None)
        if not task:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Task {task_name!r} not found", duration_ms=0, metadata={})
        agent = next((a for a in self.agents.values() if a["name"] == agent_name), None)
        if not agent:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Agent {agent_name!r} not found", duration_ms=0, metadata={})
        return await self._assign_task(task.id, agent["id"])

    async def complete_task(self, task_name: str, result: dict[str, Any]) -> CapabilityResult:
        """Complete task by name."""
        task = next((t for t in self.tasks.values() if t.name == task_name), None)
        if not task:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Task {task_name!r} not found", duration_ms=0, metadata={})
        return await self._complete_task(task.id, result)

    async def get_task_status(self, task_name: str) -> CapabilityResult:
        """Get task status by name."""
        task = next((t for t in self.tasks.values() if t.name == task_name), None)
        if not task:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Task {task_name!r} not found", duration_ms=0, metadata={})
        return await self._get_task_status(task.id)

    async def get_agent_workload(self, agent_name: str) -> CapabilityResult:
        """Get agent workload by name."""
        agent = next((a for a in self.agents.values() if a["name"] == agent_name), None)
        if not agent:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Agent {agent_name!r} not found", duration_ms=0, metadata={})
        return await self._get_agent_workload(agent["id"])

    async def broadcast(self, message: dict[str, Any]) -> CapabilityResult:
        """Broadcast message to all agents."""
        return await self._broadcast_message(message)

    async def send_message(self, from_agent: str, to_agent: str, message: dict[str, Any]) -> CapabilityResult:
        """Send message from one agent to another by name."""
        from_obj = next((a for a in self.agents.values() if a["name"] == from_agent), None)
        to_obj = next((a for a in self.agents.values() if a["name"] == to_agent), None)
        if not from_obj:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Agent {from_agent!r} not found", duration_ms=0, metadata={})
        if not to_obj:
            return CapabilityResult(capability="hive_mind", success=False, output={}, error=f"Agent {to_agent!r} not found", duration_ms=0, metadata={})
        return await self._send_message(from_obj["id"], to_obj["id"], message)
"""

with open("packages/paracle_meta/capabilities/hive_mind.py", "a", encoding="utf-8") as f:
    f.write(methods)
