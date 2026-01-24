"""
Lens Protocol adapter for signal collection.

Collects signals from Lens Protocol (Web3 social network) via GraphQL API.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class LensAdapter(BaseAdapter):
    """
    Lens Protocol adapter.

    Fetches data from Lens Protocol's GraphQL API:
    - Popular publications
    - Followed profiles' posts
    - Trending topics
    - Profile activities
    """

    # Lens API endpoint
    LENS_API = "https://api-v2.lens.dev"

    # Profiles to track (Lens handles)
    TRACKED_PROFILES: List[str] = [
        "stani.lens",          # Stani Kulechov (Aave founder)
        "aaveaave.lens",       # Aave official
        "lenster.lens",        # Lenster (Lens client)
        "lensprotocol.lens",   # Lens Protocol official
        "yoginth.lens",        # Developer/creator
        "christina.lens",      # Active community member
        "wagmi.lens",          # Web3 culture
        "nader.lens",          # Developer advocate
        "coopahtroopa.lens",   # Music NFTs
        "poap.lens",           # POAP official
    ]

    # Keywords to search for
    TRACKED_KEYWORDS: List[str] = [
        "metaverse",
        "web3 gaming",
        "NFT utility",
        "DeFi",
        "DAO governance",
        "AI blockchain",
        "token economics",
    ]

    def __init__(self, config: Optional[AdapterConfig] = None):
        super().__init__(config or AdapterConfig(timeout=60))

    @property
    def name(self) -> str:
        return "lens"

    async def fetch(self) -> AdapterResult:
        """Fetch signals from Lens Protocol."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch different types of content concurrently
        tasks = [
            self._fetch_explore_publications(),
            self._fetch_profile_publications(),
            self._fetch_trending(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif isinstance(result, list):
                signals.extend(result)

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "profiles_tracked": len(self.TRACKED_PROFILES),
                "keywords_tracked": len(self.TRACKED_KEYWORDS),
            }
        )

    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make a GraphQL request to Lens API."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.LENS_API,
                    json={"query": query, "variables": variables or {}},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            print(f"Lens GraphQL error: {e}")

        return None

    async def _fetch_explore_publications(self) -> List[SignalData]:
        """Fetch trending/explore publications."""
        signals: List[SignalData] = []

        query = """
        query ExplorePublications($request: ExplorePublicationRequest!) {
            explorePublications(request: $request) {
                items {
                    ... on Post {
                        id
                        metadata {
                            content
                            name
                            description
                        }
                        by {
                            handle {
                                fullHandle
                            }
                            metadata {
                                displayName
                            }
                        }
                        createdAt
                        stats {
                            upvotes
                            comments
                            mirrors
                        }
                    }
                }
            }
        }
        """

        variables = {
            "request": {
                "orderBy": "TOP_COMMENTED",
                "limit": "TwentyFive",
            }
        }

        result = await self._graphql_request(query, variables)

        if result and "data" in result:
            items = result["data"].get("explorePublications", {}).get("items", [])

            for item in items:
                if not item:
                    continue

                metadata = item.get("metadata", {})
                content = metadata.get("content", "")
                title = metadata.get("name") or content[:100]

                by = item.get("by", {})
                handle = by.get("handle", {}).get("fullHandle", "unknown")
                display_name = by.get("metadata", {}).get("displayName", handle)

                stats = item.get("stats", {})

                # Calculate engagement score
                engagement = (
                    (stats.get("upvotes", 0) * 1) +
                    (stats.get("comments", 0) * 2) +
                    (stats.get("mirrors", 0) * 3)
                )

                signal = SignalData(
                    source=self.name,
                    category="crypto",  # Lens is Web3/crypto focused
                    title=f"@{handle}: {title[:150]}",
                    summary=content[:500] if len(content) > 150 else None,
                    url=f"https://hey.xyz/posts/{item.get('id', '')}",
                    raw_data={
                        "type": "lens_post",
                        "publication_id": item.get("id"),
                        "handle": handle,
                        "display_name": display_name,
                        "stats": stats,
                        "created_at": item.get("createdAt"),
                    },
                    metadata={
                        "platform": "lens",
                        "engagement_score": engagement,
                    }
                )
                signals.append(signal)

        return signals

    async def _fetch_profile_publications(self) -> List[SignalData]:
        """Fetch publications from tracked profiles."""
        signals: List[SignalData] = []

        query = """
        query Publications($request: PublicationsRequest!) {
            publications(request: $request) {
                items {
                    ... on Post {
                        id
                        metadata {
                            content
                            name
                        }
                        by {
                            handle {
                                fullHandle
                            }
                        }
                        createdAt
                        stats {
                            upvotes
                            comments
                        }
                    }
                }
            }
        }
        """

        for profile_handle in self.TRACKED_PROFILES[:5]:  # Limit API calls
            variables = {
                "request": {
                    "where": {
                        "from": [profile_handle.replace(".lens", "")],
                    },
                    "limit": "Ten",
                }
            }

            result = await self._graphql_request(query, variables)

            if result and "data" in result:
                items = result["data"].get("publications", {}).get("items", [])

                for item in items[:3]:  # Top 3 per profile
                    if not item:
                        continue

                    metadata = item.get("metadata", {})
                    content = metadata.get("content", "")

                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"@{profile_handle}: {content[:150]}",
                        summary=content[:500] if len(content) > 150 else None,
                        url=f"https://hey.xyz/posts/{item.get('id', '')}",
                        raw_data={
                            "type": "lens_profile_post",
                            "publication_id": item.get("id"),
                            "handle": profile_handle,
                            "created_at": item.get("createdAt"),
                        },
                        metadata={
                            "platform": "lens",
                            "tracked_profile": True,
                        }
                    )
                    signals.append(signal)

            # Rate limiting
            await asyncio.sleep(0.3)

        return signals

    async def _fetch_trending(self) -> List[SignalData]:
        """Fetch trending content based on keywords."""
        signals: List[SignalData] = []

        query = """
        query SearchPublications($request: PublicationSearchRequest!) {
            searchPublications(request: $request) {
                items {
                    ... on Post {
                        id
                        metadata {
                            content
                            name
                        }
                        by {
                            handle {
                                fullHandle
                            }
                        }
                        createdAt
                    }
                }
            }
        }
        """

        for keyword in self.TRACKED_KEYWORDS[:3]:  # Limit searches
            variables = {
                "request": {
                    "query": keyword,
                    "limit": "Ten",
                }
            }

            result = await self._graphql_request(query, variables)

            if result and "data" in result:
                items = result["data"].get("searchPublications", {}).get("items", [])

                for item in items[:3]:
                    if not item:
                        continue

                    metadata = item.get("metadata", {})
                    content = metadata.get("content", "")
                    handle = item.get("by", {}).get("handle", {}).get("fullHandle", "unknown")

                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"[{keyword}] @{handle}: {content[:100]}",
                        summary=content[:500] if len(content) > 100 else None,
                        url=f"https://hey.xyz/posts/{item.get('id', '')}",
                        raw_data={
                            "type": "lens_search",
                            "keyword": keyword,
                            "publication_id": item.get("id"),
                            "handle": handle,
                        },
                        metadata={
                            "platform": "lens",
                            "search_keyword": keyword,
                        }
                    )
                    signals.append(signal)

            await asyncio.sleep(0.3)

        return signals

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        # Test Lens API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.LENS_API,
                    json={
                        "query": "{ ping }",
                    },
                    headers={"Content-Type": "application/json"}
                )
                base_health["lens_api_status"] = "connected" if response.status_code == 200 else "error"
        except Exception as e:
            base_health["lens_api_status"] = f"error: {e}"

        base_health["tracked_profiles"] = len(self.TRACKED_PROFILES)
        base_health["tracked_keywords"] = len(self.TRACKED_KEYWORDS)

        return base_health
