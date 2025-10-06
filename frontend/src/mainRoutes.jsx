import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ChatInterface from './features/chat/components/ChatInterface'
import { DocumentProcessingPage, ContextPruningTestPage, DocumentReaderComparisonPage } from './features/document-processing'
import { MessageSquare, FileText, Home, Scissors, GitCompare } from 'lucide-react'

// Create a client
const queryClient = new QueryClient()

// Navigation component
const Navigation = () => {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/chat', label: 'Chat', icon: MessageSquare },
    { path: '/document-processing', label: 'Document Processing', icon: FileText },
    { path: '/context-pruning-test', label: 'Context Pruning Test', icon: Scissors },
    { path: '/document-reader-comparison', label: 'Reader Comparison', icon: GitCompare },
  ]

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Finance Assistant</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

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
  },
  {
    path: '/document-processing',
    component: DocumentProcessingPage,
    exact: true
  },
  {
    path: '/context-pruning-test',
    component: ContextPruningTestPage,
    exact: true
  },
  {
    path: '/document-reader-comparison',
    component: DocumentReaderComparisonPage,
    exact: true
  }
]

// Default route component
export default function MainRoutes() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <Routes>
            <Route path="/" element={<ChatInterface />} />
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/document-processing" element={<DocumentProcessingPage />} />
            <Route path="/context-pruning-test" element={<ContextPruningTestPage />} />
            <Route path="/document-reader-comparison" element={<DocumentReaderComparisonPage />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  )
}
