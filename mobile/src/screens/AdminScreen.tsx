// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import { Alert, Button, RefreshControl, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import {
  createBranch, createInspector, errorMessage, getBranches, getMe, getUsers, resetUserPassword, setUserActive,
} from '../services/api';
import { Branch, UserAccount } from '../types';

const ROLES = [
  { key: 'school_food_inspector', label: 'School food inspector' },
  { key: 'government_inspector', label: 'Government inspector' },
  { key: 'municipal_health_inspector', label: 'Municipal health inspector' },
  { key: 'company_admin', label: 'Organisation admin' },
];

function strongPasswordProblem(p: string): string | null {
  if (p.length < 8) return 'Password must be at least 8 characters.';
  if (!/[A-Za-z]/.test(p) || !/\d/.test(p)) return 'Password must contain letters and digits.';
  return null;
}

export default function AdminScreen() {
  const [me, setMe] = useState<UserAccount | null>(null);
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [siteName, setSiteName] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('school_food_inspector');
  const [branchId, setBranchId] = useState<string | undefined>();
  const [resetFor, setResetFor] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const u = await getMe();
      setMe(u);
      if (u.role === 'company_admin' || u.role === 'administrator') {
        const [list, b] = await Promise.all([getUsers(), getBranches(u.company_id)]);
        setUsers(list);
        setBranches(b);
      }
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  if (me && me.role !== 'company_admin' && me.role !== 'administrator') {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Administration</Text>
        <Text>Signed in as {me.full_name} ({me.email}), role {me.role}.</Text>
        <Text style={styles.small}>Only organisation admins can manage inspectors and sites.</Text>
      </View>
    );
  }

  const addSite = async () => {
    if (!me?.company_id || siteName.trim().length < 2) return Alert.alert('Site name required');
    try {
      await createBranch(me.company_id, siteName.trim());
      setSiteName('');
      await load();
    } catch (e) {
      Alert.alert('Not saved', errorMessage(e));
    }
  };

  const addInspector = async () => {
    const problem = strongPasswordProblem(password);
    if (!name.trim() || !email.trim()) return Alert.alert('Name and email are required');
    if (problem) return Alert.alert('Weak password', problem);
    try {
      await createInspector({ email: email.trim().toLowerCase(), full_name: name.trim(), password, role, company_id: me?.company_id, branch_id: branchId });
      Alert.alert('Inspector created', `${name} can now log in with ${email}. Give them the password privately; they should keep it secret.`);
      setName('');
      setEmail('');
      setPassword('');
      await load();
    } catch (e) {
      Alert.alert('Not created', errorMessage(e));
    }
  };

  const doReset = async (u: UserAccount) => {
    const problem = strongPasswordProblem(newPassword);
    if (problem) return Alert.alert('Weak password', problem);
    try {
      await resetUserPassword(u.id, newPassword);
      Alert.alert('Password reset', `New password set for ${u.email}.`);
      setResetFor(null);
      setNewPassword('');
    } catch (e) {
      Alert.alert('Not saved', errorMessage(e));
    }
  };

  const siteName_ = (id?: string) => branches.find((b) => b.id === id)?.name || 'No site';

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}>
      <Text style={styles.title}>Administration</Text>
      {me && <Text style={styles.small}>Organisation: {me.organization || '—'}  •  you: {me.full_name} ({me.role})</Text>}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.subtitle}>Schools / sites ({branches.length})</Text>
      {branches.map((b) => <Text key={b.id} style={styles.line}>• {b.name}</Text>)}
      <TextInput style={styles.input} placeholder="New school / site name" value={siteName} onChangeText={setSiteName} />
      <Button title="Add site" onPress={addSite} />

      <Text style={styles.subtitle}>Create inspector</Text>
      <TextInput style={styles.input} placeholder="Full name" value={name} onChangeText={setName} />
      <TextInput style={styles.input} placeholder="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
      <TextInput style={styles.input} placeholder="Initial password (8+ letters and digits)" value={password} onChangeText={setPassword} secureTextEntry autoCapitalize="none" />
      <View style={styles.chips}>
        {ROLES.map((r) => (
          <TouchableOpacity key={r.key} onPress={() => setRole(r.key)} style={[styles.chip, role === r.key && styles.chipOn]}>
            <Text style={role === r.key ? { color: '#fff' } : undefined}>{r.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.chips}>
        <TouchableOpacity onPress={() => setBranchId(undefined)} style={[styles.chip, !branchId && styles.chipOn]}>
          <Text style={!branchId ? { color: '#fff' } : undefined}>No site</Text>
        </TouchableOpacity>
        {branches.map((b) => (
          <TouchableOpacity key={b.id} onPress={() => setBranchId(b.id)} style={[styles.chip, branchId === b.id && styles.chipOn]}>
            <Text style={branchId === b.id ? { color: '#fff' } : undefined}>{b.name}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Button title="Create inspector" onPress={addInspector} />

      <Text style={styles.subtitle}>Users in your organisation ({users.length})</Text>
      {users.map((u) => (
        <View key={u.id} style={styles.user}>
          <Text style={styles.name}>{u.full_name} {u.is_active ? '' : '(deactivated)'}</Text>
          <Text style={styles.small}>{u.email}  •  {u.role}  •  {siteName_(u.branch_id)}</Text>
          {u.id !== me?.id && (
            <View style={styles.row}>
              <Button
                title={u.is_active ? 'Deactivate' : 'Activate'}
                color={u.is_active ? '#c62828' : '#2e7d32'}
                onPress={async () => {
                  try { await setUserActive(u.id, !u.is_active); await load(); } catch (e) { Alert.alert('Not saved', errorMessage(e)); }
                }}
              />
              <Button title="Reset password" onPress={() => { setResetFor(resetFor === u.id ? null : u.id); setNewPassword(''); }} />
            </View>
          )}
          {resetFor === u.id && (
            <View>
              <TextInput style={styles.input} placeholder="New password" value={newPassword} onChangeText={setNewPassword} secureTextEntry autoCapitalize="none" />
              <Button title="Save new password" onPress={() => doReset(u)} />
            </View>
          )}
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: 'bold' },
  subtitle: { fontSize: 16, fontWeight: '600', marginTop: 18, marginBottom: 6 },
  small: { fontSize: 12, color: '#555' },
  line: { fontSize: 14, marginBottom: 2 },
  error: { color: '#c62828', marginVertical: 6 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 8, marginVertical: 4 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginVertical: 4 },
  chip: { borderWidth: 1, borderColor: '#1565c0', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 4, margin: 2 },
  chipOn: { backgroundColor: '#1565c0' },
  user: { paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#eee' },
  name: { fontWeight: '600' },
  row: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 4 },
});
