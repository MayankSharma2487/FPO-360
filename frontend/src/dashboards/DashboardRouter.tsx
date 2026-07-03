import { useAuth } from '../context/AuthContext'
import SuperAdminDashboard from './SuperAdminDashboard'
import FPOAdminDashboard from './FPOAdminDashboard'
import ManagerDashboard from './ManagerDashboard'
import AccountantDashboard from './AccountantDashboard'
import ViewerDashboard from './ViewerDashboard'

export default function DashboardRouter() {
  const { user } = useAuth()

  if (!user || !user.role) {
    return <div className="error-banner">Unable to load dashboard.</div>
  }

  const role = user.role.name

  switch (role) {
    case 'Super Admin':
      return <SuperAdminDashboard />
    case 'FPO Admin':
      return <FPOAdminDashboard />
    case 'Manager':
      return <ManagerDashboard />
    case 'Accountant':
      return <AccountantDashboard />
    case 'Viewer':
      return <ViewerDashboard />
    default:
      return <div className="error-banner">Dashboard not configured for this role.</div>
  }
}