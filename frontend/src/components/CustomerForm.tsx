import { useState } from 'react';

interface CustomerFormProps {
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export function CustomerForm({ onSubmit, onCancel }: CustomerFormProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    customer_name: '',
    mobile_number: '',
    email: '',
    address: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (!formData.customer_name.trim()) {
        throw new Error('Customer name is required');
      }

      await onSubmit({
        customer_name: formData.customer_name.trim(),
        mobile_number: formData.mobile_number.trim() || undefined,
        email: formData.email.trim() || undefined,
        address: formData.address.trim() || undefined,
      });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : err?.message || 'Failed to create customer'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid">
      {error && <div className="form-error col-span-full">{error}</div>}

      <div className="form-group form-grid--single">
        <label className="form-label form-label-required">Customer Name</label>
        <input
          type="text"
          className="form-input"
          value={formData.customer_name}
          onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
          placeholder="Enter customer name"
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">Mobile Number</label>
        <input
          type="text"
          className="form-input"
          value={formData.mobile_number}
          onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
          placeholder="Optional"
        />
      </div>

      <div className="form-group">
        <label className="form-label">Email</label>
        <input
          type="email"
          className="form-input"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          placeholder="Optional"
        />
      </div>

      <div className="form-group form-grid--single">
        <label className="form-label">Address</label>
        <textarea
          className="form-textarea"
          value={formData.address}
          onChange={(e) => setFormData({ ...formData, address: e.target.value })}
          placeholder="Optional"
        />
      </div>

      <div className="form-grid--single">
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Saving...' : 'Create Customer'}
          </button>
        </div>
      </div>
    </form>
  );
}
