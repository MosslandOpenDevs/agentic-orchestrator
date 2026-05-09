import React, { useState, useEffect } from 'react';

interface WebRTCConnectionPanelProps {
  connectionStatus: string;
  latency: number;
  isConnecting: boolean;
  error?: string;
  onDisconnect?: () => void;
}

const WebRTCConnectionPanel: React.FC<WebRTCConnectionPanelProps> = ({
  connectionStatus,
  latency,
  isConnecting,
  error,
  onDisconnect,
}) => {
  const [statusMessage, setStatusMessage] = useState('');
  const [latencyMessage, setLatencyMessage] = useState('');

  useEffect(() => {
    setStatusMessage(connectionStatus);
  }, [connectionStatus]);

  useEffect(() => {
    setLatencyMessage(`${latency}ms`);
  }, [latency]);

  return (
    <div
      className="bg-white rounded-lg shadow-md p-6 flex flex-col items-center w-full max-w-md"
      aria-label="WebRTC Connection Panel"
    >
      {isConnecting && (
        <div className="text-green-500">Connecting...</div>
      )}

      {error && (
        <div className="text-red-500 font-bold">
          Error: {error}
        </div>
      )}

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Connection Status</h3>
        <p className="text-gray-700 text-sm">{statusMessage}</p>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Latency</h3>
        <p className="text-gray-700 text-sm">{latencyMessage}</p>
      </div>

      {onDisconnect && (
        <button
          onClick={onDisconnect}
          className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mt-4 w-32"
          aria-label="Disconnect"
          tabIndex={0}
        >
          Disconnect
        </button>
      )}
    </div>
  );
};

export default WebRTCConnectionPanel;