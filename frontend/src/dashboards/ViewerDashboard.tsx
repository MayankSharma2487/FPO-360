import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

interface ViewerData {
  last_updated: string
}

export default function ViewerDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<ViewerData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<ViewerData>('/dashboard/viewer')
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Viewer'}</h2>
            <p className="page-subtitle">View reports and data.</p>
          </div>
          <div className="page-badge">{user?.role?.name ?? '—'}</div>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="error-banner">{error}</div>
  }

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Viewer'}</h2>
          <p className="page-subtitle">View reports and data.</p>
        </div>
        <div className="page-badge">{user?.role?.name ?? '—'}</div>
      </div>

      <section className="info-section">
        <div className="info-card">
          <div className="info-icon">📊</div>
          <div className="info-content">
            <h3>Read-Only Access</h3>
            <p>
              You have read-only access to reports and dashboards. For detailed information, navigate to the Reports section using the sidebar menu.
            </p>
          </div>
        </div>
      </section>

      <section className="quick-links">
        <h3 className="section-title">Available Options</h3>
        <div className="quick-grid">
          {[
            { label: 'Reports', sub: 'View all reports', path: '/reports' },
          ].map((item) => (
            <a key={item.path} href={item.path} className="quick-card">
              <span className="quick-label">{item.label}</span>
              <span className="quick-sub">{item.sub}</span>
              <span className="quick-arrow">→</span>
            </a>
          ))}
        </div>
      </section>

      {data && (
        <section className="meta-info">
          <div className="meta-item">
            <span className="meta-label">Last Updated</span>
            <span className="meta-value">{formatDate(data.last_updated)}</span>
          </div>
        </section>
      )}
    </div>
  )
}