// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useEffect, useState } from 'react';
import { Button, Image, StyleSheet, Text, TextInput, View } from 'react-native';

import { brand } from '../config/brand';
import { useConnectivity } from '../context/ConnectivityContext';
import { t } from '../i18n';
import { useAuth } from '../context/AuthContext';
import api, { login, register } from '../services/api';
import { getApiBaseUrl, isDefaultPlaceholderUrl, setApiBaseUrl } from '../services/apiConfig';

export default function LoginScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('consumer');
  const [apiUrl, setApiUrl] = useState('');
  const [error, setError] = useState('');
  const { setIsLoggedIn } = useAuth();
  const { isOnline, isChecking, serverUrl, retry } = useConnectivity();

  useEffect(() => {
    getApiBaseUrl().then((url) => setApiUrl(url));
  }, [serverUrl]);

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

  const statusText = isChecking
    ? 'Checking server...'
    : isOnline
      ? 'Server online'
      : 'Server unavailable. Reconnecting...';

  return (
    <View style={styles.container}>
      <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
      <Text style={styles.title}>{t('appName')}</Text>
      <Text style={[styles.status, isOnline ? styles.online : styles.offline]}>{statusText}</Text>
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
      <Button title="Refresh connection" onPress={retry} />
      <View style={styles.loginButton}>
        <Button
          title={mode === 'login' ? t('login') : t('register')}
          onPress={submit}
          disabled={!isOnline}
        />
      </View>
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
    backgroundColor: brand.lightBackground || '#fff',
  },
  logo: {
    width: 260,
    height: 90,
    alignSelf: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
    color: brand.primaryColor,
  },
  status: {
    textAlign: 'center',
    marginBottom: 16,
    fontSize: 14,
  },
  online: {
    color: '#2e7d32',
  },
  offline: {
    color: '#c62828',
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
  loginButton: {
    marginTop: 12,
  },
  toggle: {
    marginTop: 12,
  },
});
