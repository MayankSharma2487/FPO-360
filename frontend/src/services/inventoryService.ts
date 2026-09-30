import api from './api';

export interface InventoryBalance {
  crop_id: number;
  crop_name: string | null;
  total_in: number;
  total_out: number;
  current_balance: number;
}

export interface InventoryLedgerEntry {
  id: number;
  organization_id: number;
  crop_id: number;
  crop_name?: string | null;
  transaction_type: 'IN' | 'OUT';
  quantity: number;
  reference_type: 'PROCUREMENT' | 'MANUAL';
  reference_id: number | null;
  remarks?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface InventoryAdjustPayload {
  crop_id: number;
  transaction_type: 'IN' | 'OUT';
  quantity: number;
  remarks?: string;
}

export const inventoryService = {
  getBalances: () => api.get<InventoryBalance[]>('/inventory/balances'),
  getLedger: (cropId: number) =>
    api.get<InventoryLedgerEntry[]>(`/inventory/${cropId}/ledger`),
  adjustStock: (data: InventoryAdjustPayload) =>
    api.post<InventoryLedgerEntry>('/inventory/adjust', data),
};