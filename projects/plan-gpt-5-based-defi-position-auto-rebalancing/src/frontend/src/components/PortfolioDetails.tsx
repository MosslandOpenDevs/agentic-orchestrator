import React, { useState, useEffect } from 'react';
import { useMediaQuery } from 'react-use';

interface PortfolioDetailsProps {
  portfolioId: string;
}

const PortfolioDetails = ({ portfolioId }: PortfolioDetailsProps) => {
  const [assetHoldings, setAssetHoldings] = useState<any>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);
  const [rebalancingRecommendations, setRebalancingRecommendations] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const holdingsData = await fetch(`https://api.example.com/portfolios/${portfolioId}/holdings`).then(res => {
          if (!res.ok) {
            throw new Error(`HTTP error! Status: ${res.status}`);
          }
          return res.json();
        });
        setAssetHoldings(holdingsData);

        const metricsData = await fetch(`https://api.example.com/portfolios/${portfolioId}/metrics`).then(res => {
          if (!res.ok) {
            throw new Error(`HTTP error! Status: ${res.status}`);
          }
          return res.json();
        });
        setPerformanceMetrics(metricsData);

        const recommendationsData = await fetch(`https://api.example.com/portfolios/${portfolioId}/recommendations`).then(res => {
          if (!res.ok) {
            throw new Error(`HTTP error! Status: ${res.status}`);
          }
          return res.json();
        });
        setRebalancingRecommendations(recommendationsData);

      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [portfolioId]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading portfolio details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Error loading portfolio details: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md flex">
      <div className="md:w-6/12">
        <h2 className="text-xl font-bold mb-4">Portfolio Details</h2>

        {assetHoldings && (
          <div>
            <h3 className="text-lg font-semibold mb-2">Asset Holdings</h3>
            <p>Asset holdings data will be displayed here.</p>
          </div>
        )}

        {performanceMetrics && (
          <div>
            <h3 className="text-lg font-semibold mb-2">Performance Metrics</h3>
            <p>Performance metrics data will be displayed here.</p>
          </div>
        )}

        {rebalancingRecommendations && (
          <div>
            <h3 className="text-lg font-semibold mb-2">Rebalancing Recommendations</h3>
            <p>Rebalancing recommendations data will be displayed here.</p>
          </div>
        )}
      </div>

      <div className="md:w-6/12">
        {/* Placeholder for charts or more detailed visualizations */}
        <p>Detailed visualizations and charts will be added here.</p>
      </div>
    </div>
  );
};

export default PortfolioDetails;