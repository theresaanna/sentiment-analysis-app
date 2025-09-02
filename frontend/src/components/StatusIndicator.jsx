import React from 'react';

const StatusIndicator = ({ status }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'pending':
        return { color: 'text-yellow-600', bg: 'bg-yellow-100', text: 'Queued' };
      case 'processing':
        return { color: 'text-blue-600', bg: 'bg-blue-100', text: 'Processing...' };
      case 'completed':
        return { color: 'text-green-600', bg: 'bg-green-100', text: 'Completed' };
      case 'failed':
        return { color: 'text-red-600', bg: 'bg-red-100', text: 'Failed' };
      default:
        return { color: 'text-gray-600', bg: 'bg-gray-100', text: 'Unknown' };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
      {config.text}
    </span>
  );
};

export default StatusIndicator;