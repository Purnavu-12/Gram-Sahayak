import { useState } from 'react'
import { useTranslation } from 'react-i18next'

const STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat',
  'Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh',
  'Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab',
  'Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh',
  'Uttarakhand','West Bengal','Delhi','Jammu & Kashmir','Ladakh','Puducherry',
  'Chandigarh','Andaman & Nicobar','Dadra & Nagar Haveli','Daman & Diu','Lakshadweep',
]

interface SchemeResult {
  id: string
  name: string
  matchScore: number
  eligibility: 'eligible' | 'likely_eligible'
  benefit: number
  difficulty: 'easy' | 'medium' | 'hard'
  reason: string
}

// Demo scheme data (in a real app this comes from the API)
const DEMO_SCHEMES: SchemeResult[] = [
  { id: 'pm-kisan', name: 'PM-KISAN', matchScore: 95, eligibility: 'eligible', benefit: 6000, difficulty: 'easy', reason: 'Farmer income support — ₹6,000/year' },
  { id: 'mgnrega', name: 'MGNREGA', matchScore: 90, eligibility: 'eligible', benefit: 25000, difficulty: 'easy', reason: '100 days guaranteed employment' },
  { id: 'ayushman-bharat', name: 'Ayushman Bharat', matchScore: 85, eligibility: 'likely_eligible', benefit: 500000, difficulty: 'medium', reason: '₹5 lakh health insurance coverage' },
  { id: 'pmay-g', name: 'PM Awas Yojana (Gramin)', matchScore: 78, eligibility: 'likely_eligible', benefit: 120000, difficulty: 'hard', reason: 'Housing assistance for rural families' },
  { id: 'pmjdy', name: 'PM Jan Dhan Yojana', matchScore: 92, eligibility: 'eligible', benefit: 10000, difficulty: 'easy', reason: 'Zero balance bank account + insurance' },
]

export default function SchemesPage() {
  const { t } = useTranslation()
  const [results, setResults] = useState<SchemeResult[] | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setResults(DEMO_SCHEMES)
      setLoading(false)
    }, 800)
  }

  const difficultyBadge = (d: string) => {
    const map: Record<string, string> = { easy: 'badge-easy', medium: 'badge-medium', hard: 'badge-hard' }
    const labelMap: Record<string, string> = { easy: t('schemes.results_easy'), medium: t('schemes.results_medium'), hard: t('schemes.results_hard') }
    return <span className={`badge ${map[d] || ''}`}>{labelMap[d]}</span>
  }

  return (
    <div className="page">
      <h1>{t('schemes.title')}</h1>
      <p className="subtitle">{t('schemes.subtitle')}</p>

      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <div className="form-grid">
            <div className="form-group">
              <label>{t('schemes.form_age')}</label>
              <input type="number" min="1" max="120" placeholder="25" required />
            </div>
            <div className="form-group">
              <label>{t('schemes.form_gender')}</label>
              <select required>
                <option value="">{t('common.select')}</option>
                <option value="male">{t('schemes.form_gender_male')}</option>
                <option value="female">{t('schemes.form_gender_female')}</option>
                <option value="other">{t('schemes.form_gender_other')}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t('schemes.form_state')}</label>
              <select required>
                <option value="">{t('common.select')}</option>
                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>{t('schemes.form_occupation')}</label>
              <select required>
                <option value="">{t('common.select')}</option>
                <option value="farmer">{t('schemes.form_occupation_farmer')}</option>
                <option value="laborer">{t('schemes.form_occupation_laborer')}</option>
                <option value="self_employed">{t('schemes.form_occupation_self_employed')}</option>
                <option value="student">{t('schemes.form_occupation_student')}</option>
                <option value="unemployed">{t('schemes.form_occupation_unemployed')}</option>
                <option value="other">{t('schemes.form_occupation_other')}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t('schemes.form_income')}</label>
              <input type="number" min="0" placeholder="100000" required />
            </div>
            <div className="form-group">
              <label>{t('schemes.form_caste')}</label>
              <select required>
                <option value="">{t('common.select')}</option>
                <option value="general">{t('schemes.form_caste_general')}</option>
                <option value="obc">{t('schemes.form_caste_obc')}</option>
                <option value="sc">{t('schemes.form_caste_sc')}</option>
                <option value="st">{t('schemes.form_caste_st')}</option>
                <option value="ews">{t('schemes.form_caste_ews')}</option>
              </select>
            </div>
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? t('common.loading') : t('schemes.form_submit')}
        </button>
      </form>

      {/* Results */}
      {results && (
        <div style={{ marginTop: '2rem' }}>
          <h2 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>{t('schemes.results_title')}</h2>
          {results.length === 0 ? (
            <div className="empty-state">
              <div className="icon">🔍</div>
              <p>{t('schemes.results_none')}</p>
            </div>
          ) : (
            results.map(scheme => (
              <div key={scheme.id} className="scheme-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <h3>{scheme.name}</h3>
                  <span className={`badge ${scheme.eligibility === 'eligible' ? 'badge-eligible' : 'badge-likely'}`}>
                    {scheme.eligibility === 'eligible' ? t('schemes.results_eligible') : t('schemes.results_likely')}
                  </span>
                </div>
                <p style={{ color: 'var(--text-light)', margin: '0.5rem 0' }}>{scheme.reason}</p>
                <div className="meta">
                  <span>💰 {t('schemes.results_benefit')}: ₹{scheme.benefit.toLocaleString()}</span>
                  <span>{t('schemes.results_difficulty')}: {difficultyBadge(scheme.difficulty)}</span>
                </div>
                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                  <button className="btn btn-green" style={{ padding: '0.4rem 1rem', fontSize: '0.9rem' }}>{t('schemes.results_apply')}</button>
                  <button className="btn btn-outline" style={{ padding: '0.4rem 1rem', fontSize: '0.9rem', color: 'var(--primary)', borderColor: 'var(--primary)' }}>{t('schemes.results_details')}</button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
