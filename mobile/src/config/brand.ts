// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

// Organisation-wide branding and behaviour configuration.
// Modify values here to rebrand the pilot build without touching core screens.

export const brand = {
  appName: 'Smart Consumable Scanner AI',
  tagline: 'AI-powered consumable inspection',
  primaryColor: '#0d5aa3',
  secondaryColor: '#2e7d32',
  dangerColor: '#c62828',
  warningColor: '#ef6c00',
  lightBackground: '#f5f7fa',
  defaultBackendUrl: 'https://injured-capabilities-edt-blocking.trycloudflare.com',
};

export const supportedLanguages: { code: string; name: string; voiceLocale: string }[] = [
  { code: 'en', name: 'English', voiceLocale: 'en-ZA' },
  { code: 'zu', name: 'isiZulu', voiceLocale: 'zu-ZA' },
  { code: 'xh', name: 'isiXhosa', voiceLocale: 'xh-ZA' },
  { code: 'af', name: 'Afrikaans', voiceLocale: 'af-ZA' },
  { code: 'nso', name: 'Sesotho', voiceLocale: 'nso-ZA' },
];

export const defaultLanguage = 'en';

export const offlineConfig = {
  maxOfflineScans: 200,
  syncOnStartup: true,
  syncIntervalMs: 30000,
  retryAttempts: 5,
};
