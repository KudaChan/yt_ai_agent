import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import SummaryForm from './components/SummaryForm'
import SummaryResult from './components/SummaryResult'
import { submitSummaryRequest, getSummaryStatus, getSummaryResult } from './services/api'

function App() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [summaryData, setSummaryData] = useState<any>(null)

  // Check for job status periodically if there's an active job
  useEffect(() => {
    if (!jobId) return

    const checkStatus = async () => {
      try {
        const statusData = await getSummaryStatus(jobId)
        
        if (statusData.status === 'completed') {
          const resultData = await getSummaryResult(jobId)
          setSummaryData(resultData as any)
          setIsLoading(false)
          setJobId(null)
        } else if (statusData.status === 'failed') {
          setError('Summary generation failed. Please try again.')
          setIsLoading(false)
          setJobId(null)
        }
      } catch (err) {
        setError('Error checking job status')
        setIsLoading(false)
        console.error(err)
      }
    }
    
    const intervalId = setInterval(checkStatus, 5000)
    
    return () => clearInterval(intervalId)
  }, [jobId])

  const handleSubmit = async (url: string, language: string) => {
    try {
      setIsLoading(true)
      setError(null)
      setSummaryData(null)
      
      const response = await submitSummaryRequest({
        video_url: url,
        language
      })
      
      setJobId(response.job_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred')
      setIsLoading(false)
      console.error(err)
    }
  }

  return (
    <Layout>
      <div className="flex flex-col items-center space-y-4 sm:space-y-6 max-w-6xl mx-auto">
        <SummaryForm onSubmit={handleSubmit} isLoading={isLoading} />
        <SummaryResult 
          data={summaryData} 
          isLoading={isLoading} 
          error={error} 
        />
      </div>
    </Layout>
  )
}

export default App
