"""
Media models for Cloud Music Video Creator

Handles file references, storage abstraction, and media metadata
for both temporary and cloud storage scenarios.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator


class StorageType(str, Enum):
    """Storage backend types"""
    TEMP = "temp"           # Local temporary storage
    S3 = "s3"              # AWS S3 (future)
    GCS = "gcs"            # Google Cloud Storage (future)
    LOCAL = "local"        # Local persistent storage


class MediaType(str, Enum):
    """Media file types"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SUBTITLE = "subtitle"
    METADATA = "metadata"


class ProcessingStatus(str, Enum):
    """Media processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"


class MediaMetadata(BaseModel):
    """Media file metadata"""
    # Basic properties
    type: MediaType
    filename: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    checksum: Optional[str] = None  # For integrity verification
    
    # Media-specific properties
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None  # "1920x1080"
    frame_rate: Optional[float] = None
    bitrate: Optional[int] = None
    
    # Audio properties
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    audio_codec: Optional[str] = None
    
    # Video properties
    video_codec: Optional[str] = None
    pixel_format: Optional[str] = None
    
    # Analysis metadata (from FastTrack/Haiku analysis)
    visual_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    content_analysis: Optional[Dict[str, Any]] = None
    technical_quality: Optional[Dict[str, Any]] = None
    
    # Processing history
    processing_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    @validator('resolution')
    def validate_resolution_format(cls, v):
        """Validate resolution format"""
        if v and 'x' not in v:
            raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        return v


class MediaReference(BaseModel):
    """Reference to a media file with storage location"""
    # Identity
    id: str
    type: MediaType
    
    # Storage information
    storage_type: StorageType
    storage_path: str  # Path within storage backend
    storage_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # File metadata
    metadata: MediaMetadata
    
    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # For temp storage cleanup
    
    # Processing
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_metadata: Optional[Dict[str, Any]] = None
    
    # Access control (future)
    user_id: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if media reference has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def full_path(self) -> str:
        """Get full storage path"""
        if self.storage_type == StorageType.TEMP:
            return f"/tmp/music-video-creator/{self.storage_path}"
        elif self.storage_type == StorageType.S3:
            bucket = self.storage_metadata.get('bucket', 'default-bucket')
            return f"s3://{bucket}/{self.storage_path}"
        elif self.storage_type == StorageType.GCS:
            bucket = self.storage_metadata.get('bucket', 'default-bucket')
            return f"gs://{bucket}/{self.storage_path}"
        else:
            return self.storage_path
    
    def update_access_time(self) -> None:
        """Update last accessed timestamp"""
        self.last_accessed = datetime.utcnow()


class MediaFile(BaseModel):
    """Complete media file with content and metadata"""
    reference: MediaReference
    content: Optional[bytes] = None  # File content (for small files)
    content_path: Optional[str] = None  # Path to content (for large files)
    
    @property
    def has_content(self) -> bool:
        """Check if file content is available"""
        return self.content is not None or (
            self.content_path is not None and Path(self.content_path).exists()
        )
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return self.reference.metadata.file_size_bytes / (1024 * 1024)


class MediaAnalysis(BaseModel):
    """Analysis results for media file (from FastTrack/Haiku)"""
    media_id: str
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Content analysis
    visual_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    audio_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Technical analysis
    has_issues: bool = False
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Processing recommendations
    recommended_effects: List[str] = Field(default_factory=list)
    optimal_segments: Optional[List[Dict[str, float]]] = None  # Suggested cuts
    
    # Cost estimates
    processing_cost_estimate: float = 0.0
    processing_time_estimate: float = 0.0
    
    # Raw analysis data
    raw_analysis: Dict[str, Any] = Field(default_factory=dict)


class MediaCollection(BaseModel):
    """Collection of related media files"""
    id: str
    name: str
    description: Optional[str] = None
    
    # Media references
    media_references: List[MediaReference] = Field(default_factory=list)
    
    # Collection metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    
    # Collection properties
    tags: List[str] = Field(default_factory=list)
    total_duration: Optional[float] = None
    total_size_bytes: int = 0
    
    @property
    def video_count(self) -> int:
        """Count of video files in collection"""
        return sum(1 for ref in self.media_references if ref.type == MediaType.VIDEO)
    
    @property
    def audio_count(self) -> int:
        """Count of audio files in collection"""
        return sum(1 for ref in self.media_references if ref.type == MediaType.AUDIO)
    
    def add_media(self, media_ref: MediaReference) -> None:
        """Add media reference to collection"""
        if media_ref.id not in [ref.id for ref in self.media_references]:
            self.media_references.append(media_ref)
            self.total_size_bytes += media_ref.metadata.file_size_bytes
            self.updated_at = datetime.utcnow()
            
            # Update total duration for video/audio
            if media_ref.metadata.duration_seconds:
                if self.total_duration is None:
                    self.total_duration = media_ref.metadata.duration_seconds
                else:
                    self.total_duration += media_ref.metadata.duration_seconds
    
    def remove_media(self, media_id: str) -> bool:
        """Remove media reference from collection"""
        for i, ref in enumerate(self.media_references):
            if ref.id == media_id:
                removed_ref = self.media_references.pop(i)
                self.total_size_bytes -= removed_ref.metadata.file_size_bytes
                
                # Update total duration
                if removed_ref.metadata.duration_seconds and self.total_duration:
                    self.total_duration -= removed_ref.metadata.duration_seconds
                
                self.updated_at = datetime.utcnow()
                return True
        return False


class ProcessingJob(BaseModel):
    """Media processing job tracker"""
    id: str
    media_id: str
    job_type: str  # "analysis", "conversion", "optimization"
    
    # Job configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)  # 1 = highest, 10 = lowest
    
    # Status tracking
    status: ProcessingStatus = ProcessingStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Progress tracking
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    
    # Results
    output_media_ids: List[str] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Cost tracking
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete"""
        return self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]


class StorageQuota(BaseModel):
    """Storage quota and usage tracking"""
    user_id: str
    storage_type: StorageType
    
    # Quota limits
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB default
    max_total_size_bytes: int = 1024 * 1024 * 1024  # 1GB default
    max_file_count: int = 100
    
    # Current usage
    current_size_bytes: int = 0
    current_file_count: int = 0
    
    # Usage tracking
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def size_utilization_percent(self) -> float:
        """Calculate size quota utilization percentage"""
        return (self.current_size_bytes / self.max_total_size_bytes) * 100
    
    @property
    def file_count_utilization_percent(self) -> float:
        """Calculate file count quota utilization percentage"""
        return (self.current_file_count / self.max_file_count) * 100
    
    def can_add_file(self, file_size: int) -> bool:
        """Check if file can be added within quota"""
        return (
            file_size <= self.max_file_size_bytes and
            self.current_size_bytes + file_size <= self.max_total_size_bytes and
            self.current_file_count < self.max_file_count
        )
    
    def add_file_usage(self, file_size: int) -> None:
        """Add file to usage tracking"""
        self.current_size_bytes += file_size
        self.current_file_count += 1
        self.last_updated = datetime.utcnow()
    
    def remove_file_usage(self, file_size: int) -> None:
        """Remove file from usage tracking"""
        self.current_size_bytes = max(0, self.current_size_bytes - file_size)
        self.current_file_count = max(0, self.current_file_count - 1)
        self.last_updated = datetime.utcnow()