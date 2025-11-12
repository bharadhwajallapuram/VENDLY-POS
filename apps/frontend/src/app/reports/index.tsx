import { useState } from 'react'
import { api } from '../../lib/api'

export default function ReportsPage(){
  const [from, setFrom] = useState('2025-01-01T00:00:00Z')
  const [to, setTo] = useState('2030-01-01T00:00:00Z')
  const [total, setTotal] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  async function run(){
    setLoading(true)
    try{
      const res = await api<{ total_cents: number }>(`/reports/sales-summary?from_dt=${encodeURIComponent(from)}&to_dt=${encodeURIComponent(to)}`)
      setTotal(res.total_cents)
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Reports</h1>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="text-sm block">From (UTC)</label>
          <input className="border rounded p-2" value={from} onChange={e=>setFrom(e.target.value)} />
        </div>
        <div>
          <label className="text-sm block">To (UTC)</label>
          <input className="border rounded p-2" value={to} onChange={e=>setTo(e.target.value)} />
        </div>
        <button className="px-3 py-2 bg-black text-white rounded" onClick={run} disabled={loading}>{loading? 'Running...' : 'Run'}</button>
      </div>
      {total !== null && (
        <div className="p-4 border rounded bg-white">
          <div className="text-lg">Total Sales: <span className="font-semibold">${(total/100).toFixed(2)}</span></div>
        </div>
      )}
    </div>
  )
}