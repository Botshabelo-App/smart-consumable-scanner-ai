import { getLocales } from 'expo-localization';
import { I18n } from 'i18n-js';

import af from './locales/af.json';
import en from './locales/en.json';
import nr from './locales/nr.json';
import nso from './locales/nso.json';
import ss from './locales/ss.json';
import st from './locales/st.json';
import tn from './locales/tn.json';
import ts from './locales/ts.json';
import ve from './locales/ve.json';
import xh from './locales/xh.json';
import zu from './locales/zu.json';

const i18n = new I18n({
  en,
  af,
  zu,
  xh,
  st,
  tn,
  nso,
  ts,
  ve,
  ss,
  nr,
});

i18n.defaultLocale = 'en';
i18n.locale = getLocales()[0]?.languageCode || 'en';
i18n.enableFallback = true;

export default i18n;
export const t = (key: string, options?: Record<string, any>) => i18n.t(key, options);
