import { useState } from 'react'
import { useTranslation } from 'react-i18next'

const STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat',
  'Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh',
  'Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab',
  'Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh',
  'Uttarakhand','West Bengal','Delhi','Jammu & Kashmir','Ladakh',
]

export default function ProfilePage() {
  const { t } = useTranslation()
  const [saved, setSaved] = useState(false)

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="page">
      <h1>{t('profile.title')}</h1>
      <p className="subtitle">{t('profile.subtitle')}</p>

      {saved && <div className="alert alert-success">✓ {t('profile.saved_success')}</div>}

      <form onSubmit={handleSubmit}>
        {/* Personal Information */}
        <div className="form-section">
          <h2>{t('profile.personal')}</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>{t('profile.name')}</label>
              <input type="text" required />
            </div>
            <div className="form-group">
              <label>{t('profile.age')}</label>
              <input type="number" min="1" max="120" required />
            </div>
            <div className="form-group">
              <label>{t('profile.gender')}</label>
              <select required>
                <option value="">{t('common.select')}</option>
                <option value="male">{t('schemes.form_gender_male')}</option>
                <option value="female">{t('schemes.form_gender_female')}</option>
                <option value="other">{t('schemes.form_gender_other')}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t('profile.phone')}</label>
              <input type="tel" pattern="[0-9]{10}" placeholder="9876543210" required />
            </div>
          </div>
        </div>

        {/* Location */}
        <div className="form-section">
          <h2>{t('profile.location')}</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>{t('profile.state')}</label>
              <select required>
                <option value="">{t('common.select')}</option>
                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>{t('profile.district')}</label>
              <input type="text" required />
            </div>
            <div className="form-group">
              <label>{t('profile.block')}</label>
              <input type="text" />
            </div>
            <div className="form-group">
              <label>{t('profile.village')}</label>
              <input type="text" required />
            </div>
          </div>
        </div>

        {/* Economic */}
        <div className="form-section">
          <h2>{t('profile.economic')}</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>{t('profile.income')}</label>
              <input type="number" min="0" required />
            </div>
            <div className="form-group">
              <label>{t('profile.occupation')}</label>
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
              <label>{t('profile.land')}</label>
              <select>
                <option value="no">{t('profile.land_no')}</option>
                <option value="yes">{t('profile.land_yes')}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t('profile.bank')}</label>
              <select>
                <option value="yes">{t('profile.bank_yes')}</option>
                <option value="no">{t('profile.bank_no')}</option>
              </select>
            </div>
          </div>
        </div>

        <button type="submit" className="btn btn-primary">{t('profile.save')}</button>
      </form>
    </div>
  )
}
