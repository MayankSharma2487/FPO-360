import { useEffect, useState } from 'react';
import { ArrowLeft, Scale } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { financeService, FinanceYear } from '../services/financeService';
import { getApiErrorMessage } from '../utils/errors';

export default function TrialBalance() {
  const navigate = useNavigate();
  const [years, setYears] = useState<FinanceYear[]>([]);
  const [year, setYear] = useState('');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [zero, setZero] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    financeService.years().then(r => { setYears(r.data); const current = r.data.find(x => x.is_current); if (current) setYear(String(current.id)); })
      .catch(e => setError(getApiErrorMessage(e, 'Unable to load financial years')));
  }, []);
  const run = () => {
    setError('');
    financeService.trialBalance({ financial_year_id: Number(year), as_on_date: date, include_zero: zero })
      .then(r => setData(r.data)).catch(e => setError(getApiErrorMessage(e, 'Unable to load trial balance')));
  };

  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Accountant', 'Manager', 'Viewer']}>
    <div className="page-wrapper">
      <header className="page-header"><div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}><button type="button" className="btn btn-ghost" onClick={() => navigate('/finance')} style={{ gap: 7, padding: '7px 11px', flexShrink: 0 }}><ArrowLeft size={15} />Back to Finance</button><div><h2 className="page-title">Trial Balance</h2><p className="page-subtitle">Review debit and credit balances for a financial year</p></div></div></header>
      {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
      <section className="stat-card" style={{ padding: 20, marginBottom: 20 }}>
        <h3 style={{ fontSize: '0.9rem', marginBottom: 14 }}>Report filters</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 190px), 1fr))', gap: 14, alignItems: 'end' }}>
          <label className="form-group"><span className="form-label">Financial year</span><select className="form-select" value={year} onChange={e => setYear(e.target.value)}><option value="">Select financial year</option>{years.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}</select></label>
          <label className="form-group"><span className="form-label">As on date</span><input className="form-input" type="date" value={date} onChange={e => setDate(e.target.value)} /></label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 9, minHeight: 40, color: 'var(--text-secondary)', fontSize: '0.8rem' }}><input type="checkbox" checked={zero} onChange={e => setZero(e.target.checked)} />Include zero balances</label>
          <button className="btn btn-primary" disabled={!year} onClick={run}>Run report</button>
        </div>
      </section>
      {data && <>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 14 }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}><span className="page-count-badge">Debit total: {data.debit_total}</span><span className="page-count-badge">Credit total: {data.credit_total}</span></div>
          <span className={`status-pill ${data.debit_total === data.credit_total ? 'status-pill--active' : 'status-pill--inactive'}`}>{data.debit_total === data.credit_total ? 'Balanced' : 'Out of balance'}</span>
        </div>
        <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>Code</th><th>Account</th><th>Debit</th><th>Credit</th></tr></thead><tbody>
          {data.accounts.length === 0 ? <tr><td colSpan={4} className="empty-row"><Scale size={24} style={{ display: 'block', margin: '0 auto 8px', opacity: 0.55 }} />No balances to display for this report.</td></tr> : data.accounts.map((a: any) => <tr key={a.account_id}><td><span className="mono-tag">{a.account_code}</span></td><td className="primary-cell">{a.account_name}</td><td>{a.debit}</td><td>{a.credit}</td></tr>)}
        </tbody></table></div></div>
      </>}
    </div>
  </RoleGuard>;
}
