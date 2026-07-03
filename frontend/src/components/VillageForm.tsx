import React, { useState, useEffect } from 'react';
import { locationService } from '../services/locationService';

interface VillageFormProps {
  initialData?: any;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  isSuperAdmin: boolean;
}

export const VillageForm: React.FC<VillageFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSuperAdmin
}) => {
  const [states, setStates] = useState<any[]>([]);
  const [districts, setDistricts] = useState<any[]>([]);

  const [formData, setFormData] = useState({
    village_name: initialData?.village_name || '',
    state: initialData?.state || '',
    district: initialData?.district || '',
    block: initialData?.block || '',
    organization_id: initialData?.organization_id || 1,
  });

  const [loading, setLoading] = useState(false);
  const [districtLoading, setDistrictLoading] = useState(false);

  // Load states
  useEffect(() => {
    locationService.getStates().then((res) => {
      setStates(res.data);
    }).catch(() => {});
  }, []);

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
  const stateName = e.target.value;

  setFormData(prev => ({
    ...prev,
    state: stateName,
    district: '',
  }));

  const selectedState = states.find(
    (s: any) => s.state_name === stateName
  );

  if (selectedState) {
    setDistrictLoading(true);

    locationService
      .getDistricts(selectedState.id)
      .then((res) => setDistricts(res.data))
      .catch(() => {})
      .finally(() => setDistrictLoading(false));
  }
};

  const handleDistrictChange = (
  e: React.ChangeEvent<HTMLSelectElement>
) => {
  setFormData(prev => ({
    ...prev,
    district: e.target.value,
  }));
};

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
      <div className="form-group">
        <label className="form-label">Village Name <span style={{ color: 'var(--red)' }}>*</span></label>
        <input
          type="text"
          value={formData.village_name}
          onChange={(e) => setFormData({ ...formData, village_name: e.target.value })}
          required
          className="form-input"
          placeholder="Enter official village name"
        />
        <span className="form-hint">Enter official village name as per revenue records.</span>
      </div>

      <div className="form-group">
        <label className="form-label">State <span style={{ color: 'var(--red)' }}>*</span></label>
        <select
          value={formData.state}
          onChange={handleStateChange}
          className="form-select"
          required
        >
          <option value="">Select State</option>

          {states.map((s: any) => (
            <option
              key={s.id}
              value={s.state_name}
            >
              {s.state_name}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">District <span style={{ color: 'var(--red)' }}>*</span></label>
        <select
          value={formData.district}
          onChange={handleDistrictChange}
          className="form-select"
          required
          disabled={!formData.state || districtLoading}
        >
          <option value="">Select District</option>

          {districts.map((d: any) => (
            <option
              key={d.id}
              value={d.district_name}
            >
              {d.district_name}
            </option>
          ))}
        </select>
      </div>

      {/* Manual Block Input */}
      <div className="form-group">
        <label className="form-label">Block / Tehsil</label>
        <input
          type="text"
          value={formData.block}
          onChange={(e) =>
            setFormData({
              ...formData,
              block: e.target.value,
            })
          }
          className="form-input"
          placeholder="Enter Block / Tehsil"
        />
        <span className="form-hint">Type the block/tehsil name as per local/revenue records (optional)</span>
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
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-ghost flex-1"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary flex-1"
        >
          {loading ? 'Saving...' : initialData?.id ? 'Update Village' : 'Create Village'}
        </button>
      </div>
    </form>
  );
};