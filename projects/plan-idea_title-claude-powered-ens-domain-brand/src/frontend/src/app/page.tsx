import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeftOnCircleIcon } from '@heroicons/react/24/solid';
import { useDarkMode } from './useDarkMode'; // Assuming you have this hook

// Mock Data - Replace with actual data fetching
interface ENSDomain {
  name: string;
  tokenId: string;
  imageUrl: string;
}

interface ClaudeAsset {
  name: string;
  imageUrl: string;
}

const Dashboard = () => {
  const router = useRouter();
  const [darkMode, setDarkMode] = useDarkMode();

  // Mock data - replace with API calls
  const ensDomains: ENSDomain[] = [
    { name: 'mossland-alpha', tokenId: '1', imageUrl: '/images/domain1.png' },
    { name: 'mossland-beta', tokenId: '2', imageUrl: '/images/domain2.png' },
    { name: 'mossland-gamma', tokenId: '3', imageUrl: '/images/domain3.png' },
  ];

  const claudeAssets: ClaudeAsset[] = [
    { name: 'ClaudeAsset1', imageUrl: '/images/claudeAsset1.png' },
    { name: 'ClaudeAsset2', imageUrl: '/images/claudeAsset2.png' },
  ];

  if (router.pathname === '/') {
    router.push('/dashboard');
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : 'light'} flex flex-col`}>
      <header className="bg-gray-100 p-4 flex items-center justify-between">
        <span className="text-xl font-bold">Mossland Dashboard</span>
        <button className="text-gray-500 hover:text-gray-800">
          <ArrowLeftOnCircleIcon />
        </button>
      </header>

      <main className="flex-grow p-4">
        {/* Dashboard Content */}
        <section className="md:flex md:space-x-4">
          {/* Widget 1: Domain List */}
          <div className="md:w-1/2 p-4 border border-gray-300 rounded-md">
            <h3 className="text-lg font-semibold mb-4">ENS Domains</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {ensDomains.map((domain) => (
                <div key={domain.tokenId} className="bg-white rounded-md shadow-md p-4 hover:shadow-lg">
                  <img src={domain.imageUrl} alt={domain.name} className="w-full h-24 object-cover rounded-md" />
                  <p className="text-gray-700 font-medium mt-2">{domain.name}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Widget 2: Claude Asset Preview */}
          <div className="md:w-1/2 p-4 border border-gray-300 rounded-md">
            <h3 className="text-lg font-semibold mb-4">Claude Asset Preview</h3>
            <div className="grid grid-cols-1 gap-4">
              {claudeAssets.map((asset) => (
                <div key={asset.name} className="bg-white rounded-md shadow-md p-4 hover:shadow-lg">
                  <img src={asset.imageUrl} alt={asset.name} className="w-full h-24 object-cover rounded-md" />
                  <p className="text-gray-700 font-medium mt-2">{asset.name}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;