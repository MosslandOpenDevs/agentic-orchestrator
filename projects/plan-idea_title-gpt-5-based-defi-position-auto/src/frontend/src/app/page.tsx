import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { useColorScheme } from 'react-native';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
} from 'react-native';

const Tailwind = useTailwind();

type PortfolioData = {
  assets: {
    [key: string]: {
      name: string;
      quantity: number;
      price: number;
      totalValue: number;
    };
  };
  totalValue: number;
  riskScore: number;
};

type AppState {
  theme: 'light' | 'dark';
}

const App: React.FC<AppState> = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData>({
    assets: {
      USDC: { name: 'USDC', quantity: 100, price: 1.0, totalValue: 100.0 },
      MTL: { name: 'MTL', quantity: 50, price: 1.5, totalValue: 75.0 },
    },
    totalValue: 175.0,
    riskScore: 0.5,
  });
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setPortfolioData({
        assets: {
          USDC: { name: 'USDC', quantity: 120, price: 1.05, totalValue: 126.0 },
          MTL: { name: 'MTL', quantity: 60, price: 1.6, totalValue: 96.0 },
        },
        totalValue: 222.0,
        riskScore: 0.7,
      });
    }, 1500);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <SafeAreaView style={Tailwind.safeAreaView}>
      <View style={[Tailwind.flexBox, Tailwind.bgGray100, Tailwind.paddingVertical16]}>
        <View style={Tailwind.shadowBox}>
          <Text style={Tailwind.textTitle}>TerraForm Dashboard</Text>
          <Text style={Tailwind.textSubTitle}>Your AI-Powered DeFi Position Auto-Rebalancing Agent</Text>
          <TouchableOpacity style={Tailwind.button} onPress={toggleTheme}>
            <Text style={Tailwind.textButton}>Toggle Theme</Text>
          </TouchableOpacity>
        </View>

        <ScrollView>
          <View style={Tailwind.container}>
            {/* Portfolio Overview */}
            <View style={Tailwind.card}>
              <Text style={Tailwind.textCardTitle}>Portfolio Summary</Text>
              <Text style={Tailwind.textCardSubtitle}>Total Value: ${portfolioData.totalValue.toFixed(2)}</Text>
              <Text style={Tailwind.textCardSubtitle}>Risk Score: {portfolioData.riskScore.toFixed(2)}</Text>
            </View>

            {/* Asset Details */}
            <View style={Tailwind.card}>
              <Text style={Tailwind.textCardTitle}>Asset Details</Text>
              <View>
                <Text style={Tailwind.textCardSubtitle}>USDC</Text>
                <Text style={Tailwind.textCardSubtitle}>Quantity: 120</Text>
                <Text style={Tailwind.textCardSubtitle}>Price: $1.05</Text>
                <Text style={Tailwind.textCardSubtitle}>Value: $126.00</Text>
              </View>
              <View>
                <Text style={Tailwind.textCardSubtitle}>MTL</Text>
                <Text style={Tailwind.textCardSubtitle}>Quantity: 60</Text>
                <Text style={Tailwind.textCardSubtitle}>Price: $1.60</Text>
                <Text style={Tailwind.textCardSubtitle}>Value: $96.00</Text>
              </View>
            </View>

            {/* Placeholder for Rebalancing Form */}
            <View style={Tailwind.card}>
              <Text style={Tailwind.textCardTitle}>Rebalancing Form</Text>
              {/* Placeholder content */}
            </View>
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
};

export default App;