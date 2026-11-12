import api from './api';

export const cropMasterService = {
  // Existing transaction forms intentionally remain crop-only.
  getCropMasters: () => api.get('/crop-masters/'),
  getItems: (params?: Record<string, string | undefined>) => api.get('/items/', { params }),
  getNextCode: (itemType: string) => api.get('/items/next-code', { params: { item_type: itemType } }),
  createItem: (data: any) => api.post('/items/', data),
  updateItem: (id: number, data: any) => api.put(`/items/${id}`, data),
  toggleStatus: (id: number, isActive: boolean) => 
    api.patch(`/items/${id}/status?is_active=${isActive}`),
};
