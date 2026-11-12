import api from './api';

export const procurementService = {
  getProcurements: (params?: any) => api.get('/procurements/', { params }),

  getProcurementById: async (id: number) => {
    const res = await api.get('/procurements/');
    const record = res.data.find((p: any) => p.id === Number(id));
    if (!record) throw new Error("Procurement not found");
    return { data: record };
  },

  createProcurement: (data: any, idempotencyKey: string) => api.post('/procurements/', data, {
    headers: { 'Idempotency-Key': idempotencyKey },
  }),
  
  updateProcurement: (id: number, data: any) => api.put(`/procurements/${id}`, data),
  
  toggleStatus: (id: number, isActive: boolean) =>
    api.patch(`/procurements/${id}/status?is_active=${isActive}`),
};
