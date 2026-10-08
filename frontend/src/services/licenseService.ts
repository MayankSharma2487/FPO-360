import api from './api';

export type LicenseStatus = 'Active' | 'Expired' | 'Pending' | 'Not Applicable';

export interface LicenseRecord {
  id: number;
  organization_id: number;
  created_by: number | null;
  updated_by: number | null;
  license_type: string;
  license_number: string | null;
  issuing_authority: string;
  issue_date: string | null;
  expiry_date: string | null;
  status: LicenseStatus;
  display_status: LicenseStatus;
  expiring_soon: boolean;
  renewal_date: string | null;
  remarks: string | null;
  document_reference: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export type LicensePayload = Omit<LicenseRecord, 'id' | 'organization_id' | 'created_by' | 'updated_by' | 'display_status' | 'expiring_soon' | 'is_active' | 'created_at' | 'updated_at'>;

export const licenseService = {
  list: (params?: Record<string, string | boolean | undefined>) => api.get<LicenseRecord[]>('/licenses', { params }),
  get: (id: number) => api.get<LicenseRecord>(`/licenses/${id}`),
  create: (payload: LicensePayload) => api.post<LicenseRecord>('/licenses', payload),
  update: (id: number, payload: LicensePayload) => api.put<LicenseRecord>(`/licenses/${id}`, payload),
  setActive: (id: number, isActive: boolean) => api.patch<LicenseRecord>(`/licenses/${id}/active`, null, { params: { is_active: isActive } }),
  deactivate: (id: number) => api.delete<LicenseRecord>(`/licenses/${id}`),
};
