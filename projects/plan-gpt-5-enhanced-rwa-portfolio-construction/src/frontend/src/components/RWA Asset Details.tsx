import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface RWAAssetDetailsProps {
  assetId: string;
  assetName: string;
  price: number;
  quantity: number;
  historicalPerformance: { [key: string]: number[] }; // Key: Date, Value: [Open, High, Low, Close]
}

const RWAAssetDetails: React.FC<RWAAssetDetailsProps> = ({
  assetId,
  assetName,
  price,
  quantity,
  historicalPerformance,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (assetId) {
      // Simulate fetching data (replace with actual API call)
      setTimeout(() => {
        setLoading(false);
        if (assetId === '1') {
          setError('Simulated Error for Asset 1');
        }
      }, 1500);
    }
  }, [assetId]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-6 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-lg">Loading asset details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-6 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-lg text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md flex">
      <div className="w-64 flex flex-col items-start">
        <h2 className="text-xl font-bold mb-4">{assetName}</h2>
        <p className="text-gray-700 mb-4">Asset ID: {assetId}</p>
        <p className="text-gray-700 mb-4">Price: ${price.toFixed(2)}</p>
        <p className="text-gray-700 mb-4">Quantity: {quantity}</p>
      </div>

      <div className="flex-grow w-full">
        <h3 className="text-lg font-bold mb-4">Historical Performance</h3>
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left">
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Open</th>
              <th className="px-4 py-2">High</th>
              <th className="px-4 py-2">Low</th>
              <th className="px-4 py-2">Close</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(historicalPerformance).map((date) => (
              <tr key={date} className="text-left">
                <td className="px-4 py-2">{date}</td>
                <td className="px-4 py-2">{historicalPerformance[date][0].toFixed(2)}</td>
                <td className="px-4 py-2">{historicalPerformance[date][1].toFixed(2)}</td>
                <td className="px-4 py-2">{historicalPerformance[date][2].toFixed(2)}</td>
                <td className="px-4 py-2">{historicalPerformance[date][3].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RWAAssetDetails;