import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../../lib/api'

export default function RegisterPage(){
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<'clerk'|'manager'|'admin'>('clerk')
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')

  async function onSubmit(e: React.FormEvent){
    e.preventDefault(); setErr(''); setOk('')
    try{
      await register({ email, password, full_name: fullName, role })
      setOk('Account created. You can sign in now.')
      setTimeout(()=> nav('/login'), 600)
    }catch(ex:any){ setErr(ex.message || 'Registration failed') }
  }

  return (
    <div className="max-w-md mx-auto mt-16 bg-white p-6 rounded-2xl shadow space-y-3">
      <h1 className="text-xl font-semibold">Create account</h1>
      <form className="space-y-3" onSubmit={onSubmit}>
        <input className="border rounded w-full p-2" placeholder="Full name" value={fullName} onChange={e=>setFullName(e.target.value)} />
        <input className="border rounded w-full p-2" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="border rounded w-full p-2" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <div>
          <label className="text-sm block mb-1">Role</label>
          <select className="border rounded p-2 w-full" value={role} onChange={(e)=>setRole(e.target.value as any)}>
            <option value="clerk">Clerk</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        {err && <div className="text-sm text-red-600">{err}</div>}
        {ok && <div className="text-sm text-green-700">{ok}</div>}
        <button className="w-full py-2 bg-black text-white rounded">Create account</button>
      </form>
      <div className="text-sm text-gray-600">Already have an account? <Link className="underline" to="/login">Sign in</Link></div>
    </div>
  )
}