import api from './api';

export const salesService = {
  getSales: () => api.get('/sales/'),

  getSaleById: (id: number) => api.get(`/sales/${id}`),

  createSale: (data: any) => api.post('/sales/', data),

  updateSale: (id: number, data: any) => api.put(`/sales/${id}`, data),

  toggleStatus: (id: number, isActive: boolean) =>
    api.patch(`/sales/${id}/status?is_active=${isActive}`),
};

export const customerService = {
  getCustomers: () => api.get('/customers/'),

  getActiveCustomers: () => api.get('/customers/active'),

  createCustomer: (data: any) => api.post('/customers/', data),

  updateCustomer: (id: number, data: any) => api.put(`/customers/${id}`, data),
};
