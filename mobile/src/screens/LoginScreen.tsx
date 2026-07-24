import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useState } from 'react';
import { Button, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '../context/AuthContext';
import { login, register } from '../services/api';

export default function LoginScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('consumer');
  const [error, setError] = useState('');
  const { setIsLoggedIn } = useAuth();

  const submit = async () => {
    try {
      setError('');
      if (mode === 'login') {
        await login(email, password);
        setIsLoggedIn(true);
      } else {
        await register({ email, full_name: fullName, password, role });
        await login(email, password);
        setIsLoggedIn(true);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || 'Something went wrong');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Smart Consumable Scanner AI</Text>
      {mode === 'register' && (
        <TextInput
          style={styles.input}
          placeholder="Full name"
          value={fullName}
          onChangeText={setFullName}
        />
      )}
      {mode === 'register' && (
        <TextInput
          style={styles.input}
          placeholder="Role"
          value={role}
          onChangeText={setRole}
        />
      )}
      <TextInput
        style={styles.input}
        placeholder="Email"
        autoCapitalize="none"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <Button title={mode === 'login' ? 'Log in' : 'Register'} onPress={submit} />
      <View style={styles.toggle}>
        <Button
          title={mode === 'login' ? 'Switch to register' : 'Switch to login'}
          onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 24,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  error: {
    color: 'red',
    marginBottom: 12,
  },
  toggle: {
    marginTop: 12,
  },
});
