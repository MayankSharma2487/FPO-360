import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

interface SuperAdminData {
  total_organizations: number
  total_users: number
  active_users: number
  total_roles: number
  total_farmers: number
  total_villages: number
  total_shareholders: number
  total_procurement_quantity: number  // Stored in KG
  total_procurement_value: number
  total_crops: number
  total_farmer_crops: number
  total_acreage: number
  expected_production: number
  actual_production: number
}

const CARDS = [
  {
    key: 'total_organizations',
    label: 'Organizations',
    accent: '#4ade80',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="6" width="18" height="15" rx="2" />
        <path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
        <path d="M9 17v-4" />
        <path d="M15 17v-4" />
      </svg>
    )
  },
  {
    key: 'total_users',
    label: 'Total Users',
    accent: '#60a5fa',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    )
  },
  {
    key: 'active_users',
    label: 'Active Users',
    accent: '#f59e0b',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    )
  },
  {
    key: 'total_roles',
    label: 'Roles',
    accent: '#a78bfa',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3v18" />
        <path d="M3 12h18" />
        <circle cx="9" cy="7" r="2" />
        <circle cx="15" cy="17" r="2" />
      </svg>
    )
  },
  {
    key: 'total_farmers',
    label: 'Farmers',
    accent: '#22d3ee',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    )
  },
  {
    key: 'total_villages',
    label: 'Villages',
    accent: '#22d3ee',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    )
  },
  {
    key: 'total_shareholders',
    label: 'Shareholders',
    accent: '#c026d3',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    )
  },
  {
    key: 'total_procurement_quantity',
    label: 'Procurement',
    accent: '#8b5cf6',
    description: 'Total Quantity',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="21" r="1" />
        <circle cx="20" cy="21" r="1" />
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
      </svg>
    )
  },
  {
    key: 'total_procurement_value',
    label: 'Procurement Value',
    accent: '#14b8a6',
    description: 'Total Value'
  },
  {
    key: 'total_crops',
    label: 'Crops',
    accent: '#22d3ee'
  },
  {
    key: 'total_farmer_crops',
    label: 'Farmer Crops',
    accent: '#eab308'
  },
  {
    key: 'total_acreage',
    label: 'Acreage',
    accent: '#ec4899'
  },
]

export default function SuperAdminDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<SuperAdminData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [quantityUnit, setQuantityUnit] = useState<'KG' | 'QT' | 'MT'>('KG')

  useEffect(() => {
    api
      .get<SuperAdminData>('/dashboard/super-admin')
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load Super Admin dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  const hour = new Date().getHours()
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  /**
   * CONVERT: Convert KG value for display based on selected unit
   * 
   * Dashboard APIs return KG. Frontend converts for display only.
   * 
   * Conversions:
   * - KG: value / 1 = value
   * - QT: value / 100
   * - MT: value / 1000
   */
  const convertQuantityForDisplay = (valueInKg: number, unit: 'KG' | 'QT' | 'MT'): number => {
    if (unit === 'QT') {
      return valueInKg / 100  // 1 QUINTAL = 100 KG
    } else if (unit === 'MT') {
      return valueInKg / 1000  // 1 METRIC TON = 1000 KG
    } else {
      return valueInKg  // KG
    }
  }

  const formatValue = (key: keyof SuperAdminData, value: any) => {
    if (key === 'total_procurement_quantity') {
      const convertedValue = convertQuantityForDisplay(value ?? 0, quantityUnit)
      const unitLabel = quantityUnit === 'QT' ? 'QT' : quantityUnit === 'MT' ? 'MT' : 'KG'
      return `${convertedValue.toFixed(2)} ${unitLabel}`
    }
    if (key === 'total_procurement_value') {
      return `₹${Number(value ?? 0).toLocaleString('en-IN')}`
    }
    return value ?? 0
  }

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Super Admin'}</h2>
            <p className="page-subtitle">Platform overview • Real-time metrics</p>
          </div>
          <div className="page-badge">Super Admin</div>
        </div>
        <section>
          <h3 className="section-title">Platform Health</h3>
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
          <h2 className="page-title">
            {greeting}, {user?.full_name?.split(' ')[0] ?? 'Super Admin'}
          </h2>
          <p className="page-subtitle">Platform overview • Real-time metrics</p>
        </div>
        <div className="flex items-center gap-3">
          {/* UNIT SELECTOR: Global selector for procurement quantity display */}
          <div className="unit-selector-wrapper">
              <label className="unit-selector-label">Unit:</label>
              <select
                value={quantityUnit}
                onChange={(e) => setQuantityUnit(e.target.value as 'KG' | 'QT' | 'MT')}
                className="unit-selector"
              >
                <option value="KG">KG</option>
                <option value="QT">Quintal</option>
                <option value="MT">Metric Ton</option>
              </select>
            </div>
          <div className="page-badge">Super Admin</div>
        </div>
      </div>

      <section>
        <h3 className="section-title">Platform Health</h3>
        <div className="cards-grid">
          {CARDS.map((card) => (
            <div
              key={card.key}
              className="stat-card"
              style={{ '--accent': card.accent } as React.CSSProperties}
            >
              <div className="stat-card-header">
                <div className="stat-icon" style={{ color: card.accent }}>
                  {card.icon}
                </div>
                <span className="stat-label">{card.label}</span>
              </div>
              <div className="stat-value" style={{ color: card.accent }}>
                {loading ? '—' : formatValue(card.key as keyof SuperAdminData, (data as any)[card.key])}
              </div>
              {card.description && (
                <div className="stat-description">{card.description}</div>
              )}
              <div className="stat-accent-bar" style={{ background: card.accent }} />
            </div>
          ))}
        </div>
      </section>

      <section className="quick-links">
        <h3 className="section-title">Platform Quick Links</h3>
        <div className="quick-grid">
          {[
            { label: 'Organizations', sub: 'Manage FPOs', path: '/organizations' },
            { label: 'Users', sub: 'User management', path: '/users' },
            { label: 'Farmers', sub: 'View all farmers', path: '/farmers' },
            { label: 'Procurement', sub: 'Global procurement', path: '/procurements' },
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