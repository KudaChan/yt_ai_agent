import { useState } from 'react'

interface SummaryFormProps {
  onSubmit: (url: string, language: string) => Promise<void>
  isLoading: boolean
}

export default function SummaryForm({ onSubmit, isLoading }: SummaryFormProps) {
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('en')
  const [urlError, setUrlError] = useState<string | null>(null)
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Basic URL validation
    if (!url.trim()) {
      setUrlError('Please enter a YouTube URL')
      return
    }
    
    // Check if it's a valid YouTube URL
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/
    if (!youtubeRegex.test(url)) {
      setUrlError('Please enter a valid YouTube URL')
      return
    }
    
    setUrlError(null)
    onSubmit(url, language)
  }
  
  return (
    <div className="w-full bg-gray-800 p-4 sm:p-6 rounded-lg shadow-lg border border-gray-700">
      <h2 className="text-xl sm:text-2xl font-bold text-white mb-4">Generate Video Summary</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-300 mb-1">
            YouTube Video URL
          </label>
          <input
            type="text"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className={`w-full px-3 py-2 bg-gray-700 border ${urlError ? 'border-red-500' : 'border-gray-600'} rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500`}
            disabled={isLoading}
          />
          {urlError && (
            <p className="mt-1 text-sm text-red-500">{urlError}</p>
          )}
        </div>
        
        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-300 mb-1">
            Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            <option value="hi">Hindi</option>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
            <option value="pt">Portuguese</option>
            <option value="ru">Russian</option>
            <option value="ja">Japanese</option>
            <option value="zh">Chinese</option>
          </select>
        </div>
        
        <button
          type="submit"
          className={`w-full py-2 px-4 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 
            ${isLoading 
              ? 'bg-gray-600 text-gray-300 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
          disabled={isLoading}
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </div>
          ) : (
            'Generate Summary'
          )}
        </button>
      </form>
    </div>
  )
}
