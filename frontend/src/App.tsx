import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import MainLayout from './layouts/MainLayout';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Organizations from './pages/Organizations';
import Users from './pages/Users';
import Villages from './pages/Villages';
import Farmers from './pages/Farmers';
import Shareholders from './pages/Shareholders';
import CropMasters from './pages/CropMasters';
import FarmerCrops from './pages/FarmerCrops';
import Procurements from './pages/Procurements';
import ProcurementDetail from './pages/ProcurementDetail';

import { RoleGuard } from './components/RoleGuard';
import ProcurementReceipt from "./pages/ProcurementReceipt";
import Payments from './pages/Payments';
import PaymentDetail from './pages/PaymentDetail';
import PaymentReceipt from './pages/PaymentReceipt';
import Inventory from './pages/Inventory';
import InventoryLedger from './pages/InventoryLedger';

function ComingSoon({ page }: { page: string }) {
  return (
    <div className="page-wrapper">
      <div className="coming-soon">
        <span className="coming-soon-icon">◌</span>
        <h3>{page}</h3>
        <p>This module is coming in a future phase.</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>

          <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >

            <Route index element={<Navigate to="/dashboard" replace />} />

            <Route path="dashboard" element={<Dashboard />} />

            <Route path="organizations"
              element={
                <RoleGuard allowedRoles={['Super Admin']}>
                  <Organizations />
                </RoleGuard>
              }
            />

            <Route path="users" element={<Users />} />

            <Route path="villages" element={<Villages />} />

            <Route path="farmers" element={<Farmers />} />

            <Route path="shareholders" element={<Shareholders />} />

            <Route path="crop-masters" element={<CropMasters />} />

            <Route path="farmer-crops" element={<FarmerCrops />} />

            {/* Procurement Module */}
            <Route path="procurement" element={<Procurements />} />
            <Route path="procurement/:id" element={<ProcurementDetail />} />

            {/* Future Modules */}
            <Route path="inventory" element={<Inventory />} />
            <Route path="inventory/:cropId" element={<InventoryLedger />} />
            <Route path="sales" element={<ComingSoon page="Sales" />} />
            <Route path="finance" element={<ComingSoon page="Finance" />} />
            <Route path="licenses" element={<ComingSoon page="Licenses" />} />
            <Route path="reports" element={<ComingSoon page="Reports" />} />
            <Route path="settings" element={<ComingSoon page="Settings" />} />
            <Route path="roles" element={<ComingSoon page="Roles" />} />
            <Route path="permissions" element={<ComingSoon page="Permissions" />} />
            <Route path="procurement/:id/receipt" element={<ProcurementReceipt />}/>
            <Route path="payments" element={<Payments />} />
            <Route path="payments/:id" element={<PaymentDetail />} />
            <Route path="payments/:id/receipt" element={<PaymentReceipt />} />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}