import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

export default function HomePage() {
  const { t } = useTranslation()

  return (
    <div>
      {/* Hero */}
      <section className="hero">
        <h1>{t('home.hero_title')}</h1>
        <p>{t('home.hero_subtitle')}</p>
        <div className="hero-buttons">
          <Link to="/schemes" className="btn btn-primary">{t('home.cta_find_schemes')}</Link>
          <button className="btn btn-outline">{t('home.cta_voice')}</button>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <div className="feature-card">
          <div className="icon">🗣️</div>
          <h3>{t('home.feature1_title')}</h3>
          <p>{t('home.feature1_desc')}</p>
        </div>
        <div className="feature-card">
          <div className="icon">🔍</div>
          <h3>{t('home.feature2_title')}</h3>
          <p>{t('home.feature2_desc')}</p>
        </div>
        <div className="feature-card">
          <div className="icon">📋</div>
          <h3>{t('home.feature3_title')}</h3>
          <p>{t('home.feature3_desc')}</p>
        </div>
      </section>

      {/* Stats */}
      <section className="stats-bar">
        <div className="stat">
          <div className="number">2,500+</div>
          <div className="label">{t('home.stats_schemes')}</div>
        </div>
        <div className="stat">
          <div className="number">23</div>
          <div className="label">{t('home.stats_languages')}</div>
        </div>
        <div className="stat">
          <div className="number">36</div>
          <div className="label">{t('home.stats_states')}</div>
        </div>
      </section>

      {/* How It Works */}
      <section className="steps-section">
        <h2>{t('home.how_it_works')}</h2>
        <div className="steps">
          <div className="step">
            <div className="num">1</div>
            <h3>{t('home.step1_title')}</h3>
            <p>{t('home.step1_desc')}</p>
          </div>
          <div className="step">
            <div className="num">2</div>
            <h3>{t('home.step2_title')}</h3>
            <p>{t('home.step2_desc')}</p>
          </div>
          <div className="step">
            <div className="num">3</div>
            <h3>{t('home.step3_title')}</h3>
            <p>{t('home.step3_desc')}</p>
          </div>
        </div>
      </section>
    </div>
  )
}
