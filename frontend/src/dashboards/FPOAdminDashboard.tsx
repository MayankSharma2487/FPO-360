import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

interface FPOAdminData {
  total_farmers: number
  active_villages: number
  total_shareholders: number
  total_procurement_quantity: number  // Stored in KG
  total_procurement_value: number
  sales_this_month: number
  license_alerts: number
  total_crops: number
  total_farmer_crops: number
  total_acreage: number
}

type DashboardCard = {
  key: keyof FPOAdminData
  label: string
  description?: string
  accent: string
  icon?: React.ReactNode
}

const CARDS: DashboardCard[] = [
  {
    key: 'total_farmers',
    label: 'Farmers',
    description: 'Registered farmers',
    accent: '#4ade80',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    key: 'active_villages',
    label: 'Villages',
    description: 'Active villages',
    accent: '#60a5fa',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    ),
  },
  {
    key: 'total_shareholders',
    label: 'Shareholders',
    description: 'Active shareholders',
    accent: '#f59e0b',
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
    key: 'total_procurement_quantity',
    label: 'Procurement',
    description: 'Total Quantity',
    accent: '#8b5cf6',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="9" cy="21" r="1" />
        <circle cx="20" cy="21" r="1" />
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
      </svg>
    ),
  },
  {
    key: 'total_procurement_value',
    label: 'Procurement Value',
    description: 'Total Value',
    accent: '#14b8a6',
  },
  {
    key: 'sales_this_month',
    label: 'Sales',
    description: 'This month',
    accent: '#ec4899',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
        <path d="M6 3h13v2h-5.41c.64.48 1.15 1.15 1.45 1.95H19v2h-3.79c-.21.84-.71 1.57-1.39 2.05H19v2h-5.26c-1.04.91-2.45 1.45-4.04 1.48L17 21h-2.75l-7.75-8.5v-2h2.51c1.54 0 2.87-.88 3.51-2.16H6V6.36h7.02c-.52-.83-1.46-1.36-2.52-1.36H6V3z" />
      </svg>
    ),
  },
  {
    key: 'license_alerts',
    label: 'License Alerts',
    description: 'Pending attention',
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
    key: 'total_crops',
    label: 'Total Crops',
    description: 'Available crops',
    accent: '#22d3ee',
    icon: '⚜️',
  },
  {
    key: 'total_farmer_crops',
    label: 'Farmer Crops',
    description: 'Crop records',
    accent: '#eab308',
    icon: '☘️',
  },
  {
    key: 'total_acreage',
    label: 'Total Acreage',
    description: 'Cultivated land',
    accent: '#c026d3',
  },
]

export default function FPOAdminDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState<FPOAdminData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [quantityUnit, setQuantityUnit] = useState<'KG' | 'QT' | 'MT'>('KG')

  useEffect(() => {
    api
      .get<FPOAdminData>('/dashboard/fpo-admin')
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load FPO Admin dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

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

  const formatValue = (key: keyof FPOAdminData, value: any) => {
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
            <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Admin'}</h2>
            <p className="page-subtitle">Your FPO operations dashboard.</p>
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
          <h2 className="page-title">{greeting}, {user?.full_name?.split(' ')[0] ?? 'Admin'}</h2>
          <p className="page-subtitle">Your FPO operations dashboard.</p>
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
          <div className="page-badge">{user?.role?.name ?? '—'}</div>
        </div>
      </div>

      <section>
        <h3 className="section-title">Operations Overview</h3>
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
                {formatValue(card.key, data?.[card.key])}
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
            { label: 'Farmers', sub: 'Manage farmer records', path: '/farmers' },
            { label: 'Procurement', sub: 'Track procurement', path: '/procurements' },
            { label: 'Inventory', sub: 'Manage stock', path: '/inventory' },
            { label: 'Finance', sub: 'View financial reports', path: '/finance' },
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