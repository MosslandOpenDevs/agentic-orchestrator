import os

API_KEY = os.getenv('API_KEY')
RPC_URL = os.getenv('RPC_URL')

FEE_SPLIT_CONFIG = {
    'platform_fee_bps': int(os.getenv('PLATFORM_FEE_BPS', 1000)),
    'agent_ops_fee_bps': int(os.getenv('AGENT_OPS_FEE_BPS', 1000)),
    'min_distribution_wei': int(os.getenv('MIN_DISTRIBUTION_WEI', 1000000000000000)),
    'enabled': os.getenv('FEE_SPLIT_ENABLED', 'true').lower() == 'true'
}

DISTRIBUTION_ADDRESSES = {
    'platform': os.getenv('PLATFORM_TREASURY_ADDRESS', '0x0000000000000000000000000000000000000000'),
    'agent_ops': os.getenv('AGENT_OPS_TREASURY_ADDRESS', '0x0000000000000000000000000000000000000000'),
    'treasury': os.getenv('DAO_TREASURY_ADDRESS', '0x0000000000000000000000000000000000000000')
}