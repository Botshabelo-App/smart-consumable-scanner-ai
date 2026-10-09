// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Button, Dimensions, RefreshControl, ScrollView, StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import { BarChart } from 'react-native-chart-kit';

import { RESULT_COLOR, RESULT_LABEL } from '../components/InspectionFields';
import { useAuth } from '../context/AuthContext';
import { errorMessage, getDashboardSummary } from '../services/api';
import { getVoiceEnabled, setVoiceEnabled } from '../services/i18n';
import { DashboardSummary } from '../types';

const screenWidth = Dimensions.get('window').width;

function Tile({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <View style={[styles.tile, color ? { borderLeftColor: color } : null]}>
      <Text style={styles.tileValue}>{value}</Text>
      <Text style={styles.tileLabel}>{label}</Text>
    </View>
  );
}

export default function DashboardScreen({ navigation }: any) {
  const [s, setS] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [voice, setVoice] = useState(true);
  const { logout } = useAuth();

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setS(await getDashboardSummary());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
      getVoiceEnabled().then(setVoice);
    }, [load])
  );

  const trend = (s?.trend || []).slice(-7);

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}>
      <Text style={styles.title}>Inspection Dashboard</Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!s && loading ? <ActivityIndicator /> : null}
      {s && (
        <>
          <View style={styles.tiles}>
            <Tile label="Total inspections" value={s.total} />
            <Tile label="Today" value={s.today} />
            <Tile label="PASS" value={s.pass_count} color={RESULT_COLOR.PASS_NO_VISIBLE_ANOMALY} />
            <Tile label="WARNING" value={s.warning} color={RESULT_COLOR.WARNING} />
            <Tile label="REVIEW" value={s.review} color={RESULT_COLOR.REVIEW} />
            <Tile label="Insufficient data" value={s.insufficient_data} color={RESULT_COLOR.INSUFFICIENT_DATA} />
            <Tile label="Expired products" value={s.expired_products} color="#c62828" />
            <Tile label="Awaiting review" value={s.awaiting_review} color="#ef6c00" />
            <Tile label="Signed off" value={s.signed_off} color="#1565c0" />
          </View>

          {trend.length > 0 && (
            <>
              <Text style={styles.subtitle}>Inspections per day (last {trend.length} days with scans)</Text>
              <BarChart
                data={{ labels: trend.map((t) => t.date.slice(5)), datasets: [{ data: trend.map((t) => t.total) }] }}
                width={screenWidth - 32}
                height={200}
                yAxisLabel=""
                yAxisSuffix=""
                fromZero
                chartConfig={{
                  backgroundColor: '#fff', backgroundGradientFrom: '#fff', backgroundGradientTo: '#fff', decimalPlaces: 0,
                  color: (o = 1) => `rgba(21, 101, 192, ${o})`, labelColor: () => '#333',
                }}
                style={{ borderRadius: 8 }}
              />
            </>
          )}

          <Text style={styles.subtitle}>By school / site</Text>
          {s.by_site.map((x) => (
            <Text key={x.site} style={styles.line}>{x.site}: {x.total} (pass {x.pass}, warning {x.warning}, review {x.review})</Text>
          ))}
          <Text style={styles.subtitle}>By inspector</Text>
          {s.by_inspector.map((x) => (
            <Text key={x.inspector} style={styles.line}>{x.inspector}: {x.total} (pass {x.pass}, warning {x.warning}, review {x.review})</Text>
          ))}

          <Text style={styles.subtitle}>Latest inspections</Text>
          {s.recent.map((r) => (
            <TouchableOpacity key={r.id} onPress={() => navigation.navigate('ScanDetail', { scanId: r.id })}>
              <Text style={[styles.line, { color: RESULT_COLOR[r.overall_result || ''] || '#333' }]}>
                {r.product_name || 'Product not detected'} – {RESULT_LABEL[r.overall_result || ''] || r.overall_result}
                {r.created_at ? `  (${new Date(r.created_at).toLocaleString()})` : ''}
              </Text>
            </TouchableOpacity>
          ))}
        </>
      )}

      <View style={styles.setting}>
        <Text style={{ flex: 1 }}>Voice announcements (PASS / WARNING / REVIEW)</Text>
        <Switch value={voice} onValueChange={(v) => { setVoice(v); setVoiceEnabled(v); }} />
      </View>
      <View style={{ marginVertical: 20 }}>
        <Button title="Logout" onPress={logout} color="#c62828" />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 10 },
  subtitle: { fontSize: 16, fontWeight: '600', marginTop: 16, marginBottom: 6 },
  tiles: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  tile: { width: '32%', backgroundColor: '#f5f7fa', borderRadius: 8, padding: 8, marginBottom: 6, borderLeftWidth: 4, borderLeftColor: '#90a4ae' },
  tileValue: { fontSize: 20, fontWeight: 'bold' },
  tileLabel: { fontSize: 11, color: '#555' },
  line: { fontSize: 13, marginBottom: 3 },
  error: { color: '#c62828' },
  setting: { flexDirection: 'row', alignItems: 'center', marginTop: 20, padding: 10, backgroundColor: '#f5f7fa', borderRadius: 8 },
});
