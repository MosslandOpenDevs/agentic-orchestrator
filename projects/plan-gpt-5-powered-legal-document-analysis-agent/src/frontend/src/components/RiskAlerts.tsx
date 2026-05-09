import React, { useState, useEffect } from 'react';

interface RiskAlert {
  id: string;
  severity: 'low' | 'medium' | 'high';
  asset: string;
  description: string;
  recommendation?: string;
}

interface RiskAlertsProps {
  alerts: RiskAlert[];
  isLoading: boolean;
  error?: string;
}

const RiskAlerts: React.FC<RiskAlertsProps> = ({ alerts, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow">
        <div className="text-center text-gray-700">
          Loading Risk Alerts...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded shadow">
        <div className="text-center text-red-700">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-screen-md mx-auto p-4 rounded shadow">
      {alerts.length > 0 && (
        <ul className="list-disc list-inside text-gray-700">
          {alerts.map((alert) => (
            <li
              key={alert.id}
              className="p-2 border-b border-gray-200"
              aria-label={`Risk alert for ${alert.asset}`}
            >
              <strong className="font-semibold text-gray-800">{alert.asset}</strong> - {alert.severity}
              <p>{alert.description}</p>
              {alert.recommendation && (
                <p className="text-green-500">Recommendation: {alert.recommendation}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default RiskAlerts;