import React, { useState } from 'react';
import { UserRoleSelector } from './UserRoleSelector';

interface User {
  id?: number;
  full_name: string;
  email: string;
  role: { name: string } | null;
  organization_id: number;
  is_active: boolean;
}

interface UserFormProps {
  initialData?: Partial<User>;
  onSuccess: () => void;
  onCancel: () => void;
  isSuperAdmin: boolean;
  currentOrgId?: number;
}

export const UserForm: React.FC<UserFormProps> = ({ initialData, onSuccess, onCancel, isSuperAdmin, currentOrgId }) => {
  const [formData, setFormData] = useState({
    full_name:       initialData?.full_name  || '',
    email:           initialData?.email      || '',
    role_name:       initialData?.role?.name || 'Viewer',
    organization_id: initialData?.organization_id || currentOrgId || 1,
    password:        '',
    is_active:       initialData?.is_active ?? true,
  });
  const [loading, setLoading] = useState(false);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFormData(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try { onSuccess(); } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  const isEdit = !!initialData?.id;

  return (
    <form onSubmit={handleSubmit} className="form-grid form-grid--single" style={{ gap: '14px' }}>

      <div className="form-group">
        <label className="form-label">Full Name <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" value={formData.full_name} onChange={set('full_name')} required placeholder="e.g. Priya Sharma" />
      </div>

      <div className="form-group">
        <label className="form-label">Email Address <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" type="email" value={formData.email} onChange={set('email')} required placeholder="user@fpo360.in" />
      </div>

      {!isEdit && (
        <div className="form-group">
          <label className="form-label">Temporary Password <span style={{ color: 'var(--red)' }}>*</span></label>
          <input className="form-input" type="password" value={formData.password} onChange={set('password')} required placeholder="Min. 6 characters" />
          <span className="form-hint">User should change this after first login.</span>
        </div>
      )}

      <UserRoleSelector
        value={formData.role_name}
        onChange={(role_name) => setFormData(prev => ({ ...prev, role_name }))}
        isSuperAdmin={isSuperAdmin}
      />

      {isSuperAdmin && (
        <div className="form-group">
          <label className="form-label">Organization ID <span style={{ color: 'var(--red)' }}>*</span></label>
          <input className="form-input" type="number" min={1} value={formData.organization_id}
            onChange={(e) => setFormData(prev => ({ ...prev, organization_id: parseInt(e.target.value) || 1 }))} />
          <span className="form-hint">Enter the numeric ID of the target organization.</span>
        </div>
      )}

      <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
        <div>
          <div className="form-label" style={{ marginBottom: 0 }}>Account Status</div>
          <div className="form-hint" style={{ marginTop: 2 }}>{formData.is_active ? 'User can log in' : 'Login disabled'}</div>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={formData.is_active}
          onClick={() => setFormData(prev => ({ ...prev, is_active: !prev.is_active }))}
          style={{
            width: '44px', height: '24px', borderRadius: '12px', border: 'none', cursor: 'pointer', flexShrink: 0,
            background: formData.is_active ? 'var(--accent)' : 'var(--border-light)',
            position: 'relative', transition: 'background 0.2s'
          }}
        >
          <span style={{
            position: 'absolute', top: '3px',
            left: formData.is_active ? '23px' : '3px',
            width: '18px', height: '18px', borderRadius: '50%', background: '#fff',
            transition: 'left 0.2s', display: 'block'
          }} />
        </button>
      </div>

      <div className="form-actions" style={{ marginTop: '6px' }}>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ minWidth: '140px' }}>
          {loading ? (isEdit ? 'Saving…' : 'Creating…') : isEdit ? 'Update User' : 'Create User'}
        </button>
      </div>
    </form>
  );
};