import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { WebSocket } from 'ws';
import { useColorScheme } from 'react-native';

type WithdrawalStatus = {
  tokenId: string;
  status: 'pending' | 'completed' | 'failed';
  timestamp: number;
  reason?: string;
};

type SmartContractData = {
  contractAddress: string;
  abi: any;
  // Add other relevant smart contract data fields here
};

type WebSocketMessage = {
  type: 'withdrawal_status_update';
  data: WithdrawalStatus;
};

const Dashboard = () => {
  const { styles } = useTailwind({
    colors: {
      primary: '#3490dc',
      secondary: '#2ecc71',
      gray: {
        light: '#f2f2f2',
        medium: '#95a5a6',
        dark: '#607d8b',
      },
      white: '#ffffff',
      black: '#000000',
    },
    fontFamily: 'sans-serif',
  });

  const [withdrawalStatuses, setWithdrawalStatuses] = useState<WithdrawalStatus[]>([]);
  const [smartContractData, setSmartContractData] = useState<SmartContractData>({});
  const [loading, setLoading] = useState<boolean>(true);
  const colorScheme = useColorScheme();

  useEffect(() => {
    const ws = new WebSocket('ws://your-websocket-server-url'); // Replace with your WebSocket URL

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Simulate some initial data
      setWithdrawalStatuses([{ tokenId: 'NFT1', status: 'pending', timestamp: Date.now() }]);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data as string);
      if (message.type === 'withdrawal_status_update') {
        setWithdrawalStatuses((prevStatuses) =>
          prevStatuses.concat(message.data)
        );
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    // Simulate fetching smart contract data
    setTimeout(() => {
      setSmartContractData({
        contractAddress: '0x...',
        abi: {
          // Example ABI
          methods: ['withdraw'],
          inputs: [{ type: 'address', name: 'to' }, { type: 'uint256', name: 'amount' }],
          outputs: [{ type: 'bool', name: 'success' }],
        },
      });
      setLoading(false);
    }, 1500);
  }, []);

  const toggleDarkMode = () => {
    // Implement dark mode toggle logic here
    console.log('Toggle dark mode');
  };

  return (
    <div style={{ backgroundColor: colorScheme === 'dark' ? styles.gray.dark : styles.white, minHeight: '100vh' }}>
      <header style={{ backgroundColor: styles.primary, padding: '1rem', textAlign: 'center' }}>
        <h1>ThirdWeb Withdrawal Dashboard</h1>
        <button style={{ backgroundColor: styles.secondary, padding: '0.5rem 1rem', border: 'none', cursor: 'pointer' }} onClick={toggleDarkMode}>
          {colorScheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </header>

      <main style={{ padding: '2rem' }}>
        <section>
          <h2>Withdrawal Status</h2>
          {loading ? (
            <p>Loading withdrawal statuses...</p>
          ) : (
            withdrawalStatuses.map((status) => (
              <div key={status.tokenId} style={{ marginBottom: '1rem', border: '1px solid styles.gray.medium', padding: '1rem', borderRadius: '8px' }}>
                <p>Token ID: {status.tokenId}</p>
                <p>Status: {status.status}</p>
                <p>Timestamp: {new Date(status.timestamp).toLocaleString()}</p>
                {status.reason && <p>Reason: {status.reason}</p>}
              </div>
            ))
          )}
        </section>

        <section>
          <h2>Smart Contract Analysis</h2>
          <form>
            <label htmlFor="contractAddress">Contract Address:</label>
            <input
              type="text"
              id="contractAddress"
              value={smartContractData.contractAddress}
              onChange={(e) => setSmartContractData({ ...smartContractData, contractAddress: e.target.value })}
            />
            <br />
            <label htmlFor="abi">ABI:</label>
            <textarea id="abi" value={JSON.stringify(smartContractData.abi)} onChange={() => {}}></textarea>
            <button type="submit">Analyze</button>
          </form>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;