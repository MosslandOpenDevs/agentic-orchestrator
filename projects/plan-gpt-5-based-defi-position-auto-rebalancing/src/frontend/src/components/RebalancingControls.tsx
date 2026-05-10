import React, { useState, useEffect } from 'react';

interface RebalancingControlsProps {
  // No props needed for this simple component
}

const RebalancingControls: React.FC<RebalancingControlsProps> = () => {
  const [aggressiveness, setAggressiveness] = useState(50);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading data
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Replace with actual data fetching logic
        await new Promise(resolve => setTimeout(resolve, 1500));
        // Simulate success
        setIsLoading(false);
      } catch (err) {
        setError('Failed to load rebalancing controls.');
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleAggressivenessChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value, 10);
    if (!isNaN(newValue)) {
      setAggressiveness(newValue);
    }
  };

  const handleRebalanceClick = () => {
    // Replace with actual rebalancing logic
    console.log('Rebalancing triggered with aggressiveness:', aggressiveness);
    // Simulate a success
    alert('Rebalancing triggered!');
  };

  return (
    <div className="bg-gray-100 p-6 rounded-lg shadow-md w-full md:w-1/2">
      <h2 className="text-xl font-semibold mb-4">Rebalancing Controls</h2>

      {isLoading && <p className="text-center text-gray-500">Loading...</p>}

      {error && <p className="text-center text-red-500 italic">{error}</p>}

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Aggressiveness:</label>
        <input
          type="range"
          min="0"
          max="100"
          value={aggressiveness}
          onChange={handleAggressivenessChange}
          className="w-full appearance-none h-3 rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Rebalancing Aggressiveness"
          role="alertslider"
        />
      </div>

      <button
        onClick={handleRebalanceClick}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full"
        aria-label="Rebalance Portfolio"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            handleRebalanceClick();
          }
        }}
      >
        Rebalance Portfolio
      </button>
    </div>
  );
};

export default RebalancingControls;