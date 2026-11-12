import { useEffect, useState } from 'react';
import { ArrowLeft, CalendarDays } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { financeService, FinanceYear } from '../services/financeService';
import { getApiErrorMessage } from '../utils/errors';
import { useAuth } from '../context/AuthContext';

export default function FinancialYears() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const mayWrite = ['Super Admin', 'FPO Admin', 'Accountant'].includes(user?.role?.name || '');
  const mayLock = ['Super Admin', 'FPO Admin'].includes(user?.role?.name || '');
  const [rows, setRows] = useState<FinanceYear[]>([]);
  const [name, setName] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [err, setErr] = useState('');
  const load = () => financeService.years().then(r => setRows(r.data)).catch(e => setErr(getApiErrorMessage(e, 'Unable to load financial years')));
  useEffect(() => { load(); }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault(); setErr('');
    try {
      await financeService.createYear({ name, start_date: start, end_date: end });
      setName(''); setStart(''); setEnd(''); load();
    } catch (x) { setErr(getApiErrorMessage(x, 'Unable to create financial year')); }
  };

  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Accountant', 'Manager', 'Viewer']}>
    <div className="page-wrapper">
      <header className="page-header"><div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}><button type="button" className="btn btn-ghost" onClick={() => navigate('/finance')} style={{ gap: 7, padding: '7px 11px', flexShrink: 0 }}><ArrowLeft size={15} />Back to Finance</button><div><h2 className="page-title">Financial Years</h2><p className="page-subtitle">Manage reporting periods and their access status</p></div></div><span className="page-count-badge">{rows.length} financial year{rows.length === 1 ? '' : 's'}</span></header>
      {err && <div className="error-banner" style={{ marginBottom: 16 }}>{err}</div>}
      {mayWrite && <section className="stat-card" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}><CalendarDays size={18} color="var(--accent)" /><div><h3 style={{ fontSize: '0.95rem' }}>Create financial year</h3><p style={{ color: 'var(--text-muted)', fontSize: '0.76rem', marginTop: 3 }}>Use the April to March reporting period.</p></div></div>
        <form onSubmit={create} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 190px), 1fr))', gap: 14, alignItems: 'end' }}>
          <label className="form-group"><span className="form-label">Year name</span><input className="form-input" required placeholder="e.g. FY 2026-27" value={name} onChange={e => setName(e.target.value)} /></label>
          <label className="form-group"><span className="form-label">Start date</span><input className="form-input" required type="date" value={start} onChange={e => setStart(e.target.value)} /></label>
          <label className="form-group"><span className="form-label">End date</span><input className="form-input" required type="date" value={end} onChange={e => setEnd(e.target.value)} /></label>
          <button className="btn btn-primary" type="submit">Create year</button>
        </form>
      </section>}
      <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>Name</th><th>Start</th><th>End</th><th>Status</th><th>Actions</th></tr></thead><tbody>
        {rows.length === 0 ? <tr><td colSpan={5} className="empty-row">No financial years have been created yet.</td></tr> : rows.map(y => <tr key={y.id}>
          <td className="primary-cell">{y.name}</td><td>{y.start_date}</td><td>{y.end_date}</td>
          <td><span className={`status-pill ${y.is_locked ? 'status-pill--inactive' : y.is_current ? 'status-pill--active' : 'status-pill--pending'}`}>{y.is_locked ? 'Locked' : y.is_current ? 'Current' : 'Open'}</span></td>
          <td><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>{mayWrite && !y.is_locked && !y.is_current && <button className="btn btn-ghost" onClick={() => financeService.setCurrent(y.id).then(load)}>Set current</button>}{mayLock && <button className="btn btn-ghost" onClick={() => financeService.setLocked(y.id, !y.is_locked).then(load)}>{y.is_locked ? 'Unlock' : 'Lock'}</button>}</div></td>
        </tr>)}
      </tbody></table></div></div>
    </div>
  </RoleGuard>;
}
