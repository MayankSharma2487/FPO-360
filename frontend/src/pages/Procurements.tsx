import { useEffect, useState } from 'react';
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

export default function Procurements() {
  const [procurements, setProcurements] = useState<Procurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Partial<Procurement> | null>(null);

  const getInitials = (name: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getReverseConvertedQuantity = (storedQuantityInKg: number, unit: string): string => {
    let displayQuantity: number;

    if (unit === 'QUINTAL') {
      displayQuantity = storedQuantityInKg / 100;
    } else if (unit === 'TON') {
      displayQuantity = storedQuantityInKg / 1000;
    } else {
      displayQuantity = storedQuantityInKg;
    }

    const formatted = displayQuantity % 1 === 0
      ? displayQuantity.toString()
      : displayQuantity.toFixed(2);

    const unitLabel = unit === 'QUINTAL' ? 'QT' : unit === 'TON' ? 'MT' : 'KG';
    return `${formatted} ${unitLabel}`;
  };

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

  const filtered = procurements.filter(p =>
  (p.farmer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
  (p.crop_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
  (p.procurement_no ?? '').toLowerCase().includes(search.toLowerCase())
  );

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
    } catch (err) {
      setError('Failed to update status');
    }
  };

  const activeCount = procurements.filter(p => p.is_active).length;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Procurement</h2>
            <p className="page-subtitle">Manage farmer produce purchase records</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">
              {activeCount} of {procurements.length} active
            </div>
            <button 
              onClick={() => { setEditingRecord(null); setShowForm(true); }} 
              className="btn btn-primary"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              New Record
            </button>
          </div>
        </div>

        <div className="table-toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="Search procurements..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {error && <div className="error-banner">{error}</div>}
        {success && <div className="success-banner">{success}</div>}

        {loading ? (
          <div className="table-skeleton">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : (
          <div className="table-wrapper">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="w-12">#</th>
                    <th>PR No</th>
                    <th>Farmer</th>
                    <th>Crop</th>
                    <th>Quantity</th>
                    <th>Grade</th>
                    <th>Status</th>
                    <th className="w-20 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="empty-row">
                        {search ? 'No matching procurements found.' : 'No procurements found.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((p, idx) => (
                      <tr key={p.id} className="hover:bg-[#1a2233]">
                        <td className="row-num">{idx + 1}</td>
                        <td><span className="mono-tag">{p.procurement_no}</span></td>
                        <td>
                          <div className="user-cell">
                            <div 
                              className="mini-avatar"
                              style={{
                                background: `rgba(74, 222, 128, 0.133)`,
                                color: `rgb(74, 222, 128)`
                              }}
                            >
                              {getInitials(p.farmer_name)}
                            </div>
                            <span className="primary-cell font-medium">{p.farmer_name}</span>
                          </div>
                        </td>
                        <td><span className="mono-tag">{p.crop_name}</span></td>
                        <td className="text-sm font-medium">{getReverseConvertedQuantity(p.quantity, p.unit)}</td>
                        <td className="text-sm text-gray-400">{p.quality_grade || '—'}</td>
                        <td>
                          <span className={`status-pill ${p.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                            {p.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="text-right">
                          <div style={{ display: 'inline-flex' }}>
                            <ActionsMenu
                              actions={[
                                {
                                  label: 'Edit',
                                  icon: (
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
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
                                          <circle cx="12" cy="12" r="10"/>
                                          <line x1="8" y1="12" x2="16" y2="12"/>
                                        </>
                                      ) : (
                                        <>
                                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                          <polyline points="22 4 12 14.01 9 11.01"/>
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
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div className="modal-card modal-card--lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="modal-title">{editingRecord?.id ? 'Edit Procurement' : 'New Procurement'}</div>
                  <p className="modal-subtitle">
                    {editingRecord?.id ? 'Update procurement details' : 'Record new procurement'}
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