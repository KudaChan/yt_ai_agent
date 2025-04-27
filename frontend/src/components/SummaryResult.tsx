interface SummaryData {
  title: string
  summary: string
  key_points: string[]
  thumbnail_url?: string
}

interface SummaryResultProps {
  data: SummaryData | null
  isLoading: boolean
  error: string | null
}

export default function SummaryResult({ data, isLoading, error }: SummaryResultProps) {
  if (isLoading) {
    return (
      <div className="bg-gray-800 shadow-lg rounded-lg p-4 sm:p-6 mt-4 sm:mt-6 mb-4 sm:mb-6 w-full border border-gray-700">
        <div className="animate-pulse flex flex-col space-y-3 sm:space-y-4">
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
          <div className="h-24 sm:h-32 bg-gray-700 rounded"></div>
        </div>
        <p className="text-center mt-3 sm:mt-4 text-gray-400">Generating summary, please wait...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border-l-4 border-red-500 p-4 mt-4 sm:mt-6 mb-4 sm:mb-6 w-full rounded">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-300">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="bg-gray-800 shadow-lg rounded-lg p-4 sm:p-6 mt-4 sm:mt-6 w-full border border-gray-700">
      <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">{data.title}</h2>
      
      <div className="flex flex-col md:flex-row overflow-y-auto h-[300px] sm:h-[400px] md:h-[500px] lg:h-[600px] xl:h-[700px] 2xl:h-[800px]">
        {data.thumbnail_url && (
          <div className="md:w-1/3 mb-3 sm:mb-4 md:mb-0 md:mr-6 flex-shrink-0">
            <img 
              src={data.thumbnail_url} 
              alt={data.title} 
              className="w-full h-auto rounded"
            />
          </div>
        )}
        <div className={data.thumbnail_url ? 'md:w-2/3' : 'w-full'}>
          <div className="mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-medium text-gray-200 mb-2">Summary</h3>
            <p className="text-sm sm:text-base text-gray-300 whitespace-pre-line">{data.summary}</p>
          </div>
          
          {data.key_points && data.key_points.length > 0 && (
            <div>
              <h3 className="text-base sm:text-lg font-medium text-gray-200 mb-2">Key Points</h3>
              <ul className="list-disc pl-5 space-y-1">
                {data.key_points.map((point, index) => (
                  <li key={index} className="text-sm sm:text-base text-gray-300">{point}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
