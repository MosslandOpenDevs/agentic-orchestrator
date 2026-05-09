import React, { useState, useEffect } from 'react';
import { useMediaQuery } from 'next/use/media-query';

interface AssetDetailsProps {
  assetId: string;
  assetData: AssetData;
  isLoading: boolean;
  error?: string;
}

interface AssetData {
  name: string;
  price: number;
  historicalPerformance: HistoricalPerformanceData[];
  riskMetrics: RiskMetricsData;
}

interface HistoricalPerformanceData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface RiskMetricsData {
  beta: number;
  volatility: number;
  sharpeRatio: number;
}

const AssetDetails = ({
  assetId,
  assetData,
  isLoading,
  error,
}) => {
  const isSmallScreen = useMediaQuery('(max-width: 768px)');

  if (isLoading) {
    return <div>Loading Asset Details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!assetData) {
    return <div>No asset data available.</div>;
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6 max-w-lg">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">{assetData.name}</h1>

      <div className="mb-4">
        <p className="text-xl font-semibold text-gray-700">Price: ${assetData.price}</p>
      </div>

      <div className="mb-4">
        {isSmallScreen && (
          <p className="text-sm text-gray-600">Historical performance and risk metrics are best viewed on larger screens.</p>
        )}
      </div>

      <div className="mb-4">
        <h2>Historical Performance</h2>
        <table className="table table-striped">
          <thead>
            <tr>
              <th>Date</th>
              <th>Open</th>
              <th>High</th>
              <th>Low</th>
              <th>Close</th>
            </tr>
          </thead>
          <tbody>
            {assetData.historicalPerformance.map((item) => (
              <tr key={item.date}>
                <td>{item.date}</td>
                <td>{item.open}</td>
                <td>{item.high}</td>
                <td>{item.low}</td>
                <td>{item.close}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mb-4">
        <h2>Risk Metrics</h2>
        <div className="flex flex-col md:flex-row">
          <p className="text-xl font-semibold text-gray-700 mr-2">Beta: {assetData.riskMetrics.beta}</p>
          <p className="text-xl font-semibold text-gray-700 mr-2">Volatility: {assetData.riskMetrics.volatility}</p>
          <p className="text-xl font-semibold text-gray-700">Sharpe Ratio: {assetData.riskMetrics.sharpeRatio}</p>
        </div>
      </div>
    </div>
  );
};

export default AssetDetails;