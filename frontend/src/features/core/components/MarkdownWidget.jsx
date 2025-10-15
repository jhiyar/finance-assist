import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function MarkdownWidget({ content, isUser = false }) {
  const markdownComponents = {
    h1: ({ children }) => <h1 className="text-xl font-bold mb-2 text-gray-900">{children}</h1>,
    h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 text-gray-800">{children}</h2>,
    h3: ({ children }) => <h3 className="text-base font-medium mb-1 text-gray-700">{children}</h3>,
    p: ({ children }) => <p className="mb-2  leading-relaxed">{children}</p>,
    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-700">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-700">{children}</ol>,
    li: ({ children }) => <li className="text-gray-700">{children}</li>,
    strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
    em: ({ children }) => <em className="italic text-gray-800">{children}</em>,
    code: ({ children }) => (
      <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    ),
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-2">
        {children}
      </blockquote>
    ),
    a: ({ href, children }) => (
      <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ),
    table: ({ children }) => (
      <div className="overflow-x-auto my-2">
        <table className="min-w-full border border-gray-300 rounded-lg">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
    tbody: ({ children }) => <tbody className="bg-white">{children}</tbody>,
    tr: ({ children }) => <tr className="border-b border-gray-200">{children}</tr>,
    th: ({ children }) => (
      <th className="px-4 py-2 text-left text-sm font-medium text-gray-900 border-r border-gray-300">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-4 py-2 text-sm text-gray-700 border-r border-gray-300">
        {children}
      </td>
    ),
  }

  // For user messages, use simpler styling
  const userMarkdownComponents = {
    ...markdownComponents,
    h1: ({ children }) => <h1 className="text-lg font-bold mb-1 text-white">{children}</h1>,
    h2: ({ children }) => <h2 className="text-base font-semibold mb-1 text-white">{children}</h2>,
    h3: ({ children }) => <h3 className="text-sm font-medium mb-1 text-white">{children}</h3>,
    p: ({ children }) => <p className="mb-1 text-white leading-relaxed">{children}</p>,
    ul: ({ children }) => <ul className="list-disc list-inside mb-1 space-y-0.5 text-white">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-inside mb-1 space-y-0.5 text-white">{children}</ol>,
    li: ({ children }) => <li className="text-white">{children}</li>,
    strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
    em: ({ children }) => <em className="italic text-white">{children}</em>,
    code: ({ children }) => (
      <code className="bg-blue-700 text-white px-1 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    ),
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-300 pl-3 italic text-blue-100 my-1">
        {children}
      </blockquote>
    ),
  }

  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={isUser ? userMarkdownComponents : markdownComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownWidget
