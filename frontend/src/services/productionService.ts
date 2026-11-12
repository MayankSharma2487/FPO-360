import api from './api';

export type ProductionInput = {
  item_id: number;
  quantity: string;
  unit: string;
};

export type ProductionCreate = {
  production_date: string;
  finished_item_id: number;
  output_quantity: string;
  output_unit: string;
  inputs: ProductionInput[];
  wastage_quantity: string;
  wastage_unit: string;
  notes?: string;
};

export const productionService = {
  list: () => api.get<any[]>('/production/'),
  get: (id: number) => api.get<any>(`/production/${id}`),
  create: (payload: ProductionCreate, key: string) =>
    api.post<any>('/production/', payload, { headers: { 'Idempotency-Key': key } }),
};
