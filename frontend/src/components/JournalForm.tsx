import { useEffect, useState } from 'react';
import { Plus, Scale } from 'lucide-react';
import { financeService, FinanceAccount, FinanceYear } from '../services/financeService';
import { getApiErrorMessage } from '../utils/errors';
import { farmerService } from '../services/farmerService';
import { customerService } from '../services/salesService';

type Line = { account_id: number; debit: string; credit: string; party_id: string };
const cents = (value: string) => {
  const match = /^(\d*)(?:\.(\d{0,2}))?$/.exec(value);
  if (!match) return 0n;
  return BigInt(match[1] || '0') * 100n + BigInt(((match[2] || '') + '00').slice(0, 2));
};
const money = (value: bigint) => `${value / 100n}.${String(value % 100n).padStart(2, '0')}`;
const blankLine = (): Line => ({ account_id: 0, debit: '', credit: '', party_id: '' });
const controlStyle = { minWidth: 108 };

export default function JournalForm({ onSaved }: { onSaved: () => void }) {
  const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
  const [years, setYears] = useState<FinanceYear[]>([]);
  const [farmers, setFarmers] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [year, setYear] = useState('');
  const [narration, setNarration] = useState('');
  const [lines, setLines] = useState<Line[]>([blankLine(), blankLine()]);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const debitTotal = lines.reduce((sum, line) => sum + cents(line.debit), 0n);
  const creditTotal = lines.reduce((sum, line) => sum + cents(line.credit), 0n);
  const difference = debitTotal > creditTotal ? debitTotal - creditTotal : creditTotal - debitTotal;
  const balanced = debitTotal > 0n && debitTotal === creditTotal && lines.every(line => {
    const debit = cents(line.debit); const credit = cents(line.credit);
    return (debit > 0n) !== (credit > 0n);
  });

  useEffect(() => {
    Promise.all([financeService.accounts(), financeService.years(), farmerService.getFarmers(), customerService.getActiveCustomers()]).then(([a, y, f, c]) => {
      setAccounts(a.data.filter(x => x.is_active)); setYears(y.data);
      setFarmers(f.data.filter((x: any) => x.is_active)); setCustomers(c.data.filter((x: any) => x.is_active));
      const current = y.data.find(x => x.is_current); if (current) setYear(String(current.id));
    }).catch(e => setError(getApiErrorMessage(e, 'Unable to load journal options')));
  }, []);

  const change = (index: number, key: keyof Line, value: string) => setLines(current => current.map((line, i) => {
    if (i !== index) return line;
    if (key === 'account_id') {
      const account = accounts.find(a => a.id === Number(value));
      const oldAccount = accounts.find(a => a.id === line.account_id);
      const partyType = (item?: FinanceAccount) => item?.system_key === 'ACCOUNTS_RECEIVABLE' ? 'CUSTOMER' : item?.system_key === 'ACCOUNTS_PAYABLE_FARMERS' ? 'FARMER' : null;
      return { ...line, account_id: Number(value), party_id: partyType(oldAccount) === partyType(account) ? line.party_id : '' };
    }
    return { ...line, [key]: value };
  }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setSaving(true);
    try {
      await financeService.createJournal({ entry_date: date, financial_year_id: Number(year), narration, source_type: 'MANUAL', lines: lines.map(line => {
        const account = accounts.find(a => a.id === line.account_id);
        const partyType = account?.system_key === 'ACCOUNTS_RECEIVABLE' ? 'CUSTOMER' : account?.system_key === 'ACCOUNTS_PAYABLE_FARMERS' ? 'FARMER' : null;
        return { account_id: line.account_id, debit: line.debit || '0.00', credit: line.credit || '0.00', party_type: partyType, party_id: partyType && line.party_id ? Number(line.party_id) : null };
      }) });
      setNarration(''); setLines([blankLine(), blankLine()]); onSaved();
    } catch (e) { setError(getApiErrorMessage(e, 'Unable to post journal')); }
    finally { setSaving(false); }
  };

  return <section className="stat-card" style={{ padding: 20, marginBottom: 20 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}><span style={{ width: 36, height: 36, display: 'grid', placeItems: 'center', borderRadius: 9, background: 'rgba(74, 222, 128, 0.12)', color: 'var(--accent)' }}><Scale size={18} /></span><div><h3 style={{ fontSize: '0.98rem' }}>Create journal entry</h3><p style={{ color: 'var(--text-muted)', fontSize: '0.76rem', marginTop: 3 }}>Enter the journal details, then balance debits and credits.</p></div></div>
    {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
    <form onSubmit={submit}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 190px), 1fr))', gap: 14, alignItems: 'end', marginBottom: 20 }}>
        <label className="form-group"><span className="form-label">Entry date</span><input className="form-input" type="date" required value={date} onChange={e => setDate(e.target.value)} /></label>
        <label className="form-group"><span className="form-label">Financial year</span><select className="form-select" required value={year} onChange={e => setYear(e.target.value)}><option value="">Select financial year</option>{years.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}</select></label>
        <label className="form-group" style={{ gridColumn: '1 / -1' }}><span className="form-label">Narration</span><input className="form-input" required placeholder="Describe this journal entry" value={narration} onChange={e => setNarration(e.target.value)} /></label>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 10 }}><div><h4 style={{ fontSize: '0.84rem' }}>Journal lines</h4><p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 3 }}>Choose an account and enter an amount on either the debit or credit side.</p></div><button type="button" className="btn btn-ghost" onClick={() => setLines(current => [...current, blankLine()])}><Plus size={15} />Add line</button></div>
      <div className="table-wrapper" style={{ marginBottom: 16 }}><div className="table-scroll"><table className="data-table" style={{ minWidth: 700 }}><thead><tr><th style={{ width: 52 }}>Line</th><th style={{ minWidth: 240 }}>Account</th><th style={{ minWidth: 140 }}>Debit</th><th style={{ minWidth: 140 }}>Credit</th><th style={{ minWidth: 170 }}>Party</th></tr></thead><tbody>
        {lines.map((line, i) => {
          const account = accounts.find(a => a.id === line.account_id);
          const partyLabel = account?.system_key === 'ACCOUNTS_RECEIVABLE' ? 'Customer' : account?.system_key === 'ACCOUNTS_PAYABLE_FARMERS' ? 'Farmer' : '';
          const partyRows = partyLabel === 'Customer' ? customers : farmers;
          return <tr key={i}>
            <td style={{ color: 'var(--text-muted)' }}>{String(i + 1).padStart(2, '0')}</td>
            <td><select className="form-select" aria-label={`Line ${i + 1} account`} required value={line.account_id || ''} onChange={e => change(i, 'account_id', e.target.value)}><option value="">Select account</option>{accounts.map(a => <option key={a.id} value={a.id}>{a.account_code} · {a.account_name}</option>)}</select></td>
            <td><input className="form-input" style={controlStyle} inputMode="decimal" aria-label={`Line ${i + 1} debit`} placeholder="0.00" value={line.debit} onChange={e => change(i, 'debit', e.target.value)} /></td>
            <td><input className="form-input" style={controlStyle} inputMode="decimal" aria-label={`Line ${i + 1} credit`} placeholder="0.00" value={line.credit} onChange={e => change(i, 'credit', e.target.value)} /></td>
            <td>{partyLabel ? <select className="form-select" aria-label={`Line ${i + 1} ${partyLabel}`} required value={line.party_id} onChange={e => change(i, 'party_id', e.target.value)}><option value="">Select {partyLabel.toLowerCase()}</option>{partyRows.map((party: any) => <option key={party.id} value={party.id}>{party.customer_name || party.farmer_name}{party.customer_code || party.farmer_code ? ` · ${party.customer_code || party.farmer_code}` : ''}</option>)}</select> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
          </tr>;
        })}
      </tbody></table></div></div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}><div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(105px, auto))', gap: 1, background: 'var(--border)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
        {[['Debit total', money(debitTotal)], ['Credit total', money(creditTotal)], ['Difference', money(difference)]].map(([label, value]) => <div key={label} style={{ padding: '10px 14px', background: 'var(--bg-elevated)', minWidth: 108 }}><div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 4 }}>{label}</div><strong style={{ fontFamily: "'Space Grotesk', sans-serif", color: label === 'Difference' ? (difference === 0n && debitTotal > 0n ? '#4ade80' : 'var(--text-primary)') : 'var(--text-primary)' }}>{value}</strong></div>)}
      </div></div>
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}><button disabled={saving || !year || !narration.trim() || !balanced || lines.some(line => !line.account_id || !/^(\d*)(?:\.(\d{0,2}))?$/.test(line.debit) || !/^(\d*)(?:\.(\d{0,2}))?$/.test(line.credit) || (accounts.find(a => a.id === line.account_id)?.system_key === 'ACCOUNTS_RECEIVABLE' && !line.party_id) || (accounts.find(a => a.id === line.account_id)?.system_key === 'ACCOUNTS_PAYABLE_FARMERS' && !line.party_id))} className="btn btn-primary" type="submit">{saving ? 'Posting…' : 'Post journal'}</button></div>
    </form>
  </section>;
}
