import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { procurementService } from '../services/procurementService';

export default function ProcurementDetail() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();

  // Use router state if available, otherwise default to null for fallback loading
  const [record, setRecord] = useState<any>((location.state as any)?.record || null);
  const [loading, setLoading] = useState(!record);
  const [error, setError] = useState<string | null>(null);

  // Fallback: If accessed directly or refreshed, load the data from the service
  useEffect(() => {
    if (!record && id) {
      setLoading(true);
      procurementService.getProcurementById(Number(id))
        .then(res => setRecord(res.data))
        .catch(() => setError("Record not found or failed to load."))
        .finally(() => setLoading(false));
    }
  }, [id, record]);

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="table-skeleton"><div className="skeleton-row" /></div>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="page-wrapper empty-state">
        <div className="empty-state-title">{error || "Record not found"}</div>
        <button className="btn btn-primary empty-state-cta" onClick={() => navigate('/procurement')}>
          Back to Procurement
        </button>
      </div>
    );
  }

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">
               {record.procurement_no} 
               <span className={`status-pill ${record.is_active ? 'status-pill--active' : 'status-pill--inactive'}`} style={{ marginLeft: '12px' }}>
                 {record.is_active ? 'Active' : 'Inactive'}
               </span>
            </h2>
            <p className="page-subtitle">
              Procured on {new Date(record.procurement_date).toLocaleDateString()}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-ghost" onClick={() => navigate('/procurement')}>
              Back
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={() => navigate(`/procurement/${record.id}/receipt`, { state: { record } })}
            >
              View Receipt
            </button>
          </div>
        </div>

        {/* Dashboard/KPI Cards */}
        <div className="cards-grid">
          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">Total Value</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--accent)' }}>
              {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(record.total_amount)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">Quantity</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--amber)' }}>
              {record.quantity} {record.unit}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-label">Rate / Unit</span>
            </div>
            <div className="stat-value" style={{ color: 'var(--blue)' }}>
              {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(record.rate_per_unit)}
            </div>
          </div>
        </div>

        {/* Detail Sections */}
        <div className="form-grid">
          {/* General & Farmer */}
          <div className="stat-card">
            <h3 className="section-title">Farmer & Crop Details</h3>
            <table className="data-table" style={{ background: 'transparent', border: 'none' }}>
              <tbody>
                <tr>
                  <td className="text-muted">Farmer ID</td>
                  <td className="primary-cell">{record.farmer_id}</td>
                </tr>
                <tr>
                  <td className="text-muted">Farmer Name</td>
                  <td className="primary-cell">
                    <div className="user-cell">
                      <div className="mini-avatar">{record.farmer_name?.substring(0, 2).toUpperCase()}</div>
                      {record.farmer_name}
                    </div>
                  </td>
                </tr>
                <tr>
                  <td className="text-muted">Crop</td>
                  <td className="primary-cell">{record.crop_name}</td>
                </tr>
                <tr>
                  <td className="text-muted">Quality Grade</td>
                  <td className="primary-cell">
                    <span className="mono-tag">{record.quality_grade || 'Not specified'}</span>
                  </td>
                </tr>
                <tr>
                  <td className="text-muted">Remarks</td>
                  <td className="primary-cell">{record.remarks || '—'}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Audit & Timeline */}
          <div className="stat-card">
            <h3 className="section-title">Audit Timeline</h3>
            <table className="data-table" style={{ background: 'transparent', border: 'none' }}>
              <tbody>
                <tr>
                  <td className="text-muted">Created At</td>
                  <td className="primary-cell">
                    {record.created_at ? new Date(record.created_at).toLocaleString('en-IN') : 'Not recorded'}
                  </td>
                </tr>
                <tr>
                  <td className="text-muted">Last Updated</td>
                  <td className="primary-cell">
                    {record.updated_at ? new Date(record.updated_at).toLocaleString('en-IN') : 'Not recorded'}
                  </td>
                </tr>
                <tr>
                  <td className="text-muted">Organization ID</td>
                  <td className="primary-cell">{record.organization_id || '—'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Spin keyframe and Print Styles */}
        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
          
          @media print {
            @page { margin: 15mm; size: A4 portrait; }
            
            /* Hide UI Chrome and Interactive Elements */
            .sidebar, .navbar, .btn, .actions-menu-trigger, .actions-menu-dropdown { 
              display: none !important; 
            }
            
            /* Reset Layout to allow natural A4 document flow */
            body, .app-shell, .main-area, .page-content, .page-wrapper { 
              display: block !important; 
              height: auto !important; 
              width: 100% !important;
              overflow: visible !important; 
              background: white !important; 
              padding: 0 !important; 
              margin: 0 !important;
            }

            /* Optimize Text and Borders for Printing (Dark mode to Light mode mapping) */
            body, .page-title, .page-subtitle, .section-title, .primary-cell, .stat-value, .stat-label { 
              color: black !important; 
            }
            .text-muted, .text-secondary { 
              color: #444 !important; 
            }

            /* Ensure cards print with borders and don't break across pages */
            .stat-card { 
              background: white !important; 
              border: 1px solid #ddd !important; 
              box-shadow: none !important; 
              page-break-inside: avoid; 
              break-inside: avoid;
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
            }
            
            .data-table th { 
              background: #f1f5f9 !important; 
              border-bottom: 2px solid #ccc !important; 
              color: #333 !important; 
            }
            .data-table td { 
              border-bottom: 1px solid #ddd !important; 
            }
            .data-table tbody tr:nth-child(even) { 
              background: #f8fafc !important; 
            }
          }
        `}</style>

      </div>
    </RoleGuard>
  );
}