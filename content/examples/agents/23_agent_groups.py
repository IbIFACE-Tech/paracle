#!/usr/bin/env python3
"""Example: Agent Groups - Multi-Agent Collaboration.

This example demonstrates how to use Agent Groups for multi-agent
collaboration in Paracle. It shows:
1. Creating agent groups with different communication patterns
2. Running collaboration sessions
3. Processing results and consensus
4. Persisting sessions to SQLite

See docs/agent-groups-guide.md for full documentation.
"""

import asyncio
from datetime import datetime
from typing import Any

from paracle_agent_comm.engine import GroupCollaborationEngine
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupConfig,
    GroupMessage,
    GroupSession,
    GroupSessionStatus,
    MessageType,
)
from paracle_agent_comm.patterns import (
    BroadcastPattern,
    CoordinatorPattern,
    PeerToPeerPattern,
)
from paracle_agent_comm.persistence import InMemorySessionStore, SQLiteSessionStore


# =============================================================================
# Example 1: Understanding Communication Patterns
# =============================================================================


def example_patterns():
    """Demonstrate different communication patterns."""
    print("\n=== Communication Patterns ===\n")

    # Create a group
    members = ["architect", "coder", "tester"]

    # Peer-to-Peer Pattern
    p2p_group = AgentGroup(
        name="P2P Team",
        members=members,
        communication_pattern=CommunicationPattern.PEER_TO_PEER,
    )
    p2p = PeerToPeerPattern(p2p_group)

    print("Peer-to-Peer Pattern:")
    print(f"  - architect can message coder: {p2p.can_send_to('architect', 'coder')}")
    print(f"  - coder can message tester: {p2p.can_send_to('coder', 'tester')}")

    # Broadcast Pattern
    bc_group = AgentGroup(
        name="Broadcast Team",
        members=members,
        communication_pattern=CommunicationPattern.BROADCAST,
    )
    bc = BroadcastPattern(bc_group)

    msg = GroupMessage.create(
        group_id=bc_group.id,
        sender="architect",
        text="New design proposal",
        message_type=MessageType.PROPOSE,
    )
    recipients = bc.route_message(msg)
    print(f"\nBroadcast Pattern:")
    print(f"  - Message from architect goes to: {recipients}")

    # Coordinator Pattern
    coord_group = AgentGroup(
        name="Coordinated Team",
        members=members,
        coordinator="architect",
        communication_pattern=CommunicationPattern.COORDINATOR,
    )
    coord = CoordinatorPattern(coord_group)

    print(f"\nCoordinator Pattern (coordinator=architect):")
    print(f"  - architect can message coder: {coord.can_send_to('architect', 'coder')}")
    print(f"  - coder can message architect: {coord.can_send_to('coder', 'architect')}")
    print(f"  - coder can message tester: {coord.can_send_to('coder', 'tester')}")


# =============================================================================
# Example 2: Creating and Managing Groups
# =============================================================================


async def example_group_management():
    """Demonstrate group CRUD operations."""
    print("\n=== Group Management ===\n")

    # Create an in-memory store (use SQLiteSessionStore for persistence)
    store = InMemorySessionStore()

    # Create groups
    review_team = AgentGroup(
        name="Code Review Team",
        description="Team for code quality and review",
        members=["senior-dev", "junior-dev", "security-expert"],
        max_rounds=5,
        max_messages=50,
    )

    design_team = AgentGroup(
        name="Design Team",
        description="Architecture and design decisions",
        members=["architect", "ux-designer", "tech-lead"],
        coordinator="tech-lead",
        communication_pattern=CommunicationPattern.COORDINATOR,
    )

    # Save groups
    await store.save_group(review_team)
    await store.save_group(design_team)
    print(f"Created groups: {review_team.name}, {design_team.name}")

    # List all groups
    groups = await store.list_groups()
    print(f"\nAll groups ({len(groups)}):")
    for g in groups:
        print(f"  - {g.name}: {len(g.members)} members, pattern={g.communication_pattern.value}")

    # Get specific group
    retrieved = await store.get_group(review_team.id)
    print(f"\nRetrieved group: {retrieved.name}")
    print(f"  Members: {retrieved.members}")


# =============================================================================
# Example 3: Running a Collaboration Session
# =============================================================================


class MockAgent:
    """Simple mock agent for demonstration."""

    def __init__(self, agent_id: str, behavior: str = "cooperative"):
        self._id = agent_id
        self.behavior = behavior

    @property
    def id(self) -> str:
        return self._id

    async def respond_to_group(
        self,
        session: GroupSession,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a response based on context."""
        goal = context.get("goal", "")
        round_num = context.get("round", 1)

        # Simple response logic
        if round_num == 1:
            return {
                "message": f"[{self._id}] I understand the goal: {goal[:50]}...",
                "type": "inform",
            }
        elif round_num == 2:
            if "architect" in self._id:
                return {
                    "message": f"[{self._id}] I propose we use a modular approach",
                    "type": "propose",
                }
            else:
                return {
                    "message": f"[{self._id}] Waiting for architecture proposal",
                    "type": "inform",
                }
        else:
            # Accept proposals in later rounds
            proposals = session.get_messages_by_type(MessageType.PROPOSE)
            if proposals:
                return {
                    "message": f"[{self._id}] I accept the proposed approach",
                    "type": "accept",
                }
            return {
                "message": f"[{self._id}] Continuing work...",
                "type": "inform",
            }


class MockRegistry:
    """Simple mock agent registry."""

    def __init__(self, agents: list[MockAgent]):
        self._agents = {a.id: a for a in agents}

    async def get(self, agent_id: str) -> MockAgent:
        return self._agents[agent_id]


async def example_collaboration():
    """Run a collaboration session."""
    print("\n=== Collaboration Session ===\n")

    # Create agents
    agents = [
        MockAgent("architect"),
        MockAgent("coder"),
        MockAgent("reviewer"),
    ]
    registry = MockRegistry(agents)

    # Create group
    group = AgentGroup(
        name="Feature Team",
        members=["architect", "coder", "reviewer"],
        max_rounds=3,
    )

    # Create engine
    engine = GroupCollaborationEngine(
        group=group,
        agent_registry=registry,
    )

    # Run collaboration
    print("Starting collaboration...")
    session = await engine.collaborate(
        goal="Design and implement user authentication feature",
        initial_context={
            "requirements": ["OAuth 2.0", "JWT tokens", "Rate limiting"],
            "deadline": "End of sprint",
        },
    )

    # Print results
    print(f"\nSession completed!")
    print(f"  Status: {session.status.value}")
    print(f"  Rounds: {session.round_count}")
    print(f"  Messages: {len(session.messages)}")
    print(f"  Outcome: {session.outcome}")

    print("\nMessage history:")
    for msg in session.messages:
        content = msg.get_text_content()[:60]
        print(f"  [{msg.message_type.value:8}] {msg.sender:12}: {content}...")


# =============================================================================
# Example 4: Working with Sessions
# =============================================================================


async def example_session_operations():
    """Demonstrate session operations."""
    print("\n=== Session Operations ===\n")

    # Create a session
    session = GroupSession(
        group_id="group-123",
        goal="Implement caching layer",
        shared_context={
            "tech_stack": ["Redis", "Python"],
            "requirements": ["<100ms latency"],
        },
    )

    # Add messages
    session.add_message(
        GroupMessage.create(
            group_id=session.group_id,
            sender="architect",
            text="I propose using Redis for distributed caching",
            message_type=MessageType.PROPOSE,
        )
    )

    session.add_message(
        GroupMessage.create(
            group_id=session.group_id,
            sender="coder",
            text="Good idea. What about cache invalidation?",
            message_type=MessageType.QUERY,
        )
    )

    session.add_message(
        GroupMessage.create(
            group_id=session.group_id,
            sender="architect",
            text="We'll use TTL with event-based invalidation",
            message_type=MessageType.INFORM,
        )
    )

    session.add_message(
        GroupMessage.create(
            group_id=session.group_id,
            sender="coder",
            text="I accept this approach",
            message_type=MessageType.ACCEPT,
        )
    )

    # Query session
    print(f"Session goal: {session.goal}")
    print(f"Total messages: {len(session.messages)}")
    print(f"Has consensus: {session.has_consensus()}")

    # Filter messages
    proposals = session.get_messages_by_type(MessageType.PROPOSE)
    print(f"\nProposals ({len(proposals)}):")
    for p in proposals:
        print(f"  - {p.sender}: {p.get_text_content()}")

    # Get messages by sender
    arch_msgs = session.get_messages_by_sender("architect")
    print(f"\nArchitect messages: {len(arch_msgs)}")

    # Get recent messages
    recent = session.get_recent_messages(2)
    print(f"\nLast 2 messages:")
    for m in recent:
        print(f"  - {m.sender}: {m.get_text_content()[:40]}...")


# =============================================================================
# Example 5: Persistence with SQLite
# =============================================================================


async def example_persistence():
    """Demonstrate SQLite persistence."""
    print("\n=== SQLite Persistence ===\n")

    import tempfile
    import os

    # Create temp database file (not in context manager to avoid Windows file lock)
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "sessions.db")

    try:
        store = SQLiteSessionStore(db_path)

        # Create and save a group
        group = AgentGroup(
            name="Persistence Demo",
            members=["agent-1", "agent-2"],
        )
        await store.save_group(group)
        print(f"Saved group: {group.name}")

        # Create and save sessions
        for i in range(3):
            session = GroupSession(
                group_id=group.id,
                goal=f"Task {i + 1}",
                status=GroupSessionStatus.COMPLETED if i < 2 else GroupSessionStatus.ACTIVE,
            )
            session.add_message(
                GroupMessage.create(
                    group_id=group.id,
                    sender="agent-1",
                    text=f"Working on task {i + 1}",
                    message_type=MessageType.INFORM,
                )
            )
            await store.save_session(session)

        # Query sessions
        all_sessions = await store.list_sessions()
        print(f"\nAll sessions: {len(all_sessions)}")

        completed = await store.list_sessions(status=GroupSessionStatus.COMPLETED)
        print(f"Completed sessions: {len(completed)}")

        group_sessions = await store.list_sessions(group_id=group.id)
        print(f"Sessions for group: {len(group_sessions)}")

        # Get session count
        count = await store.get_session_count()
        print(f"\nTotal session count: {count}")

    finally:
        # Clean up (ignore errors on Windows due to file locks)
        import shutil
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass  # Ignore cleanup errors on Windows


# =============================================================================
# Main
# =============================================================================


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Agent Groups Example")
    print("=" * 60)

    # Run examples
    example_patterns()
    await example_group_management()
    await example_collaboration()
    await example_session_operations()
    await example_persistence()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
