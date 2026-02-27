import { useTranslation } from 'react-i18next'

export default function AboutPage() {
  const { t } = useTranslation()

  return (
    <div className="page">
      <h1>{t('about.title')}</h1>

      <div className="about-section">
        <h2>{t('about.mission')}</h2>
        <p style={{ color: 'var(--text-light)' }}>{t('about.mission_text')}</p>
      </div>

      <div className="about-section">
        <h2>{t('about.features_title')}</h2>
        <ul>
          <li>{t('about.feature_voice')}</li>
          <li>{t('about.feature_ai')}</li>
          <li>{t('about.feature_forms')}</li>
          <li>{t('about.feature_track')}</li>
          <li>{t('about.feature_offline')}</li>
          <li>{t('about.feature_accessible')}</li>
        </ul>
      </div>

      <div className="about-section">
        <h2>{t('about.tech_title')}</h2>
        <p style={{ color: 'var(--text-light)' }}>{t('about.tech_text')}</p>
      </div>

      <div className="about-section">
        <h2>{t('about.contact_title')}</h2>
        <p style={{ color: 'var(--text-light)' }}>{t('about.contact_text')}</p>
      </div>
    </div>
  )
}
