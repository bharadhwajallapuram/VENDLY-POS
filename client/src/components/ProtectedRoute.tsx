import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { me } from '../lib/api'
import { useEffect, useState } from 'react'

type Role = 'cashier' | 'manager' | 'admin'

export default function ProtectedRoute({ roles }: { roles?: Role[] } = {}){
  const { token, user, setUser } = useAuth()
  const loc = useLocation()
  const [ok, setOk] = useState<boolean>(!!token)

  useEffect(()=>{
    (async()=>{
      if(!token){ setOk(false); return }
      // ensure we have fresh user profile (with role)
      if(!user){
        try{ 
          const u = await me(); 
          setUser({
            email: u.email,
            role: u.role as 'cashier'|'manager'|'admin',
            full_name: u.full_name
          })
        }catch{ /* ignore */ }
      }
      if(roles && roles.length){
        if(!user || !roles.includes(user.role)) setOk(false)
        else setOk(true)
      }else{
        setOk(true)
      }
    })()
  },[token, user, roles, setUser])

  if(!token || !ok){
    return <Navigate to="/login" state={{ from: loc }} replace />
  }
  return <Outlet />
}