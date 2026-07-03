import React, { useState, useEffect } from 'react';
import { locationService } from '../services/locationService';
import { villageService } from '../services/villageService';

interface FarmerFormProps {
  initialData?: any;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  isSuperAdmin: boolean;
}

export const FarmerForm: React.FC<FarmerFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSuperAdmin
}) => {
  const [formData, setFormData] = useState({
    farmer_name: initialData?.farmer_name || '',
    mobile_number: initialData?.mobile_number || '',
    gender: initialData?.gender || '',
    date_of_birth: initialData?.date_of_birth ? initialData.date_of_birth.split('T')[0] : '',
    aadhaar_number: initialData?.aadhaar_number || '',
    photo_url: initialData?.photo_url || '',
    shareholder_no: initialData?.shareholder_no || '',
    land_holding_acres: initialData?.land_holding_acres || '',
    farmer_category: initialData?.farmer_category || '',
    is_shareholder: initialData?.is_shareholder || false,
    village_id: initialData?.village_id || '',
    organization_id: initialData?.organization_id || 1,
  });

  const [villages, setVillages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadVillages = async () => {
      try {
        const res = await villageService.getVillages();
        setVillages(res.data);
      } catch (err) {
        console.error("Failed to load villages");
      }
    };
    loadVillages();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(formData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Farmer Name <span className="text-red-500">*</span></label>
          <input
            type="text"
            value={formData.farmer_name}
            onChange={(e) => setFormData({ ...formData, farmer_name: e.target.value })}
            required
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Mobile Number <span className="text-red-500">*</span></label>
          <input
            type="tel"
            value={formData.mobile_number}
            onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
            required
            className="form-input"
          />
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Gender</label>
          <select
            value={formData.gender}
            onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
            className="form-select"
          >
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Date of Birth</label>
          <input
            type="date"
            value={formData.date_of_birth}
            onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
            className="form-input"
          />
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Aadhaar Number</label>
          <input
            type="text"
            value={formData.aadhaar_number}
            onChange={(e) => setFormData({ ...formData, aadhaar_number: e.target.value })}
            className="form-input"
            maxLength={12}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Village <span className="text-red-500">*</span></label>
          <select
            value={formData.village_id}
            onChange={(e) => setFormData({ ...formData, village_id: parseInt(e.target.value) || '' })}
            required
            className="form-select"
          >
            <option value="">Select Village</option>
            {villages.map(v => (
              <option key={v.id} value={v.id}>
                {v.village_name} ({v.village_code})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Land Holding (Acres)</label>
          <input
            type="number"
            step="0.01"
            value={formData.land_holding_acres}
            onChange={(e) => setFormData({ ...formData, land_holding_acres: e.target.value })}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Farmer Category</label>
          <select
            value={formData.farmer_category}
            onChange={(e) => setFormData({ ...formData, farmer_category: e.target.value })}
            className="form-select"
          >
            <option value="">Select Category</option>
            <option value="Marginal">Marginal</option>
            <option value="Small">Small</option>
            <option value="Semi-Medium">Semi-Medium</option>
            <option value="Medium">Medium</option>
            <option value="Large">Large</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Shareholder No</label>
        <input
          type="text"
          value={formData.shareholder_no}
          onChange={(e) => setFormData({ ...formData, shareholder_no: e.target.value })}
          className="form-input"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={formData.is_shareholder}
          onChange={(e) => setFormData({ ...formData, is_shareholder: e.target.checked })}
          className="w-4 h-4"
        />
        <label>Is Shareholder</label>
      </div>

      {isSuperAdmin && (
        <div className="form-group">
          <label className="form-label">Organization ID</label>
          <input
            type="number"
            value={formData.organization_id}
            onChange={(e) => setFormData({ ...formData, organization_id: parseInt(e.target.value) || 1 })}
            className="form-input"
          />
        </div>
      )}

      <div className="flex gap-3 pt-4">
        <button type="button" onClick={onCancel} className="btn btn-ghost flex-1">
          Cancel
        </button>
        <button type="submit" disabled={loading} className="btn btn-primary flex-1">
          {loading ? 'Saving...' : initialData?.id ? 'Update Farmer' : 'Create Farmer'}
        </button>
      </div>
    </form>
  );
};