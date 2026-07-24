import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Button, ScrollView, StyleSheet, Text, View } from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';

import { useAuth } from '../context/AuthContext';
import { getDashboardStats } from '../services/api';
import { DashboardStats } from '../types';

const screenWidth = Dimensions.get('window').width;

export default function DashboardScreen() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ActivityIndicator style={{ flex: 1 }} />;
  if (!stats) return <Text style={styles.center}>No stats available</Text>;

  const data = {
    labels: ['Total', 'Fresh', 'Near', 'Expired', 'Suspicious'],
    datasets: [
      {
        data: [stats.total_scanned, stats.fresh, stats.near_expiry, stats.expired, stats.suspicious],
      },
    ],
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Inspection Dashboard</Text>
      <View style={styles.card}>
        <Text>Total Scanned: {stats.total_scanned}</Text>
        <Text>Fresh: {stats.fresh}</Text>
        <Text>Near Expiry: {stats.near_expiry}</Text>
        <Text>Expired: {stats.expired}</Text>
        <Text>Suspicious: {stats.suspicious}</Text>
        <Text>Reports: {stats.reports_generated}</Text>
        <Text>Avg Confidence: {(stats.average_confidence * 100).toFixed(1)}%</Text>
      </View>
      <BarChart
        data={data}
        width={screenWidth - 32}
        height={220}
        yAxisLabel=""
        yAxisSuffix=""
        chartConfig={{
          backgroundColor: '#ffffff',
          backgroundGradientFrom: '#ffffff',
          backgroundGradientTo: '#ffffff',
          decimalPlaces: 0,
          color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
        }}
        style={{ marginVertical: 16, borderRadius: 8 }}
      />
      <Button title="Log out" onPress={useAuth().logout} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  card: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    gap: 8,
  },
  center: {
    flex: 1,
    textAlign: 'center',
    textAlignVertical: 'center',
  },
});
