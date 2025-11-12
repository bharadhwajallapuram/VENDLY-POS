import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { login } from '../../lib/api'
import { setToken } from '../../lib/auth'

export default function LoginPage(){
  const nav = useNavigate()
  const loc = useLocation() as any
  const [email, setEmail] = useState('owner@example.com')
  const [password, setPassword] = useState('owner123')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent){
    e.preventDefault(); setErr(''); setLoading(true)
    try{
      const tok = await login(email, password)
      setToken(tok.access_token)
      nav(loc.state?.from?.pathname || '/pos', { replace: true })
    }catch(ex: any){ setErr(ex.message || 'Login failed') }
    finally{ setLoading(false) }
  }

  return (
    <div className="max-w-md mx-auto mt-16 bg-white p-6 rounded-2xl shadow">
      <h1 className="text-xl font-semibold mb-4">Sign in</h1>
      <form className="space-y-3" onSubmit={onSubmit}>
        <input className="border rounded w-full p-2" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email"/>
        <input className="border rounded w-full p-2" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password"/>
        {err && <div className="text-sm text-red-600">{err}</div>}
        <button className="w-full py-2 bg-black text-white rounded" disabled={loading}>{loading? 'Signing in...' : 'Sign in'}</button>
      </form>
    </div>
  )
}