import React from 'react';
import StatusIndicator from './StatusIndicator';

const ResultsDisplay = ({ analysis }) => {
  if (!analysis) return null;

  const { results, status, post_url, created_at } = analysis;

  return (
    <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md mt-6">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Analysis Results</h3>
          <StatusIndicator status={status} />
        </div>
        <p className="text-sm text-gray-600 mt-1">
          URL: {post_url}
        </p>
        <p className="text-xs text-gray-500">
          Started: {new Date(created_at).toLocaleString()}
        </p>
      </div>

      {status === 'processing' && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing comments...</p>
        </div>
      )}

      {status === 'failed' && (
        <div className="text-center py-8 text-red-600">
          <p>Analysis failed. Please try again later.</p>
        </div>
      )}

      {status === 'completed' && results && (
        <div className="space-y-6">
          {/* Sentiment Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-semibold text-green-800">Positive</h4>
              <p className="text-2xl font-bold text-green-600">
                {results.sentiment_breakdown?.positive || 0}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <h4 className="font-semibold text-red-800">Negative</h4>
              <p className="text-2xl font-bold text-red-600">
                {results.sentiment_breakdown?.negative || 0}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-800">Neutral</h4>
              <p className="text-2xl font-bold text-gray-600">
                {results.sentiment_breakdown?.neutral || 0}
              </p>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">Summary</h4>
            <p>Total Comments: <span className="font-medium">{results.total_comments}</span></p>
            <p>Average Sentiment: <span className="font-medium">{(results.average_sentiment * 100).toFixed(1)}%</span></p>
          </div>

          {/* Top Keywords */}
          {results.top_keywords && results.top_keywords.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Top Keywords</h4>
              <div className="flex flex-wrap gap-2">
                {results.top_keywords.map((keyword, index) => (
                  <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sample Comments */}
          {results.comments_sample && results.comments_sample.length > 0 && (
            <div>
              <h4 className="font-semibold mb-2">Sample Comments</h4>
              <div className="space-y-2">
                {results.comments_sample.map((comment, index) => (
                  <div key={index} className="border-l-4 border-gray-200 pl-4 py-2">
                    <p className="text-sm">{comment.text}</p>
                    <div className="flex items-center mt-1 text-xs text-gray-500">
                      <span className={`font-medium ${
                        comment.sentiment === 'positive' ? 'text-green-600' :
                        comment.sentiment === 'negative' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {comment.sentiment}
                      </span>
                      <span className="ml-2">
                        ({(comment.confidence * 100).toFixed(1)}% confidence)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;