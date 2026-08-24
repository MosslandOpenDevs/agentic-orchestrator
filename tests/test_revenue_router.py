import pytest
from unittest.mock import MagicMock
from src.routers.revenue_router import RevenueRouter

@pytest.fixture
def mock_w3():
    w3 = MagicMock()
    w3.eth.send_transaction.return_value = b'tx_hash'
    return w3

@pytest.fixture
def router(mock_w3):
    config = {'platform_fee_bps': 1000, 'agent_ops_fee_bps': 1000}
    return RevenueRouter(mock_w3, config)

def test_calculate_splits(router):
    total_wei = 10 * 10**18
    splits = router.calculate_splits(total_wei)
    assert splits['platform'] == 1 * 10**18
    assert splits['agent_ops'] == 1 * 10**18
    assert splits['treasury'] == 8 * 10**18
    assert sum(splits.values()) == total_wei

def test_calculate_splits_rounding(router):
    total_wei = 1000000000000000001
    splits = router.calculate_splits(total_wei)
    assert sum(splits.values()) == total_wei

@pytest.mark.asyncio
async def test_distribute(router, mock_w3):
    total_wei = 10 * 10**18
    addresses = {'platform': '0xPlatform', 'agent_ops': '0xAgentOps', 'treasury': '0xTreasury'}
    txs = await router.distribute(total_wei, addresses)
    assert len(txs) == 3

@pytest.mark.asyncio
async def test_distribute_zero_amount(router, mock_w3):
    addresses = {'platform': '0xPlatform', 'agent_ops': '0xAgentOps', 'treasury': '0xTreasury'}
    txs = await router.distribute(0, addresses)
    assert len(txs) == 0