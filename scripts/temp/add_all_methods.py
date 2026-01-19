code = """
    async def assign_task(self, task_name: str, agent_name: str) -> CapabilityResult:
        task = next((t for t in self._tasks.values() if t.name == task_name), None)
        if not task:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Task {task_name!r} not found', duration_ms=0, metadata={})
        agent = next((a for a in self._agents.values() if a['name'] == agent_name), None)
        if not agent:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Agent {agent_name!r} not found', duration_ms=0, metadata={})
        return await self._assign_task(task.id, agent['id'])

    async def complete_task(self, task_name: str, result: dict[str, Any]) -> CapabilityResult:
        task = next((t for t in self._tasks.values() if t.name == task_name), None)
        if not task:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Task {task_name!r} not found', duration_ms=0, metadata={})
        return await self._complete_task(task.id, result)

    async def get_task_status(self, task_name: str) -> CapabilityResult:
        task = next((t for t in self._tasks.values() if t.name == task_name), None)
        if not task:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Task {task_name!r} not found', duration_ms=0, metadata={})
        return await self._get_task_status(task.id)

    async def get_agent_workload(self, agent_name: str) -> CapabilityResult:
        agent = next((a for a in self._agents.values() if a['name'] == agent_name), None)
        if not agent:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Agent {agent_name!r} not found', duration_ms=0, metadata={})
        return await self._get_agent_workload(agent['id'])

    async def broadcast(self, message: str | dict[str, Any], sender: str | None = None) -> CapabilityResult:
        start = time.time()
        duration_ms = (time.time() - start) * 1000
        return CapabilityResult(capability='hive_mind', success=True, output={'message': message, 'sender': sender or 'system', 'recipient_count': len(self._agents)}, error=None, duration_ms=duration_ms, metadata={'action': 'broadcast'})

    async def send_message(self, to_agent: str, message: str | dict[str, Any], sender: str | None = None) -> CapabilityResult:
        start = time.time()
        to_obj = next((a for a in self._agents.values() if a['name'] == to_agent), None)
        if not to_obj:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Agent {to_agent!r} not found', duration_ms=0, metadata={})
        duration_ms = (time.time() - start) * 1000
        return CapabilityResult(capability='hive_mind', success=True, output={'message': message, 'sender': sender or 'system', 'recipient': to_agent}, error=None, duration_ms=duration_ms, metadata={'action': 'send_message'})

    async def list_tasks(self, status: str | None = None) -> CapabilityResult:
        if status:
            return await self._list_tasks_by_status(status)
        return await self._list_tasks()

    async def unregister_agent(self, agent_name: str) -> CapabilityResult:
        agent = next((a for a in self._agents.values() if a['name'] == agent_name), None)
        if not agent:
            return CapabilityResult(capability='hive_mind', success=False, output={}, error=f'Agent {agent_name!r} not found', duration_ms=0, metadata={})
        return await self._unregister_agent(agent['id'])
"""

with open('packages/paracle_meta/capabilities/hive_mind.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('Added all methods')
