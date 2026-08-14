"""
OnChain data adapter for signal collection.

Collects signals from blockchain data:
- Ethereum network activity
- MOC token activity
- DeFi TVL changes
- Whale movements
"""

import asyncio
import logging
import math
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from .base import AdapterConfig, AdapterResult, BaseAdapter, SignalData, recurring_key

logger = logging.getLogger(__name__)


class OnChainAdapter(BaseAdapter):
    """
    OnChain data adapter.

    Fetches blockchain data from various sources:
    - DefiLlama (TVL data, DEX volume)
    - Etherscan (Ethereum activity)
    - Whale Alert (large transactions)
    - DEX aggregators (volume, liquidity)
    - Public RPC endpoints
    """

    # DeFi protocols to track
    TRACKED_PROTOCOLS: List[str] = [
        "uniswap",
        "aave",
        "lido",
        "makerdao",
        "curve",
        "compound",
        "convex-finance",
        "rocket-pool",
        "instadapp",
        "yearn-finance",
    ]

    # Chains to monitor
    TRACKED_CHAINS: List[str] = [
        "ethereum",
        "polygon",
        "arbitrum",
        "optimism",
        "base",
        "solana",
    ]

    # DEXes to track for volume
    TRACKED_DEXES: List[str] = [
        "uniswap",
        "curve",
        "pancakeswap",
        "sushiswap",
        "balancer",
        "trader-joe",
        "camelot",
        "velodrome",
        "aerodrome",
    ]

    # Tokens to track for whale movements (symbol: address)
    TRACKED_TOKENS: Dict[str, str] = {
        "ETH": "ethereum",
        "BTC": "bitcoin",
        "USDT": "tether",
        "USDC": "usd-coin",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "AAVE": "aave",
    }

    # Minimum transaction values for whale alerts (in USD)
    WHALE_THRESHOLDS: Dict[str, int] = {
        "ETH": 1_000_000,
        "BTC": 1_000_000,
        "USDT": 5_000_000,
        "USDC": 5_000_000,
        "default": 500_000,
    }

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        etherscan_api_key: Optional[str] = None,
        alchemy_api_key: Optional[str] = None,
        whale_alert_api_key: Optional[str] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.etherscan_api_key = etherscan_api_key or os.getenv("ETHERSCAN_API_KEY")
        self.alchemy_api_key = alchemy_api_key or os.getenv("ALCHEMY_API_KEY")
        self.whale_alert_api_key = whale_alert_api_key or os.getenv("WHALE_ALERT_API_KEY")

        # API endpoints
        self.defillama_api = "https://api.llama.fi"
        self.defillama_stablecoins_api = "https://stablecoins.llama.fi"
        self.etherscan_api = "https://api.etherscan.io/api"
        self.whale_alert_api = "https://api.whale-alert.io/v1"

    @property
    def name(self) -> str:
        return "onchain"

    async def fetch(self) -> AdapterResult:
        """Fetch on-chain signals."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Keep subsource names with their tasks so a partial failure is visible
        # without discarding signals returned by the other APIs.
        jobs = [
            ("defi_tvl", self._fetch_defi_tvl()),
            ("chain_stats", self._fetch_chain_stats()),
            ("dex_volume", self._fetch_dex_volume()),
            ("whale_transactions", self._fetch_whale_transactions()),
            ("stablecoin_assets", self._fetch_stablecoin_assets()),
            ("stablecoin_chains", self._fetch_stablecoin_chains()),
        ]
        results = await asyncio.gather(
            *(task for _, task in jobs),
            return_exceptions=True,
        )

        failed_subsources: List[str] = []
        for (subsource, _), result in zip(jobs, results, strict=True):
            if isinstance(result, Exception):
                errors.append(f"{subsource}: {result}")
                failed_subsources.append(subsource)
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
                "protocols_tracked": len(self.TRACKED_PROTOCOLS),
                "chains_tracked": len(self.TRACKED_CHAINS),
                "dexes_tracked": len(self.TRACKED_DEXES),
                "has_whale_alert": bool(self.whale_alert_api_key),
                "raises_enabled": False,
                "raises_disabled_reason": "defillama_pro_only",
                "failed_subsources": failed_subsources,
                "errors_count": len(errors),
                "partial": bool(signals and errors),
            },
        )

    async def _fetch_defi_tvl(self) -> List[SignalData]:
        """Fetch DeFi TVL data from DefiLlama."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get protocols TVL
                response = await client.get(f"{self.defillama_api}/protocols")
                response.raise_for_status()
                protocols = response.json()

                # Filter to tracked protocols and find significant changes
                for protocol in protocols:
                    name = protocol.get("slug", "").lower()
                    if name not in self.TRACKED_PROTOCOLS:
                        continue

                    tvl = protocol.get("tvl", 0)
                    change_1d = protocol.get("change_1d", 0)
                    change_7d = protocol.get("change_7d", 0)

                    # Only report significant changes (>5% in 24h or >10% in 7d)
                    if abs(change_1d or 0) > 5 or abs(change_7d or 0) > 10:
                        direction = "increased" if (change_1d or 0) > 0 else "decreased"

                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            external_id=recurring_key("defi_tvl", name, direction),
                            title=f"DeFi TVL: {protocol.get('name')} {direction} {abs(change_1d or 0):.1f}%",
                            summary=f"TVL: ${tvl/1e9:.2f}B, 24h change: {change_1d:.1f}%, 7d change: {change_7d:.1f}%",
                            url=f"https://defillama.com/protocol/{name}",
                            raw_data={
                                "type": "defi_tvl",
                                "protocol": protocol.get("name"),
                                "slug": name,
                                "tvl": tvl,
                                "change_1d": change_1d,
                                "change_7d": change_7d,
                                "chains": protocol.get("chains", []),
                            },
                            metadata={"subtype": "tvl"},
                        )
                        signals.append(signal)

        except Exception as e:
            logger.warning(f"Error fetching DeFi TVL: {e}")

        return signals

    async def _fetch_chain_stats(self) -> List[SignalData]:
        """Fetch chain statistics from DefiLlama."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.defillama_api}/v2/chains")
                response.raise_for_status()
                chains = response.json()

                for chain in chains:
                    name = chain.get("name", "").lower()
                    if name not in self.TRACKED_CHAINS:
                        continue

                    gecko_id = chain.get("gecko_id")
                    tvl = chain.get("tvl", 0)

                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        # A daily heartbeat, not an event: the TVL figure in the
                        # title moves every poll (60 rows/wk for Ethereum alone).
                        external_id=recurring_key("chain_stats", name),
                        title=f"Chain Stats: {chain.get('name')} TVL ${tvl/1e9:.2f}B",
                        summary=f"Total Value Locked on {chain.get('name')}",
                        url=f"https://defillama.com/chain/{chain.get('name')}",
                        raw_data={
                            "type": "chain_stats",
                            "chain": chain.get("name"),
                            "gecko_id": gecko_id,
                            "tvl": tvl,
                        },
                        metadata={"subtype": "chain"},
                    )
                    signals.append(signal)

        except Exception as e:
            logger.warning(f"Error fetching chain stats: {e}")

        return signals

    async def _fetch_protocol_updates(self) -> List[SignalData]:
        """Raises are Pro-only and intentionally disabled without a subscription."""
        return []

    async def _fetch_dex_volume(self) -> List[SignalData]:
        """Fetch DEX volume data from DefiLlama."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get DEX overview
                response = await client.get(f"{self.defillama_api}/overview/dexs")
                response.raise_for_status()
                data = response.json()

                protocols = data.get("protocols", [])

                for protocol in protocols:
                    protocol.get("name", "").lower()
                    slug = protocol.get("slug", "").lower()

                    if slug not in self.TRACKED_DEXES:
                        continue

                    volume_24h = protocol.get("total24h", 0)
                    volume_7d = protocol.get("total7d", 0)
                    change_1d = protocol.get("change_1d", 0)
                    change_7d = protocol.get("change_7d", 0)

                    # Only report significant volume or changes
                    if volume_24h > 50_000_000 or abs(change_1d or 0) > 20:
                        direction = "increased" if (change_1d or 0) > 0 else "decreased"

                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            external_id=recurring_key("dex_volume", slug, direction),
                            title=f"DEX Volume: {protocol.get('name')} {direction} {abs(change_1d or 0):.1f}% (${volume_24h/1e6:.1f}M)",
                            summary=f"24h volume: ${volume_24h/1e6:.1f}M, 7d volume: ${volume_7d/1e6:.1f}M, 24h change: {change_1d:.1f}%",
                            url=f"https://defillama.com/dex/{slug}",
                            raw_data={
                                "type": "dex_volume",
                                "dex": protocol.get("name"),
                                "slug": slug,
                                "volume_24h": volume_24h,
                                "volume_7d": volume_7d,
                                "change_1d": change_1d,
                                "change_7d": change_7d,
                                "chains": protocol.get("chains", []),
                            },
                            metadata={"subtype": "dex_volume"},
                        )
                        signals.append(signal)

        except Exception as e:
            logger.warning(f"Error fetching DEX volume: {e}")

        return signals

    async def _fetch_whale_transactions(self) -> List[SignalData]:
        """Fetch large transactions from Whale Alert API."""
        signals: List[SignalData] = []

        if not self.whale_alert_api_key:
            # Fallback: Use public blockchain explorers
            return await self._fetch_whale_from_explorers()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get recent transactions
                response = await client.get(
                    f"{self.whale_alert_api}/transactions",
                    params={
                        "api_key": self.whale_alert_api_key,
                        "min_value": 500000,  # Minimum $500K
                        "limit": 20,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("transactions", [])

                    for tx in transactions:
                        amount_usd = tx.get("amount_usd", 0)
                        symbol = tx.get("symbol", "").upper()
                        from_owner = tx.get("from", {}).get("owner_type", "unknown")
                        to_owner = tx.get("to", {}).get("owner_type", "unknown")

                        # Determine if this is exchange flow
                        flow_type = self._determine_flow_type(from_owner, to_owner)

                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            # A transaction is a one-time event; its hash is its
                            # identity (no day bucket).
                            external_id=(
                                f"whale:{tx.get('blockchain')}:{tx['hash']}"
                                if tx.get("hash")
                                else None
                            ),
                            title=f"🐋 Whale Alert: {tx.get('amount', 0):,.0f} {symbol} (${amount_usd/1e6:.1f}M) - {flow_type}",
                            summary=f"From: {from_owner} → To: {to_owner}. Hash: {tx.get('hash', '')[:16]}...",
                            url=f"https://whale-alert.io/transaction/{tx.get('blockchain')}/{tx.get('hash')}",
                            raw_data={
                                "type": "whale_transaction",
                                "blockchain": tx.get("blockchain"),
                                "symbol": symbol,
                                "amount": tx.get("amount"),
                                "amount_usd": amount_usd,
                                "from_owner": from_owner,
                                "to_owner": to_owner,
                                "hash": tx.get("hash"),
                                "timestamp": tx.get("timestamp"),
                            },
                            metadata={
                                "subtype": "whale",
                                "flow_type": flow_type,
                            },
                        )
                        signals.append(signal)

        except Exception as e:
            logger.warning(f"Error fetching whale transactions: {e}")

        return signals

    async def _fetch_whale_from_explorers(self) -> List[SignalData]:
        """Fallback: Fetch whale transactions from public explorers."""
        signals: List[SignalData] = []

        if not self.etherscan_api_key:
            return signals

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get large ETH transactions (internal transactions)
                await client.get(
                    self.etherscan_api,
                    params={
                        "module": "account",
                        "action": "txlist",
                        "address": "0x0000000000000000000000000000000000000000",  # Placeholder
                        "sort": "desc",
                        "apikey": self.etherscan_api_key,
                    },
                )

                # Note: This is a simplified version. Real implementation would
                # track specific whale addresses or use a service that aggregates this.

        except Exception as e:
            logger.warning(f"Error fetching from explorers: {e}")

        return signals

    def _determine_flow_type(self, from_owner: str, to_owner: str) -> str:
        """Determine the type of token flow."""
        from_is_exchange = from_owner in ["exchange", "binance", "coinbase", "kraken", "ftx", "okx"]
        to_is_exchange = to_owner in ["exchange", "binance", "coinbase", "kraken", "ftx", "okx"]

        if from_is_exchange and not to_is_exchange:
            return "Exchange Outflow (Bullish)"
        elif not from_is_exchange and to_is_exchange:
            return "Exchange Inflow (Bearish)"
        elif from_is_exchange and to_is_exchange:
            return "Inter-Exchange Transfer"
        else:
            return "Whale Transfer"

    @staticmethod
    def _finite_number(value: Any) -> Optional[float]:
        """Return a finite JSON number, excluding booleans and nulls."""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            number = float(value)
            if math.isfinite(number):
                return number
        return None

    async def _fetch_stablecoin_assets(self) -> List[SignalData]:
        """Fetch USD-pegged asset supply and price data."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.defillama_stablecoins_api}/stablecoins",
                params={"includePrices": "true"},
            )
            response.raise_for_status()
            data = response.json()

        eligible = []
        for stable in data.get("peggedAssets", []):
            if stable.get("pegType") != "peggedUSD":
                continue
            if stable.get("yieldBearing") is True or stable.get("pegMechanism") == "yield-bearing":
                continue
            circulating = self._finite_number((stable.get("circulating") or {}).get("peggedUSD"))
            if circulating is not None:
                eligible.append((circulating, stable))

        for total_circulating, stable in sorted(eligible, key=lambda item: item[0], reverse=True)[
            :10
        ]:
            price = self._finite_number(stable.get("price"))
            if price is None or abs(price - 1.0) <= 0.01:
                continue

            name = stable.get("name", "")
            symbol = stable.get("symbol", "")
            depeg_pct = (price - 1.0) * 100
            direction = "above" if depeg_pct > 0 else "below"

            signal = SignalData(
                source=self.name,
                category="crypto",
                external_id=recurring_key("stablecoin_depeg", symbol, direction),
                title=f"⚠️ Stablecoin Alert: {symbol} trading {abs(depeg_pct):.2f}% {direction} peg (${price:.4f})",
                summary=f"{name} ({symbol}) circulating: ${total_circulating/1e9:.2f}B. Current price: ${price:.4f}",
                url=f"https://defillama.com/stablecoin/{stable.get('gecko_id', '')}",
                raw_data={
                    "type": "stablecoin_depeg",
                    "name": name,
                    "symbol": symbol,
                    "price": price,
                    "depeg_pct": depeg_pct,
                    "circulating": total_circulating,
                },
                metadata={"subtype": "stablecoin_alert"},
            )
            signals.append(signal)

        return signals

    async def _fetch_stablecoin_chains(self) -> List[SignalData]:
        """Fetch the largest stablecoin supplies by chain."""
        signals: List[SignalData] = []

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.defillama_stablecoins_api}/stablecoinchains")
            response.raise_for_status()
            chains_data = response.json()

        eligible = []
        for chain_data in chains_data:
            totals = (
                chain_data.get("totalCirculatingUSD") or chain_data.get("totalCirculating") or {}
            )
            total_usd = self._finite_number(totals.get("peggedUSD"))
            if total_usd is not None:
                eligible.append((total_usd, chain_data))

        for total_usd, chain_data in sorted(eligible, key=lambda item: item[0], reverse=True)[:5]:
            if total_usd <= 10_000_000_000:
                continue

            chain_name = chain_data.get("name", "")
            signal = SignalData(
                source=self.name,
                category="crypto",
                external_id=recurring_key("stablecoin_liquidity", chain_name),
                title=f"Stablecoin Liquidity: ${total_usd/1e9:.1f}B on {chain_name}",
                summary=f"Total stablecoin supply on {chain_name} chain",
                url=f"https://defillama.com/stablecoins/{chain_name}",
                raw_data={
                    "type": "stablecoin_chain",
                    "chain": chain_name,
                    "total_usd": total_usd,
                },
                metadata={"subtype": "stablecoin_liquidity"},
            )
            signals.append(signal)

        return signals

    async def _fetch_stablecoin_flows(self) -> List[SignalData]:
        """Compatibility wrapper that keeps asset and chain failures isolated."""
        signals: List[SignalData] = []
        jobs = [
            ("assets", self._fetch_stablecoin_assets()),
            ("chains", self._fetch_stablecoin_chains()),
        ]
        results = await asyncio.gather(
            *(task for _, task in jobs),
            return_exceptions=True,
        )
        for (subsource, _), result in zip(jobs, results, strict=True):
            if isinstance(result, Exception):
                logger.warning(
                    f"Error fetching stablecoin {subsource}: " f"{type(result).__name__}: {result}"
                )
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _fetch_gas_prices(self) -> List[SignalData]:
        """Fetch current gas prices (if Etherscan API key available)."""
        signals: List[SignalData] = []

        if not self.etherscan_api_key:
            return signals

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    self.etherscan_api,
                    params={
                        "module": "gastracker",
                        "action": "gasoracle",
                        "apikey": self.etherscan_api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "1":
                    result = data.get("result", {})
                    safe_gas = int(result.get("SafeGasPrice", 0))
                    propose_gas = int(result.get("ProposeGasPrice", 0))
                    fast_gas = int(result.get("FastGasPrice", 0))

                    # Report if gas is unusually high (>50 gwei) or low (<10 gwei)
                    if fast_gas > 50 or fast_gas < 10:
                        status = "high" if fast_gas > 50 else "low"
                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            external_id=recurring_key("gas", status),
                            title=f"Gas Alert: Ethereum gas is {status} ({fast_gas} gwei)",
                            summary=f"Safe: {safe_gas} gwei, Standard: {propose_gas} gwei, Fast: {fast_gas} gwei",
                            url="https://etherscan.io/gastracker",
                            raw_data={
                                "type": "gas_price",
                                "safe": safe_gas,
                                "standard": propose_gas,
                                "fast": fast_gas,
                            },
                            metadata={"subtype": "gas"},
                        )
                        signals.append(signal)

        except Exception as e:
            logger.warning(f"Error fetching gas prices: {e}")

        return signals

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        # Check DefiLlama API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.defillama_api}/protocols")
                base_health["defillama_status"] = (
                    "connected" if response.status_code == 200 else "error"
                )
        except Exception as e:
            base_health["defillama_status"] = f"error: {e}"

        # Check Whale Alert API
        if self.whale_alert_api_key:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        f"{self.whale_alert_api}/status",
                        params={"api_key": self.whale_alert_api_key},
                    )
                    base_health["whale_alert_status"] = (
                        "connected" if response.status_code == 200 else "error"
                    )
            except Exception as e:
                base_health["whale_alert_status"] = f"error: {e}"

        base_health["etherscan_api_key"] = bool(self.etherscan_api_key)
        base_health["alchemy_api_key"] = bool(self.alchemy_api_key)
        base_health["whale_alert_api_key"] = bool(self.whale_alert_api_key)
        base_health["tracked_dexes"] = len(self.TRACKED_DEXES)

        return base_health
