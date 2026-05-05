import React, { useState, useEffect } from 'react';
import { useDebounce } from 'react-use';

interface RiskAssessmentWidgetProps {
  portfolioData: PortfolioData;
  isLoading: boolean;
  error?: string;
  width?: string;
  height?: string;
}

interface PortfolioData {
  assets: Asset[];
}

interface Asset {
  name: string;
  riskScore: number;
  percentage: number;
}

const RiskAssessmentWidget: React.FC<RiskAssessmentWidgetProps> = ({
  portfolioData,
  isLoading,
  error,
  width = '300px',
  height = '200px',
}) => {
  const [riskScore, setRiskScore] = useState<number>(0);
  const [riskDistribution, setRiskDistribution] = useState<Asset[]>([]);
  const debouncedUpdate = useDebounce((id: number) => {
    if (portfolioData && portfolioData.assets[id]) {
      setRiskScore(portfolioData.assets[id].riskScore);
      setRiskDistribution(
        portfolioData.assets.map((asset) => ({
          ...asset,
        }))
      );
    }
  }, 200);

  useEffect(() => {
    if (portfolioData && portfolioData.assets) {
      let totalRisk = 0;
      portfolioData.assets.forEach((asset) => {
        totalRisk += asset.riskScore;
      });
      setRiskScore(totalRisk);
      setRiskDistribution(portfolioData.assets);
    }
  }, [portfolioData]);

  useEffect(() => {
    debouncedUpdate(0);
  }, [debouncedUpdate]);

  if (isLoading) {
    return (
      <div
        className={`w-[${width}] h-[${height}] flex items-center justify-center`}
        aria-label="Risk Assessment Widget Loading"
      >
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`w-[${width}] h-[${height}] flex items-center justify-center`}
        aria-label="Risk Assessment Widget Error"
      >
        Error: {error}
      </div>
    );
  }

  if (!portfolioData || !portfolioData.assets) {
    return (
      <div
        className={`w-[${width}] h-[${height}] flex items-center justify-center`}
        aria-label="Risk Assessment Widget Empty Data"
      >
        No data available.
      </div>
    );
  }

  return (
    <div
      className={`w-[${width}] h-[${height}] flex flex-col items-center justify-center rounded-lg shadow-md`}
      aria-label="Risk Assessment Widget"
    >
      <p className="text-xl font-bold mb-4">Risk Score: {riskScore.toFixed(2)}</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {riskDistribution.map((asset, index) => (
          <div
            key={index}
            className={`bg-gray-100 rounded-md shadow-sm p-4 flex items-center justify-around w-full`}
          >
            <p className="text-sm">{asset.name}</p>
            <p className="text-lg">{asset.riskScore.toFixed(2)}</p>
            <p className="text-sm">{asset.percentage}%</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskAssessmentWidget;