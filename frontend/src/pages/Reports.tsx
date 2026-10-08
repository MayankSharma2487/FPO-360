import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { RoleGuard } from '../components/RoleGuard';
import { reportsService, ReportPage } from '../services/reportsService';
import { farmerService } from '../services/farmerService';
import { cropMasterService } from '../services/cropMasterService';
import { customerService } from '../services/salesService';

const cards = [
  ['farmers', 'Farmers', 'Member details and procurement/payment totals.'],
  ['procurement', 'Procurement', 'Procurement transactions, quantities and values.'],
  ['payments', 'Payments', 'Farmer payments by date, method and status.'],
  ['inventory', 'Inventory', 'Stock movements and current operational stock.'],
  ['sales', 'Sales', 'Sales transactions, values and payment status.'],
  ['finance-summary', 'Finance Summary', 'A concise view of posted Finance balances.'],
  ['licenses', 'Licenses', 'License status and upcoming expiries.'],
] as const;

const titles: Record<string, string> = Object.fromEntries(cards.map(([id, title]) => [id, title]));
const descriptions: Record<string, string> = Object.fromEntries(cards.map(([id, , description]) => [id, description]));
const money = new Set(['total', 'value', 'amount', 'paid', 'pending', 'cash', 'bank', 'other', 'revenue', 'expenses', 'net_position', 'receivables', 'payables', 'procurement_value', 'payment_total', 'average_rate']);
const label = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
const display = (key: string, value: any) => {
  if (value == null || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'string' && value.includes('T')) return new Date(value).toLocaleDateString();
  if (money.has(key)) return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  if (typeof value === 'number') return value.toLocaleString('en-IN', { maximumFractionDigits: 2 });
  return String(value);
};

export default function Reports() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selected = searchParams.get('type') || '';
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<ReportPage | null>(null);
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [farmers, setFarmers] = useState<any[]>([]);
  const [crops, setCrops] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);

  useEffect(() => {
    Promise.allSettled([farmerService.getFarmers(), cropMasterService.getCropMasters(), customerService.getCustomers()]).then(([f, c, cu]) => {
      if (f.status === 'fulfilled') setFarmers(f.value.data);
      if (c.status === 'fulfilled') setCrops(c.value.data);
      if (cu.status === 'fulfilled') setCustomers(cu.value.data);
    });
  }, []);

  const params = useMemo(() => Object.fromEntries(Object.entries({ ...filters, page, page_size: 25 }).filter(([, v]) => String(v) !== '')), [filters, page]);
  const load = useCallback(async () => {
    if (!selected) return;
    setLoading(true); setError('');
    try {
      if (selected === 'finance-summary') setSummary((await reportsService.financeSummary()).data);
      else if (selected === 'licenses') setSummary((await reportsService.licenseSummary()).data);
      else setResult((await reportsService.list(selected, params)).data);
    } catch (e: any) { setError(e?.response?.data?.detail || 'Unable to load report.'); }
    finally { setLoading(false); }
  }, [selected, params]);
  useEffect(() => { setResult(null); setSummary(null); setPage(1); setFilters({}); }, [selected]);
  useEffect(() => { load(); }, [load]);

  const setFilter = (key: string, value: string) => { setFilters(v => ({ ...v, [key]: value })); setPage(1); };
  const exportCsv = async () => {
    try {
      const response = await reportsService.export(selected, { ...params, page: undefined, page_size: undefined });
      const url = URL.createObjectURL(response.data); const a = document.createElement('a'); a.href = url; a.download = `${selected}-report.csv`; a.click(); URL.revokeObjectURL(url);
    } catch (e: any) { setError(e?.response?.data?.detail || 'Unable to export report.'); }
  };

  return <RoleGuard allowedRoles={['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer']}>
    <div className="page-wrapper">
      <div className="page-header"><div><h2 className="page-title">{selected ? titles[selected] || 'Reports' : 'Reports'}</h2><p className="page-subtitle">{selected ? descriptions[selected] : 'Operational reports from your organization records.'}</p></div>
        {selected && <button className="btn btn-secondary" onClick={() => setSearchParams({})}>All Reports</button>}
      </div>
      {!selected ? <div className="cards-grid">{cards.map(([id, title, description]) => <button key={id} className="stat-card" onClick={() => setSearchParams({ type: id })} style={{ textAlign: 'left', cursor: 'pointer' }}><div className="stat-card-header"><span className="stat-label">{title}</span></div><p className="page-subtitle">{description}</p><span className="btn btn-secondary">Open report</span></button>)}</div> : null}

      {selected === 'finance-summary' && <div className="cards-grid">{loading ? <p>Loading…</p> : Object.entries(summary || {}).map(([key, value]) => <div className="stat-card" key={key}><div className="stat-card-header"><span className="stat-label">{label(key)}</span></div><div className="stat-value">{display(key, value)}</div></div>)}<div className="stat-card"><span className="stat-label">Finance reports</span><p><Link to="/finance/trial-balance">Trial Balance</Link></p><p><Link to="/finance/general-ledger">General Ledger</Link></p></div></div>}
      {selected === 'licenses' && <div className="cards-grid">{loading ? <p>Loading…</p> : Object.entries(summary || {}).map(([key, value]) => <div className="stat-card" key={key}><div className="stat-card-header"><span className="stat-label">{label(key)}</span></div><div className="stat-value">{value}</div></div>)}<div className="stat-card"><Link className="btn btn-primary" to="/licenses">Manage Licenses</Link></div></div>}

      {error && <div className="error-banner" style={{ marginBottom: 16 }}>{error}</div>}
      {selected && !['finance-summary', 'licenses'].includes(selected) && <>
        <div className="stat-card" style={{ marginBottom: 20 }}><div className="form-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 12 }}>
          <label>From Date<input className="form-input" type="date" value={filters.from_date || ''} onChange={e => setFilter('from_date', e.target.value)} /></label>
          <label>To Date<input className="form-input" type="date" value={filters.to_date || ''} onChange={e => setFilter('to_date', e.target.value)} /></label>
          {selected === 'procurement' && <><label>Farmer<select className="form-input" value={filters.farmer_id || ''} onChange={e => setFilter('farmer_id', e.target.value)}><option value="">All farmers</option>{farmers.map(f => <option key={f.id} value={f.id}>{f.farmer_name}</option>)}</select></label><label>Crop<select className="form-input" value={filters.crop_id || ''} onChange={e => setFilter('crop_id', e.target.value)}><option value="">All crops</option>{crops.map(c => <option key={c.id} value={c.id}>{c.crop_name}</option>)}</select></label><label>Status<select className="form-input" value={filters.status || ''} onChange={e => setFilter('status', e.target.value)}><option value="">All</option><option>Active</option><option>Inactive</option></select></label></>}
          {selected === 'payments' && <><label>Farmer<select className="form-input" value={filters.farmer_id || ''} onChange={e => setFilter('farmer_id', e.target.value)}><option value="">All farmers</option>{farmers.map(f => <option key={f.id} value={f.id}>{f.farmer_name}</option>)}</select></label><label>Payment Method<input className="form-input" value={filters.payment_method || ''} onChange={e => setFilter('payment_method', e.target.value)} /></label><label>Status<input className="form-input" value={filters.status || ''} onChange={e => setFilter('status', e.target.value)} /></label></>}
          {selected === 'inventory' && <><label>Crop<select className="form-input" value={filters.crop_id || ''} onChange={e => setFilter('crop_id', e.target.value)}><option value="">All crops</option>{crops.map(c => <option key={c.id} value={c.id}>{c.crop_name}</option>)}</select></label><label>Movement Type<select className="form-input" value={filters.movement_type || ''} onChange={e => setFilter('movement_type', e.target.value)}><option value="">All</option><option>IN</option><option>OUT</option></select></label></>}
          {selected === 'sales' && <><label>Customer<select className="form-input" value={filters.customer_id || ''} onChange={e => setFilter('customer_id', e.target.value)}><option value="">All customers</option>{customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}</select></label><label>Product<select className="form-input" value={filters.crop_id || ''} onChange={e => setFilter('crop_id', e.target.value)}><option value="">All products</option>{crops.map(c => <option key={c.id} value={c.id}>{c.crop_name}</option>)}</select></label><label>Payment Status<select className="form-input" value={filters.payment_status || ''} onChange={e => setFilter('payment_status', e.target.value)}><option value="">All</option><option>Paid</option><option>Pending</option></select></label><label>Sale Status<select className="form-input" value={filters.sale_status || ''} onChange={e => setFilter('sale_status', e.target.value)}><option value="">All</option><option>Active</option><option>Inactive</option></select></label></>}
          {selected === 'farmers' && <label>Status<select className="form-input" value={filters.status || ''} onChange={e => setFilter('status', e.target.value)}><option value="">All</option><option>active</option><option>inactive</option></select></label>}
          {selected !== 'inventory' && <label>Search<input className="form-input" value={filters.search || ''} onChange={e => setFilter('search', e.target.value)} /></label>}
          <div style={{ display: 'flex', alignItems: 'end', gap: 8 }}><button className="btn btn-secondary" onClick={() => { setFilters({}); setPage(1); }}>Clear filters</button><button className="btn btn-primary" onClick={exportCsv}>Export CSV</button></div>
        </div></div>
        <div className="cards-grid">{Object.entries(result?.summary || {}).map(([key, value]) => <div className="stat-card" key={key}><div className="stat-card-header"><span className="stat-label">{label(key)}</span></div><div className="stat-value">{display(key, value)}</div></div>)}</div>
        {error && <div className="error-banner">{error}</div>}
        <div className="table-wrapper"><div className="table-scroll">{loading ? <p className="empty-state">Loading report…</p> : !result?.items.length ? <p className="empty-state">No records match these filters.</p> : <table className="data-table"><thead><tr>{Object.keys(result.items[0]).filter(k => k !== 'id').map(k => <th key={k}>{label(k)}</th>)}<th>Details</th></tr></thead><tbody>{result.items.map((row, i) => <tr key={row.id || i}>{Object.entries(row).filter(([k]) => k !== 'id').map(([key, value]) => <td key={key}>{display(key, value)}</td>)}<td>{selected === 'procurement' ? <Link to={`/procurement/${row.id}`}>View</Link> : selected === 'payments' ? <Link to={`/payments/${row.id}`}>View</Link> : selected === 'sales' ? <Link to="/sales">Sales</Link> : selected === 'farmers' ? <Link to="/farmers">Farmers</Link> : '—'}</td></tr>)}</tbody></table>}</div></div>
        <div className="table-toolbar" style={{ justifyContent: 'space-between' }}><span>{result?.total || 0} records</span><div><button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button> <span>Page {page}</span> <button className="btn btn-secondary" disabled={!result || page * result.page_size >= result.total} onClick={() => setPage(p => p + 1)}>Next</button></div></div>
      </>}
    </div>
  </RoleGuard>;
}
