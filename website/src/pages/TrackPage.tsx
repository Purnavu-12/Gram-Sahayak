import { useTranslation } from 'react-i18next'

// Demo application data
const DEMO_APPLICATIONS = [
  {
    id: 'APP-2024-001',
    scheme: 'PM-KISAN',
    date: '2024-11-15',
    status: 'approved' as const,
    updated: '2024-12-10',
  },
  {
    id: 'APP-2024-002',
    scheme: 'MGNREGA',
    date: '2024-12-01',
    status: 'pending' as const,
    updated: '2024-12-20',
  },
  {
    id: 'APP-2024-003',
    scheme: 'Ayushman Bharat',
    date: '2025-01-05',
    status: 'incomplete' as const,
    updated: '2025-01-05',
  },
]

export default function TrackPage() {
  const { t } = useTranslation()

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: 'badge-pending',
      approved: 'badge-approved',
      rejected: 'badge-rejected',
      incomplete: 'badge-incomplete',
    }
    const labelMap: Record<string, string> = {
      pending: t('track.status_pending'),
      approved: t('track.status_approved'),
      rejected: t('track.status_rejected'),
      incomplete: t('track.status_incomplete'),
    }
    return <span className={`badge ${map[status] || ''}`}>{labelMap[status]}</span>
  }

  return (
    <div className="page">
      <h1>{t('track.title')}</h1>
      <p className="subtitle">{t('track.subtitle')}</p>

      {DEMO_APPLICATIONS.length === 0 ? (
        <div className="empty-state">
          <div className="icon">📄</div>
          <p>{t('track.no_applications')}</p>
        </div>
      ) : (
        DEMO_APPLICATIONS.map(app => (
          <div key={app.id} className="track-card">
            <div>
              <h3>{app.scheme}</h3>
              <div className="info">
                {t('track.applied_on')}: {app.date} &nbsp;|&nbsp; {t('track.last_updated')}: {app.updated}
              </div>
              <div className="info" style={{ marginTop: '0.25rem' }}>ID: {app.id}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {statusBadge(app.status)}
              <button className="btn btn-outline" style={{ padding: '0.3rem 0.8rem', fontSize: '0.85rem', color: 'var(--primary)', borderColor: 'var(--primary)' }}>
                {t('track.view_details')}
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
