// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useEffect, useState } from 'react';
import { Button, StyleSheet, Text, TextInput, View } from 'react-native';

import { t } from '../i18n';
import { useAuth } from '../context/AuthContext';
import api, { login, register } from '../services/api';
import { configureApiBaseUrl, getApiBaseUrl, isDefaultPlaceholderUrl, setApiBaseUrl } from '../services/apiConfig';

export default function LoginScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('consumer');
  const [apiUrl, setApiUrl] = useState('');
  const [error, setError] = useState('');
  const { setIsLoggedIn } = useAuth();

  useEffect(() => {
    getApiBaseUrl().then((url) => setApiUrl(url));
  }, []);

  const submit = async () => {
    try {
      setError('');
      await setApiBaseUrl(apiUrl || api.defaults.baseURL || '');
      if (isDefaultPlaceholderUrl(apiUrl)) {
        setError('Please enter a real pilot server URL (tap the server field below).');
        return;
      }
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
      <Text style={styles.title}>{t('appName')}</Text>
      <TextInput
        style={styles.input}
        placeholder={t('serverUrl')}
        autoCapitalize="none"
        value={apiUrl}
        onChangeText={setApiUrl}
      />
      {mode === 'register' && (
        <TextInput style={styles.input} placeholder={t('fullName')} value={fullName} onChangeText={setFullName} />
      )}
      {mode === 'register' && (
        <TextInput style={styles.input} placeholder={t('role')} value={role} onChangeText={setRole} />
      )}
      <TextInput
        style={styles.input}
        placeholder={t('email')}
        autoCapitalize="none"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder={t('password')}
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <Button title={mode === 'login' ? t('login') : t('register')} onPress={submit} />
      <View style={styles.toggle}>
        <Button
          title={mode === 'login' ? t('register') : t('login')}
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
