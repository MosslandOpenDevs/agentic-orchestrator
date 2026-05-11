import React, { useState, useEffect, useRef } from 'react';
import { Chart, Line } from 'react-chartjs-2';
import { useViewport } from '@uswds/react';

interface RiskScoreVisualizationProps {
  riskScore: number;
  riskScoreDistribution?: { [key: string]: number };
  contractAddress?: string;
}

const RiskScoreVisualization: React.FC<RiskScoreVisualizationProps> = ({
  riskScore,
  riskScoreDistribution,
  contractAddress,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const viewport = useViewport();

  const chartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    if (!chartRef.current) return;

    const data = {
      labels: [],
      datasets: [],
    };

    if (riskScoreDistribution) {
      const labels = Object.keys(riskScoreDistribution);
      const values = Object.values(riskScoreDistribution);

      data.labels = labels;
      data.datasets = [{
        label: 'Risk Score Distribution',
        data: values,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      }];
    }

    if (riskScore) {
      data.datasets.push({
        label: 'Risk Score',
        data: [riskScore],
        fill: false,
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1,
      });
    }

    const options = {
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Risk Score'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Category'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: contractAddress ? `Risk Score for ${contractAddress}` : 'Risk Score Visualization'
        }
      },
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => {
              if (context.dataset.label === 'Risk Score') {
                return `${context.dataset.value}`;
              }
              return `${context.dataset.value}`;
            }
          }
        }
      }
    };

    new Chart(chartRef.current, {
      type: 'line',
      data: data,
      options: options,
    });
  }, [riskScore, riskScoreDistribution, contractAddress, viewport]);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <p>Loading risk score visualization...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div
      className={`w-full h-64 border rounded-lg overflow-hidden`}
      aria-label="Risk Score Visualization"
      tabIndex={0}
      onKeyDown={(e) => {
        // Implement keyboard navigation here if needed
      }}
    >
      <canvas ref={chartRef} />
    </div>
  );
};

export default RiskScoreVisualization;