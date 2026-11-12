import api from './api';

export interface OrganizationSettings {
  id: number;
  organization_id: number;
  logo_url: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
}

export type OrganizationSettingsPayload = Omit<OrganizationSettings, 'id' | 'organization_id'>;

export const organizationSettingsService = {
  get: (organizationId: number) =>
    api.get<OrganizationSettings>(`/organizations/${organizationId}/settings`),
  save: (organizationId: number, payload: OrganizationSettingsPayload) =>
    api.put<OrganizationSettings>(`/organizations/${organizationId}/settings`, payload),
};
