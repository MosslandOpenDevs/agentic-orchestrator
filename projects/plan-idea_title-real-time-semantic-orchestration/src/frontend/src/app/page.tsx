import React, { useState, useEffect } from 'react';
import { FaArrowDown, FaArrowUp, FaPlus, FaTimes } from 'react-icons/fa';
import { useTailwind } from 'tailwind-rn';
import { useColorScheme } from 'react-native';
import { Typography } from 'antd';
import { useWebSocket } from 'react-use-websocket';

const { Text } = Typography.Base;

const Dashboard = () => {
  const [darkMode, setDarkMode] = useState(false);
  const tailwind = useTailwind();
  const colorScheme = useColorScheme();

  useEffect(() => {
    setDarkMode(colorScheme === 'dark');
  }, [colorScheme]);

  const ws = useWebSocket('ws://localhost:8080/ws', {
    onMessage: (event) => {
      console.log('Received message:', event.data);
    },
    connect: () => {
      console.log('Connected to WebSocket server');
    },
    reconnect: true,
  });

  return (
    <div className={`${tailwind('bg-gray-100 p-4')`} ${darkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
      <header className={`${tailwind('bg-white shadow-md p-4')`} ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
        <Text type="h3" className={`${tailwind('text-xl font-bold')}`} >DRAIAN Dashboard</Text>
      </header>

      <main className={`${tailwind('flex-1')}`} ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <aside className={`${tailwind('w-64 bg-gray-200 p-4')`} ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
          <h4 className={`${tailwind('text-lg font-semibold mb-2')}`} >Agent Dashboard</h4>
          <button className={`${tailwind('bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded')`} onClick={() => ws.send({ type: 'createAgent' })}>
            <FaPlus size={20} /> Create Agent
          </button>
          {/* Agent List Placeholder */}
        </aside>

        <section className={`${tailwind('w-full')}`} ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <h4 className={`${tailwind('text-lg font-semibold mb-2')}`} >Message Log</h4>
          <div className={`${tailwind('p-4')}`} >
            {ws.messages.map((message, index) => (
              <div key={index} className={`${tailwind('mb-2')}`} >
                <Text type="body1" className={`${tailwind('text-gray-700')}`} >{message.data}</Text>
              </div>
            ))}
          </div>
        </section>

        <section className={`${tailwind('w-full')}`} ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <h4 className={`${tailwind('text-lg font-semibold mb-2')}`} >WebRTC Connection Panel</h4>
          {/* Placeholder for WebRTC Connection Panel - Requires WebRTC implementation */}
          <div className={`${tailwind('p-4')}`} >
            <Text type="body1" className={`${tailwind('text-gray-700')}`} >WebRTC Connection Status - Placeholder</Text>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;