import React, { useState, useEffect } from 'react';

interface PortfolioDetailsProps {
  portfolioData: PortfolioData | null;
  isLoading: boolean;
  error?: string | null;
}

interface PortfolioData {
  assetHoldings: AssetHolding[];
  performanceMetrics: PerformanceMetric[];
  riskAssessment: RiskAssessment;
}

interface AssetHolding {
  assetName: string;
  quantity: number;
  price: number;
  totalValue: number;
}

interface PerformanceMetric {
  startDate: string;
  endDate: string;
  returnPercentage: number;
  benchmarkReturnPercentage?: number;
}

interface RiskAssessment {
  riskScore: number;
  riskCategory: string;
  description: string;
}

const PortfolioDetails: React.FC<PortfolioDetailsProps> = ({
  portfolioData,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md">
        <div className="text-center">
          <p>Loading Portfolio Details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md text-red-700">
        <div className="text-center">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md">
        <div className="text-center">
          <p>No portfolio data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-center">Portfolio Details</h2>

      {/* Asset Holdings */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-2">Asset Holdings</h3>
        {portfolioData.assetHoldings.map((holding) => (
          <div key={holding.assetName} className="mb-2">
            <p className="font-semibold">{holding.assetName} ({holding.quantity})</p>
            <p className="text-gray-600">Price: ${holding.price.toFixed(2)}</p>
            <p className="text-gray-600">Total Value: ${holding.totalValue.toFixed(2)}</p>
          </div>
        ))}
      </div>

      {/* Performance Metrics */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-2">Performance Metrics</h3>
        {portfolioData.performanceMetrics.map((metric) => (
          <div key={metric.startDate} className="mb-2">
            <p className="font-semibold">{metric.startDate} - {metric.endDate}</p>
            <p className="text-gray-600">Return: {metric.returnPercentage.toFixed(2)}%</p>
            {metric.benchmarkReturnPercentage && (
              <p className="text-gray-600">Benchmark Return: {metric.benchmarkReturnPercentage.toFixed(2)}%</p>
            )}
          </div>
        ))}
      </div>

      {/* Risk Assessment */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-2">Risk Assessment</h3>
        <p className="font-semibold">{portfolioData.riskAssessment.riskCategory}</p>
        <p className="text-gray-600">{portfolioData.riskAssessment.description}</p>
        <p className="text-gray-600">Risk Score: {portfolioData.riskAssessment.riskScore}</p>
      </div>
    </div>
  );
};

export default PortfolioDetails;