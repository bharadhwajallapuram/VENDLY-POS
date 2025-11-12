import { Link, NavLink, useNavigate } from 'react-router-dom'
import { getToken, clearToken, getUser } from '../lib/auth'

export default function Nav(){
  const nav = useNavigate()
  const authed = !!getToken()
  const user = getUser()
  const role = user?.role as 'clerk'|'manager'|'admin'|undefined
  return (
    <header className="border-b bg-white">
      <nav className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link to="/pos" className="font-semibold">Vendly POS</Link>
        {authed && (
          <div className="flex items-center gap-4 text-sm">
            <NavLink to="/pos" className={({isActive})=> isActive? 'font-medium' : ''}>POS</NavLink>
            {(role==='manager' || role==='admin') && (
              <NavLink to="/products" className={({isActive})=> isActive? 'font-medium' : ''}>Products</NavLink>
            )}
            {(role==='manager' || role==='admin') && (
              <NavLink to="/inventory" className={({isActive})=> isActive? 'font-medium' : ''}>Inventory</NavLink>
            )}
            {role==='admin' && (
              <NavLink to="/customers" className={({isActive})=> isActive? 'font-medium' : ''}>Customers</NavLink>
            )}
            {(role==='manager' || role==='admin') && (
              <NavLink to="/reports" className={({isActive})=> isActive? 'font-medium' : ''}>Reports</NavLink>
            )}
            {role==='admin' && (
              <NavLink to="/settings" className={({isActive})=> isActive? 'font-medium' : ''}>Settings</NavLink>
            )}
          </div>
        )}
        <div className="ml-auto flex items-center gap-3">
          {authed ? (
            <>
              <span className="text-xs text-gray-600">{user?.email} {role && `· ${role}`}</span>
              <button className="text-sm underline" onClick={()=>{ clearToken(); nav('/login'); }}>Logout</button>
            </>
          ) : (
            <>
              <Link className="text-sm underline" to="/login">Login</Link>
              <Link className="text-sm underline" to="/register">Register</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}