import React from 'react';
import { useEventStream } from '../hooks/useEventStream';
import { CheckCircle, XCircle, Clock, Brain } from 'lucide-react';

const PredictionTable: React.FC = () => {
  const { predictions } = useEventStream();

  const getOutcomeIcon = (outcome: string) => {
    switch (outcome) {
      case 'used':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'not_used':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getOutcomeColor = (outcome: string) => {
    switch (outcome) {
      case 'used':
        return 'text-green-700 bg-green-50';
      case 'not_used':
        return 'text-red-700 bg-red-50';
      default:
        return 'text-gray-700 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatConfidence = (score: number) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  return (
    <div className="bg-white shadow-lg rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center">
          <Brain className="w-5 h-5 text-vmm-blue mr-2" />
          <h3 className="text-lg font-semibold text-gray-800">Recent Predictions</h3>
        </div>
        <span className="text-sm text-gray-600">
          {predictions.length} predictions
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        {predictions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No predictions available yet.</p>
            <p className="text-sm">Start a simulation to see AI predictions.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Predicted Pages
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Outcome
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {predictions.map((prediction) => (
                <tr key={prediction.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {formatTimestamp(prediction.timestamp)}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex flex-wrap gap-1">
                      {prediction.predictedPages.slice(0, 5).map((page, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {page}
                        </span>
                      ))}
                      {prediction.predictedPages.length > 5 && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                          +{prediction.predictedPages.length - 5} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="space-y-1">
                      {prediction.confidenceScores.slice(0, 3).map((score, index) => (
                        <div key={index} className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-600">
                            {formatConfidence(score)}
                          </span>
                        </div>
                      ))}
                      {prediction.confidenceScores.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{prediction.confidenceScores.length - 3} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center">
                      {getOutcomeIcon(prediction.outcome)}
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getOutcomeColor(prediction.outcome)}`}>
                        {prediction.outcome.replace('_', ' ')}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer with Statistics */}
      {predictions.length > 0 && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span>
                Used: {predictions.filter(p => p.outcome === 'used').length}
              </span>
              <span>
                Not Used: {predictions.filter(p => p.outcome === 'not_used').length}
              </span>
            </div>
            <div>
              Success Rate: {predictions.length > 0 
                ? `${((predictions.filter(p => p.outcome === 'used').length / predictions.length) * 100).toFixed(1)}%`
                : '0%'
              }
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionTable;

