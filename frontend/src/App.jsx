import React, { useEffect, useMemo, useRef, useState } from 'react'

function MessageBubble({ role, children }) {
  const isUser = role === 'user'
  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-2 whitespace-pre-wrap ${isUser ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-gray-100 text-gray-900 rounded-bl-sm'}`}>
        {children}
      </div>
    </div>
  )
}

function Modal({ open, title, onClose, children }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg bg-white rounded-xl shadow-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button className="text-gray-500 hover:text-gray-700" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

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
      const res = await fetch('/api/profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
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
        <input name="name" value={form.name} onChange={handleChange} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Address</label>
        <input name="address" value={form.address} onChange={handleChange} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input name="email" type="email" value={form.email} onChange={handleChange} className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="flex justify-end gap-2">
        <button type="submit" disabled={saving} className="rounded-md bg-blue-600 text-white px-4 py-2 disabled:opacity-50">{saving ? 'Saving…' : 'Save'}</button>
      </div>
    </form>
  )
}

export default function App() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hi! I\'m your Finance Assistant. Ask me about your balance, transactions, or update your profile.' }
  ])
  const [input, setInput] = useState('')
  const [widget, setWidget] = useState(null)
  const [profile, setProfile] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (widget?.widget === 'profile_update' && !profile) {
      fetch('/api/profile').then(r => r.json()).then(setProfile).catch(() => {})
    }
  }, [widget, profile])

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed) return
    const userMsg = { id: Date.now(), role: 'user', content: trimmed }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    try {
      const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: trimmed }) })
      const data = await res.json()
      if (data.type === 'text') {
        setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: data.text }])
      } else if (data.type === 'action' && data.actionType === 'open_widget') {
        setWidget(data)
        setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'Opening profile update widget…' }])
      } else {
        setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'Sorry, I did not understand.' }])
      }
    } catch (e) {
      setMessages(prev => [...prev, { id: Date.now() + 2, role: 'assistant', content: 'Network error. Please try again.' }])
    }
  }

  const header = useMemo(() => (
    <div className="flex items-center gap-3 p-4 border-b border-gray-200">
      <img src="https://avatars.githubusercontent.com/u/9919?s=64" alt="avatar" className="w-8 h-8 rounded-full" />
      <div>
        <div className="font-semibold">Finance Assistant Demo</div>
        <div className="text-xs text-gray-500">Ask about balance, transactions, profile</div>
      </div>
    </div>
  ), [])

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto max-w-3xl h-screen flex flex-col border-x border-gray-200 bg-white">
        {header}

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map(m => (
            <MessageBubble key={m.id} role={m.role}>{m.content}</MessageBubble>
          ))}
          <div ref={scrollRef} />
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type your message…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSend() }}
            />
            <button onClick={handleSend} className="rounded-full bg-blue-600 text-white px-5 py-2">Send</button>
          </div>
        </div>
      </div>

      <Modal open={!!widget} title={widget?.title || 'Widget'} onClose={() => setWidget(null)}>
        {widget?.widget === 'profile_update' && (
          <ProfileForm initialProfile={profile || {}} onSaved={(p) => { setProfile(p); setWidget(null); setMessages(prev => [...prev, { id: Date.now() + 3, role: 'assistant', content: 'Your profile has been updated.' }]) }} />
        )}
      </Modal>
    </div>
  )
}

