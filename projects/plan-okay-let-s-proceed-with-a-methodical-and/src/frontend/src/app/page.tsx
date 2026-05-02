import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { Typography, Space, Card, Avatar, Skeleton } from 'antd';
import { BarChart } from 'react-alice-charts';
import { useMediaQuery } from 'react-use';
import { useLocalSearchParams } from 'react-use';

const { Typography as AntTypography } = Typography;
const { CardContent } = Card;

const Dashboard = () => {
  const [darkMode, setDarkMode] = useMediaQuery('(prefers-dark)');
  const tailwind = useTailwind({ darkMode });

  const [loading, setLoading] = useState(true);
  const searchParams = useLocalSearchParams();

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setLoading(false);
    }, 1500);
  }, []);

  if (loading) {
    return (
      <Space style={tailwind.space}>
        <Skeleton active={true} />
      </Space>
    );
  }

  const data = [
    {
      title: 'NFT Sales',
      value: 12345,
      icon: 'diamond',
    },
    {
      title: 'Total NFTs',
      value: 5678,
      icon: 'palette',
    },
    {
      title: 'User Activity',
      value: 9012,
      icon: 'users',
    },
  ];

  const chartData = {
    title: 'NFT Sales Trend',
    xLabels: ['Jan', 'Feb', 'Mar', 'Apr'],
    data: [5000, 6000, 7500, 8000],
  };

  return (
    <div className={tailwind.container}>
      <header className={tailwind.header}>
        <AntTypography title="Dashboard" style={tailwind.headerTitle} />
      </header>

      <main className={tailwind.main}>
        <Card className={tailwind.card}>
          <CardContent>
            <AntTypography title="NFT Sales Overview" strong={true} style={tailwind.cardTitle} />
            <Space style={tailwind.space}>
              {data.map((item) => (
                <Card key={item.title} style={tailwind.cardItem}>
                  <AntTypography strong={true}>{item.title}</AntTypography>
                  <AntTypography>{item.value}</AntTypography>
                  <Avatar shape="square" size={28} src="https://via.placeholder.com/140x140.png/007bff" />
                </Card>
              ))}
            </Space>
          </CardContent>
        </Card>

        <Card className={tailwind.card}>
          <CardContent>
            <AntTypography title="NFT Sales Trend" strong={true} style={tailwind.cardTitle} />
            <BarChart
              data={chartData}
              width={600}
              height={300}
              xLabels={chartData.xLabels}
            />
          </CardContent>
        </Card>
      </main>

      <footer className={tailwind.footer}>
        <AntTypography title="Copyright 2024" style={tailwind.footerTitle} />
      </footer>
    </div>
  );
};

export default Dashboard;