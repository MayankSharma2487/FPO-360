import { useEffect, useMemo, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { CropMasterForm } from '../components/CropMasterForm';
import { cropMasterService } from '../services/cropMasterService';
import { ActionsMenu } from '../components/ActionsMenu';
import { useAuth } from '../context/AuthContext';

const TYPE_LABELS: Record<string, string> = {
  AGRICULTURAL_COMMODITY: 'Agricultural commodity / crop', PURCHASED_PRODUCT: 'Purchased resale product',
  RAW_MATERIAL: 'Raw material', PACKAGING_MATERIAL: 'Packaging material', FINISHED_GOOD: 'Finished good',
};
interface Item { id: number; item_code: string; item_name: string; item_type: string; category?: string; base_unit: string; description?: string; organization_id?: number | null; is_active: boolean; created_at: string; updated_at?: string }

export default function CropMasters() {
  const { user } = useAuth();
  const canWrite = ['Super Admin', 'FPO Admin'].includes(user?.role?.name || '');
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [active, setActive] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Partial<Item> | null>(null);
  const load = async () => { setLoading(true); try { const res = await cropMasterService.getItems({ search: search || undefined, item_type: type || undefined, is_active: active === '' ? undefined : active }); setItems(res.data); setError(null); } catch (err: any) { setError(err?.response?.data?.detail || 'Failed to load items'); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, [search, type, active]);
  const activeCount = useMemo(() => items.filter(i => i.is_active).length, [items]);
  const toggle = async (item: Item) => { try { await cropMasterService.toggleStatus(item.id, !item.is_active); setSuccess(`Item ${item.is_active ? 'deactivated' : 'activated'} successfully`); void load(); } catch (err: any) { setError(err?.response?.data?.detail || 'Failed to update item status'); } };
  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
    <div className="page-wrapper">
      <div className="page-header"><div><h2 className="page-title">Item Catalogue</h2><p className="page-subtitle">Manage shared crops and organization items</p></div><div className="flex items-center gap-4"><div className="page-count-badge">{activeCount} of {items.length} active</div>{canWrite && <button onClick={() => { setEditing(null); setShowForm(true); }} className="btn btn-primary">Add Item</button>}</div></div>
      <div className="table-toolbar"><input className="search-input" placeholder="Search items by name or code..." value={search} onChange={e => setSearch(e.target.value)}/><select className="form-select" value={type} onChange={e => setType(e.target.value)}><option value="">All item types</option>{Object.entries(TYPE_LABELS).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select><select className="form-select" value={active} onChange={e => setActive(e.target.value)}><option value="">All statuses</option><option value="true">Active</option><option value="false">Inactive</option></select></div>
      {error && <div className="error-banner">{error}</div>}{success && <div className="success-banner">{success}</div>}
      {loading ? <div className="table-skeleton">{Array.from({length:5}).map((_,i)=><div key={i} className="skeleton-row"/>)}</div> : <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>#</th><th>Item</th><th>Code</th><th>Type</th><th>Category</th><th>Base unit</th><th>Scope</th><th>Status</th>{canWrite && <th className="text-right">Actions</th>}</tr></thead><tbody>{items.length === 0 ? <tr><td colSpan={canWrite ? 9 : 8} className="empty-row">No items match these filters.</td></tr> : items.map((item,index)=><tr key={item.id}><td className="row-num">{index+1}</td><td className="primary-cell">{item.item_name}</td><td><span className="mono-tag">{item.item_code}</span></td><td>{TYPE_LABELS[item.item_type] || item.item_type}</td><td>{item.category || '—'}</td><td>{item.base_unit}</td><td>{item.organization_id == null ? 'Shared' : 'Organization'}</td><td><span className={`status-pill ${item.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>{item.is_active ? 'Active' : 'Inactive'}</span></td>{canWrite && <td className="text-right"><ActionsMenu actions={[{label:'Edit',onClick:()=>{setEditing(item);setShowForm(true);}}, {label:item.is_active?'Deactivate':'Activate',variant:item.is_active?'danger':'success',onClick:()=>void toggle(item)}]}/></td>}</tr>)}</tbody></table></div></div>}
      {showForm && <div className="modal-overlay" onClick={() => setShowForm(false)}><div className="modal-card" onClick={e => e.stopPropagation()}><div className="modal-header"><div><div className="modal-title">{editing?.id ? 'Edit Item' : 'Add Item'}</div><p className="modal-subtitle">Catalogue items are maintained within the existing crop master.</p></div><button className="modal-close" onClick={() => setShowForm(false)}>×</button></div><div className="modal-body"><CropMasterForm initialData={editing} onCancel={() => setShowForm(false)} onSubmit={async data => { if (editing?.id) await cropMasterService.updateItem(editing.id, data); else await cropMasterService.createItem(data); setSuccess(`Item ${editing?.id ? 'updated' : 'created'} successfully`); setShowForm(false); void load(); }}/></div></div></div>}
    </div>
  </RoleGuard>;
}
