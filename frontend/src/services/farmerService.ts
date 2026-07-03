import api from './api';

export const farmerService = {
  getFarmers: () => api.get('/farmers/'),
  createFarmer: (data: any) => api.post('/farmers/', data),
  updateFarmer: (id: number, data: any) => api.put(`/farmers/${id}`, data),
  toggleStatus: (id: number, isActive: boolean) => 
    api.patch(`/farmers/${id}/status?is_active=${isActive}`),
};