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

const Tailwind = useTailwind();

type PortfolioItem = {
  tokenId: string;
  name: string;
  nftImage: string;
  quantity: number;
  price: number;
};

type AppState {
  portfolio: PortfolioItem[];
  loading: boolean;
  theme: 'light' | 'dark';
}

const App: React.FC<AppState> = () => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [theme, setTheme] = useState<string>('light');

  useEffect(() => {
    // Simulate fetching data
    const fetchData = async () => {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call delay

      const mockPortfolioData: PortfolioItem[] = [
        { tokenId: '1', name: 'Mossland NFT 1', nftImage: 'https://example.com/mossland1.png', quantity: 5, price: 150 },
        { tokenId: '2', name: 'Mossland NFT 2', nftImage: 'https://example.com/mossland2.png', quantity: 10, price: 120 },
        { tokenId: '3', name: 'Mossland NFT 3', nftImage: 'https://example.com/mossland3.png', quantity: 3, price: 200 },
      ];
      setPortfolio(mockPortfolioData);
      setLoading(false);
    };

    fetchData();
  }, []);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <SafeAreaView style={Tailwind.safeContainer}>
      <View style={[Tailwind.container, Tailwind.bgGray100]}>
        <View style={Tailwind.shadowBox}>
          <Text style={Tailwind.title}>Mossland DeFi Dashboard</Text>
          <Text style={Tailwind.subtitle}>Your Portfolio & Rebalancing Insights</Text>

          <Text style={Tailwind.description}>
            Estimated Cost: $66,000 - $93,000
          </Text>

          <View style={Tailwind.cardContainer}>
            <Text style={Tailwind.cardTitle}>Portfolio Summary</Text>
            {loading ? (
              <Text style={Tailwind.loadingText}>Loading...</Text>
            ) : (
              <ScrollView horizontal>
                {portfolio.map((item) => (
                  <View
                    key={item.tokenId}
                    style={[
                      Tailwind.card,
                      { borderBottomWidth: 1, borderColor: Tailwind.bgGray300 },
                    ]}
                  >
                    <Image source={{ uri: item.nftImage }} style={Tailwind.image} />
                    <Text style={Tailwind.cardText}>{item.name}</Text>
                    <Text style={Tailwind.cardText}>
                      Quantity: {item.quantity}
                    </Text>
                    <Text style={Tailwind.cardText}>
                      Price: ${item.price}
                    </Text>
                  </View>
                ))}
              </ScrollView>
            )}
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
};

export default App;