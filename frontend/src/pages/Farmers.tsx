import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { FarmerForm } from '../components/FarmerForm';
import { farmerService } from '../services/farmerService';
import { useAuth } from '../context/AuthContext';
import { ActionsMenu } from '../components/ActionsMenu';

interface Farmer {
  id: number;
  farmer_code: string;
  farmer_name: string;
  mobile_number: string;
  village_name?: string;
  farmer_category?: string;
  land_holding_acres?: number;
  is_shareholder: boolean;
  is_active: boolean;
}

export default function Farmers() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role?.name === 'Super Admin';
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingFarmer, setEditingFarmer] = useState<Partial<Farmer> | null>(null);

  const getInitials = (name: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const loadFarmers = async () => {
    setLoading(true);
    try {
      const res = await farmerService.getFarmers();
      setFarmers(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load farmers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFarmers();
  }, []);

  const filtered = farmers.filter(f =>
    (f.farmer_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (f.farmer_code ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (f.mobile_number ?? '').includes(search)
  );

  const handleCreate = () => {
    setEditingFarmer(null);
    setShowForm(true);
  };

  const handleEdit = (farmer: Farmer) => {
    setEditingFarmer(farmer);
    setShowForm(true);
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this farmer?`)) return;
    try {
      await farmerService.toggleStatus(id, !currentActive);
      setSuccess(`Farmer ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadFarmers();
    } catch (err) {
      setError('Failed to update status');
    }
  };

  const activeCount = farmers.filter(f => f.is_active).length;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Farmers</h2>
            <p className="page-subtitle">Manage farmer records and details</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">
              {activeCount} of {farmers.length} active
            </div>
            <button onClick={handleCreate} className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              New Farmer
            </button>
          </div>
        </div>

        <div className="table-toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="Search farmers by name, code or mobile..."
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
                    <th>Name</th>
                    <th>Code</th>
                    <th>Mobile</th>
                    <th>Village</th>
                    <th>Acres</th>
                    <th>Status</th>
                    <th className="w-20 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="empty-row">
                        {search ? 'No matching farmers found.' : 'No farmers found.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((f, idx) => (
                      <tr key={f.id} className="hover:bg-[#1a2233]">
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
                              {getInitials(f.farmer_name)}
                            </div>
                            <span className="primary-cell font-medium">{f.farmer_name}</span>
                          </div>
                        </td>
                        <td><span className="mono-tag">{f.farmer_code}</span></td>
                        <td className="text-sm text-gray-400">{f.mobile_number}</td>
                        <td className="text-sm text-gray-400">{f.village_name || '—'}</td>
                        <td className="text-sm text-gray-400">{f.land_holding_acres ? `${f.land_holding_acres} ac` : '—'}</td>
                        <td>
                          <span className={`status-pill ${f.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                            {f.is_active ? 'Active' : 'Inactive'}
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
                                  onClick: () => handleEdit(f),
                                },
                                {
                                  label: f.is_active ? 'Disable' : 'Enable',
                                  variant: f.is_active ? 'danger' : 'success',
                                  icon: (
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      {f.is_active ? (
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
                                  onClick: () => handleToggle(f.id, f.is_active),
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
                  <div className="modal-title">{editingFarmer?.id ? 'Edit Farmer' : 'New Farmer'}</div>
                  <p className="modal-subtitle">
                    {editingFarmer?.id ? 'Update farmer details' : 'Add a new farmer to the system'}
                  </p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <FarmerForm
                  initialData={editingFarmer}
                  onSubmit={async (data) => {
                    try {
                      if (editingFarmer?.id) {
                        await farmerService.updateFarmer(editingFarmer.id, data);
                        setSuccess('Farmer updated successfully');
                      } else {
                        await farmerService.createFarmer(data);
                        setSuccess('Farmer created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadFarmers();
                    } catch (err: any) {
                      setError(err?.response?.data?.detail || 'Failed to save farmer');
                    }
                  }}
                  onCancel={() => setShowForm(false)}
                  isSuperAdmin={isSuperAdmin}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}