// Core application types
export interface User {
  id: string;
  email: string;
  displayName?: string;
  photoURL?: string;
  createdAt: Date;
  settings: UserSettings;
}

export interface UserSettings {
  defaultResolution: string;
  defaultFPS: number;
  defaultBPM: number;
  notifications: {
    processingComplete: boolean;
    weeklyAnalytics: boolean;
    systemUpdates: boolean;
  };
}

// Komposition types (compatible with Elm structure)
export interface Komposition {
  id: string;
  name: string;
  revision: string;
  dvlType: string;
  bpm: number;
  segments: Segment[];
  sources: Source[];
  config: VideoConfig;
  status: 'draft' | 'processing' | 'completed' | 'error';
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  beatpattern?: BeatPattern;
}

export interface Segment {
  id: string;
  sourceRef: string;
  startTimeBeats: number;
  endTimeBeats: number;
  trimInBeats?: number;
  trimOutBeats?: number;
  volume?: number;
  effects?: Effect[];
}

export interface Source {
  id: string;
  name: string;
  url: string;
  type: 'video' | 'audio' | 'image';
  duration?: number;
  metadata?: SourceMetadata;
}

export interface VideoConfig {
  width: number;
  height: number;
  fps: number;
  format: string;
}

export interface BeatPattern {
  beatsPerMeasure: number;
  pattern: boolean[];
}

export interface Effect {
  id: string;
  type: string;
  parameters: Record<string, any>;
  startTime?: number;
  endTime?: number;
}

export interface SourceMetadata {
  fileSize?: number;
  codecInfo?: string;
  uploadedAt?: Date;
  processingInfo?: any;
}

// Processing and job types
export interface ProcessingJob {
  id: string;
  userId: string;
  kompositionId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  startedAt: Date;
  completedAt?: Date;
  errorMessage?: string;
  outputUrl?: string;
}

// App state interface
export interface AppState {
  user: User | null;
  kompositions: Komposition[];
  currentKomposition: Komposition | null;
  processingJobs: ProcessingJob[];
  isLoading: boolean;
  error: string | null;
}

// Elm integration types
export interface ElmApp {
  ports?: {
    saveKomposition?: {
      subscribe: (callback: (data: any) => void) => void;
    };
    loadKomposition?: {
      send: (data: any) => void;
    };
    kompositionUpdated?: {
      subscribe: (callback: (data: Komposition) => void) => void;
    };
    firebaseTokenUpdated?: {
      send: (token: string | null) => void;
    };
  };
}

// Firebase integration types
export interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
}

// MCP integration types
export interface MCPOperation {
  id: string;
  type: string;
  inputFormat?: string;
  outputFormat?: string;
  parameters: string;
  fileSize?: {
    input: number;
    output: number;
  };
}

export interface MCPOperationEvent {
  id: string;
  timestamp: string;
  userId: string;
  platform: 'mcp' | 'komposteur';
  operation: MCPOperation;
  metrics: {
    success: boolean;
    processingTime?: number;
    errorMessage?: string;
  };
  context?: {
    workflowPosition?: number;
    totalWorkflowSteps?: number;
    userIntent?: string;
  };
}