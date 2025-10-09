import React from 'react';
import { Play, Square, Settings, Activity, AlertCircle } from 'lucide-react';
import { useSimulation } from '../hooks/useSimulation';

const ControlPanel: React.FC = () => {
  const {
    status,
    loading,
    error,
    startSimulation,
    stopSimulation,
    updateMode,
    updateWorkload,
    checkBackendHealth
  } = useSimulation();

  const modeOptions = [
    { value: 'ai_off', label: 'AI Off' },
    { value: 'prefetch_only', label: 'Prefetch Only' },
    { value: 'eviction_hints', label: 'Eviction Hints' },
    { value: 'hybrid', label: 'Hybrid' }
  ];

  const workloadOptions = [
    { value: 'sequential', label: 'Sequential' },
    { value: 'random', label: 'Random' },
    { value: 'strided', label: 'Strided' },
    { value: 'db_like', label: 'DB-like' }
  ];

  React.useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 10000);
    return () => clearInterval(interval);
  }, [checkBackendHealth]);

  return (
    <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800 flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Control Panel
        </h2>
        
        <div className="flex items-center space-x-4">
          {/* Backend Health Indicator */}
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${
              status.backendHealth ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-gray-600">
              {status.backendHealth ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div>
          
          {/* Simulation Status */}
          <div className="flex items-center">
            <Activity className={`w-4 h-4 mr-2 ${
              status.isRunning ? 'text-green-500' : 'text-gray-400'
            }`} />
            <span className="text-sm text-gray-600">
              {status.isRunning ? 'Simulation Running' : 'Simulation Stopped'}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center">
          <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
          <span className="text-red-700 text-sm">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Start/Stop Controls */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Simulation Control</label>
          <div className="flex space-x-2">
            <button
              onClick={startSimulation}
              disabled={loading || status.isRunning}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4 mr-2" />
              Start
            </button>
            <button
              onClick={stopSimulation}
              disabled={loading || !status.isRunning}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </button>
          </div>
        </div>

        {/* Mode Selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">AI Mode</label>
          <select
            value={status.mode}
            onChange={(e) => updateMode(e.target.value as any)}
            disabled={status.isRunning}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-vmm-blue disabled:opacity-50"
          >
            {modeOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Workload Selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Workload Type</label>
          <select
            value={status.workload}
            onChange={(e) => updateWorkload(e.target.value as any)}
            disabled={status.isRunning}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-vmm-blue disabled:opacity-50"
          >
            {workloadOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

