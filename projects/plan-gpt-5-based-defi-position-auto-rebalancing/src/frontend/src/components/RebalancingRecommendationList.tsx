import React, { useState, useEffect } from 'react';

interface RebalancingRecommendation {
  id: string;
  asset: string;
  percentage: number;
  description: string;
  status: 'pending' | 'accepted' | 'rejected';
}

interface RebalancingRecommendationListProps {
  recommendations: RebalancingRecommendation[];
  onAcceptRecommendation: (id: string) => void;
  onRejectRecommendation: (id: string) => void;
}

const RebalancingRecommendationList: React.FC<RebalancingRecommendationListProps> = ({
  recommendations,
  onAcceptRecommendation,
  onRejectRecommendation,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    try {
      // Simulate fetching recommendations from an API
      // Replace this with your actual API call
      // const fetchedRecommendations = [
      //   { id: '1', asset: 'BTC', percentage: 0.2, description: 'Increase Bitcoin allocation', status: 'pending' },
      //   { id: '2', asset: 'ETH', percentage: 0.1, description: 'Increase Ethereum allocation', status: 'pending' },
      // ];
      // setTimeout(() => {
      //   setLoading(false);
      //   // Set fetchedRecommendations to recommendations
      // }, 500);
    } catch (err) {
      setError('Failed to load recommendations.');
      setLoading(false);
    }
  }, []);

  if (loading) {
    return <div>Loading recommendations...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <ul
      className="list-group"
      aria-label="Rebalancing Recommendations"
      role="list"
    >
      {recommendations.map((recommendation) => (
        <li
          key={recommendation.id}
          className="list-group-item"
          role="listitem"
          tabIndex={0}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              onAcceptRecommendation(recommendation.id);
            } else if (e.key === ' ') {
              onAcceptRecommendation(recommendation.id);
            }
          }}
        >
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <strong className="text-primary">{recommendation.asset}</strong> - {recommendation.percentage}%
            </div>
            <div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onAcceptRecommendation(recommendation.id)}
                aria-label={`Accept recommendation for ${recommendation.asset}`}
              >
                Accept
              </button>
              <button
                className="btn btn-danger btn-sm"
                onClick={() => onRejectRecommendation(recommendation.id)}
                aria-label={`Reject recommendation for ${recommendation.asset}`}
              >
                Reject
              </button>
            </div>
          </div>
          <p className="text-muted small">{recommendation.description}</p>
        </li>
      ))}
    </ul>
  );
};

export default RebalancingRecommendationList;