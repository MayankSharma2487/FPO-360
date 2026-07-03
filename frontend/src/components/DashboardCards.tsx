import { useEffect, useState } from 'react'
import api from '../services/api'

interface DashboardSummary {
  total_users: number
  total_organizations: number
  total_active_users: number
}

const CARDS = [
  {
    key: 'total_organizations' as keyof DashboardSummary,
    label: 'Organizations',
    description: 'Registered FPOs',
    accent: '#4ade80',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
      </svg>
    ),
  },
  {
    key: 'total_users' as keyof DashboardSummary,
    label: 'Total Users',
    description: 'Registered accounts',
    accent: '#60a5fa',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    key: 'total_active_users' as keyof DashboardSummary,
    label: 'Active Users',
    description: 'Currently active',
    accent: '#f59e0b',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
]

export default function DashboardCards() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<DashboardSummary>('/dashboard/summary')
      .then((res) => setSummary(res.data))
      .catch(() => setError('Could not load summary data.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="cards-grid">
        {CARDS.map((c) => (
          <div key={c.key} className="stat-card stat-card--skeleton" />
        ))}
      </div>
    )
  }

  if (error) {
    return <div className="error-banner">{error}</div>
  }

  return (
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
            {summary?.[card.key] ?? 0}
          </div>
          <div className="stat-description">{card.description}</div>
          <div className="stat-accent-bar" style={{ background: card.accent }} />
        </div>
      ))}
    </div>
  )
}
