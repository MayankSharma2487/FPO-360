import api from './api';

export type ItemType =
  | 'AGRICULTURAL_COMMODITY'
  | 'PURCHASED_PRODUCT'
  | 'RAW_MATERIAL'
  | 'PACKAGING_MATERIAL'
  | 'FINISHED_GOOD';

export type BaseUnit = 'KG' | 'G' | 'QUINTAL' | 'TON' | 'L' | 'ML' | 'PCS';
export type DecimalValue = string;

export interface InventoryBalance {
  item_id: number;
  item_name: string;
  item_type: ItemType;
  base_unit: BaseUnit;
  total_in: DecimalValue;
  total_out: DecimalValue;
  current_balance: DecimalValue;
  crop_id?: number | null;
  crop_name?: string | null;
}

export interface InventoryLedgerEntry {
  id: number;
  organization_id: number;
  item_id: number;
  item_name?: string | null;
  item_type?: ItemType | null;
  base_unit?: BaseUnit | null;
  crop_id?: number | null;
  crop_name?: string | null;
  transaction_type: 'IN' | 'OUT';
  quantity: DecimalValue;
  reference_type: string;
  reference_id: number | null;
  idempotency_key?: string | null;
  reverses_id?: number | null;
  source_revision: number;
  remarks?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface InventoryAdjustPayload {
  item_id: number;
  transaction_type: 'IN' | 'OUT';
  quantity: DecimalValue;
  unit?: BaseUnit;
  remarks?: string;
}

export interface InventoryReconciliationEntry {
  organization_id: number;
  item_id: number;
  item_name: string;
  balance_quantity: DecimalValue;
  ledger_quantity: DecimalValue;
  difference: DecimalValue;
}

export const inventoryService = {
  getBalances: () => api.get<InventoryBalance[]>('/inventory/balances'),
  getLedgerEntries: () => api.get<InventoryLedgerEntry[]>('/inventory/ledger'),
  getLedger: (itemId: number) => api.get<InventoryLedgerEntry[]>(`/inventory/${itemId}/ledger`),
  getItemLedger: (itemId: number) => api.get<InventoryLedgerEntry[]>(`/inventory/items/${itemId}/ledger`),
  getReconciliation: () => api.get<InventoryReconciliationEntry[]>('/inventory/reconciliation'),
  adjustStock: (data: InventoryAdjustPayload, idempotencyKey: string) =>
    api.post<InventoryLedgerEntry>('/inventory/adjust', data, {
      headers: { 'Idempotency-Key': idempotencyKey },
    }),
};
