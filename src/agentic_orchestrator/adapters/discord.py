"""
Discord adapter for signal collection.

Collects signals from Discord servers via:
- Webhook integrations
- Public announcement channels
- Bot API (if configured)
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class DiscordAdapter(BaseAdapter):
    """
    Discord adapter for collecting announcements and updates.

    Features:
    - Webhook-based message ingestion
    - Public announcement tracking
    - Bot API integration (optional)
    """

    # Public Discord invite links for tracking (announcement channels)
    # Note: These require manual webhook setup or bot integration
    TRACKED_SERVERS: List[Dict[str, Any]] = [
        {
            "name": "Ethereum",
            "guild_id": "714888181740339261",
            "channels": ["announcements", "ecosystem-news"],
            "category": "crypto",
        },
        {
            "name": "Polygon",
            "guild_id": "635865020172861441",
            "channels": ["announcements"],
            "category": "crypto",
        },
        {
            "name": "Arbitrum",
            "guild_id": "828276976373981184",
            "channels": ["announcements"],
            "category": "crypto",
        },
        {
            "name": "Optimism",
            "guild_id": "667044843901681675",
            "channels": ["announcements"],
            "category": "crypto",
        },
        {
            "name": "Aave",
            "guild_id": "602826399994937344",
            "channels": ["announcements"],
            "category": "crypto",
        },
        {
            "name": "Uniswap",
            "guild_id": "597638925346930701",
            "channels": ["announcements"],
            "category": "crypto",
        },
        {
            "name": "OpenAI",
            "guild_id": "974519864045756446",
            "channels": ["announcements"],
            "category": "ai",
        },
    ]

    # Webhook URLs for receiving messages (configured externally)
    # Format: {"server_name": "webhook_url"}
    WEBHOOK_ENDPOINTS: Dict[str, str] = {}

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        bot_token: Optional[str] = None,
        webhook_urls: Optional[Dict[str, str]] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.bot_token = bot_token or os.getenv("DISCORD_BOT_TOKEN")
        self.webhook_urls = webhook_urls or {}

        # Load webhook URLs from environment
        for server in self.TRACKED_SERVERS:
            env_key = f"DISCORD_WEBHOOK_{server['name'].upper()}"
            if os.getenv(env_key):
                self.webhook_urls[server["name"]] = os.getenv(env_key)

        # Message cache for deduplication
        self._seen_messages: Dict[str, datetime] = {}

    @property
    def name(self) -> str:
        return "discord"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from Discord."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Method 1: Fetch via Bot API (if available)
        if self.bot_token:
            bot_signals = await self._fetch_via_bot()
            signals.extend(bot_signals)

        # Method 2: Fetch from webhook storage (if configured)
        webhook_signals = await self._fetch_from_webhooks()
        signals.extend(webhook_signals)

        # Method 3: Fetch from public APIs/scraping (limited)
        public_signals = await self._fetch_public_announcements()
        signals.extend(public_signals)

        # Clean old cache entries
        self._clean_cache()

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0 or self.bot_token is not None,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "servers_tracked": len(self.TRACKED_SERVERS),
                "has_bot_token": bool(self.bot_token),
                "webhooks_configured": len(self.webhook_urls),
            }
        )

    async def _fetch_via_bot(self) -> List[SignalData]:
        """Fetch messages using Discord Bot API."""
        signals: List[SignalData] = []

        if not self.bot_token:
            return signals

        async with httpx.AsyncClient(timeout=30) as client:
            headers = {"Authorization": f"Bot {self.bot_token}"}

            for server in self.TRACKED_SERVERS:
                guild_id = server.get("guild_id")
                if not guild_id:
                    continue

                try:
                    # Get guild channels
                    response = await client.get(
                        f"https://discord.com/api/v10/guilds/{guild_id}/channels",
                        headers=headers
                    )

                    if response.status_code != 200:
                        continue

                    channels = response.json()

                    # Find announcement channels
                    for channel in channels:
                        channel_name = channel.get("name", "").lower()
                        if not any(
                            ac in channel_name
                            for ac in server.get("channels", ["announcements"])
                        ):
                            continue

                        channel_id = channel.get("id")

                        # Fetch recent messages
                        msg_response = await client.get(
                            f"https://discord.com/api/v10/channels/{channel_id}/messages",
                            params={"limit": 10},
                            headers=headers
                        )

                        if msg_response.status_code != 200:
                            continue

                        messages = msg_response.json()

                        for msg in messages:
                            msg_id = msg.get("id")

                            # Skip if already seen
                            if msg_id in self._seen_messages:
                                continue

                            self._seen_messages[msg_id] = datetime.utcnow()

                            content = msg.get("content", "")
                            if not content or len(content) < 20:
                                continue

                            signal = SignalData(
                                source=self.name,
                                category=server.get("category", "crypto"),
                                title=f"[{server['name']}] {content[:150]}",
                                summary=content[:500] if len(content) > 150 else None,
                                url=f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}",
                                raw_data={
                                    "type": "discord_message",
                                    "guild_id": guild_id,
                                    "channel_id": channel_id,
                                    "message_id": msg_id,
                                    "author": msg.get("author", {}).get("username"),
                                    "timestamp": msg.get("timestamp"),
                                },
                                metadata={
                                    "platform": "discord",
                                    "server": server["name"],
                                    "channel": channel_name,
                                }
                            )
                            signals.append(signal)

                        # Rate limiting
                        await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"Error fetching from {server['name']}: {e}")

        return signals

    async def _fetch_from_webhooks(self) -> List[SignalData]:
        """Fetch stored messages from webhook endpoints."""
        signals: List[SignalData] = []

        # This would connect to your own webhook storage service
        # For now, return empty as this requires external setup
        return signals

    async def _fetch_public_announcements(self) -> List[SignalData]:
        """Fetch from public Discord announcement aggregators."""
        signals: List[SignalData] = []

        # Use Discord.me or similar public APIs
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Example: Fetch from a public announcement aggregator
                # This is a placeholder - actual implementation depends on available APIs

                # Discord's public server discovery API (limited)
                for server in self.TRACKED_SERVERS[:3]:
                    guild_id = server.get("guild_id")
                    if not guild_id:
                        continue

                    # Try to get server info from public API
                    response = await client.get(
                        f"https://discord.com/api/v9/guilds/{guild_id}/preview",
                        headers={"User-Agent": "Agentic-Orchestrator/0.4.0"}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        description = data.get("description", "")
                        features = data.get("features", [])

                        if description and "COMMUNITY" in features:
                            signal = SignalData(
                                source=self.name,
                                category=server.get("category", "crypto"),
                                title=f"[{server['name']}] Server active with {data.get('approximate_member_count', 0)} members",
                                summary=description[:500],
                                url=f"https://discord.gg/{data.get('discovery_splash', '')}",
                                raw_data={
                                    "type": "discord_preview",
                                    "guild_id": guild_id,
                                    "member_count": data.get("approximate_member_count"),
                                    "features": features,
                                },
                                metadata={
                                    "platform": "discord",
                                    "server": server["name"],
                                }
                            )
                            signals.append(signal)

                    await asyncio.sleep(1)

        except Exception as e:
            print(f"Error fetching public Discord data: {e}")

        return signals

    def _clean_cache(self) -> None:
        """Remove old entries from message cache."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._seen_messages = {
            k: v for k, v in self._seen_messages.items()
            if v > cutoff
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        base_health["bot_token_configured"] = bool(self.bot_token)
        base_health["webhooks_configured"] = len(self.webhook_urls)
        base_health["tracked_servers"] = len(self.TRACKED_SERVERS)

        # Test bot token if available
        if self.bot_token:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        "https://discord.com/api/v10/users/@me",
                        headers={"Authorization": f"Bot {self.bot_token}"}
                    )
                    base_health["bot_status"] = "connected" if response.status_code == 200 else "error"
            except Exception as e:
                base_health["bot_status"] = f"error: {e}"

        return base_health
