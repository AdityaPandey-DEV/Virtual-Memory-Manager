import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useMetrics } from '../hooks/useMetrics';
import { TrendingUp, Cpu, HardDrive, Target } from 'lucide-react';

const MetricsChart: React.FC = () => {
  const { metrics, timeSeriesData, loading, error } = useMetrics();

  if (loading && !metrics) {
    return (
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="text-center text-red-600">
          <p>Failed to load metrics: {error}</p>
        </div>
      </div>
    );
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatThroughput = (value: number) => `${value.toFixed(2)} MB/s`;

  return (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white shadow-lg rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Page Fault Rate</p>
              <p className="text-2xl font-bold text-vmm-blue">
                {metrics ? formatPercentage(metrics.pageFaultRate) : '0%'}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-vmm-blue" />
          </div>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Predictor CPU</p>
              <p className="text-2xl font-bold text-vmm-green">
                {metrics ? `${metrics.predictorCPU.toFixed(1)}%` : '0%'}
              </p>
            </div>
            <Cpu className="w-8 h-8 text-vmm-green" />
          </div>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Swap I/O</p>
              <p className="text-2xl font-bold text-vmm-orange">
                {metrics ? formatThroughput(metrics.swapIOThroughput) : '0 MB/s'}
              </p>
            </div>
            <HardDrive className="w-8 h-8 text-vmm-orange" />
          </div>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Precision@K</p>
              <p className="text-2xl font-bold text-vmm-gray">
                {metrics ? formatPercentage(metrics.precisionAtK) : '0%'}
              </p>
            </div>
            <Target className="w-8 h-8 text-vmm-gray" />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Page Fault Rate Over Time */}
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Page Fault Rate Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={formatTime}
                fontSize={12}
              />
              <YAxis 
                tickFormatter={formatPercentage}
                fontSize={12}
              />
              <Tooltip 
                labelFormatter={(value) => `Time: ${formatTime(value)}`}
                formatter={(value: number) => [formatPercentage(value), '']}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="pageFaultRateBaseline" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="Baseline"
              />
              <Line 
                type="monotone" 
                dataKey="pageFaultRateAI" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="AI-Assisted"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Prediction Performance */}
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Prediction Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={formatTime}
                fontSize={12}
              />
              <YAxis 
                tickFormatter={formatPercentage}
                fontSize={12}
              />
              <Tooltip 
                labelFormatter={(value) => `Time: ${formatTime(value)}`}
                formatter={(value: number) => [formatPercentage(value), '']}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="precisionAt5" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Precision@5"
              />
              <Line 
                type="monotone" 
                dataKey="recall" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Recall"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Swap I/O Throughput */}
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Swap I/O Throughput</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timeSeriesData.slice(-20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={formatTime}
                fontSize={12}
              />
              <YAxis 
                tickFormatter={formatThroughput}
                fontSize={12}
              />
              <Tooltip 
                labelFormatter={(value) => `Time: ${formatTime(value)}`}
                formatter={(value: number) => [formatThroughput(value), 'Throughput']}
              />
              <Bar dataKey="swapThroughput" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Performance Comparison */}
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Performance Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Baseline Faults', value: metrics?.pageFaultsBaseline || 0, color: '#ef4444' },
                  { name: 'AI Faults', value: metrics?.pageFaultsAI || 0, color: '#3b82f6' }
                ]}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {[
                  { name: 'Baseline Faults', value: metrics?.pageFaultsBaseline || 0, color: '#ef4444' },
                  { name: 'AI Faults', value: metrics?.pageFaultsAI || 0, color: '#3b82f6' }
                ].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default MetricsChart;

