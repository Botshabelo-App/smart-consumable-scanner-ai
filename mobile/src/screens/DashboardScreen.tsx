// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Button, Dimensions, ScrollView, StyleSheet, Text, View } from 'react-native';
import { BarChart, LineChart } from 'react-native-chart-kit';
import MapView, { Marker } from 'react-native-maps';

import { useAuth } from '../context/AuthContext';
import { getAnalytics } from '../services/api';
import { AnalyticsResult } from '../types';

const screenWidth = Dimensions.get('window').width;

export default function DashboardScreen() {
  const [analytics, setAnalytics] = useState<AnalyticsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ActivityIndicator style={{ flex: 1 }} />;
  if (!analytics) return <Text style={styles.center}>No analytics available</Text>;

  const stats = analytics.stats;
  const barData = {
    labels: ['Total', 'Fresh', 'Near', 'Expired', 'Suspicious'],
    datasets: [
      {
        data: [stats.total_scanned, stats.fresh, stats.near_expiry, stats.expired, stats.suspicious],
      },
    ],
  };

  const recent = analytics.time_series.slice(-10);
  const trendData = {
    labels: recent.map((_, i) => String(i + 1)),
    datasets: [{ data: recent.map((s) => s.average_confidence) }],
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Inspection Dashboard</Text>

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

      <Text style={styles.subtitle}>AI confidence trend</Text>
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

      <Text style={styles.subtitle}>Expired by category</Text>
      {analytics.category_expiry.map((c) => (
        <Text key={c.category} style={styles.metric}>
          {c.category}: expired {c.expired}, near {c.near_expiry}, suspicious {c.suspicious}, fresh {c.fresh}
        </Text>
      ))}

      <Text style={styles.subtitle}>Manufacturer trends</Text>
      {analytics.manufacturer_trends.map((m) => (
        <Text key={m.manufacturer_name} style={styles.metric}>
          {m.manufacturer_name}: {m.scan_count} scans, {m.expired_count} expired, {m.suspicious_count} suspicious
        </Text>
      ))}

      {analytics.geographic_distribution.length > 0 && (
        <>
          <Text style={styles.subtitle}>Geographic distribution</Text>
          <MapView
            style={styles.map}
            initialRegion={{
              latitude: analytics.geographic_distribution[0].latitude,
              longitude: analytics.geographic_distribution[0].longitude,
              latitudeDelta: 0.5,
              longitudeDelta: 0.5,
            }}
          >
            {analytics.geographic_distribution.map((g, idx) => (
              <Marker
                key={idx}
                coordinate={{ latitude: g.latitude, longitude: g.longitude }}
                title="Inspection cluster"
                description={`${g.count} inspections`}
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
