import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { CropMasterForm } from '../components/CropMasterForm';
import { cropMasterService } from '../services/cropMasterService';
import { ActionsMenu } from '../components/ActionsMenu';

interface CropMaster {
  id: number;
  crop_code: string;
  crop_name: string;
  category?: string;
  is_active: boolean;
}

export default function CropMasters() {
  const [crops, setCrops] = useState<CropMaster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingCrop, setEditingCrop] = useState<Partial<CropMaster> | null>(null);

  const getInitials = (name: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const loadCrops = async () => {
    setLoading(true);
    try {
      const res = await cropMasterService.getCropMasters();
      setCrops(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load crops');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCrops();
  }, []);

  const filtered = crops.filter(c =>
    (c.crop_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (c.crop_code ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const handleEdit = (crop: CropMaster) => {
    setEditingCrop(crop);
    setShowForm(true);
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this crop?`)) return;
    try {
      await cropMasterService.toggleStatus(id, !currentActive);
      setSuccess(`Crop ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadCrops();
    } catch (err) {
      setError('Failed to update status');
    }
  };

  const activeCount = crops.filter(c => c.is_active).length;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Crops</h2>
            <p className="page-subtitle">Manage crop master data</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">
              {activeCount} of {crops.length} active
            </div>
            <button 
              onClick={() => { setEditingCrop(null); setShowForm(true); }} 
              className="btn btn-primary"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              New Crop
            </button>
          </div>
        </div>

        <div className="table-toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="Search crops..."
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
                    <th>Crop Name</th>
                    <th>Code</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th className="w-20 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-row">
                        {search ? 'No matching crops found.' : 'No crops found.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((c, idx) => (
                      <tr key={c.id} className="hover:bg-[#1a2233]">
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
                              {getInitials(c.crop_name)}
                            </div>
                            <span className="primary-cell font-medium">{c.crop_name}</span>
                          </div>
                        </td>
                        <td><span className="mono-tag">{c.crop_code}</span></td>
                        <td className="text-sm text-gray-400">{c.category || '—'}</td>
                        <td>
                          <span className={`status-pill ${c.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                            {c.is_active ? 'Active' : 'Inactive'}
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
                                  onClick: () => handleEdit(c),
                                },
                                {
                                  label: c.is_active ? 'Disable' : 'Enable',
                                  variant: c.is_active ? 'danger' : 'success',
                                  icon: (
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      {c.is_active ? (
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
                                  onClick: () => handleToggle(c.id, c.is_active),
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
                  <div className="modal-title">{editingCrop?.id ? 'Edit Crop' : 'New Crop'}</div>
                  <p className="modal-subtitle">
                    {editingCrop?.id ? 'Update crop details' : 'Add a new crop to the system'}
                  </p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <CropMasterForm
                  initialData={editingCrop ?? undefined}
                  onSubmit={async (data) => {
                    try {
                      if (editingCrop?.id) {
                        await cropMasterService.updateCrop(editingCrop.id, data);
                        setSuccess('Crop updated successfully');
                      } else {
                        await cropMasterService.createCrop(data);
                        setSuccess('Crop created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadCrops();
                    } catch (err: any) {
                      setError(err?.response?.data?.detail || 'Failed to save crop');
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