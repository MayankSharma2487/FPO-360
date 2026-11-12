import React, { useEffect, useState } from 'react';
import { cropMasterService } from '../services/cropMasterService';

const TYPES = [
  ['AGRICULTURAL_COMMODITY', 'Agricultural commodity / crop'],
  ['PURCHASED_PRODUCT', 'Purchased resale product'],
  ['RAW_MATERIAL', 'Raw material'],
  ['PACKAGING_MATERIAL', 'Packaging material'],
  ['FINISHED_GOOD', 'Packed / manufactured finished good'],
];
const UNITS = ['KG', 'G', 'QUINTAL', 'TON', 'L', 'ML', 'PCS'];

interface Props { initialData?: any; onSubmit: (data: any) => Promise<void>; onCancel: () => void }

export const CropMasterForm: React.FC<Props> = ({ initialData, onSubmit, onCancel }) => {
  const [form, setForm] = useState({
    item_code: initialData?.item_code ?? initialData?.crop_code ?? '',
    item_name: initialData?.item_name ?? initialData?.crop_name ?? '',
    item_type: initialData?.item_type ?? 'AGRICULTURAL_COMMODITY',
    category: initialData?.category ?? initialData?.crop_category ?? '',
    base_unit: initialData?.base_unit ?? 'KG',
    description: initialData?.description ?? '',
  });
  const [loading, setLoading] = useState(false);
  const [generatedCode, setGeneratedCode] = useState(initialData?.item_code ?? initialData?.crop_code ?? '');
  const [codeLoading, setCodeLoading] = useState(!initialData?.id);
  const [error, setError] = useState<string | null>(null);
  const put = (field: string, value: string) => setForm(old => ({ ...old, [field]: value }));
  useEffect(() => {
    if (initialData?.id) return;
    let current = true;
    setCodeLoading(true);
    cropMasterService.getNextCode(form.item_type).then(response => {
      if (current) setGeneratedCode(response.data.item_code);
    }).catch((err: any) => {
      if (current) setError(err?.response?.data?.detail || 'Unable to load the generated item code');
    }).finally(() => { if (current) setCodeLoading(false); });
    return () => { current = false; };
  }, [form.item_type, initialData?.id]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError(null); setLoading(true);
    try {
      const { item_code: _displayOnlyCode, ...payload } = form;
      await onSubmit({ ...payload, category: form.category.trim() || null, description: form.description.trim() || null });
    }
    catch (err: any) { setError(err?.response?.data?.detail || err?.message || 'Failed to save item'); }
    finally { setLoading(false); }
  };
  return <form onSubmit={submit} className="form-grid">
    {error && <div className="form-error col-span-full">{error}</div>}
    <div className="form-group"><label className="form-label">{initialData?.id ? 'Item code' : 'Generated item code'}</label><input className="form-input" value={initialData?.item_code ?? initialData?.crop_code ?? (codeLoading ? 'Generating…' : generatedCode)} readOnly aria-readonly="true"/><small>{initialData?.id ? 'Item codes cannot be changed.' : 'Assigned by the system when you save. The preview may change if another item is created first.'}</small></div>
    <div className="form-group"><label className="form-label form-label-required">Item name</label><input className="form-input" value={form.item_name} onChange={e => put('item_name', e.target.value)} required minLength={2} maxLength={150}/></div>
    <div className="form-group"><label className="form-label form-label-required">Item type</label><select className="form-select" value={form.item_type} onChange={e => put('item_type', e.target.value)} disabled={!!initialData?.id}>{TYPES.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>{initialData?.id && <small>Type is fixed because it determines the generated item code.</small>}</div>
    <div className="form-group"><label className="form-label">Category</label><input className="form-input" value={form.category} onChange={e => put('category', e.target.value)} maxLength={100}/></div>
    <div className="form-group"><label className="form-label form-label-required">Base unit</label><select className="form-select" value={form.base_unit} onChange={e => put('base_unit', e.target.value)}>{UNITS.map(unit => <option key={unit} value={unit}>{unit}</option>)}</select>{form.item_type === 'AGRICULTURAL_COMMODITY' && <small>Crop transactions use KG as the stock base unit.</small>}</div>
    <div className="form-group"><label className="form-label">Description</label><textarea className="form-input" value={form.description} onChange={e => put('description', e.target.value)} maxLength={1000}/></div>
    <div className="form-grid--single"><div className="form-actions"><button type="button" className="btn btn-ghost" onClick={onCancel} disabled={loading}>Cancel</button><button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : initialData?.id ? 'Update Item' : 'Create Item'}</button></div></div>
  </form>;
};
