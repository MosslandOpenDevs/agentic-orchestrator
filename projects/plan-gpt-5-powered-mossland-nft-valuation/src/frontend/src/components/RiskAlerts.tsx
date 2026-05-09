import React, { useState, useEffect } from 'react';
import { useAlert } from 'react-alert'; // Import react-alert
import { Alert } from 'react-alert';

interface RiskAlert {
  assetId: string;
  riskLevel: number;
  message: string;
}

interface RiskAlertsProps {
  alerts: RiskAlert[];
  isLoading: boolean;
  error?: string;
}

const RiskAlerts: React.FC<RiskAlertsProps> = ({ alerts, isLoading, error }) => {
  const [alertState, setAlertState] = useState<Alert>({});
  const alert = useAlert();

  useEffect(() => {
    if (error) {
      alertState.setState({ alertText: error, type: 'error', duration: 3000 });
    }
  }, [error]);

  if (isLoading) {
    return <div>Loading Risk Alerts...</div>;
  }

  if (error) {
    return <div>Error loading risk alerts: {error}</div>;
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow-md overflow-x-auto max-w-screen-xl">
      {alerts.length === 0 && <p className="text-gray-500 text-center">No risk alerts found.</p>}
      <table className="table table-striped">
        <thead>
          <tr>
            <th className="text-left">Asset ID</th>
            <th className="text-left">Risk Level</th>
            <th className="text-left">Alert</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.assetId} aria-label={`Risk alert for asset ${alert.assetId}`}>
              <td className="text-left">{alert.assetId}</td>
              <td className="text-left">
                <span className="bg-red-200 text-red-500 px-2 py-1 rounded-md" style={{ fontSize: '1rem' }}>
                  {alert.riskLevel}
                </span>
              </td>
              <td className="text-left">{alert.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RiskAlerts;