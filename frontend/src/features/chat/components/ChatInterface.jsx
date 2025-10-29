import React, { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import RAGDetailsModal from './RAGDetailsModal'
import Modal from '../../core/components/Modal'
import ProfileForm from '../../profile/components/ProfileForm'
import { API_BASE_URL } from '../../../config/api.js'

function ChatInterface() {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      role: 'assistant', 
      content: '## Hi! I\'m your Finance Assistant\n\nI can help you with:\n\n- **Account Information**: Check your balance and transaction history\n- **Profile Management**: Update your personal details\n- **Financial Products**: Answer questions about loans, bridging loans, and other financial services\n- **Document Analysis**: Provide detailed explanations from financial documents\n\nAsk me anything! 🚀' 
    }
  ])
  const [input, setInput] = useState('')
  const [widget, setWidget] = useState(null)
  const [profile, setProfile] = useState(null)
  const [ragModalOpen, setRagModalOpen] = useState(false)
  const [selectedRAGDetails, setSelectedRAGDetails] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (widget?.widget === 'profile_update' && !profile) {
      fetch(`${API_BASE_URL}/profile`).then(r => r.json()).then(setProfile).catch(() => {})
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
      const res = await fetch(`${API_BASE_URL}/chat`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ 
          message: trimmed, 
          retriever_type: 'hybrid_search' //  agentic_rag, hybrid_search
        }) 
      })
      const data = await res.json()
      if (data.type === 'text') {
        const assistantMsg = { 
          id: Date.now() + 1, 
          role: 'assistant', 
          content: data.text,
          ragDetails: data.confidence !== undefined ? {
            confidence: data.confidence,
            citations: data.citations,
            sources_used: data.sources_used,
            rag_details: data.rag_details,
            source: data.source
          } : null
        }
        setMessages(prev => [...prev, assistantMsg])
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

  const handleShowRAGDetails = (ragDetails) => {
    setSelectedRAGDetails(ragDetails)
    setRagModalOpen(true)
  }

  const header = (
    <div className="flex items-center gap-3 p-4 border-b border-gray-200">
      <img src="https://avatars.githubusercontent.com/u/9919?s=64" alt="avatar" className="w-8 h-8 rounded-full" />
      <div>
        <div className="font-semibold">Finance Assistant with RAG</div>
        <div className="text-xs text-gray-500">Ask about balance, transactions, profile, or financial products</div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto max-w-3xl h-screen flex flex-col border-x border-gray-200 bg-white">
        {header}

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map(m => (
            <MessageBubble 
              key={m.id} 
              role={m.role}
              ragDetails={m.ragDetails}
              onShowRAGDetails={handleShowRAGDetails}
            >
              {m.content}
            </MessageBubble>
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
          <ProfileForm 
            initialProfile={profile || {}} 
            onSaved={(p) => { 
              setProfile(p); 
              setWidget(null); 
              setMessages(prev => [...prev, { 
                id: Date.now() + 3, 
                role: 'assistant', 
                content: 'Your profile has been updated.' 
              }]) 
            }} 
          />
        )}
      </Modal>

      <RAGDetailsModal 
        open={ragModalOpen} 
        onClose={() => setRagModalOpen(false)} 
        ragDetails={selectedRAGDetails} 
      />
    </div>
  )
}

export default ChatInterface
