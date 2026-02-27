import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { LANGUAGES } from '../i18n/i18n'

export default function LanguageSelector() {
  const { i18n, t } = useTranslation()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const current = LANGUAGES.find(l => l.code === i18n.language) ?? LANGUAGES[0]

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const changeLanguage = (code: string) => {
    i18n.changeLanguage(code)
    localStorage.setItem('lang', code)
    // Set text direction for RTL languages (Urdu, Sindhi)
    const rtlCodes = ['ur', 'sd']
    document.documentElement.dir = rtlCodes.includes(code) ? 'rtl' : 'ltr'
    setOpen(false)
  }

  return (
    <div className="lang-selector" ref={ref}>
      <button className="lang-btn" onClick={() => setOpen(!open)} aria-label={t('nav.language')}>
        🌐 {current.nativeLabel}
      </button>
      {open && (
        <div className="lang-dropdown" role="listbox" aria-label="Select language">
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              className={lang.code === i18n.language ? 'selected' : ''}
              role="option"
              aria-selected={lang.code === i18n.language}
              onClick={() => changeLanguage(lang.code)}
            >
              <span className="native-label">{lang.nativeLabel}</span>
              <span className="eng-label">{lang.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
