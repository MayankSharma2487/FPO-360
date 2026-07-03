import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { ShareholderForm } from '../components/ShareholderForm';
import { shareholderService } from '../services/shareholderService';
import { ActionsMenu } from '../components/ActionsMenu';
import { useAuth } from '../context/AuthContext';

interface Shareholder {
  id: number;
  shareholder_name: string;
  email: string;
  mobile_number: string;
  organization_id: number;
  is_active: boolean;
}

export default function Shareholders() {
  const [shareholders, setShareholders] = useState<Shareholder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingShareholder, setEditingShareholder] = useState<Partial<Shareholder> | null>(null);

  const getInitials = (name: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const loadShareholders = async () => {
    setLoading(true);
    try {
      const res = await shareholderService.getShareholders();
      setShareholders(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load shareholders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShareholders();
  }, []);

  const filtered = shareholders.filter(s =>
  (s.shareholder_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
  (s.email ?? '').toLowerCase().includes(search.toLowerCase()) ||
  (s.mobile_number ?? '').includes(search)
  );

  const handleEdit = (shareholder: Shareholder) => {
    setEditingShareholder(shareholder);
    setShowForm(true);
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this shareholder?`)) return;
    try {
      await shareholderService.toggleStatus(id, !currentActive);
      setSuccess(`Shareholder ${currentActive ? 'disabled' : 'enabled'} successfully`);
      setTimeout(() => setSuccess(null), 3000);
      loadShareholders();
    } catch (err) {
      setError('Failed to update status');
    }
  };

  const activeCount = shareholders.filter(s => s.is_active).length;
  const { user } = useAuth();

  const isSuperAdmin =
    user?.role?.name === 'Super Admin';

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Shareholders</h2>
            <p className="page-subtitle">Manage shareholder records</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">
              {activeCount} of {shareholders.length} active
            </div>
            <button 
              onClick={() => { setEditingShareholder(null); setShowForm(true); }} 
              className="btn btn-primary"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              New Shareholder
            </button>
          </div>
        </div>

        <div className="table-toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="Search shareholders..."
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
                    <th>Email</th>
                    <th>Mobile</th>
                    <th>Organization</th>
                    <th>Status</th>
                    <th className="w-20 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="empty-row">
                        {search ? 'No matching shareholders found.' : 'No shareholders found.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((s, idx) => (
                      <tr key={s.id} className="hover:bg-[#1a2233]">
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
                              {getInitials(s.shareholder_name)}
                            </div>
                            <span className="primary-cell font-medium">{s.shareholder_name}</span>
                          </div>
                        </td>
                        <td><span className="mono-tag">{s.email}</span></td>
                        <td className="text-sm text-gray-400">{s.mobile_number}</td>
                        <td className="text-sm text-gray-400">Org {s.organization_id}</td>
                        <td>
                          <span className={`status-pill ${s.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                            {s.is_active ? 'Active' : 'Inactive'}
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
                                  onClick: () => handleEdit(s),
                                },
                                {
                                  label: s.is_active ? 'Disable' : 'Enable',
                                  variant: s.is_active ? 'danger' : 'success',
                                  icon: (
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      {s.is_active ? (
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
          </div>
        )}

        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div className="modal-card modal-card--lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="modal-title">{editingShareholder?.id ? 'Edit Shareholder' : 'New Shareholder'}</div>
                  <p className="modal-subtitle">
                    {editingShareholder?.id ? 'Update shareholder details' : 'Add a new shareholder'}
                  </p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <ShareholderForm
                  initialData={editingShareholder ?? undefined}
                  isSuperAdmin={isSuperAdmin}
                  onSubmit={async (data) => {
                    try {
                      if (editingShareholder?.id) {
                        await shareholderService.updateShareholder(editingShareholder.id, data);
                        setSuccess('Shareholder updated successfully');
                      } else {
                        await shareholderService.createShareholder(data);
                        setSuccess('Shareholder created successfully');
                      }
                      setShowForm(false);
                      setTimeout(() => setSuccess(null), 3000);
                      loadShareholders();
                    } catch (err: any) {
                      setError(err?.response?.data?.detail || 'Failed to save shareholder');
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