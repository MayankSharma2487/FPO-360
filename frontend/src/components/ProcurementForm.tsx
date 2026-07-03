import { useState, useEffect } from 'react'
import { farmerService } from '../services/farmerService'
import { cropMasterService } from '../services/cropMasterService'

interface ProcurementFormProps {
  initialData?: any
  onSubmit: (data: any) => Promise<void>
  onCancel: () => void
}

export function ProcurementForm({ initialData, onSubmit, onCancel }: ProcurementFormProps) {
  const [farmers, setFarmers] = useState<any[]>([])
  const [crops, setCrops] = useState<any[]>([])
  const [loadingOptions, setLoadingOptions] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * REVERSE CONVERT: Convert KG storage value to display unit
   * 
   * Frontend rule: Display reverse-converted quantities
   * Example:
   * - Database: quantity=500, unit=QUINTAL → Display: 5 QT
   * - Database: quantity=2000, unit=TON → Display: 2 MT
   * - Database: quantity=120, unit=KG → Display: 120 KG
   */
  const getReverseConvertedQuantity = (storedQuantityInKg: number, unit: string): number => {
    if (unit === 'QUINTAL') {
      return storedQuantityInKg / 100  // 500 KG / 100 = 5 QT
    } else if (unit === 'TON') {
      return storedQuantityInKg / 1000  // 2000 KG / 1000 = 2 MT
    } else {
      return storedQuantityInKg  // KG stays as-is
    }
  }

  const [formData, setFormData] = useState({
    procurement_date: initialData?.procurement_date 
      ? initialData.procurement_date.split('T')[0] 
      : new Date().toISOString().split('T')[0],
    farmer_id: initialData?.farmer_id || '',
    crop_id: initialData?.crop_id || '',
    // REVERSE CONVERT: If editing, show reverse-converted quantity
    quantity: initialData?.quantity 
      ? getReverseConvertedQuantity(initialData.quantity, initialData.unit).toString()
      : '',
    unit: initialData?.unit || 'KG',
    rate_per_unit: initialData?.rate_per_unit || '',
    total_amount: initialData?.total_amount || 0,
    quality_grade: initialData?.quality_grade || 'A',
    remarks: initialData?.remarks || '',
  })

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [farmerRes, cropRes] = await Promise.all([
          farmerService.getFarmers(),
          cropMasterService.getCropMasters()
        ])
        setFarmers(farmerRes.data)
        setCrops(cropRes.data)
      } catch (err) {
        setError('Failed to load form options')
      } finally {
        setLoadingOptions(false)
      }
    }
    loadOptions()
  }, [])

  /**
   * Auto-calculate total amount using DISPLAYED quantity (not KG-converted)
   * 
   * Example:
   * - User enters: 5 QT
   * - Rate: ₹2500 per QT
   * - Total: 5 × ₹2500 = ₹12,500
   * (NOT 500 KG × ₹2500)
   */
  useEffect(() => {
    const qty = parseFloat(formData.quantity) || 0
    const rate = parseFloat(formData.rate_per_unit) || 0
    const total = (qty * rate).toFixed(2)
    setFormData(prev => ({ ...prev, total_amount: total }))
  }, [formData.quantity, formData.rate_per_unit])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      // Validation
      if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
        throw new Error('Quantity must be greater than 0')
      }
      if (!formData.rate_per_unit || parseFloat(formData.rate_per_unit) <= 0) {
        throw new Error('Rate must be greater than 0')
      }

      /**
       * IMPORTANT: Submit exactly what user entered
       * 
       * Frontend rule: Never convert before sending
       * The backend will convert to KG for storage
       * 
       * Example:
       * - User enters: 5 QT at ₹2500
       * - Send: { quantity: 5, unit: "QUINTAL", rate_per_unit: 2500 }
       * - Backend converts: 5 × 100 = 500 KG for storage
       * - Total calculated by backend: 5 × ₹2500 = ₹12,500
       */
      const submitData = {
        procurement_date: formData.procurement_date,
        farmer_id: parseInt(formData.farmer_id),
        crop_id: parseInt(formData.crop_id),
        quantity: parseFloat(formData.quantity),  // Send exactly what user entered
        unit: formData.unit,  // Send original unit
        rate_per_unit: formData.rate_per_unit,
        quality_grade: formData.quality_grade || undefined,
        remarks: formData.remarks || undefined,
      }

      await onSubmit(submitData)
    } catch (err: any) {
      setError(err?.message || 'Failed to save procurement record')
    } finally {
      setSubmitting(false)
    }
  }

  if (loadingOptions) {
    return <div className="text-gray-400 text-sm">Loading form options...</div>
  }

  return (
  <form onSubmit={handleSubmit} className="form-grid">
    {error && <div className="form-error col-span-full">{error}</div>}

    <div className="form-group">
      <label className="form-label form-label-required">Procurement Date</label>
      <input
        type="date"
        className="form-input"
        value={formData.procurement_date}
        onChange={(e) => setFormData({ ...formData, procurement_date: e.target.value })}
        required
      />
    </div>

    <div className="form-group">
      <label className="form-label form-label-required">Farmer</label>
      <select
        className="form-select"
        value={formData.farmer_id}
        onChange={(e) => setFormData({ ...formData, farmer_id: parseInt(e.target.value) })}
        required
      >
        <option value="">Select Farmer...</option>
        {farmers.map(f => (
          <option key={f.id} value={f.id}>
            {f.farmer_name} ({f.farmer_code})
          </option>
        ))}
      </select>
    </div>

    <div className="form-group">
      <label className="form-label form-label-required">Crop</label>
      <select
        className="form-select"
        value={formData.crop_id}
        onChange={(e) => setFormData({ ...formData, crop_id: parseInt(e.target.value) })}
        required
      >
        <option value="">Select Crop...</option>
        {crops.map(c => (
          <option key={c.id} value={c.id}>
            {c.crop_name} ({c.crop_code})
          </option>
        ))}
      </select>
    </div>

    <div className="form-group">
      <label className="form-label form-label-required">Quantity</label>
      <input
        type="number"
        step="0.01"
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
        <option value="KG">KG (Kilogram)</option>
        <option value="QUINTAL">QT (Quintal)</option>
        <option value="TON">MT (Metric Ton)</option>
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
      <span className="form-hint">{parseFloat(formData.quantity) || 0} × ₹{parseFloat(formData.rate_per_unit) || 0}</span>
    </div>

    <div className="form-group">
      <label className="form-label">Quality Grade</label>
      <select
        className="form-select"
        value={formData.quality_grade}
        onChange={(e) => setFormData({ ...formData, quality_grade: e.target.value })}
      >
        <option value="A">A - Premium</option>
        <option value="B">B - Good</option>
        <option value="C">C - Fair</option>
        <option value="D">D - Below Average</option>
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
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={submitting}
        >
          {submitting ? 'Processing...' : (initialData?.id ? 'Update' : 'Create')}
        </button>
      </div>
    </div>
  </form>
)};