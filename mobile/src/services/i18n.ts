// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import * as Speech from 'expo-speech';

import { supportedLanguages } from '../config/brand';
import { Condition } from '../types';

type Messages = Record<Condition, string>;

type VoiceMessages = Record<string, Messages>;

const voiceMessages: VoiceMessages = {
  en: {
    fresh: 'Inspection result: Fresh. Safe to consume.',
    near_expiry: 'Inspection result: Near expiry. Inspect carefully before use.',
    suspicious:
      'Inspection result: Suspicious. Possible label or expiry-date tampering detected, or packaging damage or contamination.',
    expired: 'Inspection result: Expired. Do not consume.',
  },
  zu: {
    fresh: 'Isiphumo sokuhlola: Sisha. Kulungile ukudla.',
    near_expiry: 'Isiphumo sokuhlola: Sakuphelelwa yisikhathi kaseduze. Hlola kahle ngaphambi kokusisebenzisa.',
 suspicious:
      'Isiphumo sokuhlola: Kuningi okungahambi kahle. Kungenzeka kushintshe ilebhuli noma idethi yokuphelelwa, noma iphakheji elimele noma elinobubi.',
    expired: 'Isiphumo sokuhlola: Siphelelwe yisikhathi. Ungaludli.',
  },
  xh: {
    fresh: 'Isiphumo sokuhlola: Tsha. Kulungile ukutya.',
    near_expiry: 'Isiphumo sokuhlola: Kusede ukuphelelwa kwexesha. Hlola kakuhle ngaphambi kokusebenzisa.',
 suspicious:
      'Isiphumo sokuhlola: Ucingo. Kungenzeka ukutshintshwa kwelebhile okanye idethi yokuphelelwa kwexesha, okanye intlako yepakethe okanye ukuxinana.',
    expired: 'Isiphumo sokuhlola: Iphelelwe yixesha. Ungalutyi.',
  },
  af: {
    fresh: 'Inspeksieresultaat: Vars. Veilig vir verbruik.',
    near_expiry: 'Inspeksieresultaat: Naby verstryking. Inspekteer versigtig voor gebruik.',
 suspicious:
      'Inspeksieresultaat: Verdag. Moontlike etiket- of verstrykingsdatum-knoery, of verpakking-skade of kontaminasie.',
    expired: 'Inspeksieresultaat: Verstryk. Moenie verbruik nie.',
  },
  nso: {
    fresh: 'Sephetho sa tekolo: Lefsa. Bolokehile go ja.',
    near_expiry: 'Sephetho sa tekolo: Kgara ya fshelela. Hlahloba ka tlhokomelo pele o dirisa.',
 suspicious:
      'Sephetho sa tekolo: Ke phoso. Go ka bago gore ke go fetotswe lebolo kgotsa letshatsi la kgara, kgotsa go senyegile sephuthelo kgotsa go na le tshilo.',
    expired: 'Sephetho sa tekolo: E feditswe ke nako. O se ke wa ja.',
  },
};

export const languageOptions = supportedLanguages;

export function getVoiceMessage(condition: Condition, lang: string): string {
  return voiceMessages[lang]?.[condition] || voiceMessages.en[condition];
}

export function speak(condition: Condition, lang: string) {
  const text = getVoiceMessage(condition, lang);
  const locale =
    supportedLanguages.find((l) => l.code === lang)?.voiceLocale || 'en-ZA';
  Speech.speak(text, {
    language: locale,
    pitch: 1,
    rate: 0.95,
  });
}
