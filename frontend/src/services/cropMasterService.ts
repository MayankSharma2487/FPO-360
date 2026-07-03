import api from './api';

export const cropMasterService = {
  getCropMasters: () => api.get('/crop-masters/'),
  createCrop: (data: any) => api.post('/crop-masters/', data),
  updateCrop: (id: number, data: any) => api.put(`/crop-masters/${id}`, data),
  toggleStatus: (id: number, isActive: boolean) => 
    api.patch(`/crop-masters/${id}/status?is_active=${isActive}`),
};