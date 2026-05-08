import React, { useState, useEffect } from 'react';
import { Chart } from 'chart.js';
import { Line } from 'react-chartjs-2';

// Dummy Data (Replace with actual data fetching)
interface NFTCollection {
  name: string;
  price: number;
  volume: number;
  sentimentScore: number;
}

const dummyNFTCollections: NFTCollection[] = [
  { name: 'Mossland NFT', price: 1500, volume: 12000, sentimentScore: 0.8 },
  { name: 'Pixelverse', price: 800, volume: 8000, sentimentScore: 0.6 },
  { name: 'MetaMoon', price: 2200, volume: 18000, sentimentScore: 0.9 },
];

const PortfolioDashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<NFTCollection | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [theme, setTheme] = useState<string>("light"); // "light" or "dark"

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      const randomCollection = dummyNFTCollections[Math.floor(Math.random() * dummyNFTCollections.length)];
      setPortfolio(randomCollection);
      setRiskAssessment(Math.random() * 10);
      setIsLoading(false);
    }, 1500);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  const data = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Risk Assessment',
        data: [5, 8, 12, 15, 13],
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }
    ]
  };

  return (
    <div className={`min-h-screen ${theme === 'light' ? 'bg-gray-100' : 'bg-gray-800'}`}>
      <header className="bg-gray-100 shadow-md p-4 flex items-center justify-between">
        <button onClick={toggleTheme} className="text-gray-500 hover:text-gray-800">
          {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
        </button>
        {/* Navigation would go here */}
      </header>

      <div className="container mx-auto p-4">
        {isLoading ? (
          <div className="text-center mt-8">Loading portfolio data...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Portfolio Overview Card */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-semibold mb-4">Portfolio</h2>
              <p className="text-gray-700">NFT Collection: {portfolio?.name}</p>
              <p className="text-gray-700">Price: ${portfolio?.price}</p>
              <p className="text-gray-700">Volume: {portfolio?.volume}</p>
              <p className="text-gray-700">Sentiment Score: {portfolio?.sentimentScore}</p>
            </div>

            {/* Risk Assessment Chart */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-semibold mb-4">Risk Assessment</h2>
              <Line data={data} className={`rounded-xl shadow-md`} />
            </div>

            {/* NFT Collection Details (Placeholder) */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-semibold mb-4">NFT Collection Details</h2>
              {/* Display detailed information about a specific NFT collection */}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioDashboard;