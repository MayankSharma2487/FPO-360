import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface NavItem {
  label: string;
  path: string;
  icon: string;
  roles: string[];
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard',     path: '/dashboard',     icon: '⬡', roles: ['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer'] },
  { label: 'Organizations', path: '/organizations', icon: '◈', roles: ['Super Admin'] },
  { label: 'Users',         path: '/users',         icon: '◎', roles: ['Super Admin', 'FPO Admin'] },
  { label: 'Roles',         path: '/roles',         icon: '◉', roles: ['Super Admin'] },
  { label: 'Permissions',   path: '/permissions',   icon: '◐', roles: ['Super Admin'] },
  { label: 'Farmers',       path: '/farmers',       icon: '⬟', roles: ['FPO Admin', 'Manager'] },
  { label: 'Villages',      path: '/villages',      icon: '◇', roles: ['FPO Admin', 'Manager'] },
  { label: 'Shareholders',  path: '/shareholders',  icon: '◆', roles: ['FPO Admin'] },
  { label: 'Crop Masters', path: '/crop-masters', icon: '⚜', roles: [ 'FPO Admin', 'Manager'] },
  { label: 'Farmer Crops', path: '/farmer-crops', icon: '☘', roles: [ 'FPO Admin', 'Manager', 'Accountant'] },
  { label: 'Procurement',   path: '/procurement',   icon: '⬢', roles: ['FPO Admin', 'Manager'] },
  { label: 'Inventory',     path: '/inventory',     icon: '▣', roles: ['FPO Admin'] },
  { label: 'Sales',         path: '/sales',         icon: '◆', roles: ['FPO Admin', 'Accountant'] },
  { label: 'Finance',       path: '/finance',       icon: '◐', roles: ['FPO Admin', 'Accountant'] },
  { label: 'Licenses',      path: '/licenses',      icon: '▢', roles: ['FPO Admin'] },
  { label: 'Reports',       path: '/reports',       icon: '▤', roles: ['Super Admin', 'FPO Admin', 'Manager', 'Accountant', 'Viewer'] },
  { label: 'Settings',      path: '/settings',      icon: '◌', roles: ['Super Admin', 'FPO Admin'] },

];

interface Props {
  open?: boolean;
  onClose?: () => void;
}

export default function RoleBasedSidebar({ open = false, onClose }: Props) {
  const { user } = useAuth();
  const userRole = user?.role?.name || '';
  const visibleItems = NAV_ITEMS.filter(item => item.roles.includes(userRole));

  return (
    <aside className={`sidebar${open ? ' sidebar--open' : ''}`}>
      {/* Mobile close button */}
      <button className="sidebar-close-btn" onClick={onClose} aria-label="Close menu">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>

      <div className="sidebar-logo">
        <span className="logo-mark">F</span>
        <span className="logo-text">FPO<span className="logo-accent">360</span></span>
      </div>

      <nav className="sidebar-nav">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'nav-item--active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="version-tag">Phase 1.6 · Secure</span>
      </div>
    </aside>
  );
}