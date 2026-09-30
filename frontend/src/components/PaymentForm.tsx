import { useState, useEffect } from 'react';
import { procurementService } from '../services/procurementService';

interface PaymentFormProps {
  initialData?: any;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}

export function PaymentForm({ initialData, onSubmit, onCancel }: PaymentFormProps) {
  const [procurements, setProcurements] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    procurement_id: initialData?.procurement_id || '',
    farmer_id: initialData?.farmer_id || '',
    amount: initialData?.amount || '',
    payment_date: initialData?.payment_date ? new Date(initialData.payment_date).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
    payment_method: initialData?.payment_method || 'Bank Transfer',
    reference_no: initialData?.reference_no || '',
    status: initialData?.status || 'Pending',
    remarks: initialData?.remarks || ''
  });

  useEffect(() => {
    // Fetch the full list (unfiltered) so an existing payment being edited can
    // still resolve/display its linked procurement even if that procurement
    // has since been disabled. The dropdown itself only offers active ones.
    procurementService.getProcurements().then(res => {
      setProcurements(res.data);
    });
  }, []);

  const selectedProcurement = procurements.find(p => p.id === Number(formData.procurement_id));

  const selectableProcurements = procurements.filter(
    (p: any) => p.is_active || p.id === Number(formData.procurement_id)
  );

  const handleProcurementChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const procId = Number(e.target.value);
    const selectedProc = procurements.find(p => p.id === procId);
    setError(null);

    if (selectedProc) {
      setFormData(prev => ({
        ...prev,
        procurement_id: procId,
        farmer_id: selectedProc.farmer_id,
        amount: selectedProc.total_amount || ''
      }));
    } else {
      setFormData(prev => ({ ...prev, procurement_id: '', farmer_id: '', amount: '' }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.procurement_id) {
      setError('Please select a procurement record.');
      return;
    }

    const amt = Number(formData.amount);
    if (!amt || amt <= 0) {
      setError('Payment amount must be greater than 0.');
      return;
    }

    if (selectedProcurement && amt > Number(selectedProcurement.total_amount)) {
      setError(`Payment amount cannot exceed the procurement total of Rs. ${selectedProcurement.total_amount}.`);
      return;
    }

    onSubmit({
      ...formData,
      amount: amt,
      farmer_id: Number(formData.farmer_id),
      procurement_id: Number(formData.procurement_id)
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}

      <div className="form-group" style={{ marginBottom: '14px' }}>
        <label className="form-label">Procurement Record <span className="form-label-required"></span></label>
        <select 
          className="form-select" 
          value={formData.procurement_id} 
          onChange={handleProcurementChange} 
          required
          disabled={!!initialData}
        >
          <option value="">Select Procurement...</option>
          {selectableProcurements.map(p => (
            <option key={p.id} value={p.id}>
              {p.procurement_no} - {p.farmer_name} (Total: Rs. {p.total_amount})
            </option>
          ))}
        </select>
        <div className="form-hint">Selecting a procurement auto-fills the linked farmer and amount.</div>
      </div>

      {selectedProcurement && (
        <div
          className="form-group"
          style={{
            marginBottom: '14px',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '6px',
            padding: '12px 14px'
          }}
        >
          <div className="form-label" style={{ marginBottom: '8px' }}>Procurement Summary</div>
          <div className="form-grid">
            <div>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Procurement No.</span>
              <div className="primary-cell">{selectedProcurement.procurement_no}</div>
            </div>
            <div>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Procurement Date</span>
              <div className="primary-cell">{new Date(selectedProcurement.procurement_date).toLocaleDateString('en-IN')}</div>
            </div>
            <div>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Farmer</span>
              <div className="primary-cell">{selectedProcurement.farmer_name}</div>
            </div>
            <div>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Crop</span>
              <div className="primary-cell">{selectedProcurement.crop_name}</div>
            </div>
            <div>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Quantity</span>
              <div className="primary-cell">{selectedProcurement.quantity} {selectedProcurement.unit}</div>
            </div>
            <div>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Procurement Total</span>
              <div className="primary-cell" style={{ fontWeight: 600 }}>Rs. {selectedProcurement.total_amount}</div>
            </div>
          </div>
        </div>
      )}

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Payment Amount <span className="form-label-required"></span></label>
          <input 
            type="number" 
            className="form-input" 
            step="0.01" 
            min="1"
            max={selectedProcurement ? selectedProcurement.total_amount : undefined}
            value={formData.amount} 
            onChange={e => { setFormData({...formData, amount: e.target.value}); setError(null); }} 
            required 
          />
        </div>

        <div className="form-group">
          <label className="form-label">Payment Date <span className="form-label-required"></span></label>
          <input 
            type="datetime-local" 
            className="form-input" 
            value={formData.payment_date} 
            onChange={e => setFormData({...formData, payment_date: e.target.value})} 
            required 
          />
        </div>

        <div className="form-group">
          <label className="form-label">Payment Method <span className="form-label-required"></span></label>
          <select 
            className="form-select" 
            value={formData.payment_method} 
            onChange={e => setFormData({...formData, payment_method: e.target.value})}
          >
            <option value="Bank Transfer">Bank Transfer</option>
            <option value="Cash">Cash</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Payment Status <span className="form-label-required"></span></label>
          <select 
            className="form-select" 
            value={formData.status} 
            onChange={e => setFormData({...formData, status: e.target.value})}
          >
            <option value="Pending">Pending</option>
            <option value="Paid">Paid</option>
          </select>
        </div>
      </div>

      <div className="form-group" style={{ marginTop: '14px' }}>
        <label className="form-label">Reference / UTR No. <span className="form-label-optional"></span></label>
        <input 
          type="text" 
          className="form-input" 
          placeholder="e.g. UPI Ref, Cheque No"
          value={formData.reference_no} 
          onChange={e => setFormData({...formData, reference_no: e.target.value})} 
        />
      </div>

      <div className="form-group" style={{ marginTop: '14px' }}>
        <label className="form-label">Remarks <span className="form-label-optional"></span></label>
        <textarea 
          className="form-textarea" 
          style={{ minHeight: '80px' }}
          value={formData.remarks} 
          onChange={e => setFormData({...formData, remarks: e.target.value})} 
        />
      </div>

      <div className="form-actions" style={{ marginTop: '20px' }}>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn btn-primary">Save Payment</button>
      </div>
    </form>
  );
}