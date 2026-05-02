import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useDarkMode } from './useDarkMode'; // Assuming you have this hook

// Placeholder components - replace with actual implementations
import NFTGeneratorForm from './components/NFTGeneratorForm';
import NFTDetailsView from './components/NFTDetailsView';
import UserDashboard from './components/UserDashboard';

const GenesisCanvasDashboard = () => {
  const router = useRouter();
  const [darkMode, setDarkMode] = useDarkMode();

  // Simulate data fetching for demonstration
  const [nftData, setNftData] = useState<any[]>([]);

  useEffect(() => {
    // Simulate fetching NFT data
    const fetchData = async () => {
      // Replace with actual API call
      const data = [
        { id: 1, prompt: 'A majestic dragon', image: 'dragon.png', price: 0.1 },
        { id: 2, prompt: 'A futuristic cityscape', image: 'cityscape.png', price: 0.2 },
      ];
      setNftData(data);
    };

    fetchData();
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <header className="bg-gray-100 shadow-md p-4 flex items-center justify-between">
        <button onClick={toggleDarkMode} className="text-gray-800 focus:outline-none">
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
        <h1 className="text-2xl font-bold">Genesis Canvas</h1>
      </header>

      <div className="flex">
        <aside className="bg-gray-50 p-4 w-64">
          {/* Sidebar content */}
          <nav>
            <ul className="list-none">
              <li className="mb-2">
                <a href="/" className="block p-2 text-gray-700 hover:bg-gray-100">
                  Dashboard
                </a>
              </li>
              <li className="mb-2">
                <a href="/generate" className="block p-2 text-gray-700 hover:bg-gray-100">
                  Generate NFT
                </a>
              </li>
              <li className="mb-2">
                <a href="/details" className="block p-2 text-gray-700 hover:bg-gray-100">
                  NFT Details
                </a>
              </li>
            </ul>
          </nav>
        </aside>

        <main className="p-4 flex-grow">
          {/* Main content area */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Dashboard widgets */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold mb-2">NFT Overview</h2>
              {nftData.length > 0 ? (
                nftData.map((nft) => (
                  <div key={nft.id} className="border-gray-300 p-3 rounded-md mb-3">
                    <img src={nft.image} alt={nft.prompt} className="w-32 h-24 object-cover rounded-md mb-2" />
                    <p className="font-semibold">{nft.prompt}</p>
                    <p className="text-gray-600">Price: ${nft.price}</p>
                  </div>
                ))
              ) : (
                <p>No NFTs found.</p>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold mb-2">Data Visualization Placeholder</h2>
              {/* Placeholder for charts or graphs */}
              <p>Data visualization will go here.</p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold mb-2">User Activity Placeholder</h2>
              {/* Placeholder for user activity stats */}
              <p>User activity stats will go here.</p>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default GenesisCanvasDashboard;