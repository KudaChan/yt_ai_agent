import { useState } from 'react'

interface SummaryFormProps {
  onSubmit: (url: string, language: string) => Promise<void>
  isLoading: boolean
}

export default function SummaryForm({ onSubmit, isLoading }: SummaryFormProps) {
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('hi')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      await onSubmit(url, language)
    }
  }

  return (
    <div className="bg-gray-800 shadow-lg rounded-lg p-4 sm:p-6 mb-4 sm:mb-6 w-full border border-gray-700">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="url" className="block text-lg font-medium text-gray-300">
            YouTube Video URL
          </label>
          <input
            type="url"
            id="url"
            className="mt-1 h-12 p-2 text-md block w-full rounded-md bg-gray-700 border-gray-600 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="language" className="block text-lg font-medium text-gray-300">
            Summary Language
          </label>
          <select
            id="language"
            className="mt-1 h-12 p-2 text-md block w-full rounded-md bg-gray-700 border-gray-600 text-white shadow-sm focus:border-purple-500 focus:ring-purple-500"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="hi">Hindi</option>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="pt">Portuguese</option>
            <option value="ru">Russian</option>
          </select>
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white ${
            isLoading ? 'bg-purple-700' : 'bg-purple-600 hover:bg-purple-500'
          } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500`}
        >
          {isLoading ? 'Processing...' : 'Generate Summary'}
        </button>
      </form>
    </div>
  )
}
