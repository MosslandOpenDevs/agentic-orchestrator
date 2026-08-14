"""DefiLlama API contract and data-quality regression tests."""

import httpx
import pytest

from agentic_orchestrator.adapters.base import SignalData
from agentic_orchestrator.adapters.onchain import OnChainAdapter


def _patch_http_client(monkeypatch, routes):
    class _Client:
        calls = []

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, **kwargs):
            self.__class__.calls.append((url, kwargs))
            status, payload = routes[url]
            request = httpx.Request("GET", url, params=kwargs.get("params"))
            return httpx.Response(status, json=payload, request=request)

    monkeypatch.setattr("agentic_orchestrator.adapters.onchain.httpx.AsyncClient", _Client)
    return _Client


@pytest.mark.asyncio
async def test_raises_are_disabled_without_network(monkeypatch):
    class _UnexpectedClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("no HTTP client should be created")

    monkeypatch.setattr(
        "agentic_orchestrator.adapters.onchain.httpx.AsyncClient", _UnexpectedClient
    )

    assert await OnChainAdapter()._fetch_protocol_updates() == []


def _asset(symbol, circulating, price, **overrides):
    asset = {
        "name": symbol,
        "symbol": symbol,
        "pegType": "peggedUSD",
        "yieldBearing": False,
        "circulating": {"peggedUSD": circulating},
        "price": price,
        "gecko_id": symbol.lower(),
    }
    asset.update(overrides)
    return asset


@pytest.mark.asyncio
async def test_stablecoin_assets_use_free_endpoint_sort_and_filter(monkeypatch):
    url = "https://stablecoins.llama.fi/stablecoins"
    # LOW is depegged but ranks 11th and must not consume a Top-10 alert.
    assets = [_asset("LOW", 1_000_000_000, 0.80)]
    assets.extend(_asset(f"USD{i}", i * 1_000_000_000, 1.0) for i in range(2, 11))
    assets.append(_asset("TOP", 20_000_000_000, 0.98))
    assets.extend(
        [
            _asset("EUR", 100_000_000_000, 1.20, pegType="peggedEUR"),
            _asset("YIELD", 90_000_000_000, 1.15, yieldBearing=True),
            _asset("NOPRICE", 80_000_000_000, None),
        ]
    )
    client = _patch_http_client(monkeypatch, {url: (200, {"peggedAssets": assets})})

    signals = await OnChainAdapter()._fetch_stablecoin_assets()

    assert [signal.raw_data["symbol"] for signal in signals] == ["TOP"]
    assert client.calls == [(url, {"params": {"includePrices": "true"}})]


@pytest.mark.asyncio
async def test_stablecoin_chains_use_exact_path_and_market_cap_order(monkeypatch):
    url = "https://stablecoins.llama.fi/stablecoinchains"
    chains = [
        {"name": "Small", "totalCirculatingUSD": {"peggedUSD": 10_500_000_000}},
        {"name": "Second", "totalCirculating": {"peggedUSD": 40_000_000_000}},
        {"name": "Fifth", "totalCirculatingUSD": {"peggedUSD": 11_000_000_000}},
        {"name": "First", "totalCirculatingUSD": {"peggedUSD": 50_000_000_000}},
        {"name": "Fourth", "totalCirculatingUSD": {"peggedUSD": 20_000_000_000}},
        {"name": "Third", "totalCirculatingUSD": {"peggedUSD": 30_000_000_000}},
    ]
    client = _patch_http_client(monkeypatch, {url: (200, chains)})

    signals = await OnChainAdapter()._fetch_stablecoin_chains()

    assert [signal.raw_data["chain"] for signal in signals] == [
        "First",
        "Second",
        "Third",
        "Fourth",
        "Fifth",
    ]
    assert client.calls[0][0] == url


@pytest.mark.asyncio
async def test_fetch_preserves_chain_signals_when_asset_source_fails(monkeypatch):
    adapter = OnChainAdapter()
    chain_signal = SignalData(
        source="onchain",
        category="crypto",
        title="Stablecoin Liquidity: $20B on Example",
    )

    async def empty():
        return []

    async def broken_assets():
        raise RuntimeError("asset endpoint unavailable")

    async def chain_signals():
        return [chain_signal]

    monkeypatch.setattr(adapter, "_fetch_defi_tvl", empty)
    monkeypatch.setattr(adapter, "_fetch_chain_stats", empty)
    monkeypatch.setattr(adapter, "_fetch_dex_volume", empty)
    monkeypatch.setattr(adapter, "_fetch_whale_transactions", empty)
    monkeypatch.setattr(adapter, "_fetch_stablecoin_assets", broken_assets)
    monkeypatch.setattr(adapter, "_fetch_stablecoin_chains", chain_signals)

    result = await adapter.fetch()

    assert result.success is True
    assert result.signals == [chain_signal]
    assert result.metadata["partial"] is True
    assert result.metadata["failed_subsources"] == ["stablecoin_assets"]
    assert "asset endpoint unavailable" in result.error
    assert result.metadata["raises_enabled"] is False
    assert result.metadata["raises_disabled_reason"] == "defillama_pro_only"
