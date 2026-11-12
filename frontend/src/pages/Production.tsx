import { useEffect, useMemo, useRef, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { cropMasterService } from '../services/cropMasterService';
import { productionService } from '../services/productionService';
import { getApiErrorMessage } from '../utils/errors';
import { useAuth } from '../context/AuthContext';
import { compatibleUnits } from '../utils/productionUnits.js';

type Item = { id: number; item_code: string; item_name: string; item_type: string; base_unit: string; is_active: boolean };
type InputRow = { item_id: number | ''; quantity: string; unit: string };
function newKey() {
  return globalThis.crypto?.randomUUID?.() ?? `production-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function Production() {
  const { user } = useAuth();
  const canPost = ['FPO Admin', 'Manager'].includes(user?.role?.name || '');
  const [items, setItems] = useState<Item[]>([]);
  const [records, setRecords] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const keyByPayload = useRef(new Map<string, string>());
  const [form, setForm] = useState({
    production_date: new Date().toISOString().slice(0, 10), finished_item_id: '' as number | '',
    output_quantity: '', output_unit: 'KG', wastage_quantity: '0', wastage_unit: 'KG', notes: '',
    inputs: [{ item_id: '' as number | '', quantity: '', unit: 'KG' }] as InputRow[],
  });

  const load = async () => {
    setLoading(true);
    try {
      const [itemResponse, productionResponse] = await Promise.all([
        cropMasterService.getItems({ is_active: 'true' }), productionService.list(),
      ]);
      setItems(itemResponse.data);
      setRecords(productionResponse.data);
      setError(null);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load Production & Packing'));
    } finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  const finishedGoods = useMemo(() => items.filter(i => i.item_type === 'FINISHED_GOOD'), [items]);
  const rawMaterials = useMemo(() => items.filter(i =>['RAW_MATERIAL', 'AGRICULTURAL_COMMODITY'].includes(i.item_type)),[items]);
  const packaging = useMemo(() => items.filter(i => i.item_type === 'PACKAGING_MATERIAL'), [items]);
  const selectedFinished = finishedGoods.find(i => i.id === form.finished_item_id);

  const begin = () => {
    const finished = finishedGoods[0];
    const raw = rawMaterials[0];
    setForm({
      production_date: new Date().toISOString().slice(0, 10), finished_item_id: finished?.id ?? '',
      output_quantity: '', output_unit: finished?.base_unit ?? 'KG', wastage_quantity: '0',
      wastage_unit: finished?.base_unit ?? 'KG', notes: '',
      inputs: raw ? [{ item_id: raw.id, quantity: '', unit: raw.base_unit }] : [{ item_id: '', quantity: '', unit: 'KG' }],
    });
    setFormError(null);
    setShowForm(true);
  };

  const updateInput = (index: number, changes: Partial<InputRow>) => setForm(current => ({
    ...current,
    inputs: current.inputs.map((line, row) => row === index ? { ...line, ...changes } : line),
  }));

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);
    if (!form.finished_item_id || form.inputs.some(line => !line.item_id || !line.quantity || Number(line.quantity) <= 0) || !form.output_quantity || Number(form.output_quantity) <= 0) {
      setFormError('Choose a finished product and valid positive quantities for output and each input.'); return;
    }
    if (new Set(form.inputs.map(line => line.item_id)).size !== form.inputs.length) {
      setFormError('Use one row per input item.'); return;
    }
    const payload = {
      production_date: form.production_date,
      finished_item_id: Number(form.finished_item_id),
      output_quantity: form.output_quantity,
      output_unit: form.output_unit,
      inputs: form.inputs.map(line => ({ item_id: Number(line.item_id), quantity: line.quantity, unit: line.unit })),
      wastage_quantity: form.wastage_quantity || '0', wastage_unit: form.wastage_unit,
      notes: form.notes.trim() || undefined,
    };
    const signature = JSON.stringify(payload);
    const key = keyByPayload.current.get(signature) ?? newKey();
    keyByPayload.current.set(signature, key);
    setSaving(true);
    try {
      const response = await productionService.create(payload, key);
      setRecords(current => [response.data, ...current.filter(row => row.id !== response.data.id)]);
      setSelected(response.data);
      setShowForm(false);
      await load();
    } catch (err) { setFormError(getApiErrorMessage(err, 'Production posting failed')); }
    finally { setSaving(false); }
  };

  const openRecord = async (id: number) => {
    try { setSelected((await productionService.get(id)).data); }
    catch (err) { setError(getApiErrorMessage(err, 'Failed to load production details')); }
  };

  return <RoleGuard allowedRoles={['FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
    <div className="page-wrapper">
      <div className="page-header">
        <div><h2 className="page-title">Production &amp; Packing</h2><p className="page-subtitle">Post material consumption and finished goods through Inventory</p></div>
        {canPost && <button className="btn btn-primary" onClick={begin} disabled={!finishedGoods.length || !rawMaterials.length}>New production</button>}
      </div>
      {error && <div className="error-banner" role="alert">{error}</div>}
      {loading ? <div className="table-skeleton"><div className="skeleton-row" /><div className="skeleton-row" /></div> : records.length === 0 ?
        <div className="empty-state">No production records yet.</div> :
        <div className="table-container"><table className="data-table"><thead><tr><th>Reference</th><th>Date</th><th>Finished product</th><th>Output</th><th>Input consumption</th><th>Wastage</th><th>Status</th></tr></thead><tbody>
          {records.map(record => <tr key={record.id} onClick={() => void openRecord(record.id)} style={{ cursor: 'pointer' }}>
            <td>{record.reference_no}</td><td>{record.production_date}</td><td>{record.finished_item_name}</td>
            <td>{record.output_quantity} {record.output_unit}</td>
            <td>{record.total_input_consumption.map((v: any) => `${v.quantity} ${v.unit}`).join(', ')}</td>
            <td>{record.wastage_quantity} {record.wastage_unit}</td><td>{record.status}</td>
          </tr>)}
        </tbody></table></div>}

      {selected && <div className="stat-card" style={{ marginTop: 20 }}>
        <div className="page-header"><div><h3>{selected.reference_no} · {selected.finished_item_name}</h3><p>{selected.production_date} · {selected.status}</p></div><button className="btn btn-secondary" onClick={() => setSelected(null)}>Close</button></div>
        <p>Output: {selected.output_quantity} {selected.output_unit} ({selected.output_base_quantity} {selected.base_unit})</p>
        <p>Wastage: {selected.wastage_quantity} {selected.wastage_unit} ({selected.wastage_base_quantity} {selected.base_unit})</p>
        <h4>Consumed materials</h4><ul>{selected.inputs.map((line: any) => <li key={line.id}>{line.item_name} ({line.item_type}): {line.quantity} {line.unit} · stock movement {line.base_quantity} {line.base_unit}</li>)}</ul>
        {selected.notes && <p>{selected.notes}</p>}
      </div>}

      {showForm && <div className="modal-overlay" onMouseDown={() => !saving && setShowForm(false)}>
        <form className="modal-card modal-card--lg" onSubmit={submit} onMouseDown={event => event.stopPropagation()}>
          <h3>Post production</h3>
          {formError && <div className="form-error" role="alert">{formError}</div>}
          <div className="form-grid">
            <label><span className="form-label">Production date</span><input className="form-input" type="date" required value={form.production_date} onChange={e => setForm({ ...form, production_date: e.target.value })} /></label>
            <label><span className="form-label">Finished product</span><select className="form-select" required value={form.finished_item_id} onChange={e => { const item = finishedGoods.find(i => i.id === Number(e.target.value)); setForm({ ...form, finished_item_id: item?.id ?? '', output_unit: item?.base_unit ?? 'KG', wastage_unit: item?.base_unit ?? 'KG' }); }}><option value="">Select finished product</option>{finishedGoods.map(i => <option key={i.id} value={i.id}>{i.item_name} ({i.item_code}) · {i.base_unit}</option>)}</select></label>
            <label><span className="form-label">Output quantity</span><input className="form-input" type="number" min="0.000001" step="0.000001" required value={form.output_quantity} onChange={e => setForm({ ...form, output_quantity: e.target.value })} /></label>
            <label><span className="form-label">Output unit</span><select className="form-select" value={form.output_unit} onChange={e => setForm({ ...form, output_unit: e.target.value })}>{compatibleUnits(selectedFinished?.base_unit ?? 'KG').map(u => <option key={u}>{u}</option>)}</select></label>
          </div>
          <h4>Raw materials</h4>
          {form.inputs.map((line, index) => ({ line, index }))
            .filter(({ line }) => line.item_id === '' || rawMaterials.some(item => item.id === line.item_id))
            .map(({ line, index }) => <div className="form-grid" key={index}>
            <label><span className="form-label">Material</span><select className="form-select" value={line.item_id} onChange={e => { const item = rawMaterials.find(i => i.id === Number(e.target.value)); updateInput(index, { item_id: item?.id ?? '', unit: item?.base_unit ?? 'KG' }); }}><option value="">Select raw material</option>{rawMaterials.map(i => <option key={i.id} value={i.id}>{i.item_name} ({i.item_code})</option>)}</select></label>
            <label><span className="form-label">Quantity</span><input className="form-input" type="number" min="0.000001" step="0.000001" value={line.quantity} onChange={e => updateInput(index, { quantity: e.target.value })} /></label>
            <label><span className="form-label">Unit</span><select className="form-select" value={line.unit} onChange={e => updateInput(index, { unit: e.target.value })}>{compatibleUnits(rawMaterials.find(i => i.id === line.item_id)?.base_unit ?? 'KG').map(u => <option key={u}>{u}</option>)}</select></label>
            <button type="button" className="btn btn-secondary" onClick={() => setForm({ ...form, inputs: form.inputs.filter((_, row) => row !== index) })} disabled={form.inputs.length === 1}>Remove</button>
          </div>)}
          <button type="button" className="btn btn-secondary" onClick={() => { const item = rawMaterials[0]; setForm({ ...form, inputs: [...form.inputs, { item_id: item?.id ?? '', quantity: '', unit: item?.base_unit ?? 'KG' }] }); }} disabled={!rawMaterials.length}>Add material</button>
          <h4>Packaging materials</h4>
          {packaging.length === 0 ? <p>No active packaging materials in the catalogue.</p> : <div className="form-grid">
            {packaging.map((item, index) => <label key={item.id}><span className="form-label">{item.item_name} ({item.base_unit})</span><input className="form-input" type="number" min="0" step="0.000001" value={form.inputs.find(line => line.item_id === item.id)?.quantity ?? ''} onChange={e => {
              const existing = form.inputs.findIndex(line => line.item_id === item.id);
              if (existing >= 0 && e.target.value) updateInput(existing, { quantity: e.target.value });
              else if (existing >= 0) setForm({ ...form, inputs: form.inputs.filter((_, row) => row !== existing) });
              else if (e.target.value) setForm({ ...form, inputs: [...form.inputs, { item_id: item.id, quantity: e.target.value, unit: item.base_unit }] });
            }} placeholder="0" /></label>)}
          </div>}
          <div className="form-grid">
            <label><span className="form-label">Wastage quantity</span><input className="form-input" type="number" min="0" step="0.000001" value={form.wastage_quantity} onChange={e => setForm({ ...form, wastage_quantity: e.target.value })} /></label>
            <label><span className="form-label">Wastage unit</span><select className="form-select" value={form.wastage_unit} onChange={e => setForm({ ...form, wastage_unit: e.target.value })}>{compatibleUnits(selectedFinished?.base_unit ?? 'KG').map(u => <option key={u}>{u}</option>)}</select></label>
          </div>
          <label><span className="form-label">Notes</span><textarea className="form-input" maxLength={1000} value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></label>
          <p className="page-subtitle">Posting consumes each listed input and adds finished output atomically. Wastage is recorded separately and does not add stock.</p>
          <div className="form-actions"><button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)} disabled={saving}>Cancel</button><button className="btn btn-primary" type="submit" disabled={saving}>{saving ? 'Posting…' : 'Post production'}</button></div>
        </form>
      </div>}
    </div>
  </RoleGuard>;
}
