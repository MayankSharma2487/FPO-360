import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { VillageForm } from '../components/VillageForm';
import { villageService } from '../services/villageService';
import { useAuth } from '../context/AuthContext';
import { VillageActionsMenu } from '../components/VillageActionsMenu';

interface Village {
  id: number;
  village_code: string;
  village_name: string;
  block?: string;
  district: string;
  state: string;
  organization_id: number;
  is_active: boolean;
}

export default function Villages() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role?.name === 'Super Admin';
  const [villages, setVillages] = useState<Village[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingVillage, setEditingVillage] = useState<Partial<Village> | null>(null);

  const loadVillages = async () => {
    setLoading(true);
    try {
      const res = await villageService.getVillages();
      setVillages(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load villages');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVillages();
  }, []);

  const filtered = villages.filter(v =>
    v.village_name.toLowerCase().includes(search.toLowerCase()) ||
    v.village_code.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = () => {
    setEditingVillage(null);
    setShowForm(true);
  };

  const handleEdit = (village: Village) => {
    setEditingVillage(village);
    setShowForm(true);
  };

  const handleSubmit = async (data: any) => {
    try {
      if (editingVillage?.id) {
        await villageService.updateVillage(editingVillage.id, data);
      } else {
        await villageService.createVillage(data);
      }
      setShowForm(false);
      loadVillages();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Operation failed');
    }
  };

  const handleToggle = async (id: number, currentActive: boolean) => {
    if (!confirm(`Are you sure you want to ${currentActive ? 'disable' : 'enable'} this village?`)) return;
    try {
      await villageService.toggleStatus(id, !currentActive);
      loadVillages();
    } catch (err) {
      alert('Failed to update status');
    }
  };

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Villages</h2>
            <p className="page-subtitle">Manage covered villages and clusters</p>
          </div>
          <button onClick={handleCreate} className="btn btn-primary">+ New Village</button>
        </div>

        <div className="table-toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="Search by name or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="table-skeleton">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton-row" />)}
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Village Code</th>
                  <th>Village Name</th>
                  <th>Block</th>
                  <th>District</th>
                  <th>State</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={8} className="empty-row">No villages found.</td></tr>
                ) : (
                  filtered.map((v, idx) => (
                    <tr key={v.id}>
                      <td className="row-num">{idx + 1}</td>
                      <td><span className="mono-tag">{v.village_code}</span></td>
                      <td className="primary-cell">{v.village_name}</td>
                      <td>{v.block || '—'}</td>
                      <td>{v.district}</td>
                      <td>{v.state}</td>
                      <td>
                        <span className={`status-pill ${v.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>
                          {v.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="text-right">
                        <VillageActionsMenu
                            villageId={v.id}
                            isActive={v.is_active}
                            onEdit={() => handleEdit(v)}
                            onToggleStatus={handleToggle}
                        />
                        </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {showForm && (
          <div className="modal-overlay">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <div className="modal-title">{editingVillage ? 'Edit Village' : 'New Village'}</div>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <VillageForm
                  initialData={editingVillage}
                  onSubmit={handleSubmit}
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