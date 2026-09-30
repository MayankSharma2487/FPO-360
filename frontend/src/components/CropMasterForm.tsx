import React, { useState } from 'react';

interface CropMasterFormProps {
  initialData?: any;
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
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validation
      if (!formData.crop_code || formData.crop_code.trim() === '') {
        throw new Error('Crop code is required');
      }
      if (!formData.crop_name || formData.crop_name.trim() === '') {
        throw new Error('Crop name is required');
      }

      const submitData = {
        crop_code: formData.crop_code.trim(),
        crop_name: formData.crop_name.trim(),
        crop_category: formData.crop_category?.trim() || null,
        unit: formData.unit?.trim() || 'Kg',
      };

      await onSubmit(submitData);
    } catch (err: any) {
      setError(err?.message || 'Failed to save crop');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid">
      {error && (
        <div className="form-error col-span-full">{error}</div>
      )}

      <div className="form-group">
        <label className="form-label form-label-required">Crop Code</label>
        <input
          type="text"
          className="form-input"
          value={formData.crop_code}
          onChange={(e) => setFormData({ ...formData, crop_code: e.target.value })}
          placeholder="e.g., 001"
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label form-label-required">Crop Name</label>
        <input
          type="text"
          className="form-input"
          value={formData.crop_name}
          onChange={(e) => setFormData({ ...formData, crop_name: e.target.value })}
          placeholder="e.g., Wheat"
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">Category</label>
        <input
          type="text"
          className="form-input"
          value={formData.crop_category}
          onChange={(e) => setFormData({ ...formData, crop_category: e.target.value })}
          placeholder="e.g., Cereal"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Unit</label>
        <select
          className="form-select"
          value={formData.unit}
          onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
        >
          <option value="Kg">Kg (Kilogram)</option>
          <option value="Quintal">Quintal</option>
          <option value="Ton">Ton</option>
        </select>
      </div>

      <div className="form-grid--single">
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : (initialData?.id ? 'Update Crop' : 'Create Crop')}
          </button>
        </div>
      </div>
    </form>
  );
};