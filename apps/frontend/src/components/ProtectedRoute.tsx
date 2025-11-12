import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { getToken, getUser, setUser } from '../lib/auth'
import { me } from '../lib/api'
import { useEffect, useState } from 'react'

type Role = 'clerk' | 'manager' | 'admin'

export default function ProtectedRoute({ roles }: { roles?: Role[] } = {}){
  const token = getToken()
  const loc = useLocation()
  const [ok, setOk] = useState<boolean>(!!token)

  useEffect(()=>{
    (async()=>{
      if(!token){ setOk(false); return }
      // ensure we have fresh user profile (with role)
      const cached = getUser()
      if(!cached){
        try{ const u = await me(); setUser(u) }catch{ /* ignore */ }
      }
      if(roles && roles.length){
        const u = getUser()
        if(!u || !roles.includes(u.role)) setOk(false)
        else setOk(true)
      }else{
        setOk(true)
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[])

  if(!token || !ok){
    return <Navigate to="/login" state={{ from: loc }} replace />
  }
  return <Outlet />
}