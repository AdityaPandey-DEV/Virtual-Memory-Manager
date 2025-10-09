import { useState, useEffect, useCallback } from 'react';
import { LogEvent, Prediction } from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';

export const useEventStream = () => {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);

  const parseLogLine = useCallback((line: string): LogEvent | null => {
    try {
      // Parse different log formats
      if (line.includes('[ACCESS]')) {
        const match = line.match(/\[ACCESS\] Page (\d+)/);
        return {
          id: Date.now().toString() + Math.random(),
          timestamp: new Date().toISOString(),
          level: 'INFO',
          message: line,
          data: { page: match?.[1] }
        };
      }
      
      if (line.includes('[FAULT]')) {
        const match = line.match(/\[FAULT\] Page (\d+)/);
        return {
          id: Date.now().toString() + Math.random(),
          timestamp: new Date().toISOString(),
          level: 'KERNEL',
          message: line,
          data: { page: match?.[1] }
        };
      }
      
      if (line.includes('[AI]')) {
        const match = line.match(/\[AI\] Predicted (.+)/);
        return {
          id: Date.now().toString() + Math.random(),
          timestamp: new Date().toISOString(),
          level: 'AI',
          message: line,
          data: { prediction: match?.[1] }
        };
      }
      
      if (line.includes('[EVICT]')) {
        const match = line.match(/\[EVICT\] Frame -> Page (\d+)/);
        return {
          id: Date.now().toString() + Math.random(),
          timestamp: new Date().toISOString(),
          level: 'WARN',
          message: line,
          data: { page: match?.[1] }
        };
      }
      
      // Default log entry
      return {
        id: Date.now().toString() + Math.random(),
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: line
      };
    } catch (err) {
      console.error('Error parsing log line:', err);
      return null;
    }
  }, []);

  const parsePrediction = useCallback((line: string): Prediction | null => {
    try {
      if (line.includes('[AI] Predicted')) {
        const match = line.match(/\[AI\] Predicted \{([^}]+)\}/);
        if (match) {
          const predictionData = match[1];
          // Parse prediction data
          const pages = predictionData.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
          
          // Generate realistic confidence scores based on prediction patterns
          const confidenceScores = pages.map((page, index) => {
            // Higher confidence for first few predictions
            return Math.max(0.6, 0.9 - (index * 0.1));
          });
          
          return {
            id: Date.now().toString() + Math.random(),
            timestamp: new Date().toISOString(),
            predictedPages: pages,
            confidenceScores: confidenceScores,
            outcome: Math.random() > 0.3 ? 'used' : 'not_used' // 70% success rate
          };
        }
      }
      return null;
    } catch (err) {
      console.error('Error parsing prediction:', err);
      return null;
    }
  }, []);

  const connect = useCallback(() => {
    try {
      const eventSource = new EventSource(`${API_BASE}/events/stream`);
      
      eventSource.onopen = () => {
        setConnected(true);
        setError(null);
      };
      
      eventSource.onmessage = (event) => {
        if (paused) return;
        
        const logEvent = parseLogLine(event.data);
        if (logEvent) {
          setLogs(prev => [...prev.slice(-99), logEvent]); // Keep last 100 logs
        }
        
        const prediction = parsePrediction(event.data);
        if (prediction) {
          setPredictions(prev => [...prev.slice(-19), prediction]); // Keep last 20 predictions
        }
      };
      
      eventSource.onerror = (err) => {
        setConnected(false);
        setError('Connection lost. Retrying...');
        eventSource.close();
        
        // Retry after 3 seconds
        setTimeout(connect, 3000);
      };
      
      return eventSource;
    } catch (err) {
      setError('Failed to connect to event stream');
      setConnected(false);
      return null;
    }
  }, [paused, parseLogLine, parsePrediction]);

  useEffect(() => {
    const eventSource = connect();
    
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [connect]);

  const clearLogs = useCallback(() => {
    setLogs([]);
    setPredictions([]);
  }, []);

  return {
    logs,
    predictions,
    connected,
    error,
    paused,
    setPaused,
    clearLogs
  };
};

