import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { procurementService } from '../services/procurementService';

export default function ProcurementReceipt() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();

  const [record, setRecord] = useState<any>((location.state as any)?.record || null);
  const [loading, setLoading] = useState(!record);
  const [error, setError] = useState<string | null>(null);

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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount || 0);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-IN', { 
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        
        {/* Top Controls (Hidden during print) */}
        <div className="page-header no-print">
          <div>
            <h2 className="page-title">Receipt Preview</h2>
            <p className="page-subtitle">Printable procurement document</p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-ghost" onClick={() => navigate(-1)}>
              Back
            </button>
            <button className="btn btn-primary" onClick={() => window.print()}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '6px' }}>
                <polyline points="6 9 6 2 18 2 18 9" />
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                <rect x="6" y="14" width="12" height="8" />
              </svg>
              Print
            </button>
            <button className="btn btn-secondary" disabled title="Coming Soon">
              Download PDF
            </button>
          </div>
        </div>

        {/* Printable A4 Document */}
        <div className="receipt-document stat-card">
          
          {/* Header */}
          <div className="receipt-header">
            <div className="receipt-brand">
              <h1 style={{ margin: 0, fontSize: '24px', fontFamily: "'Space Grotesk', sans-serif" }}>FPO360 ERP</h1>
              <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>Farmer Producer Organization</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <h2 style={{ margin: 0, fontSize: '20px', color: '#333' }}>Procurement Receipt</h2>
              <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#555' }}>
                <strong>Date:</strong> {new Date(record.procurement_date).toLocaleDateString('en-IN')}
              </p>
            </div>
          </div>

          {/* Quick Identifiers */}
          <div className="receipt-identifiers">
            <div>
              <span className="label">Receipt Number:</span>
              <span className="value">REC-{record.procurement_no}</span>
            </div>
            <div>
              <span className="label">Procurement No:</span>
              <span className="value">{record.procurement_no}</span>
            </div>
          </div>

          {/* Body Sections */}
          <div className="receipt-grid">
            
            {/* Farmer Information */}
            <div className="receipt-section">
              <h3 className="section-heading">Farmer Information</h3>
              <table className="receipt-table">
                <tbody>
                  <tr>
                    <td className="lbl">Farmer Name</td>
                    <td className="val"><strong>{record.farmer_name}</strong></td>
                  </tr>
                  <tr>
                    <td className="lbl">Farmer ID</td>
                    <td className="val">{record.farmer_id}</td>
                  </tr>
                  <tr>
                    <td className="lbl">Village</td>
                    <td className="val">{record.village_name || '—'}</td>
                  </tr>
                  <tr>
                    <td className="lbl">Organization</td>
                    <td className="val">{record.organization_id || '—'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Crop Information */}
            <div className="receipt-section">
              <h3 className="section-heading">Crop Information</h3>
              <table className="receipt-table">
                <tbody>
                  <tr>
                    <td className="lbl">Crop</td>
                    <td className="val"><strong>{record.crop_name}</strong></td>
                  </tr>
                  <tr>
                    <td className="lbl">Quantity</td>
                    <td className="val">{record.quantity} {record.unit}</td>
                  </tr>
                  <tr>
                    <td className="lbl">Rate</td>
                    <td className="val">{formatCurrency(record.rate_per_unit)} / {record.unit}</td>
                  </tr>
                  <tr>
                    <td className="lbl">Quality Grade</td>
                    <td className="val">{record.quality_grade || '—'}</td>
                  </tr>
                  <tr>
                    <td className="lbl" style={{ paddingTop: '12px' }}><strong>Total Amount</strong></td>
                    <td className="val" style={{ paddingTop: '12px', fontSize: '1.1rem' }}>
                      <strong>{formatCurrency(record.total_amount)}</strong>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Remarks */}
          <div className="receipt-section" style={{ marginTop: '24px' }}>
            <h3 className="section-heading">Remarks</h3>
            <p style={{ margin: 0, padding: '12px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '4px', color: '#333' }}>
              {record.remarks || 'No remarks provided.'}
            </p>
          </div>

          {/* Audit Information */}
          <div className="receipt-section" style={{ marginTop: '24px' }}>
            <h3 className="section-heading">Audit Information</h3>
            <div style={{ display: 'flex', gap: '40px', fontSize: '13px', color: '#555' }}>
              <div><strong>Created At:</strong> {formatDate(record.created_at)}</div>
              <div><strong>Updated At:</strong> {formatDate(record.updated_at)}</div>
            </div>
          </div>

          {/* Signatures */}
          <div className="receipt-signatures">
            <div className="sig-box">
              <div className="sig-line"></div>
              <span>Prepared By</span>
            </div>
            <div className="sig-box">
              <div className="sig-line"></div>
              <span>Authorized Signature</span>
            </div>
            <div className="sig-box">
              <div className="sig-line"></div>
              <span>Farmer Signature</span>
            </div>
          </div>

        </div>

        <style>{`
          /* Display styles for the document wrapper */
          .receipt-document {
            background: #ffffff !important;
            color: #000000 !important;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
          }

          .receipt-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 2px solid #333;
            padding-bottom: 16px;
            margin-bottom: 20px;
          }

          .receipt-identifiers {
            display: flex;
            justify-content: space-between;
            background: #f1f5f9;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
          }

          .receipt-identifiers .label {
            color: #475569;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-right: 8px;
          }

          .receipt-identifiers .value {
            font-weight: 700;
            font-family: 'Courier New', monospace;
            font-size: 15px;
          }

          .receipt-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
          }

          .section-heading {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 8px;
            margin-bottom: 16px;
            margin-top: 0;
          }

          .receipt-table {
            width: 100%;
            border-collapse: collapse;
          }

          .receipt-table td {
            padding: 6px 0;
            vertical-align: top;
            font-size: 14px;
          }

          .receipt-table .lbl {
            color: #64748b;
            width: 40%;
          }

          .receipt-table .val {
            color: #0f172a;
            text-align: right;
          }

          .receipt-signatures {
            display: flex;
            justify-content: space-between;
            margin-top: 80px;
            padding-top: 20px;
          }

          .sig-box {
            text-align: center;
            width: 25%;
          }

          .sig-line {
            border-top: 1px solid #333;
            margin-bottom: 8px;
          }

          .sig-box span {
            font-size: 13px;
            color: #475569;
          }

          /* Print Overrides */
          @media print {
            @page { margin: 15mm; size: A4 portrait; }
            
            .no-print, .sidebar, .navbar { 
              display: none !important; 
            }
            
            body, .app-shell, .main-area, .page-content, .page-wrapper { 
              display: block !important; 
              height: auto !important; 
              width: 100% !important;
              overflow: visible !important; 
              background: white !important; 
              padding: 0 !important; 
              margin: 0 !important;
            }

            .receipt-document {
              padding: 0 !important;
              border: none !important;
              box-shadow: none !important;
              max-width: 100% !important;
            }

            .receipt-identifiers {
              background: transparent !important;
              border: 1px solid #ccc !important;
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
            }
          }
        `}</style>
      </div>
    </RoleGuard>
  );
}