import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { WebSocket } from 'ws';

// Define types for data and WebSocket messages
interface WithdrawalData {
  tokenId: string;
  status: 'pending' | 'success' | 'failed';
  timestamp: number;
  amount: number;
}

interface SmartContractAnalysis {
  contractAddress: string;
  analysisResult: string;
  timestamp: number;
}

// Tailwind configuration
const tailwind = useTailwind({
  theme: {
    extend: {
      colors: {
        'mossland-primary': '#3490dc',
        'mossland-secondary': '#2ecc71',
      },
    },
  },
});

const Dashboard: React.FC = () => {
  const [withdrawalData, setWithdrawalData] = useState<WithdrawalData[]>([]);
  const [smartContractAnalysis, setSmartContractAnalysis] = useState<SmartContractAnalysis>({
    contractAddress: '',
    analysisResult: '',
    timestamp: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

  // WebSocket connection
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const newWs = new WebSocket('ws://localhost:8080'); // Replace with your WebSocket server URL
      setWs(newWs);

      newWs.onopen = () => {
        console.log('WebSocket connected');
        setLoading(false);
      };

      newWs.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'withdrawal') {
          setWithdrawalData((prevData) => [...prevData, data.withdrawal]);
        } else if (data.type === 'analysis') {
          setSmartContractAnalysis(data.analysis);
        }
      };

      newWs.onclose = () => {
        console.log('WebSocket disconnected');
        setLoading(true);
      };

      newWs.onerror = (error) => {
        console.error('WebSocket error:', error);
        setLoading(true);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className={`${tailwind.container} ${isDarkMode ? 'dark' : ''}`}>
      <header className={`${tailwind.header}`}>
        <h1 className={`${tailwind.title}`}>Mossland Token Withdrawal Automation Agent</h1>
        <button className={`${tailwind.toggleButton} ${isDarkMode ? 'dark:bg-mossland-primary dark:text-white' : 'bg-mossland-primary text-white'}`} onClick={() => setIsDarkMode(!isDarkMode)}>
          {isDarkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </header>

      <main className={`${tailwind.main}`}>
        <aside className={`${tailwind.sidebar}`}>
          {/* Sidebar content */}
        </aside>

        <div className={`${tailwind.content}`}>
          {loading && <p className={`${tailwind.loading}`}>Loading data...</p>}

          {/* Withdrawal Dashboard */}
          <div className={`${tailwind.dashboardCard}`}>
            <h2 className={`${tailwind.cardTitle}`}>Withdrawal Status</h2>
            {withdrawalData.length > 0 ? (
              withdrawalData.map((item) => (
                <div key={item.tokenId} className={`${tailwind.dashboardItem}`}>
                  <p>Token ID: {item.tokenId}</p>
                  <p>Status: {item.status}</p>
                  <p>Timestamp: {new Date(item.timestamp).toLocaleString()}</p>
                  <p>Amount: {item.amount}</p>
                </div>
              ))
            ) : (
              <p>No withdrawals yet.</p>
            )}
          </div>

          {/* Smart Contract Analysis Panel */}
          <div className={`${tailwind.dashboardCard}`}>
            <h2 className={`${tailwind.cardTitle}`}>Smart Contract Analysis</h2>
            <p>Contract Address: {smartContractAnalysis.contractAddress}</p>
            <p>Analysis Result: {smartContractAnalysis.analysisResult}</p>
            <p>Timestamp: {new Date(smartContractAnalysis.timestamp).toLocaleString()}</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;