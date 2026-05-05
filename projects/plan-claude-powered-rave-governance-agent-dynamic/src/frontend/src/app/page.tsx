import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { Chart as ChartJS, Title, Label } from 'chart.js';
import { Line } from 'react-chartjs-2';

type PortfolioData = {
  name: string;
  assets: string[];
  value: number;
  riskScore: number;
};

type RiskAssessmentData = {
  level: string;
  description: string;
};

const App = () => {
  const tailwind = useTailwind();
  const [loading, setLoading] = useState(true);
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentData | null>(null);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      const data: PortfolioData = {
        name: 'Mossland Portfolio',
        assets: ['NFT1', 'NFT2', 'NFT3'],
        value: 150000,
        riskScore: 75,
      };
      const assessment: RiskAssessmentData = {
        level: 'Medium',
        description: 'Portfolio exhibits moderate risk due to asset diversification.',
      };

      setPortfolioData(data);
      setRiskAssessment(assessment);
      setLoading(false);
    }, 1500);
  }, []);

  if (loading) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-xl font-bold')}>Loading...</p>
      </div>
    );
  }

  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Value',
        data: [100000, 120000, 150000, 130000, 160000],
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div className={tailwind('min-h-screen bg-gray-100')}>
      <header className={tailwind('bg-white shadow-md p-4')}>
        <h1 className={tailwind('text-3xl font-bold')}>RAVE Governance Agent Dashboard</h1>
        <button
          onClick={() => setDarkMode(!darkMode)}
          className={tailwind(
            darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-700',
            'px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
          )}
        >
          Toggle Dark Mode
        </button>
      </header>

      <div className={tailwind('flex')}>
        <aside className={tailwind('bg-gray-200 p-4 w-64')}>
          {/* Sidebar content */}
          <h2 className={tailwind('text-lg font-semibold mb-2')}>Navigation</h2>
          <ul>
            <li className={tailwind('mb-2')}>
              <a href="#" className={tailwind('block p-2 rounded-md hover:bg-gray-300')}>
                Portfolio Dashboard
              </a>
            </li>
            <li className={tailwind('mb-2')}>
              <a href="#" className={tailwind('block p-2 rounded-md hover:bg-gray-300')}>
                Portfolio Details
              </a>
            </li>
            <li className={tailwind('mb-2')}>
              <a href="#" className={tailwind('block p-2 rounded-md hover:bg-gray-300')}>
                Risk Assessment
              </a>
            </li>
            <li className={tailwind('mb-2')}>
              <a href="#" className={tailwind('block p-2 rounded-md hover:bg-gray-300')}>
                Report Generator
              </a>
            </li>
          </ul>
        </aside>

        <main className={tailwind('p-4 flex')}>
          {/* Main content */}
          <section className={tailwind('w-full')}>
            <h2 className={tailwind('text-2xl font-bold mb-4')}>Portfolio Overview</h2>
            <div className={tailwind('bg-white rounded-md shadow-md p-6')}>
              <p className={tailwind('text-xl font-semibold mb-4')}>
                Name: {portfolioData?.name}
              </p>
              <p className={tailwind('text-lg mb-4')}>
                Value: ${portfolioData?.value}
              </p>
              <p className={tailwind('text-lg mb-4')}>
                Risk Score: {portfolioData?.riskScore}
              </p>
              <p className={tailwind('text-gray-600')}>
                Assets: {portfolioData?.assets.join(', ')}
              </p>
            </div>

            <h2 className={tailwind('text-2xl font-bold mb-4')}>Risk Assessment</h2>
            <div className={tailwind('bg-white rounded-md shadow-md p-6')}>
              <p className={tailwind('text-xl font-semibold mb-4')}>
                Level: {riskAssessment?.level}
              </p>
              <p className={tailwind('text-lg mb-4')}>
                Description: {riskAssessment?.description}
              </p>
            </div>

            <h2 className={tailwind('text-2xl font-bold mb-4')}>
              Portfolio Value Trend
            </h2>
            <Line data={chartData} className={tailwind('w-full h-40')} />
          </section>
        </main>
      </div>
    </div>
  );
};

export default App;