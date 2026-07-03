import api from './api';

export const shareholderService = {
  getShareholders: () => api.get('/shareholders/'),
  createShareholder: (data: any) => api.post('/shareholders/', data),
  updateShareholder: (id: number, data: any) => api.put(`/shareholders/${id}`, data),
  toggleStatus: (id: number, isActive: boolean) => 
    api.patch(`/shareholders/${id}/status?is_active=${isActive}`),
};