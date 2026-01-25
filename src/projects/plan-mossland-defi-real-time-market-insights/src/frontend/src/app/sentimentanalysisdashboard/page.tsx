import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface SentimentData {
  timestamp: string;
  sentimentScore: number;
}

interface Props {
  apiUrl: string;
}

const SentimentAnalysisDashboard: React.FC<Props> = ({ apiUrl }) => {
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(apiUrl);
        setSentimentData(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch data');
        setLoading(false);
      }
    };

    const intervalId = setInterval(fetchData, 5000);

    fetchData();

    return () => clearInterval(intervalId);
  }, [apiUrl]);

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (error) return <div className="flex items-center justify-center h-screen text-red-500">{error}</div>;

  const data = sentimentData.map((item, index) => ({
    name: item.timestamp,
    score: item.sentimentScore
  }));

  return (
    <div className="p-4 max-w-full mx-auto">
      <h1 className="text-2xl font-bold mb-4">Sentiment Analysis Dashboard</h1>
      <LineChart width={800} height={400} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="score" stroke="#8884d8" activeDot={{ r: 8 }} />
      </LineChart>
    </div>
  );
};

export default SentimentAnalysisDashboard;