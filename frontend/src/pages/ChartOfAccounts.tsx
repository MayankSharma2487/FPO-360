import { useEffect, useState } from 'react';
import { ArrowLeft, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import AccountForm from '../components/AccountForm';
import { financeService, FinanceAccount } from '../services/financeService';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage } from '../utils/errors';

export default function ChartOfAccounts() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [rows, setRows] = useState<FinanceAccount[]>([]);
  const [error, setError] = useState('');
  const load = () => financeService.accounts().then(r => setRows(r.data)).catch(e => setError(getApiErrorMessage(e, 'Unable to load accounts')));
  useEffect(() => { load(); }, []);
  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Accountant', 'Manager', 'Viewer']}>
    <div className="page-wrapper">
      <header className="page-header"><div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}><button type="button" className="btn btn-ghost" onClick={() => navigate('/finance')} style={{ gap: 7, padding: '7px 11px', flexShrink: 0 }}><ArrowLeft size={15} />Back to Finance</button><div><h2 className="page-title">Chart of Accounts</h2><p className="page-subtitle">Accounts used to record and report organization activity</p></div></div><span className="page-count-badge">{rows.length} accounts</span></header>
      {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
      {['Super Admin', 'FPO Admin', 'Accountant'].includes(user?.role?.name || '') && <AccountForm onSaved={load} />}
      <div className="table-wrapper"><div className="table-scroll"><table className="data-table"><thead><tr><th>Code</th><th>Account</th><th>Type</th><th>Group</th><th>Status</th></tr></thead><tbody>
        {rows.length === 0 ? <tr><td colSpan={5} className="empty-row"><BookOpen size={24} style={{ display: 'block', margin: '0 auto 8px', opacity: 0.55 }} />No accounts found.</td></tr> : rows.map(a => <tr key={a.id}>
          <td><span className="mono-tag">{a.account_code}</span></td>
          <td><span className="primary-cell">{a.account_name}</span>{a.system_key && <span className="status-pill status-pill--pending" style={{ marginLeft: 9 }}>System</span>}</td>
          <td>{a.account_type}</td><td>{a.account_group}</td>
          <td><span className={`status-pill ${a.is_active ? 'status-pill--active' : 'status-pill--inactive'}`}>{a.is_active ? 'Active' : 'Inactive'}</span></td>
        </tr>)}
      </tbody></table></div></div>
    </div>
  </RoleGuard>;
}
