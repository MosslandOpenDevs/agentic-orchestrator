import React, { useState, useEffect, useRef } from 'react';
import { Chart, Line } from 'react-chartjs-2';
import { useViewport } from '@usvillas/use-viewport';

interface RiskAnalysisChartProps {
  data: {
    labels: string[];
    values: number[];
  };
  riskThreshold: number;
}

const RiskAnalysisChart: React.FC<RiskAnalysisChartProps> = ({ data, riskThreshold }) => {
  const [chartData, setChartData] = useState<any>();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLCanvasElement>(null);
  const { width } = useViewport();

  useEffect(() => {
    setLoading(true);
    setError(null);

    const chart = new Chart(chartRef.current, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [
          {
            label: 'Volatility',
            data: data.values,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Time'
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: 'Volatility'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: 'Portfolio Volatility',
            font: {
              size: 16
            }
          }
        },
        animation: false
      },
    });

    setChartData(chart);

    return () => {
      if (chart) {
        chart.destroy();
      }
    };
  }, [data, riskThreshold]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const riskLevel = data.values.length > 0 ? data.values.reduce((max, val) => Math.max(max, val), 0) > riskThreshold ? 'High' : 'Medium' : 'Low';

  return (
    <div className="relative w-full" aria-label="Portfolio Volatility Chart" tabIndex={0} >
      <canvas ref={chartRef} width={width} height={300} />
      <div className="absolute bottom-0 left-0 w-full bg-gray-800 text-white font-medium p-2">
        Risk Level: {riskLevel}
      </div>
    </div>
  );
};

export default RiskAnalysisChart;