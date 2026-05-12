import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { WebSocket } from 'ws';

// Dummy data for demonstration
interface ContractData {
  contractAddress: string;
  name: string;
  version: string;
  vulnerabilityScore: number;
  threatModel: string;
}

const initialContractData: ContractData = {
  contractAddress: '',
  name: '',
  version: '',
  vulnerabilityScore: 0,
  threatModel: '',
};

const DashboardPage = () => {
  const [selectedContract, setSelectedContract] = useState<ContractData>(initialContractData);
  const [contractData, setContractData] = useState<ContractData>(initialContractData);
  const [loading, setLoading] = useState<boolean>(true);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const contractAddress = searchParams.get('contractAddress') || '';

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulate fetching data from an API
        const fakeContractData: ContractData = {
          contractAddress: contractAddress,
          name: 'Mossland Contract 1',
          version: '1.0',
          vulnerabilityScore: 75,
          threatModel: 'Basic',
        };
        setContractData(fakeContractData);
      } catch (error) {
        console.error('Error fetching data:', error);
        setContractData(initialContractData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // WebSocket connection
    const wsInstance = new WebSocket('ws://localhost:8080'); // Replace with your WebSocket server URL

    wsInstance.onopen = () => {
      console.log('WebSocket connected');
      setMessage('Connected to WebSocket');
    };

    wsInstance.onmessage = (event) => {
      setMessage(event.data);
    };

    wsInstance.onclose = () => {
      setMessage('Disconnected from WebSocket');
    };

    setWs(wsInstance);

  }, [contractAddress]);

  const handleContractChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedContract({ ...selectedContract, [event.target.name]: event.target.value });
  };

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>CPDV-SR Dashboard</h1>
        <nav>
          <button onClick={() => searchParams.set('contractAddress', '')} className="bg-blue-500 text-white px-4 rounded">
            Clear Contract
          </button>
        </nav>
      </header>

      <main className="mt-8 flex">
        <aside className="w-64 bg-gray-200 p-4">
          <h2>Contract Details</h2>
          <form>
            <label htmlFor="contractAddress" className="block mb-2">
              Contract Address:
            </label>
            <input
              type="text"
              id="contractAddress"
              name="contractAddress"
              value={selectedContract.contractAddress}
              onChange={handleContractChange}
              className="w-full p-2 border rounded"
            />
            <label htmlFor="name" className="block mb-2">
              Name:
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={selectedContract.name}
              onChange={handleContractChange}
              className="w-full p-2 border rounded"
            />
            <label htmlFor="version" className="block mb-2">
              Version:
            </label>
            <input
              type="text"
              id="version"
              name="version"
              value={selectedContract.version}
              onChange={handleContractChange}
              className="w-full p-2 border rounded"
            />
          </form>
        </aside>

        <div className="w-full p-4">
          {loading ? (
            <div className="text-center">Loading contract data...</div>
          ) : (
            <>
              <h2>{contractData.name} ({contractData.contractAddress})</h2>
              <p>Vulnerability Score: {contractData.vulnerabilityScore}</p>
              <p>Threat Model: {contractData.threatModel}</p>
              {/* Data Visualization Placeholder */}
              <div className="bg-gray-300 rounded p-4 mt-4">
                <p>Data visualization would go here.</p>
              </div>
              {/* ContractAnalysisDashboard Component (Placeholder) */}
              <div className="mt-4">
                <p>ContractAnalysisDashboard Component (Placeholder)</p>
              </div>
            </>
          )}
        </div>
      </main>

      {/* WebSocket Message Display */}
      <div className="mt-8 bg-gray-200 p-4 rounded">
        <h3 className="font-bold">WebSocket Messages:</h3>
        {message && <p>{message}</p>}
      </div>
    </div>
  );
};

export default DashboardPage;