import { useState, useEffect } from 'react';
import { cropMasterService } from '../services/cropMasterService';
import { customerService } from '../services/salesService';
import { CustomerForm } from './CustomerForm';

interface SaleFormProps {
  initialData?: any;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export function SaleForm({ initialData, onSubmit, onCancel }: SaleFormProps) {
  const [customers, setCustomers] = useState<any[]>([]);
  const [crops, setCrops] = useState<any[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCustomerForm, setShowCustomerForm] = useState(false);

  /**
   * Reverse-convert the stored item-base quantity into the sale's display unit.
   */
  const getReverseConvertedQuantity = (storedQuantityInBase: number, unit: string, baseUnit = 'KG'): number => {
    const factors: Record<string, number> = { G: 0.001, KG: 1, QUINTAL: 100, TON: 1000, ML: 0.001, L: 1, PCS: 1 };
    return storedQuantityInBase * (factors[baseUnit] || 1) / (factors[unit] || 1);
  };

  const [formData, setFormData] = useState({
    sale_date: initialData?.sale_date
      ? String(initialData.sale_date).split('T')[0]
      : new Date().toISOString().split('T')[0],
    customer_id: initialData?.customer_id || '',
    crop_id: initialData?.crop_id || '',
    quantity: initialData?.quantity != null
      ? getReverseConvertedQuantity(Number(initialData.quantity), initialData.unit || 'KG', initialData.base_unit || 'KG').toString()
      : '',
    unit: initialData?.unit || 'KG',
    rate_per_unit: initialData?.rate_per_unit != null ? String(initialData.rate_per_unit) : '',
    total_amount: initialData?.total_amount != null ? String(initialData.total_amount) : '0',
    payment_status: initialData?.payment_status || 'Pending',
    remarks: initialData?.remarks || '',
  });

  const loadOptions = async () => {
    try {
      const [customerRes, cropRes] = await Promise.all([
        customerService.getActiveCustomers(),
        cropMasterService.getItems({ is_active: 'true' }),
      ]);
      setCustomers(customerRes.data || []);
      setCrops((cropRes.data || []).filter((item: any) => ['AGRICULTURAL_COMMODITY', 'FINISHED_GOOD'].includes(item.item_type)));
    } catch {
      setError('Failed to load form options');
    } finally {
      setLoadingOptions(false);
    }
  };

  useEffect(() => {
    loadOptions();
  }, []);

  // Auto-calculate total from DISPLAYED quantity × rate (not KG)
  useEffect(() => {
    const qty = parseFloat(formData.quantity) || 0;
    const rate = parseFloat(formData.rate_per_unit) || 0;
    const total = (qty * rate).toFixed(2);
    setFormData((prev) => ({ ...prev, total_amount: total }));
  }, [formData.quantity, formData.rate_per_unit]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (!formData.customer_id) {
        throw new Error('Customer is required');
      }
      if (!formData.crop_id) {
        throw new Error('Crop is required');
      }
      if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
        throw new Error('Quantity must be greater than 0');
      }
      if (!formData.rate_per_unit || parseFloat(formData.rate_per_unit) <= 0) {
        throw new Error('Rate must be greater than 0');
      }

      /**
       * Submit user-entered quantity + unit. Backend converts to KG.
       * Do NOT send total_amount or organization_id.
       */
      const submitData = {
        sale_date: formData.sale_date,
        customer_id: Number(formData.customer_id),
        crop_id: Number(formData.crop_id),
        quantity: parseFloat(formData.quantity),
        unit: formData.unit,
        rate_per_unit: parseFloat(formData.rate_per_unit),
        payment_status: formData.payment_status,
        remarks: formData.remarks || undefined,
      };

      await onSubmit(submitData);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : err?.message || 'Failed to save sale record'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleCustomerCreated = async (data: any) => {
    const res = await customerService.createCustomer(data);
    const created = res.data;
    setShowCustomerForm(false);
    await loadOptions();
    if (created?.id) {
      setFormData((prev) => ({ ...prev, customer_id: created.id }));
    }
  };

  if (loadingOptions) {
    return <div className="text-gray-400 text-sm">Loading form options...</div>;
  }

  return (
    <>
      <form onSubmit={handleSubmit} className="form-grid">
        {error && <div className="form-error col-span-full">{error}</div>}

        <div className="form-group">
          <label className="form-label form-label-required">Sale Date</label>
          <input
            type="date"
            className="form-input"
            value={formData.sale_date}
            onChange={(e) => setFormData({ ...formData, sale_date: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label form-label-required">Customer</label>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <select
              className="form-select"
              value={formData.customer_id}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  customer_id: e.target.value ? Number(e.target.value) : '',
                })
              }
              required
              style={{ flex: 1 }}
            >
              <option value="">Select Customer...</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.customer_name} ({c.customer_code})
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setShowCustomerForm(true)}
              title="New Customer"
              style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
            >
              + New
            </button>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label form-label-required">Crop or finished product</label>
          <select
            className="form-select"
            value={formData.crop_id}
              onChange={(e) => {
                const item = crops.find((candidate: any) => candidate.id === Number(e.target.value));
                setFormData({
                  ...formData,
                  crop_id: item?.id ?? '',
                  unit: item?.base_unit ?? 'KG',
                  quantity: '',
                });
              }}
            required
          >
            <option value="">Select crop or finished product...</option>
            {crops
              .filter((c) => c.is_active !== false)
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.item_name} ({c.item_code}) · {c.item_type === 'FINISHED_GOOD' ? 'Finished good' : 'Agricultural commodity'}
                </option>
              ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label form-label-required">Quantity</label>
          <input
            type="number"
            step="0.000001"
            className="form-input"
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
            placeholder="0.00"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label form-label-required">Unit</label>
          <select
            className="form-select"
            value={formData.unit}
            onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
            required
          >
            {(crops.find((item: any) => item.id === Number(formData.crop_id))?.base_unit === 'PCS'
              ? ['PCS']
              : ['G', 'KG', 'QUINTAL', 'TON'].includes(crops.find((item: any) => item.id === Number(formData.crop_id))?.base_unit)
                ? ['G', 'KG', 'QUINTAL', 'TON']
                : ['ML', 'L']
            ).map(unit => <option key={unit} value={unit}>{unit}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label form-label-required">Rate per Unit (₹)</label>
          <input
            type="number"
            step="0.01"
            className="form-input"
            value={formData.rate_per_unit}
            onChange={(e) => setFormData({ ...formData, rate_per_unit: e.target.value })}
            placeholder="0.00"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Total Amount (₹)</label>
          <input
            type="text"
            className="form-input"
            value={formData.total_amount}
            readOnly
            placeholder="Auto-calculated"
          />
          <span className="form-hint">
            {parseFloat(formData.quantity) || 0} × ₹{parseFloat(formData.rate_per_unit) || 0}
          </span>
        </div>

        <div className="form-group">
          <label className="form-label form-label-required">Payment Status</label>
          <select
            className="form-select"
            value={formData.payment_status}
            onChange={(e) => setFormData({ ...formData, payment_status: e.target.value })}
            required
          >
            <option value="Pending">Pending</option>
            <option value="Paid">Paid</option>
          </select>
        </div>

        <div className="form-group form-grid--single">
          <label className="form-label">Remarks</label>
          <textarea
            className="form-textarea"
            value={formData.remarks}
            onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
            placeholder="Any additional notes..."
          />
        </div>

        <div className="form-grid--single">
          <div className="form-actions">
            <button type="button" className="btn btn-ghost" onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Processing...' : initialData?.id ? 'Update' : 'Create'}
            </button>
          </div>
        </div>
      </form>

      {/* Nested customer create modal */}
      {showCustomerForm && (
        <div className="modal-overlay" onClick={() => setShowCustomerForm(false)} style={{ zIndex: 10000 }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="modal-title">New Customer</div>
                <p className="modal-subtitle">Create a customer for this sale</p>
              </div>
              <button className="modal-close" onClick={() => setShowCustomerForm(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <CustomerForm
                onSubmit={handleCustomerCreated}
                onCancel={() => setShowCustomerForm(false)}
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
