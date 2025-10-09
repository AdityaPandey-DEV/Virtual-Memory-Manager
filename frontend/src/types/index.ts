export interface Metrics {
  totalPageAccesses: number;
  pageFaultsBaseline: number;
  pageFaultsAI: number;
  pageFaultRate: number;
  swapIOThroughput: number;
  predictorCPU: number;
  predictorLatency: number;
  precisionAtK: number;
  recall: number;
  timestamp: string;
}

export interface LogEvent {
  id: string;
  timestamp: string;
  level: 'INFO' | 'AI' | 'KERNEL' | 'WARN';
  message: string;
  data?: any;
}

export interface Prediction {
  id: string;
  timestamp: string;
  predictedPages: number[];
  confidenceScores: number[];
  outcome: 'used' | 'not_used';
  actualPages?: number[];
}

export interface SimulationStatus {
  isRunning: boolean;
  mode: 'ai_off' | 'prefetch_only' | 'eviction_hints' | 'hybrid';
  workload: 'sequential' | 'random' | 'strided' | 'db_like';
  backendHealth: boolean;
}

export interface TimeSeriesData {
  timestamp: string;
  pageFaultRateBaseline: number;
  pageFaultRateAI: number;
  precisionAt5: number;
  recall: number;
  swapThroughput: number;
}

