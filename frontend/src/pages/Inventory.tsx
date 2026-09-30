import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { ActionsMenu } from '../components/ActionsMenu';
import { inventoryService, InventoryBalance } from '../services/inventoryService';
import { cropMasterService } from '../services/cropMasterService';
import { getApiErrorMessage } from '../utils/errors';

interface CropOption {
  id: number;
  crop_name: string;
  crop_code?: string;
  is_active: boolean;
}

function formatKg(value: number): string {
  if (value == null) return '—';
  return value.toLocaleString('en-IN', { maximumFractionDigits: 2 }) + ' KG';
}

export default function Inventory() {
  const navigate = useNavigate();

  const [balances, setBalances] = useState<InventoryBalance[]>([]);
  const [crops, setCrops] = useState<CropOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [formCropId, setFormCropId] = useState<number | ''>('');
  const [formType, setFormType] = useState<'IN' | 'OUT'>('IN');
  const [formQty, setFormQty] = useState<string>('');
  const [formRemarks, setFormRemarks] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [balRes, cropRes] = await Promise.all([
        inventoryService.getBalances(),
        cropMasterService.getCropMasters(),
      ]);
      setBalances(balRes.data);
      setCrops(cropRes.data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load inventory'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const activeCrops = useMemo(
    () => crops.filter((c) => c.is_active),
    [crops]
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return balances;
    return balances.filter(
      (b) =>
        (b.crop_name ?? '').toLowerCase().includes(q) ||
        String(b.crop_id).includes(q)
    );
  }, [balances, search]);

  const activeCropsInStock = balances.filter((b) => b.current_balance > 0).length;

  const openForm = () => {
    setFormCropId('');
    setFormType('IN');
    setFormQty('');
    setFormRemarks('');
    setFormError(null);
    setShowForm(true);
  };

  const submitForm = async () => {
    setFormError(null);

    if (!formCropId) {
      setFormError('Please select a crop');
      return;
    }
    const qty = Number(formQty);
    if (!qty || qty <= 0) {
      setFormError('Quantity must be a positive number');
      return;
    }

    setSubmitting(true);
    try {
      await inventoryService.adjustStock({
        crop_id: Number(formCropId),
        transaction_type: formType,
        quantity: qty,
        remarks: formRemarks.trim() || undefined,
      });
      setSuccess('Stock adjusted successfully');
      setShowForm(false);
      setTimeout(() => setSuccess(null), 3000);
      loadAll();
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'Failed to adjust stock'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Inventory</h2>
            <p className="page-subtitle">
              Live stock balances derived from the inventory ledger
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div className="page-count-badge">
              {activeCropsInStock} crop{activeCropsInStock !== 1 ? 's' : ''} in stock
            </div>
            <button onClick={openForm} className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              Manual Adjustment
            </button>
          </div>
        </div>

        {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
        {success && <div className="success-banner" style={{ marginBottom: 16 }}>{success}</div>}

        <div className="table-toolbar" style={{ marginBottom: 12 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 380 }}>
            <input
              type="text"
              className="search-input"
              placeholder="Search by crop name or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 12 }}
            />
          </div>
        </div>

        {loading ? (
          <div className="table-skeleton">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton-row" style={{ marginBottom: 2, borderRadius: 4 }} />
            ))}
          </div>
        ) : (
          <div className="table-wrapper">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: 44 }}>#</th>
                    <th style={{ minWidth: 100 }}>Crop ID</th>
                    <th style={{ minWidth: 180 }}>Crop</th>
                    <th style={{ minWidth: 120 }}>Total IN</th>
                    <th style={{ minWidth: 120 }}>Total OUT</th>
                    <th style={{ minWidth: 140 }}>Current Balance</th>
                    <th style={{ width: 90, textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="empty-row">
                        <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                          {search ? 'No matching crops' : 'No inventory records yet'}
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filtered.map((b, idx) => (
                      <tr
                        key={b.crop_id}
                        style={{ cursor: 'pointer' }}
                        onClick={() => navigate(`/inventory/${b.crop_id}`)}
                      >
                        <td className="row-num">{idx + 1}</td>
                        <td>
                          <span className="mono-tag">{b.crop_id}</span>
                        </td>
                        <td>
                          <span className="primary-cell">{b.crop_name ?? '—'}</span>
                        </td>
                        <td>
                          <span style={{ color: '#4ade80', fontWeight: 600 }}>
                            {formatKg(b.total_in)}
                          </span>
                        </td>
                        <td>
                          <span style={{ color: '#f87171', fontWeight: 600 }}>
                            {formatKg(b.total_out)}
                          </span>
                        </td>
                        <td>
                          <span
                            style={{
                              fontWeight: 700,
                              color: b.current_balance > 0 ? '#60a5fa' : 'var(--text-muted)',
                            }}
                          >
                            {formatKg(b.current_balance)}
                          </span>
                        </td>
                        <td
                          style={{ textAlign: 'right' }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div style={{ display: 'inline-flex' }}>
                            <ActionsMenu
                              actions={[
                                {
                                  label: 'View Ledger',
                                  onClick: () => navigate(`/inventory/${b.crop_id}`),
                                },
                              ]}
                            />
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div
              className="modal-card"
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: 480 }}
            >
              <div className="modal-header">
                <div>
                  <div className="modal-title">Manual Adjustment</div>
                  <p className="modal-subtitle">Add or remove stock (in KG)</p>
                </div>
                <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
              </div>
              <div className="modal-body">
                <div style={{ display: 'grid', gap: 14 }}>
                  <label>
                    <span style={{ display: 'block', marginBottom: 6, fontSize: 13 }}>Crop</span>
                    <select
                      value={formCropId}
                      onChange={(e) =>
                        setFormCropId(e.target.value ? Number(e.target.value) : '')
                      }
                      className="form-input"
                      style={{ width: '100%' }}
                    >
                      <option value="">— Select crop —</option>
                      {activeCrops.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.crop_name} ({c.crop_code ?? c.id})
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    <span style={{ display: 'block', marginBottom: 6, fontSize: 13 }}>Type</span>
                    <select
                      value={formType}
                      onChange={(e) => setFormType(e.target.value as 'IN' | 'OUT')}
                      className="form-input"
                      style={{ width: '100%' }}
                    >
                      <option value="IN">IN (add stock)</option>
                      <option value="OUT">OUT (remove stock)</option>
                    </select>
                  </label>

                  <label>
                    <span style={{ display: 'block', marginBottom: 6, fontSize: 13 }}>
                      Quantity (KG)
                    </span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={formQty}
                      onChange={(e) => setFormQty(e.target.value)}
                      className="form-input"
                      style={{ width: '100%' }}
                    />
                  </label>

                  <label>
                    <span style={{ display: 'block', marginBottom: 6, fontSize: 13 }}>
                      Remarks
                    </span>
                    <input
                      type="text"
                      value={formRemarks}
                      onChange={(e) => setFormRemarks(e.target.value)}
                      className="form-input"
                      style={{ width: '100%' }}
                      maxLength={500}
                    />
                  </label>

                  {formError && (
                    <div className="error-banner">{formError}</div>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowForm(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={submitForm}
                  disabled={submitting}
                >
                  {submitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}