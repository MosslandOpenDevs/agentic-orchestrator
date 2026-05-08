import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface Strategy {
  id: string;
  name: string;
  description: string;
  riskLevel: 'low' | 'medium' | 'high';
  performance: number; // Percentage
  isActive: boolean;
}

interface StrategyListProps {
  strategies: Strategy[];
  loading: boolean;
  error?: string;
}

const StrategyList: React.FC<StrategyListProps> = ({ strategies, loading, error }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const filterByRiskLevel = searchParams.get('riskLevel');
  const sortOrder = searchParams.get('sortOrder') || 'asc';

  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>(strategies);
  const [sortedStrategies, setSortedStrategies] = useState<Strategy[]>(strategies);

  useEffect(() => {
    if (filterByRiskLevel) {
      const filtered = strategies.filter((strategy) =>
        strategy.riskLevel === filterByRiskLevel
      );
      setFilteredStrategies(filtered);
      setSortedStrategies(filtered);
    } else {
      setFilteredStrategies(strategies);
      setSortedStrategies(strategies);
    }
  }, [strategies, filterByRiskLevel]);

  useEffect(() => {
    if (sortOrder === 'desc') {
      setSortedStrategies([...sortedStrategies].sort((a, b) =>
        (a.performance > b.performance) ? 1 : -1
      ));
    } else {
      setSortedStrategies([...sortedStrategies].sort((a, b) =>
        (a.performance > b.performance) ? -1 : 1
      ));
    }
  }, [sortOrder, sortedStrategies.length]);

  if (loading) {
    return <div>Loading strategies...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="max-w-screen-md mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">DAO Strategies</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {sortedStrategies.map((strategy) => (
          <div
            key={strategy.id}
            className={`bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300 ease-in-out`
              + ` ${strategy.isActive ? 'border-green-500' : 'border-red-500'}`
            }
            aria-label={strategy.name}
          >
            <h3 className="text-xl font-semibold mb-2">{strategy.name}</h3>
            <p className="text-gray-700">Risk Level: {strategy.riskLevel}</p>
            <p className="text-gray-700">Performance: {strategy.performance.toFixed(2)}%</p>
            <p className="text-gray-700">{strategy.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Risk Level:</label>
        <div className="flex space-x-3">
          <button
            onClick={() => setSearchParams({ riskLevel: null })}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded-md"
            aria-label="Clear Risk Level Filter"
          >
            All
          </button>
          <button
            onClick={() => setSearchParams({ riskLevel: 'low' })}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded-md"
            aria-label={`Filter by Low Risk Level`}
          >
            Low
          </button>
          <button
            onClick={() => setSearchParams({ riskLevel: 'medium' })}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded-md"
            aria-label={`Filter by Medium Risk Level`}
          >
            Medium
          </button>
          <button
            onClick={() => setSearchParams({ riskLevel: 'high' })}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded-md"
            aria-label={`Filter by High Risk Level`}
          >
            High
          </button>
        </div>
      </div>

      <div className="mt-6">
        <label className="block text-sm font-medium text-gray-700 mb-1">Sort by Performance:</label>
        <select
          onChange={(e) => setSearchParams({ sortOrder: e.target.value })}
          className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded-md"
          aria-label="Sort by Performance"
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
      </div>
    </div>
  );
};

export default StrategyList;