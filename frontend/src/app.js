import React, { useState, useEffect } from 'react';
import AnalysisForm from './components/AnalysisForm';
import ResultsDisplay from './components/ResultsDisplay';
import { submitAnalysis, getAnalysis } from './services/api';
import './index.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [error, setError] = useState('');

  const handleSubmitAnalysis = async (postUrl) => {
    setLoading(true);
    setError('');
    setCurrentAnalysis(null);

    try {
      const response = await submitAnalysis(postUrl);

      // Start polling for results
      pollAnalysisResults(response.analysis_id);

    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit analysis');
      setLoading(false);
    }
  };

  const pollAnalysisResults = (analysisId) => {
    const pollInterval = setInterval(async () => {
      try {
        const analysis = await getAnalysis(analysisId);
        setCurrentAnalysis(analysis);

        // Stop polling if completed or failed
        if (analysis.status === 'completed' || analysis.status === 'failed') {
          clearInterval(pollInterval);
          setLoading(false);
        }

      } catch (err) {
        console.error('Polling error:', err);
        clearInterval(pollInterval);
        setError('Failed to get analysis results');
        setLoading(false);
      }
    }, 2000); // Poll every 2 seconds

    // Set initial analysis state
    setCurrentAnalysis({
      id: analysisId,
      status: 'pending',
      created_at: new Date().toISOString()
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Instagram Sentiment Analyzer
          </h1>
          <p className="text-gray-600">
            Analyze the sentiment of comments on Instagram posts
          </p>
        </div>

        <AnalysisForm onSubmit={handleSubmitAnalysis} loading={loading} />

        {error && (
          <div className="max-w-md mx-auto mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {currentAnalysis && (
          <ResultsDisplay analysis={currentAnalysis} />
        )}
      </div>
    </div>
  );
}

export default App;