import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useSession } from 'next/ui';

// Tailwind CSS imports
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Text,
  Input,
  FormLabel,
  FormErrorMessage,
  Alert,
  Spinner,
} from '@headlessui/react';
import { FaEthereum, FaNft } from 'react-icons/fa';
import { BarChart } from 'react-chartjs-2';
import Chart from 'chart.js/auto';

// Mock Data (Replace with actual data fetching)
interface NFT {
  tokenId: string;
  name: string;
  description: string;
  imageUri: string;
  price: number;
  domainName: string;
}

const mockNFTs: NFT[] = [
  { tokenId: '1', name: 'Mossland Genesis', description: 'First NFT from Mossland', imageUri: 'ipfs://...', price: 100, domainName: 'mossland.eth' },
  { tokenId: '2', name: 'Sunset Collection', description: 'Limited edition sunset NFTs', imageUri: 'ipfs://...', price: 200, domainName: 'mossland.eth' },
  { tokenId: '3', name: 'Lunar Phase', description: 'Dynamic NFT based on the moon', imageUri: 'ipfs://...', price: 300, domainName: 'mossland.eth' },
];

const Dashboard = () => {
  const router = useRouter();
  const { data: session } = useSession({
    onSuccess: () => {
      router.push('/dashboard');
    },
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newNFT, setNewNFT] = useState({
    tokenId: '',
    name: '',
    description: '',
    imageUri: '',
    price: 0,
    domainName: '',
  });

  const [minting, setMinting] = useState(false);

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setLoading(false);
    }, 1500);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewNFT({ ...newNFT, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      // Simulate minting process
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Add new NFT to mock data
      mockNFTs.push(newNFT);

      // Reset form
      setNewNFT({
        tokenId: '',
        name: '',
        description: '',
        imageUri: '',
        price: 0,
        domainName: '',
      });
    } catch (err) {
      setError('Failed to mint NFT. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
      setMinting(false);
    }
  };

  const chartData = {
    labels: ['Genesis', 'Sunset', 'Lunar'],
    datasets: [
      {
        label: 'NFT Price (ETH)',
        data: mockNFTs.map(nft => nft.price),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Price (ETH)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'NFT Name'
        }
      }
    },
    plugins: {
      title: {
        display: true,
        text: 'NFT Price Comparison'
      }
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <Spinner className="animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="mb-4" severity="error">
        {error}
      </Alert>
    );
  }

  return (
    <div className="bg-gray-100 p-4">
      <header className="bg-white shadow-md p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Mossland Dashboard</h1>
          <div className="flex space-x-4">
            {/* Add user profile or other relevant info here */}
          </div>
        </div>
      </header>

      <main className="mt-6">
        <Card>
          <CardHeader className="bg-white shadow-md p-6">
            <Text className="text-xl font-bold">Domain Overview</Text>
          </CardHeader>
          <CardBody>
            {mockNFTs.map((nft) => (
              <div key={nft.tokenId} className="grid grid-cols-3 gap-4">
                <div className="col-span-1">
                  <img
                    src={nft.imageUri}
                    alt={nft.name}
                    className="w-full h-32 object-cover rounded-md"
                  />
                </div>
                <div className="col-span-2">
                  <Text className="text-lg font-semibold">{nft.name}</Text>
                  <Text className="text-gray-600">{nft.description}</Text>
                  <Text className="font-bold text-xl">Price: {nft.price} ETH</Text>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="bg-white shadow-md p-6">
            <Text className="text-xl font-bold">NFT Price Chart</Text>
          </CardHeader>
          <CardBody>
            <BarChart data={chartData} options={chartOptions} />
          </CardBody>
        </Card>
      </main>
    </div>
  );
};

export default Dashboard;