import React, { useState, useEffect } from 'react';
import { useDebounce } from 'use-lodash-debounce';

interface NFTPositionDetailsProps {
  nftPosition: NFTPosition;
  isLoading: boolean;
  error?: string;
}

interface NFTPosition {
  asset: string;
  quantity: number;
  price: number;
  totalValue: number;
  riskScore: number;
  historicalPerformance: HistoricalPerformanceData[];
}

interface HistoricalPerformanceData {
  date: string;
  openPrice: number;
  closePrice: number;
  highPrice: number;
  lowPrice: number;
  change: number;
}

const NFTPositionDetails: React.FC<NFTPositionDetailsProps> = ({
  nftPosition,
  isLoading,
  error,
}) => {
  const [hoveredAsset, setHoveredAsset] = useState<string | null>(null);

  const debouncedHandleHover = useDebounce((asset: string) => {
    setHoveredAsset(asset);
  }, 200);

  useEffect(() => {
    debouncedHandleHover(nftPosition.asset);
  }, [nftPosition.asset]);

  return (
    <div
      className="bg-white rounded-lg shadow-md overflow-hidden w-full max-w-md"
      aria-label="NFT Position Details"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'ArrowLeft') {
          // Handle navigation - Implement as needed
        } else if (e.key === 'ArrowRight') {
          // Handle navigation - Implement as needed
        }
      }}
    >
      {isLoading && <p className="text-gray-200 p-4">Loading...</p>}
      {error && <p className="text-red-500 p-4">{error}</p>}
      {nftPosition && (
        <div className="p-4">
          <h2 className="text-xl font-bold mb-4">{nftPosition.asset}</h2>
          <p className="text-gray-700 mb-4">
            Quantity: {nftPosition.quantity}
          </p>
          <p className="text-gray-700 mb-4">
            Price: ${nftPosition.price.toFixed(2)}
          </p>
          <p className="text-gray-700 mb-4">
            Total Value: ${nftPosition.totalValue.toFixed(2)}
          </p>
          <p className="text-gray-700 mb-4">
            Risk Score: {nftPosition.riskScore.toFixed(2)}
          </p>

          {/* Historical Performance */}
          <h3>Historical Performance</h3>
          <table className="table-auto w-full">
            <thead>
              <tr className="text-left">
                <th>Date</th>
                <th>Open</th>
                <th>Close</th>
                <th>High</th>
                <th>Low</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {nftPosition.historicalPerformance.map((item) => (
                <tr key={item.date} className="text-left">
                  <td>{item.date}</td>
                  <td>{item.openPrice.toFixed(2)}</td>
                  <td>{item.closePrice.toFixed(2)}</td>
                  <td>{item.highPrice.toFixed(2)}</td>
                  <td>{item.lowPrice.toFixed(2)}</td>
                  <td>{item.change.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default NFTPositionDetails;