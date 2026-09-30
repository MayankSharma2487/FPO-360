import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { PaymentForm } from '../components/PaymentForm';
import { paymentService } from '../services/paymentService';
import { ActionsMenu } from '../components/ActionsMenu';

export default function Payments() {
  const navigate = useNavigate();
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any | null>(null);

  const loadPayments = async () => {
    setLoading(true);
    try {
      const res = await paymentService.getPayments();
      setPayments(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, []);

  const totalPayments = payments.length;
  const totalPaid = payments.filter(p => p.status === 'Paid').reduce((sum, p) => sum + (Number(p.amount) || 0), 0);
  const totalPending = payments.filter(p => p.status === 'Pending').reduce((sum, p) => sum + (Number(p.amount) || 0), 0);

  const formatCurrency = (amount: any) => {
    return 'Rs. ' + (Number(amount) || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  };

  const filtered = payments.filter(p =>
    (p.farmer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (p.payment_no ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (p.procurement_no ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this record?`)) return;
    try {
      await paymentService.toggleStatus(id, !currentActive);
      setSuccess(`Record ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadPayments();
    } catch {
      setError('Failed to update record status');
    }
  };

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Payments</h2>
            <p className="page-subtitle">Manage farmer payments</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button onClick={() => { setEditingRecord(null); setShowForm(true); }} className="btn btn-primary">
              New Payment
            </button>
          </div>
        </div>

        <div className="cards-grid">
          <div className="stat-card" style={{ '--accent': '#60a5fa' } as React.CSSProperties}>
            <div className="stat-card-header"><span className="stat-label">Total Payments</span></div>
            <div className="stat-value" style={{ color: '#60a5fa' }}>{loading ? '—' : totalPayments}</div>
          </div>
          <div className="stat-card" style={{ '--accent': '#4ade80' } as React.CSSProperties}>
            <div className="stat-card-header"><span className="stat-label">Total Paid</span></div>
            <div className="stat-value" style={{ color: '#4ade80' }}>{loading ? '—' : formatCurrency(totalPaid)}</div>
          </div>
          <div className="stat-card" style={{ '--accent': '#f59e0b' } as React.CSSProperties}>
            <div className="stat-card-header"><span className="stat-label">Pending Dues</span></div>
            <div className="stat-value" style={{ color: '#f59e0b' }}>{loading ? '—' : formatCurrency(totalPending)}</div>
          </div>
        </div>

        {error && <div className="error-banner" style={{ marginBottom: '16px' }}>{error}</div>}
        {success && <div className="success-banner" style={{ marginBottom: '16px' }}>{success}</div>}

        <div className="table-toolbar">
          <div style={{ position: 'relative', flex: 1, maxWidth: '380px' }}>
            <input
              type="text"
              className="search-input"
              placeholder="Search by Payment No, Farmer, or PR No..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {loading ? (
          <div className="table-skeleton"><div className="skeleton-row" /></div>
        ) : (
          <div className="table-wrapper">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Payment No.</th>
                    <th>Farmer</th>
                    <th>PR No.</th>
                    <th>Amount</th>
                    <th>Date</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr><td colSpan={9} className="empty-row">No payment records found</td></tr>
                  ) : (
                    filtered.map((p, idx) => (
                      <tr key={p.id} style={{ cursor: 'pointer', opacity: p.is_active ? 1 : 0.6 }} onClick={() => navigate(`/payments/${p.id}`, { state: { record: p } })}>
                        <td className="row-num" onClick={(e) => e.stopPropagation()}>{idx + 1}</td>
                        <td onClick={(e) => e.stopPropagation()}><span className="mono-tag">{p.payment_no}</span></td>
                        <td className="primary-cell">{p.farmer_name}</td>
                        <td className="text-muted">{p.procurement_no}</td>
                        <td style={{ fontWeight: 600 }}>{formatCurrency(p.amount)}</td>
                        <td>{new Date(p.payment_date).toLocaleDateString('en-IN')}</td>
                        <td>{p.payment_method}</td>
                        <td>
                          <span className={`status-pill ${p.status === 'Paid' ? 'status-pill--active' : 'status-pill--pending'}`}>
                            {p.status}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                          <ActionsMenu
                            actions={[
                              { label: 'View Details', onClick: () => navigate(`/payments/${p.id}`, { state: { record: p } }) },
                              { label: 'Edit', onClick: () => { setEditingRecord(p); setShowForm(true); } },
                              {
                                label: p.is_active ? 'Disable Record' : 'Enable Record',
                                variant: p.is_active ? 'danger' : 'success',
                                onClick: () => handleToggle(p.id, p.is_active),
                              },
                            ]}
                          />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div className="modal-card" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="modal-title">{editingRecord ? 'Edit Payment' : 'New Payment'}</div>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <PaymentForm
                  initialData={editingRecord}
                  onSubmit={async (data) => {
                    try {
                      if (editingRecord) {
                        await paymentService.updatePayment(editingRecord.id, data);
                        setSuccess('Payment updated successfully');
                      } else {
                        await paymentService.createPayment(data);
                        setSuccess('Payment created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadPayments();
                    } catch (err: any) {
                      setError(err?.response?.data?.detail || 'Failed to save payment');
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