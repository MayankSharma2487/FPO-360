import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarDays, BookOpen, ClipboardList, BookMarked, Scale, ArrowRight } from 'lucide-react';
import { RoleGuard } from '../components/RoleGuard';
import { financeService } from '../services/financeService';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage } from '../utils/errors';

const sections = [
  { title: 'Financial Years', description: 'Manage reporting periods and year status.', path: '/finance/years', icon: CalendarDays, accent: '#60a5fa' },
  { title: 'Chart of Accounts', description: 'Review the accounts used by your organization.', path: '/finance/accounts', icon: BookOpen, accent: '#a78bfa' },
  { title: 'Journal Entries', description: 'Record and review balanced journal entries.', path: '/finance/journals', icon: ClipboardList, accent: '#4ade80' },
  { title: 'General Ledger', description: 'Review activity and balances by account.', path: '/finance/general-ledger', icon: BookMarked, accent: '#fbbf24' },
  { title: 'Trial Balance', description: 'Compare account debit and credit balances.', path: '/finance/trial-balance', icon: Scale, accent: '#fb7185' },
];

export default function Finance() {
  const { user } = useAuth();
  const canWrite = ['Super Admin', 'FPO Admin', 'Accountant'].includes(user?.role?.name || '');
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    financeService.setupStatus().then(r => setStatus(r.data))
      .catch(e => setError(getApiErrorMessage(e, 'Unable to load Finance')));
  }, []);

  const setup = async () => {
    setError('');
    try {
      await financeService.setup();
      const response = await financeService.setupStatus();
      setStatus(response.data);
    } catch (e) {
      setError(getApiErrorMessage(e, 'Unable to set up accounts'));
    }
  };

  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Accountant', 'Manager', 'Viewer']}>
    <div className="page-wrapper">
      <header className="page-header">
        <div><h2 className="page-title">Finance</h2><p className="page-subtitle">Accounting foundation and financial reports</p></div>
      </header>
      {error && <div className="error-banner" style={{ marginBottom: 18 }}>{error}</div>}
      <div className="cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 210px), 1fr))', gap: 14, marginBottom: 24 }}>
        {sections.map(({ title, description, path, icon: Icon, accent }) => <Link
          className="stat-card"
          key={path}
          to={path}
          style={{ display: 'flex', flexDirection: 'column', minHeight: 152, textDecoration: 'none', color: 'inherit', gap: 12 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ width: 38, height: 38, display: 'grid', placeItems: 'center', borderRadius: 9, background: `${accent}18`, color: accent }}><Icon size={19} /></span>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
          </div>
          <div>
            <h3 style={{ fontSize: '0.98rem', color: 'var(--text-primary)', marginBottom: 5 }}>{title}</h3>
            <p style={{ fontSize: '0.78rem', lineHeight: 1.5, color: 'var(--text-secondary)' }}>{description}</p>
          </div>
        </Link>)}
      </div>
      {canWrite && status && !status.configured && <section className="stat-card" style={{ padding: '18px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div><h3 style={{ fontSize: '0.95rem', marginBottom: 5 }}>Finance setup</h3><p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Install the default 23 account chart for this organization.</p></div>
          <button className="btn btn-primary" onClick={setup}>Set up chart of accounts</button>
        </div>
      </section>}
    </div>
  </RoleGuard>;
}
