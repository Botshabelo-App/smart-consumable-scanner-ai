import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Button, FlatList, StyleSheet, Text, TextInput, View } from 'react-native';

import { getBranches, getCompanies, register } from '../services/api';
import { Branch, Company } from '../types';

export default function AdminScreen() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [companyId, setCompanyId] = useState('');
  const [branchName, setBranchName] = useState('');
  const [inspectorEmail, setInspectorEmail] = useState('');
  const [inspectorName, setInspectorName] = useState('');

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      const [c, b] = await Promise.all([getCompanies(), getBranches()]);
      setCompanies(c);
      setBranches(b);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const addInspector = async () => {
    if (!inspectorEmail || !inspectorName) return;
    try {
      await register({
        email: inspectorEmail,
        full_name: inspectorName,
        password: 'changeme123',
        role: 'government_inspector',
        company_id: companyId || undefined,
        branch_id: undefined,
      });
      Alert.alert('Inspector created');
      setInspectorEmail('');
      setInspectorName('');
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || e.message);
    }
  };

  if (loading) return <ActivityIndicator style={{ flex: 1 }} />;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Enterprise Administration</Text>
      <Text style={styles.subtitle}>Companies ({companies.length})</Text>
      <FlatList
        data={companies}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <Text>{item.name}</Text>}
        ListEmptyComponent={<Text>No companies yet.</Text>}
      />
      <Text style={styles.subtitle}>Branches ({branches.length})</Text>
      <FlatList
        data={branches}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <Text>{item.name}</Text>}
        ListEmptyComponent={<Text>No branches yet.</Text>}
      />
      <Text style={styles.subtitle}>Create inspector</Text>
      <TextInput style={styles.input} placeholder="Full name" value={inspectorName} onChangeText={setInspectorName} />
      <TextInput style={styles.input} placeholder="Email" value={inspectorEmail} onChangeText={setInspectorEmail} autoCapitalize="none" />
      <TextInput style={styles.input} placeholder="Company UUID (optional)" value={companyId} onChangeText={setCompanyId} />
      <Button title="Create inspector" onPress={addInspector} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 12 },
  subtitle: { fontSize: 16, fontWeight: '600', marginTop: 12, marginBottom: 4 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, marginBottom: 8 },
});
