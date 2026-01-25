import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface SentimentAnalysisData {
  sentiment: string;
  score: number;
}

const MosslandCryptoCommunitySentimentSecurityDashboard = () => {
  const [sentimentData, setSentimentData] = useState<SentimentAnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Mock API call to fetch sentiment analysis data
    const fetchData = async () => {
      try {
        const response = await axios.get('https://api.example.com/sentiment');
        setSentimentData(response.data);
      } catch (error) {
        console.error("Error fetching sentiment data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header with navigation */}
      <header className="bg-white shadow dark:bg-gray-800">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Top">
          <div className="w-full py-6 flex items-center justify-between border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <a href="#" className="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500 transition duration-150 ease-in-out">
                Mossland DeFi
              </a>
              <p className="ml-2 text-sm font-medium">Real-Time Market Insights Platform</p>
            </div>
          </div>
        </nav>
      </header>

      {/* Main content area */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading ? (
            <p>Loading...</p>
          ) : sentimentData ? (
            <>
              {/* Sentiment Analysis Card */}
              <div className="bg-white rounded-lg shadow overflow-hidden dark:bg-gray-800">
                <div className="px-4 py-5 sm:p-6 text-center">
                  <dt className="text-sm font-medium text-gray-500 truncate dark:text-gray-400">Sentiment</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">{sentimentData.sentiment}</dd>
                </div>
              </div>

              {/* Security Alert Widget */}
              <SecurityAlertWidget />
            </>
          ) : (
            <p>No data available</p>
          )}
        </div>
      </main>
    </div>
  );
};

const SecurityAlertWidget = () => {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden dark:bg-gray-800">
      <div className="px-4 py-5 sm:p-6 text-center">
        <dt className="text-sm font-medium text-gray-500 truncate dark:text-gray-400">Security Alerts</dt>
        <dd className="mt-1 text-xl font-semibold text-red-600 dark:text-red-300">No active alerts</dd>
      </div>
    </div>
  );
};

export default MosslandCryptoCommunitySentimentSecurityDashboard;