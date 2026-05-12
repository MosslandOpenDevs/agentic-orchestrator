import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { WebSocket } from 'ws';

// Placeholder data - replace with actual data fetching
interface ContractData {
  name: string;
  severityScore: number;
  details: string;
}

const dummyContractData: ContractData[] = [
  { name: 'Contract 1', severityScore: 8, details: 'Details for Contract 1' },
  { name: 'Contract 2', severityScore: 3, details: 'Details for Contract 2' },
];

type WebSocketMessage = string;

const DashboardPage = () => {
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';
  const [contractData, setContractData] = useState<ContractData | null>(null);
  const [loading, setLoading] = useState(true);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8080'); // Replace with your WebSocket server URL

      ws.onopen = () => {
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const message = event.data as WebSocketMessage;
        console.log('WebSocket message:', message);
        // Handle incoming messages here - e.g., update contract data
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };

      return ws;
    };

    const disconnectWebSocket = (ws: WebSocket | null) => {
      if (ws) {
        ws.close();
      }
    };

    const initialWs = connectWebSocket();
    setWs(initialWs);

    return () => {
      disconnectWebSocket(initialWs);
      disconnectWebSocket(ws);
    };
  }, []);


  useEffect(() => {
    if (contractId) {
      const contract = dummyContractData.find((c) => c.name === contractId);
      setContractData(contract);
    }
  }, [contractId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!contractData) {
    return <div>Contract not found.</div>;
  }

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>Smart Contract Dashboard</h1>
        <nav>
          <ul className="flex space-x-4">
            <li>
              <a href="#" className="hover:text-blue-500">Overview</a>
            </li>
            <li>
              <a href="#" className="hover:text-blue-500">Analysis</a>
            </li>
            <li>
              <a href="#" className="hover:text-blue-500">Reporting</a>
            </li>
          </ul>
        </nav>
      </header>

      <main className="mt-8 flex">
        <aside className="w-64 bg-gray-700 p-4">
          {/* Sidebar - Navigation */}
          <h2 className="text-lg font-semibold text-white">Contracts</h2>
          <ul className="space-y-2">
            {dummyContractData.map((contract) => (
              <li
                key={contract.name}
                className="hover:bg-gray-600 cursor-pointer"
              >
                <a href={`?contractId=${contract.name}`}>{contract.name}</a>
              </li>
            ))}
          </ul>
        </aside>

        <div className="w-full ml-4">
          {/* Main Content */}
          <section className="mb-4">
            <h2 className="text-xl font-bold mb-2">{contractData.name}</h2>
            <p className="text-gray-700">Severity Score: {contractData.severityScore}</p>
            <p className="text-gray-700">{contractData.details}</p>
          </section>

          {/* Placeholder for Data Visualization - Replace with actual charts */}
          <div className="bg-white p-4 rounded shadow-md">
            <h3 className="text-lg font-semibold mb-2">Data Visualization</h3>
            {/* Add charts here using libraries like Chart.js or Recharts */}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white p-4 fixed bottom-0 w-full">
        <p>&copy; 2024 Smart Contract Dashboard</p>
      </footer>
    </div>
  );
};

export default DashboardPage;