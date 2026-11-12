import { useState } from 'react';
import { Plus } from 'lucide-react';
import { financeService } from '../services/financeService';
import { getApiErrorMessage } from '../utils/errors';

export default function AccountForm({ onSaved }: { onSaved: () => void }) {
  const [form, setForm] = useState({ account_code: '', account_name: '', account_type: 'Asset', account_group: 'Current Assets', account_subtype: '' });
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setSaving(true);
    try { await financeService.createAccount({ ...form, account_subtype: form.account_subtype || null }); onSaved(); }
    catch (e) { setError(getApiErrorMessage(e, 'Unable to add account')); }
    finally { setSaving(false); }
  };
  return <section className="stat-card" style={{ padding: 20, marginBottom: 20 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}><Plus size={18} color="var(--accent)" /><div><h3 style={{ fontSize: '0.95rem' }}>Add account</h3><p style={{ color: 'var(--text-muted)', fontSize: '0.76rem', marginTop: 3 }}>Add an organization account to the chart.</p></div></div>
    {error && <div className="error-banner" style={{ marginBottom: 14 }}>{error}</div>}
    <form onSubmit={submit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 180px), 1fr))', gap: 14, alignItems: 'end' }}>
      <label className="form-group"><span className="form-label">Account code</span><input className="form-input" required placeholder="e.g. 1001" value={form.account_code} onChange={e => setForm({ ...form, account_code: e.target.value })} /></label>
      <label className="form-group"><span className="form-label">Account name</span><input className="form-input" required placeholder="Account name" value={form.account_name} onChange={e => setForm({ ...form, account_name: e.target.value })} /></label>
      <label className="form-group"><span className="form-label">Account type</span><select className="form-select" value={form.account_type} onChange={e => setForm({ ...form, account_type: e.target.value })}>{['Asset', 'Liability', 'Equity', 'Income', 'Expense'].map(x => <option key={x}>{x}</option>)}</select></label>
      <label className="form-group"><span className="form-label">Account group</span><input className="form-input" required placeholder="e.g. Current Assets" value={form.account_group} onChange={e => setForm({ ...form, account_group: e.target.value })} /></label>
      <label className="form-group"><span className="form-label">Subtype <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></span><select className="form-select" value={form.account_subtype} onChange={e => setForm({ ...form, account_subtype: e.target.value })}><option value="">No subtype</option><option value="CASH">Cash</option><option value="BANK">Bank</option></select></label>
      <button disabled={saving} className="btn btn-primary" type="submit">{saving ? 'Saving…' : 'Add account'}</button>
    </form>
  </section>;
}
