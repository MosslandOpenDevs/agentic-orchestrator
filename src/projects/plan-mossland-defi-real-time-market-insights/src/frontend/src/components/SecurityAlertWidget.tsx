import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface SecurityAlert {
  id: number;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
}

interface Props {
  userId: number;
}

const SecurityAlertWidget: React.FC<Props> = ({ userId }) => {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await axios.get(`/api/alerts/${userId}`);
        setAlerts(response.data);
      } catch (err) {
        setError('Failed to load security alerts');
      }
      setLoading(false);
    };

    fetchAlerts();
  }, [userId]);

  if (loading) return <div className="text-center">Loading...</div>;
  if (error) return <div role="alert" aria-label={error} className="text-red-500 text-center">{error}</div>;

  return (
    <div className="bg-white shadow-md rounded-lg p-4 max-w-sm w-full">
      <h2 className="text-xl font-bold mb-4">Security Alerts</h2>
      {alerts.length === 0 ? (
        <p role="alert" aria-label="No active alerts" className="text-center text-gray-500">No active alerts.</p>
      ) : (
        <ul className="space-y-3">
          {alerts.map((alert) => (
            <li key={alert.id} className={`flex items-start space-x-2 ${alert.severity === 'high' ? 'text-red-500' : ''}`}>
              <button
                onClick={() => alertDetails(alert)}
                role="link"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && alertDetails(alert)}
                className={`flex-grow p-2 rounded-lg hover:bg-gray-100 focus:outline-none`}
                aria-label={`View details for ${alert.title}`}
              >
                <span>{alert.title}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  function alertDetails(alert: SecurityAlert) {
    // Placeholder for opening a modal or navigating to an alert detail page
    console.log(`Viewing details for ${alert.title}`);
  }
};

export default SecurityAlertWidget;