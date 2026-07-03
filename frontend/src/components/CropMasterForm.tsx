import React, { useState } from 'react';

interface CropMaster {
  id?: number;
  crop_code: string;
  crop_name: string;
  crop_category?: string;
  unit: string;
}

interface CropMasterFormProps {
  initialData?: Partial<CropMaster>;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export const CropMasterForm: React.FC<CropMasterFormProps> = ({
  initialData,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    crop_code: initialData?.crop_code || '',
    crop_name: initialData?.crop_name || '',
    crop_category: initialData?.crop_category || '',
    unit: initialData?.unit || 'Kg',
  });
  const [loading, setLoading] = useState(false);

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
      <div>
        <label className="form-label">Crop Code</label>
        <input
          type="text"
          value={formData.crop_code}
          onChange={(e) => setFormData({ ...formData, crop_code: e.target.value })}
          required
          className="form-input"
        />
      </div>

      <div>
        <label className="form-label">Crop Name</label>
        <input
          type="text"
          value={formData.crop_name}
          onChange={(e) => setFormData({ ...formData, crop_name: e.target.value })}
          required
          className="form-input"
        />
      </div>

      <div>
        <label className="form-label">Category</label>
        <input
          type="text"
          value={formData.crop_category}
          onChange={(e) => setFormData({ ...formData, crop_category: e.target.value })}
          className="form-input"
        />
      </div>

      <div>
        <label className="form-label">Unit</label>
        <select
          value={formData.unit}
          onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
          className="form-select"
        >
          <option value="Kg">Kg</option>
          <option value="Quintal">Quintal</option>
          <option value="Ton">Ton</option>
          <option value="Bunch">Bunch</option>
        </select>
      </div>

      <div className="flex gap-3 pt-4">
        <button type="button" onClick={onCancel} className="btn btn-ghost flex-1">Cancel</button>
        <button type="submit" disabled={loading} className="btn btn-primary flex-1">
          {loading ? 'Saving...' : initialData?.id ? 'Update Crop' : 'Create Crop'}
        </button>
      </div>
    </form>
  );
};