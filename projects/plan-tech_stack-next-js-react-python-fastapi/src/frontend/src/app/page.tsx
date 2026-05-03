import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { useColorScheme } from 'react-native';
import {
  View,
  Text,
  Button,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  SafeAreaView,
} from 'react-native';

const Tailwind = useTailwind({
  theme: {
    colors: {
      'primary': '#2962FF',
      'secondary': '#64B5F6',
      'background': '#FFFFFF',
      'card': '#F5F5F5',
      'text': '#212121',
      'light': '#EEEEEE',
    },
  },
});

const Dashboard = () => {
  const [isDark, setIsDark] = useState(false);
  const colorScheme = useColorScheme();
  useEffect(() => {
    setIsDark(colorScheme === 'dark');
  }, [colorScheme]);

  const [loading, setLoading] = useState(true);
  const [estimatedCost, setEstimatedCost] = useState({
    labor: {
      min: 120000,
      max: 180000,
    },
    infrastructure: {
      min: 5000,
      max: 10000,
    },
    securityAudits: {
      min: 10000,
      max: 30000,
    },
  });

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setLoading(false);
    }, 2000);
  }, []);

  if (loading) {
    return (
      <View style={Tailwind.container}>
        <Text style={Tailwind.text}>Loading...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={Tailwind.container}>
      <View style={[Tailwind.header, isDark ? { backgroundColor: Tailwind.colors.background } : { backgroundColor: Tailwind.colors.background }]}>
        <Text style={Tailwind.title}>Argus Dashboard</Text>
      </View>
      <ScrollView>
        <View style={[Tailwind.card, isDark ? { backgroundColor: Tailwind.colors.card } : { backgroundColor: Tailwind.colors.card }]}>
          <Text style={Tailwind.heading}>Estimated Cost</Text>
          <Text>Labor: ${estimatedCost.labor.min} - ${estimatedCost.labor.max}</Text>
          <Text>Infrastructure: ${estimatedCost.infrastructure.min} - ${estimatedCost.infrastructure.max}</Text>
          <Text>Security Audits: ${estimatedCost.securityAudits.min} - ${estimatedCost.securityAudits.max}</Text>
        </View>
        <View style={[Tailwind.card, isDark ? { backgroundColor: Tailwind.colors.card } : { backgroundColor: Tailwind.colors.card }]}>
          <Text style={Tailwind.heading}>Frontend</Text>
          <Text>Next.js/React - Chosen for performance and scalability.</Text>
        </View>
        <View style={[Tailwind.card, isDark ? { backgroundColor: Tailwind.colors.card } : { backgroundColor: Tailwind.colors.card }]}>
          <Text style={Tailwind.heading}>Backend</Text>
          <Text>Python/FastAPI - Ideal for data science and ML.</Text>
        </View>
        <View style={[Tailwind.card, isDark ? { backgroundColor: Tailwind.colors.card } : { backgroundColor: Tailwind.colors.card }]}>
          <Text style={Tailwind.heading}>Database</Text>
          <Text>Pinecone - Efficient vector storage and retrieval.</Text>
        </View>
        <View style={[Tailwind.card, isDark ? { backgroundColor: Tailwind.colors.card } : { backgroundColor: Tailwind.colors.card }]}>
          <Text style={Tailwind.heading}>Blockchain Integration</Text>
          <Text>Ethereum (Mainnet) - Web3.js for smart contract interaction.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default Dashboard;