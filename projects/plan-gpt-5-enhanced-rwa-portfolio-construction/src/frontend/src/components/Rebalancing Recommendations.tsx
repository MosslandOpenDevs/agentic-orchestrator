import React, { useState, useEffect } from 'react';
import { useMediaQuery } from 'next/useMeta';

interface RebalancingRecommendation {
  asset: string;
  quantityChange: number;
  direction: 'increase' | 'decrease';
}

interface RebalancingRecommendationsProps {
  recommendations: RebalancingRecommendation[];
  isLoading: boolean;
  error?: string;
}

const RebalancingRecommendations: React.FC<RebalancingRecommendationsProps> = ({
  recommendations,
  isLoading,
  error,
}) => {
  const [isSmallScreen, setIsSmallScreen] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 768px)');
    setIsSmallScreen(mediaQuery.matches);

    const handleMediaQueryChange = (event: MediaQueryListEvent) => {
      setIsSmallScreen(event.matches);
    };

    mediaQuery.addEventListener('change', handleMediaQueryChange);

    return () => {
      mediaQuery.removeEventListener('change', handleMediaQueryChange);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-lg font-bold text-gray-700">
          Rebalancing Recommendations Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md text-red-700">
        <p className="text-lg font-bold">Error: {error}</p>
      </div>
    );
  }

  return (
    <div
      className={`bg-white p-4 rounded-lg shadow-md flex flex-col ${
        isSmallScreen ? 'max-w-xs' : 'min-w-48'
      }`}
      aria-label="Rebalancing Recommendations"
    >
      {recommendations.length > 0 ? (
        <div className="text-lg font-bold text-gray-700 mb-4">
          Recommended Rebalancing Actions
        </div>
        <ul className="list-disc text-gray-700">
          {recommendations.map((recommendation) => (
            <li
              key={recommendation.asset}
              className={`rounded-md p-2 mb-2 ${
                recommendation.direction === 'increase'
                  ? 'bg-green-100'
                  : 'bg-red-100'
              } flex items-center`}
              role="region"
              aria-label={`Rebalance ${recommendation.asset}`}
            >
              {recommendation.asset} - {recommendation.quantityChange}
              <span className="text-sm text-gray-500 ml-2">
                {recommendation.direction === 'increase' ? 'Increase' : 'Decrease'}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-lg font-bold text-gray-700 mb-4">
          No rebalancing recommendations available.
        </div>
      )}
    </div>
  );
};

export default RebalancingRecommendations;