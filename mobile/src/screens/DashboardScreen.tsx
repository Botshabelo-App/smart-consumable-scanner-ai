import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Button, Dimensions, ScrollView, StyleSheet, Text, View } from 'react-native';
import { BarChart, LineChart } from 'react-native-chart-kit';
import MapView, { Marker } from 'react-native-maps';

import { useAuth } from '../context/AuthContext';
import { getDashboardStats, getScans } from '../services/api';
import { DashboardStats, ScanResult } from '../types';

const screenWidth = Dimensions.get('window').width;

export default function DashboardScreen() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();

  useEffect(() => {
    Promise.all([getDashboardStats(), getScans()])
      .then(([s, list]) => {
        setStats(s);
        setScans(list);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ActivityIndicator style={{ flex: 1 }} />;
  if (!stats) return <Text style={styles.center}>No stats available</Text>;

  const barData = {
    labels: ['Total', 'Fresh', 'Near', 'Expired', 'Suspicious'],
    datasets: [
      {
        data: [stats.total_scanned, stats.fresh, stats.near_expiry, stats.expired, stats.suspicious],
      },
    ],
  };

  // Confidence trend from recent scans
  const recent = [...scans].sort((a, b) => +new Date(a.created_at) - +new Date(b.created_at)).slice(-10);
  const trendLabels = recent.map((_, i) => String(i + 1));
  const trendData = {
    labels: trendLabels,
    datasets: [{ data: recent.map((s) => s.confidence) }],
  };

  const conditionCounts = {
    fresh: stats.fresh,
    near_expiry: stats.near_expiry,
    suspicious: stats.suspicious,
    expired: stats.expired,
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Inspector Dashboard</Text>

      <View style={styles.card}>
        <Text style={styles.metric}>Total inspections: {stats.total_scanned}</Text>
        <Text style={styles.metric}>Fresh: {stats.fresh}</Text>
        <Text style={styles.metric}>Near expiry: {stats.near_expiry}</Text>
        <Text style={styles.metric}>Expired: {stats.expired}</Text>
        <Text style={styles.metric}>Suspicious: {stats.suspicious}</Text>
        <Text style={styles.metric}>Reports generated: {stats.reports_generated}</Text>
        <Text style={styles.metric}>Average AI confidence: {(stats.average_confidence * 100).toFixed(1)}%</Text>
      </View>

      <Text style={styles.subtitle}>Inspection breakdown</Text>
      <BarChart
        data={barData}
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

      <Text style={styles.subtitle}>AI confidence trend (last 10 scans)</Text>
      <LineChart
        data={trendData}
        width={screenWidth - 32}
        height={200}
        chartConfig={{
          backgroundColor: '#ffffff',
          backgroundGradientFrom: '#ffffff',
          backgroundGradientTo: '#ffffff',
          decimalPlaces: 2,
          color: (opacity = 1) => `rgba(46, 125, 50, ${opacity})`,
        }}
        bezier
        style={{ marginVertical: 16, borderRadius: 8 }}
      />

      {scans.some((s) => s.latitude && s.longitude) && (
        <>
          <Text style={styles.subtitle}>GPS map of inspections</Text>
          <MapView
            style={styles.map}
            initialRegion={{
              latitude: scans.find((s) => s.latitude)!.latitude!,
              longitude: scans.find((s) => s.longitude)!.longitude!,
              latitudeDelta: 0.5,
              longitudeDelta: 0.5,
            }}
          >
            {scans
              .filter((s) => s.latitude && s.longitude)
              .map((s) => (
                <Marker
                  key={s.id}
                  coordinate={{ latitude: s.latitude!, longitude: s.longitude! }}
                  title={s.product_name || 'Inspection'}
                  description={`${s.condition} (${(s.confidence * 100).toFixed(0)}%)`}
                />
              ))}
          </MapView>
        </>
      )}

      <Button title="Log out" onPress={logout} />
      <View style={{ height: 24 }} />
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
  subtitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
  },
  card: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    gap: 8,
  },
  metric: {
    fontSize: 15,
  },
  map: {
    width: screenWidth - 32,
    height: 300,
    marginVertical: 16,
    borderRadius: 8,
  },
  center: {
    flex: 1,
    textAlign: 'center',
    textAlignVertical: 'center',
  },
});
