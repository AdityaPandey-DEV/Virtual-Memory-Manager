import React, { useRef, useEffect } from 'react';
import { useEventStream } from '../hooks/useEventStream';
import { Play, Pause, Trash2, Wifi, WifiOff } from 'lucide-react';

const LogPanel: React.FC = () => {
  const { logs, connected, error, paused, setPaused, clearLogs } = useEventStream();
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (logContainerRef.current && !paused) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, paused]);

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'INFO':
        return 'text-gray-600';
      case 'AI':
        return 'text-blue-600';
      case 'KERNEL':
        return 'text-green-600';
      case 'WARN':
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  const getLogLevelBg = (level: string) => {
    switch (level) {
      case 'INFO':
        return 'bg-gray-50';
      case 'AI':
        return 'bg-blue-50';
      case 'KERNEL':
        return 'bg-green-50';
      case 'WARN':
        return 'bg-orange-50';
      default:
        return 'bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="bg-white shadow-lg rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-800">Live Logs</h3>
          
          {/* Connection Status */}
          <div className="flex items-center">
            {connected ? (
              <Wifi className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm ${connected ? 'text-green-600' : 'text-red-600'}`}>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPaused(!paused)}
            className={`flex items-center px-3 py-1 rounded-md text-sm ${
              paused 
                ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                : 'bg-orange-100 text-orange-700 hover:bg-orange-200'
            }`}
          >
            {paused ? (
              <>
                <Play className="w-4 h-4 mr-1" />
                Resume
              </>
            ) : (
              <>
                <Pause className="w-4 h-4 mr-1" />
                Pause
              </>
            )}
          </button>
          
          <button
            onClick={clearLogs}
            className="flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-md text-sm hover:bg-red-200"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Clear
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border-b border-red-200">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Logs Container */}
      <div 
        ref={logContainerRef}
        className="h-64 overflow-y-auto p-4 font-mono text-sm"
        style={{ scrollBehavior: 'smooth' }}
      >
        {logs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No logs available. Start a simulation to see live events.</p>
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log) => (
              <div
                key={log.id}
                className={`p-2 rounded border-l-4 ${
                  log.level === 'INFO' ? 'border-gray-300' :
                  log.level === 'AI' ? 'border-blue-300' :
                  log.level === 'KERNEL' ? 'border-green-300' :
                  'border-orange-300'
                } ${getLogLevelBg(log.level)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`font-semibold ${getLogLevelColor(log.level)}`}>
                        [{log.level}]
                      </span>
                      <span className="text-gray-500 text-xs">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                    <div className="text-gray-800 break-words">
                      {log.message}
                    </div>
                    {log.data && (
                      <div className="mt-1 text-xs text-gray-600">
                        {JSON.stringify(log.data, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-600">
        <span>
          {logs.length} log entries
        </span>
        <span>
          {paused ? 'Paused' : 'Live streaming'}
        </span>
      </div>
    </div>
  );
};

export default LogPanel;

