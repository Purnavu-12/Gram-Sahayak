import { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

/**
 * Maps our i18n language codes to BCP 47 language tags used by the Speech Synthesis API.
 * Browsers vary in which voices they support — this gives the best match for Indian languages.
 */
const LANG_TO_BCP47: Record<string, string> = {
  en:  'en-IN',
  hi:  'hi-IN',
  bn:  'bn-IN',
  te:  'te-IN',
  mr:  'mr-IN',
  ta:  'ta-IN',
  gu:  'gu-IN',
  kn:  'kn-IN',
  ml:  'ml-IN',
  or:  'or-IN',
  pa:  'pa-IN',
  as:  'as-IN',
  ur:  'ur-IN',
  mai: 'mai-IN',
  sat: 'sat-IN',
  ks:  'ks-IN',
  ne:  'ne-NP',
  sd:  'sd-IN',
  doi: 'doi-IN',
  kok: 'kok-IN',
  mni: 'mni-IN',
  brx: 'brx-IN',
  sa:  'sa-IN',
}

export function useSpeech() {
  const { i18n } = useTranslation()
  const [speaking, setSpeaking] = useState(false)
  const [supported, setSupported] = useState(true)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setSupported(false)
      return
    }

    // Voices may load asynchronously in some browsers
    const loadVoices = () => setVoices(window.speechSynthesis.getVoices())
    loadVoices()
    window.speechSynthesis.addEventListener('voiceschanged', loadVoices)
    return () => window.speechSynthesis.removeEventListener('voiceschanged', loadVoices)
  }, [])

  // Stop speech when language changes
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
    }
  }, [i18n.language])

  const speak = useCallback((text: string) => {
    if (!supported) return

    // Cancel any ongoing speech first
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    const bcp47 = LANG_TO_BCP47[i18n.language] || 'en-IN'
    utterance.lang = bcp47

    // Try to find a matching voice for this language
    const langPrefix = bcp47.split('-')[0]
    const match = voices.find(v => v.lang === bcp47)
      || voices.find(v => v.lang.startsWith(langPrefix))
    if (match) {
      utterance.voice = match
    }

    utterance.rate = 0.9
    utterance.onstart = () => setSpeaking(true)
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)

    window.speechSynthesis.speak(utterance)
  }, [i18n.language, supported, voices])

  const stop = useCallback(() => {
    if (!supported) return
    window.speechSynthesis.cancel()
    setSpeaking(false)
  }, [supported])

  return { speak, stop, speaking, supported }
}
