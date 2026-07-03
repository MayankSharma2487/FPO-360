import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

interface AccountantData {
  revenue: number
  expenses: number
  outstanding_payments: number
  loans: number
}

const CARDS = [
  {
    key: 'revenue' as keyof AccountantData,
    label: 'Revenue',
    description: 'Total income',
    accent: '#4ade80',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
    ),
  },
  {
    key: 'expenses' as keyof AccountantData,
    label: 'Expenses',
    description: 'Total outflow',
    accent: '#f59e0b',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2m0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8m3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5m-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11m3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
      </svg>
    ),
  },
  {
    key: 'outstanding_payments' as keyof AccountantData,
    label: 'Outstanding',
    description: 'Pending payments',
    accent: '#ef4444',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3.05h16.94a2 2 0 0 0 1.71-3.05L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
  {
    key: 'loans' as keyof AccountantData,
    label: 'Loans',
    description: 'Outstanding loans',
    accent: '#8b5cf6',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
      </svg>
    ),
  },
]

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

export default function AccountantDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<AccountantData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<AccountantData>('/dashboard/accountant')
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load Accountant dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Accountant'}</h2>
            <p className="page-subtitle">Financial overview and analysis.</p>
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
          <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Accountant'}</h2>
          <p className="page-subtitle">Financial overview and analysis.</p>
        </div>
        <div className="page-badge">{user?.role?.name ?? '—'}</div>
      </div>

      <section>
        <h3 className="section-title">Financial Summary</h3>
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
                {data ? formatCurrency(data[card.key]) : '₹0'}
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
            { label: 'Finance', sub: 'Detailed ledger', path: '/finance' },
            { label: 'Sales', sub: 'Sales analytics', path: '/sales' },
            { label: 'Reports', sub: 'Generate reports', path: '/reports' },
            { label: 'Settings', sub: 'Account settings', path: '/settings' },
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