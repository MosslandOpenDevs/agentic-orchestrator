import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { FaArrowDown, FaArrowUp } from 'react-icons/fa';
import {
  Chart as ChartJs,
  LineElement,
  CategoryScale,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Dummy Data (Replace with actual data fetching)
interface ContractDetails {
  name: string;
  address: string;
  contractSourceCode: string;
  vulnerabilities: Vulnerability[];
}

interface Vulnerability {
  id: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  solution: string;
}

const Dashboard = () => {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [contractDetails, setContractDetails] = useState<ContractDetails | null>(null);

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      const dummyContract: ContractDetails = {
        name: 'Cerberus',
        address: '0x...',
        contractSourceCode: '// Dummy contract code...',
        vulnerabilities: [
          { id: 'v1', severity: 'high', description: 'Critical vulnerability', solution: 'Implement fix' },
          { id: 'v2', severity: 'medium', description: 'Medium vulnerability', solution: 'Patch code' },
        ],
      };
      setContractDetails(dummyContract);
      setLoading(false);
    }, 1500);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!contractDetails) {
    return <div>Error loading data.</div>;
  }

  const riskDashboardData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Risk Level',
        data: [5, 8, 3, 7, 12],
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
      },
    ],
  };

  const vulnerabilityChartData = {
    labels: ['Vulnerability 1', 'Vulnerability 2'],
    datasets: [
      {
        label: 'Severity',
        data: ['High', 'Medium'],
        backgroundColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)'],
        hoverOffset: 4,
      },
    ],
  };

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-white shadow-md p-4 flex items-center justify-between">
        <h1>Cerberus Dashboard</h1>
        <nav>
          <a href="#" className="text-gray-600 hover:text-gray-800">
            Overview
          </a>
          <a href="#" className="text-gray-600 hover:text-gray-800">
            Reports
          </a>
          <a href="#" className="text-gray-600 hover:text-gray-800">
            Settings
          </a>
        </nav>
      </header>

      <main className="mt-8 p-4">
        {/* Risk Dashboard */}
        <div className="mb-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Risk Dashboard</h2>
          <Line data={riskDashboardData} className="w-full h-48" />
        </div>

        {/* Vulnerability Report Card */}
        <div className="mb-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Vulnerability Report</h2>
          <div className="p-4">
            {contractDetails.vulnerabilities.map((vulnerability) => (
              <div
                key={vulnerability.id}
                className="bg-white rounded-md shadow-sm p-4 mb-2"
              >
                <h3 className="font-semibold mb-2">{vulnerability.id}</h3>
                <p className="text-gray-700">Severity: {vulnerability.severity}</p>
                <p className="text-gray-700">{vulnerability.description}</p>
                <p className="text-gray-700">Solution: {vulnerability.solution}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Contract Details Page (Placeholder) */}
        <div className="mb-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Contract Details</h2>
          <p>Contract Name: {contractDetails.name}</p>
          <p>Contract Address: {contractDetails.address}</p>
          <pre className="bg-gray-100 p-4 rounded-md">
            <code>{contractDetails.contractSourceCode}</code>
          </pre>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;