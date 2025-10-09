import { useState, useEffect, useCallback } from 'react';
import { Metrics, TimeSeriesData } from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';

export const useMetrics = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/metrics`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      const newMetrics: Metrics = {
        totalPageAccesses: data.total_accesses || 0,
        pageFaultsBaseline: data.page_faults || 0,
        pageFaultsAI: data.page_faults || 0,
        pageFaultRate: data.page_fault_rate || 0,
        swapIOThroughput: (data.swap_ins || 0) + (data.swap_outs || 0),
        predictorCPU: data.ai_prediction_confidence ? data.ai_prediction_confidence * 100 : 0,
        predictorLatency: 0,
        precisionAtK: data.ai_hit_rate || 0,
        recall: data.ai_hit_rate || 0,
        timestamp: new Date().toISOString()
      };

      setMetrics(newMetrics);
      
      // Add to time series data
      setTimeSeriesData(prev => {
        const newData: TimeSeriesData = {
          timestamp: newMetrics.timestamp,
          pageFaultRateBaseline: newMetrics.pageFaultRate,
          pageFaultRateAI: newMetrics.pageFaultRate,
          precisionAt5: newMetrics.precisionAtK,
          recall: newMetrics.recall,
          swapThroughput: newMetrics.swapIOThroughput
        };
        
        const updated = [...prev, newData];
        // Keep only last 50 data points
        return updated.slice(-50);
      });
      
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
      console.error('Error fetching metrics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    
    // Poll every 5 seconds
    const interval = setInterval(fetchMetrics, 5000);
    
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  return {
    metrics,
    timeSeriesData,
    loading,
    error,
    refetch: fetchMetrics
  };
};

