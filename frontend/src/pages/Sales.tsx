import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { SaleForm } from '../components/SaleForm';
import { salesService } from '../services/salesService';
import { ActionsMenu } from '../components/ActionsMenu';

interface Sale {
  id: number;
  sale_no: string;
  sale_date: string;
  customer_id: number;
  customer_name: string;
  crop_id: number;
  crop_name: string;
  quantity: number;
  unit: string;
  rate_per_unit: number;
  total_amount: number;
  payment_status: string;
  is_active: boolean;
  remarks?: string;
}

function getInitials(name: string): string {
  if (!name) return '?';
  return name
    .split(' ')
    .map((n) => n[0])
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
  return (
    'Rs. ' +
    num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  );
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

function unitLabel(unit: string): string {
  if (unit === 'QUINTAL') return 'QT';
  if (unit === 'TON') return 'MT';
  return 'KG';
}

interface KpiCardProps {
  label: string;
  value: string | number;
  description: string;
  accent: string;
  icon: React.ReactNode;
}

function KpiCard({ label, value, description, accent, icon }: KpiCardProps) {
  return (
    <div className="stat-card" style={{ '--accent': accent } as React.CSSProperties}>
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

export default function Sales() {
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Partial<Sale> | null>(null);

  const loadSales = async () => {
    setLoading(true);
    try {
      const res = await salesService.getSales();
      setSales(res.data || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load sales');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSales();
  }, []);

  const totalSales = sales.length;

  const todaysSales = sales.filter((s) => isToday(s.sale_date)).length;

  const totalQuantityKg = sales.reduce((sum, s) => sum + (Number(s.quantity) || 0), 0);
  const totalQuantityDisplay: string = (() => {
    if (totalQuantityKg >= 1000) {
      const mt = totalQuantityKg / 1000;
      return (mt % 1 === 0 ? mt.toString() : mt.toFixed(2)) + ' MT';
    }
    return totalQuantityKg.toLocaleString('en-IN') + ' KG';
  })();

  const totalValue = sales.reduce((sum, s) => sum + (Number(s.total_amount) || 0), 0);
  const totalValueDisplay = formatCurrency(totalValue);

  const filtered = sales.filter(
    (s) =>
      (s.customer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
      (s.crop_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
      (s.sale_no ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const handleEdit = (record: Sale) => {
    setEditingRecord(record);
    setShowForm(true);
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (
      !confirm(
        `Are you sure you want to ${currentActive ? 'disable' : 'enable'} this sale?`
      )
    )
      return;
    try {
      await salesService.toggleStatus(id, !currentActive);
      setSuccess(`Sale ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadSales();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update status');
    }
  };

  const activeCount = sales.filter((s) => s.is_active).length;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        {/* ── Page Header ── */}
        <div className="page-header">
          <div>
            <h2 className="page-title">Sales</h2>
            <p className="page-subtitle">Manage customer sales and inventory dispatches</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div className="page-count-badge">
              {activeCount} of {totalSales} active
            </div>
            <button
              onClick={() => {
                setEditingRecord(null);
                setShowForm(true);
              }}
              className="btn btn-primary"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Sale
            </button>
          </div>
        </div>

        {/* ── KPI Cards ── */}
        <div className="cards-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <KpiCard
            label="Total Sales"
            value={loading ? '—' : totalSales}
            description="All sales records"
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
            label="Today's Sales"
            value={loading ? '—' : todaysSales}
            description="Sales recorded today"
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
            label="Total Quantity Sold"
            value={loading ? '—' : totalQuantityDisplay}
            description="Cumulative quantity dispatched"
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
            label="Total Sales Value"
            value={loading ? '—' : totalValueDisplay}
            description="Cumulative sales value"
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
        {error && (
          <div className="error-banner" style={{ marginBottom: '16px' }}>
            {error}
          </div>
        )}
        {success && (
          <div className="success-banner" style={{ marginBottom: '16px' }}>
            {success}
          </div>
        )}

        {/* ── Search Toolbar ── */}
        <div className="table-toolbar" style={{ marginBottom: '12px' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: '380px' }}>
            <span
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
                pointerEvents: 'none',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </span>
            <input
              type="text"
              className="search-input"
              placeholder="Search by Sale No, customer or crop..."
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
                    <th style={{ minWidth: '120px' }}>Sale No.</th>
                    <th style={{ minWidth: '160px' }}>Customer</th>
                    <th style={{ minWidth: '120px' }}>Crop</th>
                    <th style={{ minWidth: '110px' }}>Date</th>
                    <th style={{ minWidth: '100px' }}>Quantity</th>
                    <th style={{ minWidth: '120px' }}>Rate / Unit</th>
                    <th style={{ minWidth: '130px' }}>Total Value</th>
                    <th style={{ minWidth: '90px' }}>Payment</th>
                    <th style={{ minWidth: '90px' }}>Status</th>
                    <th style={{ width: '52px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="empty-row">
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '10px',
                            padding: '32px 16px',
                          }}
                        >
                          <svg
                            width="40"
                            height="40"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1"
                            style={{ color: 'var(--text-muted)', opacity: 0.4 }}
                          >
                            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                            <line x1="3" y1="6" x2="21" y2="6" />
                            <path d="M16 10a4 4 0 0 1-8 0" />
                          </svg>
                          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                            {search ? 'No matching sales' : 'No sales records'}
                          </span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                            {search
                              ? `No results for "${search}"`
                              : 'Create a new sale using the button above'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filtered.map((s, idx) => (
                      <tr key={s.id}>
                        <td className="row-num">{idx + 1}</td>

                        <td>
                          <span className="mono-tag">{s.sale_no ?? '—'}</span>
                        </td>

                        <td>
                          <div className="user-cell">
                            <div
                              className="mini-avatar"
                              style={{
                                background: 'rgba(96, 165, 250, 0.13)',
                                color: '#60a5fa',
                              }}
                            >
                              {getInitials(s.customer_name)}
                            </div>
                            <span className="primary-cell">{s.customer_name ?? '—'}</span>
                          </div>
                        </td>

                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <svg
                              width="13"
                              height="13"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              style={{ color: 'var(--text-muted)', flexShrink: 0 }}
                            >
                              <path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12" />
                              <path d="M12 6v6l4 2" />
                            </svg>
                            <span style={{ color: 'var(--text-primary)', fontSize: '0.8125rem' }}>
                              {s.crop_name ?? '—'}
                            </span>
                          </div>
                        </td>

                        <td>
                          <span
                            style={{
                              fontSize: '0.8125rem',
                              color: isToday(s.sale_date) ? '#4ade80' : 'var(--text-secondary)',
                              fontWeight: isToday(s.sale_date) ? 600 : 400,
                            }}
                          >
                            {formatDate(s.sale_date)}
                          </span>
                        </td>

                        <td>
                          <span
                            style={{
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              fontFamily: "'Space Grotesk', sans-serif",
                            }}
                          >
                            {getReverseConvertedQuantity(s.quantity, s.unit)}
                          </span>
                        </td>

                        <td>
                          <span
                            style={{
                              fontSize: '0.8125rem',
                              color: 'var(--text-secondary)',
                              fontFamily: "'Space Grotesk', sans-serif",
                            }}
                          >
                            {s.rate_per_unit != null
                              ? `Rs. ${Number(s.rate_per_unit).toLocaleString('en-IN')} / ${unitLabel(s.unit)}`
                              : '—'}
                          </span>
                        </td>

                        <td>
                          <span
                            style={{
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              color: '#4ade80',
                              fontFamily: "'Space Grotesk', sans-serif",
                            }}
                          >
                            {formatCurrency(s.total_amount)}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`status-pill ${
                              s.payment_status === 'Paid'
                                ? 'status-pill--active'
                                : 'status-pill--inactive'
                            }`}
                          >
                            {s.payment_status === 'Paid' ? 'Paid' : 'Pending'}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`status-pill ${
                              s.is_active ? 'status-pill--active' : 'status-pill--inactive'
                            }`}
                          >
                            {s.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>

                        <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                          <div style={{ display: 'inline-flex' }}>
                            <ActionsMenu
                              actions={[
                                {
                                  label: 'Edit',
                                  icon: (
                                    <svg
                                      width="16"
                                      height="16"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth="2"
                                    >
                                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                    </svg>
                                  ),
                                  onClick: () => handleEdit(s),
                                },
                                {
                                  label: s.is_active ? 'Disable' : 'Enable',
                                  variant: s.is_active ? 'danger' : 'success',
                                  icon: (
                                    <svg
                                      width="16"
                                      height="16"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth="2"
                                    >
                                      {s.is_active ? (
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
                                  onClick: () => handleToggle(s.id, s.is_active),
                                },
                              ]}
                            />
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {filtered.length > 0 && (
              <div
                style={{
                  padding: '10px 14px',
                  borderTop: '1px solid var(--border-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '8px',
                }}
              >
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Showing {filtered.length} of {totalSales} record
                  {totalSales !== 1 ? 's' : ''}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Filtered value:{' '}
                    <span style={{ color: '#4ade80', fontWeight: 600 }}>
                      {formatCurrency(
                        filtered.reduce((sum, s) => sum + (Number(s.total_amount) || 0), 0)
                      )}
                    </span>
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Qty:{' '}
                    <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
                      {(() => {
                        const kg = filtered.reduce(
                          (sum, s) => sum + (Number(s.quantity) || 0),
                          0
                        );
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

        {/* ── Sale Form Modal ── */}
        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div className="modal-card modal-card--lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="modal-title">
                    {editingRecord?.id ? 'Edit Sale' : 'New Sale'}
                  </div>
                  <p className="modal-subtitle">
                    {editingRecord?.id ? 'Update sale details' : 'Record a new customer sale'}
                  </p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>
                  ✕
                </button>
              </div>
              <div className="modal-body">
                <SaleForm
                  initialData={editingRecord}
                  onSubmit={async (data) => {
                    try {
                      if (editingRecord?.id) {
                        await salesService.updateSale(editingRecord.id, data);
                        setSuccess('Sale updated successfully');
                      } else {
                        await salesService.createSale(data);
                        setSuccess('Sale created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadSales();
                    } catch (err: any) {
                      // Re-throw so SaleForm can show backend detail (e.g. insufficient stock)
                      throw err;
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
