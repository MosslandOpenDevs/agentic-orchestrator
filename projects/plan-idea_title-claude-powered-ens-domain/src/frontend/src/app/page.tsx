import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useSession } from 'next-auth/react';

// Tailwind CSS imports
import {
  Box,
  Flex,
  Heading,
  Button,
  IconButton,
  useColorModeValue,
  Divider,
  Stack,
  Text,
  Alert,
  Spinner,
  Table,
  TBody,
  TFoot,
  TH,
  Tr,
  Td,
} from '@chakra-ui/react';

// Placeholder components - Replace with actual implementations
interface Domain {
  name: string;
  tokenId: string;
}

interface NFT {
  name: string;
  tokenId: string;
  metadata?: any;
}

type UserSession = {
  name?: string;
  accessToken?: string;
};

const Dashboard = () => {
  const { data: session } = useSession();
  const router = useRouter();

  const [domains, setDomains] = useState<Domain[]>([]);
  const [nfts, setNfts] = useState<NFT[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      if (session) {
        setDomains([{ name: 'mossland.eth', tokenId: '123' }]);
        setNfts([{ name: 'Mossland NFT', tokenId: '456', metadata: { description: 'A cool NFT' } }]);
      } else {
        setError('No session found. Please log in.');
      }
      setLoading(false);
    }, 2000);
  }, [session]);

  if (loading) {
    return (
      <Box p={4} bg="gray.100">
        <Spinner size="xl" />
        <Text mt={4}>Loading dashboard...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={4} bg="gray.200">
        <Alert severity="error" w="100%">
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box bg="gray.50" p={4} w="100%">
      <Heading mb={4} size="xl" align="center">Claude-Powered ENS Portfolio Dashboard</Heading>

      <Box p={4} bg="white" borderRadius="lg" shadow-md>
        <Heading size="h3" mb={3}>Domains</Heading>
        {domains.length === 0 ? (
          <Text>No domains managed.</Text>
        ) : (
          <Table size="md" variant="striped">
            <Thead>
              <Tr>
                <TH>Name</TH>
                <TH>Token ID</TH>
              </Tr>
            </Thead>
            <TBody>
              {domains.map((domain) => (
                <Tr key={domain.tokenId}>
                  <Td>{domain.name}</Td>
                  <Td>{domain.tokenId}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Box>

      <Box p={4} bg="white" borderRadius="lg" shadow-md mt={4}>
        <Heading size="h3" mb={3}>NFTs</Heading>
        {nfts.length === 0 ? (
          <Text>No NFTs minted.</Text>
        ) : (
          <Table size="md" variant="striped">
            <Thead>
              <Tr>
                <TH>Name</TH>
                <TH>Token ID</TH>
                <TH>Metadata</TH>
              </Tr>
            </Thead>
            <TBody>
              {nfts.map((nft) => (
                <Tr key={nft.tokenId}>
                  <Td>{nft.name}</Td>
                  <Td>{nft.tokenId}</Td>
                  <Td>{JSON.stringify(nft.metadata)}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Box>

      <Box p={4} bg="white" borderRadius="lg" shadow-md mt={4}>
        <Heading size="h3" mb={3}>Mint NFT</Heading>
        <MintForm />
      </Box>
    </Box>
  );
};

interface MintFormProps {
  onSubmit: (data: any) => void;
}

const MintForm: React.FC<MintFormProps> = ({ onSubmit }) => {
  const [nftName, setNftName] = useState<string>('');
  const [tokenId, setTokenId] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name: nftName, tokenId: tokenId });
  };

  return (
    <Box p={4} bg="gray.100" borderRadius="lg" shadow-md>
      <Heading size="h4" mb={2}>New NFT</Heading>
      <form onSubmit={handleSubmit}>
        <Stack spacing={4}>
          <Input label="NFT Name" value={nftName} onChange={((e) => setNftName(e.target.value))} />
          <Input label="Token ID" value={tokenId} onChange={((e) => setTokenId(e.target.value))} />
          <Button type="submit" colorScheme="blue" size="md">Mint</Button>
        </Stack>
      </form>
    </Box>
  );
};

export default Dashboard;