import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface RiskMetric {
  name: string;
  value: number;
  threshold: number;
}

interface RiskMonitoringPanelProps {
  metrics: RiskMetric[];
  thresholds: Record<string, number>;
}

const RiskMonitoringPanel: React.FC<RiskMonitoringPanelProps> = ({ metrics, thresholds }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, [metrics, thresholds]);

  const handleThresholdChange = (metricName: string, newValue: number) => {
    // Update thresholds (replace with actual update logic)
    const updatedThresholds = { ...thresholds };
    updatedThresholds[metricName] = newValue;
    setError(null);
    setLoading(true); // Refresh to reflect changes
    // Simulate update
    setTimeout(() => {
      setLoading(false);
    }, 200);
  };

  const checkRisk = (metric: RiskMetric) => {
    if (metric.value > metric.threshold) {
      toast(`Alert: ${metric.name} exceeds threshold (${metric.threshold})`, {
        type: 'warning',
        position: 'top-right',
        autoClose: 5000,
      });
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-lg font-bold text-gray-700">Risk Monitoring</div>
        <p className="text-sm text-gray-600">Loading metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-lg font-bold text-red-700">Error</div>
        <p className="text-sm text-red-600">Failed to load metrics: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
      <div className="text-lg font-bold text-gray-700">Risk Monitoring</div>
      {metrics.map((metric) => (
        <div
          key={metric.name}
          className="bg-white p-3 rounded-md shadow-sm mb-2 hover:bg-gray-200"
          aria-label={`Risk monitoring for ${metric.name}`}
        >
          <span className="text-xl font-semibold">{metric.name}:</span>
          <span className="text-lg text-gray-700">{metric.value}</span>
          <span className="text-sm text-gray-600">Threshold: {thresholds[metric.name]}</span>
          <input
            type="number"
            value={thresholds[metric.name]}
            onChange={(e) => handleThresholdChange(metric.name, parseFloat(e.target.value) || 0)}
            className="mt-2 w-full text-sm rounded p-1"
            aria-label={`Change threshold for ${metric.name}`}
          />
        </div>
      ))}
    </div>
  );
};

export default RiskMonitoringPanel;