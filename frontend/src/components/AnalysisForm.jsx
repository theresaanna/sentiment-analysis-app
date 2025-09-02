import React, { useState } from 'react';

const AnalysisForm = ({ onSubmit, loading }) => {
  const [postUrl, setPostUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!postUrl.trim()) {
      setError('Please enter an Instagram post URL');
      return;
    }

    // Basic URL validation
    const instagramUrlPattern = /https?:\/\/(www\.)?(instagram\.com|instagr\.am)\/p\/[A-Za-z0-9_-]+\/?/;
    if (!instagramUrlPattern.test(postUrl)) {
      setError('Please enter a valid Instagram post URL');
      return;
    }

    await onSubmit(postUrl.trim());
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">Instagram Sentiment Analysis</h2>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="postUrl" className="block text-sm font-medium text-gray-700 mb-2">
            Instagram Post URL
          </label>
          <input
            type="url"
            id="postUrl"
            value={postUrl}
            onChange={(e) => setPostUrl(e.target.value)}
            placeholder="https://www.instagram.com/p/..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="mb-4 text-red-600 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Analyzing...' : 'Analyze Sentiment'}
        </button>
      </form>
    </div>
  );
};

export default AnalysisForm;