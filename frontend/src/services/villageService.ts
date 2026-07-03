import api from './api';

export const villageService = {
  getVillages: () => api.get('/villages/'),
  createVillage: (data: any) => api.post('/villages/', data),
  updateVillage: (id: number, data: any) => api.put(`/villages/${id}`, data),
  toggleStatus: (id: number, isActive: boolean) => 
    api.patch(`/villages/${id}/status?is_active=${isActive}`),
};