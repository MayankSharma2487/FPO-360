import api from './api';

export const paymentService = {
  getPayments: () => api.get('/payments/'),
  getPaymentById: (id: number) => api.get(`/payments/${id}`),
  createPayment: (data: any) => api.post('/payments/', data),
  updatePayment: (id: number, data: any) => api.put(`/payments/${id}`, data),
  toggleStatus: (id: number, isActive: boolean) => api.patch(`/payments/${id}/status?is_active=${isActive}`)
};