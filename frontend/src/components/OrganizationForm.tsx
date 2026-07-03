import React, { useState } from 'react';

interface Organization {
  id?: number;
  organization_name: string;
  registration_number: string;
  pan_number?: string | null;
  gst_number?: string | null;
  fssai_number?: string | null;
  state?: string | null;
  district?: string | null;
}

interface OrganizationFormProps {
  initialData?: Partial<Organization>;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export const OrganizationForm: React.FC<OrganizationFormProps> = ({ initialData, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    organization_name:  initialData?.organization_name  || '',
    registration_number: initialData?.registration_number || '',
    pan_number:         initialData?.pan_number   || '',
    gst_number:         initialData?.gst_number   || '',
    fssai_number:       initialData?.fssai_number || '',
    state:              initialData?.state        || '',
    district:           initialData?.district     || '',
  });
  const [loading, setLoading] = useState(false);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setFormData(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try { await onSubmit(formData); } finally { setLoading(false); }
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid form-grid--single" style={{ gap: '16px' }}>

      <div className="form-section-label" style={{ display: 'block', gridColumn: 'unset' }}>Basic Information</div>

      <div className="form-group">
        <label className="form-label">Organization Name <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" value={formData.organization_name} onChange={set('organization_name')} required placeholder="e.g. Sahyadri FPO" />
      </div>

      <div className="form-group">
        <label className="form-label">Registration Number <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" value={formData.registration_number} onChange={set('registration_number')} required placeholder="CIN / Registration No." />
      </div>

      <div className="form-section-label" style={{ display: 'block', gridColumn: 'unset' }}>Tax &amp; Compliance</div>

      <div className="form-grid" style={{ margin: 0 }}>
        <div className="form-group">
          <label className="form-label">PAN Number <span className="form-label-optional">(optional)</span></label>
          <input className="form-input" value={formData.pan_number} onChange={set('pan_number')} placeholder="ABCDE1234F" />
        </div>
        <div className="form-group">
          <label className="form-label">GST Number <span className="form-label-optional">(optional)</span></label>
          <input className="form-input" value={formData.gst_number} onChange={set('gst_number')} placeholder="27ABCDE1234F1Z5" />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">FSSAI Number <span className="form-label-optional">(optional)</span></label>
        <input className="form-input" value={formData.fssai_number} onChange={set('fssai_number')} placeholder="FSSAI License No." />
      </div>

      <div className="form-section-label" style={{ display: 'block', gridColumn: 'unset' }}>Location</div>

      <div className="form-grid" style={{ margin: 0 }}>
        <div className="form-group">
          <label className="form-label">State</label>
          <input className="form-input" value={formData.state} onChange={set('state')} placeholder="Maharashtra" />
        </div>
        <div className="form-group">
          <label className="form-label">District</label>
          <input className="form-input" value={formData.district} onChange={set('district')} placeholder="Nashik" />
        </div>
      </div>

      <div className="form-actions" style={{ marginTop: '8px' }}>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ minWidth: '160px' }}>
          {loading ? 'Saving…' : initialData?.id ? 'Update Organization' : 'Create Organization'}
        </button>
      </div>
    </form>
  );
};