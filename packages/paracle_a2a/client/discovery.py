"""Agent Discovery.

Discovers A2A agents via Agent Cards.
"""

import time

import httpx

from paracle_a2a.config import A2AClientConfig
from paracle_a2a.exceptions import A2AError, AgentNotFoundError
from paracle_a2a.models import AgentCard


class AgentDiscovery:
    """Discovers A2A agents via Agent Cards.

    Fetches and caches Agent Cards from remote A2A servers.
    """

    def __init__(self, config: A2AClientConfig | None = None):
        """Initialize agent discovery.

        Args:
            config: Client configuration
        """
        self.config = config or A2AClientConfig()

        # Card cache: url -> (card, timestamp)
        self._cache: dict[str, tuple[AgentCard, float]] = {}

    async def discover(
        self,
        url: str,
        *,
        force_refresh: bool = False,
    ) -> AgentCard:
        """Discover agent at URL.

        Fetches the Agent Card from the standard .well-known location.

        Args:
            url: Agent base URL or full .well-known URL
            force_refresh: Force cache refresh

        Returns:
            AgentCard for the agent

        Raises:
            AgentNotFoundError: If agent not found
            A2AError: If discovery fails
        """
        # Check cache
        if not force_refresh and self.config.cache_agent_cards:
            cached = self._get_cached(url)
            if cached:
                return cached

        # Build well-known URL
        if not url.endswith("/.well-known/agent.json"):
            well_known_url = f"{url.rstrip('/')}/.well-known/agent.json"
        else:
            well_known_url = url

        # Fetch card
        try:
            async with httpx.AsyncClient(
                timeout=self.config.connect_timeout_seconds,
                verify=self.config.verify_ssl,
                headers={
                    "User-Agent": self.config.user_agent,
                    **self.config.get_auth_headers(),
                },
            ) as client:
                response = await client.get(well_known_url)

                if response.status_code == 404:
                    raise AgentNotFoundError(url)

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AgentNotFoundError(url) from e
            raise A2AError(f"HTTP error: {e}") from e
        except httpx.RequestError as e:
            raise A2AError(f"Request failed: {e}") from e

        # Parse card
        try:
            card = AgentCard(**data)
        except Exception as e:
            raise A2AError(f"Invalid Agent Card: {e}") from e

        # Cache
        if self.config.cache_agent_cards:
            self._cache[url] = (card, time.time())

        return card

    async def discover_agents(
        self,
        server_url: str,
        *,
        force_refresh: bool = False,
    ) -> list[AgentCard]:
        """Discover all agents at a server.

        Fetches the root Agent Card and then individual agent cards.

        Args:
            server_url: Server base URL
            force_refresh: Force cache refresh

        Returns:
            List of AgentCards
        """
        # Get root card first
        root_card = await self.discover(server_url, force_refresh=force_refresh)

        cards = []

        # If root card has skills that are agents, fetch their cards
        for skill in root_card.skills:
            if "agent" in skill.tags:
                try:
                    agent_url = f"{server_url.rstrip('/')}/agents/{skill.id}"
                    card = await self.discover(agent_url, force_refresh=force_refresh)
                    cards.append(card)
                except Exception:
                    # Skip individual failures
                    pass

        # If no agent skills, return root card
        if not cards:
            cards = [root_card]

        return cards

    def _get_cached(self, url: str) -> AgentCard | None:
        """Get cached Agent Card if valid.

        Args:
            url: Agent URL

        Returns:
            Cached AgentCard or None
        """
        if url not in self._cache:
            return None

        card, timestamp = self._cache[url]
        age = time.time() - timestamp

        if age > self.config.card_cache_ttl_seconds:
            del self._cache[url]
            return None

        return card

    def clear_cache(self) -> None:
        """Clear the Agent Card cache."""
        self._cache.clear()

    def get_cached_urls(self) -> list[str]:
        """Get list of cached Agent Card URLs.

        Returns:
            List of cached URLs
        """
        return list(self._cache.keys())


async def discover_agent(
    url: str,
    config: A2AClientConfig | None = None,
) -> AgentCard:
    """Convenience function to discover an agent.

    Args:
        url: Agent URL
        config: Optional client config

    Returns:
        AgentCard
    """
    discovery = AgentDiscovery(config)
    return await discovery.discover(url)
