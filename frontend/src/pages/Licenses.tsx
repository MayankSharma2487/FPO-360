import { useEffect, useMemo, useState } from 'react';
import { BadgeCheck, CalendarClock, FileBadge, Plus, Search } from 'lucide-react';
import { RoleGuard } from '../components/RoleGuard';
import { Modal } from '../components/ui/Modal';
import LicenseForm from '../components/LicenseForm';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage } from '../utils/errors';
import { licenseService, LicensePayload, LicenseRecord, LicenseStatus } from '../services/licenseService';

const READ_ROLES = ['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer'];
const WRITE_ROLES = ['Super Admin', 'FPO Admin', 'Manager'];
type StatusFilter = LicenseStatus | 'Expiring Soon' | '';

const statusClass = (status: string) => status === 'Active' ? 'status-pill--active' : status === 'Expired' ? 'status-pill--inactive' : 'status-pill--pending';
const formatDate = (value: string | null) => value ? new Date(`${value}T00:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

export default function Licenses() {
  const { user } = useAuth();
  const canWrite = WRITE_ROLES.includes(user?.role?.name || '');
  const [licenses, setLicenses] = useState<LicenseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<LicenseRecord | null>(null);
  const [details, setDetails] = useState<LicenseRecord | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const load = async () => {
    setLoading(true); setError('');
    try { const response = await licenseService.list(); setLicenses(response.data); }
    catch (e) { setError(getApiErrorMessage(e, 'Unable to load licenses')); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  const licenseTypes = useMemo(() => Array.from(new Set(licenses.map(item => item.license_type))).sort((a, b) => a.localeCompare(b)), [licenses]);
  const filtered = useMemo(() => licenses.filter(item => {
    const text = `${item.license_type} ${item.license_number ?? ''} ${item.issuing_authority}`.toLowerCase();
    const matchesSearch = text.includes(search.trim().toLowerCase());
    const matchesType = !typeFilter || item.license_type === typeFilter;
    const matchesStatus = !statusFilter || (statusFilter === 'Expiring Soon' ? item.is_active && item.expiring_soon : item.display_status === statusFilter);
    return matchesSearch && matchesType && matchesStatus;
  }), [licenses, search, statusFilter, typeFilter]);

  const totals = {
    total: licenses.length,
    active: licenses.filter(item => item.is_active && item.display_status === 'Active').length,
    expiring: licenses.filter(item => item.is_active && item.expiring_soon).length,
    expired: licenses.filter(item => item.is_active && item.display_status === 'Expired').length,
  };

  const save = async (payload: LicensePayload) => {
    if (editing) await licenseService.update(editing.id, payload);
    else await licenseService.create(payload);
    setShowForm(false); setEditing(null); await load();
  };

  const openDetails = async (item: LicenseRecord) => {
    setDetailLoading(true); setError('');
    try { const response = await licenseService.get(item.id); setDetails(response.data); }
    catch (e) { setError(getApiErrorMessage(e, 'Unable to load license details')); }
    finally { setDetailLoading(false); }
  };

  const toggleActive = async (item: LicenseRecord) => {
    if (item.is_active && !window.confirm(`Deactivate ${item.license_type}${item.license_number ? ` (${item.license_number})` : ''}?`)) return;
    setError('');
    try {
      if (item.is_active) await licenseService.deactivate(item.id);
      else await licenseService.setActive(item.id, true);
      await load();
    } catch (e) { setError(getApiErrorMessage(e, 'Unable to update license')); }
  };

  return <RoleGuard allowedRoles={READ_ROLES}>
    <div className="page-wrapper">
      <header className="page-header">
        <div><h2 className="page-title">Licenses</h2><p className="page-subtitle">Keep organization licenses and renewal dates in one place</p></div>
        {canWrite && <button className="btn btn-primary" onClick={() => { setEditing(null); setShowForm(true); }}><Plus size={16} />Add License</button>}
      </header>

      <div className="cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 170px), 1fr))', gap: 14, marginBottom: 20 }}>
        {[
          { label: 'Total', value: totals.total, icon: FileBadge, color: '#60a5fa' },
          { label: 'Active', value: totals.active, icon: BadgeCheck, color: '#4ade80' },
          { label: 'Expiring Soon', value: totals.expiring, icon: CalendarClock, color: '#fbbf24' },
          { label: 'Expired', value: totals.expired, icon: CalendarClock, color: '#f87171' },
        ].map(({ label, value, icon: Icon, color }) => <div className="stat-card" key={label} style={{ padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}><span className="stat-label">{label}</span><Icon size={17} color={color} /></div>
          <div className="stat-value" style={{ fontSize: '1.5rem', color }}>{loading ? '—' : value}</div>
        </div>)}
      </div>

      {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
      <div className="table-toolbar" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 240px', maxWidth: 420 }}><Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} /><input className="search-input" style={{ paddingLeft: 36, width: '100%' }} placeholder="Search type, number or authority" value={search} onChange={e => setSearch(e.target.value)} /></div>
        <select className="form-select" style={{ width: 'auto', minWidth: 150 }} value={statusFilter} onChange={e => setStatusFilter(e.target.value as StatusFilter)}><option value="">All statuses</option><option value="Active">Active</option><option value="Expiring Soon">Expiring Soon</option><option value="Expired">Expired</option><option value="Pending">Pending</option><option value="Not Applicable">Not Applicable</option></select>
        <select className="form-select" style={{ width: 'auto', minWidth: 170 }} value={typeFilter} onChange={e => setTypeFilter(e.target.value)}><option value="">All license types</option>{licenseTypes.map(type => <option key={type}>{type}</option>)}</select>
      </div>

      {loading ? <div className="table-skeleton">{Array.from({ length: 5 }).map((_, index) => <div className="skeleton-row" key={index} style={{ marginBottom: 4 }} />)}</div> : <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>License</th><th>Issuing authority</th><th>Issue date</th><th>Expiry date</th><th>Status</th><th>Record</th><th>Actions</th></tr></thead><tbody>
        {filtered.length === 0 ? <tr><td colSpan={7} className="empty-row">{licenses.length ? 'No licenses match these filters.' : 'No licenses have been added yet.'}</td></tr> : filtered.map(item => <tr key={item.id}>
          <td><div className="primary-cell">{item.license_type}</div><span className="mono-tag" style={{ display: 'inline-block', marginTop: 5 }}>{item.license_number || 'Number not recorded'}</span></td>
          <td>{item.issuing_authority}</td><td>{formatDate(item.issue_date)}</td><td>{formatDate(item.expiry_date)}</td>
          <td><span className={`status-pill ${item.is_active ? statusClass(item.display_status) : 'status-pill--inactive'}`}>{item.is_active ? item.display_status : 'Deactivated'}</span>{item.is_active && item.expiring_soon && <span className="status-pill status-pill--pending" style={{ display: 'inline-block', margin: '4px 0 0 5px' }}>Expiring Soon</span>}</td>
          <td><span className="status-pill status-pill--pending">{item.is_active ? 'Active record' : 'Archived'}</span></td>
          <td><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}><button className="btn btn-ghost" onClick={() => openDetails(item)}>View</button>{canWrite && <><button className="btn btn-ghost" onClick={() => { setEditing(item); setShowForm(true); }}>Edit</button><button className="btn btn-ghost" onClick={() => toggleActive(item)}>{item.is_active ? 'Deactivate' : 'Reactivate'}</button></>}</div></td>
        </tr>)}
      </tbody></table></div></div>}

      <Modal isOpen={showForm} onClose={() => { setShowForm(false); setEditing(null); }} title={editing ? 'Edit license' : 'Add license'} subtitle="Record the license details and dates for this organization." size="lg">
        <LicenseForm key={editing?.id ?? 'new-license'} initialData={editing} onSubmit={save} onCancel={() => { setShowForm(false); setEditing(null); }} />
      </Modal>
      <Modal isOpen={detailLoading || !!details} onClose={() => setDetails(null)} title="License details" subtitle="License registry information" size="md">
        {detailLoading ? <div className="table-skeleton"><div className="skeleton-row" /></div> : details && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 180px), 1fr))', gap: 14 }}>
          {[
            ['License type', details.license_type], ['License number', details.license_number || 'Not recorded'], ['Issuing authority', details.issuing_authority],
            ['Status', details.display_status], ['Issue date', formatDate(details.issue_date)], ['Expiry date', formatDate(details.expiry_date)],
            ['Renewal date', formatDate(details.renewal_date)], ['Document reference', details.document_reference || 'Not provided'],
          ].map(([label, value]) => <div key={label}><div className="form-label">{label}</div><div style={{ color: 'var(--text-primary)', fontSize: '0.84rem', overflowWrap: 'anywhere' }}>{value}</div></div>)}
          {details.expiring_soon && <span className="status-pill status-pill--pending">Expiring within 30 days</span>}
          {details.remarks && <div style={{ gridColumn: '1 / -1' }}><div className="form-label">Remarks</div><p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', whiteSpace: 'pre-wrap' }}>{details.remarks}</p></div>}
        </div>}
      </Modal>
    </div>
  </RoleGuard>;
}
