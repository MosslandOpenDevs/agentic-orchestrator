import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { EtherscanContract } from '../abis/EtherscanContract'; // Replace with your ABI
import { ethers } from 'ethers';

const App = () => {
  const { tailwind } = useTailwind();
  const [contractAddress, setContractAddress] = useState<string>('');
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [contractDetails, setContractDetails] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  useEffect(() => {
    const initialize = async () => {
      try {
        // Replace with your contract address
        const contract = new EtherscanContract(
          '0x...', // Replace with your contract address
          new ethers.providers.Web3Provider(window.ethereum)
        );

        const score = await contract.getRiskScore();
        setRiskScore(score);

        const details = await contract.getContractDetails();
        setContractDetails(details);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    initialize();
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  if (loading) {
    return (
      <div className={`${tailwind.container} ${tailwind.fillHeight} flex items-center justify-center`}>
        <p className={`${tailwind.textBase} text-gray-500`}>
          Loading dashboard...
        </p>
      </div>
    );
  }

  return (
    <div
      className={`${tailwind.container} ${tailwind.fillHeight} transition-colors duration-300 ${darkMode ? 'dark-mode' : ''}`}
    >
      <header className={`${tailwind.bgGray} p-4`}>
        <div className="flex items-center justify-between">
          <h1 className={`${tailwind.textBase} font-bold`}>
            Project Chimera
          </h1>
          <button
            className={`${tailwind.btn} ${tailwind.btnPrimary} px-4 py-2 rounded-md`}
            onClick={toggleDarkMode}
          >
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </header>

      <div className="flex">
        <aside className={`${tailwind.sidebar} ${tailwind.w3/4} ${darkMode ? 'dark-mode-sidebar' : ''}`}>
          {/* Sidebar content */}
          <p className="text-gray-600">Sidebar Content Here</p>
        </aside>

        <main className={`${tailwind.w3/4} ${darkMode ? 'dark-mode-main' : ''}`}>
          <RiskScoreCard riskScore={riskScore} />
          <ContractDetailsView contractDetails={contractDetails} />
          {/* Placeholder for data visualization */}
          <p className="text-gray-600">Data Visualization Placeholder</p>
        </main>
      </div>
    </div>
  );
};

const RiskScoreCard = ({ riskScore }) => {
  return (
    <div className={`${tailwind.card} ${tailwind.shadow-md} rounded-md p-4 ${darkMode ? 'dark-mode-card' : ''}`}>
      <h2 className={`${tailwind.textBase} font-bold`}>Risk Score: {riskScore || 'N/A'}</h2>
      <p className="text-gray-600">
        This score represents the assessed risk level of the contract.
      </p>
    </div>
  );
};

const ContractDetailsView = ({ contractDetails }) => {
  return (
    <div className={`${tailwind.card} ${tailwind.shadow-md} rounded-md p-4 ${darkMode ? 'dark-mode-card' : ''}`}>
      <h2 className={`${tailwind.textBase} font-bold`}>Contract Details</h2>
      {contractDetails && (
        <pre className="code-block p-2 rounded-md bg-gray-100">
          <code>{JSON.stringify(contractDetails, null, 2)}</code>
        </pre>
      )}
    </div>
  );
};

export default App;