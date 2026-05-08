import React, { useState, useEffect } from 'react';
import { FaArrowDown } from 'react-icons/fa';
import { FaArrowUp } from 'react-icons/fa';
import { useTailwind } from 'tailwind-rn';
import { WebSocket } from 'react-query-worker';

// Placeholder data - replace with actual data fetching
interface ProposalData {
  fullVersion: string;
  estimatedCost: number;
  developmentCost: number;
  infrastructureCost: number;
  gpt5Cost: number;
  totalCost: number;
}

const ProposalDetails = ({ data }: { data: ProposalData }) => {
  const { tailwind } = useTailwind();

  return (
    <div className={`${tailwind('bg-gray-100 p-4 rounded-lg shadow-md')}`}>
      <h3 className={`${tailwind('text-xl font-bold mb-2')}`}>Proposal Details</h3>
      <p className={`${tailwind('text-gray-700')}`}>
        Full Version (16-24 weeks): {data.fullVersion}
      </p>
      <p className={`${tailwind('text-gray-700')}`}>
        Estimated Cost: ${data.estimatedCost}
      </p>
      <div className={`${tailwind('grid grid-cols-1 md:grid-cols-2 gap-4')}`}>
        <div className={`${tailwind('bg-white p-4 rounded-md')}`}>
          <h4 className={`${tailwind('text-lg font-bold mb-2')}`}>Development (MVP)</h4>
          <p className={`${tailwind('text-gray-700')}`}>$50,000 - $80,000</p>
        </div>
        <div className={`${tailwind('bg-white p-4 rounded-md')}`}>
          <h4 className={`${tailwind('text-lg font-bold mb-2')}`}>Infrastructure</h4>
          <p className={`${tailwind('text-gray-700')}`}>$5,000 - $10,000</p>
        </div>
      </div>
      <div className={`${tailwind('grid grid-cols-1 md:grid-cols-2 gap-4')}`}>
        <div className={`${tailwind('bg-white p-4 rounded-md')}`}>
          <h4 className={`${tailwind('text-lg font-bold mb-2')}`}>GPT-5 API Access & Training</h4>
          <p className={`${tailwind('text-gray-700')}`}>$10,000 - $20,000</p>
        </div>
        <div className={`${tailwind('bg-white p-4 rounded-md')}`}>
          <h4 className={`${tailwind('text-lg font-bold mb-2')}`}>Total (MVP)</h4>
          <p className={`${tailwind('text-gray-700')}`}>$65,000 - $110,000</p>
        </div>
      </div>
    </div>
  );
};

const PortfolioDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ProposalData>({
    fullVersion: 'Expand to include advanced features, user interface enhancements, and integration with additional NFT markets.',
    estimatedCost: 0,
    developmentCost: 0,
    infrastructureCost: 0,
    gpt5Cost: 0,
    totalCost: 0,
  });

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setData({
        fullVersion: 'Expand to include advanced features, user interface enhancements, and integration with additional NFT markets.',
        estimatedCost: 50000,
        developmentCost: 80000,
        infrastructureCost: 5000,
        gpt5Cost: 20000,
        totalCost: 110000,
      });
      setLoading(false);
    }, 2000);
  }, []);

  if (loading) {
    return (
      <div className={`${tailwind('flex items-center justify-center h-screen')}`}>
        <FaArrowUp className={`${tailwind('text-4xl rotate-[-45deg] text-gray-500')}`} />
        <p className={`${tailwind('text-2xl text-gray-700')}`}>Loading...</p>
      </div>
    );
  }

  return (
    <div className={`${tailwind('flex min-h-screen')}`}>
      {/* Header */}
      <div className={`${tailwind('bg-white shadow-md p-4')}`}>
        <h1 className={`${tailwind('text-3xl font-bold text-gray-800')}`}>Mossland Agent Dashboard</h1>
      </div>

      {/* Main Content */}
      <div className={`${tailwind('flex-1 p-4')}`}>
        {/* PortfolioDashboard Component */}
        <ProposalDetails data={data} />
      </div>
    </div>
  );
};

export default PortfolioDashboard;