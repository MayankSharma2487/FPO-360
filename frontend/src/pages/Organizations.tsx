import { useEffect, useState } from 'react';
import api from '../services/api';
import { OrganizationForm } from '../components/OrganizationForm';
import { OrganizationActionsMenu } from '../components/OrganizationActionsMenu';

interface Organization {
  id: number;
  organization_name: string;
  registration_number: string;
  pan_number: string | null;
  gst_number: string | null;
  fssai_number: string | null;
  state: string | null;
  district: string | null;
}

export default function Organizations() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Partial<Organization> | null>(null);

  const loadOrganizations = async () => {
    setLoading(true);
    try {
      const res = await api.get<Organization[]>('/organizations/');
      setOrgs(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrganizations();
  }, []);

  const filtered = orgs.filter((o) =>
    o.organization_name.toLowerCase().includes(search.toLowerCase()) ||
    o.registration_number.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = () => {
    setEditingOrg(null);
    setShowForm(true);
  };

  const handleEdit = (org: Organization) => {
    setEditingOrg(org);
    setShowForm(true);
  };

  const handleSubmit = async (data: any) => {
    try {
      if (editingOrg?.id) {
        await api.put(`/organizations/${editingOrg.id}`, data);
      } else {
        await api.post('/organizations/', data);
      }
      setShowForm(false);
      loadOrganizations();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Operation failed');
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h2 className="page-title">Organizations</h2>
          <p className="page-subtitle">Registered Farmer Producer Organizations</p>
        </div>
        <button
          onClick={handleCreate}
          className="btn btn-primary"
        >
          + New Organization
        </button>
      </div>

      <div className="table-toolbar">
        <input
          type="text"
          className="search-input"
          placeholder="Search organizations..."
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
        <div className="table-wrapper"><div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th className="w-12">#</th>
                <th>Organization Name</th>
                <th>Registration No.</th>
                <th>PAN</th>
                <th>GST</th>
                <th>State</th>
                <th>District</th>
                <th className="w-20 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="empty-row py-16">No organizations found.</td>
                </tr>
              ) : (
                filtered.map((org, idx) => (
                  <tr key={org.id} className="hover:bg-[#1a2233]">
                    <td className="row-num">{idx + 1}</td>
                    <td className="primary-cell font-medium">{org.organization_name}</td>
                    <td><span className="mono-tag">{org.registration_number}</span></td>
                    <td>{org.pan_number || '—'}</td>
                    <td>{org.gst_number || '—'}</td>
                    <td>{org.state || '—'}</td>
                    <td>{org.district || '—'}</td>
                    <td className="text-right">
                      <OrganizationActionsMenu
                        org={org}
                        onEdit={handleEdit}
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
        <div className="modal-overlay">
          <div className="modal-card modal-card--lg">
            <div className="modal-header">
              <div>
                <div className="modal-title">{editingOrg ? 'Edit Organization' : 'New Organization'}</div>
                <div className="modal-subtitle">{editingOrg ? 'Update FPO details below.' : 'Register a new Farmer Producer Organization.'}</div>
              </div>
              <button className="modal-close" onClick={() => setShowForm(false)} title="Close">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div className="modal-body">
              <OrganizationForm
                initialData={editingOrg || undefined}
                onSubmit={handleSubmit}
                onCancel={() => setShowForm(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}