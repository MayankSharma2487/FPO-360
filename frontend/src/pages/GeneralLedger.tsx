import { useEffect, useState } from 'react';
import { ArrowLeft, BookMarked } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { financeService, FinanceAccount } from '../services/financeService';
import { getApiErrorMessage } from '../utils/errors';

export default function GeneralLedger() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
  const [account, setAccount] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  useEffect(() => { financeService.accounts().then(r => setAccounts(r.data)).catch(e => setError(getApiErrorMessage(e, 'Unable to load accounts'))); }, []);
  const run = () => {
    setError('');
    financeService.ledger({ account_id: Number(account), start_date: from || undefined, end_date: to || undefined })
      .then(r => setData(r.data)).catch(e => setError(getApiErrorMessage(e, 'Unable to load ledger')));
  };

  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Accountant', 'Manager', 'Viewer']}>
    <div className="page-wrapper">
      <header className="page-header"><div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}><button type="button" className="btn btn-ghost" onClick={() => navigate('/finance')} style={{ gap: 7, padding: '7px 11px', flexShrink: 0 }}><ArrowLeft size={15} />Back to Finance</button><div><h2 className="page-title">General Ledger</h2><p className="page-subtitle">Review journal activity and running balances by account</p></div></div></header>
      {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
      <section className="stat-card" style={{ padding: 20, marginBottom: 20 }}>
        <h3 style={{ fontSize: '0.9rem', marginBottom: 14 }}>Report filters</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 190px), 1fr))', gap: 14, alignItems: 'end' }}>
          <label className="form-group"><span className="form-label">Account</span><select className="form-select" value={account} onChange={e => setAccount(e.target.value)}><option value="">Select account</option>{accounts.map(a => <option key={a.id} value={a.id}>{a.account_code} · {a.account_name}</option>)}</select></label>
          <label className="form-group"><span className="form-label">From date</span><input className="form-input" type="date" value={from} onChange={e => setFrom(e.target.value)} /></label>
          <label className="form-group"><span className="form-label">To date</span><input className="form-input" type="date" value={to} onChange={e => setTo(e.target.value)} /></label>
          <button className="btn btn-primary" disabled={!account} onClick={run}>Show ledger</button>
        </div>
      </section>
      {data && <>
        <div className="cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 165px), 1fr))', gap: 12, marginBottom: 18 }}>
          {([['Opening balance', data.opening_balance, data.opening_balance_side], ['Debit total', data.debit_total, 'Debit'], ['Credit total', data.credit_total, 'Credit'], ['Closing balance', data.closing_balance, data.closing_balance_side]] as [string, any, string][]).map(([label, value, side]) => <div className="stat-card" key={label} style={{ padding: '15px 17px' }}><div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 7 }}>{label}</div><strong style={{ fontSize: '1rem', fontFamily: "'Space Grotesk', sans-serif" }}>{value} <small style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', fontWeight: 500 }}>{side}</small></strong></div>)}
        </div>
        <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>Date</th><th>Journal</th><th>Narration</th><th>Debit</th><th>Credit</th><th>Balance</th><th>Side</th></tr></thead><tbody>
          {data.lines.length === 0 ? <tr><td colSpan={7} className="empty-row"><BookMarked size={24} style={{ display: 'block', margin: '0 auto 8px', opacity: 0.55 }} />No ledger activity for this account and date range.</td></tr> : data.lines.map((line: any, i: number) => <tr key={`${line.journal_no}-${i}`}><td>{line.date}</td><td><span className="mono-tag">{line.journal_no}</span></td><td>{line.narration}</td><td>{line.debit}</td><td>{line.credit}</td><td className="primary-cell">{line.running_balance}</td><td><span className="status-pill status-pill--pending">{line.balance_side}</span></td></tr>)}
        </tbody></table></div></div>
      </>}
    </div>
  </RoleGuard>;
}
