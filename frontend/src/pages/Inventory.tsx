import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { ActionsMenu } from '../components/ActionsMenu';
import { inventoryService, InventoryBalance, BaseUnit, ItemType, DecimalValue } from '../services/inventoryService';
import { cropMasterService } from '../services/cropMasterService';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage } from '../utils/errors';
import { hasPositiveStock } from '../utils/inventoryStock';

interface ItemOption {
  id: number;
  item_code: string;
  item_name: string;
  item_type: ItemType;
  base_unit: BaseUnit;
  organization_id?: number | null;
  is_active: boolean;
}

const TYPE_NAMES: Record<ItemType, string> = {
  AGRICULTURAL_COMMODITY: 'Agricultural commodity',
  PURCHASED_PRODUCT: 'Purchased product',
  RAW_MATERIAL: 'Raw material',
  PACKAGING_MATERIAL: 'Packaging material',
  FINISHED_GOOD: 'Finished good',
};

const MASS_UNITS: BaseUnit[] = ['G', 'KG', 'QUINTAL', 'TON'];
const VOLUME_UNITS: BaseUnit[] = ['ML', 'L'];

function unitsFor(base: BaseUnit): BaseUnit[] {
  if (MASS_UNITS.includes(base)) return MASS_UNITS;
  if (VOLUME_UNITS.includes(base)) return VOLUME_UNITS;
  return ['PCS'];
}

function formatQty(value: DecimalValue, unit: BaseUnit): string {
  const [integerPart, fractionalPart = ''] = String(value || '0').split('.');
  const groupedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const trimmedFraction = fractionalPart.replace(/0+$/, '');
  return `${groupedInteger}${trimmedFraction ? `.${trimmedFraction}` : ''} ${unit}`;
}

function newRequestKey(): string {
  return globalThis.crypto?.randomUUID?.() ?? `inventory-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function Inventory() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const canAdjust = ['FPO Admin', 'Manager'].includes(user?.role?.name || '');
  const [balances, setBalances] = useState<InventoryBalance[]>([]);
  const [items, setItems] = useState<ItemOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [itemId, setItemId] = useState<number | ''>('');
  const [direction, setDirection] = useState<'IN' | 'OUT'>('IN');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState<BaseUnit>('KG');
  const [remarks, setRemarks] = useState('');
  const [requestKey, setRequestKey] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [balanceResponse, itemResponse] = await Promise.all([
        inventoryService.getBalances(),
        cropMasterService.getItems({ is_active: 'true' }),
      ]);
      setBalances(balanceResponse.data);
      setItems(itemResponse.data);
      setError(null);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load inventory'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadAll(); }, []);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return balances;
    return balances.filter(item =>
      item.item_name.toLowerCase().includes(term) ||
      String(item.item_id).includes(term) ||
      item.item_type.toLowerCase().includes(term)
    );
  }, [balances, search]);

  const openForm = () => {
    const first = items[0];
    setItemId(first?.id ?? '');
    setUnit(first?.base_unit ?? 'KG');
    setDirection('IN');
    setQuantity('');
    setRemarks('');
    setRequestKey(newRequestKey());
    setFormError(null);
    setShowForm(true);
  };

  const selectedItem = items.find(item => item.id === itemId);

  const submitForm = async () => {
    setFormError(null);
    if (!itemId) { setFormError('Select an item'); return; }
    if (!/^\d+(?:\.\d{1,6})?$/.test(quantity) || !/[1-9]/.test(quantity)) {
      setFormError('Enter a positive quantity with at most 6 decimal places'); return;
    }
    const fractionalPart = quantity.split('.')[1] ?? '';
    if (unit === 'PCS' && /[1-9]/.test(fractionalPart)) {
      setFormError('PCS quantities must be whole numbers'); return;
    }
    setSubmitting(true);
    try {
      await inventoryService.adjustStock({
        item_id: Number(itemId), transaction_type: direction, quantity,
        unit, remarks: remarks.trim() || undefined,
      }, requestKey);
      setSuccess('Inventory movement posted successfully');
      setShowForm(false);
      void loadAll();
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'Failed to post inventory movement'));
    } finally {
      setSubmitting(false);
    }
  };

  const itemCount = balances.filter(row => hasPositiveStock(row.current_balance)).length;

  return (
    <RoleGuard allowedRoles={['FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Inventory</h2>
            <p className="page-subtitle">Current stock by catalogue item</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">{itemCount} item{itemCount === 1 ? '' : 's'} in stock</div>
            {canAdjust && <button onClick={openForm} className="btn btn-primary">Manual movement</button>}
          </div>
        </div>

        {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
        {success && <div className="success-banner" style={{ marginBottom: 16 }}>{success}</div>}

        <div className="table-toolbar" style={{ marginBottom: 12 }}>
          <input
            type="search" className="search-input" placeholder="Search by item name, ID or type..."
            value={search} onChange={event => setSearch(event.target.value)}
          />
        </div>

        {loading ? <div className="table-skeleton">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton-row" />)}</div> : (
          <div className="table-wrapper"><div className="table-scroll"><table className="data-table">
            <thead><tr><th>#</th><th>Item</th><th>Type</th><th>Unit</th><th>Total IN</th><th>Total OUT</th><th>On hand</th><th className="text-right">Actions</th></tr></thead>
            <tbody>{filtered.length === 0 ? <tr><td colSpan={8} className="empty-row">{search ? 'No matching inventory items' : 'No stock movements recorded yet'}</td></tr> : filtered.map((row, index) => (
              <tr key={row.item_id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/inventory/${row.item_id}`)}>
                <td className="row-num">{index + 1}</td>
                <td><span className="primary-cell">{row.item_name}</span><div className="text-sm text-gray-400">Item #{row.item_id}</div></td>
                <td>{TYPE_NAMES[row.item_type]}</td><td>{row.base_unit}</td>
                <td>{formatQty(row.total_in, row.base_unit)}</td><td>{formatQty(row.total_out, row.base_unit)}</td>
                <td><strong>{formatQty(row.current_balance, row.base_unit)}</strong></td>
                <td className="text-right" onClick={event => event.stopPropagation()}><ActionsMenu actions={[{ label: 'View ledger', onClick: () => navigate(`/inventory/${row.item_id}`) }]} /></td>
              </tr>
            ))}</tbody>
          </table></div></div>
        )}

        {showForm && <div className="modal-overlay" onClick={() => !submitting && setShowForm(false)}>
          <div className="modal-card" onClick={event => event.stopPropagation()} style={{ maxWidth: 520 }}>
            <div className="modal-header"><div><div className="modal-title">Manual inventory movement</div><p className="modal-subtitle">Posted movements are retained in the ledger.</p></div><button className="modal-close" onClick={() => !submitting && setShowForm(false)}>×</button></div>
            <div className="modal-body"><div style={{ display: 'grid', gap: 14 }}>
              <label><span className="form-label">Item</span><select className="form-select" value={itemId} onChange={event => { const id = Number(event.target.value); setItemId(id || ''); setUnit(items.find(item => item.id === id)?.base_unit ?? 'KG'); }}>
                <option value="">Select item</option>{items.map(item => <option key={item.id} value={item.id}>{item.item_name} · {TYPE_NAMES[item.item_type]} · {item.item_code}</option>)}
              </select></label>
              {selectedItem && <div className="text-sm text-gray-400">Base unit: {selectedItem.base_unit}</div>}
              <label><span className="form-label">Movement</span><select className="form-select" value={direction} onChange={event => setDirection(event.target.value as 'IN' | 'OUT')}><option value="IN">IN · opening stock, receive or correct upward</option><option value="OUT">OUT · issue or correct downward</option></select></label>
              <div className="form-grid"><label><span className="form-label">Quantity</span><input className="form-input" type="text" inputMode="decimal" value={quantity} onChange={event => setQuantity(event.target.value)} /></label>
                <label><span className="form-label">Entry unit</span><select className="form-select" value={unit} onChange={event => setUnit(event.target.value as BaseUnit)} disabled={!selectedItem}>{selectedItem && unitsFor(selectedItem.base_unit).map(value => <option key={value} value={value}>{value}</option>)}</select></label></div>
              <label><span className="form-label">Reason / remarks</span><input className="form-input" value={remarks} maxLength={500} onChange={event => setRemarks(event.target.value)} /></label>
              {formError && <div className="error-banner">{formError}</div>}
            </div></div>
            <div className="modal-footer"><button className="btn btn-secondary" onClick={() => setShowForm(false)} disabled={submitting}>Cancel</button><button className="btn btn-primary" onClick={submitForm} disabled={submitting || !selectedItem}>{submitting ? 'Saving...' : 'Post movement'}</button></div>
          </div>
        </div>}
      </div>
    </RoleGuard>
  );
}
