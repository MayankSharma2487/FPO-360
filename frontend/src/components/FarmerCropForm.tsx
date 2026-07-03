import React, { useState, useEffect } from 'react';
import { farmerService } from '../services/farmerService';
import { cropMasterService } from '../services/cropMasterService';

interface FarmerCrop {
  id?: number;
  farmer_id: number;
  crop_id: number;
  season?: string;
  year: number;
  area_acres?: number;
  sowing_date?: string;
  harvest_date?: string;
  expected_yield?: number;
  actual_yield?: number;
  remarks?: string;
}

interface FarmerCropFormProps {
  initialData?: Partial<FarmerCrop>;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export const FarmerCropForm: React.FC<FarmerCropFormProps> = ({
  initialData,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    farmer_id: initialData?.farmer_id || 0,
    crop_id: initialData?.crop_id || 0,
    season: initialData?.season || '',
    year: initialData?.year || new Date().getFullYear(),
    area_acres: initialData?.area_acres || 0,
    sowing_date: initialData?.sowing_date ? initialData.sowing_date.split('T')[0] : '',
    harvest_date: initialData?.harvest_date ? initialData.harvest_date.split('T')[0] : '',
    expected_yield: initialData?.expected_yield || 0,
    actual_yield: initialData?.actual_yield || 0,
    remarks: initialData?.remarks || '',
  });

  const [farmers, setFarmers] = useState<any[]>([]);
  const [crops, setCrops] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [formLoading, setFormLoading] = useState(true);

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [farmerRes, cropRes] = await Promise.all([
          farmerService.getFarmers(),
          cropMasterService.getCropMasters()
        ]);
        setFarmers(farmerRes.data);
        setCrops(cropRes.data);
      } catch (err) {
        console.error('Failed to load dropdowns');
      } finally {
        setFormLoading(false);
      }
    };
    loadOptions();
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

  if (formLoading) return <div className="p-8 text-center">Loading options...</div>;

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Farmer</label>
          <select
            value={formData.farmer_id}
            onChange={(e) => setFormData({ ...formData, farmer_id: parseInt(e.target.value) })}
            required
            className="form-select"
          >
            <option value="">Select Farmer</option>
            {farmers.map(f => (
              <option key={f.id} value={f.id}>{f.farmer_name} ({f.farmer_code})</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Crop</label>
          <select
            value={formData.crop_id}
            onChange={(e) => setFormData({ ...formData, crop_id: parseInt(e.target.value) })}
            required
            className="form-select"
          >
            <option value="">Select Crop</option>
            {crops.map(c => (
              <option key={c.id} value={c.id}>{c.crop_name} ({c.crop_code})</option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Season</label>
          <select
            value={formData.season}
            onChange={(e) => setFormData({ ...formData, season: e.target.value })}
            className="form-select"
          >
            <option value="">Select Season</option>
            <option value="Kharif">Kharif</option>
            <option value="Rabi">Rabi</option>
            <option value="Zaid">Zaid</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Year</label>
          <input
            type="number"
            value={formData.year}
            onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
            required
            className="form-input"
          />
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Area (Acres)</label>
          <input
            type="number"
            step="0.01"
            value={formData.area_acres}
            onChange={(e) => setFormData({ ...formData, area_acres: parseFloat(e.target.value) })}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Expected Yield</label>
          <input
            type="number"
            step="0.01"
            value={formData.expected_yield}
            onChange={(e) => setFormData({ ...formData, expected_yield: parseFloat(e.target.value) })}
            className="form-input"
          />
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">Sowing Date</label>
          <input
            type="date"
            value={formData.sowing_date}
            onChange={(e) => setFormData({ ...formData, sowing_date: e.target.value })}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Harvest Date</label>
          <input
            type="date"
            value={formData.harvest_date}
            onChange={(e) => setFormData({ ...formData, harvest_date: e.target.value })}
            className="form-input"
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Remarks</label>
        <textarea
          value={formData.remarks}
          onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
          className="form-textarea"
          rows={3}
        />
      </div>

      <div className="flex gap-3 pt-6">
        <button type="button" onClick={onCancel} className="btn btn-ghost flex-1">Cancel</button>
        <button type="submit" disabled={loading} className="btn btn-primary flex-1">
          {loading ? 'Saving...' : initialData?.id ? 'Update Record' : 'Create Record'}
        </button>
      </div>
    </form>
  );
};