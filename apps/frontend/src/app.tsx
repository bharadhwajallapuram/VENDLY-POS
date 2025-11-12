import { Routes, Route, Navigate } from 'react-router-dom'
import Nav from './components/Nav'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './app/login'
import RegisterPage from './app/register'
import POSPage from './app/pos'
import ProductsPage from './app/products'
import InventoryPage from './app/inventory'
import CustomersPage from './app/customers'
import ReportsPage from './app/reports'
import SettingsPage from './app/settings'

export default function App(){
  return (
    <div className="min-h-dvh">
      <Nav />
      <div className="max-w-6xl mx-auto py-6 px-4">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Anyone signed in */}
          <Route element={<ProtectedRoute />}> 
            <Route path="/pos" element={<POSPage />} />
          </Route>

          {/* Manager+ */}
          <Route element={<ProtectedRoute roles={["manager","admin"]} />}> 
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>

          {/* Admin only */}
          <Route element={<ProtectedRoute roles={["admin"]} />}> 
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          <Route path="/" element={<Navigate to="/pos" replace />} />
          <Route path="*" element={<Navigate to="/pos" replace />} />
        </Routes>
      </div>
    </div>
  )
}