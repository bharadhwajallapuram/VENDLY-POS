import { useAuth } from '../../contexts/AuthContext'

export default function SettingsPage(){
  const { user } = useAuth()
  
  return (
    <div className="space-y-6">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h1 className="text-xl font-semibold text-red-800">⚙️ Admin Settings</h1>
        <p className="text-red-600 mt-2">
          <strong>🔒 Admin Access Only</strong> - Only administrators can access this page.
        </p>
        <p className="text-sm text-red-500 mt-1">
          Current user: <strong>{user?.email}</strong> ({user?.role})
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">🏪 Store Configuration</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Store name and address</li>
            <li>• Tax rates and settings</li>
            <li>• Receipt templates</li>
            <li>• Payment methods</li>
          </ul>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">👥 User Management</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Add/remove users</li>
            <li>• Manage roles & permissions</li>
            <li>• Reset passwords</li>
            <li>• View user activity</li>
          </ul>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">🔧 System Settings</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Database backup/restore</li>
            <li>• API configurations</li>
            <li>• Security settings</li>
            <li>• System logs</li>
          </ul>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">📊 Analytics</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Sales analytics</li>
            <li>• User performance</li>
            <li>• System health</li>
            <li>• Custom reports</li>
          </ul>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">🔄 Integrations</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Payment gateways</li>
            <li>• Inventory systems</li>
            <li>• Accounting software</li>
            <li>• Third-party APIs</li>
          </ul>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">🛡️ Security</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Access controls</li>
            <li>• Audit trails</li>
            <li>• Data encryption</li>
            <li>• Compliance settings</li>
          </ul>
        </div>
      </div>
    </div>
  )
}