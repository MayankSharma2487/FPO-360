import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { FarmerCropForm } from '../components/FarmerCropForm';
import { farmerCropService } from '../services/farmerCropService';
import { ActionsMenu } from '../components/ActionsMenu';

interface FarmerCrop {
  id: number;
  farmer_id: number;
  farmer_name: string;
  crop_id: number;
  crop_name: string;
  acreage: number;
  is_active: boolean;
}

export default function FarmerCrops() {
  const [farmerCrops, setFarmerCrops] = useState<FarmerCrop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Partial<FarmerCrop> | null>(null);

  const getInitials = (name: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const loadFarmerCrops = async () => {
    setLoading(true);
    try {
      const res = await farmerCropService.getFarmerCrops();
      setFarmerCrops(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load farmer crops');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFarmerCrops();
  }, []);

  const filtered = farmerCrops.filter(fc =>
    (fc.farmer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (fc.crop_name ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const handleEdit = (record: FarmerCrop) => {
    setEditingRecord(record);
    setShowForm(true);
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this record?`)) return;
    try {
      await farmerCropService.toggleStatus(id, !currentActive);
      setSuccess(`Record ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadFarmerCrops();
    } catch (err) {
      setError('Failed to update status');
    }
  };

  const activeCount = farmerCrops.filter(fc => fc.is_active).length;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Farmer Crops</h2>
            <p className="page-subtitle">Manage farmer crop allocations</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">
              {activeCount} of {farmerCrops.length} active
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
            placeholder="Search farmer crops..."
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
                    <th>Farmer</th>
                    <th>Crop</th>
                    <th>Acreage</th>
                    <th>Status</th>
                    <th className="w-20 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-row">
                        {search ? 'No matching records found.' : 'No farmer crops found.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((fc, idx) => (
                      <tr key={fc.id} className="hover:bg-[#1a2233]">
                        <td className="row-num">{idx + 1}</td>
                        <td>
                          <div className="user-cell">
                            <div 
                              className="mini-avatar"
                              style={{
                                background: `rgba(74, 222, 128, 0.133)`,
                                color: `rgb(74, 222, 128)`
                              }}
                            >
                              {getInitials(fc.farmer_name)}
                            </div>
                            <span className="primary-cell font-medium">{fc.farmer_name}</span>
                          </div>
                        </td>
                        <td><span className="mono-tag">{fc.crop_name}</span></td>
                        <td className="text-sm text-gray-400">{fc.acreage} ac</td>
                        <td>
                          <span className={`status-pill ${fc.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                            {fc.is_active ? 'Active' : 'Inactive'}
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
                                  onClick: () => handleEdit(fc),
                                },
                                {
                                  label: fc.is_active ? 'Disable' : 'Enable',
                                  variant: fc.is_active ? 'danger' : 'success',
                                  icon: (
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      {fc.is_active ? (
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
                                  onClick: () => handleToggle(fc.id, fc.is_active),
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
            <div className="modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="modal-title">{editingRecord?.id ? 'Edit Record' : 'New Farmer Crop'}</div>
                  <p className="modal-subtitle">
                    {editingRecord?.id ? 'Update farmer crop allocation' : 'Add new farmer crop allocation'}
                  </p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <FarmerCropForm
                  initialData={editingRecord ?? undefined}
                  onSubmit={async (data) => {
                    try {
                      if (editingRecord?.id) {
                        await farmerCropService.updateFarmerCrop(editingRecord.id, data);
                        setSuccess('Record updated successfully');
                      } else {
                        await farmerCropService.createFarmerCrop(data);
                        setSuccess('Record created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadFarmerCrops();
                    } catch (err: any) {
                      setError(err?.response?.data?.detail || 'Failed to save record');
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