import { useState } from 'react';
import { getApiErrorMessage } from '../utils/errors';
import { LicensePayload, LicenseRecord, LicenseStatus } from '../services/licenseService';

const statuses: LicenseStatus[] = ['Active', 'Expired', 'Pending', 'Not Applicable'];

export default function LicenseForm({
  initialData,
  onSubmit,
  onCancel,
}: {
  initialData?: LicenseRecord | null;
  onSubmit: (payload: LicensePayload) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<LicensePayload>({
    license_type: initialData?.license_type ?? '',
    license_number: initialData?.license_number ?? '',
    issuing_authority: initialData?.issuing_authority ?? '',
    issue_date: initialData?.issue_date ?? '',
    expiry_date: initialData?.expiry_date ?? '',
    status: initialData?.status ?? 'Active',
    renewal_date: initialData?.renewal_date ?? '',
    remarks: initialData?.remarks ?? '',
    document_reference: initialData?.document_reference ?? '',
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const change = (key: keyof LicensePayload, value: string) => setForm(current => ({ ...current, [key]: value }));

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('');
    if (form.issue_date && form.expiry_date && form.expiry_date < form.issue_date) {
      setError('Expiry date cannot be before issue date'); return;
    }
    if (form.issue_date && form.renewal_date && form.renewal_date < form.issue_date) {
      setError('Renewal date cannot be before issue date'); return;
    }
    setSaving(true);
    try {
      await onSubmit({ ...form, license_number: form.license_number || null, issue_date: form.issue_date || null, expiry_date: form.expiry_date || null, renewal_date: form.renewal_date || null, remarks: form.remarks || null, document_reference: form.document_reference || null });
    } catch (e) { setError(getApiErrorMessage(e, 'Unable to save license')); }
    finally { setSaving(false); }
  };

  return <form onSubmit={submit} style={{ display: 'grid', gap: 14 }}>
    {error && <div className="error-banner">{error}</div>}
    <div className="form-grid">
      <label className="form-group"><span className="form-label form-label-required">License type</span><input className="form-input" required maxLength={100} placeholder="e.g. FSSAI" value={form.license_type} onChange={e => change('license_type', e.target.value)} /></label>
      <label className="form-group"><span className="form-label">License number</span><input className="form-input" maxLength={100} value={form.license_number ?? ''} onChange={e => change('license_number', e.target.value)} /></label>
      <label className="form-group"><span className="form-label form-label-required">Issuing authority</span><input className="form-input" required maxLength={200} placeholder="Issuing authority" value={form.issuing_authority} onChange={e => change('issuing_authority', e.target.value)} /></label>
      <label className="form-group"><span className="form-label">Status</span><select className="form-select" value={form.status} onChange={e => change('status', e.target.value)}>{statuses.map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="form-group"><span className="form-label">Issue date</span><input className="form-input" type="date" value={form.issue_date ?? ''} onChange={e => change('issue_date', e.target.value)} /></label>
      <label className="form-group"><span className="form-label">Expiry date</span><input className="form-input" type="date" value={form.expiry_date ?? ''} min={form.issue_date || undefined} onChange={e => change('expiry_date', e.target.value)} /></label>
      <label className="form-group"><span className="form-label">Renewal date</span><input className="form-input" type="date" value={form.renewal_date ?? ''} min={form.issue_date || undefined} onChange={e => change('renewal_date', e.target.value)} /></label>
      <label className="form-group"><span className="form-label">Document reference</span><input className="form-input" maxLength={500} placeholder="File name, URL or reference" value={form.document_reference ?? ''} onChange={e => change('document_reference', e.target.value)} /></label>
      <label className="form-group" style={{ gridColumn: '1 / -1' }}><span className="form-label">Remarks</span><textarea className="form-textarea" rows={3} value={form.remarks ?? ''} onChange={e => change('remarks', e.target.value)} /></label>
    </div>
    <div className="form-actions"><button type="button" className="btn btn-ghost" onClick={onCancel} disabled={saving}>Cancel</button><button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : initialData ? 'Save changes' : 'Add license'}</button></div>
  </form>;
}
