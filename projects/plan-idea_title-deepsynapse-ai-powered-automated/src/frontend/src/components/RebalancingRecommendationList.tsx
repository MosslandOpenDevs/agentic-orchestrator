import React, { useState, useEffect } from 'react';
import { useDebounce } from 'use-lodash-debounce';
import { SortDirection } from '../types/sort'; // Assuming this exists

interface RebalancingRecommendation {
  id: string;
  securityToken: string;
  recommendationDate: Date;
  // Add other relevant fields here
}

interface RebalancingRecommendationListProps {
  recommendations: RebalancingRecommendation[];
  onFilterSecurityToken?: (token: string) => void;
  onSort?: (sortDirection: SortDirection) => void;
}

const RebalancingRecommendationList: React.FC<RebalancingRecommendationListProps> = ({
  recommendations,
  onFilterSecurityToken,
  onSort,
}) => {
  const [filteredRecommendations, setFilteredRecommendations] = useState<RebalancingRecommendation[]>(
    recommendations
  );
  const [sortDirection, setSortDirection] = useState<SortDirection | null>(null);

  const debouncedFilter = useDebounce((token: string) => {
    if (token) {
      setFilteredRecommendations(
        recommendations.filter((rec) => rec.securityToken.toLowerCase().includes(token.toLowerCase()))
      );
    } else {
      setFilteredRecommendations(recommendations);
    }
  }, 250);

  useEffect(() => {
    debouncedFilter(recommendations[0]?.securityToken || '');
  }, [recommendations, debouncedFilter]);

  useEffect(() => {
    if (sortDirection !== null) {
      onSort && onSort({ direction: sortDirection, field: 'recommendationDate' });
      setSortDirection(null);
    }
  }, [sortDirection, onSort]);

  const handleSort = (field: string) => {
    if (sortDirection === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortDirection(field);
    }
  };

  return (
    <div className="max-w-screen-md mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Rebalancing Recommendations</h2>

      {/* Filtering */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter by Security Token..."
          className="px-3 py-2 border rounded w-full"
          onChange={(e) => {
            debouncedFilter(e.target.value);
          }}
        />
      </div>

      {/* Sorting */}
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => handleSort('recommendationDate')}
          className={`px-3 py-2 border rounded ${
            sortDirection === 'recommendationDate'
              ? 'bg-gray-200'
              : ''
          }`}
          aria-label="Sort by Recommendation Date"
        >
          Sort by Date
        </button>
      </div>

      {/* List */}
      <ul
        className={`list-sortable rounded-md ${
          filteredRecommendations.length === 0
            ? 'hidden'
            : ''
        }`}
        aria-label="Rebalancing Recommendations"
      >
        {filteredRecommendations.map((rec) => (
          <li
            key={rec.id}
            className={`rounded-md p-4 border shadow-sm ${
              sortDirection === 'recommendationDate' &&
              rec.recommendationDate < new Date()
                ? 'text-gray-500'
                : ''
            }`}
            role="listitem"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === ' ') {
                // Handle spacebar for keyboard navigation (optional)
              }
            }}
          >
            <p>Security Token: {rec.securityToken}</p>
            <p>Recommendation Date: {rec.recommendationDate.toLocaleDateString()}</p>
            {/* Add more details here */}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RebalancingRecommendationList;