import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { inventoryService, InventoryLedgerEntry } from '../services/inventoryService';
import { getApiErrorMessage } from '../utils/errors';

function formatDate(value: string): string {
  if (!value) return '—';
  try {
    const d = new Date(value);
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return value;
  }
}

function formatKg(v: number): string {
  return (Number(v) || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }) + ' KG';
}

export default function InventoryLedger() {
  const { cropId } = useParams<{ cropId: string }>();
  const navigate = useNavigate();

  const [entries, setEntries] = useState<InventoryLedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!cropId) return;
      setLoading(true);
      try {
        const res = await inventoryService.getLedger(Number(cropId));
        setEntries(res.data);
      } catch (err) {
        setError(getApiErrorMessage(err, 'Failed to load ledger'));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [cropId]);

  const cropName = entries[0]?.crop_name ?? `Crop #${cropId}`;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <button
              className="btn btn-secondary"
              onClick={() => navigate('/inventory')}
              style={{ marginBottom: 8 }}
            >
              ← Back to Inventory
            </button>
            <h2 className="page-title">Ledger — {cropName}</h2>
            <p className="page-subtitle">All inventory movements for this crop</p>
          </div>
          <div className="page-count-badge">
            {entries.length} entr{entries.length === 1 ? 'y' : 'ies'}
          </div>
        </div>

        {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}

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
                    <th style={{ minWidth: 110 }}>Date</th>
                    <th style={{ minWidth: 80 }}>Type</th>
                    <th style={{ minWidth: 120 }}>Quantity</th>
                    <th style={{ minWidth: 120 }}>Source</th>
                    <th style={{ minWidth: 140 }}>Reference</th>
                    <th style={{ minWidth: 180 }}>Remarks</th>
                    <th style={{ minWidth: 90 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="empty-row">
                        <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                          No ledger entries yet
                        </div>
                      </td>
                    </tr>
                  ) : (
                    entries.map((e) => (
                      <tr key={e.id}>
                        <td>
                          <span style={{ fontSize: 13 }}>{formatDate(e.created_at)}</span>
                        </td>
                        <td>
                          <span
                            className={`status-pill ${e.transaction_type === 'IN' ? 'status-pill--active' : 'status-pill--inactive'}`}
                          >
                            {e.transaction_type}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontWeight: 600 }}>{formatKg(e.quantity)}</span>
                        </td>
                        <td>
                          <span className="mono-tag">{e.reference_type}</span>
                        </td>
                        <td>
                          {e.reference_id != null ? (
                            <span className="mono-tag">#{e.reference_id}</span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>—</span>
                          )}
                        </td>
                        <td>
                          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                            {e.remarks ?? '—'}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`status-pill ${e.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}
                          >
                            {e.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}