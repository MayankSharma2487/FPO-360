import api from './api';

export const farmerCropService = {
  getFarmerCrops: () => api.get('/farmer-crops/'),

  createFarmerCrop: (data: any) => api.post('/farmer-crops/', data),

  updateFarmerCrop: (id: number, data: any) => api.put(`/farmer-crops/${id}`, data),

  toggleStatus: (id: number, isActive: boolean) =>
    api.patch(`/farmer-crops/${id}/status?is_active=${isActive}`),
};