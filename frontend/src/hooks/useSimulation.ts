import { useState, useCallback } from 'react';
import { SimulationStatus } from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';

export const useSimulation = () => {
  const [status, setStatus] = useState<SimulationStatus>({
    isRunning: false,
    mode: 'ai_off',
    workload: 'random',
    backendHealth: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkBackendHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/metrics`);
      const isHealthy = response.ok;
      setStatus(prev => ({ ...prev, backendHealth: isHealthy }));
      return isHealthy;
    } catch (err) {
      setStatus(prev => ({ ...prev, backendHealth: false }));
      return false;
    }
  }, []);

  const startSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    console.log('Starting simulation with:', { mode: status.mode, workload: status.workload });
    
    try {
      const response = await fetch(`${API_BASE}/simulate/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mode: status.mode,
          workload: status.workload
        })
      });
      
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Failed to start simulation: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('Success response:', result);
      setStatus(prev => ({ ...prev, isRunning: true }));
    } catch (err) {
      console.error('Start simulation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to start simulation');
    } finally {
      setLoading(false);
    }
  }, [status.mode, status.workload]);

  const stopSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    console.log('Stopping simulation');
    
    try {
      const response = await fetch(`${API_BASE}/simulate/stop`, {
        method: 'POST'
      });
      
      console.log('Stop response status:', response.status);
      console.log('Stop response ok:', response.ok);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Stop error response:', errorText);
        throw new Error(`Failed to stop simulation: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('Stop success response:', result);
      setStatus(prev => ({ ...prev, isRunning: false }));
    } catch (err) {
      console.error('Stop simulation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to stop simulation');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateMode = useCallback((mode: SimulationStatus['mode']) => {
    setStatus(prev => ({ ...prev, mode }));
  }, []);

  const updateWorkload = useCallback((workload: SimulationStatus['workload']) => {
    setStatus(prev => ({ ...prev, workload }));
  }, []);

  return {
    status,
    loading,
    error,
    startSimulation,
    stopSimulation,
    updateMode,
    updateWorkload,
    checkBackendHealth
  };
};

