"""
Coingecko adapter for signal collection.

Collects market signals from Coingecko API:
- Trending coins
- Price changes (significant movers)
- Market cap changes
- Volume spikes
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class CoingeckoAdapter(BaseAdapter):
    """
    Coingecko market data adapter.

    Fetches cryptocurrency market data:
    - Trending coins (search trends)
    - Top gainers/losers (24h price changes)
    - Volume spikes
    - Market cap changes
    - Global market stats

    Uses free API tier with rate limiting (10-30 req/min).
    """

    # Coins to always track (by id)
    TRACKED_COINS: List[str] = [
        "bitcoin",
        "ethereum",
        "solana",
        "polygon",
        "arbitrum",
        "optimism",
        "avalanche-2",
        "bnb",
        "cardano",
        "polkadot",
        "chainlink",
        "uniswap",
        "aave",
        "maker",
        "lido-dao",
        "mossland",  # MOC token
    ]

    # Categories to monitor for trending
    CATEGORIES: List[str] = [
        "decentralized-finance-defi",
        "non-fungible-tokens-nft",
        "metaverse",
        "gaming",
        "layer-1",
        "layer-2",
        "artificial-intelligence",
    ]

    # Thresholds for signals
    PRICE_CHANGE_THRESHOLD: float = 10.0  # 10% price change
    VOLUME_SPIKE_THRESHOLD: float = 100.0  # 100% volume increase
    MARKET_CAP_THRESHOLD: int = 100_000_000  # $100M minimum market cap

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        api_key: Optional[str] = None,
    ):
        # Use rate limiting for free tier (10 requests per minute)
        default_config = AdapterConfig(
            timeout=30,
            rate_limit=0.15,  # ~10 requests per minute
        )
        super().__init__(config or default_config)
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY")

        # API endpoints
        self.base_url = "https://api.coingecko.com/api/v3"
        self.pro_url = "https://pro-api.coingecko.com/api/v3"

        # Use pro API if key available
        self.api_url = self.pro_url if self.api_key else self.base_url

    @property
    def name(self) -> str:
        return "coingecko"

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        headers = {
            "Accept": "application/json",
        }
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        return headers

    async def fetch(self) -> AdapterResult:
        """Fetch market signals from Coingecko."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch different types of market data concurrently
        tasks = [
            self._fetch_trending(),
            self._fetch_top_movers(),
            self._fetch_global_stats(),
            self._fetch_tracked_coins(),
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
                "has_api_key": bool(self.api_key),
                "tracked_coins": len(self.TRACKED_COINS),
                "categories": len(self.CATEGORIES),
            }
        )

    async def _fetch_trending(self) -> List[SignalData]:
        """Fetch trending coins from Coingecko."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_url}/search/trending",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                trending_coins = data.get("coins", [])

                for item in trending_coins[:7]:  # Top 7 trending
                    coin = item.get("item", {})
                    name = coin.get("name", "")
                    symbol = coin.get("symbol", "").upper()
                    market_cap_rank = coin.get("market_cap_rank", "N/A")
                    price_btc = coin.get("price_btc", 0)

                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"Trending: {name} ({symbol}) is trending on Coingecko",
                        summary=f"Market cap rank: #{market_cap_rank}. Price: {price_btc:.8f} BTC. This coin is seeing increased search interest.",
                        url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                        raw_data={
                            "type": "trending",
                            "coin_id": coin.get("id"),
                            "name": name,
                            "symbol": symbol,
                            "market_cap_rank": market_cap_rank,
                            "price_btc": price_btc,
                            "thumb": coin.get("thumb"),
                        },
                        metadata={"subtype": "trending"}
                    )
                    signals.append(signal)

                # Also check trending NFTs if available
                trending_nfts = data.get("nfts", [])
                for nft in trending_nfts[:3]:  # Top 3 trending NFTs
                    name = nft.get("name", "")
                    floor_price = nft.get("floor_price_in_native_currency", 0)
                    floor_change_24h = nft.get("floor_price_24h_percentage_change", 0)

                    if abs(floor_change_24h) > 5:  # Only report significant changes
                        direction = "up" if floor_change_24h > 0 else "down"
                        signal = SignalData(
                            source=self.name,
                            category="nft",
                            title=f"NFT Trending: {name} floor price {direction} {abs(floor_change_24h):.1f}%",
                            summary=f"Floor price: {floor_price:.4f} ETH. 24h change: {floor_change_24h:+.1f}%",
                            url=f"https://www.coingecko.com/en/nft/{nft.get('id', '')}",
                            raw_data={
                                "type": "trending_nft",
                                "nft_id": nft.get("id"),
                                "name": name,
                                "floor_price": floor_price,
                                "floor_change_24h": floor_change_24h,
                            },
                            metadata={"subtype": "trending_nft"}
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error fetching trending: {e}")

        return signals

    async def _fetch_top_movers(self) -> List[SignalData]:
        """Fetch top gainers and losers."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get market data for top 250 coins by market cap
                response = await client.get(
                    f"{self.api_url}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": 1,
                        "sparkline": False,
                        "price_change_percentage": "24h,7d",
                    },
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                coins = response.json()

                # Filter for significant movers
                gainers = []
                losers = []

                for coin in coins:
                    change_24h = coin.get("price_change_percentage_24h", 0) or 0
                    market_cap = coin.get("market_cap", 0) or 0

                    # Only consider coins with reasonable market cap
                    if market_cap < self.MARKET_CAP_THRESHOLD:
                        continue

                    if change_24h >= self.PRICE_CHANGE_THRESHOLD:
                        gainers.append((coin, change_24h))
                    elif change_24h <= -self.PRICE_CHANGE_THRESHOLD:
                        losers.append((coin, change_24h))

                # Sort and take top 5 each
                gainers.sort(key=lambda x: x[1], reverse=True)
                losers.sort(key=lambda x: x[1])

                for coin, change in gainers[:5]:
                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"Market Mover: {coin['name']} ({coin['symbol'].upper()}) +{change:.1f}% in 24h",
                        summary=f"Price: ${coin.get('current_price', 0):,.4f}. Market cap: ${coin.get('market_cap', 0)/1e9:.2f}B. Rank: #{coin.get('market_cap_rank', 'N/A')}",
                        url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                        raw_data={
                            "type": "gainer",
                            "coin_id": coin.get("id"),
                            "name": coin.get("name"),
                            "symbol": coin.get("symbol"),
                            "price": coin.get("current_price"),
                            "market_cap": coin.get("market_cap"),
                            "change_24h": change,
                            "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                            "volume_24h": coin.get("total_volume"),
                        },
                        metadata={"subtype": "gainer", "change_pct": change}
                    )
                    signals.append(signal)

                for coin, change in losers[:5]:
                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"Market Mover: {coin['name']} ({coin['symbol'].upper()}) {change:.1f}% in 24h",
                        summary=f"Price: ${coin.get('current_price', 0):,.4f}. Market cap: ${coin.get('market_cap', 0)/1e9:.2f}B. Rank: #{coin.get('market_cap_rank', 'N/A')}",
                        url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                        raw_data={
                            "type": "loser",
                            "coin_id": coin.get("id"),
                            "name": coin.get("name"),
                            "symbol": coin.get("symbol"),
                            "price": coin.get("current_price"),
                            "market_cap": coin.get("market_cap"),
                            "change_24h": change,
                            "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                            "volume_24h": coin.get("total_volume"),
                        },
                        metadata={"subtype": "loser", "change_pct": change}
                    )
                    signals.append(signal)

                # Check for volume spikes
                for coin in coins:
                    volume = coin.get("total_volume", 0) or 0
                    market_cap = coin.get("market_cap", 0) or 0

                    if market_cap > 0:
                        volume_to_mcap = (volume / market_cap) * 100

                        # Volume > 50% of market cap indicates unusual activity
                        if volume_to_mcap > 50:
                            signal = SignalData(
                                source=self.name,
                                category="crypto",
                                title=f"Volume Spike: {coin['name']} ({coin['symbol'].upper()}) 24h volume is {volume_to_mcap:.0f}% of market cap",
                                summary=f"24h volume: ${volume/1e6:.1f}M. Market cap: ${market_cap/1e6:.1f}M. This indicates unusually high trading activity.",
                                url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                                raw_data={
                                    "type": "volume_spike",
                                    "coin_id": coin.get("id"),
                                    "name": coin.get("name"),
                                    "symbol": coin.get("symbol"),
                                    "volume_24h": volume,
                                    "market_cap": market_cap,
                                    "volume_to_mcap_pct": volume_to_mcap,
                                },
                                metadata={"subtype": "volume_spike"}
                            )
                            signals.append(signal)

        except Exception as e:
            print(f"Error fetching top movers: {e}")

        return signals

    async def _fetch_global_stats(self) -> List[SignalData]:
        """Fetch global market statistics."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_url}/global",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json().get("data", {})

                total_market_cap = data.get("total_market_cap", {}).get("usd", 0)
                total_volume = data.get("total_volume", {}).get("usd", 0)
                market_cap_change_24h = data.get("market_cap_change_percentage_24h_usd", 0)
                btc_dominance = data.get("market_cap_percentage", {}).get("btc", 0)
                eth_dominance = data.get("market_cap_percentage", {}).get("eth", 0)

                # Report significant market changes
                if abs(market_cap_change_24h) > 3:
                    direction = "increased" if market_cap_change_24h > 0 else "decreased"
                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"Global Market: Total crypto market cap {direction} {abs(market_cap_change_24h):.1f}% to ${total_market_cap/1e12:.2f}T",
                        summary=f"24h volume: ${total_volume/1e9:.0f}B. BTC dominance: {btc_dominance:.1f}%. ETH dominance: {eth_dominance:.1f}%.",
                        url="https://www.coingecko.com/en/global-charts",
                        raw_data={
                            "type": "global_market",
                            "total_market_cap": total_market_cap,
                            "total_volume": total_volume,
                            "market_cap_change_24h": market_cap_change_24h,
                            "btc_dominance": btc_dominance,
                            "eth_dominance": eth_dominance,
                            "active_cryptocurrencies": data.get("active_cryptocurrencies"),
                        },
                        metadata={"subtype": "global_market"}
                    )
                    signals.append(signal)

                # Report dominance shifts
                if btc_dominance < 40 or btc_dominance > 60:
                    status = "low" if btc_dominance < 40 else "high"
                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"BTC Dominance Alert: Bitcoin dominance is {status} at {btc_dominance:.1f}%",
                        summary=f"ETH dominance: {eth_dominance:.1f}%. Total market cap: ${total_market_cap/1e12:.2f}T",
                        url="https://www.coingecko.com/en/global-charts",
                        raw_data={
                            "type": "dominance_shift",
                            "btc_dominance": btc_dominance,
                            "eth_dominance": eth_dominance,
                            "status": status,
                        },
                        metadata={"subtype": "dominance"}
                    )
                    signals.append(signal)

        except Exception as e:
            print(f"Error fetching global stats: {e}")

        return signals

    async def _fetch_tracked_coins(self) -> List[SignalData]:
        """Fetch data for specifically tracked coins."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Fetch data for tracked coins
                ids = ",".join(self.TRACKED_COINS)
                response = await client.get(
                    f"{self.api_url}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": ids,
                        "order": "market_cap_desc",
                        "sparkline": False,
                        "price_change_percentage": "24h,7d,30d",
                    },
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                coins = response.json()

                for coin in coins:
                    change_24h = coin.get("price_change_percentage_24h", 0) or 0
                    change_7d = coin.get("price_change_percentage_7d_in_currency", 0) or 0
                    change_30d = coin.get("price_change_percentage_30d_in_currency", 0) or 0

                    # Report significant movements in tracked coins
                    if abs(change_24h) > 5 or abs(change_7d) > 15:
                        direction = "up" if change_24h > 0 else "down"
                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            title=f"Tracked Coin: {coin['name']} ({coin['symbol'].upper()}) is {direction} {abs(change_24h):.1f}% (24h)",
                            summary=f"Price: ${coin.get('current_price', 0):,.4f}. 7d: {change_7d:+.1f}%. 30d: {change_30d:+.1f}%. Volume: ${coin.get('total_volume', 0)/1e6:.1f}M",
                            url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                            raw_data={
                                "type": "tracked_coin",
                                "coin_id": coin.get("id"),
                                "name": coin.get("name"),
                                "symbol": coin.get("symbol"),
                                "price": coin.get("current_price"),
                                "market_cap": coin.get("market_cap"),
                                "change_24h": change_24h,
                                "change_7d": change_7d,
                                "change_30d": change_30d,
                                "volume_24h": coin.get("total_volume"),
                                "ath": coin.get("ath"),
                                "ath_change_percentage": coin.get("ath_change_percentage"),
                            },
                            metadata={"subtype": "tracked", "is_tracked": True}
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error fetching tracked coins: {e}")

        return signals

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        # Check Coingecko API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_url}/ping",
                    headers=self._get_headers(),
                )
                base_health["coingecko_status"] = "connected" if response.status_code == 200 else "error"
                base_health["api_type"] = "pro" if self.api_key else "free"
        except Exception as e:
            base_health["coingecko_status"] = f"error: {e}"

        base_health["has_api_key"] = bool(self.api_key)
        base_health["tracked_coins"] = len(self.TRACKED_COINS)

        return base_health
