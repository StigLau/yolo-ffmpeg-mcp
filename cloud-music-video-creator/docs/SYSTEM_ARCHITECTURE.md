# Cloud Music Video Creator - System Architecture

## Overview

This document defines the architecture for a Cloud Run service that enables users to create professional music videos through AI-guided komposition workflows. The system leverages learnings from the YOLO-FFMPEG-MCP project to deliver cost-effective, high-quality video processing.

## High-Level Architecture

### Request Flow
```
User Request
    ↓
FastAPI Frontend
    ↓
Gemini Pro 2.5 (User-facing LLM)
    ↓ MCP Protocol
MCP Server Layer
    ↓
Registry + Komposition Services
    ↓
Gemini Flash/Haiku (Processing LLM)
    ↓
FFmpeg Operations
    ↓
Response to User
```

## Component Breakdown

### 1. API Layer (`src/api/`)

**FastAPI Application**
- **Endpoints**: RESTful API for komposition CRUD, processing requests, status polling
- **Authentication**: User session management (future: OAuth integration)
- **WebSocket Support**: Real-time processing updates and conversation streaming
- **Error Handling**: Graceful error responses with user-friendly messages

**Key Endpoints**:
```python
POST /kompositions/           # Create new komposition from prompt
GET  /kompositions/{id}       # Retrieve komposition with processing history
PUT  /kompositions/{id}       # Update/refine existing komposition
POST /kompositions/{id}/process  # Trigger video generation
GET  /kompositions/{id}/status   # Processing status and progress
GET  /kompositions/{id}/videos   # List generated videos
```

### 2. LLM Integration Layer (`src/llm/`)

**Gemini Pro 2.5 Integration**
```python
class GeminiProClient:
    """High-level creative and conversational LLM"""
    
    async def create_komposition(self, user_prompt: str) -> KompositionSpec
    async def refine_komposition(self, komposition: Komposition, user_feedback: str) -> KompositionSpec
    async def suggest_improvements(self, komposition: Komposition) -> List[Suggestion]
```

**Gemini Flash/Haiku Integration**
```python
class ProcessingLLM:
    """Technical processing and FFmpeg command generation"""
    
    async def generate_ffmpeg_commands(self, segments: List[Segment]) -> List[FFmpegCommand]
    async def analyze_video_content(self, video_path: str) -> VideoAnalysis
    async def optimize_processing_strategy(self, komposition: Komposition) -> ProcessingStrategy
```

### 3. MCP Server Layer (`src/mcp/`)

**Core MCP Server**
```python
class CloudMusicVideoMCP:
    """MCP server providing komposition and video processing tools"""
    
    # Registry tools
    @mcp.tool()
    async def create_komposition(self, spec: KompositionSpec) -> Komposition
    
    @mcp.tool()
    async def get_komposition(self, komposition_id: str) -> Komposition
    
    @mcp.tool()
    async def update_komposition(self, komposition_id: str, updates: dict) -> Komposition
    
    # Processing tools
    @mcp.tool()
    async def process_video_segment(self, segment: Segment, effects: List[Effect]) -> ProcessedSegment
    
    @mcp.tool()
    async def generate_final_video(self, komposition: Komposition) -> VideoOutput
    
    # Registry tools
    @mcp.tool()
    async def register_media_file(self, file_path: str, metadata: MediaMetadata) -> MediaReference
    
    @mcp.tool()
    async def get_media_file(self, media_id: str) -> MediaFile
```

### 4. Data Models (`src/models/`)

**Core Models**
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class BeatSyncType(str, Enum):
    QUARTER_NOTE = "quarter"
    EIGHTH_NOTE = "eighth"
    MEASURE = "measure"

class EffectType(str, Enum):
    CROSSFADE = "crossfade"
    ZOOM = "zoom"
    COLOR_GRADE = "color_grade"
    EIGHT_BIT = "8bit"
    LEICA = "leica"

class MediaReference(BaseModel):
    """Reference to media file (temp or cloud storage)"""
    id: str
    type: str  # "video", "audio", "image"
    location: str  # file path or cloud URL
    storage_type: str  # "temp", "s3", "gcs"
    metadata: Dict[str, Any]

class Segment(BaseModel):
    """Individual video segment within komposition"""
    id: str
    start_beat: float
    duration_beats: float
    start_seconds: float
    duration_seconds: float
    source_media: MediaReference
    effects: List[Effect]
    visual_score: float

class AudioTrack(BaseModel):
    """Audio track for komposition"""
    source: MediaReference
    bpm: float
    duration_seconds: float
    fade_in: Optional[float] = None
    fade_out: Optional[float] = None

class Komposition(BaseModel):
    """Complete music video komposition"""
    id: str
    title: str
    description: Optional[str]
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    # Audio/tempo info
    bpm: float
    total_beats: float
    duration_seconds: float
    audio_track: AudioTrack
    
    # Visual info
    resolution: str  # "1920x1080", "1280x720"
    segments: List[Segment]
    
    # Processing
    status: str  # "draft", "processing", "completed", "failed"
    processing_metadata: Optional[Dict[str, Any]]
    
    # Output
    generated_videos: List[VideoOutput] = []

class VideoOutput(BaseModel):
    """Generated video output"""
    id: str
    komposition_id: str
    file_reference: MediaReference
    generation_timestamp: datetime
    processing_cost: float
    quality_score: float
    processing_duration: float
```

### 5. Registry System (`src/registry/`)

**Komposition Registry**
```python
class KompositionRegistry:
    """Manages komposition lifecycle and persistence"""
    
    async def create(self, spec: KompositionSpec, user_id: str) -> Komposition
    async def get(self, komposition_id: str) -> Optional[Komposition]
    async def update(self, komposition_id: str, updates: dict) -> Komposition
    async def list_user_kompositions(self, user_id: str) -> List[Komposition]
    async def delete(self, komposition_id: str) -> bool
```

**Media Registry**
```python
class MediaRegistry:
    """Manages media file lifecycle across temp and cloud storage"""
    
    async def register_file(self, file_path: str, metadata: MediaMetadata) -> MediaReference
    async def get_file(self, media_id: str) -> Optional[MediaFile]
    async def cleanup_temp_files(self, older_than: datetime) -> int
    async def promote_to_permanent(self, media_id: str) -> MediaReference
```

### 6. Komposition Processing (`src/komposition/`)

**Komposition Processor**
```python
class KompositionProcessor:
    """Orchestrates komposition creation and refinement"""
    
    def __init__(self, llm_client: GeminiProClient, processing_llm: ProcessingLLM):
        self.llm = llm_client
        self.processing_llm = processing_llm
    
    async def create_from_prompt(self, prompt: str, user_id: str) -> Komposition
    async def refine_komposition(self, komposition: Komposition, feedback: str) -> Komposition
    async def generate_video(self, komposition: Komposition) -> VideoOutput
```

### 7. Storage Abstraction (`src/storage/`)

**Storage Interface**
```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Abstract storage interface for temp and cloud storage"""
    
    @abstractmethod
    async def store_file(self, data: bytes, path: str) -> str
    
    @abstractmethod
    async def retrieve_file(self, path: str) -> bytes
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool
    
    @abstractmethod
    async def list_files(self, prefix: str) -> List[str]

class TempStorageBackend(StorageBackend):
    """Local temp storage for development and processing"""
    
class CloudStorageBackend(StorageBackend):
    """Cloud storage backend (S3/GCS) for production"""
    # Implementation deferred to future phase
```

## Processing Flow

### Komposition Creation Flow
```
1. User Prompt → Gemini Pro 2.5
   ↓ "Create a 135 BPM music video with urban street scenes"
   
2. Gemini Pro 2.5 → MCP Server
   ↓ create_komposition(spec) with structured requirements
   
3. MCP Server → Registry
   ↓ Store new komposition with "draft" status
   
4. Registry → Processing LLM
   ↓ Analyze requirements, suggest source media, calculate timing
   
5. Processing LLM → MCP Server
   ↓ Refined komposition with technical details
   
6. MCP Server → User
   ↓ Return complete komposition for review
```

### Video Generation Flow
```
1. User Request → process_komposition(id)
   ↓
   
2. MCP Server → Processing LLM
   ↓ Generate FFmpeg commands for each segment
   
3. Processing LLM → Video Processing
   ↓ Execute FFmpeg operations with FastTrack optimization
   
4. Video Processing → Quality Check
   ↓ Verify output quality and format
   
5. Quality Check → Registry
   ↓ Store video output and update komposition
   
6. Registry → User
   ↓ Return completed video with metadata
```

## Deployment Architecture (Cloud Run)

### Container Configuration
```dockerfile
# Production-optimized container
FROM python:3.11-slim

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Application setup
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

# Cloud Run configuration
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Resource Configuration
```yaml
# Cloud Run service configuration
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: cloud-music-video-creator
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/cpu: "2"
    spec:
      containerConcurrency: 10
      timeoutSeconds: 300
```

## Data Storage Strategy

### Development Phase (Temp Storage)
- **Location**: `/tmp/music-video-creator/`
- **Structure**: Organized by user session and komposition ID
- **Cleanup**: Automatic cleanup after processing completion
- **Persistence**: None - stateless processing

### Production Phase (Future - Cloud Storage)
- **Temp Storage**: Container temp directories for processing
- **Permanent Storage**: GCS/S3 buckets for kompositions and outputs
- **CDN**: Cloud CDN for video delivery
- **Database**: Cloud SQL/Firestore for metadata

## Cost Optimization Strategy

### LLM Usage Optimization
- **Tier Routing**: Use cheapest capable model for each operation
- **Batch Processing**: Group similar operations when possible
- **Caching**: Cache analysis results and intermediate processing
- **Budget Controls**: Daily/monthly limits with graceful degradation

### Processing Optimization
- **FastTrack Integration**: $0.02-0.05 analysis vs manual $125 decisions
- **Smart Strategies**: Auto-select optimal FFmpeg approaches
- **Resource Limits**: Container-aware processing limits
- **Cold Start Mitigation**: Pre-warm critical paths

## Security & Privacy

### Data Handling
- **Temp Files**: Automatic cleanup, no persistent user data storage
- **Session Management**: Secure session tokens, limited lifetime
- **Media Files**: Secure temp storage, automatic purge policies
- **Logs**: Structured logging without sensitive data

### API Security
- **Rate Limiting**: Per-user and global rate limits
- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: No sensitive information in error messages
- **CORS**: Appropriate CORS policies for web frontend

## Monitoring & Observability

### Metrics
- **Processing Metrics**: Video generation times, success rates, quality scores
- **Cost Metrics**: LLM usage, processing costs per komposition
- **Performance Metrics**: Response times, resource utilization
- **Error Metrics**: Failure rates by component, error categorization

### Logging
- **Structured Logging**: JSON format for parsing and analysis
- **Request Tracing**: End-to-end request tracking
- **LLM Interactions**: LLM request/response logging (without sensitive data)
- **Processing Events**: Video generation pipeline events

## Future Enhancements

### Phase 2 Features
- **User Authentication**: OAuth integration, user profiles
- **Collaborative Editing**: Multiple users working on same komposition
- **Template Library**: Pre-built komposition templates
- **Advanced Effects**: More sophisticated video effects library

### Phase 3 Features
- **Cloud Storage Integration**: Full S3/GCS integration
- **CDN Integration**: Fast video delivery
- **Analytics Dashboard**: User usage patterns and system metrics
- **API Marketplace**: Third-party integrations