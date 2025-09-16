import React from 'react'

function Modal({ open, title, onClose, children, size = 'lg' }) {
  if (!open) return null
  
  const sizeClasses = {
    sm: 'max-w-lg',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl'
  }
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className={`relative z-10 w-full ${sizeClasses[size]} bg-white rounded-xl shadow-xl max-h-[90vh] overflow-hidden flex flex-col`}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button className="text-gray-500 hover:text-gray-700 text-xl" onClick={onClose}>✕</button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </div>
    </div>
  )
}

export default Modal
