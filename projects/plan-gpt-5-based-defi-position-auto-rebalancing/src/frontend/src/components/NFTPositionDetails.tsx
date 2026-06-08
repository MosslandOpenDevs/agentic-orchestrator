import React, { useState, useEffect } from 'react';

interface NFTPositionDetailsProps {
  positionId: string;
  asset: {
    name: string;
    symbol: string;
    price: number;
    quantity: number;
  };
  defiProtocol: {
    name: string;
    logoUrl: string;
    riskScore: number;
    liquidityRatios: {
      tvl: number;
      dailyVolume: number;
    };
  };
  riskAssessmentMetrics: {
    volatility: number;
    correlation: number;
    liquidity: number;
  };
}

const NFTPositionDetails: React.FC<NFTPositionDetailsProps> = ({
  positionId,
  asset,
  defiProtocol,
  riskAssessmentMetrics,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    try {
      // Simulate fetching data - Replace with actual API calls
      // This is just a placeholder for demonstration
    } catch (err) {
      setError('Failed to load position details.');
      setLoading(false);
    } finally {
      setLoading(false);
    }
  }, [positionId]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
        <div className="text-center">Loading position details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md w-full max-w-md">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-md shadow-md w-full max-w-md">
      <h2 className="text-xl font-bold mb-4">NFT Position Details</h2>

      <div className="mb-4">
        <h3 className="font-semibold mb-2">Asset Holdings</h3>
        <p className="text-gray-700">
          {asset.name} ({asset.symbol}) - Price: ${asset.price.toFixed(2)} - Quantity: {asset.quantity}
        </p>
      </div>

      <div className="mb-4">
        <h3 className="font-semibold mb-2">DeFi Protocol Details</h3>
        <img
          src={defiProtocol.logoUrl}
          alt={`${defiProtocol.name} Logo`}
          aria-label={`${defiProtocol.name} Logo`}
          className="w-16 h-16 mb-2 rounded-full"
        />
        <p className="text-gray-700">
          {defiProtocol.name} - Risk Score: {defiProtocol.riskScore.toFixed(2)} - TVL: ${defiProtocol.liquidityRatios.tvl.toFixed(2)} - Daily Volume: ${defiProtocol.liquidityRatios.dailyVolume.toFixed(2)}
        </p>
      </div>

      <div className="mb-4">
        <h3 className="font-semibold mb-2">Risk Assessment Metrics</h3>
        <p className="text-gray-700">
          Volatility: {riskAssessmentMetrics.volatility.toFixed(2)} - Correlation: {riskAssessmentMetrics.correlation.toFixed(2)} - Liquidity: {riskAssessmentMetrics.liquidity.toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export default NFTPositionDetails;