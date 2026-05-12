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
  Stack,
  Text,
  Divider,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Table,
  TableCaption,
  TableBody,
  TableRow,
  TableCell,
  Sprintf,
} from '@chakra-ui/react';
import { FaArrowDown, FaArrowUp } from 'react-icons/fa';

// Placeholder components - Replace with actual implementations
const PortfolioOverview = () => {
  return (
    <Card w="full" shadow="md" borderRadius="md" mb={4}>
      <CardHeader bg="white" px={4} py={4}>
        <Heading size="m" color="gray.700">Portfolio Overview</Heading>
      </CardHeader>
      <CardBody p={4}>
        <Text>Portfolio Value: $1,234,567.89</Text>
        <Text>Total Assets: 123</Text>
      </CardBody>
      <CardFooter p={4}>
        <Button colorScheme="blue" variant="solid" size="md">
          Rebalance Portfolio
        </Button>
      </CardFooter>
    </Card>
  );
};

const AssetDetails = () => {
  return (
    <Card w="full" shadow="md" borderRadius="md" mb={4}>
      <CardHeader bg="white" px={4} py={4}>
        <Heading size="m" color="gray.700">Asset Details</Heading>
      </CardHeader>
      <CardBody p={4}>
        <Text>Asset Name: Bitcoin</Text>
        <Text>Current Price: $30,000</Text>
      </CardBody>
      <CardFooter p={4}>
        <Button colorScheme="green" variant="solid" size="md">
          Add to Portfolio
        </Button>
      </CardFooter>
    </Card>
  );
};

const Settings = () => {
  return (
    <Card w="full" shadow="md" borderRadius="md" mb={4}>
      <CardHeader bg="white" px={4} py={4}>
        <Heading size="m" color="gray.700">Settings</Heading>
      </CardHeader>
      <CardBody p={4}>
        <Text>Dark Mode: On</Text>
        <Button colorScheme="blue" variant="solid" size="md">
          Save Changes
        </Button>
      </CardBody>
      <CardFooter p={4}>
        <Button colorScheme="red" variant="solid" size="md">
          Logout
        </Button>
      </CardFooter>
    </Card>
  );
};

const Dashboard = () => {
  const router = useRouter();
  const { data: session } = useSession();

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) {
      router.push('/login');
    }
    setLoading(false);
  }, [router, session]);

  if (loading) {
    return (
      <Box bg="gray.100" p={4}>
        <Heading size="xl" color="blue.700">Mossland Dashboard</Heading>
        <Text>Loading...</Text>
      </Box>
    );
  }

  return (
    <Box bg="gray.100" p={4} w="100%">
      <Header />
      <Flex direction="row" mb={4}>
        <Sidebar />
        <main>
          <PortfolioOverview />
          <AssetDetails />
          <Settings />
        </main>
      </Flex>
    </Box>
  );
};

const Header = () => {
  return (
    <Box bg="white" p={4} shadow="md" borderRadius="md">
      <Flex justifyContent="space-between" alignItems="center" mb={2}>
        <Heading size="xl" color="blue.700">Mossland</Heading>
        {session && (
          <Button colorScheme="blue" size="sm">
            {session?.name || session?.username}
          </Button>
        )}
      </Flex>
      <Divider />
    </Box>
  );
};

const Sidebar = () => {
  return (
    <Box bg="white" p={4} shadow="md" borderRadius="md" w="300px">
      <Heading size="lg" color="gray.700">Navigation</Heading>
      <Stack spacing={4}>
        <Button colorScheme="blue" size="md" onClick={() => router.push('/portfolio')}>
          Portfolio
        </Button>
        <Button colorScheme="green" size="md" onClick={() => router.push('/assets')}>
          Assets
        </Button>
        <Button colorScheme="red" size="md" onClick={() => router.push('/settings')}>
          Settings
        </Button>
      </Stack>
    </Box>
  );
};

export default Dashboard;