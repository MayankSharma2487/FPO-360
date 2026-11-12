import { FormEvent, useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { useAuth } from '../context/AuthContext';
import {
  organizationSettingsService,
  OrganizationSettingsPayload,
} from '../services/organizationSettingsService';
import { getApiErrorMessage } from '../utils/errors';

const EMPTY_SETTINGS: OrganizationSettingsPayload = {
  logo_url: '',
  address: '',
  phone: '',
  email: '',
  website: '',
};

export default function Settings() {
  const { user } = useAuth();
  const organizationId = user?.organization_id;
  const [values, setValues] = useState<OrganizationSettingsPayload>(EMPTY_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!organizationId) {
        setError('An organization context is required to manage settings.');
        setLoading(false);
        return;
      }
      try {
        const response = await organizationSettingsService.get(organizationId);
        if (!cancelled) {
          const { logo_url, address, phone, email, website } = response.data;
          setValues({ logo_url: logo_url ?? '', address: address ?? '', phone: phone ?? '', email: email ?? '', website: website ?? '' });
        }
      } catch (err: any) {
        if (!cancelled && err?.response?.status === 404) {
          setValues(EMPTY_SETTINGS);
        } else if (!cancelled) {
          setError(getApiErrorMessage(err, 'Failed to load organization settings'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [organizationId]);

  const setField = (field: keyof OrganizationSettingsPayload, value: string) => {
    setValues(current => ({ ...current, [field]: value }));
    setSuccess(null);
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!organizationId) {
      setError('An organization context is required to save settings.');
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await organizationSettingsService.save(organizationId, {
        logo_url: values.logo_url?.trim() || null,
        address: values.address?.trim() || null,
        phone: values.phone?.trim() || null,
        email: values.email?.trim() || null,
        website: values.website?.trim() || null,
      });
      setSuccess('Organization settings saved.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save organization settings'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Organization settings</h2>
            <p className="page-subtitle">Contact and branding details for your FPO</p>
          </div>
        </div>
        {error && <div className="error-banner" role="alert">{error}</div>}
        {success && <div className="success-banner" role="status">{success}</div>}
        {loading ? <div className="table-skeleton">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton-row" />)}</div> : (
          <form className="form-card" onSubmit={save} style={{ maxWidth: 760 }}>
            <div className="form-grid">
              <label><span className="form-label">Contact email</span><input className="form-input" type="email" maxLength={255} value={values.email ?? ''} onChange={event => setField('email', event.target.value)} /></label>
              <label><span className="form-label">Phone</span><input className="form-input" type="tel" maxLength={20} value={values.phone ?? ''} onChange={event => setField('phone', event.target.value)} /></label>
              <label><span className="form-label">Website</span><input className="form-input" type="url" maxLength={255} value={values.website ?? ''} onChange={event => setField('website', event.target.value)} placeholder="https://example.org" /></label>
              <label><span className="form-label">Logo URL</span><input className="form-input" type="url" maxLength={500} value={values.logo_url ?? ''} onChange={event => setField('logo_url', event.target.value)} placeholder="https://example.org/logo.png" /></label>
              <label style={{ gridColumn: '1 / -1' }}><span className="form-label">Address</span><textarea className="form-input" rows={4} maxLength={500} value={values.address ?? ''} onChange={event => setField('address', event.target.value)} /></label>
            </div>
            <div className="form-actions" style={{ marginTop: 20 }}>
              <button className="btn btn-primary" type="submit" disabled={saving || loading || !organizationId}>{saving ? 'Saving...' : 'Save settings'}</button>
            </div>
          </form>
        )}
      </div>
    </RoleGuard>
  );
}
