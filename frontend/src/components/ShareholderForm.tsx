import React, { useState, useEffect } from 'react';
import { farmerService } from '../services/farmerService';

interface ShareholderFormProps {
  initialData?: any;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  isSuperAdmin: boolean;
}

export const ShareholderForm: React.FC<ShareholderFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSuperAdmin
}) => {
  const [formData, setFormData] = useState({
    farmer_id: initialData?.farmer_id || '',
    share_certificate_no: initialData?.share_certificate_no || '',
    share_count: initialData?.share_count || 1,
    share_value: initialData?.share_value || 100,
    joining_date: initialData?.joining_date ? initialData.joining_date.split('T')[0] : '',
    is_active: initialData?.is_active !== false,
  });

  const [farmers, setFarmers] = useState<any[]>([]);
  const [totalCapital, setTotalCapital] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadFarmers = async () => {
      try {
        const res = await farmerService.getFarmers();
        setFarmers(res.data);
      } catch (err) {
        console.error("Failed to load farmers");
      }
    };
    loadFarmers();
  }, []);

  useEffect(() => {
    const capital = (formData.share_count || 0) * (formData.share_value || 0);
    setTotalCapital(capital);
  }, [formData.share_count, formData.share_value]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({ ...formData, total_share_capital: totalCapital });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="form-group">
        <label className="form-label">Farmer <span className="text-red-500">*</span></label>
        <select
          value={formData.farmer_id}
          onChange={(e) => setFormData({ ...formData, farmer_id: parseInt(e.target.value) })}
          required
          className="form-select"
        >
          <option value="">Select Farmer</option>
          {farmers.map(f => (
            <option key={f.id} value={f.id}>
              {f.farmer_name} | {f.mobile_number} | {f.village_name || '—'}
            </option>
          ))}
        </select>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Share Certificate No</label>
          <input
            type="text"
            value={formData.share_certificate_no}
            onChange={(e) => setFormData({ ...formData, share_certificate_no: e.target.value })}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Joining Date</label>
          <input
            type="date"
            value={formData.joining_date}
            onChange={(e) => setFormData({ ...formData, joining_date: e.target.value })}
            className="form-input"
          />
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Share Count <span className="text-red-500">*</span></label>
          <input
            type="number"
            min="1"
            value={formData.share_count}
            onChange={(e) => setFormData({ ...formData, share_count: parseInt(e.target.value) || 1 })}
            required
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Share Value (₹) <span className="text-red-500">*</span></label>
          <input
            type="number"
            min="1"
            value={formData.share_value}
            onChange={(e) => setFormData({ ...formData, share_value: parseFloat(e.target.value) || 100 })}
            required
            className="form-input"
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Total Share Capital (₹)</label>
        <input
          type="text"
          value={totalCapital.toLocaleString('en-IN')}
          className="form-input bg-gray-800"
          readOnly
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={formData.is_active}
          onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
        />
        <label>Active Shareholder</label>
      </div>

      <div className="flex gap-3 pt-4">
        <button type="button" onClick={onCancel} className="btn btn-ghost flex-1">Cancel</button>
        <button type="submit" disabled={loading} className="btn btn-primary flex-1">
          {loading ? 'Saving...' : initialData?.id ? 'Update' : 'Create Shareholder'}
        </button>
      </div>
    </form>
  );
};