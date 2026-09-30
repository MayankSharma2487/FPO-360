import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { ProcurementForm } from '../components/ProcurementForm';
import { procurementService } from '../services/procurementService';
import { ActionsMenu } from '../components/ActionsMenu';

interface Procurement {
  id: number;
  procurement_no: string;
  procurement_date: string;
  farmer_id: number;
  farmer_name: string;
  crop_id: number;
  crop_name: string;
  quantity: number;
  unit: string;
  rate_per_unit: number;
  total_amount: number;
  quality_grade?: string;
  is_active: boolean;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function getInitials(name: string): string {
  if (!name) return '?';
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function getReverseConvertedQuantity(storedQuantityInKg: any, unit: string): string {
  const qty = Number(storedQuantityInKg) || 0;
  let displayQuantity: number;
  
  if (unit === 'QUINTAL') {
    displayQuantity = qty / 100;
  } else if (unit === 'TON') {
    displayQuantity = qty / 1000;
  } else {
    displayQuantity = qty;
  }
  
  const formatted =
    displayQuantity % 1 === 0
      ? displayQuantity.toString()
      : displayQuantity.toFixed(2);
      
  const unitLabel = unit === 'QUINTAL' ? 'QT' : unit === 'TON' ? 'MT' : 'KG';
  return `${formatted} ${unitLabel}`;
}

function formatCurrency(amount: any): string {
  const num = Number(amount);
  if (isNaN(num) || amount == null) return '—';
  return 'Rs. ' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function isToday(dateStr: string): boolean {
  if (!dateStr) return false;
  try {
    const d = new Date(dateStr);
    const today = new Date();
    return (
      d.getDate() === today.getDate() &&
      d.getMonth() === today.getMonth() &&
      d.getFullYear() === today.getFullYear()
    );
  } catch {
    return false;
  }
}

function getGradeBadgeStyle(grade?: string): { background: string; color: string; border: string } {
  switch (grade) {
    case 'A':
      return {
        background: 'rgba(74, 222, 128, 0.12)',
        color: '#4ade80',
        border: '1px solid rgba(74, 222, 128, 0.3)',
      };
    case 'B':
      return {
        background: 'rgba(96, 165, 250, 0.12)',
        color: '#60a5fa',
        border: '1px solid rgba(96, 165, 250, 0.3)',
      };
    case 'C':
      return {
        background: 'rgba(245, 158, 11, 0.12)',
        color: '#f59e0b',
        border: '1px solid rgba(245, 158, 11, 0.3)',
      };
    case 'D':
      return {
        background: 'rgba(248, 113, 113, 0.12)',
        color: '#f87171',
        border: '1px solid rgba(248, 113, 113, 0.3)',
      };
    default:
      return {
        background: 'rgba(74, 97, 124, 0.2)',
        color: '#7f96b2',
        border: '1px solid rgba(74, 97, 124, 0.3)',
      };
  }
}

// ─── KPI Card ────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string;
  value: string | number;
  description: string;
  accent: string;
  icon: React.ReactNode;
}

function KpiCard({ label, value, description, accent, icon }: KpiCardProps) {
  return (
    <div
      className="stat-card"
      style={{ '--accent': accent } as React.CSSProperties}
    >
      <div className="stat-card-header">
        <div className="stat-icon" style={{ color: accent }}>
          {icon}
        </div>
        <span className="stat-label">{label}</span>
      </div>
      <div className="stat-value" style={{ color: accent }}>
        {value}
      </div>
      <div className="stat-description">{description}</div>
      <div className="stat-accent-bar" style={{ background: accent }} />
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function Procurements() {
  const navigate = useNavigate();

  const [procurements, setProcurements] = useState<Procurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Partial<Procurement> | null>(null);

  const loadProcurements = async () => {
    setLoading(true);
    try {
      const res = await procurementService.getProcurements();
      setProcurements(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load procurements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProcurements();
  }, []);

  // ── Computed KPIs (from loaded data, robust number parsing) ──────────────────

  const totalProcurements = procurements.length;

  const todaysProcurements = procurements.filter(p =>
    isToday(p.procurement_date)
  ).length;

  // Safely parse quantity to avoid string concatenation issues
  const totalQuantityKg = procurements.reduce((sum, p) => sum + (Number(p.quantity) || 0), 0);
  const totalQuantityDisplay: string = (() => {
    if (totalQuantityKg >= 1000) {
      const mt = totalQuantityKg / 1000;
      return (mt % 1 === 0 ? mt.toString() : mt.toFixed(2)) + ' MT';
    }
    return totalQuantityKg.toLocaleString('en-IN') + ' KG';
  })();

  // Safely parse total_amount to avoid NaN/String concatenation errors
  const totalValue = procurements.reduce((sum, p) => sum + (Number(p.total_amount) || 0), 0);
  const totalValueDisplay = formatCurrency(totalValue);

  // ── Filtered rows ─────────────────────────────────────────────────────────

  const filtered = procurements.filter(p =>
    (p.farmer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (p.crop_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (p.procurement_no ?? '').toLowerCase().includes(search.toLowerCase())
  );

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleViewDetail = (record: Procurement) => {
    navigate(`/procurement/${record.id}`, { state: { record } });
  };

  const handleEdit = (record: Procurement) => {
    setEditingRecord(record);
    setShowForm(true);
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this record?`)) return;
    try {
      await procurementService.toggleStatus(id, !currentActive);
      setSuccess(`Procurement ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadProcurements();
    } catch {
      setError('Failed to update status');
    }
  };

  const activeCount = procurements.filter(p => p.is_active).length;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">

        {/* ── Page Header ── */}
        <div className="page-header">
          <div>
            <h2 className="page-title">Procurement</h2>
            <p className="page-subtitle">Manage farmer produce purchase records</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div className="page-count-badge">
              {activeCount} of {totalProcurements} active
            </div>
            <button
              onClick={() => { setEditingRecord(null); setShowForm(true); }}
              className="btn btn-primary"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Record
            </button>
          </div>
        </div>

        {/* ── Procurement Dashboard KPIs ── */}
        <div className="cards-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <KpiCard
            label="Total Procurements"
            value={loading ? '—' : totalProcurements}
            description="All purchase records"
            accent="#4ade80"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <path d="M16 10a4 4 0 0 1-8 0" />
              </svg>
            }
          />
          <KpiCard
            label="Today's Procurements"
            value={loading ? '—' : todaysProcurements}
            description="Records created today"
            accent="#60a5fa"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
            }
          />
          <KpiCard
            label="Total Quantity"
            value={loading ? '—' : totalQuantityDisplay}
            description="Cumulative produce procured"
            accent="#f59e0b"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            }
          />
          <KpiCard
            label="Total Value"
            value={loading ? '—' : totalValueDisplay}
            description="Cumulative procurement value"
            accent="#a78bfa"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <line x1="12" y1="1" x2="12" y2="23" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            }
          />
        </div>

        {/* ── Alerts ── */}
        {error && <div className="error-banner" style={{ marginBottom: '16px' }}>{error}</div>}
        {success && <div className="success-banner" style={{ marginBottom: '16px' }}>{success}</div>}

        {/* ── Search Toolbar ── */}
        <div className="table-toolbar" style={{ marginBottom: '12px' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: '380px' }}>
            <span style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
            }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </span>
            <input
              type="text"
              className="search-input"
              placeholder="Search by PR No, farmer or crop..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '36px' }}
            />
          </div>
          {search && (
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
              {filtered.length} result{filtered.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* ── Table ── */}
        {loading ? (
          <div className="table-skeleton">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton-row" style={{ marginBottom: '2px', borderRadius: '4px' }} />
            ))}
          </div>
        ) : (
          <div className="table-wrapper">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: '44px' }}>#</th>
                    <th style={{ minWidth: '120px' }}>PR No.</th>
                    <th style={{ minWidth: '160px' }}>Farmer</th>
                    <th style={{ minWidth: '120px' }}>Crop</th>
                    <th style={{ minWidth: '110px' }}>Date</th>
                    <th style={{ minWidth: '100px' }}>Quantity</th>
                    <th style={{ minWidth: '120px' }}>Rate / Unit</th>
                    <th style={{ minWidth: '130px' }}>Total Value</th>
                    <th style={{ minWidth: '70px' }}>Grade</th>
                    <th style={{ minWidth: '90px' }}>Status</th>
                    <th style={{ width: '52px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="empty-row">
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '10px',
                          padding: '32px 16px',
                        }}>
                          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" style={{ color: 'var(--text-muted)', opacity: 0.4 }}>
                            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                            <line x1="3" y1="6" x2="21" y2="6" />
                            <path d="M16 10a4 4 0 0 1-8 0" />
                          </svg>
                          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                            {search ? 'No matching procurements' : 'No procurement records'}
                          </span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                            {search
                              ? `No results for "${search}"`
                              : 'Create a new record using the button above'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filtered.map((p, idx) => {
                      const gradeStyle = getGradeBadgeStyle(p.quality_grade);
                      return (
                        <tr
                          key={p.id}
                          style={{ cursor: 'pointer' }}
                          onClick={() => handleViewDetail(p)}
                        >
                          <td className="row-num">{idx + 1}</td>

                          {/* PR No. */}
                          <td>
                            <span className="mono-tag">{p.procurement_no ?? '—'}</span>
                          </td>

                          {/* Farmer */}
                          <td>
                            <div className="user-cell">
                              <div
                                className="mini-avatar"
                                style={{
                                  background: 'rgba(74, 222, 128, 0.13)',
                                  color: '#4ade80',
                                }}
                              >
                                {getInitials(p.farmer_name)}
                              </div>
                              <span className="primary-cell">{p.farmer_name ?? '—'}</span>
                            </div>
                          </td>

                          {/* Crop */}
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
                                <path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12" />
                                <path d="M12 6v6l4 2" />
                              </svg>
                              <span style={{ color: 'var(--text-primary)', fontSize: '0.8125rem' }}>
                                {p.crop_name ?? '—'}
                              </span>
                            </div>
                          </td>

                          {/* Date */}
                          <td>
                            <span style={{
                              fontSize: '0.8125rem',
                              color: isToday(p.procurement_date)
                                ? '#4ade80'
                                : 'var(--text-secondary)',
                              fontWeight: isToday(p.procurement_date) ? 600 : 400,
                            }}>
                              {formatDate(p.procurement_date)}
                            </span>
                          </td>

                          {/* Quantity */}
                          <td>
                            <span style={{
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              fontFamily: "'Space Grotesk', sans-serif",
                            }}>
                              {getReverseConvertedQuantity(p.quantity, p.unit)}
                            </span>
                          </td>

                          {/* Rate per Unit */}
                          <td>
                            <span style={{
                              fontSize: '0.8125rem',
                              color: 'var(--text-secondary)',
                              fontFamily: "'Space Grotesk', sans-serif",
                            }}>
                              {p.rate_per_unit != null
                                ? `Rs. ${Number(p.rate_per_unit).toLocaleString('en-IN')} / ${p.unit === 'QUINTAL' ? 'QT' : p.unit === 'TON' ? 'MT' : 'KG'}`
                                : '—'
                              }
                            </span>
                          </td>

                          {/* Total Value */}
                          <td>
                            <span style={{
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              color: '#4ade80',
                              fontFamily: "'Space Grotesk', sans-serif",
                            }}>
                              {formatCurrency(p.total_amount)}
                            </span>
                          </td>

                          {/* Grade */}
                          <td>
                            {p.quality_grade ? (
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                width: '28px',
                                height: '22px',
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                ...gradeStyle,
                              }}>
                                {p.quality_grade}
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>—</span>
                            )}
                          </td>

                          {/* Status */}
                          <td>
                            <span className={`status-pill ${p.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                              {p.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>

                          {/* Actions */}
                          <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                            <div style={{ display: 'inline-flex' }}>
                              <ActionsMenu
                                actions={[
                                  {
                                    label: 'View Details',
                                    icon: (
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                        <circle cx="12" cy="12" r="3" />
                                      </svg>
                                    ),
                                    onClick: () => handleViewDetail(p),
                                  },
                                  {
                                    label: 'Edit',
                                    icon: (
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                      </svg>
                                    ),
                                    onClick: () => handleEdit(p),
                                  },
                                  {
                                    label: p.is_active ? 'Disable' : 'Enable',
                                    variant: p.is_active ? 'danger' : 'success',
                                    icon: (
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        {p.is_active ? (
                                          <>
                                            <circle cx="12" cy="12" r="10" />
                                            <line x1="8" y1="12" x2="16" y2="12" />
                                          </>
                                        ) : (
                                          <>
                                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                            <polyline points="22 4 12 14.01 9 11.01" />
                                          </>
                                        )}
                                      </svg>
                                    ),
                                    onClick: () => handleToggle(p.id, p.is_active),
                                  },
                                ]}
                              />
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Table Footer */}
            {filtered.length > 0 && (
              <div style={{
                padding: '10px 14px',
                borderTop: '1px solid var(--border-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '8px',
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Showing {filtered.length} of {totalProcurements} record{totalProcurements !== 1 ? 's' : ''}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Filtered value:{' '}
                    <span style={{ color: '#4ade80', fontWeight: 600 }}>
                      {formatCurrency(filtered.reduce((sum, p) => sum + (Number(p.total_amount) || 0), 0))}
                    </span>
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Qty:{' '}
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                      {(() => {
                        const kg = filtered.reduce((sum, p) => sum + (Number(p.quantity) || 0), 0);
                        if (kg >= 1000) {
                          const mt = kg / 1000;
                          return (mt % 1 === 0 ? mt.toString() : mt.toFixed(2)) + ' MT';
                        }
                        return kg.toLocaleString('en-IN') + ' KG';
                      })()}
                    </span>
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Procurement Form Modal ── */}
        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div
              className="modal-card modal-card--lg"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <div>
                  <div className="modal-title">
                    {editingRecord?.id ? 'Edit Procurement' : 'New Procurement'}
                  </div>
                  <p className="modal-subtitle">
                    {editingRecord?.id
                      ? 'Update procurement details'
                      : 'Record new procurement'}
                  </p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <ProcurementForm
                  initialData={editingRecord}
                  onSubmit={async (data) => {
                    try {
                      if (editingRecord?.id) {
                        await procurementService.updateProcurement(editingRecord.id, data);
                        setSuccess('Procurement updated successfully');
                      } else {
                        await procurementService.createProcurement(data);
                        setSuccess('Procurement created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadProcurements();
                    } catch (err: any) {
                      setError(err?.response?.data?.detail || 'Failed to save procurement');
                    }
                  }}
                  onCancel={() => setShowForm(false)}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}