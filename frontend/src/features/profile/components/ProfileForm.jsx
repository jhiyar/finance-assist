import React, { useState } from 'react'
import { API_BASE_URL } from '../../../config/api.js'

function ProfileForm({ initialProfile, onSaved }) {
  const [form, setForm] = useState(() => ({ name: '', address: '', email: '', ...initialProfile }))
  const [saving, setSaving] = useState(false)
  
  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const res = await fetch(`${API_BASE_URL}/profile`, { 
        method: 'PATCH', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(form) 
      })
      const data = await res.json()
      onSaved?.(data)
    } finally {
      setSaving(false)
    }
  }
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Name</label>
        <input 
          name="name" 
          value={form.name} 
          onChange={handleChange} 
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Address</label>
        <input 
          name="address" 
          value={form.address} 
          onChange={handleChange} 
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input 
          name="email" 
          type="email" 
          value={form.email} 
          onChange={handleChange} 
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
        />
      </div>
      <div className="flex justify-end gap-2">
        <button 
          type="submit" 
          disabled={saving} 
          className="rounded-md bg-blue-600 text-white px-4 py-2 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  )
}

export default ProfileForm
