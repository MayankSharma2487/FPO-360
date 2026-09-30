import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { paymentService } from '../services/paymentService';

export default function PaymentDetail() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();

  const [record, setRecord] = useState<any>((location.state as any)?.record || null);
  const [loading, setLoading] = useState(!record);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!record && id) {
      setLoading(true);
      paymentService.getPaymentById(Number(id))
        .then(res => setRecord(res.data))
        .catch(() => setError("Record not found or failed to load."))
        .finally(() => setLoading(false));
    }
  }, [id, record]);

  if (loading) return <div className="page-wrapper"><div className="table-skeleton"><div className="skeleton-row" /></div></div>;
  if (error || !record) return <div className="page-wrapper empty-state">{error || "Not found"}</div>;

  const formatCurrency = (amount: number) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">
               {record.payment_no} 
               <span className={`status-pill ${record.status === 'Paid' ? 'status-pill--active' : 'status-pill--pending'}`} style={{ marginLeft: '12px' }}>
                 {record.status}
               </span>
               {!record.is_active && (
                 <span className="status-pill status-pill--inactive" style={{ marginLeft: '8px' }}>
                   Disabled Record
                 </span>
               )}
            </h2>
            <p className="page-subtitle">Farmer Payment Details</p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-ghost" onClick={() => navigate('/payments')}>Back</button>
            <button className="btn btn-secondary" onClick={() => navigate(`/payments/${record.id}/receipt`, { state: { record } })}>View Receipt</button>
          </div>
        </div>

        {/* Payment Summary */}
        <div className="cards-grid">
          <div className="stat-card">
            <div className="stat-card-header"><span className="stat-label">Payment Amount</span></div>
            <div className="stat-value" style={{ color: 'var(--accent)' }}>{formatCurrency(record.amount)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-header"><span className="stat-label">Payment Method</span></div>
            <div className="stat-value" style={{ color: 'var(--blue)' }}>{record.payment_method}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-header"><span className="stat-label">Reference / UTR</span></div>
            <div className="stat-value" style={{ color: 'var(--amber)' }}>{record.reference_no || 'N/A'}</div>
          </div>
        </div>

        <div className="form-grid">
          {/* Procurement Details */}
          <div className="stat-card">
            <h3 className="section-title">Procurement Details</h3>
            <table className="data-table" style={{ background: 'transparent', border: 'none' }}>
              <tbody>
                <tr><td className="text-muted">Procurement No.</td><td className="primary-cell"><span className="mono-tag">{record.procurement_no}</span></td></tr>
                <tr><td className="text-muted">Farmer</td><td className="primary-cell">{record.farmer_name} (ID: {record.farmer_id})</td></tr>
                <tr><td className="text-muted">Crop</td><td className="primary-cell">{record.crop_name}</td></tr>
                <tr><td className="text-muted">Quantity</td><td className="primary-cell">{record.procurement_qty}</td></tr>
                <tr><td className="text-muted">Procurement Total</td><td className="primary-cell" style={{ fontWeight: 600 }}>{formatCurrency(record.procurement_total)}</td></tr>
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Payment Details */}
            <div className="stat-card">
              <h3 className="section-title">Payment Details</h3>
              <table className="data-table" style={{ background: 'transparent', border: 'none' }}>
                <tbody>
                  <tr><td className="text-muted">Payment Date</td><td className="primary-cell">{new Date(record.payment_date).toLocaleString('en-IN')}</td></tr>
                  <tr><td className="text-muted">Remarks</td><td className="primary-cell">{record.remarks || '—'}</td></tr>
                </tbody>
              </table>
            </div>

            {/* System Audit */}
            <div className="stat-card">
              <h3 className="section-title">System Audit</h3>
              <table className="data-table" style={{ background: 'transparent', border: 'none' }}>
                <tbody>
                  <tr><td className="text-muted">Created At</td><td className="primary-cell">{new Date(record.created_at).toLocaleString('en-IN')}</td></tr>
                  <tr><td className="text-muted">Updated At</td><td className="primary-cell">{record.updated_at ? new Date(record.updated_at).toLocaleString('en-IN') : '—'}</td></tr>
                  <tr><td className="text-muted">Record Status</td><td className="primary-cell">{record.is_active ? 'Active' : 'Disabled'}</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </RoleGuard>
  );
}