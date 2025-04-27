import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen max-h-screen flex flex-col overflow-hidden bg-gradient-to-br from-gray-900 to-gray-800">
      <header className="bg-gray-800 shadow-lg border-b border-gray-700 flex-shrink-0">
        <div className="max-w-7xl mx-auto py-3 px-4 sm:px-6 lg:px-8">
          <h1 className="text-xl sm:text-2xl font-bold text-white">YouTube Summarizer</h1>
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        <div className="max-w-7xl mx-auto h-full px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
          {children}
        </div>
      </main>
    </div>
  )
}
