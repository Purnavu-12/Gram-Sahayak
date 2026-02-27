import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import hi from './locales/hi.json';
import bn from './locales/bn.json';
import te from './locales/te.json';
import mr from './locales/mr.json';
import ta from './locales/ta.json';
import gu from './locales/gu.json';
import kn from './locales/kn.json';
import ml from './locales/ml.json';
import or from './locales/or.json';
import pa from './locales/pa.json';
import as_ from './locales/as.json';
import ur from './locales/ur.json';
import mai from './locales/mai.json';
import sat from './locales/sat.json';
import ks from './locales/ks.json';
import ne from './locales/ne.json';
import sd from './locales/sd.json';
import doi from './locales/doi.json';
import kok from './locales/kok.json';
import mni from './locales/mni.json';
import brx from './locales/brx.json';
import sa from './locales/sa.json';

export const LANGUAGES = [
  { code: 'en',  label: 'English',       nativeLabel: 'English',     script: 'Latin' },
  { code: 'hi',  label: 'Hindi',         nativeLabel: 'हिन्दी',        script: 'Devanagari' },
  { code: 'bn',  label: 'Bengali',       nativeLabel: 'বাংলা',        script: 'Bengali' },
  { code: 'te',  label: 'Telugu',        nativeLabel: 'తెలుగు',       script: 'Telugu' },
  { code: 'mr',  label: 'Marathi',       nativeLabel: 'मराठी',        script: 'Devanagari' },
  { code: 'ta',  label: 'Tamil',         nativeLabel: 'தமிழ்',        script: 'Tamil' },
  { code: 'gu',  label: 'Gujarati',      nativeLabel: 'ગુજરાતી',     script: 'Gujarati' },
  { code: 'kn',  label: 'Kannada',       nativeLabel: 'ಕನ್ನಡ',       script: 'Kannada' },
  { code: 'ml',  label: 'Malayalam',     nativeLabel: 'മലയാളം',      script: 'Malayalam' },
  { code: 'or',  label: 'Odia',          nativeLabel: 'ଓଡ଼ିଆ',       script: 'Odia' },
  { code: 'pa',  label: 'Punjabi',       nativeLabel: 'ਪੰਜਾਬੀ',      script: 'Gurmukhi' },
  { code: 'as',  label: 'Assamese',      nativeLabel: 'অসমীয়া',      script: 'Bengali' },
  { code: 'ur',  label: 'Urdu',          nativeLabel: 'اردو',         script: 'Arabic' },
  { code: 'mai', label: 'Maithili',      nativeLabel: 'मैथिली',       script: 'Devanagari' },
  { code: 'sat', label: 'Santali',       nativeLabel: 'ᱥᱟᱱᱛᱟᱲᱤ',    script: 'Ol Chiki' },
  { code: 'ks',  label: 'Kashmiri',      nativeLabel: 'कॉशुर',        script: 'Devanagari' },
  { code: 'ne',  label: 'Nepali',        nativeLabel: 'नेपाली',       script: 'Devanagari' },
  { code: 'sd',  label: 'Sindhi',        nativeLabel: 'سنڌي',         script: 'Arabic' },
  { code: 'doi', label: 'Dogri',         nativeLabel: 'डोगरी',        script: 'Devanagari' },
  { code: 'kok', label: 'Konkani',       nativeLabel: 'कोंकणी',       script: 'Devanagari' },
  { code: 'mni', label: 'Manipuri',      nativeLabel: 'মণিপুরী',     script: 'Bengali' },
  { code: 'brx', label: 'Bodo',          nativeLabel: 'बड़ो',         script: 'Devanagari' },
  { code: 'sa',  label: 'Sanskrit',      nativeLabel: 'संस्कृतम्',    script: 'Devanagari' },
] as const;

export type LanguageCode = typeof LANGUAGES[number]['code'];

const resources: Record<string, { translation: Record<string, unknown> }> = {
  en:  { translation: en },
  hi:  { translation: hi },
  bn:  { translation: bn },
  te:  { translation: te },
  mr:  { translation: mr },
  ta:  { translation: ta },
  gu:  { translation: gu },
  kn:  { translation: kn },
  ml:  { translation: ml },
  or:  { translation: or },
  pa:  { translation: pa },
  as:  { translation: as_ },
  ur:  { translation: ur },
  mai: { translation: mai },
  sat: { translation: sat },
  ks:  { translation: ks },
  ne:  { translation: ne },
  sd:  { translation: sd },
  doi: { translation: doi },
  kok: { translation: kok },
  mni: { translation: mni },
  brx: { translation: brx },
  sa:  { translation: sa },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('lang') || 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
