import api from './api';

export const procurementService = {
  getProcurements: (params?: any) => api.get('/procurements/', { params }),
  
  createProcurement: (data: any) => api.post('/procurements/', data),
  
  updateProcurement: (id: number, data: any) => api.put(`/procurements/${id}`, data),
  
  toggleStatus: (id: number, isActive: boolean) =>
    api.patch(`/procurements/${id}/status?is_active=${isActive}`),
};