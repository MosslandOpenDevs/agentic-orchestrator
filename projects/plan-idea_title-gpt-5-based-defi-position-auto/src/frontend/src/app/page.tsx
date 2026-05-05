import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { useColorScheme } from 'react-native';
import {
  SafeAreaView,
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
} from 'react-native';

// Placeholder data - Replace with actual data fetching
interface PortfolioItem {
  asset: string;
  balance: number;
  price: number;
}

const PortfolioDashboard = () => {
  const tailwind = useTailwind();
  const colorScheme = useColorScheme();
  const [theme, setTheme] = useState<string>('light');

  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([
    { asset: 'SOL', balance: 100, price: 150 },
    { asset: 'USDC', balance: 5000, price: 1 },
    { asset: 'LAND', balance: 5, price: 1000 },
  ]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <SafeAreaView style={tailwind.safeAreaView}>
      <View style={[tailwind.container, theme === 'dark' ? tailwind.darkContainer : tailwind.container]}>
        <View style={tailwind.header}>
          <Text style={tailwind.headerText}>TerraForm - Portfolio Dashboard</Text>
          <TouchableOpacity style={tailwind.toggleButton} onPress={toggleTheme}>
            <Text style={tailwind.toggleButtonText}>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</Text>
          </TouchableOpacity>
        </View>

        <ScrollView>
          <View style={tailwind.content}>
            <View style={tailwind.card}>
              <Text style={tailwind.cardTitle}>Portfolio Overview</Text>
              {portfolio.map((item) => (
                <View key={item.asset} style={tailwind.cardItem}>
                  <Text>{item.asset}</Text>
                  <Text>{item.balance}</Text>
                  <Text>{item.price}</Text>
                </View>
              ))}
            </View>

            {/* Placeholder for Rebalancing Settings */}
            <View style={tailwind.card}>
              <Text style={tailwind.cardTitle}>Rebalancing Settings</Text>
              <Text>Coming Soon - Configure your risk tolerance and investment preferences.</Text>
            </View>

            {/* Placeholder for Recommendation Display */}
            <View style={tailwind.card}>
              <Text style={tailwind.cardTitle}>GPT-5 Recommendation</Text>
              <Text>Coming Soon - The AI will generate a rebalancing recommendation based on your settings.</Text>
            </View>
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    backgroundColor: '#f0f0f0',
    padding: 16,
    alignItems: 'center',
    justifyContent: 'space-between',
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
  },
  headerText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  toggleButton: {
    backgroundColor: '#ddd',
    padding: 8,
    borderRadius: 4,
  },
  toggleButtonText: {
    fontSize: 16,
  },
  content: {
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    shadowColor: '#ccc',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.23,
    shadowRadius: 2.62,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  cardItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
});

export default PortfolioDashboard;