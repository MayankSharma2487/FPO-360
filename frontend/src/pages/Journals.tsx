import { useEffect, useState } from 'react';
import { ArrowLeft, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import JournalForm from '../components/JournalForm';
import { financeService, Journal } from '../services/financeService';
import { useAuth } from '../context/AuthContext';
import { Modal } from '../components/ui/Modal';
import { getApiErrorMessage } from '../utils/errors';

export default function Journals() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const canWrite = ['Super Admin', 'FPO Admin', 'Accountant'].includes(user?.role?.name || '');
  const [rows, setRows] = useState<Journal[]>([]);
  const [selected, setSelected] = useState<Journal | null>(null);
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const load = () => financeService.journals().then(r => setRows(r.data)).catch(e => setError(getApiErrorMessage(e, 'Unable to load journals')));
  useEffect(() => { load(); }, []);

  const voidJournal = async (e: React.FormEvent) => {
    e.preventDefault(); if (!selected) return;
    setBusy(true); setError('');
    try { await financeService.voidJournal(selected.id, reason); setSelected(null); setReason(''); await load(); }
    catch (e) { setError(getApiErrorMessage(e, 'Unable to void journal')); }
    finally { setBusy(false); }
  };

  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Accountant', 'Manager', 'Viewer']}>
    <div className="page-wrapper">
      <header className="page-header"><div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}><button type="button" className="btn btn-ghost" onClick={() => navigate('/finance')} style={{ gap: 7, padding: '7px 11px', flexShrink: 0 }}><ArrowLeft size={15} />Back to Finance</button><div><h2 className="page-title">Journal Entries</h2><p className="page-subtitle">Posted manual journals are immutable and auditable</p></div></div><span className="page-count-badge">{rows.length} entries</span></header>
      {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
      {canWrite && <JournalForm onSaved={load} />}
      <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>Journal</th><th>Date</th><th>Narration</th><th>Source</th><th>Status</th><th>Actions</th></tr></thead><tbody>
        {rows.length === 0 ? <tr><td colSpan={6} className="empty-row"><FileText size={24} style={{ display: 'block', margin: '0 auto 8px', opacity: 0.55 }} />No journal entries found.</td></tr> : rows.map(j => <tr key={j.id}>
          <td><span className="mono-tag">{j.journal_no}</span></td><td>{j.entry_date}</td><td className="primary-cell">{j.narration}</td><td><span className="status-pill status-pill--pending">{j.source_type}</span></td>
          <td><span className={`status-pill ${j.status === 'Posted' ? 'status-pill--active' : j.status === 'Void' ? 'status-pill--inactive' : 'status-pill--pending'}`}>{j.status}</span></td>
          <td>{canWrite && j.status === 'Posted' && <button className="btn btn-ghost" onClick={() => { setError(''); setSelected(j); }}>Void</button>}</td>
        </tr>)}
      </tbody></table></div></div>
      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Void journal" subtitle="This action preserves the journal and removes it from reports.">
        <form onSubmit={voidJournal} style={{ display: 'grid', gap: 14 }}><label className="form-group" htmlFor="void-reason"><span className="form-label">Reason</span><textarea className="form-textarea" id="void-reason" required maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} /></label>{error && <div className="error-banner">{error}</div>}<div style={{ display: 'flex', justifyContent: 'flex-end' }}><button disabled={busy || !reason.trim()} className="btn btn-primary" type="submit">{busy ? 'Voiding…' : 'Confirm void'}</button></div></form>
      </Modal>
    </div>
  </RoleGuard>;
}
