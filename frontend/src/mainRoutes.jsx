import React from 'react'
import ChatInterface from './features/chat/components/ChatInterface'

// Main routes configuration
export const routes = [
  {
    path: '/',
    component: ChatInterface,
    exact: true
  },
  {
    path: '/chat',
    component: ChatInterface,
    exact: true
  }
]

// Default route component
export default function MainRoutes() {
  return <ChatInterface />
}
