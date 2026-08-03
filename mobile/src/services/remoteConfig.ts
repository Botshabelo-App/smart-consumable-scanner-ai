// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

const BACKEND_URL_SOURCE =
  'https://raw.githubusercontent.com/Botshabelo-App/smart-consumable-scanner-ai/devin/initial-scaffold/backend-url.txt';

export async function fetchRemoteBackendUrl(): Promise<string | null> {
  try {
    const cacheBuster = `?t=${Date.now()}`;
    const response = await fetch(BACKEND_URL_SOURCE + cacheBuster, { cache: 'no-cache' });
    if (!response.ok) return null;
    const text = (await response.text()).trim();
    if (text.startsWith('http')) return text;
    return null;
  } catch {
    return null;
  }
}
