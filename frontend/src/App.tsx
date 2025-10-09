import React from 'react';
import ControlPanel from './components/ControlPanel';
import MetricsChart from './components/MetricsChart';
import LogPanel from './components/LogPanel';
import PredictionTable from './components/PredictionTable';
import { Monitor, Activity } from 'lucide-react';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Monitor className="w-8 h-8 text-vmm-blue mr-3" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">VMM Dashboard</h1>
                <p className="text-sm text-gray-600">Virtual Memory Manager with AI Predictor</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-600">
                <Activity className="w-4 h-4 mr-2 text-green-500" />
                <span>Real-time Monitoring</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Control Panel */}
        <ControlPanel />

        {/* Metrics Section */}
        <div className="mb-6">
          <MetricsChart />
        </div>

        {/* Bottom Section - Logs and Predictions */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Log Panel - Takes 2 columns on xl screens */}
          <div className="xl:col-span-2">
            <LogPanel />
          </div>
          
          {/* Prediction Table - Takes 1 column on xl screens */}
          <div className="xl:col-span-1">
            <PredictionTable />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              Virtual Memory Manager Dashboard
            </div>
            <div>
              Built with React, TailwindCSS & Recharts
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;

