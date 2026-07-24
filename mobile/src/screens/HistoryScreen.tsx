// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';

import { getScans } from '../services/api';
import { ScanResult } from '../types';

const conditionEmoji: Record<string, string> = {
  fresh: '🟢',
  near_expiry: '🟡',
  suspicious: '🟠',
  expired: '🔴',
};

export default function HistoryScreen() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getScans()
      .then(setScans)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ActivityIndicator style={{ flex: 1 }} />;

  return (
    <FlatList
      data={scans}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.container}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.name}>
            {conditionEmoji[item.condition] || '⚪'} {item.product_name || 'Unknown product'}
          </Text>
          <Text>Condition: {item.condition}</Text>
          <Text>Confidence: {(item.confidence * 100).toFixed(1)}%</Text>
          <Text>{new Date(item.created_at).toLocaleString()}</Text>
        </View>
      )}
      ListEmptyComponent={<Text style={styles.empty}>No scans yet.</Text>}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
  },
  card: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    marginBottom: 12,
  },
  name: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  empty: {
    textAlign: 'center',
    marginTop: 24,
  },
});
