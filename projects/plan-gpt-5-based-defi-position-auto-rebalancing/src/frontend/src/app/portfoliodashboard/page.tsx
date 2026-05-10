import React, { useState, useEffect } from 'react';
import { useServer } from '../../api/useServer'; // Assuming API server is in a separate file
import { PortfolioHolding } from '../../types';

const PortfolioDashboard = () => {
  const { portfolio, loading, error } = useServer();
  const [rebalanceAmount, setRebalanceAmount] = useState<number>(0);

  const handleRebalance = () => {
    // Simulate rebalancing logic - replace with actual implementation
    console.log('Rebalancing by:', rebalanceAmount);
    // Call API to execute rebalancing
  };

  if (loading) return <div>Loading portfolio...</div>;
  if (error) return <div>Error loading portfolio: {error}</div>;

  const totalPortfolioValue = portfolio?.holdings?.reduce((sum, holding) => sum + holding.value, 0) || 0;

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      <div className="mb-4">
        <p className="text-gray-700">Total Portfolio Value: <span className="font-semibold">
          ${totalPortfolioValue.toFixed(2)}
        </span></p>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Rebalance Amount:</label>
        <input
          type="number"
          className="form-control text-sm rounded-md shadow-outline"
          value={rebalanceAmount}
          onChange={(e) => setRebalanceAmount(parseFloat(e.target.value))}
        />
      </div>

      <button
        onClick={handleRebalance}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full max-w-sm"
        aria-label="Rebalance Portfolio"
      >
        Rebalance Portfolio
      </button>

      <h2 className="text-xl font-bold mb-4">NFT Holdings</h2>
      {portfolio?.holdings?.map((holding) => (
        <div key={holding.tokenId} className="mb-2">
          <p className="text-gray-700">NFT ID: {holding.tokenId}</p>
          <p className="text-gray-700">Name: {holding.name}</p>
          <p className="text-gray-700">Value: ${holding.value.toFixed(2)}</p>
        </div>
      ))}
    </div>
  );
};

export default PortfolioDashboard;