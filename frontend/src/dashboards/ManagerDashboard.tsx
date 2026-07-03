import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

interface ManagerData {
  farmer_registrations: number
  village_coverage: number
  procurement_activities: number
  pending_tasks: number
}

const CARDS = [
  {
    key: 'farmer_registrations' as keyof ManagerData,
    label: 'New Farmers',
    description: 'This month',
    accent: '#4ade80',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    key: 'village_coverage' as keyof ManagerData,
    label: 'Village Coverage',
    description: 'Active villages',
    accent: '#60a5fa',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    key: 'procurement_activities' as keyof ManagerData,
    label: 'Procurements',
    description: 'Active activities',
    accent: '#f59e0b',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="9" cy="21" r="1" />
        <circle cx="20" cy="21" r="1" />
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
      </svg>
    ),
  },
  {
    key: 'pending_tasks' as keyof ManagerData,
    label: 'Tasks',
    description: 'Awaiting action',
    accent: '#8b5cf6',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
      </svg>
    ),
  },
]

export default function ManagerDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<ManagerData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<ManagerData>('/dashboard/manager')
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load Manager dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Manager'}</h2>
            <p className="page-subtitle">Management operations overview.</p>
          </div>
          <div className="page-badge">{user?.role?.name ?? '—'}</div>
        </div>
        <section>
          <h3 className="section-title">Overview</h3>
          <div className="cards-grid">
            {CARDS.map((c) => (
              <div key={c.key} className="stat-card stat-card--skeleton" />
            ))}
          </div>
        </section>
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
          <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Manager'}</h2>
          <p className="page-subtitle">Management operations overview.</p>
        </div>
        <div className="page-badge">{user?.role?.name ?? '—'}</div>
      </div>

      <section>
        <h3 className="section-title">Management Metrics</h3>
        <div className="cards-grid">
          {CARDS.map((card) => (
            <div key={card.key} className="stat-card" style={{ '--accent': card.accent } as React.CSSProperties}>
              <div className="stat-card-header">
                <div className="stat-icon" style={{ color: card.accent }}>
                  {card.icon}
                </div>
                <span className="stat-label">{card.label}</span>
              </div>
              <div className="stat-value" style={{ color: card.accent }}>
                {data?.[card.key] ?? 0}
              </div>
              <div className="stat-description">{card.description}</div>
              <div className="stat-accent-bar" style={{ background: card.accent }} />
            </div>
          ))}
        </div>
      </section>

      <section className="quick-links">
        <h3 className="section-title">Quick access</h3>
        <div className="quick-grid">
          {[
            { label: 'Farmers', sub: 'View farmer data', path: '/farmers' },
            { label: 'Villages', sub: 'Manage villages', path: '/villages' },
            { label: 'Procurement', sub: 'Track activities', path: '/procurement' },
            { label: 'Reports', sub: 'Generate reports', path: '/reports' },
          ].map((item) => (
            <a key={item.path} href={item.path} className="quick-card">
              <span className="quick-label">{item.label}</span>
              <span className="quick-sub">{item.sub}</span>
              <span className="quick-arrow">→</span>
            </a>
          ))}
        </div>
      </section>
    </div>
  )
}